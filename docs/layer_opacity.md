# Layer opacity

Open Draw → Layers…, choose a layer, enter **Opacity (%)**, then **Apply opacity**
or Enter. 100% is normal; a lower amount makes all of that layer's drawings faint.
The entered number is a draft until applied. One Apply is one Undo/autosave action.
Changing selection discards an unapplied amount. Visibility and opacity are separate:
Show keeps the amount; Hide keeps it too. At 0%, raise the amount before painting
or filling so that edits can be seen.

This is whole-layer setup across the project timeline. It does not change the
opacity of brush ink already stored in a cel, create opacity animation, or flatten
paint. Full-opacity layers and old projects retain their exact original output.
The four-layer/32-cel bounds remain. Normal Undo/Redo, packed/linked HAS, recovery,
lesson snapshots, fill boundaries and final PNG/MP4 use the same amount. Onion
guides multiply their own guide strength by the active layer's opacity and hide at
zero. Source pixels stay unchanged.

The optional layer `opacity` value is a finite number in [0,1], default 1 when
absent. Writers omit it when returning to normal through the UI. Storage validates
before writes or replacing the live project; invalid opacity cannot qualify a
manifest as a good backup. Project schema1–4/HAS ZIPv1 remain unchanged. Older
Studio builds ignore this additional field, so use this updated Studio to reproduce
faded projects. This is additive read compatibility, not an old-binary rendering
guarantee.

Straight RGBA8 color is retained and alpha becomes `round(source_alpha * opacity)`.
The existing native Image compositor supplies preview/fill/final output, avoiding
a second rendering path. At most four derived rasters (~31.6 MiB at1080p) are cached
using weak source identities and transient image revisions. A brush stroke updates
its dirty region; tile Undo/Redo updates its affected region. Full fills/replacements
and a new opacity rebuild the corresponding raster. New/Open/close clear caches.
No cache fields are written into PNG/project metadata.

Applying a new amount or first seeing a different faded cel can pause briefly;
it is explicit Apply rather than continuous scrubbing. The current fixture measures
whole-image preparation and a small patch separately; the final report in
`output/opacity-verification.json` records actual timings. Warm holds reuse pixels.
These readings exclude full UI/render latency and do not certify every hardware
or large-document workload. Dirty raster uploads and the native composition itself
retain the existing full-resolution costs.

Recovery previews still copy detached raw Images on the main thread. Their existing
CPU worker resizes first, then applies the captured amount at thumbnail size,
without touching scene nodes, shared caches or source Images. Recorded-take metadata
accounting includes stored opacity. Tutorial checks use the actual faded pixels,
rejecting zero-opacity layers and paint that rounds to fully transparent.

Run `python tests/verify_opacity.py` for alpha/cache domain checks and actual hidden
Windows controls, brush/tile history, fill, onion, save/recovery/thumbnail and MP4
checks. See the latest progress memo for actual completed regression/save status.
Opacity animation, blend modes/groups, larger lazy-loaded documents and physical
tablet/artist acceptance remain unfinished.
