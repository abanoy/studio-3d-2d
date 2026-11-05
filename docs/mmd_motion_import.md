# Import an MMD motion

In desktop Studio, select an MMD-prepared character and choose **Import MMD
motion…** in Model / pose properties. Select a `.vmd`, choose a start point in
source seconds and a length in scene frames, then **Prepare motion**. Review the
matched controls and destination frames before applying. The current playhead
is the destination start. Import does not change the shot length or camera keys.

The imported interval uses ordinary editable HAS body and expression keys in a
standard movable timeline block. Move/copy/split it with the existing animation
tools. One Undo restores the whole import. Native file identity, SHA256, source
start/rate and original destination range stay in model metadata; playback and
packed HAS use the normalized keys, not an external VMD playback engine.

This increment accepts an empty range, a range inside one existing block, or an
extension of the final block. It refuses ranges that cross several existing
blocks rather than merge away their independent curves. Source ranges beyond
the motion end hold its final pose; shortened ranges omit later source motion.
Review discloses either condition. Cancel or a changed scene/rate/range preserves
the current animation and allows retry. Camera-only VMDs get explicit guidance.

VMD has no embedded frame-rate field. This adapter treats source frames as 30fps
and samples them at the scene's rational frame rate. Bone XYZ translation uses
the destination key's four native Bezier controls; rotation uses a shortest-path
quaternion slerp with its own Bezier factor. Morph amounts interpolate linearly.
The four native 16-byte interpolation blocks are used directly, including the
Z/rotation coordinates that some writers omit from the first block's redundant
bytes. See the installed MMD Tools reader/importer/exporter and its
[motion documentation](https://github.com/powroupi/blender_mmd_tools/wiki/Documentation).
[Three.js's pinned loader](https://github.com/mrdoob/three.js/blob/r171/examples/jsm/loaders/MMDLoader.js)
also documents the 30fps time conversion and separate position/rotation curves.
No third-party implementation is bundled or copied into these adapters.

Samples become linear keys on the integer scene frame grid. Between those keys,
fractional-frame interpolation is the standard HAS interpolation; the original
VMD Bezier handles are not retained as editable curves. Existing import/model
metadata and geometry remain shared with VPD/MMD/Source/VRM/other adapters.

Freshly prepared models retain [supported joint chains](standard_ik.md); their
IK controls and stepped on/off switches are baked into standard FK keys. A
disabled chain restores its captured authored FK baseline. Old prepared models
need reimporting to gain chain declarations. Native inherited transforms,
physics, camera, light, self-shadow and visibility tracks are not applied.
Counted non-model sections are disclosed in review. Morphs use
the supported raw-vertex/group resolver; unsupported groups remain skipped with
reasons. Unsupported/unreachable joint chains need manual adjustment; native
fidelity across arbitrary rigs is unproven. Legacy VMD version1 and damaged/truncated CP932 identities are
refused. No retargeting between unrelated skeletons is inferred.

Bounds: 32MiB VMD, 200000 total source records, 4096 tracks per bone/morph set,
1000000 source-frame ceiling, 1–241 destination samples, 8MiB conversion result.
Existing 32-piece/2048-control and 1MiB project-metadata budgets still apply.
Each object retains up to 32 motion-import provenance records.
Long/dense motions can exceed those budgets and are refused before commit.
Preparation and editor-side key construction are cancellable. The hidden worker
reads/converts the source; the editor builds an isolated candidate in batches
across UI frames and shows the number of prepared frames. Seeking, changing the
scene or cancelling discards the candidate without creating any Undo entries.
Only the reviewed Apply commits the completed animation. Batches target 4ms,
but each sample and final validation are atomic; this is not a hard frame-time
guarantee. Initial authored-baseline capture and result parsing also remain
synchronous. Worst-case dense rigs and a broader native motion corpus remain open.

## Verification

`python tests/test_mmd_motion.py`: nine bounded-reader/sampler checks, including
an independently installed MMD Tools reader/writer, Japanese identities,
nonlinear axes, shortest-path rotation, rational-rate conversion, camera/IK
section inventory and malformed data.

`python tests/verify_mmd_motion.py`: original authored VMD and real retained Miku
preparation, independently compared at 25 scene samples against installed MMD
Tools Bezier evaluation/BoneConverter and mathutils slerp. Maximum position
difference 1.41e-6 scene units; quaternion component-vector difference below
3e-7. The test uncovered normalization of tiny native bone-basis length
deviations; preserving the basis fixed the issue without relaxing the comparison.

The actual private-desktop app checks the file picker, range/review, stale-range
rejection, cancellation, camera-only refusal, all 25 imported body samples,
independent blink keys, one whole-import Undo/Redo, moving the complete block,
source provenance, editable independent drawing, packed HAS reopen and exact
preview/export PNG equality. Movie: H2641920x1080,24fps,48frames,two seconds.
This is authored-fixture and Miku evidence, not native IK or arbitrary VMD-corpus
certification. The existing VPD workflow is checked separately after shared-code
changes. No model/motion original is modified or distributed with the source.

`python tests/verify_mmd_motion_progress.py`: 241 destination frames through the
actual hidden Windows editor, cancellation after key construction starts,
scene-seek invalidation, unchanged original/history on both paths, a successful
retry with multiple UI frames, exact candidate parity with the synchronous API
(transaction-local clip IDs excluded), and one-step Undo. The final run used 223
batches and observed a maximum UI-frame interval of 73.241ms on this machine.
That interval includes rendering; it does not establish a universal latency bound
or performance on a dense production rig. Source hashes and the private-desktop
receipt are checked. Short workflow/HAS/movie and retained-IK tests remain separate.
