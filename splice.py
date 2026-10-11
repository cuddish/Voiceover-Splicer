"""Pause-trimming voiceover processor. Python 3.10+, NumPy, FFmpeg on PATH."""
import argparse
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import wave

import numpy as np

RATE = 44100


def run(args):
    return subprocess.run(args, check=True, capture_output=True)


def read_wav(path):
    with wave.open(str(path), 'rb') as f:
        channels = f.getnchannels()
        return np.frombuffer(f.readframes(f.getnframes()), dtype='<i2').reshape(-1, channels).copy()


def write_wav(path, data):
    with wave.open(str(path), 'wb') as f:
        f.setnchannels(data.shape[1])
        f.setsampwidth(2)
        f.setframerate(RATE)
        f.writeframes(data.astype('<i2').tobytes())


def tempo_filter(speed):
    factors = []
    while speed > 2:
        factors.append(2.0)
        speed /= 2
    factors.append(speed)
    return ','.join(f'atempo={v:.10f}' for v in factors)


def process(source, output, maximum, settings, ffmpeg='ffmpeg'):
    source, output = Path(source), Path(output)
    if not shutil.which(str(ffmpeg)):
        raise ValueError('FFmpeg is required on PATH.')
    if not source.is_file():
        raise ValueError('Input audio does not exist.')
    report_path = output.with_suffix('.json')
    if output.suffix.lower() != '.wav':
        raise ValueError('Use a .wav output path.')
    if output.exists() or report_path.exists() or source.resolve() == output.resolve():
        raise ValueError('Choose a new output path; existing files are never overwritten.')
    if not math.isfinite(maximum) or maximum <= .1:
        raise ValueError('Maximum duration must exceed 0.1 seconds.')
    required = {'threshold_db', 'minimum_pause_ms', 'tail_ms', 'head_ms', 'fade_ms', 'base_speed'}
    if not isinstance(settings, dict) or not required <= settings.keys():
        raise ValueError('Settings must include all required preset fields.')
    for key, value in settings.items():
        if not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f'Invalid setting: {key}')
    if not -100 <= settings['threshold_db'] <= -10:
        raise ValueError('threshold_db must be between -100 and -10.')
    if settings['base_speed'] < 1 or settings['minimum_pause_ms'] <= 0:
        raise ValueError('Invalid speed or pause setting.')
    minimum_speed = settings.get('minimum_speed', 1.30)
    maximum_speed = settings.get('maximum_speed', 1.33)
    if not 1 <= minimum_speed <= settings['base_speed'] <= maximum_speed:
        raise ValueError('Base speed must lie within the configured speed range.')
    if any(settings[k] < 0 for k in ('tail_ms', 'head_ms', 'fade_ms')):
        raise ValueError('Margins and fades cannot be negative.')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as tmp:
        decoded, joined, rendered = [Path(tmp) / n for n in ('decoded.wav', 'joined.wav', 'rendered.wav')]
        run([str(ffmpeg), '-v', 'error', '-i', str(source), '-ar', str(RATE), '-c:a', 'pcm_s16le', str(decoded)])
        data = read_wav(decoded)
        duration = len(data) / RATE
        if not len(data) or np.max(np.abs(data.astype(np.int32))) < 4:
            raise ValueError('Input is empty or effectively silent.')
        result = run([str(ffmpeg), '-hide_banner', '-i', str(decoded), '-af',
                      f"silencedetect=noise={settings['threshold_db']}dB:d={settings['minimum_pause_ms']/1000}",
                      '-f', 'null', '-']).stderr.decode(errors='replace')
        events = re.findall(r'silence_(start|end):\s*([\d.]+)', result)
        gaps, start = [], None
        for kind, number in events:
            if kind == 'start':
                start = float(number)
            elif start is not None:
                gaps.append((start, min(float(number), duration)))
                start = None
        if start is not None:
            gaps.append((start, duration))
        cuts = []
        for a, b in gaps:
            left = 0 if a <= 1 / RATE else a + settings['tail_ms'] / 1000
            right = duration if b >= duration - 1 / RATE else b - settings['head_ms'] / 1000
            lo, hi = max(0, round(left * RATE)), min(len(data), round(right * RATE))
            if hi > lo:
                cuts.append((lo, hi))
        pieces, cursor = [], 0
        for lo, hi in cuts:
            if lo > cursor:
                pieces.append(data[cursor:lo].copy())
            cursor = hi
        if cursor < len(data):
            pieces.append(data[cursor:].copy())
        if not pieces:
            raise ValueError('No audio remains at this threshold; use a lower threshold.')
        # Short fades at detected cut edges; speech preservation still needs listening.
        for i, part in enumerate(pieces):
            n = min(round(settings['fade_ms'] * RATE / 1000), len(part) // 2)
            if n:
                if i > 0 or cuts and cuts[0][0] == 0:
                    part[:n] = (part[:n] * np.linspace(0, 1, n)[:, None]).astype(np.int16)
                if i < len(pieces) - 1 or cuts and cuts[-1][1] == len(data):
                    part[-n:] = (part[-n:] * np.linspace(1, 0, n)[:, None]).astype(np.int16)
        stitched = np.concatenate(pieces)
        write_wav(joined, stitched)
        speed = max(settings['base_speed'], len(stitched) / RATE / maximum)
        # Re-render from the original splice if FFmpeg's frame rounding exceeds the cap.
        for _ in range(5):
            if speed > maximum_speed:
                raise ValueError('Duration cap requires exceeding the permitted speed range. '
                                 'No final audio saved; increase the cap or explicitly change the speed range.')
            rate = math.ceil(RATE * speed)
            if settings.get('speed_changes_pitch', False) and rate / RATE > maximum_speed + 1e-12:
                raise ValueError('Sample-rate rounding exceeds the permitted speed range.')
            audio_filter = (f'asetrate={rate},aresample={RATE}'
                            if settings.get('speed_changes_pitch', False) else tempo_filter(speed))
            run([str(ffmpeg), '-v', 'error', '-y', '-i', str(joined), '-af', audio_filter,
                 '-c:a', 'pcm_s16le', str(rendered)])
            final = read_wav(rendered)
            actual = len(final) / RATE
            if actual <= maximum:
                break
            speed *= actual / maximum * 1.002
        else:
            raise ValueError('Unable to meet the duration cap. No final audio was saved.')
        report = dict(input=source.name, raw_seconds=duration, spliced_seconds=len(stitched)/RATE,
                      output_seconds=actual, maximum_seconds=maximum, speed=speed,
                      effective_speed=rate/RATE if settings.get('speed_changes_pitch', False) else speed,
                      removed_seconds=(len(data)-len(stitched))/RATE,
                      pitch_mode='speed-linked' if settings.get('speed_changes_pitch', False) else 'preserved',
                      settings=settings, cuts=[dict(start=a/RATE, end=b/RATE) for a,b in cuts],
                      status='Prototype; listening approval pending. Energy detection is not word recognition.')
        shutil.copyfile(rendered, output)
        report_path.write_text(json.dumps(report, indent=2) + '\n')
        return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('input')
    p.add_argument('output')
    p.add_argument('--max-seconds', type=float, default=43)
    p.add_argument('--settings', type=Path, default=Path(__file__).with_name('settings.json'))
    args = p.parse_args()
    try:
        print(json.dumps(process(args.input, args.output, args.max_seconds,
                                 json.loads(args.settings.read_text())), indent=2))
    except (ValueError, subprocess.CalledProcessError) as exc:
        p.exit(1, f'Processing failed: {exc}\n')
