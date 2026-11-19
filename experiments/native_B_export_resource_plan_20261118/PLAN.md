# Minimal candidate adapter and proof obligations

## Authenticated observations and scope

Root's `native_B_issue_attribution_20261118/RESULT.json` binds the original
resource payload `d47ed4cc…`. All four image-issue rows are the two codes on
Viewer images 2/3. FILE/IMAGE records 0/1 each have one packed part and **zero
original image issues**. The other two issue rows describe the same weak-path
reference as recorded in `all` and `unpacked` path categories. The ownership
projection binds it to one local Material's exact `ID.library_weak_reference`
property, with no linked library. It is not an unowned image dependency.

Both Viewer records have zero observed direct ID users, material-node
references, reachable materials or other ID owners, and one IMAGE_EDITOR
reference each. Non-IMAGE_EDITOR UI and implicit Viewer-producer semantics
remain unobserved. These are metadata observations, not resource acceptance.
The original six issues and refusal remain unchanged.

## Pinned exporter argument

The normal material route is primitive material index/slot ->
`get_base_material` / `gather_material` -> material texture sockets ->
`gather_texture_info` -> `gather_texture` -> `gather_image` -> shader-tree
search for `ShaderNodeTexImage` -> `ExportImage` encoding. The search traverses
linked sockets and node groups. An unrelated editor image is not an input to
that route. Actual selected objects/materials/socket/image IDs still require
a new exact exporter-use binding; a name or UI-reference count is insufficient.

The optional `traverse_additional_images` path explicitly filters out source
`VIEWER`. **The main material image route has no equivalent Viewer-source
filter.** A Viewer connected to an exported shader socket can still reach
image encoding. Therefore the exclusion argument must be scoped to the
observed image identities, exact material graph and frozen exporter paths.
Do not delete Viewer IDs, change their UI references or globally accept every
Viewer. User extensions and pre-export/post-export callback lists can change
the gathered data; their exact empty/approved registries must be bound.
`export.save` can also call `scene.frame_set(0)` before gathering and restore
the original frame afterwards. Freeze the current-frame option and qualify
frame/depsgraph/handler state at the actual gather boundary, not only during
the earlier survey. None of this proves all-Blender/UI reachability closure.

No installed exporter Python source references `library_weak_reference`.
The local Material's weak property is append-origin metadata, while its actual
`library` is absent. The exporter obtains material/image data from admitted
live datablocks, not this weak pathname. This supports leaving this exact
property unchanged without copying its target for the glTF stage. It does not
prove preload IO confinement, general weak-reference semantics or existence
of the weak path; no external path was opened or statted by this analysis.

For a clean FILE image, `ExportImage.__encode_from_image` first uses
`packed_file.data` when present. Its disk-read branch is the alternative for
an unpacked file. Thus a packed FILE image does **not** require external copying
merely because a filepath string exists. Keep both packed payloads in the
byte-identical owned blend; no unpack, repack, reload or filepath change is
required by this candidate plan.

Packed data does not guarantee identical output bytes. Channel composition,
MIME mismatch or another encoding branch can read image buffers and create a
temporary encoded image. The exporter also reads dimensions in relevant
paths. Those real export operations need owned TEMP/TMP/output and bounded
resource policy. They do not justify a pixel read during ordinary metadata
discovery or a claim that the prior survey already proved IO confinement.

One option is particularly material: `gltf_keep_original_textures=true`
constructs an original-URI image and calls `__gather_original_uri`, which
resolves/tests the original path and may return no image if it is absent.
This can omit a packed image despite its embedded payload. A candidate new
GLB policy should explicitly freeze `export_keep_originals=false` (internal
`gltf_keep_original_textures=false`) and then establish equivalence against
retained B. Do not infer B's historical option branch from hashes; it remains
UNKNOWN. Freeze all image/quality/WebP/material/unused-image/unused-texture,
selection, extras and extension/variant options affecting the route.

