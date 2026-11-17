# Pinned Blender 5.1 custom normal carrier audit

Status: **source-only support for an isolated carrier experiment; no native repair qualified**. No engine, real Win32, CIM or Git calls ran. No native arrays were read, copied or emitted. Installed tools and functional application files were not changed.

## Source identity

The approved input lock is `experiments/replay_audio_fix_20261115/builder/input-lock.json`, SHA256 `3bb7c2ce75f55dcb53143aab0df5ab8b39c68180617092664a579126fb09cfb6`. Its exporter root is `C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2`. The exact approved identity reader (SHA256 `5be1d34aa6aced8fc112bee3ecadd489be9b7f38ab710553385bfd77ca500d83`) confirmed **all 120 noncache exporter files**, including membership, bytes, modification timestamps and SHA256, match the lock. Canonical JSON digest of that metadata map: `db1ad603f0d5537cea3c3874b36f05430ccc2360b4cfa597382ddb320fdc51f7`.

The source facts below concern that installed package, not another upstream version.

## Attribute enablement and names

- `export_attributes` defaults to false; the operator describes attributes beginning with underscore. It becomes `export_settings['gltf_attributes']` at [__init__.py:560](<C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2/__init__.py:560>) and [__init__.py:1156](<C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2/__init__.py:1156>). The existing application bridge's export calls at `tools/blender_source_bridge.py:488–495` do not enable it, so a carrier experiment must explicitly pass `export_attributes=True`.
- `KeepAttribute` initially accepts names starting with `_`; the `gltf_attributes` flag must also be true. The user-extension hook can change keep/name decisions. Accepted names are uppercased, and a case-folded collision is warned about and skipped: [blender/exp/primitive_extract.py:174](<C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2/blender/exp/primitive_extract.py:174>) (through line 228). Use an explicit unique uppercase name, inventory existing underscore attributes, and reject a missing/renamed/colliding carrier.
- EDGE-domain custom attributes are skipped. POINT/FLOAT_VECTOR is supported. The normal carrier must be a mesh attribute, not an object custom property or `export_extras` field.

## POINT values travel through the actual split/dedup path

1. `FLOAT_VECTOR` resolves to three `np.float32` components: [blender/com/conversion.py:88](<C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2/blender/com/conversion.py:88>), [blender/com/conversion.py:113](<C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2/blender/com/conversion.py:113>), [blender/com/conversion.py:129](<C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2/blender/com/conversion.py:129>), [blender/com/conversion.py:145](<C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2/blender/com/conversion.py:145>).
2. The dots dtype starts with a uint32 `vertex_index`, then includes all non-skipped custom attribute components. A dot exists for each mesh loop: [blender/exp/primitive_extract.py:317](<C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2/blender/exp/primitive_extract.py:317>) (through line 347). Its vertex identity is populated from `.corner_vert` at [blender/exp/primitive_extract.py:370](<C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2/blender/exp/primitive_extract.py:370>).
3. Underscore attributes dispatch to the generic layer reader at [blender/exp/primitive_extract.py:1137](<C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2/blender/exp/primitive_extract.py:1137>). FLOAT_VECTOR uses `attribute.data.foreach_get('vector', data)` into the F32 array at [blender/exp/primitive_extract.py:1334](<C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2/blender/exp/primitive_extract.py:1334>) (especially lines 1337–1338 and 1364–1366). POINT data is looked up by `self.dots['vertex_index']` and copied to each loop's component fields at [blender/exp/primitive_extract.py:1387](<C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2/blender/exp/primitive_extract.py:1387>) (through line 1400).
4. Both shared-accessor and per-material paths deduplicate the complete structured dots, not just POSITION/NORMAL: [blender/exp/primitive_extract.py:830](<C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2/blender/exp/primitive_extract.py:830>) and [blender/exp/primitive_extract.py:900](<C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2/blender/exp/primitive_extract.py:900>). Regular custom fields are then gathered from those same deduplicated rows at lines 853–857 / 919–923 and [blender/exp/primitive_extract.py:1646](<C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2/blender/exp/primitive_extract.py:1646>).

Inference: a POINT carrier constant for each existing Blender vertex should not create a new equivalence split, because `vertex_index` already distinguishes vertices and every loop of that vertex receives the same carrier. It also follows existing UV/normal/material splitting correctly. This is not a guarantee of identical output vertex ordering or byte-identical indices; a future experiment must verify the actual counts, index buffers and all non-NORMAL accessors rather than assume them.

