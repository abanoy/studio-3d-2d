# Material-only library inspection preparation

2026-11-20. **AUTHORED, UNRUN.** Three stdlib-only helper/test/documentation files
were written here. No B/native asset, Blender, renderer, process, Git command or
test execution was used. Root will separately qualify a cold host/driver; this
directory does not launch one. Existing packets/application code are unchanged.

## API and ownership

`material_inspection.inspect_material_library(bpy, owned_path, material_names,
enumeration_module)` accepts an authenticated owned B copy and exactly four
distinct independently native-matched admitted names in a tuple. The whole
saved B material catalogue may contain additional unused entries: selected names
must each occur exactly once in a bounded1..256 catalogue. The helper does not
select the first four, request the whole catalogue, or infer correspondence from
equal counts. Root authenticates that admission, actual bpy classes and supplied
enumeration helper. The reviewed private helper API comes from library_worker.py18242B, SHA256
`6258a798b0cb37e14f9d8d478ac5030e36db663e2391675f5de5912feb3c19fc`.
It supplies `_census`, `_unchanged`, `_library_keys` and `_empty_requests`.
That predecessor's main wrongly assumed the whole catalogue had four Materials
and refused an actual enumeration. Tests import only its unchanged private
definitions. The native caller must use Root's separately qualified bounded
census successor, not replay the predecessor's whole-catalogue guard.

Every destination list is initially checked empty and the exact admitted
four-name subset rechecked. The request list is allocated first; assigning ONLY
destination.materials is the **last statement inside the context**. There is no
assumption of rollback: Blender's library context may append during exit even
when a body/exit error occurs. Returned Material refs must replace the strings
in that same list and order; no `bpy.data` name lookup chooses them.

Original exposed BlendData IDs retain actual refs, pointers, types, names and
library refs. Only four newly appended local Materials matching returned refs
and new local Images genuinely reached by their accepted graphs are permitted.
Node groups, objects, other added IDs, extra materials, preexisting/reused image
refs, missing returned refs and renamed requested Materials refuse. Nothing is removed to make a
failed census pass. Embedded Material ShaderNodeTrees are checked separately
from top-level collections. Final census and graph checks detect later changes
while metadata/packed data are inspected.

Cached ID refs (Material, Image, embedded NodeTree) retain Python `is` checks.
Non-ID RNA structs may have fresh Python wrappers per getter/iteration. Node,
Socket, Link, ImagePackedFile and PackedFile identity therefore requires exact
admitted RNA type, actual owning cached ID `is` the expected owner, and a bounded
nonzero `as_pointer()` value. Actual wrappers are retained privately. Endpoint,
schema, membership and repeated pointer/field checks remain strict; names,
equal values and proximity never establish identity. These keys are never
public payloads. The native returned request list is still the same Python list.

## Narrow observation profile

Genuine types come from bpy.types: Material, Image, ShaderNodeTree,
ShaderNodeOutputMaterial, ShaderNodeBsdfPrincipled, ShaderNodeTexImage, NodeLink,
NodeSocket, ImagePackedFile and PackedFile. The graph must be local, original,
embedded/nonanimated, have one active ALL Output, one Principled and at most
one TexImage. Only BSDF -> Surface, Color -> Base Color, and optional matching
Alpha links are accepted. Exact socket/node/link ownership is required; extra,
muted, group, mapping, vector-input and alternate-output paths refuse before
packed-byte access. Bounded socket default metadata is retained privately.

Shared actual Image refs across Materials are valid inspection observations;
the helper does not infer exporter hook counts or a bijection. Every added
Image must be reached. There may be zero Images for solid-color materials.

Image inspection reads only name/source/type/filepath/library and packed
references/collections. Filepaths are bounded inert metadata, never resolved,
tested on disk, loaded or renamed. A .vtf-looking path with embedded PNG bytes
does not itself cause retrieval; future exporter MIME/path admission remains
separate. FILE/IMAGE, exactly one connected packed part and genuine PackedFile
are required. Multiple parts, unpacked/external data and Viewer kinds refuse.

All packed sizes (64MiB/image,128MiB total) are admitted **before the first
PackedFile.data copy**. Each encoded payload is copied once, length-checked and
hashed. PNG signature, IHDR structure/CRC, 8-bit RGB/RGBA, ordinary compression/
filtering/noninterlaced headers and prospective F32 RGBA storage bounds are
checked:64MiB/image,128MiB total. These are encoded-header observations, not a
full PNG validator or pixel decoder. Image.size/channels/pixels/has_data and
filepath_raw are never read; no depsgraph update or render is requested.

## Result and refusal semantics

