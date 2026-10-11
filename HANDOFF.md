# Conversation handoff — 2026-10-11

This is a curated project-memory summary, not a verbatim export or live migration of a Codex conversation. It preserves the decisions needed for Claude Code, Codex, or a human to use the processor.

## What the owner wants

Local trimming of voiceovers, originally generated with the Adam voice. Keep all words in order. Trim pauses and audible inter-word breaths. Increase speed and pitch together. Final files should be MP3.

Current standing speed is 1.30–1.33x, preferring the closest possible value to 1.30x. Default cap is 43 seconds, subject to the user's instructions. A cap is not a target. Short samples remain short. A one-off request for 1.40x does not change the standing default.

## What changed during calibration

1. The original draft preserved pitch with atempo. The user clarified that they wanted pitch to rise with speed, like ordinary rate-based playback.
2. Initial 1.45x and later 1.35x speeds were superseded by the current 1.30–1.33x range.
3. The user reported breaths surviving the initial -45 dB threshold. The working trial moved to -35 dB with the same 120 ms minimum gap and 35/45 ms margins. This is still an energy threshold, not reliable breath recognition.
4. For several specific files, slower speech was requested while retaining a higher pitch. A fragmented speech-block time-stretch method was later rejected for sounding like slow motion while sped up. Do not reuse it by default.
5. The owner explicitly rejected forcing every recording to 39–40 seconds. Use the natural result within limits, and honor individual exceptions only when requested.
6. An MP3 export through mp3_mf had wrong duration metadata. Use libmp3lame. Final MP3 files must decode successfully and meet the cap.

## Current workflow

Run `voiceover.py`, using the single settings.json preset. It decodes audio to 44.1 kHz PCM, detects low-level gaps, retains margins, joins remaining audio in order, applies speed-linked pitch, and exports 192 kbps MP3. Verify the result, report speed/duration, and let the user listen. Do not interpret a filename's voice-generation settings as processing instructions.

## Scope of sharing

Code, current rules, setup instructions, tests and this decision summary can travel with the project. Personal recordings, private drive paths, full chat transcript, credentials and historical output files are not in the distribution. The original four raw/edited pairs belong to the owner; pair 05 should remain held out from tuning if supplied later.

## Known limits

No transcription or acoustic word-preservation proof. Breath removal, quiet consonants and transitions remain listening tasks. Same code/settings are reproducible within an environment; different FFmpeg builds may differ slightly. The prototype is not a measured replica of CapCut.
