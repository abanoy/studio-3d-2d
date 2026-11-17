# Bounded primary-source API review

The tagged Blender 5.1.0 source was read for API side effects. It is an API/source interpretation, not proof of this installed binary's exact compiled source. The future native host separately requires the approved binary identity. No native getter was executed during preparation.

- [rna_image.cc](https://raw.githubusercontent.com/blender/blender/v5.1.0/source/blender/makesrna/intern/rna_image.cc): `has_data` checks the existing image cache (473–478). Several dimension, resolution, depth, duration and pixel getters acquire an image buffer (479 onward), so the collector omits them. ImagePackedFile fields describe the stored packed entry (832–859). Stored path/name/source/type/alpha/color-space/multiview and dirty/cache metadata are read; no update method is called.
- [rna_packedfile.cc](https://raw.githubusercontent.com/blender/blender/v5.1.0/source/blender/makesrna/intern/rna_packedfile.cc): packed size and data expose an already stored memory allocation (34–44, 60–67). The collector admits all sizes before copying and hashing any payload; it emits only byte counts/hashes.
- [bpy.cc](https://raw.githubusercontent.com/blender/blender/v5.1.0/source/blender/python/intern/bpy.cc): the blend_paths callback appends path strings and returns without replacing a path (87–159). The collector asks for stored relative strings with packed resources included and excluded, without dereferencing them.

The API documentation endpoint was unavailable during the source review; these exact official tagged C++ sources support the bounded interpretation. None establishes that loading an arbitrary blend is safe before the collector runs. No shader evaluation, image decoding, Blender export or native IO-confinement experiment was performed.
