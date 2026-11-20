# Shared source Image admission without losing exporter provenance

Source-only design. No tests, native assets/parser, Blender, processes, CIM or
Git were executed. Both inspector2 folders and the frozen RNA resource packet
remain unchanged. Root reports the actual inspector2 worker passed four graphs,
two reached Images/two shared references,1709130 packed bytes and83886080
prospective RGBA-F32 bytes, with one exact owned-source Library verified and no
ImBuf getter used. The private child reported closed/exit0 after4.091 seconds;
Root subsequently confirmed finalPASS: exit0/reaped,35 preservation checksTrue
and a fresh physical observation with zero owned processes. Its
stage is `output/source-material-inspection2-run-1795215149366755200`. This is
completed narrow Root inspection evidence, not an actual exporter/cache/normal
result. The earlier first refusal is unchanged.

The smallest successor should retain one ticket per genuine source Image ID,
allow that actual ID to be reached from multiple separately admitted material
graphs, and separate per-socket gather bindings from unique emitted glTF Images.
Repeated hooks qualify only through an exact observed exporter cache event.
Removing the current duplicate-image checks alone is insufficient.

## Frozen inputs to the design

The RNA resource successor is published at
`experiments/source_resource_rna_20261120` and prepared under
`output/source-resource-rna-successor-prep-20261120`:

| Source | Bytes | SHA256 |
| --- | ---: | --- |
| resource_gate_proposal.py |33098|1f9aa3545dcd9a4fd2d740802fc88f1920f3f0b74a27a5e5a49517c771bc9a85|
| export_hook_proposal.py |33179|1b6e6b5fa4acb1e3bea1d37fd433f42c1294ed70a24047c4ea0e4c60b18afbae|
| test_export_hook_proposal.py |35090|a48a6bee400407cffefa2780ddbef6957bcd2e13acdfbdbb67fb454c3f3e8121|

Root reported38 pure tests passed. That proves neither installed exporter hook
execution nor resource/normal fidelity. The current constructor deliberately
refuses a source Image shared between graphs; later image-hook uniqueness and
final equal-cardinality checks also assume unshared resources.

The primary implementation read here is the installed, source-pinned exporter
at `C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2`.
The relevant files retain these exact hashes from the original17-file surface:

| File | SHA256 |
| --- | --- |
| blender/exp/cache.py |12fc08e6403c9dd604f6884fdfdcf787ed5a898a2c6f4e2990f1826d6e265d98|
| blender/exp/material/image.py |fc1ce104f15d6168ee959742e2313f668aeb0e8526cf0b4122e796a1a241c509|
| blender/exp/material/texture.py |9abd202b09a224c2cfe14a1ff596be362e1d7e19e11ce71bad68cd56092a0e20|
| blender/exp/material/texture_info.py |962d784eefcd81e1f5bfe7cc7f96bb19b2b7725dfa4a00250ecf87db551d144a|
| blender/exp/material/encode_image.py |1f59e5a2a3116c21afab6c2baf49f9ea1b4c9d663b268d69ec5123d2bf011de1|
| blender/exp/material/search_node_tree.py |2bafe2b2d24bf6d8087c22a6d3a5fddc9f39eb537a2f052e99c1d9dc92136c59|
| blender/exp/material/materials.py |e9660b8325208928317df15c05ed980c04f275a8afad01e1195a1a3f1859c5f6|
| blender/exp/exporter.py |49c1e0174a65efd6d411b906cd154b6b04502c4840c9b31a7bfac87e0888f242|
| io/com/gltf2_io.py |d0bad0c89e40c0975ed9e435656151e353240134011f69602e473e0a5f1592f4|

One additional explicit surface is needed for actual image-cache key equality:
`io/exp/binary_data.py`,1123B, SHA256
`ed6e29b6557522b6a056a9bb1e3a0b6a8fffe250e9d0afdf47f7f2eef2447dcf`.
It is already part of the immutable120-file exporter catalogue. A successor
should add it to its explicit module/runtime surface, leaving all prior pins
unchanged, rather than trusting an unverified custom hash/equality object.

## What the pinned cache actually does

[`cache.py:8`](<C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2/blender/exp/cache.py:8>)
stores a dictionary on the genuine unwrapped function. The key is supplied by
the genuine key function; the default includes all actual arguments except
export_settings. It resets only when the function has no settings record or
the settings compare unequal, then either returns the cached value or calls
the body and inserts its result. A settings object mutated in place is still
the same dictionary; do not treat that comparison as an immutable options proof.
The existing strict option/sole-collector checks remain required.

