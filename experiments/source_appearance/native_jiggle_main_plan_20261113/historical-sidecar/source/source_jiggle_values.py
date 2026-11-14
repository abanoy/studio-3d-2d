"""Inert bounded MDL49 JIGGLE prefix decoder, stdlib only.

Layout documentation is the locally pinned SourceIO reader. This module never
imports it or evaluates native/model scripts and makes no simulation promise.
"""
from __future__ import annotations
import hashlib
import math
import struct

MAX_BYTES = 16 * 1024 * 1024
MAX_BONES = 4096
MAX_RULES = 128
HEADER_PREFIX = 408
BONE_BYTES = 216
PREFIX_BYTES = 120
KNOWN_MASK = 0x7F
FLAGS = {1: "IS_FLEXIBLE", 2: "IS_RIGID", 4: "HAS_YAW_CONSTRAINT", 8: "HAS_PITCH_CONSTRAINT",
         16: "HAS_ANGLE_CONSTRAINT", 32: "HAS_LENGTH_CONSTRAINT", 64: "HAS_BASE_SPRING"}
# Wire order, not JiggleRule dataclass declaration order: friction then bounce.
FIELDS = ("length", "tip_mass", "yaw_stiffness", "yaw_damping", "pitch_stiffness", "pitch_damping",
          "along_stiffness", "along_damping", "angle_limit", "min_yaw", "max_yaw", "yaw_friction", "yaw_bounce",
          "min_pitch", "max_pitch", "pitch_friction", "pitch_bounce", "base_mass", "base_stiffness", "base_damping",
          "base_min_left", "base_max_left", "base_left_friction", "base_min_up", "base_max_up", "base_up_friction",
          "base_min_forward", "base_max_forward", "base_forward_friction")

class DecodeError(ValueError): pass

def require(ok, message):
    if not ok: raise DecodeError(message)

def overlap(a, b): return max(a[0], b[0]) < min(a[1], b[1])

