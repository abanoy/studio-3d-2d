# Material-only library inspection preparation

2026-11-20. **AUTHORED, UNRUN.** Three stdlib-only helper/test/documentation files
were written here. No B/native asset, Blender, renderer, process, Git command or
test execution was used. Root will separately qualify a cold host/driver; this
directory does not launch one. Existing packets/application code are unchanged.

## API and ownership

`material_inspection.inspect_material_library(bpy, owned_path, material_names,
enumeration_module)` accepts an authenticated owned B copy and exactly four
distinct names in a tuple from Root's preceding empty-request enumeration.
Root authenticates the actual bpy classes and supplied enumeration helper.
The current reviewed enumeration helper is library_worker.py18242B, SHA256
`6258a798b0cb37e14f9d8d478ac5030e36db663e2391675f5de5912feb3c19fc`.
It supplies `_census`, `_unchanged`, `_library_keys` and `_empty_requests`.

Every destination list is initially checked empty and the exact four-name
catalogue rechecked. The request list is allocated first; assigning ONLY
destination.materials is the **last statement inside the context**. There is no
assumption of rollback: Blender's library context may append during exit even
when a body/exit error occurs. Returned Material refs must replace the strings
in that same list and order; no `bpy.data` name lookup chooses them.

Original exposed BlendData IDs retain actual refs, pointers, types, names and
library refs. Only four newly appended local Materials matching returned refs
and new local Images genuinely reached by their accepted graphs are permitted.
Node groups, objects, other added IDs, extra materials, preexisting/reused image
refs, missing returned refs and renaming refuse. Nothing is removed to make a
failed census pass. Embedded Material ShaderNodeTrees are checked separately
from top-level collections. Final census and graph checks detect later changes
while metadata/packed data are inspected.

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

## Prospective Root checks

The tests use independently constructed fake RNA/graphs/library exits and
synthetic PNG headers only. They consume the reviewed enumeration definitions
without invoking that module's main. They exercise exact returned refs, original
identity/name preservation, unexpected dependencies, no image buffer getters,
shared images, pre-copy aggregate budgets, header failures, post-append/late
mutation refusals and public-summary privacy. They do not import Blender or
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
