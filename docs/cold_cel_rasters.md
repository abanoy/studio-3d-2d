# Cel raster ownership and automatic cold loading

Studio automatically requests adaptive raster loading when the project's full-HD
cel reservation exceeds64MiB. Eight cel records remain eager; nine exceed the
threshold. Root and direct editable child scenes count together. Aliases count
conservatively, so reservation is not unique physical memory. Small projects keep
the eager path to avoid the measured distinct-frame seek cost.

In adaptive mode, compressible drawings retain immutable lossless snapshots until
pixels are needed. Incompressible drawings retain the existing independent eager
Image/COW backing. The 1920×1080 canvas, saved schemas/PNGs and32-cel limit remain
unchanged. This policy applies to ordinary directory/HAS Open and recovery. It
does not cool newly authored or already edited cels during the editing session.

## Integrity and ownership

Every declared file is opened, size/header checked and fingerprinted. Initial PNG
decoding and supplied pixel-checksum validation still finish before live adoption;
only subsequent materialization is lazy. Identical encoded PNGs share one validated
capture across root/child scenes, with a distinct logical owner per cel. Legacy
non-PNG image loaders keep their validated pixel behavior.

Snapshots retain base-level RGBA8 pixels, including hidden RGB under zero alpha.
Detached conversion does not change original format, mipmaps, metadata or pixels.
Zstandard is retained only when its payload is at most seven-eighths of raw bytes;
otherwise the adaptive loader keeps the original eager Image/COW backing.
Descriptor, payload and decoded-pixel SHA256 checks guard materialization. Canvas
bounds determine the fixed decompression allocation. There is no thumbnail or
lossy substitution, global project cache, or source-file dependency after capture.

The project-owned decoded LRU defaults to16,588,800 logical pixel bytes (two full-HD
rasters). Sources are weak and callers receive separate resources/COW storage.
Caller/history-held images, derived preview/opacity images and GPU textures are
outside that count; it is not a whole-app memory bound.

A cold read does not pin editable pixels. Brush contact, fill commit and selection/
transform Apply explicitly pin one authoritative Image. Pixel Undo retains that
exact Image identity across cache eviction. Edited owners stay hot while legacy
pixel commands can mutate them. Selection adopts borrowed pixels only with the
current token and exact format/dimensions/content. Zero-pressure presses and
previews do not pin cold sources. Clipboard copies/right halves remain independent.

Timing signatures and memory/history accounting inspect stable owner/revision and
byte metadata without decoding inactive cels. Recovery and retained-history budgets
still reserve full decoded sizes conservatively. Compression does not authorize
larger limits or undercharging retained history.

## Rendering, saving and errors

Preview, onion, sampler, tutorial ink observation, recovery-preview capture and
final rendering use checked accessors. Preview keeps weak logical identities,
reuses held composites after decoded-cache eviction and checks active cold payload
integrity before a hit. Nested render signatures preserve shared/held behavior.

Save reads one cel at a time, validates canvas/RGBA8, and hashes/writes exact pixels
without pinning inactive sources. Canonical paths, normal packing and checkpoint
journaling remain unchanged. Serialized `raster_owner` values are discarded before
validated loading; a record cannot contain two authoritative representations.

Corrupt or missing pixels return an error rather than blank replacement artwork.
Movie/PNG errors preserve completed outputs. A preview error stops playback,
guards canvas editing and labels its retained last valid picture; a valid preview
clears it. Sampler errors keep the selected pen color. A failed save keeps the
previous manifest and manual HAS. A saved checkpoint may remain valid even when
its separate preview cannot be prepared.

## APIs and verification

`Drawing.image/read_image/edit_image/raster_token/raster_bytes` accept eager or
owned records. `replace_image` explicitly replaces representation for previews or
new pixels. Callers must propagate checked read failures.

`CelRasterReader.read` and default `Storage.load_project` remain eager API paths.
`read_adaptive` exposes the owned path; `read_record` follows its context policy.
`Storage.load_project(folder, manifest, true, threshold)` enables adaptive above
the supplied reservation, or forces it at threshold0. Studio uses64MiB. The older
`read_cold` API remains a staging primitive that clears eager reuse per file; use
the adaptive path for repeated-PNG sharing. No personal/project settings UI or
persisted render policy is introduced.

With pinned tools and an explicitly provisioned private Linux display, run:

```sh
python tests/verify_cel_raster_snapshot.py
python tests/verify_cel_raster_adaptive.py
python tests/verify_cel_raster_reader.py --auto-open --isolated-display :106
python tests/verify_cel_raster_write.py --adaptive-open --isolated-display :106
python tests/verify_sequences.py --adaptive-open --mask-recovery --isolated-display :106
python tests/verify_cel_raster_app_benchmark.py --isolated-display :106
```

The display number is an example, not shared-desktop authorization. Windows uses
the existing private-desktop launcher. Source-hashed scoped receipts are in
[benchmarks](benchmarks/cel_raster_policy_2026-11-06.json).

The176 domain checks include ownership, cache bounds, exact alpha/color, corruption,
non-hydrating accounting, streamed-save refusal and64MiB boundaries. The independent
16-case PNG corpus passes eager/adaptive (gray/indexed/RGB/GA/RGBA,8/16bit,gamma/sRGB,
Adam7). The automatic32cel suite passes78checks including actual SIGKILL and normal
startup with original project/WAV/writer cache unavailable. Explicit adaptive GUI
editing passes30writer/12reader checks; nested graph3 acceptance passes224checks
with child brush/Undo/Redo, shared instances, masks, editable procedural rig,
packed/linked/active-child saves and normal startup recovery. Existing small-project
clipboard/history154checks pass. These suites overlap; do not add them into a
unique overall coverage count or infer native fidelity from procedural fixtures.

## Measured tradeoffs and remaining work

Three-run reader allocations for32originalHDrecords:

| Fixture | Eager loaded tracked bytes | Adaptive loaded | Adaptive after sequential reads |
|---|---:|---:|---:|
| Distinct sparse PNGs |265,512,940 |185,883 |16,777,683 |
| Repeated PNG |8,332,312 |55,458 |8,351,334 |
| Distinct incompressible PNGs |265,512,940 |265,512,940 |265,512,812 |

All RGBA checksums are exact. Repeated PNGs still decode once with31hits. Noise
has no memory saving and compression attempts make its load slower. See
[adaptive raw runs](benchmarks/cel_raster_adaptive_2026-11-06.json).

The actual app benchmark used32distinct sparseHDcels and an empty3Dworld on private
software GL. Three-run Open means:1600ms eager/1546ms adaptive; ready1710/1686ms;
distinct seek52.7/80.3ms; held seek37.5/36.6ms. Adaptive per-run distinct-seek p95s
were94.0,81.6,89.8ms. Both rebuilt zero held composites. Tracked increases after
ready were265.5MB/8.49MB relative to an initialized empty app, not absolute memory.
Seek times include two UI frames/GPU presentation; pixel checks follow timing.
See [app raw runs](benchmarks/cel_raster_app_2026-11-06.json) and
[nested evidence](benchmarks/cel_raster_nested_2026-11-06.json).

These are scoped CPU allocation/time results, not peak/RSS/GPU, hardware, noisy-app
or artist-comfort certification. Cold seeks are slower; the small-project eager
policy preserves their existing path. Edited-owner/global dense-project budgets,
higher caps and device/native acceptance remain unfinished. MEM-02 stays partial.
