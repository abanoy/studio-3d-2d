"""Draft inline-or-omitted inert jiggle metadata, no runtime imports/solver."""
from __future__ import annotations
import copy
import hashlib
import json
import math
import re
import struct
import source_jiggle_values as Raw

FORMAT = "studio_source_jiggle_metadata_1"
LAYOUT = "sourceio_flags_plus_29_float_prefix_120"
READER_SHA256 = "3a6f690ad94498ae88803a6665c686cceb6d8f97c5f50b4d22a3ade65c69983e"
SOURCEIO_REVISION = "fe24260b97ac03b899d9b5d4f0fd7b34772f3647"
METADATA_LIMIT = 128 * 1024
REPORT_LIMIT = 256 * 1024
STATUS_LIMIT = 4096
KEY = "source_jiggle"
REASONS = {"layout_unsupported": "Optional native jiggle layout could not be retained.",
    "native_inventory_mismatch": "Native bone identities differ from the imported native inventory.",
    "metadata_value_budget": "Native jiggle values exceed the optional metadata admission bound.",
    "metadata_budget": "Complete jiggle metadata exceeds128KiB; no partial rules are retained.",
    "report_budget": "Complete jiggle metadata does not fit the256KiB parameter report.",
    "baseline_report_over_budget": "The original parameter report already exceeds256KiB.",
    "baseline_unserializable": "The original report cannot be encoded as finite JSON."}


class SourceIdentityError(ValueError): pass

def _sha(value): return isinstance(value, str) and re.fullmatch("[0-9a-f]{64}", value) is not None

def _name_in_budget(value):
    if type(value) is not str: return False
    try: return len(value.encode("utf-8")) <= 256
    except UnicodeError: return False

