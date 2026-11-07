# Cold cel raster staging (MEM-02 foundation)

This is an opt-in storage primitive, **not yet the live editor's cel storage**.
`Storage.decode_project()` still adopts eager `cel.image` resources and the
32-cel limit remains. No project schema or saved PNG changes are introduced.

`CelRasterReader.read_cold()` uses the existing file-size, canvas, PNG decode and
optional pixel-checksum checks, then captures an independent immutable RGBA8
snapshot and releases that reader's eager decode cache. Use a separate reader for
cold staging; mixing calls intentionally discards eager reuse. Every source is
fully decoded and validated before capture. This reduces retained cold memory for
compressible pixels; it does not defer initial validation or accelerate Open.
Legacy supported image formats follow the same reader compatibility path.

The snapshot stores only base-level RGBA8 pixels. A detached conversion leaves
the original format, mipmaps, metadata and pixels untouched. Zstandard is used
only if its payload is at most seven-eighths of raw bytes; otherwise raw pixels
are retained without expansion. There is no thumbnail substitution or lossy
compression. Hidden RGB under zero alpha remains exact. Descriptor, stored-payload
and decoded-pixel SHA256 checks guard materialization, and the supported canvas
bounds determine the fixed decompression allocation. Missing or corrupt inputs
return an error, not blank replacement artwork.

The caller-owned decoded LRU defaults to two full-HD rasters (16,588,800 logical
pixel bytes). It holds weak references to snapshots and returns separate Image
resources with copy-on-write pixel ownership. Editing a returned image cannot
change a peer or the captured snapshot. The cache does not write changes back:
**a future live-cel owner must retain an edited image or capture a new snapshot**.
Eviction can only discard the cache's own decoded copies. Caller/history-held
images are outside its byte count; the count is not a whole-app memory bound.
No global cache, disk ownership or source-file dependency survives capture.

## Current evidence and costs

`python tests/verify_cel_raster_snapshot.py` runs 29 domain checks and 31 original
reader compatibility checks headlessly using the pinned engine. Add
`--benchmark all` for the larger original sparse/noise fixtures. Each fixture has
32 distinct 1920×1080 PNGs, and each of three same-process runs verifies every
materialized RGBA checksum. Measurements exclude fixture creation and report
Godot tracked CPU allocations, not process RSS, peak allocation or GPU memory.
The curated raw runs and source hashes are in
[the measurement artifact](benchmarks/cold_cel_rasters_2026-11-06.json).

Sparse drawings retain 108,751 tracked bytes after capture versus 265,496,440
for eager loading; after reading all drawings through the two-image cache the
cold run retains 16,701,779 tracked bytes. Cold capture and reads are slower.
Incompressible seeded noise receives no meaningful memory reduction and has
additional checksum/compression costs. Do not generalize sparse compression to
photographic or densely painted artwork, or use it to raise the existing limits.

These tests cover cold ownership, exact alpha/color, bounded decoded caching,
source independence, eviction/rehydration, cache-hit corruption refusal, invalid
sizes/checksums, raw fallback and the unchanged eager reader. They do not establish
live brush/fill/selection Undo, packed/cold app adoption, crash recovery, GPU
preview/export parity, device performance or acceptable scrubbing latency.

## Integration work still required

Before changing production cel representation, migrate the audited consumers:

| Consumer | Required ownership contract |
|---|---|
| Drawing composite, preview cache, onion, sampler, sequence render | Borrow materialized pixels for a frame without pinning every cel. |
| Brush, fill, selection/transform and pixel Undo | Pin one authoritative editable Image before mutation; preserve its identity through Undo/Redo. |
| Clipboard and affected-cel history | Snapshot the intended content; preserve peers, stable owner/layer addresses and correct memory charges. |
| Cel timing signatures and sequence/history accounting | Use stable identity/revision and size metadata without decoding every inactive cel. |
| Save, recovery and nested scenes | Stream exact source pixels with independent worker/cache ownership; keep atomic adoption and late-corruption refusal. |

