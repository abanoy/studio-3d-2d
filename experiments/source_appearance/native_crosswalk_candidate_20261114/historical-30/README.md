# Restricted native → Blender → exported glTF crosswalk candidate

This is **output-only new binding code and authored CPU evidence**. It is outside
the current source/runtime lease and has not been ported into Studio. No model,
texture, GLB, HAS, image, audio, movie or runtime binary is included. No installed
Blender/SourceIO module was imported or executed by the CPU tests.

`source_jiggle_crosswalk.py` implements a restricted native/Blender identity,
parent and rest proof plus an identity-based export collector. Its normal profile
admits only JunkoHair native MDL SHA256
`8da09c905227ddc8eef73a3f83594a4eb1c3a6d5304ee41ba5471bef834bc716`
and all69native bones. Alternate profiles in the tests admit self-authored
three-bone bytes; they are not a general-model compatibility claim.

## Exact code and admission boundaries

The diagnostic rest oracle independently checks immutable MDL49 bytes, length,
bone-table/name/parent domains, unique short ASCII constructor keys and finite
position/quaternion values. The pinned SourceIO Bone reader consumes name at0,
parent at4, six controller floats at8–31, position at32–43 and XYZW quaternion
at44–59 inside each216byte record. The selected native SHA must first match the
caller's independently captured SHA. A different SHA profile remains unsupported.

The pinned MdlV49 reader assigns each `Bone.bone_id` its native index. The factory
creates a fresh armature and calls `edit_bones.new(bone.name[:63])`, then applies
native-index parents and parent-relative
`LocRotScale(position * scale, Quaternion((w,x,y,z)), unit_scale)`. Junko's69names
are unique ASCII and at most20characters. Inside that exact SHA/factory domain,
constructor keys are injective. The candidate requires the complete69-key
bijection; generated suffixes, truncation, duplicates, missing or extra bones
refuse the whole proof. It does not zip native, data-bone or pose-bone collections.

Each loaded SourceIO `bone_id`, name, parent and all seven rest float32 words must
match the raw record. Actual data-bone parent pointers and every `matrix_local`
must match the independent parent-composed rest reference. PoseBone owner,
data-bone pointer, parent pointer and current rest matrix must agree. The armature
must remain an identity-transformed object in Object mode. Matrix admission uses
relative tolerance2e-5; native quaternion norm must be within1e-4 of1. These are
strict proof gates, not value corrections or simulation parameter mappings.

The caller must attest that the observed source hashes identify the functions
actually used. The candidate compares supplied source-pin dictionaries, but does
not itself import SourceIO or inspect live function aliases. A real worker must
verify the actual loaded mdl49 factory alias is the pinned mdl44 factory, code
origins, whole-runtime source identities and the selected-MDL capture/recheck.

## Three installed-exporter APIs

Installed root inspected as text only:

`C:\Program Files\Blender Foundation\Blender 5.1\5.1\scripts\addons_core\io_scene_gltf2`

The exact hashes and absolute paths are in `SOURCE_AUDIT.json` and in the candidate
pin dictionaries. Relevant observed APIs are:

| Source | Seam |
| --- | --- |
| `blender/exp/joints.py:101` | `gather_joint_hook(node, blender_bone, export_settings)`, where `blender_bone` is the actual PoseBone. |
| `blender/exp/skins.py:48` | `gather_skin_hook(skin, blender_armature_object, export_settings)`. |
| `blender/exp/export.py:67` | `gather_gltf_extensions_hook(gltf, export_settings)` after scene traversal, node/skin references and GPU-instance management. |
| `blender/exp/tree.py:83`, `nodes.py:77` | Export tree retains the actual armature object and final node-object references. |
| `blender/exp/exporter.py:397` | Child-of-root properties become references into final root arrays; the collector enumerates those arrays by object identity. |
| `blender/exp/export.py:312` | JSON cleanup preserves list order. |
| `io/exp/user_extensions.py:5` | Dispatcher invokes `hook(*args, export_settings)` and catches/logs exceptions. |
| `__init__.py:1323` | Enabled addon modules supply `glTF2ExportUserExtension` constructors. |

The pinned `__init__.py` declares these operator keywords and settings mappings.
These are **source defaults**, not observed values from an actual candidate run.
The current bridge explicitly passes only the three rows marked Yes below; the
collector admits/refuses the actual `export_settings` values at the late hook.

| `bpy.ops.export_scene.gltf` keyword | Declared default / definition line | `export_settings` key / assignment line | Current bridge passes it | Candidate requires |
| --- | --- | --- | --- | --- |
| `export_extras` | false /637 | `gltf_extras` /1192 | Yes:false | false |
| `export_yup` | true /643 | `gltf_yup` /1193 | Yes:true | true |
| `export_animations` | true /662 | `gltf_animations` /1197 | Yes:false | false |
| `export_skins` | true /890 | `gltf_skins` /1262 | No | true |
| `export_armature_object_remove` | false /749 | `gltf_armature_object_remove` /1201 | No | false |
| `export_rest_position_armature` | true /872 | `gltf_rest_position_armature` /1269 | No | true |
| `export_hierarchy_flatten_bones` | false /737 | `gltf_flatten_bones_hierarchy` /1199 | No | false |
| `export_hierarchy_flatten_objs` | false /743 | `gltf_flatten_obj_hierarchy` /1200 | No | false |
| `export_leaf_bone` | false /758 | `gltf_leaf_bone` /1202 | No | false |
| `export_gpu_instances` | false /961 | `gltf_gpu_instances` /1285 | No | false |
| `export_use_gltfpack` | false /216 | `gltf_use_gltfpack` /1295 | No | false |
| `export_draco_mesh_compression_enable` | false /432 | `gltf_draco_mesh_compression` /1143, or forcedfalse /1151 when unavailable | No | false |

