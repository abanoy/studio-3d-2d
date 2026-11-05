# Sequence drop shadows

In **Sequences…**, choose an instance, enable **Drop shadow**, set its offset,
softness, color/opacity and choose **Apply shadow**. Disable and Apply to remove
it. The editable child, its original pixels, camera, audio and the parent world
stay independent. One Undo restores the previous style. Copy/paste and split
retain the style while repeated instances can have different shadows.

The shadow follows the child's composited silhouette, including its drawing and
visible world. It sits immediately beneath that instance in clip order. Clip
rotation/scale also transform the silhouette; offset is measured in parent canvas
pixels, so its direction stays consistent when the child rotates. Clip opacity,
source alpha and shadow opacity each multiply once. Picture visibility hides both
picture and shadow; sound remains controlled independently.

Softness0 keeps the original silhouette edge. Higher values, through32, sample
mip-filtered alpha for a soft edge with a bounded texture cache. This is a simple
2D compositing effect, not a physically projected 3D shadow or an exact Gaussian
blur. The result is cropped to the parent's1920×1080 canvas. Offset is bounded to
±2048pixels on each axis. Color and opacity are normalized RGBA. Values that do
not change in the inspector retain their exact saved precision.

Applying an enabled shadow promotes the graph to `studio_sequences_2`, still
inside project schema6 / HAS container1. Every clip then has a `shadow` field:
empty `{}` means disabled; enabled data has exactly `offset`, `color`, `softness`.
Existing `studio_sequences_1` graphs remain readable and retain their format until
a shadow is applied. Applying an already-disabled style is a no-op. Undo of the
first shadow returns to the earlier graph/format. Earlier readers reject graph2
explicitly; they do not silently omit the effect. Disabling a previously enabled
shadow restores the original picture but keeps the promoted graph version.

Packed/linked HAS, child context, recovery, nested rendering, PNG and MP4 all use
the same graph/renderer. Shadow textures share each asset's cached picture and
add mip levels only for promoted graphs. Rendering remains bounded to4 asset
frames and8 picture/shadow pairs, at most16 sprites. This does not add arbitrary
long-project caching or general drawing-layer masks/glow.

Normal close cancels new preview requests and drains active and queued render
callers before freeing their nodes. Runtime replacement similarly waits for queued
callers; a preview awaiting a retired node must finish rather than remain busy.

`python tests/verify_sequence_shadows.py --isolated-display :99` on Linux requires
an already provisioned private display and pinned Godot/FFmpeg environment. Windows
retains private-desktop receipts. The test exercises actual alpha, hard/soft edges,
Undo/Redo, UI disable and precision no-ops, source preservation, graph promotion,
copy/paste, packed/linked cold reopening, recovery, normal close and exact MP4 input.
Python and Godot share a malformed metadata corpus. A separate runtime regression
starts one active and one queued render before retirement and checks both complete.
Fresh cloud checks use procedural originals, llvmpipe and dummy audio. Native
hardware, physical-device feel and artistic shadow quality remain owner gates.

[Picture masks](sequence_masks.md) can now crop or cut out a sequence instance.
Graph3 preserves shadow fields and generates shadows from the masked silhouette.
