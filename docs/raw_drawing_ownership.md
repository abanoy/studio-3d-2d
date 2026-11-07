# Incompressible adaptive drawings

Adaptive Open now gives incompressible decoded artwork a registered raster owner,
just as it does compressed artwork. Previously the raw fallback returned an eager
Image outside the document registry. Even though its pixels stayed allocated, the
soft budget reported zero owners and zero bytes for that drawing.

Each record receives its own editable Image resource with copy-on-write pixel
storage. The counter conservatively charges each logical owner's decoded size;
it does not infer shared physical pages or process RSS. Compressed and raw reads
retain the same checksum and independent source-preservation rules. The explicit
eager API and small-project eager policy are unchanged.

When raw artwork cannot compress, an idle release attempt reports `incompressible`
and keeps both the owner and its charged bytes. It never substitutes blank pixels
or reports a successful release. The 64 MiB target remains soft, and the 32-cel cap
is unchanged. Legacy eager images, clipboard, history tiles, derived/GPU resources
and global admission remain separate accounting work.

Focused checks cover two noisy independent owners, exact decoded bytes, conservative
accounting and failed cooling without pixel loss, alongside the prior integrity,
edit isolation, nested loading and legacy-reader assertions. The full app fixture
can now exercise noisy full-HD artwork through the existing unweakened brush,
Undo/Redo, save/reopen, crash recovery, preview and export checks:

```sh
python tests/verify_cel_raster_reader.py --isolated-display :107 --auto-open --noise-art --output /absolute/new/result
```

Use an owned private display; the number above is an example. Native hardware and
Windows acceptance are not established by the cloud fixtures. See
[recorded evidence](benchmarks/raw_drawing_ownership_2026-11-06.json).
