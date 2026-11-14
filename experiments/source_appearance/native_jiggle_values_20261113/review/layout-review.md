# Independent JunkoHair MDL49 JIGGLE layout review

Read-only inspection of the locally pinned SourceIO text and exact owned MDL bytes. Only this review directory was written. SourceIO was not imported; converters, native viewers, runtimes, GPU tools, network and Git were not used.

## Verified input and layout

- MDL: `output/sfm-broader-native-cases-20261113/stage/junko_v25/models/touhou/tamo/junko hair.mdl`
- SHA256: `8da09c905227ddc8eef73a3f83594a4eb1c3a6d5304ee41ba5471bef834bc716`
- Magic `IDST`; signed version 49 at +4; file size at +76 is 37,644, equal to actual bytes.
- Header bone count/index at +156/+160 are 69 and 664. Version-49 bone stride is 216 bytes, so the table is [664, 15568).
- Bone-relative fields: name offset signed i32 at +0, parent signed i32 at +4, flags u32 at +160, procedure type u32 at +164, procedure offset u32 at +168, physics index u32 at +172, surface-property signed relative offset at +176, contents u32 at +180, eight u32 reserved values at +184.
- Procedure type 5 means JIGGLE in pinned `bone.py`. Procedure payload begins at bone-record start + procedure offset; the offset is not file-relative or relative to the offset field.
- Exactly 49 bones have nonzero procedure type, all 5; 20 type-zero bones have zero procedure offsets. All 69 names are nonempty, unique, terminated within the file, and valid UTF-8 in this input. Parent indices are in [-1,68], root is bone 0, and every nonroot parent is earlier than its child.
- At each of the 49 JIGGLE pointers, pinned SourceIO decodes a 120-byte prefix: signed i32 flags followed by 29 IEEE754 little-endian float32 values. This does not prove the complete native rule size or any extension layout. All 1,421 float values are finite. Raw flags are 49 / 0x00000031 in every payload.
- Payload addresses are unique and collectively fill [15568,21448), but are not monotonic in bone order. Gathering bones 60..68 occupy the beginning of this span. Bone 47 points at 20728, whereas bone 51 points at 20368. A reader must follow each stored pointer.

## Flag and semantic limits

Pinned `jiggle_bone.py` names only 0x01 IS_FLEXIBLE, 0x02 IS_RIGID, 0x04 HAS_YAW_CONSTRAINT, 0x08 HAS_PITCH_CONSTRAINT, 0x10 HAS_ANGLE_CONSTRAINT, 0x20 HAS_LENGTH_CONSTRAINT and 0x40 HAS_BASE_SPRING. Known mask is 0x7f. Preserve the flags' complete 32-bit pattern and report unknown bits as raw_u32 & 0xffffff80; do not let signed/IntFlag behavior hide them. Observed 0x31 consists of the pinned names IS_FLEXIBLE, HAS_ANGLE_CONSTRAINT and HAS_LENGTH_CONSTRAINT; unknown bits are zero.

SourceIO provides field names and wire reads, with no allowable numeric ranges, unit declarations, integration algorithm, timestep, constraints implementation or fidelity guarantees in these structs. Numeric minima/maxima in the adjacent JSON are observations of this exact input, not valid general ranges. Retain all values even when corresponding flag names are absent. No angular unit conversion, spring simulation, clamping or material interpretation is justified by this inspection.

## Two traps in pinned code

1. `JiggleRule` dataclass declaration lists pitch_bounce before pitch_friction, but `from_buffer` reads pitch_friction first and explicitly swaps constructor arguments. Wire order is **pitch_friction at payload +64**, **pitch_bounce at +68** (float indices 15 and 16). Deriving order from dataclass annotations would silently swap them; this MDL's both-zero values would conceal the defect.
2. `Bone.from_buffer` final positional constructor call passes `procedural_rule` into the `procedural_rule_type` field and again into the final rule field. Do not rely on that returned attribute for raw procedure type. Read the integer at bone +164, leaving pinned code unchanged.

## Recommended strict reader assertions

- Pin SHA256 and require IDST/version49; require declared size == actual size, sufficient header bytes, and safe bounded [bone_index, bone_index+bone_count*216) before iterating.
- Bound every bone-relative name and procedure pointer against actual bytes, require a terminated nonempty name for this input, and preserve names exactly. Validate parent range, self-parent/cycles, and resolve parent name using the full bone table.
- Reject type5 with zero procedure pointer or any truncated 120-byte payload. Report unsupported nonzero types separately rather than treating their payload as JIGGLE.
- Check unique/nonoverlapping procedure payload spans and no overlap with the bone table for this exact fixture. Do not require payload offsets to increase with bone index. General claims about other MDLs are outside this review.
- Decode `<i29f`; also retain flags as `<I` and raw payload bytes/hash for lossless provenance. Require all 29 floats finite; use JSON `allow_nan=False`.
- Match exactly49 JIGGLE declarations and69 bones for this exact fixture; retain bone index, name, parent index/name, bone record offset, stored relative offset and resolved absolute payload offset per row.
- Add an unequal pitch-friction/pitch-bounce sentinel in a synthetic in-memory fixture to catch the order trap; original all-zero values cannot test it.

## Numeric cross-check

Values form exactly two complete tuples:17 payloads use yaw_stiffness=pitch_stiffness=100;32 use both50. Other27 fields match across all49 payloads. Length and tip_mass are20, yaw/pitch damping5, along_stiffness100, along_damping0, angle_limit0.7853981852531433. Remaining values and their exact observed bounds are recorded in `independent-byte-audit.json`, together with all49 per-bone values, offset provenance, payload hashes and hashes of the four pinned source files inspected.

No blocker to metadata-only numeric extraction was found. Physics execution or a claim of native simulation fidelity remains unsupported by these layout facts.
