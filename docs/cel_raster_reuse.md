# Reopening repeated drawing rasters

Projects with multiple cel records containing the same encoded PNG now decode
those pixels once per project load. Every cel still gets a distinct Image
resource. Godot shares the lossless pixel storage until an edit needs a writable
copy. Painting, filling, Undo or editing one cel leaves its peers independent.
Parent and child scenes share the reader context; the context dies when decoding
finishes. It retains no global project cache or original file ownership.

The reader opens every declared file, checks its size before allocating the
input buffer, and validates PNG canvas dimensions before decoding. Reuse is keyed
by a computed SHA256 of captured PNG bytes. A supplied decoded-pixel checksum is
still checked for each cel, including cache hits. Missing/changed duplicate files,
wrong dimensions, malformed checksums and unsafe paths refuse the project before
live adoption. Legacy directory image formats keep their existing loader behavior.
The existing32-cel/shared-sequence and32MiB-per-cel limits remain unchanged.
No stored fields, schema versions, path rules or source images change.

For an original32-cel1080p fixture referencing one PNG, three-run mean Open time
changed from1578.915ms to50.456ms. Tracked incremental load memory changed from
265500196bytes to8372804bytes. Editing one cel then added8294432bytes while all31
peers retained exact RGBA and all32Image identities stayed separate.

A separate32-distinct-PNG fixture retained exactly265500964tracked bytes in both
readers. Its recorded means were1573.655ms before and1659.263ms after, about5.4%
slower. This optimization targets repeated encoded rasters; it does not solve
memory growth for unique drawings or implement lazy loading. These are tracked
Godot CPU allocation deltas, excluding fixture creation and post-load edits;
they are not whole-app RSS, GPU memory or universal timing claims. Raw runs,
source hashes and scopes are in the
[measurement artifact](benchmarks/cel_raster_reuse_2026-11-06.json).

Run `python tests/verify_cel_raster_reader.py --isolated-display :103` with an
explicitly provisioned private Linux display. `--output /absolute/new/folder`
keeps proof outside the checkout. Windows uses the existing private launcher.
The final run passes31domain checks,16original PNG compatibility cases,19actual
Studio checks,5cold-reader checks and6normal startup checks after actual SIGKILL.
The PNG corpus compares captured-buffer decoding to both the old file loader and
independent mathematical RGBA: grayscale1/2/4/8/16-bit, indexed transparency,
RGB/gray-alpha/RGBA8/16-bit, gamma/sRGB metadata and Adam7 interlacing.

Actual painting/Undo/Redo changes only cel7 among32, including exact GPU preview,
normal packed save/reopen and known-frame movie input. Four invalid late-cel
projects preserve the installed document/history. Cold packed readers and normal
startup succeed with original source project/WAV and writer cache unavailable.
The48frame1080p24 H264/AAC movie decodes its frame24 cue at sample48001 versus
48000; manual HAS and source files remain unchanged. Proof:
`/workspace/has-handoff-audit/raster-reader-final-accepted/verification.json`.

The existing161check drawing-timing suite and70check kept-reference/lesson suite
also pass on the changed production code. They include a complete60second movie,
packed/linked cold readers and abrupt startup recovery across existing schemas.
Only the new PNG fixture/test invocation was added afterward; final61+16verification
and312Python tests cover that final test tree. Python has311passes and one existing
independent-MMD-reader skip. Native/device/artist acceptance remains separate.

`tests/cel_raster_reader_benchmark.gd` reproduces the repeated-PNG measurement
headlessly through `run.command()`, with a fresh output folder after `--`.
