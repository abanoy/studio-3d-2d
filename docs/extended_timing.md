# Longer parent timelines

**Options → Scene length (frames)** now extends a parent project beyond240frames,
up to60seconds and7200frames. At24fps the limit is1440frames; at120fps it is7200.
The exact integer limit at24000/1001fps is1438frames. The Options panel shows the
current limit. Child scenes remain at most240frames and can be placed or looped
later in the parent.

Existing frame addresses, source assets, drawing holds, camera/pose animation,
audio samples and source trims stay unchanged. Increasing length adds time. It
never stretches existing content. Shortening still refuses content beyond the
new end. A frame-rate change that would take an extended parent beyond60seconds
refuses before changing its history, settings or audio, including changes made
while editing a child. The legacy duration domain of1–240frames remains readable
at unusual slower custom rates; existing audio limits still apply.

A new child in a longer parent starts with at most240frames. Its initial placement
also fits that bounded local source. Set Loop explicitly to repeat it farther
through the parent. Drawing imports can start later in a longer parent, but each
video/Krita preparation remains capped at240outputframes with the existing32-cel
and raster-memory budgets. Longer source clips must be shortened externally.
Named reusable movement-path files likewise remain capped at240frames; short
routes can be used in a longer project.

## Storage and compatibility

Extended projects use **schema8**, with `timing_content_schema_version` identifying
the existing content schema3–7. A kept reference and nested graph can therefore be
represented as8→7→6; the reference and graph formats retain their own meanings.
Decoding returns the underlying runtime schema so a legacy scene still uses its
legacy scene loader. Short projects without extended features keep their existing
schema; no blanket migration is performed.

Late imported drawing ancestry uses `studio_drawing_origin_3` for Krita and
`studio_drawing_origin_4` for video. These keep the original descriptive identity
and import placement without following any external source path. Old ancestry
formats retain their240frame placement bound. New ancestry or retained extended
sequence placement keys keep schema8 even if a scene is subsequently shortened.
An enclosing project also declares schema8 when one of its children needs it.

Older readers refuse schema8. Removing the wrapper cannot make a longer project
or late ancestry valid under an older schema: both GDScript and Python readers
reject that downgrade. Existing content-addressed files, packed/linked ownership,
reference PNGs, source hashes and crash checkpoints use their established paths.

## Scope and verification

This is bounded longer-shot support. It retains four layers per scene,32cels,
241sparse camera/model controls, four sequence assets, eight sequence clips,
shared object/effect/audio budgets,1MiB manifests and60second audio mixing.
It does not implement lazy cel paging, arbitrary-length audio/video tracks,
large dense scenes or a zoomable timeline. Exact frame entry and navigation remain
available; full-fit mouse selection becomes less precise on long timelines.

`python tests/verify_extended_timing.py --isolated-display :101` requires an
already-provisioned private dummy display on Linux; Windows uses the existing
private-desktop launcher. The verifier creates original procedural fixtures,
checks60second parent editing and late video import, packed and lesson cold readers with originals and writer cache unavailable, linked
readers with their declared source files available and writer cache unavailable, unchanged normal
startup after SIGKILL, exact late preview/export pixels, and actual252frame
1080p12 H.264/AAC with sound beyond the former frame240limit. It also exercises
schema3–7 wrappers, exact rational boundaries and the7200frame storage boundary.
Software-rendering checks do not establish Windows GPU, tablet feel, native
import fidelity or owner acceptance.
