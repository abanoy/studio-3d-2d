# Cel raster ownership and automatic cold loading

Studio automatically requests adaptive raster loading when the project's native
cel reservation exceeds64MiB. At1080p, eight records remain eager and nine exceed
the threshold; lower native sizes reserve their actual decoded pixels. Root and direct editable child scenes count together. Aliases count
conservatively, so reservation is not unique physical memory. Small projects keep
the eager path to avoid the measured distinct-frame seek cost.

In adaptive mode, compressible drawings retain immutable lossless snapshots until
pixels are needed. Incompressible drawings retain independent owned Image/COW backing. Accepted
eager app loads also register their owners. Native1080p/720p/540p canvases use the
same bounded pixel maxima and saved schemas/PNGs. Projects permit up to400 drawings
across their editable scenes, subject to320MiB registered admission; see
[larger projects](large_projects.md). This policy applies to ordinary directory/HAS Open and recovery. It
also covers newly authored app cels through [document ownership](new_drawing_ownership.md); edited owned cels can be cooled during idle time as described below.

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
transform Apply explicitly pin one authoritative Image. Owned pixel Undo commands retain the logical owner, scene address and tiles,
rather than a live Image pointer. They preserve writable identity while hot and
can rehydrate exact content after explicit cooling. Legacy Image commands remain
compatible and keep their strong pointer. Selection adopts borrowed pixels only with the
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

The208 domain checks include ownership, cache bounds, exact alpha/color, corruption,
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
policy preserves their existing path. Global dense-project budgets,
higher caps and device/native acceptance remain unfinished. MEM-02 stays partial.

## Edited-owner history and safe release

App history promotes a pixel command only when exactly one active owner holds its
Image. Owner-addressed Undo validates the current scene and unique live target,
checks every tile before pinning/writing, and refuses malformed/empty/out-of-bounds
history atomically. Eager legacy commands keep their existing Image behavior.

`CelRasterOwner.cool()` can now capture edited pixels without changing logical
identity or revision, then release the full Image. It refuses while any external
Image handle remains (active stroke/selection or unpromoted legacy history), when
there is no shared cache, or when pixels are incompressible. Decoded borrowed
images carry the saved revision, so a later verified selection can adopt them.
Weak-reference tests confirm the old Image actually dies. Undo/Redo can rehydrate
and cool repeatedly with exact RGBA; wrong-scene or missing targets do not hydrate.

The app stores owner-addressed pixel commands for owned cels. A project-local weak
registry includes owners retained by the current document or history without
keeping discarded owners alive. Once owned hot pixels plus decoded-cache bytes
exceed a soft64MiB target, the app attempts to cool one inactive owner per second
of idle time. It protects the current cel in each active layer and defers during
gestures, fills/transforms, playback, export, physics, dialogs and Home. A fair
cursor prevents a borrowed or incompressible owner from starving other candidates.
External Image references independently prevent unsafe release. Successful New
drops the context; refused New/Open preserves the current document context.

This is a soft target for registered owners and decoded cache. Newly authored eager
cels, raw/incompressible fallback, drawing-history tiles, derived previews and GPU
storage remain outside it. Protected, borrowed or incompressible owners can leave
it above target. Global admission/accounting and larger dense-project acceptance
remain unfinished. No resource cap is raised. The 35-check explicit cold editing writer/12-check fresh
reader verifies real cooling with Undo present and all four pixel-edit tools;
existing154legacy GUI history checks also pass. See
[the pixel-history receipt](benchmarks/cel_pixel_history_2026-11-06.json).


## Automatic idle-release evidence

The permanent verifier runs208 domain checks and a12-check real app fixture:

```sh
python tests/verify_cel_raster_budget.py --isolated-display :107 --output /absolute/new/result
```

Provision an owned private display first; Windows uses the private desktop launcher.
The fixture paints12 distinct sparseHDcels through the actual brush and naturally
idles. Five inactive owners cool in4131ms, reducing owned hot pixels from99,532,800
to58,060,800 bytes with8,294,400 decoded-cache bytes. Tracked Godot allocation
falls by41,462,025 bytes. The current drawing stays hot, all12 commands remain,
and every Undo/Redo restores exact RGBA. Active gestures defer release. Refused
New preserves context; successful New clears it. Original manifest stays unchanged.

These are scoped tracked allocations, not peak/RSS/GPU, noisy-project or physical
hardware acceptance. See [the idle-release receipt](benchmarks/cel_raster_budget_2026-11-06.json).

Registered authorities and retained decoded cache now also use
[owned-raster admission](raster_admission.md); the64MiB idle target stays soft.
