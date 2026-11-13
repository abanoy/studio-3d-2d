# Read-only Source appearance table catalogue candidate

This is an output-only, stdlib component for reviewing static import choices. It opens no files, acquires no archive members, imports no converter or native reader, and changes no original input. Its tests construct small binary buffers by hand. No real MDL, archive, Steam asset, Blender, Godot or graphics process was used for this packet. Main was frozen at the parent-reported `1236796865e677b150a2d7e2add20f2aac5325fe`; this packet makes no claim to be a main-source port.

`source_mdl_choices.catalogue(raw: bytes, source_sha256: str, member: str = '') -> dict` returns a complete supported catalogue or raises `CatalogueError`, a `ValueError` carrying a stable `code`. The enclosing input loader must verify the supplied lowercase original-source SHA, select/acquire the member safely, and preserve its own original/runtime stamps. The module computes `native_mdl_sha256` from the exact supplied immutable bytes. It never equates the native header checksum with a SHA. `member` is canonical relative resource context; empty is allowed for loose MDL. It is not opened here.

The success format is `studio_source_mdl_choices_1`:

- `original_source_sha256`, `selected_member`, `native_mdl_sha256`, `native_mdl_bytes`, `native_version`, `native_checksum` bind provenance and inspected bytes.
- `materials` has indexed `name`, `raw_name_sha256`, and `display_name` rows.
- `skins` has `index`, exact `material_indices`, and corresponding `material_names`; duplicate skin rows and repeated material names preserve their distinct numeric indices. `skin_reference_count` retains the native row width.
- `bodygroups` has `index`, native `name`, `raw_name_sha256`, separate `display_name`, observed positive `native_base`, and `choices`. Each choice has `index`, native `name`, `raw_name_sha256`, separate `display_name`, `vertex_count`, and `true_blank`.
- `catalogue_sha256` hashes ASCII canonical JSON of every other result field (`sort_keys=True`, `ensure_ascii=True`, `separators=(',', ':')`). A member/source-context change therefore changes the digest even when native bytes match.

`name` is Latin-1 decoding of bytes before the terminating NUL, a reversible byte mapping rather than a claim about the author's encoding. It is not stripped, case-folded or translated. Its SHA hashes those exact pre-NUL bytes. Empty group/choice names get a display fallback only; ASCII/C1 control characters are escaped only in `display_name`. A literal name `blank` with nonzero vertices is visible, while a zero-vertex choice with any name is marked `true_blank`. Native indices, never display text, identify selections. Duplicate exact bodygroup names refuse because the later converted-container mapping is keyed by those names; duplicate material/choice names remain representable by native indices.

The renderer/converter remains authoritative for selected-object ownership, blank/object correspondence, native column-to-material mapping and converted variant count. A successful metadata catalogue does **not** establish those facts. A very large nonnegative native vertex count is recorded without allocating/reading vertices and without claiming geometry validity.

## Documented binary scope

The published independent reader and its format review document the common MDL49 prefix: magic `IDST` at0, signed version49 at4, unsigned checksum at8, declared byte length at76, material count/absolute offset at204/208, skin columns/families/absolute offset at220/224/228, and bodypart count/absolute offset at232/236. Only this240-byte prefix is inspected/reserved; it is not represented as the complete native studio header.

Material records are64 bytes with a signed name pointer relative to each record. Skin entries are unsigned16 row-major material-table indices. Bodypart records are16 bytes (`name_offset`, `model_count`, `base`, `model_offset`); model offset is signed relative to the bodypart. Model records are148 bytes, containing a NUL-terminated fixed64-byte name and signed vertex count at80. No host C++ pointer sizes are used. A backward relative model/name pointer is supported when its target is in-bounds and does not overlap structural tables. No file alignment is invented.

The local documentation points to Valve's public [studio.h](https://raw.githubusercontent.com/ValveSoftware/source-sdk-2013/master/src/public/studio.h), whose public header version is48, and the independently reviewed pinned SourceIO revision `fe24260b97ac03b899d9b5d4f0fd7b34772f3647` for corroborating common MDL49 structures. This is a bounded compatibility scope, not a claim that every MDL49 producer/layout is supported. Neither implementation is imported here. Exact local reference hashes are in `SOURCE_BASES.json`.

Every inspected structural table is registered before following external name pointers. Aliased/partially overlapping tables and external strings overlapping an inspected table refuse; fixed model-name fields are intentionally read only inside their own checked model records. Exact shared or suffix-pooled external strings are allowed outside those tables. Uninspected native structures are not traversed and their possible overlaps/validity are not certified.

## Bounds and deliberate refusals

Input must be immutable bytes,240 bytes through16MiB, with exact declared length, `IDST`, version49. Counts are bounded to2048 materials,2048 skin columns,256 skin families,256 bodygroups,256 choices per group and4096 total choices. Strings include a NUL within1024 bytes (within64 bytes for model names). Every skin index must be below native material count. All table ranges must be in-bounds outside the inspected header prefix and pairwise disjoint.

The supported catalogue requires a nonempty material/skin table, nonempty material names, at least one choice per existing group, and a positive native group base. An empty bodygroup table is supported only with its offset0. These conservative compatibility refusals do not redefine the historical default importer. Mixed-radix base semantics, mesh counts, geometry offsets, bones/unique bone names/parents, sidecars, material resources, flexes, animations and VTX/VVD are intentionally not validated here.

The full result, including digest, must fit256KiB of deterministic two-space ASCII JSON. Streaming JSON encoding checks the cap before accumulating an excessive result. There is no successful truncation. `json_bytes(result)` returns exactly this bounded deterministic encoding. Loaders should use it rather than add unbounded formatting or decoration. The code limits input-driven allocations using the above table counts and does not allocate by vertex counts.

The test command is `python -B test_source_mdl_choices.py`. Each invocation preserves a fresh `runs/<time>-<nonce>/unittest.log` and `result.json`, including parser/test SHA,size,nsmtime before/after. Results cover authored buffers only. Earlier successful source versions are historical evidence, not proof for later changed code. `PACKET.json` identifies the final frozen proof and source hashes.

`scope.native_fidelity_verified`, `scope.resources_verified` and `scope.converted_object_correspondence_verified` remain false on every success. Native flex evaluation, shaders, jiggle, animation and broader native geometry acceptance remain separate work.
