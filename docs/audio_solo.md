# Solo sound clips

Select a sound clip and enable **Solo audio clip** in Properties. Preview and final
export play only the marked sound clips in the current scene. More than one clip
can be soloed. **Mute audio** still silences a soloed clip. Turning off the last
Solo restores the other sounds without changing their mute flags.

Solo is scene-local: a parent scene's Solo also suppresses its nested sequence
sound. Solo inside an editable child changes that child's mix; it does not mute
independent parent sound. This matches the existing nested scene composition.

Each toggle is one authored Undo step and marks the project changed. Solo survives
packed/linked HAS and recovery. Gain, trims and fades keep their existing behavior.
It does not alter source WAV/MP3/Ogg files, camera keys, world objects or artwork.

A clip with a stored `solo` boolean uses the versioned `studio_audio_5` audio
collection. It retains the existing trim/fade fields. Unknown/unversioned and
non-boolean values refuse before replacing valid project data. Older Studio
builds reject the new collection instead of silently ignoring Solo. Projects
without Solo retain their earlier audio representation; clearing the last Solo
field returns to that representation. HAS remains the existing ZIPv1 container.

Current private-display verification passed38domain checks,25cross-runtime
validation cases,22actual writer checks,22packed/linked/recovery reader checks,
and30HAS container regression tests. Original audio and manual HAS bytes stayed
unchanged. Packed/recovery readers had original sound files and writer cache
offline. Decoded H264/AAC1080p24 output measured the isolated1000Hz voice at5955
amplitude, with1500Hz peer and500Hz child below1; the trimmed tail was silent.
The existing non-solo sparse/nested/fade suite also passed its43domain checks,
actual editor/cold-reader assertions and unchanged decoded levels. This does not
certify a physical sound device, subjective listening or Windows installation.
