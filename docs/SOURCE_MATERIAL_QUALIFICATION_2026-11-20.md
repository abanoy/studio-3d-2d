# Next Source qualification: materials, dependencies and face slots

2026-11-20. Source-only plan; no new native launch, B load, asset parsing,
export, pixel access or correction was performed for this note. Only this file
was written. Existing published packets and application sources were untouched.

The next result should establish **an exact material attachment relation for a
new SourceIO derivative**. It must not certify historical B point identity or
load B meshes, objects, armatures or scenes into Blender.

## Starting identities

Reuse the current probe's complete Root admission, preservation, private desktop,
owned TEMP, failure cleanup and physical-closure conditions; do not merely reuse
an old runtime lease. The immutable runtime lock is
`experiments/replay_audio_fix_20261115/builder/input-lock.json`, SHA256
`3bb7c2ce75f55dcb53143aab0df5ab8b39c68180617092664a579126fb09cfb6`
(six runtimes, SourceIO574, exporter120). Runtime is the same pinned Blender5.1;
actual successful worker reported Python3.13.9, optimize0, no pycache prefix.

| Input or baseline | Bytes | SHA256 |
| --- | ---: | --- |
| Current worker | 35572 | `d78369585463dcc2a511e00889f7e768e10c61004cf4f3fac0df3885b7d60c93` |
| Current Root driver | 51728 | `f9bc228e02f3097548fad9ed1e83bc7c3d475abc40c088cd3c236e91f1dbf324` |
| Actual narrow result, `output/source-current-id-run-1795202600420799400/PUBLIC_ROOT_RESULT.json` | 3455 | `4bd6932ee005334b6464300edfc110eb64eaf5d674f6c172f84209b99f7be755` |
| B blend: hash-only provenance so far in this probe | 2423175 | `ead1f1913812593abd69e353fed375944a15f280738784886fcef7fda3ee65c6` |
| Original B GLB, later comparison baseline | 2322644 | `4e6ac7c2a7a84dea4b46b0bcb5724af68781243f57737e555b4cc82f2628b90d` |

The current result closes two fresh meshes, 9661 points, 42702 corners, 69 groups
per mesh and four observed creation stages; it does not append resources or
export. Preserve the full-module code attestation and observer AST inverse.

## First implement the independent slot oracle

Add a separate bounded pure MDL49/VTX7 material decoder and synthetic tests;
leave the pinned cbb4 point producer unchanged. Its `_mdl` already reads each
116-byte mesh record's material index, but does not qualify the texture table,
search paths, skin families or material correspondence.

Read source entry points from the approved SourceIO tree:
`library/models/mdl/structs/header.py::MdlHeaderV49`,
`structs/material.py::MaterialV49.from_buffer`, `v49/mdl_file.py::from_buffer`,
`structs/mesh.py::MeshV36Plus`, and `blender_bindings/models/common.py`.
Independently validate bounded tables/strings, texture names/flags, search-path
order, uint16 skin-family references and each mesh material index. Derive the
triangle material stream in VTX mesh order, repeating the MDL material index for
each admitted triangle; the importer reverses the complete triangle order with
`material_indices_array[::-1]`. Keep the existing closed strip/topology profile.

At the genuine importer stages, retain actual placeholder references and verify
every polygon's slot against this independent stream. Build the explicit chain
native material index -> placeholder reference -> mesh slot -> face order.
`get_or_create_material` reuses case-folded `full_path`; `add_material` deduplicates
by name plus `full_path`. Therefore native indices, mesh slots and final glTF
material indices are different domains. Refuse ambiguous aliases or renaming;
never zip their integer indices or use nearest/name-similarity repair.

`import_model` also assigns `skin_groups` custom properties using Material refs
when supported, with a name-string fallback. Record which branch actually ran.
Before deleting owned placeholders, account for slots, these properties and
`mdl.materials[i].bpy_material`. Rebind only the declared native skin-family
relation to the eventual returned B material refs; do not leave stale pointers
or silently change skin metadata. Include that metadata in later comparison.

## Admit the B dependency closure before appending