The default `export_shared_accessors=False` is explicit at [__init__.py:656](<C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2/__init__.py:656>); the extractor chooses the matching branch at [blender/exp/primitive_extract.py:42](<C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2/blender/exp/primitive_extract.py:42>). The carrier must be checked for every primitive in either branch.

## Accessor format and serialization

The regular-attribute setter maps FLOAT_VECTOR to component type FLOAT (`5126`) / data type VEC3: [blender/exp/primitive_extract.py:1665](<C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2/blender/exp/primitive_extract.py:1665>), [blender/com/conversion.py:94](<C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2/blender/com/conversion.py:94>), [blender/com/conversion.py:119](<C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2/blender/com/conversion.py:119>), [io/com/constants.py:8](<C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2/io/com/constants.py:8>). It does not take the BYTE_COLOR unsigned-short normalization path.

Generic attributes go through `array_to_accessor()` with no max/min request and no normalization flag unless data explicitly supplied one: [blender/exp/primitive_attributes.py:239](<C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2/blender/exp/primitive_attributes.py:239>) (through line 251). The ordinary accessor path writes `array.tobytes()` directly, sets count to the row count, sets no accessor byte offset or sparse payload, and retains the component/data types: [blender/exp/accessors.py:37](<C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2/blender/exp/accessors.py:37>) (through line 75). On this pinned Windows platform these native F32 words are little-endian. The GLB consumer should still require explicit FLOAT/VEC3, valid count/range/alignment and a non-normalized, nonsparse accessor.

The buffer writer creates 4-byte-aligned buffer views without a byte stride at [io/exp/buffer.py:20](<C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2/io/exp/buffer.py:20>). Exporter traversal moves BinaryData into such a view at [blender/exp/exporter.py:517](<C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2/blender/exp/exporter.py:517>). A correction tool must nevertheless validate actual accessor/view byte ranges and aliasing; do not assume that an input GLB is tightly packed or has independent storage merely from this source path.

## Important exact-word exception: negative zero

`fast_structured_np_unique()` rewrites **every floating dtype field's -0.0 to +0.0 before deduplication**, including generic carriers: [blender/com/gltf2_blender_utils.py:8](<C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2/blender/com/gltf2_blender_utils.py:8>) (documentation at lines 19–23; actual write at lines 33–36). It then passes a byte-oriented view to `np.unique()` at line 62 and restores the structured dtype.

Thus a raw FLOAT_VECTOR carrier avoids normal quantization and preserves ordinary finite nonzero F32 values through this path, but it **cannot promise bit identity for signed zero**. This distinction matters if the intended proof is original-word equality rather than numerical normal error. Do not state that all 32-bit words pass through untouched.

Also, Blender INT custom attributes map to FLOAT accessors and `np.float32`, not a 32-bit integer accessor ([blender/com/conversion.py:98](<C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2/blender/com/conversion.py:98>), [blender/com/conversion.py:155](<C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2/blender/com/conversion.py:155>)). Reinterpreting arbitrary normal bit patterns as an INT numeric value would therefore lose precision above binary32's exact integer range.

Two source-compatible alternatives, still unrun:

- A one-based FLOAT/POINT source-vertex ID, bounded to the independent parser's 200,000-vertex profile. Every value up to 200,000 is exactly representable in F32 and is positive, so it survives zero canonicalization. Use the pinned native VVD normal map in RAM after export to recover the source values for each exported split vertex. This is an identity carrier, not a self-contained normal payload.
- For a self-contained bit carrier, split each F32 word into two unsigned 16-bit integer halves and store the three low halves and three high halves in two FLOAT_VECTOR/POINT attributes. Values 0–65535 are exactly representable finite F32; mint positive zero for zero halves. Require finite integer-valued bounded halves before reconstructing words. This preserves signed-zero bits without encoding arbitrary uint32 integers as floats. Reject nonfinite reconstructed normals before assigning glTF NORMAL.

## Coordinate convention differs from NORMAL

The generic custom reader/setter contains no normal normalization, decimal rounding, skinning normal matrix or Y-up swizzle. A custom vector has no normal semantics merely because its name mentions normals.

