# Material-only B inspection: scope review

2026-11-20. **Recommendation: proceed with the two separate bounded inspection
experiments described below.** A complete static DNA dependency proof is not a
prerequisite for this narrower result. The previous plan required that proof
to support a stronger claim that no unexpected dependency or C-level read could
ever occur. This inspection expressly makes neither claim. The governing result
is preserved originals, an isolated owned job, recorded actual in-memory changes,
and refusal before export/binding if the observed resource profile fails.

This is a source-only review. No B/native assets, parsers, Blender, processes,
Git commands or inspection workers were executed here. Earlier plans remain
unchanged historical records. This note does not relax subsequent exporter,
strict non-NORMAL, normal-fidelity or application-adoption gates.

## Two distinct Root-owned experiments

1. **Enumeration only:** cold factory/offline/disabled-autoexec Blender, owned
   TEMP/user directories and hidden private desktop; load the authenticated owned
   B library with every destination request empty. Record exact before/after ID
   sets and the bounded material-name catalogue count/digest. A successful result
   requires unchanged actual ID sets. It establishes library enumeration for this
   exact copy/build, not resource closure or native material correspondence.
2. **Material-only read-only inspection:** a separate fresh owned job, with the
   same 4GiB/150-second bounds and retained cleanup/physical closure, may request
   exactly the four authenticated B Material names. No other direct requests,
   native point labels, old mesh selection, SourceIO import, geometry binding,
   exporter, save, pack/unpack, render or correction belong to this experiment.
   Root identifies this owned copy as byte-identical to original B, 2423175
   bytes, SHA256 `ead1f1913812593abd69e353fed375944a15f280738784886fcef7fda3ee65c6`.

Here "read-only" describes filesystem/original preservation and inspection intent;
append deliberately creates in-memory IDs. Four B materials and four native
texture records are different domains: equal counts do not bind them.

## Source-backed caveats that remain

Official Blender reference sources were read through the GitHub connector at
commit `ec6e62d40fa9e9d1bea33ad5d00148c99a4f0832` on the5.1 release branch.
These are source references, not an attestation of the installed binary's exact
build commit; Root must check the actual host API/profile.

| Source | Git content blob |
| --- | --- |
| [Python library context implementation](https://github.com/blender/blender/blob/ec6e62d40fa9e9d1bea33ad5d00148c99a4f0832/source/blender/python/intern/bpy_library_load.cc#L475) | `c2902e04ca6781801345510fe5625076f85f0777` |
| [Link/append dependency processing](https://github.com/blender/blender/blob/ec6e62d40fa9e9d1bea33ad5d00148c99a4f0832/source/blender/blenkernel/intern/blendfile_link_append.cc#L1240) | `ac0ae3df96cc2daaef86594d465adae19f364314` |
| [PackedFile RNA bytes getter](https://github.com/blender/blender/blob/ec6e62d40fa9e9d1bea33ad5d00148c99a4f0832/source/blender/makesrna/intern/rna_packedfile.cc#L37) | `a6e3e307c047fcb3f961182a38b8cdf33efd1515` |

The library entry reads the blend/index before request assignment. Exit links
and appends before replacing requested names with returned refs, and ignores
context exception arguments. Thus an exception inside the body after setting
requests is not rollback; make assignments last, after admission. Reject returned
`None`, renamed/colliding items, unexpected reuse or changed request ordering.

Append walks ID dependencies. `link=False` and nonrecursive append do not mean
only requested IDs were ever read: other-library dependencies can remain linked.
A post-append census describes surviving IDs, not every transient ID or read.
This is acceptable for the stated inspection scope; it must remain explicit in
the receipt. Do not claim OS filesystem denial or universal external-read absence
from offline mode, disabled autoexec or a Python file wrapper.

The packed-data RNA getter copies already embedded bytes; it is distinct from
image buffer/pixel acquisition. Bound packed sizes and total bytes before
copying data. Hash bytes and inspect encoded headers without image.size,
channels or pixels getters. The existing exporter-source review establishes that
image dimension/encoding accesses can precede late image hooks, so none of those
export paths belong in this inspection.

## Required observations and supported outcome

Capture complete baseline and final `bpy.data` ID sets, not only requested
materials/images; account separately for embedded material node trees. Inspect
new ID categories, actual returned Material refs, linked-library state, reachable
node groups/images, ID-valued properties and animation/driver dependencies.
Keep the graph and actual reference relation private. An added geometry ID is
recorded and causes refusal; do not delete it to manufacture a clean census.
Likewise record/refuse linked or otherwise unsupported dependencies before any
export or binding. Do not touch vertex arrays merely to count an unexpected mesh.

Distinguish actual dependency links from append provenance metadata. The reference
append code itself adds library weak-reference records to eligible local IDs.
A local Material's weak-reference path is not, by itself, proof that an external
resource was loaded or evidence of a reachable Image dependency. Record its exact
typed metadata privately; do not infer roles from path text or suppress it.

Keep preexisting factory/editor IDs distinct from added/reachable IDs. An
unrequested Viewer or other editor resource elsewhere in B is not automatically
a selected material input; an actually reached unsupported resource still
refuses. Unknown categories or unobserved edges remain unresolved. No dependency
is deleted, shader simplified, resource renamed or external path fetched to turn
a refusal into success.

The public success statement may say: this exact owned B copy/build appended
the requested Material refs in a disposable private job; the recorded surviving
ID/graph/packed-header profile matched the declared inspection policy; originals,
owned input bytes and source/runtime identities remained unchanged; the owned
launcher, job and desktop closed with fresh physical observation. Raw graphs,
names/paths, packed bytes and native arrays are not public report payloads.

It must **not** say that no historical geometry/transient ID was ever loaded,
no C-level external read occurred, every material fits the future exporter,
native IDs came from B, or B/native rendering fidelity was proved. A profile
refusal is still useful inspection evidence and remains a refusal.

All historical/native point causality, default MDL49 engine behavior, material
binding to fresh meshes, resource/export binding, non-NORMAL equivalence,
`2e-5` normal fidelity and HAS adoption flags stay false. A later fresh-mesh host
must establish its own native/slot/skin relation; it cannot inherit that proof
from material enumeration or this inspection's four returned resources.