The official [Blender5.1 library implementation](https://raw.githubusercontent.com/blender/blender/blender-v5.1-release/source/blender/python/intern/bpy_library_load.cc)
is a reference, not an attestation of this installed build commit. `__enter__`
opens the blend and enumerates ID names. `__exit__` links/appends dependencies,
then replaces request strings with returned ID refs; missing items can become
`None`. It ignores context exception arguments: a body exception after setting
requests is not rollback. The API does not supply an indirect-ID/file-access
allowlist. Confirm the installed signature/build before depending on extra
keyword options; start from supported `libraries.load(path, link=False)`.

Smallest next native boundary: an **enumeration-only** cold probe with every
destination request empty, an owned byte-identical B copy and complete before/
after ID census. This may parse B file bytes; it must instantiate no historical
geometry IDs. It can qualify requested-name availability and the API, not the
material graph or dependency closure.

Before a nonempty append, require an authenticated bounded dependency manifest
for each selected B Material: embedded node tree, referenced node groups,
images, ID-valued custom properties, animation/driver targets, libraries and
other indirect IDs. Existing point/weight evidence supplies none of this.
If retained metadata does not prove complete closure, the intervening task is
a bounded raw-B ID/dependency metadata reader, not a blind append followed by
deleting unexpected objects. Keep unresolved references refused. A Python
`open` wrapper or post-append census cannot prove C-level forbidden reads never
happened. Admit only the owned B and embedded, local dependencies; external
libraries/images and geometry-ID dependencies need refusal before append.

Then one cold material-only append may request the exact unique names **last**
inside the context. Request no other ID types and do no fallible validation
after populating requests. Pre-admit collision-free names, disable local-ID
reuse/overrides using only qualified options, and preserve original metadata.
Bind returned `data_to.materials` refs by the admitted request relation, not a
later global name lookup. Verify local/non-evaluated refs, no `None`, exact names,
complete allowed ID-set difference and unchanged fresh mesh/rig references.
Refuse unexpected dependencies; do not export or save on failure.

Native descriptors/search-path candidates and authenticated B material metadata
must yield a unique explicit material relation. NoMaterialIO placeholder names
alone do not prove the original resolved VMT path. Do not call the production
bridge's VMT/VTF rebuild, decode external files, rename resources, rebuild
shaders, unpack images or alter the historical B. Assign only admitted returned
materials, preserving the complete face stream and declared skin relation.

## Profile admission and the following gates

The source-only resource prototype is deliberately narrow:
`experiments/source_export_hook_20261120/resource_gate_proposal.py`, SHA256
`336119221fc6c96d78b69cf301e2d89b0130c48febaedb81fc1c0b0134211e14`.
It admits 2–3 nodes: one active ALL Output, one Principled and at most one
TexImage, Color -> Base Color and optional Alpha. It refuses extra nodes,
groups, mapping/vector links, normal/ORM paths, shared images across materials,
external/Viewer/UDIM images and non-PNG paths. Packed PNG limits are 64MiB per
image and 128MiB aggregate for both encoded and prospective F32 RGBA storage.
Check all packed headers before image size/channels/pixels getters.

Source alone does **not** establish whether these B materials fit that profile.
The production bridge can build other paths; retained issue summaries are not a
complete graph admission. An unsupported graph is a recorded profile refusal,
not permission to simplify it or broaden the shader evaluator during the run.

After material-only success, separately qualify one cold exporter invocation
using the same actual fresh Object/Mesh refs and observed native ID chain.
Bind actual slots, shader sockets, images, gather/cache refs and output refs;
keep early resource guards, swallowed-exception failure latch and exact scoped
hook restoration. The hook core remains independently pinned at
`1b6e6b5fa4acb1e3bea1d37fd433f42c1294ed70a24047c4ea0e4c60b18afbae`.

Then require strict unchanged non-NORMAL comparison against original B GLB:
decoded attributes/order/topology, UVs/colors, weights/joints/inverse binds,
rig/transforms/hierarchy, extras/skins, face/material bindings and exact encoded
resources. Fresh SourceIO import plus preserved materials can still differ in
rig, metadata, geometry splitting or export behavior. Neither current IDs nor
material-only success establishes this equivalence. Only after this gate passes
attempt append-only NORMAL correction with the existing signed-axis transport
and unchanged `2e-5` bound. Preserve failed baselines; historical native causality,
generic format qualification and HAS adoption remain separate and false.

Public receipts contain counts, statuses and digest bindings only; dependency
tables, paths, native rows, graphs, packed bytes and geometry stay private/RAM.