## Smallest candidate plan

1. Copy the original B blend exclusively into an owned directory with its
   whole-file identity unchanged. Keep FILE images 0/1, Viewer IDs 2/3,
   material/node graph and local Material weak-reference metadata untouched.
2. Admit the two packed FILE records only under the unchanged FILE/IMAGE,
   one-packed-part, non-dirty, no-multiview/no-alias/no-linked-resource profile,
   preserving their encoded sizes/hashes and all relevant image properties.
   Raw `filepath`, `filepath_raw`, packed-part paths, names, basename spellings
   and raw-path equality classes remain unchanged, including empty paths.
3. Add a separately pinned exporter-scoped disposition for the exact two
   observed Viewer records and exact local weak property. Keep every original
   issue row as evidence. This new disposition is neither a rewrite of the old
   collector nor a blanket ignore rule.
4. Return `external_copy_requests=[]` only when authenticated complete metadata
   plus the frozen actual exporter-use relation prove no other file-consuming
   dependency. The current evidence supports proposing that plan; it does not
   itself complete the actual-use proof or accept the resource profile.
5. If a new actual gathered dependency is unpacked, resolve it against the
   original B parent, require exact approved descriptors and bounded stable
   regular-file reads, copy exclusively to owned storage, preserve basenames
   and raw-path equality relationships, and prove before/after identities.
   Reject unknown/linked/ambiguous dependencies. Do not build a general copier
   or copy the weak-reference target merely to clear an issue counter.

Hash-renaming packed paths is specifically inappropriate: `image.py` can
choose composed image names using raw filepath equality and basenames. MIME
selection may use raw suffixes; empty packed paths instead permit magic-byte
checks. A remap can change non-NORMAL image metadata even with matching pixels.

## Gates before an actual carrier export

- Bind exact approved source/runtime catalogues and a fresh closed native /
  graphics context. Historical admissions are not current authority.
- Bind original/owned blend identities, complete current image/material/group
  graph and packed hashes. Reopened-session pointers are new; any session join
  needs explicit exact identities and alias preservation, not heuristic names.
- Bind actual selected object -> material slot/index -> socket/tree -> image
  use, including node groups, unused texture/image paths, material variants and
  exact approved user extensions/pre/post callbacks. Refuse any Viewer entering that relation. Recheck that
  no handler/hook or intervening mutation invalidated the observed graph.
- Freeze the explicit new options and prove their actual non-NORMAL output
  against B; do not relabel UNKNOWN historical options. No image omission,
  fallback warning or unexpected encoder branch may be silently accepted.
- Preserve original source bytes/stamps, owned packed hashes, image metadata
  and graph structure around export; keep all writes/temp work owned. Actual
  output comparison must include exact encoded image bytes, material/texture /
  sampler metadata and bindings, not only equal pixels or packed input hashes.
- Retain the separate independent point join, exporter-to-final primitive
  relation, strict input-domain/semantic checks and exact corrected NORMAL
  contract. Resource planning does not complete any of those gates.

## Pure CPU helper that could be implemented next

Proposed API: `build_export_resource_plan(authenticated_resource,
authenticated_ownership, frozen_policy, independent_exporter_use_relation)`.
It would authenticate both saved payload joins, retain all six issue rows,
verify exact per-ID/per-property witnesses, and return private action rows:
`KEEP_PACKED_UNCHANGED`, `LEAVE_EXACT_NON_EXPORTER_VIEWER`,
`LEAVE_LOCAL_APPEND_PROVENANCE`, plus explicit bounded external-copy requests
or unresolved refusals. It would perform no IO or Blender mutation and could
not manufacture the native exporter-use relation.

Meaningful synthetic negatives would include a Viewer used by an exported
socket, unknown hooks/options, a weak-path owner/property mismatch, missing or
changed packed bytes, altered path equality/basename/MIME behavior, and an
unowned external dependency. **That helper and those tests are not implemented
or run by this plan packet.**
