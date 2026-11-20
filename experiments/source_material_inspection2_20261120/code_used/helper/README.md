# Inspector2: one authenticated owned-source Library

Source preparation only. No tests, native assets/parser, Blender, processes,
CIM or Git were executed by this author. The earlier helper1cf and eight-file
first host remain unchanged, including their first actual refusal evidence.

Root reported the first actual cold inspection refused
`UNSUPPORTED_ADDED_ID_CATEGORY` after four exact native-selected Materials were
appended from a five-Material B catalogue. The exposed ID census changed from
38 to45 with additions Materials4/Images2/Libraries1, original IDs unchanged.
No graph qualified and no packed bytes were read. The safe diagnostic observed
four Output, four Principled and four TexImage node types. Those observations
do not establish the Library's pathname, parent, dependency relation or cause.

## Exact successor policy

The helper starts from the exact1cf source and keeps its existing ordered
four-name subset, assignment-last append, ID survivor/reachability, non-ID RNA
canonical identity, graph, packed-byte and prospective image budgets. It adds
only this bounded branch before any graph/encoded-byte gate:

- The initial complete exposed BlendData census must contain no Library IDs.
- Added IDs may be Materials, Images and at most one Library. Every other
  category, a second Library or any linked Material/Image/embedded NodeTree
  still refuses. No unexpected ID is deleted or altered to force acceptance.
- A retained Library must have exact genuine `bpy.types.Library` type, cached
  original ID identity, `library is None`, and a bounded nonzero actual pointer.
- Its inert `filepath` metadata must lexically match the authenticated owned B
  passed by Root, under Windows case/separator normalization. Both paths must
  be local absolute drive paths, with no UNC/device/blend-relative path, NUL or
  alternate data stream. No resolve/abspath/exists/stat/file read is performed
  by this helper. Caller authentication and Root's later source/copy preservation
  supply actual file identity; a matching pathname alone does not.
- `parent`, `packed_file` and `archive_parent_library` must all be None;
  `is_archive` must be exactly False; `archive_libraries` must be empty. This
  branch admits no packed-library or retained other-library/archive dependency.
- The actual Library ID is retained privately. Its exact pointer and raw
  filepath metadata plus all above conditions are checked again after the
  packed/graph observations and final unchanged ID census.

Zero retained Library IDs remain allowed, but the result then states count0
and does not claim a Library was verified. A successful count1 records only the
canonical pathname SHA256, never its name, pathname, pointer or actual object.
All normal/export/resource/non-NORMAL/dependency-closure/native/historical/app
qualification flags remain False. No absence of transient C reads/IDs follows.

Private API remains
`inspect_material_library(bpy, owned_path, material_names, enumeration_module)`.
It returns the prior private refs plus `retained_owned_source_library` (actual
Library or None). Summary format is now
`has_material_only_library_inspection_summary_2`; success is
`INSPECTED_MATERIAL_ONLY_OWNED_LIBRARY_AND_PACKED_PNG_HEADERS_2`.
New summary fields are `retained_owned_source_libraries`,
`owned_source_library_validation_attempted`,
`retained_owned_source_library_verified`, and conditional
`retained_library_filepath_sha256`. Refusals retain safe counts and the fixed
reason. Header, profile, local-resource and all budget gates remain unchanged.

## Primary source basis and limits

All primary links below are pinned to Blender commit
`ec6e62d40fa9e9d1bea33ad5d00148c99a4f0832`. They describe public source, not an
attestation of the installed binary's actual result.

[`bpy_library_load.cc`](https://github.com/blender/blender/blob/ec6e62d40fa9e9d1bea33ad5d00148c99a4f0832/source/blender/python/intern/bpy_library_load.cc#L661)
(blob `c2902e04ca6781801345510fe5625076f85f0777`) creates the library context
from the absolute source path, calls `BKE_blendfile_link`, then
`BKE_blendfile_append` for append mode, finalizes, and replaces requested names
with actual returned IDs. It does not promise that the resulting exposed ID
census contains no Library ID. Default nonrecursive/reuse-local=False behavior
remains explicit in the source.

[`blendfile_link_append.cc`](https://github.com/blender/blender/blob/ec6e62d40fa9e9d1bea33ad5d00148c99a4f0832/source/blender/blenkernel/intern/blendfile_link_append.cc#L1215)
(blob `ac0ae3df96cc2daaef86594d465adae19f364314`) distinguishes directly
appended source libraries from dependencies and can keep other-library IDs
linked in nonrecursive mode. Its append tail remaps/deletes selected linked
IDs, clears temporary IDs and finishes versioning/runtime cleanup; the
[`relocation cleanup`](https://github.com/blender/blender/blob/ec6e62d40fa9e9d1bea33ad5d00148c99a4f0832/source/blender/blenkernel/intern/blendfile_link_append.cc#L2081)
has separate explicit unused-library deletion logic. Thus a blanket ban on all
Library IDs conflates a retained source record with an actually linked resource,
while a blanket allowance would miss retained external dependencies.

The same append source keeps weak references as source filepath/ID-name reuse
metadata. This does **not** prove that the actual observed retained Library was
caused by weak-reference bookkeeping, nor that it has no external dependencies.
Inspector2 requires observed actual fields instead of that assumption.

[`rna_ID.cc`](https://github.com/blender/blender/blob/ec6e62d40fa9e9d1bea33ad5d00148c99a4f0832/source/blender/makesrna/intern/rna_ID.cc#L2689)
(blob `f1985d5d234c277043d4ce60bb965f1c6771a2bd`) defines `Library` as an ID,
its literal filepath, runtime parent, packed pointer and archive relations.
These getters expose retained metadata/pointers without loading an image buffer
or fetching that external file. The actual cold successor run must still
qualify the installed API, exact owned-source relation and unchanged inputs.

## Prospective Root-only checks

The exact B2 enumerator6c3 is copied beside the helper, so tests depend on a
reviewed packaged source rather than an output cache elsewhere. There are42
authored synthetic methods: the original31 plus11 owned-Library cases covering
positive shared/local resources, normalized owned path, foreign path, extra
Library, parent/packed/archive relations, wrong type/original/locality/pointer,
linked resources, preexisting Library, post-read metadata drift, unsupported
path forms, and truthful count0. They were not run by the author.

```text
python -B -m unittest test_material_inspection
```

Only Root may execute that suite, then a separately versioned host and fresh
bounded actual cold job. This source does not reclassify the earlier refusal
or prove the actual PNG header/profile will pass once the Library is qualified.