The standard NORMAL path instead reads mesh corner normals, rounds with `ROUNDING_DIGIT=4`, normalizes, applies the armature/object normal transform when present, normalizes again, replaces zero normals and finally converts Z-up to Y-up: [blender/exp/primitive_extract.py:1435](<C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2/blender/exp/primitive_extract.py:1435>) (through line 1483); rounding constant at [io/com/constants.py:159](<C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2/io/com/constants.py:159>). The exact matrix is `armature.matrix_world.to_3x3() @ inverse_transpose((armature.matrix_world.inverted_safe() @ object.matrix_world).to_3x3())` at lines 1459–1465. The Y-up helper is x,y,z → x,z,-y at [blender/exp/primitive_extract.py:84](<C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2/blender/exp/primitive_extract.py:84>).

A carrier correction must explicitly identify its coordinate convention. Either carry already computed desired final glTF-space normal words, or carry mesh-local source values/IDs plus a separately validated transform and apply the transport once in the correction. Assigning mesh-local custom values directly to NORMAL would skip transformations; repeating an already applied Y-up swizzle would also be wrong. Never substitute Blender's lossy NORMAL readback as the source of the correction.

The evaluated mesh path requests `preserve_all_data_layers=True` when modifiers are applied ([blender/exp/nodes.py:296](<C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2/blender/exp/nodes.py:296>), especially line 314). That is source intent, not proof arbitrary modifiers preserve source identity or carrier values. The initial experiment should remain on the exact validated two-mesh profile and verify custom attribute readback before export and every exported carrier afterwards.

## Minimum qualification gates for a later experiment

Keep the original failed raw result and report unchanged. Produce a separately named carrier export and correction; no installed exporter patch is needed. Require exact input/runtime/source pins, no underscore-name collision, expected mesh/primitive/count coverage, finite values and a declared coordinate transform. Explicitly disable Draco compression (its default is false at [__init__.py:432](<C:/Program Files/Blender Foundation/Blender 5.1/5.1/scripts/addons_core/io_scene_gltf2/__init__.py:432>)) and reject unsupported compression/sparse/quantization or modifier profiles rather than silently decoding an unreviewed path.

Before promotion, verify a bijective source identity or independently checked carrier-to-native relation for every exported vertex, and verify all non-NORMAL geometry/indices, UVs, weights/joints, morphs, materials, images, nodes/skins and unrelated metadata against the preserved export. Treat signed-zero handling explicitly if word identity is claimed. Then rerun the original independent native-normal threshold on the corrected GLB. Source inspection alone does not qualify this repair or change the historical FAILED_UNQUALIFIED result.

## Exact source SHA256 values

| Exporter file | SHA256 |
|---|---|
| `__init__.py` | `dddd7d2362b937f34a5d4a1978259317720a9bc647bb3b4dc113f9d5c38cbf56` |
| `blender/exp/primitive_extract.py` | `455a3566d833481b230141b457452b5bf4ff4a1661d4dd6765a568488e0a2769` |
| `blender/exp/primitive_attributes.py` | `df0de732f5ff39311c41e259c71b6b76bc731021701df1eaa619819300f3559e` |
| `blender/com/conversion.py` | `a9007860d8763746d30c358e5181a4fb6f36f83c13c2f3ed5a21143a3c322e71` |
| `blender/com/gltf2_blender_utils.py` | `7ce3f41dd813e231e810659ed2ce701524b795e8768f16b9e3a2d1601d219eff` |
| `blender/exp/accessors.py` | `6468fea56eb319a45b07da1dc0073f13ba5739cfe521c7e807834b206a0204b5` |
| `io/com/constants.py` | `be59f961a8f6d08068a7aaae4b91a72c5fadd832ca9b228276732b40f0f68a38` |
| `io/exp/binary_data.py` | `ed6e29b6557522b6a056a9bb1e3a0b6a8fffe250e9d0afdf47f7f2eef2447dcf` |
| `io/exp/buffer.py` | `7e4f666312b273a01fee63590e8676f1baa39635fe60f6befb797ef52eb47aca` |
| `blender/exp/exporter.py` | `49c1e0174a65efd6d411b906cd154b6b04502c4840c9b31a7bfac87e0888f242` |
| `blender/exp/nodes.py` | `6c77f1ec3f13bd4636ca72f766429abc9cd4353ff218fdb088db1e41f184b7c3` |
