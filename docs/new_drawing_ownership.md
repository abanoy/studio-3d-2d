# Owned storage for newly authored drawings

New blank/copy cels, timeline paste/split, fill-created cels and accepted prepared
artwork now join the same document-owned raster cache used by adaptive loaded
projects. Registration happens before structural history is recorded. A new empty
project creates its cache when it first accepts a drawing; no Save/Open cycle is
needed. Current drawings remain editable and are protected during idle release.

The app still enforces32cels. The64MiB owned-hot/decoded-cache target is soft:
compression runs at most once per idle second and never replaces missing/corrupt
pixels with blanks. External writable Image handles, active work and incompressible
artwork can prevent cooling. This is not an RSS, GPU, total history or whole-project
memory ceiling. Eager app Open now registers its accepted Images without compression; see
[eager ownership](eager_drawing_ownership.md). Adaptive raw fallback also
registers owned Images; see [incompressible drawings](raw_drawing_ownership.md).

`RasterOwner.from_image(image, cache)` preserves the current writable Image and
registers its logical owner. `Drawing.adopt_owner` changes only representation,
keeping cel identity/timing. Invalid cache/pixels refuse without changing the cel.
Creation/paste/fill restore the pre-edit structure on a failed adoption. Prepared
artwork stages adopted records separately before installing its layer. Its native
Krita preparation is still an external fixture/platform gate; the shared commit
path is exercised by procedural video import.

Owner-addressed pixel history can rehydrate cooled new drawings. Structural
commands retain owners rather than full writable Images, so they do not pin hot
artwork. Fill-created cels now use the existing affected-cel patch instead of
retaining the entire layer. Other layer history, global tile accounting and dense
project acceptance remain separate work; no cap increase follows from this change.

Consumers must read through `Drawing.image/read_image` and pin before writing
through `Drawing.edit_image`. Workflow test reads and fixture mutations now use
those existing interfaces, preserving the original pixel/identity/Undo assertions.
Representation-specific negative domain tests remain explicit. Broad native test
consumers were parsed after migration; parsing is not native runtime acceptance.

```sh
python tests/verify_cel_raster_budget.py --isolated-display :108 --output /absolute/new/result
python tests/verify_cel_clipboard.py --isolated-display :108 --output /absolute/new/clipboard
```

On the scoped cloud fixture, twelve fresh authored drawings previously retained
99,532,800 pixel bytes while the budget registered zero owners. They now register
all twelve. The natural idle cadence cools four inactive drawings in about3.1s,
releasing33,177,600 tracked hot bytes while retaining the current drawing. Every
new brush Undo/Redo, creation Undo/Redo and packed Save/Open restores exact RGBA.
These are tracked ownership figures on sparse art, not hardware/RSS guarantees.

See [current evidence](benchmarks/new_drawing_ownership_2026-11-06.json). MEM-01 and
MEM-02 remain partial/open for legacy/global accounting and broader acceptance.
