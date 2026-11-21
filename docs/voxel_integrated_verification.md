# Integrated bounded-room lighting verification

Qualified source: `28db0902825721626b17b218aa2a4554ab6da552`, tree
`f8ba87293d1f2e3bfce2087535507779c1b4af22`. This receipt adds no runtime changes.
All 1,212 functional files (10,336,157 bytes) match the independently fetched
source before and after graphics. See the compact
[evidence](benchmarks/voxel_integrated_verification_2026-11-21.json).

The primary ran `python -B tests/verify_scene_lighting.py --voxel`: **68/68**.
I independently inspected its report, source hashes, log files and private-job
receipts. Both themes show actual moving-model indirect occlusion: sampled red
illumination changes 22.3828 → 18.8672 → 22.3828. Live Camera Focus comparisons,
portable HAS cold reopen and bounce-patch comparisons have zero mean difference
at frames 0, 1 and 3. Scene Setup also shows the occlusion. The moving movie is
Neon's four-frame H.264, 1920×1080 at 24 fps; its source PNG comparisons are exact.
Classic's moving movie was not separately exported by that test.

On the same source, I ran `python -B tests/verify_voxel_empty_rebake.py --graphics`:
**22/22**, actual exec21816, exit0. In Neon and Classic, a successful real bake
followed by empty bounds clears old data and stays invisible through later syncs.
Actual movie export returns the actionable room error and creates no MP4. Undo
performs a fresh bake with distinct data; export then succeeds. Both recovery
movies probe as two-frame H.264, 1920×1080 at 24 fps. No further source fix was needed.

These were serial runs on the existing private desktop launcher, Godot4.6
Forward+ and Intel Arc140V. All three jobs/desktops closed, with no foreground
child observed and no script/error/leak messages in inspected logs. GPU ownership
was explicitly released to the primary after exec21816 was reaped. Private media,
generated assets and binaries remain in ignored output folders.

Launch `python run.py --forward-plus`, choose Lit, then Lights → advanced indirect
lighting → bounded-room VoxelGI. Fit the room to the static environment and bake.
The project stores bounds/quality/strength, regenerating bake data on reopen.
Compatibility keeps direct authored lights; VoxelGI requires Forward+.

The native bake early-return guard and empty-room guard are already integrated in
28db0902. Adopt only this documentation/evidence commit; do not replace the
primary's app, renderer, numeric-editor or runtime files. Existing CPU42/18
results establish the complementary deterministic failure paths; the GPU68/22
results establish their physical and export paths. The separate Full5d pass does
not qualify newer VoxelGI source.

This is coarse voxel indirect illumination and moving occlusion, not path tracing
or exact contact shadows. One bounded fixture at 64 subdivisions and one GPU are
qualified; arbitrary maps, multiple probes and bone-deformation occlusion remain
unqualified. Static geometry edits require Rebuild. Unlit/custom materials retain
their documented limitations; no materials or saved model data are replaced.
The next practical increment is a measured 128-subdivision comparison on a second
bounded room, including animated bone deformation and thin-wall leakage, before
expanding probe count or automatic placement.
