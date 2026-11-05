# Prepared raster clip contract

This is the local preparation backend used by [Studio's Krita importer](krita_import.md).
`tools/prepare_krita.py` produces `studio_raster_clip_1`: full-frame RGBA8 PNGs,
relative paths/checksums and consecutive local-frame holds. Original source
identity and explicit layer choices remain separate from rendered pixels. No
live scene, authored key, existing drawing or HAS file is mutated by this worker.

## Request and review

`--inspect source.kra --result fresh.json` returns compact layer/timing metadata,
source SHA and render-support limits. Full keyframe arrays remain in the offline
inventory; the UI response is bounded to1MiB. Oversized sources can be inspected
but are marked unsupported for current rendering. A response file must be new.

A preparation request names original source/SHA, fresh output directory, an owned
cancel path, installed Krita/FFmpeg, project numerator/denominator, remaining scene
frames and cel slots, output size and an optional `layer_visibility` map. Overrides
use original UUIDs and actual booleans. No background-name guess or automatic layer
removal occurs. Explicit overrides change only `maindoc.xml` in a new scratch KRA;
other native members preserve bytes/CRC and the original stays untouched. Native
Krita renders those choices; HAS does not approximate Krita's paint tiles.

The newer `<image-name>/animation/index.xml` overrides legacy animation fields in
`maindoc.xml`, field by field. The inspector follows native loader precedence,
retains conflicting legacy timing for review and rejects duplicate timing fields.
This matters: the actual divergent-index fixture initially rendered more frames
than its legacy XML suggested; the output guard stopped it before committing a
clip. A corrected fixture verified frames3–8 at30000/1001fps against original
frame pixel hashes. Saved current time is not the playback range.

## Native work and bounds

The installed Krita batch process stays on an owned private Windows desktop. No
desktop switch/visible fallback/ordinary-instance command is used. Optional new
launcher flags signal cancellation and limit aggregate committed job memory to
3GiB; existing test calls keep their original defaults. Cancel and preparation
failure both let the launcher close its owned job/desktop and retain a receipt.
Timeout fallback terminates only the owned launcher and its kill-on-close job.

Current native limits:192MiB source,16,777,216pixels,128layers,2GiB declared native
payload,240source frames,180s render,512MiB generated native PNGs. These are guards,
not universal native-fidelity or memory/performance guarantees. Unsupported input
refuses before scene adoption. Large/dense/long clips need a later cache/resource
increment; do not silently omit content or raise the application's limits.

## Pixels and time

Normalized output fits inside the target frame, centered with transparent padding,
never cropped. Integer dimensions round to the nearest pixel. Native alpha is
premultiplied in RGB float, scaled with Lanczos, unpremultiplied and stored as
RGBA8. RGB planes only are multiplied; alpha is not squared. This uses encoded
RGB values and does not claim linear-light/ICC/HDR color-management fidelity.
Current bounds are1920×1080,32held drawings and256MiB normalized PNG data, with
90s normalization and individual converter deadlines.

Timing uses exact fractions. Target frame `t` samples native local frame
`floor(t × sourceFPS × projectDenominator / projectNumerator)`. Target duration
is the ceiling of source seconds in project frames, so its end may round up by
less than one target frame. Native naming/range/frame count and every PNG CRC are
checked. Repeated normalized image hashes form explicit holds. A still uses its
requested exposure. The worker refuses beyond the caller's scene/cel budget.

`clip.json` is written atomically only after all images/source checks pass.
`progress.json` reports copy/render/normalize/ready/error/cancelled. An optional
fresh job-local `result.json` reports preflight errors or the clip/checksum. Partial
files alone never mean success. The app controller rejects late cancellation and
stale scene/frame/source state; a prepared clip never overwrites a current drawing.

## Measured scope

Actual native Hecatia with an explicitly excluded UUID Background produced eight
transparent six-frame holds over48frames. Pinned-engine pixel decoding found
transparent, partial and opaque pixels; an authored hidden-blue/opaque-red control
had zero colored fringe after normalization. Original KRA SHA remained exact.
Mid-render cancellation and an intentionally tiny output-budget refusal both
closed the owned job/desktop and produced no ready clip. Expected cancellation
receipts exit2; they are not counted as ordinary exit0 graphical passes.

The original100-layer Alice still also prepared successfully, preserving native
visibility as one48-frame hold at24000/1001project fps. A source range3–8 fixture
at30000/1001 produced two four-frame holds with exact reference PNG hashes.
Native logs retain Fontconfig warnings: these paint-layer tests do not certify
text/font/vector fidelity. Original files remain unchanged. No new dependency,
model weights, plugin or binary runtime is redistributed.

The in-app review now validates this typed packet against captured scene state,
decodes independent editable Images and commits one new layer with one Undo.
Portable ancestry, HAS/recovery and preview/movie use existing common paths.
Native audio and editable original Krita layers are explicitly not imported by
this rendered-artwork contract. Video/chroma/nesting/long clips remain unfinished.

Tests: `python tests/test_krita_assets.py` and `python tests/test_krita_preparation.py`.
Owner-specific real-render evidence stays local in the dated checkpoint, outside
the source archive. See the progress memo for actual counts and paths.

Primary references: [matching native animation metadata loader](https://github.com/KDE/krita/blob/0619060/plugins/impex/libkra/kis_kra_loader.cpp#L592),
[FFmpeg premultiply/unpremultiply](https://ffmpeg.org/ffmpeg-filters.html#premultiply),
[Windows job committed-memory limits](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_extended_limit_information)
and [Krita command line](https://docs.krita.org/en/reference_manual/linux_command_line.html).