The production audit found direct Image access in these paths, including timing
signatures that inspect every cel and stroke commands that retain Image identity.
Replacing dictionaries with uncoordinated lazy reads would lose edits or pin all
pixels again. This foundation therefore remains explicitly staged. Next implement
the authoritative live-cel accessor/write ownership contract, then verify actual
brush/fill/Undo, onion/sampler, parent/child scenes, normal packed saves, cold
readers, abrupt recovery and preview/movie equality before enabling cold storage.
Keep MEM-02 partial and resource limits unchanged throughout that migration.

## Authoritative live-cel owner contract (staged)

`CelRasterOwner` now provides the next migration primitive. A cold owner references
an immutable snapshot and a caller-owned decoded cache. A read returns independent
pixels without pinning them. Explicit `pin()` makes one Image authoritative and
retains its exact identity, so existing pixel Undo commands continue to address
that Image even after decoded-cache eviction. A hot owner read borrows that
writable authoritative Image; ordinary readers must not mutate it.

Tokens contain stable owner identity and the live pixel revision. Identity/byte
queries do not hydrate cold pixels. Pinning unchanged pixels alone does not
advance the token. Selection may adopt an already borrowed image only with the
current token, exact dimensions/format/pixels and original revision; stale or
modified previews refuse atomically. An owned hot Image is never automatically
cooled while legacy Undo may still mutate it. A new immutable snapshot can be
captured for a worker/save without changing subsequent live edits.

Drawing now exposes `image`, `edit_image`, `raster_token` and `raster_bytes` accessors.
Its real composite accepts staged owner records or legacy eager records, and
existing-start insertion clears stale owner representation when replacing pixels.
A record containing both `image` and `raster_owner` refuses as ambiguous. Missing
or corrupt cold pixels return null/error instead of substituting a blank drawing.
Callers must propagate that failure before enabling production adoption.

The owner adds 22 headless checks to the verifier (82 total): brush mutation and
pixel Undo/Redo retain exact identity across cache eviction, cold peers remain
unchanged, worker snapshots freeze content, selection pinning rejects stale/
modified pixels, metadata queries remain cold, eager compatibility remains exact,
and actual Drawing composite agrees across cold/eager hold and opacity paths.
These exercise the domain contract, not a GUI selecting or editing adopted cold
cels. The other direct Image consumers in the table above still need migration.

## Metadata consumer migration

Timing-editor signatures now use the stable raster token, so opening a drawing
menu or checking a drag context does not decode every inactive cel. Affected-cel
history strips transient ownership from serialized metadata, recognizes identical
owner identity without reading pixels, and materializes only when independent
owners need an exact pixel-equality comparison. Legacy whole-number JSON timing
and eager Image identity comparisons retain their behavior.

Recovery reservations, removed-layer charges and retired sequence-history charges
use decoded byte metadata without materialization. They deliberately reserve full
uncompressed pixels, keeping the previous conservative budgets. Compression is
not used as permission to raise caps or undercharge retained history. Retired
sequence rasters are still charged once per command and excluded when live.

The metadata migration adds 14 checks (96 total domain checks). A 32-cel cold
fixture stays at zero decodes through timing signatures, Cut Undo/Redo, root/child
recovery reservations and actual sequence-history budget passes. Independent
rebuilt-owner equality decodes on demand, and editing one owner changes only its
revision token. This advances consumer migration; remaining render/edit/save
consumers and production cold adoption are still unfinished.

## Readonly render consumer migration

Preview, onion guides, color sampling, tutorial ink observation, recovery-preview
capture and final renderer now use checked raster access. Nested rendering uses
stable owner/revision picture signatures and checked composites on rebuild.
Drawing composites preserve the original eager pixel path while returning a
specific cel/frame error for unreadable pixels. Movie and transparent-PNG render
loops propagate those errors and preserve completed outputs.

The preview cache keeps weak logical source identities, so a held frame reuses
its derived picture even after the decoded cold cache is cleared. Active cold
payload integrity is checked before a preview cache hit. Onion uploads similarly
follow stable logical revisions rather than transient materialized Image IDs.
Sampler errors preserve the selected pen color. On preview failure, playback
stops, editing is guarded, and the app explicitly labels its retained last valid
preview. A later valid preview clears that error.

