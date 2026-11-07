# 400 unique full-HD raster measurement

The storage foundation was measured with four layers of 100 unique 1920 × 1080
transparent drawings, including hidden RGB. Their logical eager pixel reservation
is3,317,760,000 bytes; that full eager allocation was not attempted. Each PNG's
initial decode validates its declared pixel SHA before becoming a cold owner.

On this cloud run:

| Observation | Result |
|---|---:|
| Unique original RGBA identities |400 |
| Retained cold payload after staging |321,920bytes |
| Tracked Godot allocation growth after staging |2,247,431bytes |
| Staging400 unique PNGs |20.003s |
| Sequential exact RGBA reads of all 400 |22.522s |
| Eight random/reverse composites with eager-source references |2.925s |
| Maximum retained decoded cache |16,588,800bytes |
| Final accounted storage after four editable authorities |41,790,705bytes |
| Maximum observed Linux process RSS/high-water sample |185,982,976bytes |
| Godot static allocation peak |108,163,971bytes |
| Whole fixture/staging/seek/oracle/media run |82.609s |

The process observation samples `/proc` every50ms and includes fixture generation
and per-frame eager comparison work. It excludes other processes and GPU memory;
it is a cloud measurement, not a portable hard RSS guarantee. Godot allocation
metrics and RSS measure different things.

Every source is read back exactly without pinning all cels. Four independent
owner-addressed tile Undo/Redo edits preserve source hashes and other drawings.
Eight full-HD composite PNGs match ordinary eager-source decoding and produce a
probed **8-frame H264 movie at 24fps**, as a
CPU-composition artifact. No app GPU/native-format/artist acceptance is implied.

The normal application still accepts at most 32 live cels at this checkpoint. This
benchmark calls the raster foundation directly; it does not establish ordinary
projects with 400 drawings, including Save/Open, UI or crash recovery. The archive still has a separate
128-member limit. A source audit also found lesson snapshot loading decodes eagerly
before calling the normal Open path; that duplicate load must be addressed before
larger lesson snapshots are enabled.

See [resource inventory](drawing_resource_inventory.md) and
[measured evidence](benchmarks/dense_raster_2026-11-07.json). Reproduce with
`python tests/verify_dense_rasters.py --count 400`. No graphical display is needed.
