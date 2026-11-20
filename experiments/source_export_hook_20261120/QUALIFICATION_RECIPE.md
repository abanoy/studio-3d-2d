# Actual Source export hook preparation

**UNRUN PROPOSAL, 2026-11-20. No actual export qualification.**

This isolated output packet was authored while Root held the functional source
freeze for the complete Windows suite. Its author read source and wrote only
these new files. The author did not execute the proposed Python/tests, Blender,
SourceIO, a converter, an engine, native/private asset computations, process
queries or Git. Source hash reads are metadata observations, not runtime tests.

The proposal is not connected to Studio or its bridge. It writes no asset, opens
no native file and invokes no operator. Its import is standard-library only and
performs no IO. `PinnedSurface` reads only the explicitly pinned exporter/helper
Python source when a future host constructs it. The resource gate subsequently
reads only already admitted in-memory packed encoded PNG bytes and metadata; it
does not read pixels or discover external files. Those future actual calls need
the complete separately admitted host and private resource context.

## Files and scope

- `export_hook_proposal.py`: exact source/runtime function checks, cold-cache
  admission, owned reversible patches, one extension collector, swallowed-error
  latch, actual extractor/cache/gather/owning-Mesh/reference bridge to the existing
  `GatherBinding`. No exporter-call retry or ordinary-export fallback exists.
- `resource_gate_proposal.py`: deliberately small active Output / Principled /
  optional Image Texture graph, Base Color and optional Alpha only. Actual socket
  references and root tree context bind to complete `ExportImage` channel
  descriptors, actual Image/Texture/TextureInfo/Material objects and final actual
  root-reference indices. It refuses unsupported graph/resource paths.
- `test_export_hook_proposal.py`: 30 authored synthetic test methods. No native
  fixtures, runtime qualification or claimed test results. The fake surface
  deliberately bypasses `PinnedSurface`; that distinction is explicit.

Source review caught two false-refusal bugs before any execution: the private
`__to_reference` lookup must use `_GlTF2Exporter__to_reference` while `__init__`
must remain unmangled, and stripping decorators must preserve the earliest
decorator line as `co_firstlineno` when comparing complete code objects. Tests
explicitly exercise both; they remain unrun by the author.

## Exact source-derived boundaries

Both `primitives.gather_primitives` and `__gather_cache_primitives` have **six**
arguments. Their material argument occupies different positions. Their real
return lists are retained by reference. A cache hit missing the fresh creator
observation, repeated extraction, evaluated-mesh substitution or aliased object
refuses. The existing binder's two-object/four-primitive/no-new-split budgets
remain unchanged.

The extractor observer derives the pinned complete class AST and its exact
inverse from the published helper, then this proposal installs the resulting two
method objects using its ownership-aware patch scope. It does not use the older
helper's unconditional restoration context. Every owned original is restored by
identity on success, partial installation or operator failure. A foreign patch is
left untouched and latches a hard refusal; other owned slots still restore. A
real export exception remains primary.

`blender_idxs` is exact `np.uint32`; the material slot is an exact `np.uint32`
scalar. The nonshared inverse-topology array is exact `np.intp`, nonnegative and
bounded, because the pinned `fast_structured_np_unique` delegates to
`np.unique(..., return_inverse=True)` and bundled NumPy `_unique1d` allocates its
inverse with `dtype=np.intp`. A blanket unsigned inverse requirement would
incorrectly refuse the actual source. No arbitrary `int()` conversion is used
for point/topology/scalar admission. Only lossless `.tolist()` / `.item()` occurs
after exact types/dtypes/shapes/bounds. The actual complete NumPy runtime and
native extension catalogue remain future host admission requirements.

The resource graph is admitted before export and rechecked before ordinary
gather. This matters because ORM's `check_same_size_images` reads image metadata
earlier than the image descriptor hook. Unsupported ORM/other input links/groups
already refuse. The `image.__get_image_data` wrapper checks actual root
`NodeSocket.socket` and `group_path == [actual material.node_tree]` references
**before** calling the genuine function and checks the complete returned channel
descriptor **before** subsequent encoding. The late `gather_image_hook` supplies
evidence, not authorization. Newly constructed NodeSocket wrapper identities are
not mistaken for actual socket identity.

The minimal resource profile is local original Materials, one supported graph,
packed clean static FILE/IMAGE PNG inputs, unique Image names and a single image
per material, with source images unshared between Materials. The graph snapshot
also freezes the exporter-read `use_backface_culling` scalar. It preserves raw
image path/name/metadata classes. Both image paths
must be empty or have a PNG suffix: AUTO JPEG/WebP suffix conflicts refuse before
encoding. Alpha-only composition also refuses before encoding; that would
otherwise enter pixel/temp paths despite having packed source bytes. External
images, UDIM, RGB-to-BW fills, numpy computations/stored values/original-image mode,
alternate links/groups, copied final Materials, WebP/extensions and unsupported
image paths refuse. Before any RNA size/channels getter, all authenticated packed
PNG IHDR headers and CRCs are validated: static noninterlaced RGB/RGBA 8-bit only,
64 MiB prospective RGBA F32 memory per image and 128 MiB total. Native getter
dimensions must then equal the admitted header. This bounds that prospective
buffer policy; it is not a PNG decoder or proof that opening the original blend
has no other memory/resource effects. A one-UV0 mesh with implicit Vector input is a separate
mandatory host admission; this module does not yet inspect the mesh UV layer
policy itself. The exact final primitive Material must be the observed base
Material, so the exporter's nonzero-texcoord deepcopy cannot silently pass.

