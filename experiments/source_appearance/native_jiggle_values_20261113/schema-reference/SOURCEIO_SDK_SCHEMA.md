# Source jiggle metadata preparation

This is read-only design research for a later feature. It changes no importer, solver, tests or native asset. Current static-appearance conversion/adoption acceptance remains separate. No SourceIO imports, native parsing, extraction, converters, Godot or graphical process ran for this research. The proposal below is not an implemented contract or native motion-fidelity result.

## Pinned SourceIO evidence

Local source root: `output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647`. Exact file identities are in `SOURCEIO_INPUT_HASHES.json`.

`library/models/mdl/structs/bone.py:125–130` defines procedural kinds AXISINTERP=1, QUATINTERP=2, AIMATBONE=3, AIMATATTACH=4, JIGGLE=5. Its `Bone` fields include native name/parent, bone flags, procedural type, and rule. The reader follows a bone-relative procedure offset when the native type and offset are nonzero (`:213–220`).

Important positional-constructor mismatch: the dataclass declares `procedural_rule_type` at `bone.py:149`, but `from_buffer` passes the parsed rule object into that position (`:221–223`), as well as into the final `procedural_rule` position. A later adapter must not assume `int(bone.procedural_rule_type)` works. Use an explicit, bounded rule-class mapping and retain the independently admitted numeric native type when available. Do not modify the approved runtime to hide this discrepancy.

`jiggle_bone.py:7–14` defines these rule bits:

| Bit | SourceIO name |
| --- | --- |
| 0x01 | IS_FLEXIBLE |
| 0x02 | IS_RIGID |
| 0x04 | HAS_YAW_CONSTRAINT |
| 0x08 | HAS_PITCH_CONSTRAINT |
| 0x10 | HAS_ANGLE_CONSTRAINT |
| 0x20 | HAS_LENGTH_CONSTRAINT |
| 0x40 | HAS_BASE_SPRING |

The explicit dataclass field inventory (`jiggle_bone.py:18–48`) is flags plus 29 floats:

- General: `length`, `tip_mass`.
- Tip springs: `yaw_stiffness`, `yaw_damping`, `pitch_stiffness`, `pitch_damping`, `along_stiffness`, `along_damping`.
- Angular constraints: `angle_limit`, `min_yaw`, `max_yaw`, `yaw_friction`, `yaw_bounce`, `min_pitch`, `max_pitch`, `pitch_bounce`, `pitch_friction`.
- Base spring: `base_mass`, `base_stiffness`, `base_damping`, `base_min_left`, `base_max_left`, `base_left_friction`, `base_min_up`, `base_max_up`, `base_up_friction`, `base_min_forward`, `base_max_forward`, `base_forward_friction`.

The reader consumes one signed32-bit flags value and 29 float32 values, a 120-byte prefix. The pitch dataclass declaration lists bounce before friction; its reader deliberately reorders the two variables at construction. Serialize named fields explicitly rather than relying on positional field order.

Bone flags are a separate namespace: ALWAYS_PROCEDURAL=0x04, USED_BY_HITBOX=0x100, USED_BY_VERTEX_LOD0=0x400. A jiggle-rule flags value must never be confused with those bone flags. Bone usage bits alone do not establish a specific runtime deform-bone binding.

## Official SDK cross-check

