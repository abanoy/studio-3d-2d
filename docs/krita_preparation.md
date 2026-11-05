# Krita native preparation and inventory

`tools/krita_assets.py` reads bounded native ZIP/XML metadata and source identity.
It does not decode paint tiles, infer animation from a saved still, change source
layers or install a plugin. The separate [in-app importer](krita_import.md) uses
installed Krita to render reviewed layers into the existing drawing timeline.

The inventory records canvas dimensions/color profile, full original layer
attributes, content and other animation channels, exact keyframe times, FPS,
inclusive playback range and saved current frame. Namespaced XML is supported.
`mergedimage.png` is explicitly a saved still: it cannot stand in for animation.
For example one supplied file saves current frame324 outside its0–318 playback
range. Metadata and rendering must follow the intended range rather than that
cached image.

Input is local `.kra`, at most2GiB,32768members/16MiBcentral directory,4MiB per XML
and16MiBtotal XML. No archive member is extracted by the inspector. Duplicate,
unsafe/encrypted members, malformed metadata, entities, remote paths and unsupported
directories refuse. Unknown layer attributes remain data for later review. The
source is streamed for SHA256 when requested; size/mtime changes during reading
refuse. These are inventory bounds, not promises that every such source is cheap
or supported for rendering or that an external converter is an isolation boundary.

The actual nine referenced KRA files were inventoried, including six animation
parts at2560×1440/24fps with9–16layers and115–319playback frames. Two other animated
drawings have19/82layers. The current application limits (four drawing layers,
32cels,240frames, bounded HAS) must not be evaded by dropping layers, cutting the
end or loading all native pixels at once. Metadata support is not full KRA fidelity.

Installed Krita5.3.2.1 (git0619060) has a documented `--export-sequence` path.
The matching upstream source confirms batch exports stay in a separate process
instead of forwarding the request to the owner's ordinary instance. Actual hidden
help and an actual native batch export were tested without a desktop switch or
foreground child observed. Only the owned job was controlled.

The referenced30MiB `hecatia.kra` produced48frames at2160×3840/24fps in about14s.
Original SHA256 stayed exact. All PNG chunks/CRCs validated. Eight distinct PNGs
decode in the pinned Godot engine, with eight consecutive six-frame holds. This
proves an external native-rendering route; it does not prove an in-app import,
transparent compositing or editable native Krita layers inside HAS. The source has
a visible Background layer; decoded output is opaque. Do not silently remove it
or call it transparent artwork. Background/layer inclusion needs explicit review.

The next increment has now verified an explicitly reviewed transparent variant,
cancellable preparation, alpha-safe normalization, static images and fractional
source-range mapping; see [prepared raster clips](raster_clip_preparation.md).
Its inspector follows the newer animation index ahead of legacy maindoc fields.
App review/adoption/Undo/HAS integration is described in the importer guide.
Original identity is retained, oversized imports refuse before scene mutation,
and a complete import has one atomic Undo.
Longer/dense clips need cache/resource work rather than raising memory caps blindly.
KRA source-only layer editing, a packed native source, video/chroma and nested
sequences remain unresolved. No additional package/runtime was installed.

Run `python tests/test_krita_assets.py` for authored data-only ZIP/XML guards.
Owner-specific inventories/rendered art stay local outside source archives;
actual reports and private-desktop receipts are recorded in the dated memo.

Primary sources: [Krita batch export documentation](https://docs.krita.org/en/reference_manual/linux_command_line.html),
[matching startup batch routing](https://github.com/KDE/krita/blob/0619060/krita/main.cc#L706),
[native sequence export implementation](https://github.com/KDE/krita/blob/0619060/libs/ui/KisApplication.cpp#L696)
and [KRA format](https://docs.krita.org/en/general_concepts/file_formats/file_kra.html).
