# Independent cel IDs and directory-save filenames

Directory saves now name each raster from its layer/cel row numbers inside a new
revision directory, for example `cels/<revision>/layer_0_cel_0.png`. Document IDs
remain unchanged in the manifest. Content-addressed HAS/recovery paths continue
to use pixel hashes. No project format version or reader path rule changes.

Previously the ordinary directory writer used the cel ID as a filename. A
controlled fixture demonstrated that `../../../escaped` wrote a PNG outside the
project folder and left a manifest the reader refused. Another fixture showed
that equal IDs on separate layers overwrote the first layer's PNG and silently
lost its pixels on reopen. Both reproductions used original procedural art and
owned directories under `/workspace/has-handoff-audit`; no owner asset was used.

The new filenames are derived only from numeric row positions and fixed text.
Opaque IDs, path-looking text, Windows device names, long strings and duplicate
IDs cannot select output paths or merge raster files. This changes storage
naming, preserving the IDs rather than assigning new identities to imported data.
Existing PNGs and previous-revision backups remain readable. This fix applies to
new saves; it does not reconstruct raster data overwritten by an earlier writer.

`python tests/verify_cel_file_paths.py --isolated-display :103` requires an owned
private Linux display. `--output /absolute/new/folder` keeps proof outside the
checkout; Windows uses the existing private desktop launcher. The run passes:

- 12 headless cases: 32 opaque/duplicate-ID cels, contained filenames, exact
  ID/range/RGBA round trips, source markers, readable revision backups, rejected
  invalid later saves, unchanged content/recovery paths and legacy schema3.
- 14 actual Studio cases: equal-ID cels on two layers, painting, normal directory
  Save/reopen, exact GPU pixels, packed HAS and a48frame1080p24 H264/AAC movie.
- 4 fresh packed-reader checks with original directory/WAV and writer cache
  unavailable. Both rasters/IDs and exact final composition survive.

The movie's edited frame7 PNG equals the reopened preview; decoded frame24 sound
onset is sample48001 versus48000. Original imported PNGs, WAV and manual HAS bytes
remain unchanged. Proof:
`/workspace/has-handoff-audit/cel-file-paths-accepted/verification.json`.

The first round-trip test compared integer frame values with JSON numeric values.
Normalizing validated whole frames to integers corrected that test-only mismatch;
all source pixel and path assertions are retained. Software checks do not replace
native/physical-device or artist acceptance.

Existing raster31domain/16PNG/19GUI/5cold/6SIGKILL startup and kept-reference
19storage/25writer/14cold/5startup/7lesson suites also pass with their original
assertions. Python discovery runs312tests:311passes and one existing skip.