def parse(raw: bytes) -> dict:
    require(type(raw) is bytes and HEADER_PREFIX <= len(raw) <= MAX_BYTES, "MDL byte length outside supported budget")
    require(raw[:4] == b"IDST", "Only IDST MDL magic is supported")
    version, checksum = struct.unpack_from("<iI", raw, 4)
    require(version == 49, "Only the inspected MDL49 layout is supported")
    require(struct.unpack_from("<I", raw, 76)[0] == len(raw), "Declared MDL byte length differs")
    count, start = struct.unpack_from("<2I", raw, 156)
    require(1 <= count <= MAX_BONES, "Bone count outside reader budget")
    require(start >= HEADER_PREFIX and start % 4 == 0 and start <= len(raw) - count * BONE_BYTES, "Bone table offset/length invalid")
    end = start + count * BONE_BYTES
    bones = []; strings = []; payloads = []; unsupported = []
    for index in range(count):
        at = start + index * BONE_BYTES
        name_relative, parent = struct.unpack_from("<2i", raw, at)
        name_at = at + name_relative
        # This narrow supported subset keeps names beyond the admitted bone
        # table; it is a reader admission rule, not a universal MDL claim.
        require(end <= name_at < len(raw), "Bone name offset overlaps admitted structures or escapes file")
        nul = raw.find(b"\0", name_at, min(len(raw), name_at + 257))
        require(nul > name_at, "Bone name missing, unterminated or exceeds256bytes")
        name_bytes = raw[name_at:nul]
        name = name_bytes.decode("latin-1")
        require(-1 <= parent < count and parent != index, "Native parent index invalid")
        bone_flags, kind, relative = struct.unpack_from("<3I", raw, at + 160)
        offset_signed, = struct.unpack_from("<i", raw, at + 168)
        require(offset_signed >= 0, "Negative signed procedure offset unsupported by pinned unsigned reader")
        bone = {"index": index, "name": name, "parent": parent, "bone_flags_uint32": bone_flags,
            "procedural_type_uint32": kind, "record_offset": at, "record_sha256": hashlib.sha256(raw[at:at + BONE_BYTES]).hexdigest(),
            "name_offset": name_at, "name_bytes_sha256": hashlib.sha256(name_bytes).hexdigest(), "procedure_relative_offset_uint32": relative}
        bones.append(bone); strings.append((name_at, nul + 1))
        if kind == 0:
            require(relative == 0, "Zero procedure type has nonzero offset; ambiguous declaration")
            continue
        require(relative != 0, "Nonzero procedure type has zero offset")
        target = at + relative
        require(end <= target <= len(raw) - 4 and target % 4 == 0, "Procedure target outside supported bounds/alignment")
        if kind != 5:
            unsupported.append({"bone_index": index, "procedure_type": kind, "reason": "Only type5 prefix is decoded", "payload_offset": target})
            continue
        require(len(payloads) < MAX_RULES, "JIGGLE record count exceeds reader budget")
        require(target <= len(raw) - PREFIX_BYTES, "JIGGLE120byte prefix truncated")
        span = (target, target + PREFIX_BYTES)
        require(not any(overlap(span, previous) for previous in payloads), "JIGGLE payload prefixes overlap or alias")
        payloads.append(span)
        flags_signed, *values = struct.unpack_from("<i29f", raw, target)
        flags_u32, = struct.unpack_from("<I", raw, target)
        require(all(math.isfinite(value) for value in values), "Nonfinite JIGGLE parameter")
        words = struct.unpack_from("<29I", raw, target + 4)
        unknown = flags_u32 & (~KNOWN_MASK & 0xFFFFFFFF)
        params = dict(zip(FIELDS, values))
        bone["jiggle"] = {"payload_offset": target, "prefix_bytes": PREFIX_BYTES,
            "prefix_sha256": hashlib.sha256(raw[target:target + PREFIX_BYTES]).hexdigest(),
            "flags_signed_int32": flags_signed, "flags_uint32": flags_u32, "known_flags_mask": KNOWN_MASK,
            "known_flags": [name for bit, name in FLAGS.items() if flags_u32 & bit], "unknown_flags_mask": unknown,
            "layout": "sourceio_flags_plus_29_float_prefix_120", "full_native_rule_layout_verified": False,
            "parameters": params, "float32_words_uint32": list(words),
            "fields_above_proposed_abs1e6_budget": [name for name, value in params.items() if abs(value) > 1e6],
            "runtime_support": "not_implemented", "applied": False}
        if unknown:
            unsupported.append({"bone_index": index, "unknown_flags_mask": unknown,
                "reason": "Bits outside pinnedSourceIO0x7f retained; SDK48BOING0x80/full140byte layout not inferred"})
    require(len({bone["name"] for bone in bones}) == len(bones), "Duplicate native names outside this reader's admitted identity subset")
    # Follow native indices, never name joins or a presumed topological order.
    done = set()
    for index in range(count):
        visiting = set(); cursor = index
        while cursor >= 0 and cursor not in done:
            require(cursor not in visiting, "Native parent cycle")
            visiting.add(cursor); cursor = bones[cursor]["parent"]
        done.update(visiting)
    require(not any(overlap(payload, string) for payload in payloads for string in strings), "JIGGLE payload aliases a bone name string")
    rules = [{key: value for key, value in bone.items() if key != "jiggle"} | bone["jiggle"] for bone in bones if "jiggle" in bone]
    sorted_spans = sorted(payloads)
    return {"format": "has_raw_mdl49_jiggle_prefix_values_1", "native_mdl_sha256": hashlib.sha256(raw).hexdigest(),
        "native_mdl_bytes": len(raw), "native_version": version, "native_checksum_uint32": checksum,
        "bone_count": count, "bone_table_offset": start, "bone_record_bytes": BONE_BYTES, "bone_table_end": end,
        "bones": [{key: value for key, value in bone.items() if key != "jiggle"} for bone in bones], "rules": rules,
        "unsupported": unsupported, "wire_field_order": list(FIELDS), "known_jiggle_flags_mask": KNOWN_MASK,
        "observed_prefix_ranges": [list(span) for span in sorted_spans],
        "observed_prefix_ranges_contiguous": bool(sorted_spans) and all(a[1] == b[0] for a, b in zip(sorted_spans, sorted_spans[1:])),
        "runtime_support": "not_implemented", "applied": False,
        "scope": "Inert bounded numeric prefix extraction only; noSourceIOimport, geometry/runtimebinding or simulation"}