Mandatory actual observed options include GLB, attributes on, nonshared
accessors, EXPORT materials, keep-originals off, Draco off, AUTO images, unused
images/textures off, add-WebP/fallback off, current-frame on and animations off.
PNG input magic plus preflight suffix and final PNG MIME/source constraints
refuse AUTO WebP's extension-source branch too. The future host must freeze the
complete invocation profile; this minimum dictionary is not the full production
profile. The exact sole collector and empty pre/post callback lists are checked
repeatedly. Before yielding control to the export operator, an inventory of
authentic enabled-addon module namespaces rejects foreign exporter constructors
and callbacks without invoking them. Sole-extension checks in pre_export_hook
alone would be too late: foreign extension constructors execute first. The host
must supply and freeze the actual enabled-addon collection, not a subset, and
admit its module/runtime catalogue.

Missing image/texture/material events refuse after the operator, including the
exporter's swallowed image-encoding failure that can return an empty image before
the late hook. Exact actual reference events and serialized resource counts and
links are checked. This is **not** full material/encoded-image semantic
equivalence, a complete shader evaluator or a global unreachability proof.

## Root recipe

1. Finish and physically close the full Windows suite, preserve its frozen source
   and evidence, and review/hash this isolated packet. Run only the synthetic
   checks first, from this checkout:

   ```powershell
   python -B -m unittest discover -s output/source-export-hook-prep-20261120 -p test_*.py -v
   ```

   Expect **30 methods / zero skips** if unchanged. There is no test result yet.
   Run under the real bundled Python too before any native use; these tests
   specifically depend on CPython complete code-object/line-table behavior.

2. Independently review/admit a new one-cold-export hidden-desktop host. This
   packet deliberately does not supply a launch script. Preserve original B,
   setter, native and provenance hashes/stamps and close the exact owned process
   job after one attempt. Disable scripts/UI loading. TEMP/TMP and cached
   `tempfile.gettempdir()` must resolve inside owned storage before encoding.
   No preferences, installed exporter, original blend or source asset save.

3. Establish **current** point identity independently. The published historical
   ordered-native-write to saved-B numeric relation matched 9,661 points and
   42,702 corners, but it has no retained native-ID attribute and does not prove
   hidden causal identity for intrinsically indistinguishable coincident points.
   Eight normal ambiguity classes remain a known concern. Do not break ties by
   proximity, current normals, output carrier, group/UV equality or cache order.
   If exact current admission remains unresolved, STOP before exporting. The
   callable `point_admission` is a future host obligation, not a success-token
   shortcut; it must recheck actual object/mesh ownership, point order and the
   authenticated joins. No qualification flag here upgrades it. A newly admitted
   SourceIO import with observed native integer lineage may supply a separately
   named current derivative later; it does not relabel historical B.

4. Admit material-preserving original B's disposable copy, exact object/mesh/
   source Material refs, selected face slots, supported modifiers/rest/skin/UV0,
   complete scene snapshots and independently authenticated packed PNG tickets.
   The original B's historical branch/options are still UNKNOWN. Refuse anything
   outside this small profile and retain the refusal; do not simplify materials,
   delete Viewer resources or alter source channels to force it through.

5. Load exact actual exporter module objects plus the published pinned binder and
   observer. Construct `PinnedSurface`, `SimplePackedResources` and
   `ExportHookSession`. Add only the admitted one-based native-ID FLOAT/POINT
   attribute in memory after collision/integral-F32 checks. Within
   `session.install(...)`, call one explicit export operator and require its
   actual FINISHED result, then leave the scope. The host must restore the owned
   attribute, any authorized resource remap and scene context in its own finally,
   even when the hook scope refuses. No second collector beside the production
   bone collector; an eventual combined production collector needs separate
   review. This isolated collector is not production composition.

6. Outside the operator and patch scope, check the latch and all exact original
   identities. On immutable separately named GLB bytes call `session.finish`.
   Retain the private returned primitive/source relation only in private storage.
   Public evidence may contain compact counts/errors/source/input hashes only,
   never points, normals, weights, UVs, source IDs or graph/descriptor arrays.

7. Run the unchanged strict raw/domain and `compare_qualified_non_normal` gates
   on retained B versus carrier: exact decoded non-NORMAL bytes/types/order,
   topology, transforms, skin/weights, supported morphs, materials and encoded
   images, and other semantics. `finish` is not a substitute. No row-reordering,
   new split allowance or tolerance change to obtain a pass.

8. Only after those gates, separately apply existing append-only correction to a
   new derivative, preserve all old BIN bytes, remove only the owned carrier
   reference and prove exact source-normal word/transport and preservation
   contracts. Then apply the unchanged independent source normal **2e-5** gate.
   The retained original gate remains FAILED (8,364 / 9,661 above threshold;
   max 0.00121654672362075). Do not revise that evidence or confuse the carrier
   binding with a normal-fidelity pass. Application adoption stays a later gate.

## Pins and unresolved qualification

`export_hook_proposal.PINS` contains 17 exporter-source SHA256s, freshly checked
as source reads by this author. Helper pins remain the published observer
`15145030fab5b662be490e519ff59f870c4e9c0352766ff59bf3da3f12198f7b` and binder
`617c062b516ecefa5fab0a6ec8f98163a3b13f76896969cb22102f859323b850`.
Bundled NumPy `_arraysetops_impl.py` source read SHA256 is
`d112be99ab44d57b78642fe4606f8b040022549022d319bcea66a89c1fba5ee6`.
The latter is a derivation pin, not yet an automatic runtime admission in this
prototype. Complete runtime/catalogue/NumPy/SourceIO identity, current B identity,
actual API admission, resource metadata correctness on actual B, source normal,
semantic equivalence and product adoption are **all unqualified** here. Actual
observations/refusals and any successor source hash must be retained separately.
