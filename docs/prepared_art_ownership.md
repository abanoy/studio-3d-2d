# Prepared artwork and lesson loading

Krita and video review now decode each prepared PNG into an admitted raster owner
as it arrives. Compressible artwork stays cold; raw fallback is charged by the
shared ownership budget. Existing drawings, pending artwork and the accepted layer
use the same document cache. A new empty project adopts its staged cache only when
the user accepts the layer. Cancelling releases staged owners and reader entries.

The PNG's captured encoded SHA is checked again inside the bounded read before
decoding or cache reuse. Preview uses the integrity-checked drawing accessor.
Commit rechecks source identity, scene state, slots and owner/cache consistency;
it preserves one layer Undo action and exact editable pixels. The preparation
phase displays progress and Cancel while drawings are decoded. A failed admission
or source check leaves existing scene/history and the previous source file intact.

The former per-import sum of eagerly decoded frame sizes is replaced by admitted
retained storage. The encoded preparation budget remains256MiB, the registered
owner/cache limit remains320MiB. Projects now permit up to400 drawings across
root and direct child scenes, subject to byte admission. Native canvas and timing
are captured as before. See [larger projects](large_projects.md); the original
prepared-owner receipt below records the earlier32-drawing checkpoint.

Lesson Previous/Continue now inspect only bounded editor UI metadata before calling
ordinary project Open once. That Open still validates all project metadata/assets
and prepares render state before installation. Invalid editor containers refuse
before Open; complete-project failures keep their ordinary error and old state.
The removed eager preflight no longer duplicates every drawing in a lesson snapshot.

Checks cover exact captured-file identity, cold prepared review, cache transfer,
Cancel releasing weak owners, over-budget preparation without partial installation,
Undo/Redo, packed/cold Open, checkpoint and preview/movie equality. The procedural
video suite exercises the shared importer; native Krita fidelity is not inferred.
Actual lesson Previous/Continue and all five abrupt recovery cases retain their
source/manual-save and teacher state checks. See
[recorded evidence](benchmarks/prepared_art_ownership_2026-11-07.json).
