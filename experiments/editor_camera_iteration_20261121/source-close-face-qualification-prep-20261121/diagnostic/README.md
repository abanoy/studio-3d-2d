# Saved Youmu close-face diagnostic

SOURCE ONLY. Unparsed, unrun, no runtime or GPU qualification. This packet changes no application files and contains no model, texture, pose arrays, or private camera coordinates.

The protected saved `stuff.has` is a different model and case from Summer Sakuya's earlier expression report. It contains Youmu school, empty shape draft/base amounts, all 85 imported default morph amounts zero, saved editor frame 0, and a body draft at frame 43. Its face material is alpha blended and single sided; other head surfaces are alpha blended and double sided. Geometry and skin input sanity aggregates are in `SOURCE_INSPECTION.json`. These facts do not identify a rendering cause.

Root may place the diagnostic script in a fresh owned Studio snapshot, import that snapshot, and launch it with the existing private desktop/job wrapper and an external timeout. Do not run it in the owner's installed Studio or a shared review project. Pass exactly two user arguments after `--`: the protected `stuff.has` path and a new private output directory. That directory must not already exist. The archive pin is checked before it is opened. Only the embedded pinned GLB is written into the new private output for the normal importer; the original archive and owner project are read-only.

The script preserves saved camera orientation, FOV, far clip, actor transforms, pose dictionaries, visibility, and imported shared materials. It distinguishes playback at frame 0 from selected-actor editing at saved draft frame 43, matching the production world's explicit editing context. At each context it moves the camera backward along its own local Z by 0, 0.1, 0.3, or 1 HAS units. Each position has five independently restored captures:

- Baseline: authored material and clip settings.
- Near plane reduced to one tenth: isolates clipping sensitivity; other camera settings remain saved values.
- Face culling disabled: tests sidedness sensitivity with a private surface material copy.
- Face made opaque: tests transparency-path sensitivity with a private surface material copy. The face texture has meaningful transparent and partially transparent pixels. This control intentionally changes cutouts; it must never be treated as a suggested product fix.
- Head mesh culling margin enlarged: tests sensitivity to automatic skinned/morph bounds. The actual posed bounds query and camera-space depth interval are recorded separately.

There are 40 planned captures, two rendered frame boundaries per capture, and a 180-second internal watchdog. The Root launcher must also retain an external timeout and close the private job/desktop after completion or refusal. No authored camera key, material, model, pose, or clipping value is saved back. A fresh private world is disposed when the script exits.

Every PNG, working GLB, and `PRIVATE_RESULT.json` must remain private. The result includes private camera coordinates/depth intervals. Do not archive those into public source checkpoints. Root should visually compare matching cells, report capture count and structural preservation separately, and avoid asserting that any image difference proves a cause. If the baseline does not reproduce the disappearing face, record that limitation before changing product behavior.

Unrun limitations: exact imported `face` resource naming is checked by refusal rather than guessed; skin evaluation and frame readback must still be qualified on Windows; preview hair simulation is not driven by this minimal harness; no successful face reproduction or fix is claimed.
