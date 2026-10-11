"""Portable local voiceover processing and verified MP3 delivery."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

import numpy as np
from splice import RATE, process, read_wav, run

ROOT = Path(__file__).resolve().parent


def find_ffmpeg(explicit=None):
    candidates = [explicit] if explicit else [os.environ.get('VOICEOVER_FFMPEG')]
    if not any(candidates):
        try:
            import imageio_ffmpeg
            candidates.append(imageio_ffmpeg.get_ffmpeg_exe())
        except (ImportError, RuntimeError):
            pass
        candidates.append(shutil.which('ffmpeg'))
    for candidate in filter(None, candidates):
        resolved = shutil.which(str(candidate))
        if not resolved:
            continue
        encoders = run([resolved, '-hide_banner', '-encoders']).stdout.decode(errors='replace')
        if re.search(r'\blibmp3lame\b', encoders):
            return resolved
    raise ValueError('Install requirements.txt, or supply --ffmpeg with an FFmpeg build containing libmp3lame.')


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def deliver(source, output, maximum=43, settings=None, ffmpeg=None):
    source, output = Path(source).resolve(), Path(output).resolve()
    if not source.is_file():
        raise ValueError('Input audio does not exist.')
    if output.suffix.lower() != '.mp3':
        raise ValueError('Final output must use .mp3.')
    destinations = [output, output.with_suffix('.wav'), output.with_suffix('.json')]
    if any(p.exists() or p == source for p in destinations):
        raise ValueError('Choose a new output name; MP3, WAV and JSON must not already exist.')
    if not math.isfinite(maximum) or maximum <= .1:
        raise ValueError('Maximum duration must exceed 0.1 seconds.')
    if settings is None:
        settings = json.loads((ROOT/'settings.json').read_text(encoding='utf-8'))
    encoder = find_ffmpeg(ffmpeg)
    original = sha256(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    published = []
    try:
        with tempfile.TemporaryDirectory(prefix='.voiceover-', dir=output.parent) as temp:
            temp = Path(temp)
            wav, mp3, report_file = temp/'processed.wav', temp/'processed.mp3', temp/'report.json'
            report = process(source, wav, maximum, settings, ffmpeg=encoder)
            run([encoder, '-v', 'error', '-n', '-i', str(wav), '-c:a', 'libmp3lame', '-b:a', '192k', str(mp3)])
            pcm = run([encoder, '-v', 'error', '-i', str(mp3), '-f', 's16le', '-ar', str(RATE), '-']).stdout
            channels = read_wav(wav).shape[1]
            samples = np.frombuffer(pcm, dtype='<i2')
            seconds = len(samples)/channels/RATE
            if not len(samples) or not np.any(samples) or seconds > maximum:
                raise ValueError('Final MP3 failed decoded audio/duration verification; nothing delivered.')
            if abs(seconds-report['output_seconds']) > .05:
                raise ValueError('MP3 decoded duration differs from WAV; nothing delivered.')
            if sha256(source) != original:
                raise ValueError('Source changed during processing; nothing delivered.')
            report.update(mp3_seconds=seconds, mp3_bitrate_kbps=192, source_sha256=original,
                          source_unchanged=True, ffmpeg_version=run([encoder, '-version']).stdout.decode(errors='replace').splitlines()[0],
                          processing='local; no transcription or AI audio generation')
            report_file.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
            # Exclusive creation also prevents overwrites if a competing process creates a file.
            for staged, destination in zip([mp3, wav, report_file], destinations):
                with destination.open('xb') as target:
                    published.append(destination)
                    with staged.open('rb') as origin:
                        shutil.copyfileobj(origin, target)
        return report
    except Exception:
        for path in published:
            path.unlink(missing_ok=True)
        raise


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('input', nargs='?')
    p.add_argument('output', nargs='?')
    p.add_argument('--max-seconds', type=float, default=43)
    p.add_argument('--settings', type=Path, default=ROOT/'settings.json')
    p.add_argument('--speed', type=float, help='Preferred speed for this run only')
    p.add_argument('--max-speed', type=float, help='Explicitly override upper speed limit for this run')
    p.add_argument('--ffmpeg', help='Optional path to an FFmpeg executable with libmp3lame')
    p.add_argument('--check', action='store_true', help='Check dependencies without processing audio')
    args = p.parse_args()
    try:
        if args.check:
            encoder = find_ffmpeg(args.ffmpeg)
            print('Ready: NumPy and FFmpeg with libmp3lame.\n'+encoder)
            return
        if not args.input or not args.output:
            p.error('input and output are required unless --check is used')
        settings = json.loads(args.settings.read_text(encoding='utf-8'))
        if not isinstance(settings, dict):
            raise ValueError('Settings must be a JSON object.')
        if args.speed is not None:
            settings['base_speed'] = args.speed
        if args.max_speed is not None:
            settings['maximum_speed'] = args.max_speed
        report = deliver(args.input, args.output, args.max_seconds, settings, args.ffmpeg)
        print(json.dumps({'mp3':str(Path(args.output).resolve()), 'seconds':report['mp3_seconds'],
                          'speed':report['effective_speed'], 'removed_seconds':report['removed_seconds'],
                          'listening':'Please check breaths, quiet consonants and transitions.'}, indent=2))
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        details = exc.stderr.decode(errors='replace')[-1200:] if isinstance(exc, subprocess.CalledProcessError) and exc.stderr else str(exc)
        p.exit(1, f'Processing failed: {details}\n')


if __name__ == '__main__':
    main()