[`search_node_tree.py:740`](<C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2/blender/exp/material/search_node_tree.py:740>)
defines the exporter's ordinary Python `NodeSocket` wrapper without custom
equality/hash. Its identity participates in a gather cache key. It is distinct
from an RNA NodeSocket wrapper: retain the existing typed owning-ID/C-pointer
canonical key for RNA provenance, but observe the genuine ordinary wrapper
objects in the actual exporter cache key. Never replace the real cache key with
our canonical socket key, reorder it or manufacture a hit.

[`image.py:19`](<C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2/blender/exp/material/image.py:19>)
caches gather_image by actual socket-wrapper tuple and tile. On a body call,
`__get_image_data` normally creates a fresh ExportImage descriptor. Its complete
FillImage destination/source-channel relation must still be validated before
encoding. ExportImage has ordinary object identity; sharing a source Image does
not justify aliasing two independently created descriptors.

[`image.py:101`](<C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2/blender/exp/material/image.py:101>)
separately caches `__make_image(buffer_view, extensions, extras, mime_type, name,
image_data, settings)`. For this GLB profile the URI isNone and MIME isPNG.
[`BinaryData:19`](<C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2/io/exp/binary_data.py:19>)
compares/hashes by its encoded bytes. Thus distinct per-material descriptors
and BinaryData objects can produce the same genuine make-image cache key and
the same glTF Image object. The gather_image body still calls gather_image_hook
after that cache hit. This is a source-derived explanation for a possible
repeated glTF Image hook, not an actual observed export result.

`gather_texture` is separately cached by socket-wrapper tuple/tile and creates
a Texture in its body. TextureInfo has a separate primary-socket/tuple/kind/
filter key. Material gathering caches by original material identity; the UV0
final-material path returns the base material when all indices areNone.
The existing no-deepcopy/UV0/material/Texture/TextureInfo identity rules should
remain. Shared source Images do not generally mean shared TextureInfo objects.

[`exporter.py:397`](<C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2/blender/exp/exporter.py:397>)
converts actual child-of-root objects to unique indices; repeated use of the
same glTF Image should retain its same final index. Traversal mutates nested
resource refs into integers. Cache/body observations belong to the gather
phase; later reference observations must permit only the existing known
reference transition, not arbitrary resource mutation or a new gather phase.

## Concrete narrow successor contract

1. **Preflight actual graph incidence.** Keep unique genuine Image tickets and
   strict same-ID/image snapshot checks. Build an explicit bounded incidence
   relation: actual source Material/NodeTree plus ordered canonical color/Alpha
   socket keys → actual Image ID and complete channel plan. Every ticket must
   be reached, every graph remains independently typed/local/admitted, and all
   paths/defaults/packed refs/bytes remain unchanged. Names, hashes or equality
   never establish that two source Images are the same ID. Distinct Image IDs
   with equal bytes/names must not gain sharing authorization.
2. **Pre-admit repeated encoding cost.** Retain all existing unique-ticket PNG,
   encoded and prospective-decoded limits before any ImBuf getter. Also bound
   the known per-binding encoded cost, call count and retained cache/key/buffer
   observations before invoking the ordinary exporter, so shared resources do
   not introduce unbounded repeated encodes or retained BinaryData. Do not
   increase the existing128MiB limits to make a fixture pass.
3. **Attest the cache machinery before installation.** Extend the current exact
   function/code/globals/defaults/closure/alias checks to gather_image,
   __make_image, __gather_buffer_view, __gather_uri, gather_texture and the
   texture-info helper/key functions involved in this profile. Check the exact
   BinaryData class and runtime __init__/__hash__/__eq__ source/code/module
   identities and image/exporter aliases. All relevant original caches must be
   absent/cold before the operation; never clear or prefill them to pass. Any
   complete-code-object mismatch refuses and is diagnosed independently;
   source hashes alone do not excuse it.
4. **Observe exact invocation frames.** Wrap the actual cached entry points
   and __make_image with OwnedPatches and the existing failure latch. Hold both
   the actual exporter cache arguments and our semantic graph/socket key. On
   entry validate all settings/options/graph refs. Inspect the actual unwrapped
   cache state without changing it. Require absent initial state or the exact
   same settings/cache objects and previously observed entries. Unexpected,
   warm, replaced or unobserved entries refuse. A cache miss must add exactly
   its own key/result; a hit must retain the exact previously observed value
   and unchanged mapping. No extra entries may appear. Bound the dictionaries.