def _compact(value): return json.dumps(value, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode("utf-8") + b"\n"

def report_bytes(report, newline="\n"):
    if newline not in ("\n", "\r\n"): raise ValueError("Use explicit LF or Windows CRLF")
    text = json.dumps(report, ensure_ascii=True, indent=2, allow_nan=False)
    return text.replace("\n", newline).encode("utf-8")

def _status(reason, context=None):
    result = {"format": FORMAT, "status": "unavailable", "reason": reason, "detail": REASONS[reason],
        "applied": False, "runtime_support": "not_implemented", "binding_status": "unattempted"}
    result.update(context or {})
    return result

def inspect(raw, original_source_sha256, native_mdl_sha256, native_bones, source_scale):
    """Inspect one selected MDL; mismatch is integrity failure, not a fallback.

    Caller must supply an independently frozen selected-MDL SHA and keep its
    existing original-container/native-byte guards. Those guards are mandatory.
    """
    if not _sha(original_source_sha256) or not _sha(native_mdl_sha256) or type(raw) is not bytes or hashlib.sha256(raw).hexdigest() != native_mdl_sha256:
        raise SourceIdentityError("Original/native jiggle source identity is invalid or changed")
    context = {"original_source_sha256": original_source_sha256, "native_mdl_sha256": native_mdl_sha256}
    try:
        if not Raw.HEADER_PREFIX <= len(raw) <= Raw.MAX_BYTES or raw[:4] != b"IDST" or struct.unpack_from("<i", raw, 4)[0] != 49 or struct.unpack_from("<I", raw, 76)[0] != len(raw):
            return {"state": "unavailable", "status": _status("layout_unsupported", context)}
        count, start = struct.unpack_from("<2I", raw, 156)
        if not (1 <= count <= Raw.MAX_BONES and Raw.HEADER_PREFIX <= start <= len(raw) - count * Raw.BONE_BYTES and start % 4 == 0):
            return {"state": "unavailable", "status": _status("layout_unsupported", context)}
        declared = sum(struct.unpack_from("<I", raw, start + i * Raw.BONE_BYTES + 164)[0] == 5 for i in range(count))
        context.update(native_bone_count=count, declared_jiggle_rule_count=declared)
        if not declared:
            return {"state": "none"}  # No new report key, artifact or writer path.
        parsed = Raw.parse(raw)
    except (Raw.DecodeError, struct.error, OverflowError):
        return {"state": "unavailable", "status": _status("layout_unsupported", context)}
    expected = [{"name": row["name"], "parent": row["parent"]} for row in parsed["bones"]]
    valid_bones = type(native_bones) is list and len(native_bones) == count and all(type(row) is dict and set(row) == {"name", "parent"}
        and _name_in_budget(row["name"]) and type(row["parent"]) is int for row in native_bones)
    if not valid_bones or native_bones != expected:
        return {"state": "unavailable", "status": _status("native_inventory_mismatch", context)}
    if type(source_scale) not in (int, float) or not math.isfinite(source_scale) or not 0 < source_scale <= 1e6 or any(row["fields_above_proposed_abs1e6_budget"] for row in parsed["rules"]):
        return {"state": "unavailable", "status": _status("metadata_value_budget", context)}
    rules = []
    for row in parsed["rules"]:
        rules.append({"native_bone_index": row["index"], "native_bone_name": row["name"], "native_parent_index": row["parent"],
            "native_bone_flags": row["bone_flags_uint32"], "native_procedure_type": row["procedural_type_uint32"],
            "raw_rule_flags": row["flags_uint32"], "known_rule_flags": row["known_flags"], "unknown_rule_flag_bits": row["unknown_flags_mask"],
            "parameters": row["parameters"], "binary_provenance": {"bone_record_offset": row["record_offset"], "bone_relative_rule_offset": row["procedure_relative_offset_uint32"],
                "rule_absolute_offset": row["payload_offset"], "prefix_bytes": 120, "prefix_sha256": row["prefix_sha256"], "float32_words_uint32": row["float32_words_uint32"]},
            "binding_status": "unattempted", "applied": False})
    metadata = {"format": FORMAT, "status": "retained_inert", "applied": False, "runtime_support": "not_implemented", "binding_status": "unattempted",
        **context, "native_version": 49, "native_bone_count": count, "native_bone_catalogue_sha256": hashlib.sha256(_compact(expected)).hexdigest(),
        "parser_revision": "source_jiggle_prefix_1", "layout_reader_sha256": READER_SHA256, "sourceio_revision": SOURCEIO_REVISION,
        "parsed_layout": LAYOUT, "full_native_rule_layout_verified": False, "source_scale": float(source_scale),
        "value_units": "Raw native values; scale recorded as context, not applied", "rules": rules, "unsupported": parsed["unsupported"]}
    candidate = candidate_fingerprint(metadata)
    if candidate["metadata_candidate_bytes"] > METADATA_LIMIT:
        return {"state": "unavailable", "status": _status("metadata_budget", {**context, **candidate})}
    return {"state": "retained", "metadata": metadata}

def _inert(metadata, native_bones):
    if type(metadata) is not dict or metadata.get("format") != FORMAT or metadata.get("status") != "retained_inert" or metadata.get("applied") is not False or metadata.get("runtime_support") != "not_implemented" or metadata.get("binding_status") != "unattempted" or metadata.get("full_native_rule_layout_verified") is not False:
        raise ValueError("Only the exact inert/unbound metadata state is admitted")
    if not _sha(metadata.get("original_source_sha256")) or not _sha(metadata.get("native_mdl_sha256")) or type(metadata.get("native_bone_count")) is not int or not 1 <= metadata["native_bone_count"] <= Raw.MAX_BONES or metadata.get("native_version") != 49 or type(metadata.get("native_version")) is not int or metadata.get("parsed_layout") != LAYOUT or metadata.get("layout_reader_sha256") != READER_SHA256 or metadata.get("sourceio_revision") != SOURCEIO_REVISION:
        raise ValueError("Invalid native metadata identity domain")
    if type(metadata.get("source_scale")) not in (int, float) or not math.isfinite(metadata["source_scale"]) or not 0 < metadata["source_scale"] <= 1e6:
        raise ValueError("Invalid finite numeric native metadata scale")
    if type(native_bones) is not list or len(native_bones) != metadata["native_bone_count"]: raise ValueError("Native bone catalogue domain differs")
    rules = metadata.get("rules")
    if type(rules) is not list or not 1 <= len(rules) <= Raw.MAX_RULES: raise ValueError("Invalid rule count")
    seen = set()
    for row in rules:
        index = row.get("native_bone_index"); parent = row.get("native_parent_index")
        if type(index) is not int or index in seen or not 0 <= index < metadata["native_bone_count"] or type(parent) is not int or not -1 <= parent < metadata["native_bone_count"] or parent == index or row.get("native_procedure_type") != 5 or type(row.get("native_procedure_type")) is not int or row.get("applied") is not False or row.get("binding_status") != "unattempted":
            raise ValueError("Invalid rule identity/inert binding")
        seen.add(index)
        if native_bones[index] != {"name": row.get("native_bone_name"), "parent": parent} or not _name_in_budget(row.get("native_bone_name")):
            raise ValueError("Native rule index/name/parent differs")
        for field in ("native_bone_flags", "raw_rule_flags", "unknown_rule_flag_bits"):
            if type(row.get(field)) is not int or not 0 <= row[field] <= 0xFFFFFFFF: raise ValueError("Invalid uint32 flags")
        flags = row["raw_rule_flags"]
        if row["known_rule_flags"] != [name for bit, name in Raw.FLAGS.items() if flags & bit] or row["unknown_rule_flag_bits"] != flags & (~Raw.KNOWN_MASK & 0xFFFFFFFF):
            raise ValueError("Rule flag interpretation differs")
        params = row.get("parameters")
        if type(params) is not dict or set(params) != set(Raw.FIELDS) or any(type(value) not in (int, float) or not math.isfinite(value) or abs(value) > 1e6 for value in params.values()):
            raise ValueError("Invalid finite bounded jiggle fields")
        provenance = row.get("binary_provenance", {})
        words = provenance.get("float32_words_uint32")
        if type(words) is not list or len(words) != 29 or any(type(word) is not int or not 0 <= word <= 0xFFFFFFFF for word in words) or provenance.get("prefix_bytes") != 120 or not _sha(provenance.get("prefix_sha256")):
            raise ValueError("Invalid prefix provenance")
        encoded = struct.pack("<I29I", flags, *words)
        if hashlib.sha256(encoded).hexdigest() != provenance["prefix_sha256"] or list(struct.unpack("<29I", struct.pack("<29f", *[params[name] for name in Raw.FIELDS]))) != words:
            raise ValueError("Named values differ from exact prefix words/hash")
        for name in ("bone_record_offset", "bone_relative_rule_offset", "rule_absolute_offset"):
            if type(provenance.get(name)) is not int or provenance[name] < 0: raise ValueError("Invalid native prefix offsets")
        if provenance["bone_record_offset"] + provenance["bone_relative_rule_offset"] != provenance["rule_absolute_offset"]: raise ValueError("Bone-relative prefix target differs")

def candidate_fingerprint(metadata):
    raw = _compact(metadata)
    return {"metadata_candidate_sha256": hashlib.sha256(raw).hexdigest(), "metadata_candidate_bytes": len(raw),
        "rule_count": len(metadata["rules"]), "native_bone_count": metadata["native_bone_count"]}

def _context(metadata):
    return {"original_source_sha256": metadata["original_source_sha256"], "native_mdl_sha256": metadata["native_mdl_sha256"],
        **candidate_fingerprint(metadata)}

def _validated_identity(base, metadata):
    if type(base) is not dict or type(base.get("native_parameters")) is not dict or KEY in base["native_parameters"]:
        raise ValueError("Expected the original unaugmented native report")
    _inert(metadata, base["native_parameters"].get("bones"))
    if base.get("source_sha256") != metadata["original_source_sha256"] or hashlib.sha256(_compact(base["native_parameters"].get("bones"))).hexdigest() != metadata["native_bone_catalogue_sha256"] or type(base.get("scale")) not in (int, float) or base["scale"] != metadata["source_scale"]:
        raise SourceIdentityError("Metadata belongs to a different original/native catalogue or conversion scale")

def plan_report(base_report, inspection, newline="\n", *, expected_native_mdl_sha256=None):
    """Inline exact values or explicitly omit whole optional branch, never clamp.

    report_bytes=None means use the exact original writer/report. Omission notes
    are bounded JSON for the existing conversion log, not a sidecar/portable asset.
    Original/native source checks precede every optional serialization/budget gate.
    Nonempty inspections require expected_native_mdl_sha256 from the caller's
    independently frozen selected-MDL context, never from inspection metadata.
    No-rule/BSP no-op state publishes no new data and keeps its original writer.
    """
    base = copy.deepcopy(base_report)
    state = inspection.get("state")
    if state == "none":
        return {"state": "unchanged", "report": base, "report_bytes": None, "note_bytes": None, "omission": None}
    if state == "retained":
        metadata = copy.deepcopy(inspection["metadata"])
        _validated_identity(base, metadata)
        context = _context(metadata)
    elif state == "unavailable":
        status = copy.deepcopy(inspection["status"])
        if type(status) is not dict or status.get("reason") not in {"layout_unsupported", "native_inventory_mismatch", "metadata_value_budget", "metadata_budget"} or status.get("format") != FORMAT or status.get("applied") is not False or status.get("runtime_support") != "not_implemented" or status.get("binding_status") != "unattempted" or not _sha(status.get("original_source_sha256")) or not _sha(status.get("native_mdl_sha256")):
            raise ValueError("Invalid optional metadata inspection status")
        if type(base) is not dict or base.get("source_sha256") != status["original_source_sha256"]:
            raise SourceIdentityError("Unavailable jiggle status belongs to a different original source")
        context = {key: status[key] for key in ("original_source_sha256", "native_mdl_sha256", "metadata_candidate_sha256", "metadata_candidate_bytes", "rule_count", "native_bone_count", "declared_jiggle_rule_count") if key in status}
    else:
        raise ValueError("Unexpected optional metadata inspection state")
    if not _sha(expected_native_mdl_sha256) or context["native_mdl_sha256"] != expected_native_mdl_sha256:
        raise SourceIdentityError("Jiggle inspection differs from independently frozen selected-MDL identity")
    try:
        base_bytes = report_bytes(base, newline)
    except (ValueError, TypeError, OverflowError):
        return _omit(base, _status("baseline_unserializable", context), newline, baseline_unusable=True)
    if len(base_bytes) > REPORT_LIMIT:
        return _omit(base, _status("baseline_report_over_budget", context), newline, baseline_unusable=True)
    if type(base.get("native_parameters")) is not dict or KEY in base["native_parameters"]:
        raise ValueError("Expected original unaugmented native report")
    if state == "unavailable": return _omit(base, status, newline)
    if context["metadata_candidate_bytes"] > METADATA_LIMIT:
        return _omit(base, _status("metadata_budget", context), newline)
    candidate = copy.deepcopy(base); candidate["native_parameters"][KEY] = metadata
    encoded = report_bytes(candidate, newline)
    if len(encoded) <= REPORT_LIMIT:
        return {"state": "embedded", "report": candidate, "report_bytes": encoded, "note_bytes": None, "omission": None}
    context["full_report_candidate_bytes"] = len(encoded)
    context["full_report_line_ending"] = "CRLF" if newline == "\r\n" else "LF"
    return _omit(base, _status("report_budget", context), newline)

def _omit(base, status, newline, baseline_unusable=False):
    status = copy.deepcopy(status)
    status["status"] = "omitted"
    status["retained_rule_count"] = 0
    status["source_of_truth"] = "retained_native_mdl_and_preparation_bundle"
    status["metadata_candidate_sha256"] = status.get("metadata_candidate_sha256")
    status["metadata_candidate_bytes"] = status.get("metadata_candidate_bytes")
    status["candidate_state"] = "formed_not_retained" if status["metadata_candidate_sha256"] else "not_formed"
    note = _compact(status)
    if len(note) > STATUS_LIMIT: raise ValueError("Omission status exceeds4KiB")
    candidate = copy.deepcopy(base); encoded = None
    if not baseline_unusable:
        candidate["native_parameters"][KEY] = copy.deepcopy(status)
        attempt = report_bytes(candidate, newline)
        if len(attempt) <= REPORT_LIMIT: encoded = attempt
    return {"state": "omitted_status_inline" if encoded is not None else "omitted_log_only", "report": candidate if encoded is not None else copy.deepcopy(base),
        "report_bytes": encoded, "note_bytes": note, "omission": status}