`python tests/verify_cel_raster_read.py --isolated-display :106` runs the 131 domain
checks and a private GPU fixture that explicitly injects cold owners into four
original held cels. This is not enabled loader adoption. It checks exact eager/
cold final frames, preview, onion textures, held-cache reuse, actual raw sampler,
movie input and transparent PNG equality, independent original assets, unpinned
readonly owners, bounded decoded cache, and corrupt-preview/PNG/movie refusal.
Independent media inspection checks actual1080p24 H264/AAC,48frames/2seconds,
frame24 cue timing and every PNG's dimensions. See the dated read-path receipt.

Live brush/fill/selection/clipboard mutation and save consumers still require
migration. Normal Storage loading remains eager until those paths and actual
cold-adopted save/load/Undo/recovery/latency acceptance pass. Do not enable cold
project adoption or increase limits based on these readonly checks.

## Write pinning and streamed persistence (staged)

Brush contact now pins the active cel's authoritative Image only when painting
starts; a zero-pressure tablet press does not hydrate an existing cold cel.
Selection and transform previews keep an independent read image and do not pin
until Apply verifies the current owner token and borrowed pixels. Fill similarly
reads detached worker inputs and pins at commit. Preview candidates explicitly
replace their copied dictionary's representation without mutating the live owner.
Clipboard Copy/Cut/Split materialize independent clipboard/right-half pixels while
preserving the untouched cold source; affected-cel Undo keeps stable ownership.

Save reads one cel at a time through the accessor, validates the supported canvas
and RGBA8 format, hashes/writes exact pixels, and keeps inactive sources cold.
Normal canonical PNGs, schema selection, packing and checkpoint journaling remain
unchanged. A missing/corrupt or unsupported source returns before manifest commit.
Loading serialized data discards the transient `raster_owner` field before
installing validated PNG pixels, so JSON cannot shadow the authoritative image.

`python tests/verify_cel_raster_write.py --isolated-display :106` runs 138 domain
checks plus a fixture-injected cold editing writer and fresh packed reader. The
writer exercises real brush/fill/selection/transform/clipboard Undo/Redo, normal
packed Save, actual checkpoint and movie, and a late corrupt-cel Save refusal.
Its untouched fifth cel stays cold through Save and recovery. The fresh process
opens that compatible HAS with the writer cache physically unavailable and
compares five complete final frames and all authored RGBA hashes. Independent
ZIP checks exclude transient owner/pixel-revision fields; media inspection checks
48 H2641080p24 frames, AAC and the authored one-second cue. Readonly cold adoption
is still injected by the test; the normal loader/fresh reader remain eager.

Cold loader adoption, its startup/recovery paths, nested scenes and latency gates
remain next. This does not increase the 32-cel limit or certify physical pressure
hardware. Edited owners stay hot while legacy pixel Undo may retain their Images.

## Adaptive loading (opt-in acceptance stage)

`CelRasterReader.read_adaptive` now captures compressible decoded pixels into
shared immutable snapshots and returns a distinct owner per cel. Its decode
context retains the compressed snapshot rather than every decoded Image.
Identical encoded PNGs share one validated capture, while every declared file is
still opened, size/header checked and fingerprinted. Supplied pixel checksums are
checked on every record, including aliases/cache hits. Incompressible pixels use
the existing independent eager Image/COW backing, avoiding cold-cache work on
subsequent reads. Legacy non-PNG loaders preserve their validated pixel behavior.

`Storage.load_project(folder, manifest, true)` selects this mode explicitly; its
default remains eager. One context serves root and child scenes. Studio has an
internal `cold_cel_loading` acceptance flag, currently false, which routes ordinary
directory/HAS Open and recovery through that same loader. No user-facing settings
or project fields are added. Initial PNG decoding/validation remains complete
before adoption; only later pixel materialization is lazy. This is memory cold
storage, not deferred validation or a claim that Open never decodes PNGs.

