# Voiceover Splicer instructions

Read README.md, HANDOFF.md and CALIBRATION.md before work. settings.json is the single current preset.

- Run voiceover.py for final MP3 delivery; splice.py is the WAV processing engine.
- Prefer 1.30x, hard range 1.30–1.33x. Default cap 43 seconds. Raise speed only to meet a cap. User instructions can override these for a recording; do not persist a one-off override.
- Speed determines pitch directly. Do not independently stretch speech or use the rejected fragmented speech-block retiming approach by default.
- Preserve every spoken word in its original order. Remove pauses and unwanted inter-word breaths only. Never truncate speech, force a fixed duration, or exceed speed limits to fit.
- If speed and cap cannot both be met, explain the conflict and ask for a revised limit. Do not change the threshold merely to hit the cap.
- Keep originals and references immutable. Use new output names; deliver the MP3 and report duration/speed. WAV and JSON are retained for verification.
- Processing remains local, deterministic and free of per-recording AI API expense. No transcription, voice generation or cloud audio upload without concrete need and user authorization.
- Energy detection is not speech recognition or a breath classifier. Quiet consonants and noisy gaps need listening. Never claim flawless preservation, exact pitch/CapCut equivalence, or an approved preset without evidence.
- Ask for timestamps when users report clipping, breaths or pacing issues. Record feedback and accepted/rejected settings in CALIBRATION.md. Keep pair 05 held out if reference pairs are supplied.
- No interface-building until the sound is accepted. Keep changes small and run meaningful checks.
- Do not publish private input/output audio or the original chat history. This repository contains the curated handoff only.
