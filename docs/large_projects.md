# Larger drawing projects

Projects permit up to 400 independent drawings in total across the root and direct
editable child scenes. The same count applies to Create, Paste, Split, prepared
Krita/video import, directory/packed Open, save and recovery. A rejected operation
preserves existing artwork and history. There are still at most four layers per
scene and four direct child assets.

This count is separate from the 320 MiB admission for registered drawing authorities
and retained decoded cache. Incompressible full-HD art or retained Undo drawings
can reach that byte limit well before 400 drawings. The soft 64 MiB idle target,
two-full-HD-frame decoded cache and 256 MiB encoded preparation limit remain.
History tiles, derived textures, GPU, audio, engine allocations and transient
old/incoming project overlap are outside registered ownership accounting.

Packed projects now permit up to 1,024 bounded members, while the 512 MiB total,
1 MiB manifest and existing member/path/ZIP safety checks remain. This accommodates
400 distinct drawing PNGs without relaxing aggregate payload limits. No schema is
renumbered. Older builds with smaller count limits refuse larger projects; keep
copies when moving between builds. Explicit eager decoding refuses projects whose
decoded reservation exceeds admission; normal Open selects adaptive storage.

Measured ordinary application workflow uses four layers with 100 unique full-HD
procedural drawings each. It checks independent identities, sampled exact GPU
composition, one-drawing brush changes with 399 unchanged peers, structural and
brush Undo/Redo, admission and actual packed save/reopen. On this cloud executor,
Open took 20.5 seconds, packed Save 68.5 seconds and packed reopen 21.3 seconds.
Recovery retains the 512 MiB disk budget. When a conservative decoded estimate
would refuse a large cold project, preflight measures actual PNG sizes one at a
time, including child drawings and source assets, before checkpoint writes. It
never uses the internal snapshot compression size as a persisted PNG estimate.
Over-budget or unreadable drawings preserve the previous checkpoint.

Save serialization and checkpoint creation can block the application; this is a
remaining responsiveness issue, not quiet background saving acceptance.

The16application assertions, 13 focused drawing-limit assertions, 292
raster-domain checks, 117 Python tests and clipboard/history regression passed.
Fresh packed Open passes five checks; ordinary automatic startup after actual
SIGKILL passes eight checks, with original input/cache/audio unavailable. The
writer passes seven checks, and its101-frame1080p24 H264/AAC movie has audio onset
at sample48,001 (expected48,000). Maximum observed individual process RSS/HWM was
427,520,000 bytes across the workflow; this excludes other processes and GPU
accounting. All400source PNGs match the independent original corpus. The existing
32-drawing noisy-art crash/media regression and205clipboard/history checks pass.

Run `python tests/verify_large_project.py --input /absolute/400drawing.has
--output /absolute/new/result --isolated-display :109` using a private owned
display. For the authored edit/Undo/save phase, run `tests/large_project_smoke.gd`
with a fresh output folder and a400-drawing directory project.
See [recorded evidence](benchmarks/large_projects_2026-11-07.json). The required
full verifier currently stops in a Windows-only native Krita harness on Linux;
this is recorded separately from the targeted passes. Procedural fixtures do not establish
native Krita fidelity, Windows behavior, target hardware or artist acceptance.
