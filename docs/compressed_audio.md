# MP3 and Ogg sounds in the shared timeline

Desktop **Add audio** accepts PCM16 WAV, MP3 and Ogg. The sound starts at the
frame captured when the picker opens, even if the playhead subsequently moves.
WAV keeps its existing direct import. MP3/Ogg preparation runs in a hidden local
worker and displays a nonexclusive Cancel dialog. The original file is untouched.
All sound clips use the existing Audio chooser, timing, trim, gain, mute, Undo,
preview clock and output mix; no compressed-format playback engine is added.

The worker decodes the first audio stream to 48kHz PCM16 WAV, retaining mono or
stereo layouts instead of forcing a mono-to-stereo rematrix, using the
configured movie-encoder FFmpeg. The normalized file is created in a new managed
`output/audio-imports/` job directory. Studio verifies its checksum and parses it
through the existing bounded WAV reader before adding one ordinary sound clip.
The original filename stays visible. Cancel or a scene/revision/settings change
discards the result without appending a clip or changing Undo. Seeking alone is
allowed because placement was captured explicitly. Playing/exporting during
preparation prevents automatic insertion. Failure allows another attempt.

Packed HAS includes the decoded WAV; it can reopen/play/export without the MP3
or Ogg and without running a decoder. Linked HAS externalizes generated normalized
WAVs to its stable neighboring `.assets` directory, not the original compressed
input or a disposable decode-job folder. Keep that sidecar directory with the
linked project, or choose packed saves. Existing checksummed/deduplicated WAV
members and audio schemas stay unchanged. Old projects keep working; old Studio
versions still have their existing multi-clip limitation.

## Bounds and failure handling

Source input is at most32MiB; decoded clips remain limited to60seconds and the
existing16-clip/64MiB decoded-PCM scene budget. To detect excess duration from
actual decoded samples, conversion reads at most61seconds and rejects results
over60; it never adds the first60seconds as though it were the complete sound.
The worker has a45second timeout, polls cancellation and terminates/reaps its
FFmpeg child before publishing a failure. Temporary output is removed on failure;
result JSON is published atomically. A missing decoder points to the existing
Advanced movie-encoder path; malformed inputs preserve existing sounds.

Only local MP3 and Ogg demuxers are selected, with FFmpeg's input protocol
allowlist limited to `file`. Metadata, pictures and video streams are not imported.
No audio file or sample leaves the computer. This is bounded input handling,
not hostile-media certification. See FFmpeg's primary
[protocol documentation](https://www.ffmpeg.org/ffmpeg-protocols.html),
[format documentation](https://ffmpeg.org/ffmpeg-formats.html) and
[command options](https://ffmpeg.org/ffmpeg.html).

This increment does not add M4A/FLAC, float/24-bit WAV conversion, streaming URLs,
audio effects/fades, source splitting, microphone recording or a new web build.
The web preview retains its WAV path and explains that compressed preparation
needs desktop Studio. PCM mixing/rebuilding is still synchronous and bounded;
long scenes and artist listening/input acceptance remain separate work.

## Verification entry point

`python tests/verify_compressed_audio.py` generates original tones and encodes
MP3/Ogg using installed FFmpeg, checks real failure/cancel/overlong paths, then
uses the actual private-desktop Studio file picker and worker. It covers append
placement, original names, untouched earlier sound, exact Undo/Redo, captured
AudioStreamPlayer output or explicit Dummy fallback, cancellation, missing/bad
decoder/input, stale scene rejection, retry, packed reopening while WAV sources
are hidden, linked reopening with generated decode files still hidden and exact
PCM, an independent drawing and ordinary
H2641080p24/AAC movie. The host decodes the movie, checks all three tone windows
and silence, and verifies original input hashes and the private-desktop receipt.
The latest dated progress memo records actual results and limitations.
