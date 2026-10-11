# Voiceover Splicer

A local Python/FFmpeg prototype for trimming low-level gaps and speeding up voiceovers. Works from a terminal or through Claude Code/Codex. No OpenAI or Anthropic API key is needed for audio processing. Using an AI assistant has its own account requirements.

## Current preset

- Prefer **1.30x**, maximum **1.33x**; raise speed only when the duration cap requires it.
- Default cap: **43 seconds**, not a target. Short recordings stay short.
- Pitch rises directly with speed. No separate pitch adjustment or speech-block stretching.
- Gap detection: **-35 dB**, minimum **120 ms**, retaining **35 ms after / 45 ms before** speech, with **2 ms** edge fades.
- Deliver **192 kbps MP3**, plus a WAV and JSON timing/cut report.

This is the current working preset, not an approved universal preset. Energy detection can mistake quiet consonants for silence and miss breaths. Listen before using a result. Never cut speech or exceed the speed range just to meet a cap.

## Setup once

Install Python **3.10 or newer**. Download this repository with **Code → Download ZIP** and extract it, or clone it. Open a terminal in the extracted folder.

Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe voiceover.py --check
```

macOS / Linux:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python voiceover.py --check
```

`imageio-ffmpeg` supplies a local FFmpeg executable on supported platforms. After installation, processing is offline. If your platform has no compatible bundled binary, install FFmpeg with `libmp3lame` and use `--ffmpeg "/path/to/ffmpeg"`. The `VOICEOVER_FFMPEG` environment variable also selects an executable. Do not use `mp3_mf`: an earlier build produced incorrect duration metadata.

No dependency on the original owner's drive letters, Codex Python runtime, or Krita installation is required. An explicit FFmpeg override remains available for existing installations.

## Process a recording

Windows:

```powershell
.\.venv\Scripts\python.exe voiceover.py "input.mp3" "output/take01.mp3"
```

macOS / Linux:

```sh
.venv/bin/python voiceover.py "input.mp3" "output/take01.mp3"
```

You get `take01.mp3`, `take01.wav`, and `take01.json`. Existing files are never overwritten. The MP3 is decoded and checked for nonzero audio and duration before final delivery. Source SHA-256 is checked before and after processing. Settings and cut intervals are recorded in the JSON.

For a recording-specific cap:

```sh
python voiceover.py "input.mp3" "output/short.mp3" --max-seconds 37.95
```

Use 37.95 for a strict **under 38 seconds** request, leaving small rounding headroom. The preferred speed still stays 1.30x when it meets the cap.

Only when the user explicitly requests an exception, for example **this recording at 1.40x**:

```sh
python voiceover.py "input.mp3" "output/special.mp3" --speed 1.40 --max-speed 1.40
```

These flags affect that run only; they do not change the preset. If a cap and maximum speed conflict, processing fails without final output. Ask for a revised cap or speed limit; do not silently tighten the detector to remove more audio.

## Use with Claude Code

Open this folder in Claude Code and paste:

> Read CLAUDE.md, README.md, and HANDOFF.md. Set up the local dependencies, then process my voiceover with voiceover.py. Prefer 1.30x and never exceed 1.33x unless I explicitly change it. Default cap is 43 seconds. Preserve word order, use direct speed-linked pitch, deliver the MP3, and tell me its duration and actual speed. Do not stretch short audio to fill the cap. Ask me to listen for clipped consonants or remaining breaths.

Then provide your recording's local file path. Ordinary browser chat alone does not give an assistant local file/command access. This repository is the portable handoff; the original chat session and private recordings are not included.

## Sharing and updates

The owner can invite a friend through the private repository's **Settings → Collaborators → Add people**. Once access is accepted, the friend can clone or download it. A ZIP can also be shared directly. GitHub stores the project; processing runs on the computer where Python runs.

Keep recordings in `input/`, results in `output/`. Both are ignored by Git. Never commit credentials, personal recordings, local environments, or entire chat transcripts by accident. `HANDOFF.md` preserves relevant decisions without private paths and recording history.

## Verification

```sh
python -m unittest discover -s tests -v
```

Tests exercise duration/speed bounds, input errors, no-overwrite behavior, MP3 export, source immutability, a known-frequency pitch shift, and a synthetic quiet edge. A synthetic signal cannot prove real consonants survive. Windows is tested locally; other platforms still need a local setup/listening check.

See `CALIBRATION.md` for the curated history and remaining listening checks. The original reference pairs stay with their owner; pair 05 is reserved for later validation.