The official [studio header](https://github.com/ValveSoftware/source-sdk-2013/blob/master/src/public/studio.h) adds BOING=0x80 and five boing floats. Its full struct is therefore 140 bytes, while the pinned reader exposes 120. The header declares version48; this comparison alone does not establish every SFM MDL49 rule layout. Its angular limits are radians. Preserve unsupported bits and label missing fields; never fill them with guessed zeros.

The official [solver implementation](https://github.com/ValveSoftware/source-sdk-2013/blob/master/src/public/jigglebones.cpp) uses goal-matrix column2 for the native tip direction. Tip/base “mass” values directly contribute downward acceleration; they are not kilogram inputs. Dimensional inference: lengths/base offsets use Source coordinates, stiffness acts as inverse-seconds-squared, damping as inverse-seconds. The integration clock is seconds. Yaw/pitch limits clip direction and clear tip velocity; their recorded friction/bounce fields are not used in this implementation. Base friction is used. The code includes frame-rate fallback and reinitialization, so a generic spring solver is not equivalent.

These are browsed `master` sources on 2026-11-13, not an immutable SDK commit pin. A later implementation should pin the chosen official reference revision. The separate [instance-state header](https://github.com/ValveSoftware/source-sdk-2013/blob/master/src/public/jigglebones.h) confirms that dynamic simulation state belongs to an instance. Compiler-side authoring defaults/clamps were not established by this research.

## Proposed inert metadata boundary

Proposed format name: `studio_source_jiggle_metadata_1`. Keep this under the retained native report, separate from HAS secondary-rig configuration. Initially `applied` must be false and runtime support must state `not_implemented`; successful metadata retention must not turn Hair & clothes on or replace authored pose data.

Proposed envelope fields:

| Field | Meaning |
| --- | --- |
| `format`, `applied`, `runtime_support` | Exact schema discriminator and explicit inert status. |
| `original_source_sha256`, `native_mdl_sha256` | Bind original container/input and selected MDL independently. |
| `native_version`, `native_bone_count` | Admitted native identity and bounded index domain. |
| `parser_revision`, `parser_file_sha256` | Approved SourceIO pin plus exact reader identities. |
| `parsed_layout` | Explicitly `sourceio_flags_plus_29_float_prefix_120`; no full-rule-size claim. |
| `source_scale` | Record the actual conversion scale without rewriting the raw values. |
| `rules` | Explicit bounded array, native-index ordered, containing the fields below. |
| `unsupported` | Bounded reason records for unsupported kind, flags, layout, or binding. |

Each rule should carry native bone index/name/parent, numeric procedural type, separate bone flags and raw rule flags, decoded known flag names, unknown-bit mask, and exactly the 29 named numeric fields above. Retain the native index as identity; do not merge bones by display label. A future proven imported-binding correspondence belongs in a separate field and should identify the exact imported asset and binding. Do not imply that storing a name establishes correspondence.

Proposed admission limits (product budgets, not Source-format facts):

- At most4096 native bone identities, at most128 jiggle records, at most128 unsupported reason records, and at most256 UTF-8 bytes per name/reason. Refuse the new metadata branch on overflow; do not silently truncate it or reject an otherwise valid static import without a separate product decision.
- All 29 values are mandatory explicit finite numbers; reject booleans, NaN and infinities. Preserve signed values within an explicit absolute bound of1e6. That bound limits metadata, not runtime stability. A strict JSON encoder must also disallow NaN.
- Indices are unique integers inside the admitted bone domain; parent is -1 or a valid distinct native index. Validate the whole native parent graph independently. Preserve flags as exact uint32 bit patterns, with unsupported bits reported.
- Serialized jiggle metadata at most128KiB, and the full adjacent parameters report must remain within the existing256KiB adoption limit. Check encoded size before publication.
- Zero/negative tip length, reversed enabled limits, unknown flags, conflicting flexible/rigid modes, boing, unsupported procedural kinds and absent/ambiguous bindings remain inert and visibly unsupported. They are not candidates for silent clamping or approximate activation.

Metadata retention can cover all known finite fields even while motion remains unsupported. A later runtime candidate needs a separately reviewed subset and numerical/stability budgets. Preserve source values first; derive any HAS settings into a distinct report carrying conversion/basis assumptions and approximation reasons. A HAS fan is additional authored behavior, not evidence that native jiggle parameters were reproduced.

## Junko evidence boundary

The already parsed `WIDER_FAMILIES.json` Junko hair record binds MDL SHA256 `8da09c905227ddc8eef73a3f83594a4eb1c3a6d5304ee41ba5471bef834bc716`, version49, 69 bones and49 type5 declarations. It records names/indices and `rule_parsed`, but no JiggleRule numeric payloads. No flag/parameter distribution can be inferred from that record. Parent-owned `JUNKO_CASES.json` and `HAS_MAPPING.md` hold the separate case and solver-mapping research.

Future acceptance should first prove finite, source-bound metadata retention through packed/linked cold reopen. Native timed-motion comparison, basis/scale correspondence, toggle-off restoration, fan response, export determinism and owner review remain separate later gates. No native fidelity is accepted here.