`export_def_bones` additionally defaultsfalse at731 and maps to `gltf_def_bones`
at1198. It is not a separate candidate settings gate; the complete native-node and
skin-joint bijection refuses dropped bones. Qualification must record this value.
The caller must not silently change existing export arguments to manufacture a
passing proof. Last-used/operator runtime values and constructor discovery remain
actual-runtime observations to make after the current lease.

`ExportCollector` observes actual data/PoseBone identities from the proven native
domain, retains joint-object and skin-object references, and resolves final node
indices and skin joint slots by `is` identity. Equal labels, reordered nodes and
reordered skin slots are not joins. It verifies actual exported parent edges,
target skin membership and an exported mesh using each target skin. It requires
one scene, one observable armature object and controlled export settings.

**Hook errors latch.** Throwing inside a Blender hook alone cannot refuse export,
because the installed dispatcher catches exceptions. `finish(final_glb_bytes)`
must run outside the export operator after it returns. It refuses any latched or
missing hook, rechecks native/Blender identity/rest, and reconciles its immutable
node/skin snapshot against the final emitted GLB bytes. It binds the result to
that complete GLB SHA. The caller must run this after owned GLB postprocessing.

Extras remainfalse. The collector changes no node, skin, bone, property, mesh,
material or native value. Scoped registration adds only the constructor attribute
to the already enabled, pinned exporter module in the private worker's memory;
it enables no addon, saves no preference, edits no installed file and replaces no
exporter function. An existing registration or changed registration owner refuses.
Actual discovery through this seam is stillUNRUN.

The resulting dictionary is an inactive **report-only** crosswalk. It retains
native indices, rest words, Blender observations, final glTF indices/skin slots,
source pins and GLB SHA. It reports `HAS_runtime_binding="unattempted"` and
`native_simulation=false`. Its complete compact128KiB proof cap is additional to
the existing whole parameters256KiB and project1MiB caps. No report writer,
publication API, partial-row fallback, sidecar promise or automatic activation is
provided. Real report admission must measure the complete final nested report.

`node_dict` and `skin_dict` implement the admitted top-level empty-field pruning
against authored objects. The installed JSON cleanup additionally handles nested
empty values and integral floats. A real diagnostic must observe the actual
`gltf2_io.Node`/`Skin` types, identity retention through flattening, numeric child
and skin references at the late hook, and exact final JSON normalization. Those
are qualification targets; mock types and source inspection do not establish
that the live exporter supplies them. A normalization mismatch currently refuses
reconciliation and must remain visible for review.

## Authored CPU result and retained failure

`cpu-attempt2.log`: **30tests,0failures,0errors**, approved Python3.13 with `-B`.
The tests use authored MDL bytes, fake RNA objects, hand-calculated90degree
rest transforms and fake exporter objects. They cover:

- Full native/factory bijection despite reordered SourceIO and Blender collections;
  raw rest-word/ID/parent/hash gates, two scales, wrong owner/pointer/matrix cases.
- Duplicate/long/non-ASCII keys, native cycles, invalid numeric values, changed
  factory/reader/exporter pins and unsupported SHA profiles.
- Reordered exported nodes and skin slots with deliberately equal labels;
  missing/duplicate objects, changed hierarchy, foreign/missing skins/mesh use.
- Wrong export settings/extras, swallowed-hook failure latching, missing final
  hooks, immutable snapshots, changed final GLB and post-hook pose mutation.
- Inclusive complete-proof byte budget and scoped constructor cleanup on success,
  exception, an existing constructor and an unobservable addon.
- Absence of Blender, mathutils, SourceIO and installed exporter imports.

`cpu-attempt1.log` remains a **failed candidate attempt**:30tests with14errors.
Every error came from the same evidence recheck: initial source-pin insertion
order differed from its reconstructed sorted dictionary. Canonical JSON
`sort_keys=True` fixes that representation instability. No production or runtime
failure is implied, and the failed log is not replaced by the later pass.

## Required qualification after the current lease ends

Actual Blender export, actual Junko/native rest proof, main-bridge integration,
Studio adoption, packed/linked/cold persistence, source-to-HAS runtime binding,
geometry/weight/inverse-bind behavior, fan response, solver semantics and rendered
fidelity are all **UNRUN**. The final-GLB check here observes node/skin structure;
it does not establish binary-accessor correctness or weighted deformation.

First run a separately owned private diagnostic using the exact current worker,
selected Junko capture and pinned installed exporter. Attest69complete native ↔
data/PoseBone ↔ glTF joint rows, actual rest transforms, constructor discovery,
final GLB SHA and unchanged geometry/material/weight fingerprints. Retain any
strict refusal rather than weaken a gate to obtain a pass. Then join the proven
glTF indices to `scene3d.gd`'s existing `has_source_bones` mapping in a fresh Godot
import and test neutral/posed weighted geometry, reports and cold persistence.
Native tip-axis, units, dynamics, lifecycle and fan tests remain the separately
saved runtime plan; no source-to-solver parameter conversion is implemented here.
