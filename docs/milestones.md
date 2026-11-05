# Milestones

| Stage | Current evidence | Remaining acceptance |
|---|---|---|
| 0 | Pinned installed engine, isolated source, Python launcher, original GLB, repeatable tests/docs | Clean Windows machine and packaged EXE/installer untested |
| Spike A | Runtime import, full-HD paint, toggle, unchanged GLB, exact repeated GPU frame, zoom/pan input mapping | Owner brush responsiveness/pen hardware |
| Spike B | 48 PNGs → 2.000s H.264; known WAV → AAC; decoded tone at frame 24 | Audible owner listening/voice test |
| 1 | Working editor slice, camera keys, held cels, undo/redo, save/reopen, silent export; own-control smoke | Owner follows README with own scene and art; wider import/corruption matrix |
| 2 | First audio increment: one WAV, offset/trim/gain/mute, waveform, actual playback/capture, save/reopen, synchronized MP4 | Drawing usability, additional audio formats/clips, owner voice test; first recovery increment tested |
| 3 | Owner-prioritized first manual FK/model increment: one character beside environment, gizmos, root/bone keys, reference exclusion, real Miku rendering/export | Pose library, more instances, full native semantics, owner posing feedback |
| 4–5 | Deferred | Explicit prioritization after earlier stages work |

The central acceptance story now has a first tested manual posing path; the full
specification and clean-machine/artist acceptance remain **incomplete**.
The room/camera/independent drawing/WAV/export subset now runs as one integration
fixture. Local regression results do not imply clean-machine or artist acceptance.


Owner-prioritized compatibility checkpoint: Source MDL/BSP/GMA/legacy-bin preparation
now feeds the shared GLB/model path. It includes native file/member UI, cancellable
isolated Blender worker, content mounts, dependency/native preservation and warnings.
Tested Reimu, gm_construct and partial shrine; see source_import.md. This is bounded
compatibility work, not completion of native rendering, physics, VMF or all formats.
