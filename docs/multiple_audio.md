# Multiple sound clips

Development **Add audio** appends a PCM16 WAV without replacing earlier sounds.
Desktop [MP3 and Ogg import](compressed_audio.md) now normalizes those sources
locally to the same PCM clip contract before appending.
**Shorten sound…** or the timeline block's right-edge handle now sets a
non-destructive end in Simple; see
[audio end trimming](audio_end_trim.md) for version3 audio compatibility.
Use the Audio chooser or click an audio row to select a sound. Each has its own
Start at frame, Mute and Remove controls in Simple. Drag its timeline block to
change the start with one Undo; motion remains a preview until release. Escape,
focus loss, New/Open and export cancel tentative dragging. Pointer motion/release
continues outside the timeline through the editor's normal input router. Selecting
a sound reveals its inspector controls. Advanced keeps source trim and gain.
**Fade sound…** adds editable fade-in/out durations in Simple; see
[sound fades](audio_fades.md) for version4 compatibility and measured scope.

This is one shared scene/timeline and one output mix, not separate playback clocks.
Clips overlap additively. Preview and MP4 use the same full-length48kHz stereo PCM;
the master clock, pause/seek and explicit Dummy fallback stay unchanged. Sources
retain their sample rate and mono/stereo channels. Mixing resamples from the
original samples at rational frame offsets, sums before quantization/clipping,
then clamps to PCM16. Excessive overlap displays a request to lower clip gain;
there is no hidden automatic volume adjustment. Each row has its own project-time
waveform. The editor mix waveform remains available for existing tools/tests.

## Native data and compatibility

Silent and single-clip saves retain the existing `audio` dictionary layout. Two
or more use `{"format":"studio_audio_2","clips":[...]}` within the same native
project/container. Each stable clip ID has its own start/source-sample trim/gain/
mute. Asset WAVs remain SHA-addressed and identical source bytes deduplicate in
the package. Removing all but one returns losslessly to the old single layout.
No scene/model schema or external-format exporter changes.

Current readers accept old projects. **Older Studio versions cannot open multi-
clip scenes**; their existing validation refuses the missing legacy audio identity
rather than silently discarding sounds. Use project copies with this development
version. Packed/linked HAS, cache sidecars/relink membership, recovery, lesson
snapshots, Undo/Redo and contact/physics metadata estimates include every sound.
The selected editing clip is an editor selection, not a separate audio track or
audio value applied to the whole scene. Existing single-clip internal callers
still address that selected clip; whole-scene writers use the full collection.

Bounds remain explicit:16 clips,64MiB of referenced decoded PCM, existing32MiB/
60-second WAV limit, supported PCM16 mono/stereo8–96kHz, existing project duration,
1MiB metadata/512MiB container/128member archive caps. Repeated references count
conservatively toward decoded/sample-processing budget. Unknown versions,
duplicate IDs, unsafe paths, invalid timing/gain, incomplete samples, over-budget
sources or bad checksums refuse without replacing the current scene/last save.

## Verification and remaining work

`python tests/verify_multi_audio.py` runs domain/container checks and actual five-
native world editing, hardware playback capture, packed/linked HAS, fresh-process
recovery/lesson readers and two movies. Its report is
`output/multi-audio-verification.json`. Source hashes guard the complete run;
original WAV/native HAS bytes stay unchanged. Full-verifier integration runs this
after producing the native contact fixture. Current full-regression status lives
in the dated progress memo; old full-review results do not certify new source.

Technical basis: Godot's [WAV PCM stream](https://docs.godotengine.org/en/4.6/classes/class_audiostreamwav.html)
and [audio synchronization](https://docs.godotengine.org/en/4.6/tutorials/audio/sync_with_audio.html)
documentation; actual pinned4.6 Windows tests determine behavior here.

The base multi-clip increment does not add splitting,
pan/loops/effects/recording, animated gain, ripple editing or audio buses.
Mix rebuilding is synchronous and bounded; long/dense responsiveness needs work.
Physical mouse/tablet comfort and subjective hearing remain artist acceptance.
The normal installation, earlier review candidate and frozen web package remain
separate. The complete specification/addendum goal remains active.

Add audio places a new sound at the playhead frame where the file picker was opened.
Its title shows that frame. Import and placement form one Undo action. At the end
boundary choose an earlier frame, since no exported frame begins at that boundary.
