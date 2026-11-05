# Optional human/map size reference

Development now offers [opt-in character height review](height_import.md) before
placement and physics. It uses uniform root scale and an explicit keep-original
choice. Partial models and uncertain proportions are protected. The audit below
remains historical; the new guide records current code and verification. Map
calibration is now available for static unattached maps through
[known-distance map sizing](map_calibration.md). Animated/attached map resizing,
contact reanchoring and existing animated-model resizing remain unfinished.

On2026-11-01 the owner requested consistent size across imported humanoids, while
preserving intentionally unusual proportions. Provide an optional human-height
choice using6feet (exactly1.8288metres) as the reference. If unchecked or declined,
do not attempt this extra stature adjustment. Existing source unit/axis conversion
is a separate operation and must not be confused with this artistic resize.
Preserve original assets and existing scenes; no silent retroactive normalization.

The user allowed a default option or explicit choice; automatic enablement and
confidence thresholds are not settled. First implementation should make the target,
measured height and uncertainty visible. Uniform scaling preserves proportions;
do not stretch bones to make legs/torso fit a template. Do not infer intended age,
height or stylization from size alone. Source metadata, reliable humanoid bindings
and neutral proportions can support suggestions, not a guarantee of artist intent.
Keep deliberately short/tall/stylized or uncertain models unchanged unless the
artist explicitly chooses to fit them. Advanced retains the original scale and
measurement/provenance; reset/Undo must recover it.

## Actual code and neutral-geometry audit

Current defaults are MMD .08, Source .01905 and VRM/common formats1 before any
chosen import override. Source's documented .01905 is an importer default, not a
universal real-world stature guarantee. Do not globally change it to another
assumed unit conversion as a substitute for the requested option.

A separate headless engine audit loaded the five prepared native standard assets
at neutral pose with their saved root orientation/scale, independently of animated
crouches/contact pins and transformed parents. Actual skinned mesh-bound heights:

| Prepared model | Full mesh height in current scene units |
| --- | ---: |
| Miku PMD | 1.60923 |
| GMod Reimu | 1.29532 |
| SFM Scout | 1.55624 |
| VRM1 sample | 1.55812 |
| VRM0 sample | 1.55812 |

Five precise queries, zero conservative fallback meshes/errors. Scout's saved
root rotation is essential; ignoring it can measure a sideways model. These are
**full-mesh bounds**, including possible hair, hats, heels or accessories, not
certified anatomical stature and not evidence that any model was intended to be
six feet tall. All target factors were hypothetical; no normalization was applied.
Source fixture SHA was unchanged. First audit's Python result read used the Windows
default encoding and failed on Japanese names; explicit UTF-8 fixed the research
reader. Evidence: `output/import-height-audit.json` and per-run logs/results.

## Maps and application boundaries

The new SFM sample corpus includes separate head, skirt, hair and wing MDLs.
Do not fit such parts independently to six feet, even when they carry a full
skeleton. Require a confirmed complete character or an explicitly assembled
group before estimating stature. Mesh coverage matters as well as bone names.

Provide a separate optional map calibration using a representative doorway or
floor/ceiling reference chosen by the artist, with an editable known height. Show
a six-foot person/reference guide and the resulting clearance. Do not infer map
scale from its overall bounds, force every room to one ceiling height, or assume
all US interiors have identical dimensions. Door/ceiling presets are editable
references, not a universal building standard. Apply one uniform scene scale.

Normalize before placement/animation/helper/physics creation where possible.
Runtime colliders, springs, parent transforms and future particle dimensions must
use the evaluated scale. Existing world-space foot pins must not move silently;
an existing animated model needs explicit behavior and complete-range validation,
not merely changing a draft scale at one frame. Cameras, drawings and peers must
remain independent. Save/Open/Undo, repeated import/relink, reset, source unit
provenance and no-double-application need actual tests. The new import guide records
the implemented subset; map/existing-animation/reset/first-use gates remain OPEN.
Current normal installation contains no new fit UI. Development static map sizing
implements the reviewed known-distance/six-foot guide subset described above;
the remaining map/existing-animation/reset/first-use gates stay open.