5. **Connect make-image hits causally.** A __make_image call occurs only inside
   one active admitted gather-image body whose early descriptor was validated.
   The call's complete original key, exact BinaryData type/bytes/length/pin and
   bufferViewTarget=None, MIME/name/URI,
   descriptor channel map and source Image ID must match. On a hit, permit the
   same glTF Image only if the prior authorized key event has that **same actual
   source Image ID and complete mapping**, not merely equal encoded data. A hit
   that merges distinct source Image IDs or a changed mapping refuses even if
   the genuine exporter could otherwise merge equal byte content.
6. **Consume hook events once.** An image hook must consume exactly one new
   unconsumed make-image event from its active gather body, for the exact
   descriptor, original socket arguments, canonical context and returned glTF
   Image. A second authorized distinct socket context can bind the same unique
   glTF Image only through its proven cache hit. The same hook/context replay,
   an event-less hook, a changed descriptor, cross-context composition or a
   foreign glTF object refuses. A gather-image cache hit skips its body/hooks;
   validate its actual cached return against the already observed binding,
   never synthesize another hook or descriptor observation.
7. **Separate unique objects from bindings.** Keep `descriptors` for distinct
   actual body-created descriptors; `image_bindings` for admitted per-socket
   body/hook events; and `images` for unique actual glTF Image objects. Store
   the binding→descriptor→make-image event→unique Image relation explicitly.
   Texture/TextureInfo/material hooks keep their current uniqueness and graph
   ownership gates unless a separately proven actual cache-hit return reuses
   an existing record without a new hook. No blanket repeated-hook allowance.
8. **Finalize by incidence and reference coverage.** Replace only the old
   equality `images == descriptors == textures == infos` with independent exact
   coverage of planned textured socket contexts and each unique object table.
   Every material/slot/primitive binding and Image ticket must be reached; every
   descriptor/event consumed; no extra/missing binding or unique object allowed.
   Existing final-index reassignment/collision rules and serialized table/
   texture-source/material-info checks remain. Multiple Texture records may
   point at the one observed Image index; repeated references to that same
   actual Image must keep the same index. Distinct glTF objects may not be
   declared identical merely to satisfy cardinality.

For a future **qualified** four-material/two-source-Image, direct-RGBA profile,
one possible source-predicted cold trace is four descriptors/bindings, two
make-image misses plus two hits, two unique glTF Images, four Textures and four
TextureInfos. That is a test scenario, not an assumed native result or an
unconditional required output count. Actual graph/channel/key incidence must
derive the expected relationships and the actual cache trace must prove them.

## Independent tests and integration boundary

Author only a separately versioned proposal after this plan is reviewed; keep
all38 passing RNA tests and predecessor sources. Add meaningful synthetic cases
for: same actual Image/two distinct material contexts and one legitimate cache
hit; no-hit/no-sharing baseline; genuine gather-cache hit with no body hook;
equal bytes on distinct Image IDs refused; wrong cached return or injected warm
entry; changed key/mapping/MIME/name/URI/buffer pin; repeated/event-less/cross-key
hook; missing consumed event; shared source with different unsupported channel
composition; stale settings/cache function/closure/class; root index collision
or wrong serialized incidence; pre-admitted repeat-cost budget; swallowed hook
failure and exact restoration/partial-install/foreign-writer failures.

The future actual host must consume inspector2's completed narrow Root
Library/local graph/resource qualification, then build a fresh independently observed native-ID/
current-weight scene with the exact native slot/material relation. Historical
B contributes only authenticated local material resources; it never supplies
native point labels or saved numeric identity. Root's separate carrier plan
must preserve all non-NORMAL semantics and obtain a real export/cache/hook
receipt before comparing the exact output.

The same strict non-NORMAL comparator and unchanged2e-5 independent normal gate
remain mandatory. Cache provenance is not visual/material equivalence, generic
shader evaluation, source-normal fidelity or application adoption. All such
flags remainFalse until their separate actual checks pass. Full runtime/source
pins, cold private bounds, originals/copies preservation, closure proofs,
failure latch and exact owned method restoration remain required throughout.
