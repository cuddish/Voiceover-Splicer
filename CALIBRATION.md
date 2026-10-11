# Curated calibration record

This portable record summarizes the original owner's feedback; the full local log and audio stay on their computer. Dates describe that history, not new listening approval.

| Date | Decision | Status / reason |
|---|---|---|
| 2026-09-22 | Initial pair 01 sounded "pretty solid" | Positive initial feedback, not general approval |
| 2026-09-22 | Pitch must rise with speed | Replaced default pitch-preserving processing |
| 2026-09-22 | Trial threshold -35 dB; retain 120 ms minimum and 35/45 ms margins | Intended to catch quieter breaths; consonant/breath quality still pending |
| 2026-09-29 | Reject forced 39–40 s and fragmented speech-block stretching | User described a slow-motion vocal artifact |
| 2026-10-08 | Final standing range 1.30–1.33x, prefer 1.30x, cap 43 s | User's latest persistent preference |
| 2026-10-11 | One recording at 1.40x | Explicit one-off exception, not the default |
| 2026-10-11 | Portable package consolidates -35 dB working trial and automatic MP3 export | Supersedes stale checked-in -45 dB preset; does not imply listening approval |

The original pairs are 01, 02, 04 and 05. Pair 05 stays held out. No speed estimate was inferred from raw/edited duration ratios, which combine cuts and speed.

Unresolved: reliable breath identification, preservation of all quiet consonants, exact reference alignment, unfamiliar voices, cross-platform listening comparison. No UI should be built until the sound is accepted.

## New feedback

Portable verification (2026-10-11): all seven automated tests passed with both an existing FFmpeg installation and a fresh project-local installation of NumPy 2.5.4 / imageio-ffmpeg 0.6.0 (bundled FFmpeg 7.1), using Python 3.12 on Windows. A real owner's recording matched the prior processor's cuts and duration exactly: 39.929 seconds at 1.30x. Source hash remained unchanged. That recording is not included in this repository. These are technical checks, not new listening approval or cross-platform test results.

Record the input's non-sensitive identifier, output timestamp/word, setting changed, and accepted/rejected result here. Change one parameter group at a time. Technical tests do not replace listening.