`verify_cel_raster_adaptive.py` checks 165 domain cases and the 16-case independent
PNG corpus in both modes. Adaptive-specific checks cover repeated/aliased files,
missing/changed files, malformed checksums, canvas/path checks, independent paint,
raw fallback, captured-corruption refusal, legacy JPEG and nested shared decode.
`verify_cel_raster_write.py --adaptive-open --isolated-display :106` additionally
uses actual ordinary Open instead of injecting owners (30 writer/12 fresh-reader
checks). `verify_cel_raster_reader.py --adaptive-open --isolated-display :106`
passes 31 domain,16 PNG,19 writer,5 fresh-reader and6 normal startup checks, with
an actual SIGKILL and original project/WAV/writer cache unavailable at startup.
The observer uses unchanged production startup, not a recovery bypass.

The tests access stable raster identities and checked pixels rather than private
`cel.image` fields; eager identities and pixel-Undo Image identity remain checked.
An initial adaptive-edit launch omitted switching the normal Open's Scene mode to
Draw. Diagnostics identified the missing precondition; unchanged edit assertions
pass after selecting Draw. No product behavior or acceptance boundary was relaxed.

Three-run owned 32-record measurements are in
[the adaptive receipt](benchmarks/cel_raster_adaptive_2026-11-06.json):

| Fixture | Eager loaded tracked bytes | Adaptive loaded tracked bytes | Adaptive after sequential reads |
|---|---:|---:|---:|
| 32 distinct sparse PNGs |265,512,940 |185,883 |16,777,683 |
| 32 records of one PNG |8,332,312 |55,458 |8,351,334 |
| 32 distinct incompressible PNGs |265,512,940 |265,512,940 |265,512,812 |

All RGBA checksums are exact. Repeated PNGs still decode once (31 cache hits).
Noise keeps zero cold owners and zero decoded-cache bytes, with no memory saving;
attempted compression makes its load slower. Sparse sequential materialization
also costs more than eager reads. These are tracked CPU deltas, not peak/RSS/GPU
or whole-app latency measurements. Do not infer universal timing or compression.

Default adoption is still disabled pending actual nested cold rendering and
app-level load/seek latency acceptance. The 32-cel cap stays unchanged, and edited
owners remain hot under legacy pixel Undo. Larger/dense-project budgeting and
hardware/native acceptance remain incomplete; MEM-02 stays partial.

## Nested acceptance and measured app latency

The opt-in adaptive nested suite now passes 224 checks:106 graph,9 audio,8 storage,
23 runtime,48 writer,25 fresh reader and5 normal startup. It includes graph3 masks,
looped/shared instances, child brush pin/Undo/Redo through normal editor navigation,
exact restored parent composite, packed/linked/active-child saves and recovery
following actual SIGKILL. The procedural skinned actor remains editable; this does
not establish fidelity for unavailable native assets. Child audio decodes at
0.2500208s versus the authored0.25s. See
[the nested receipt](benchmarks/cel_raster_nested_2026-11-06.json).

`verify_cel_raster_app_benchmark.py --isolated-display :106` measures three pairs
of ordinary eager/adaptive app Opens,32 distinct-frame seeks and10 held-frame
seeks on an empty 3D world with32 original sparseHDcels. All preview RGBA is exact.
The benchmark includes two UI frames and GPU presentation in seek time, and does
pixel verification afterward. It is not a physical tablet, native scene, noisy
artwork, peak-memory or artist-comfort acceptance test.

| Three-run mean | Eager | Adaptive |
|---|---:|---:|
| Synchronous Open call |1600ms |1546ms |
| Ready after layout/draw |1710ms |1686ms |
| Distinct-frame seek |52.7ms |80.3ms |
| Held-frame seek |37.5ms |36.6ms |
| Tracked allocation increase after ready |265.5MB |8.49MB |

Adaptive per-run distinct-seek p95 values were94.0,81.6 and89.8ms; eager values
were62.4,62.9 and54.9ms. Both modes rebuilt zero held composites. The tracked
increase is relative to an already initialized empty app, not absolute RAM/RSS,
peak allocation or GPU memory. Raw samples, source hashes and scope are in
[the app measurement](benchmarks/cel_raster_app_2026-11-06.json).

These results verify functionality and expose the cost of on-demand decoding;
they do not certify universal latency. Default adoption remains off while the
latency/compatibility policy is evaluated. Larger edited-owner/global dense-project
budgets and higher caps are still separate unfinished work.
