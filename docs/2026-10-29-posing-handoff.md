

## History continuation - Shared standard model and GMod-style manual posing
> OpenAI Codex / GPT-6, Windows desktop app, **2026-10-29 at 1530 EDT**.

- Owner explicitly prioritized imported MMD models poseable with GMod-style controls,
  reminding that MMD and GMod backsupport must feed one standard model. Added a
  source-independent studio_model_1 record/model.gd and pose_editor.gd. Both environment
  and character use the same existing self-contained GLB loader. No MMD-specific pose
  engine or native format branch. One optional model slot stands beside the environment.
- Working: searchable native bone tree and viewport joint picking; RGB rotation/move
  handles, local/world axes,15degree/0.1unit snap, axis locks, local numeric overrides,
  root uniform scale, reset, one-command drag undo/redo, Escape cancellation. Root and
  bones record explicit pose keys on the master timeline with hold/linear/ease and
  quaternion slerp. World moves account for parent rotation/scale. Existing camera,
  independent drawing cels, audio and Simple/Advanced presentation remain intact.
- No keys means a static pose. With keys, playback/export use recorded poses; unrecorded
  draft appears in Pose mode at its frame and is saved/recovered. Root position/rotation/
  scale also key. Reference-only preserves preview but excludes model from final frames;
  skeleton/handles are UI-only and never export. Temporary framed posing view can be
  explicitly saved as a camera key from Advanced. No automatic camera/pose overwrites.
- Schema3 stores managed GLB, checksum/native bone identity, working draft, root/bone
  keys and native parameter report metadata. Schema1/2 still load with no model. Binding
  validation precedes replacing live scene/model; unknown bone IDs fail safely. Changed
  source at the same path reloads the rig. Original GLBs remain byte-identical. Native
  parameter JSON and unknown fields round-trip; report >256KiB/invalid JSON errors
  instead of being silently dropped. Full native/blend bundle remains external: keep it.
- Bounds: one actor,512bones,241posekeys,128MiBGLB,1MiBmanifest. Model undo snapshots
  receive a conservative byte charge under existing history budget. No native MMD IK,
  ragdoll simulation, facial morph UI, child world-lock, bone scaling, pose library,
  additional actor slots or lossless native round-trip. Direct GMod Source/BSP/MDL
  decoding remains pending; future adapters must emit this same GLB/model contract.
  Native shader appearance still approximate. Framing uses imported mesh bounds and
  screen-drag sensitivity is provisional, not certified physical GMod feel/all DPI.
- Saved21source/test/docs files to canonical prototypes/studio-3d-2d with pre-copy hash
  conflict checks, source hash verification and backups under output/checkpoints/
  2026-10-29-152745-before-model-posing. Retained matching managed-worktree snapshot.
  Added docs/standard_model.md and refreshed README, compatibility, architecture,
  decisions, milestones, progress and credits. Original two-bone skinned box fixture
  is authored test geometry, not downloaded art. Uses existing Windows system font
  fallback for native bone names; no font or new package redistributed/installed.
- Actual canonical python -u tests/verify.py exit0:unit24, GPU spikes, editor39,
  encode fail/cancel, audio24, Dummy fallback, UI23, recovery writer/restart and pose44.
  Actual prepared Miku PMD fixture tested (126runtimebones, native 左腕 selection,
  visible skin deformation, interpolation, save/reopen, native metadata preservation).
  Pose suite also covers generic skin/root animation, exact rendered undo/redo,
  world move through rotated/scaled parent, handle hit, snapping/locks, unknown-bone
  rejection, recovery, reference exclusion and original-asset hashes.
- Actual generic and Miku MP4 exports: ffprobe H2641920x1080,24/1,48frames,2.000s each.
  Native frame24 matches exported PNG exactly; existing audio onset1.000s/RMS5658.30
  regression retained. Screenshots/projects/movies in canonical output/pose-smoke;
  miku-project is a saved local demo with room, animated Miku and separate test mark.
  Pose runner reports actual_mmd_tested true here, but explicitly skips private Miku
  fixture when absent in clean checkout; original rig checks remain mandatory.
- Iterations caught runner inferred-type, numeric Variant comparison, operation-mode
  selection and actual SpinBox scale-grid rounding issues. Fixed and rerun. Initial
  invalid-array access was a runner still in Move while checking Rotate; corrected.
  Final tests have no script errors or ObjectDB leaks. Worktree shader-cache warning
  is known; canonical final suite has none. No tablet/physical mouse comfort, audible
  listening, clean-machine or arbitrary native rig/format certification.
- No deployment/publishing, external uploads, vendor model/code copying into Git,
  GMod add-on/Lua execution, tool installation or original artwork modifications.
  Capabilities unchanged. Full specification remains open. Next: owner tries the
  model guide; prioritize posing feel/bundle persistence/morph or multi-instance work
  before claiming broader native GMod compatibility.