Success returns PRIVATE `{materials, graphs, images, summary}`. Raw references,
Material/Image names and filepaths, socket defaults and packed observations stay
in RAM. The summary alone is public-safe: counts, statuses and digest bindings.
It reports original-survivor/census changes and encoded/prospective budgets.
No raw packed bytes, names, graphs or geometry are in public summary fields.

On refusal, `Refusal.code` is a fixed code and `Refusal.summary` carries safe
observed counts. A fresh failure census is attempted even when context exit
raises after adding IDs. Added IDs remain in the disposable process; the host
must retain failure and perform its own job/desktop/physical closure. There is
no retry, shader rewrite, resource substitution, image creation, cleanup,
unpacking, export, save, geometry binding, SourceIO or native-ID labeling here.

Material binding, resource/export equivalence, native/historical point identity,
normal fidelity, application adoption and absence of transient IDs/C-level
reads are explicitly unqualified. This observation does not prove all B
resources fit the future exporter. Unknown actual B graphs may honestly refuse
this deliberately small profile; do not edit them to force success.

## Source basis for wrapper identity

Official Blender sources at commit
`ec6e62d40fa9e9d1bea33ad5d00148c99a4f0832` were read through the GitHub
connector. They are reference sources, not an attestation of the installed
binary's exact build. Root's cold actual API qualification remains necessary.

- [bpy_rna.cc](https://github.com/blender/blender/blob/ec6e62d40fa9e9d1bea33ad5d00148c99a4f0832/source/blender/python/intern/bpy_rna.cc#L8623),
  blob `ade15a1e1d0066226f3793320b65843f99963663`: reuse requires an existing
  RNA_struct_instance; otherwise a new wrapper is allocated.
- [rna_access.cc](https://github.com/blender/blender/blob/ec6e62d40fa9e9d1bea33ad5d00148c99a4f0832/source/blender/makesrna/intern/rna_access.cc#L1082),
  blob `4a4c15888967232675eb350cc43766ab3b73ac7a`, walks registered instance
  callbacks; [rna_ID.cc](https://github.com/blender/blender/blob/ec6e62d40fa9e9d1bea33ad5d00148c99a4f0832/source/blender/makesrna/intern/rna_ID.cc#L1157),
  blob `f1985d5d234c277043d4ce60bb965f1c6771a2bd`, supplies ID.py_instance.
- [rna_node_socket.cc](https://github.com/blender/blender/blob/ec6e62d40fa9e9d1bea33ad5d00148c99a4f0832/source/blender/makesrna/intern/rna_node_socket.cc#L771),
  blob `b6c050c373dfff1c6aa48c5d5214e76cb34fa7dc`, has no instance callback;
  its node getter carries the NodeTree owner.
- [rna_image.cc](https://github.com/blender/blender/blob/ec6e62d40fa9e9d1bea33ad5d00148c99a4f0832/source/blender/makesrna/intern/rna_image.cc#L731),
  blob `5a7b8777521bfeb7b3e2b31942cf3b2b6bb84cff`, creates the packed-file
  pointer with the Image parent. Packed entries and their packed pointers keep
  that owning Image ID.

The original0abd61a8 helper/bc3f8340 tests/5d6c6187 README are retained byte-exact
under predecessors/0abd61a8. That source-only predecessor incorrectly used Python
wrapper identity and assumed the four requests were the whole B catalogue;
neither assumption is retained in this successor.

## Prospective Root checks

The tests use independently constructed fake RNA/graphs/library exits and
synthetic PNG headers only. They consume the reviewed enumeration definitions
without invoking that module's main. They exercise exact returned refs, original
identity/name preservation, unexpected dependencies, no image buffer getters,
shared images, pre-copy aggregate budgets, header failures, post-append/late
mutation refusals and public-summary privacy. Fresh non-ID getter/iteration
wrappers, wrong owners, equal pointers with different types, changed pointers,
foreign same-looking sockets and nontrivial four-name catalogue subsets are
covered. They do not import Blender or
read a B/native file.

Prospective Root-only CPU command, **not executed by the author**:

```powershell
& 'C:\Program Files\Python313\python.exe' -B -m unittest discover -s 'C:\a\Programming\cloudflare\has-body-addition-20261120\output\source-material-inspection-prep-20261120' -p 'test_material_inspection.py' -v
```

The later native host must first pass current source review/tests and Root's
fresh full-suite/source/runtime/owned-B preservation and exclusive private-job
admission. The source-scope recommendation and primary references are in
output/source-material-inspection-scope-review-20261120.md. Strict unchanged
non-NORMAL B comparison and the original `2e-5` normal gate are later work.
