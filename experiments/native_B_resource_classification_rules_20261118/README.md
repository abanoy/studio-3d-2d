# B saved resource classification rules

Experimental source packet. This pure classifier labels saved, authenticated
metadata; it does not load Blender, inspect a process, open a discovered path,
read a native/private body, save a model, export, or change the application.
The two old collectors copied here are byte-exact test dependencies, not a new
native runtime. Old packets remain immutable.

The Root-attested actual observation is bound by
`../native_B_ownership_root_classification_20261118/RESULT.json`, SHA256
`3481821aef0643fdaf75cbfef79d624e1671a5a4243ce9459b5921f9ad1a3dd0`.
Its typed findings motivated these rules. This packet has not applied them to
the private native outputs; its results are synthetic CPU observations only.

## Small API and schema

`classification.classify(resource_private, resource_public, ownership,
limits=Limits())` returns `(private_classification, public_summary)`. Pass the
original `has_private_B_resource_metadata_survey_1` dictionary, the original
`has_B_resource_metadata_survey_summary_1` dictionary (the nested survey summary
when the diagnostic uses a wrapper), and the separate
`has_private_B_resource_ownership_metadata_1` dictionary. The caller must first
authenticate the saved bodies and collector/runtime provenance. This pure API
does not authenticate files or make an untrusted input trustworthy.

The consumed schema is the exact saved collector vocabulary: survey image IDs,
source/type/paths/packed metadata, original issues/material references and both
external-path tables; ownership typed IDs, local/linked flag, path observations,
weak descriptors/property paths, exact joins, Viewer graph lists and explicit
IMAGE_EDITOR witnesses. Additional metadata remains bounded and hash-bound.
The classifier recomputes exact raw joins and validates consumed identities,
coverage, status, original issues and graph/UI bindings. It cannot reconstruct
the complete `user_map` because the saved collector retains only Viewer graph
summaries. Source authentication is therefore required independently.

Malformed, stale, contradictory or over-budget evidence raises a fixed-code
`ClassificationError` without a partial result. Valid insufficient/ambiguous
evidence receives `UNRESOLVED`. Every saved external-path row and every image
gets a separate classification row. The original issue list is copied intact;
all input bodies remain unchanged and all three hashes bind the new output.
The public output contains counts, hashes and fixed scalar claims, not private
paths, names, RNA data paths or session pointers.

## Four labels

| Label | Necessary evidence and meaning |
| --- | --- |
| `REQUIRED_EXTERNAL_REFERENCE` | One exact observed path owner, a nonempty exact raw path also present in the unpacked table, and either a typed Library owner or one FILE/IMAGE ID with identical filepath/filepath_raw and no packed entries. Competing FILE path claims or weak-descriptor joins remain unresolved. This records a typed external reference, not existence, content identity or export relevance. |
| `LOCAL_APPENDED_ASSET_PROVENANCE` | One exact observed owner/path and one matching LibraryWeakReference descriptor for that owner; the descriptor's property path is observed and ends with `.library_weak_reference`; its target ID is nonempty; the owner's linked-library field is false; no competing FILE path claim or duplicate weak descriptor exists. The general owner's human-readable RNA path may remain unobserved. The label describes the stored append-reuse provenance role of that exact property. It does not prove that the whole model has no external dependencies. |
| `INTERNAL_VIEWER_EDITOR_OBSERVATION` | Typed VIEWER plus RENDER_RESULT/COMPOSITING, local image with empty paths/no packed entries, no saved direct ID/material-node/reachable-material/other-ID owners, and explicit bound IMAGE_EDITOR witness membership with a typed Screen owner and area/space/image identities. The source collector observes `space.type` and `space.image` before appending that witness. Its optional human-readable RNA path may be UNOBSERVED and that status is retained. |
| `UNRESOLVED` | Everything else, including aliases, ambiguous owners/descriptors, unsupported kinds, packed FILE image paths, weak properties without observed paths, linked weak owners, and Viewers with graph references or without UI witnesses. |

Raw path equality is literal: no basename, filename role, normalization,
case-folding, resolved-path alias or inferred brush role is used. A typed
Library defensive positive fixture does not weaken the unchanged original
collector's immediate linked-library refusal.

Viewer rows always retain `non_IMAGE_EDITOR_UI` and
`implicit_viewer_producer_semantics` as unobserved. Every path row retains
external-content existence/identity and export-dependency relevance as
unobserved. `ID.users` is preserved and checked against the saved Viewer value;
it is not equated to `user_map` or UI counts. Zero reported graph owners proves
only the saved observation's scope, not global unreachability.

## Bounds and verification

Default hard ceilings are 512 KiB per input and output, 60,000 JSON nodes,
1 MiB aggregate text, 4,096 bytes per string, 24 nested levels and 4,096 entries
per collection. Limits may only be reduced. A type/structure/text walk precedes
JSON serialization; cycles and non-JSON objects are refused. These are bounds on
already supplied CPU metadata, not on a future JSON decoder, Blender allocation,
native `user_map`, process memory or filesystem activity.

Run from this packet directory:

```powershell
& 'C:/Program Files/Python313/python.exe' -B -m unittest -v test_classification
```

The 16 CPU methods cover the exact six-refusal synthetic pattern generated by
the old collectors, local Material weak provenance with an unknown general RNA
path, both internal Viewer types, optional unknown UI paths, required Library and
unpacked FILE references, packed/alias paths, duplicate owners/descriptors,
competing FILE claims, graph/UI/stale-ID failures, malformed schemas, each
budget, input retention and absence of IO/native/process/path-normalization
calls. `CPU_RESULT.json` and `CPU_TESTS.log` record this source-only run.

No resource is accepted, excluded or silently ignored. RESOURCE_PROFILE_REFUSED
and all six original issues remain. Export provenance is not recomputed; the
earlier actual UNKNOWN remains unchanged. Normal repair, strict31, original
2e-5 comparisons, fidelity, export equivalence, carrier and adoption remain
unqualified. Formal implementation 52/54 and acceptance 55/62 remain unchanged.
Root may later apply this API read-only to authenticated saved private bodies
and publish only a scalar/hash projection in a separate packet. No new native
admission or rerun is supplied here.
