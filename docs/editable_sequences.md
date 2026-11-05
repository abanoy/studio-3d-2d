# Editable sequences

Use **Sequences…** above the timeline, then **New sequence and edit…**. A child
has its own editable world, camera, drawing layers and sound. **Back to parent**
returns to the enclosing scene. Add another instance of the same asset at the
playhead to reuse its animation over another background; edits to the child
update every instance. A child composites transparently unless its geometry or
artwork supplies a background.

Each sequence row uses the existing frame ruler. Click to seek, drag to move,
double-click to edit, or right-click for controls. With the row focused, S splits
at the playhead, Ctrl+C/V copies/pastes an instance, and Delete removes it.
Removing an instance keeps the reusable definition. Remove unused definitions
through Sequences; referenced or open ancestor definitions cannot be removed.

The browser provides parent start/length, child in frame, looping, picture
visibility, sound mute/gain, and placement keys for offset, scale, rotation and
opacity. Keys support linear, hold and ease interpolation. Rotation retains full
turns. Picture visibility and sound mute are independent. Non-looping placements
must fit their source; invalid changes refuse atomically. Splitting preserves the
original placement curve and rational audio epoch rather than resampling either.

Saving from a child saves the entire enclosing HAS project. Packed and linked
projects, recovery, thumbnails, movie export and drawing-only PNG export retain
the graph. Recovery and ordinary reopen restore the active child and frame;
selection and temporary navigation views are live editor state. Each editor has
its own Undo context, with one shared history budget. FPS is shared by all scenes;
local durations are independent. An invalid duration change leaves everything
unchanged.

## Data and resource contract

Projects with editable sequences use project schema6 and `studio_sequences_1`.
The HAS container version remains1. Older Studio versions reject schema6; projects
without sequences retain their existing schema. The root graph contains shared
asset definitions and ordered clip lists. Child scenes use the ordinary schema4/5
world, camera, drawing, audio and palette structures. Nested references use IDs
in one flat graph; cycles and more than four nested asset levels are rejected.
`studio_sequence_editor_1` records the active child/frame separately from root time.

A clip stores parent start/duration, child source/time windows, placement key
window, loop, picture visibility, independent sound mute/gain and placement keys.
The internal time/key windows preserve split curves and fractional sample phase.
Source windows are bounded to one million frames; placement keys allow that
window plus the project frame bound. Child scenes remain at most240frames.
[Longer parents](extended_timing.md) support up to60seconds and7200frames with
an explicit schema8 wrapper; new children and their initial clips stay bounded.
All scenes share1920×1080 and one rational frame rate. There are at most4 shared
assets,8 clip instances and32 placement keys per clip. Limits shared across the
project are32 cels,16 source audio clips,64 world objects and16 effects; each local
scene has at most4 ink layers. Archive member, path/hash and byte checks remain.

PCM mixing uses48kHz stereo with exact rational placement boundaries, recursive
gain/mute and a64MiB mixed-cache bound. Source PCM has a separate64MiB bound.
Rendering caches one frame per asset, at most4, and uses at most8 picture/shadow pairs (16 sprites). Child pixels composite between the parent's world and ink. Transparent
viewport readbacks are converted from premultiplied alpha before CPU blending;
placement filtering uses premultiplied textures to avoid dark translucent edges.
Source images and original model/audio files stay unchanged. This is bounded
short-scene reuse; it does not establish arbitrary long-project performance.

This project-local sequence graph does not settle the addendum's OPEN independent
native model/map packaging or extension choice. Freeform masks, glow,
standalone sequence exchange and canvas transform handles remain separate work.

## Validation

`python tests/verify_sequences.py --isolated-display :99` on Linux requires an
already provisioned private dummy display and the pinned engine/FFmpeg environment.
Windows uses the existing private desktop launcher. The verifier exercises graph
validation, exact split audio, recursive alpha, actual child editing and timeline
input, shared-instance propagation, two original backgrounds, Undo, FPS/duration,
packed/linked cold reopening and real H.264/AAC decoding. It also kills its writer,
checks absent graceful teardown hooks, and launches the ordinary startup scene
to recover child context while preserving manual HAS bytes.

Fresh Linux checks use llvmpipe and dummy audio with original procedural assets.
They do not establish native importer fidelity, Windows GPU/device behavior or
artist acceptance. See the requirement reconciliation for the remaining gates.

Optional [sequence drop shadows](sequence_shadows.md) now add a reversible silhouette
effect. Enabling one explicitly promotes the graph to studio_sequences_2 while
keeping project schema6; earlier unstyled graphs keep their original format.

[Held artwork caching](sequence_cache.md) now reuses source pictures across held
exposures while keeping parent placement/shadow evaluation and marked-pixel invalidation.

[Sequence picture masks](sequence_masks.md) now add a reversible rectangular crop
or cutout before shadow generation. Enabling one promotes to studio_sequences_3,
still project schema6, with up to8 derived mask textures per runtime.
