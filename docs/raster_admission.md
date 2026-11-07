# Owned-raster admission

Registered drawing authorities and the document's retained decoded cache now share
a320MiB admission limit. This includes live cels, deleted drawings kept by Undo,
retired sequence drawings and the transient clipboard while they retain owners.
Hot Image authorities charge their decoded pixel size conservatively. Shared
immutable cold snapshots charge one payload per identity. Dead weak registrations
release capacity without retaining old documents.

A new owner or cold-to-editable hydration checks capacity before changing authority.
Disposable decoded-cache entries are evicted first. A refusal leaves existing
pixels, revisions, structure and history intact; it does not create a blank cel or
report a successful memory release. Copy replacement retains the previous clipboard
if staging its replacement has no room. At the bound, read-only materialization
can still serve preview/save/export, but an over-limit decoded frame is not cached.

The separate64MiB idle hot/cache target remains soft; its ordinary cooling cadence
can free capacity. The decoded cache still retains at most two full-HD frames.
The320MiB limit includes that cache and cold payloads. Projects permit up to
400 drawings across root and direct child scenes, subject to this byte admission.
32 full-HD logical authorities plus a clipboard fit the configured limit; additional Undo retention can reach it. Save and reopen a project to release
old Undo/clipboard state when needed. No artist history is silently discarded by
this admission check.

This is a persistent registered-ownership bound, not process RSS or total GPU RAM.
History tiles, derived CPU/GPU textures, engine/3D/audio resources and bounded
transient decoding/compression/readback buffers are outside this counter. A staged
Open temporarily retains separate old and incoming project contexts. Broader
resource accounting and target-device acceptance remain necessary before claiming
whole-project memory safety. See [larger projects](large_projects.md).

Focused checks use small explicit budgets to prove atomic rejection/release,
shared-cold deduplication, safe edit/borrowed-selection refusal, decoded eviction,
readability at the bound and failed incoming decode without source modification.
The default bound accepts40of48attempted retained full-HD authorities and rejects
the rest; these are independent COW Image resources, not48live app cels or measured
physical pages. The prior code accepted all48 (398,131,200logical bytes).

Actual app checks fill a test budget with live drawings and clipboard, then verify
Create/Copy/brush refusal, usable Undo/Redo and packed Save/Open without pixel loss.
The existing32cel noisy-art and cold-edit workflows check full GUI/media/recovery
compatibility. Run:

```sh
python tests/verify_raster_admission.py --isolated-display :107 --output /absolute/new/result
```

Use an owned private display. See
[recorded evidence](benchmarks/raster_admission_2026-11-06.json). Native Windows,
physical hardware and global admission acceptance remain separate gates.
