"""Draft inert Source jiggle metadata adapter. No Blender/SourceIO or file IO.

No-jiggle and BSP callers retain the existing writer path. All report-size
decisions use the exact nested JSON bytes, including caller-specified newlines.
"""
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
METADATA_FILE = "native-jiggle.json"
STATUS_FILE = "native-jiggle-status.json"
KEY = "source_jiggle"
REASONS = {"layout_unsupported": "Native jiggle layout could not be retained by this optional reader.",
    "native_inventory_mismatch": "Native bone identities differ from the imported native inventory.",
    "metadata_value_budget": "Native jiggle values exceed the optional metadata admission bound.",
    "metadata_budget": "Complete native jiggle metadata exceeds its128KiB budget; no rules were truncated.",
    "report_budget": "Complete native jiggle metadata does not fit the256KiB parameter report.",
    "baseline_report_over_budget": "The existing parameter report already exceeds256KiB.",
    "baseline_unserializable": "The existing report cannot be encoded as finite JSON.",
    "sidecar_not_published": "External native jiggle metadata was not published with its expected bytes."}

class SourceIdentityError(ValueError): pass

def _sha(value): return isinstance(value, str) and re.fullmatch("[0-9a-f]{64}", value) is not None
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
        if not any(struct.unpack_from("<I", raw, start + i * Raw.BONE_BYTES + 164)[0] == 5 for i in range(count)):
            return {"state": "none"}  # No new report key, artifact or writer path.
        parsed = Raw.parse(raw)
    except (Raw.DecodeError, struct.error, OverflowError):
        return {"state": "unavailable", "status": _status("layout_unsupported", context)}
    expected = [{"name": row["name"], "parent": row["parent"]} for row in parsed["bones"]]
    valid_bones = type(native_bones) is list and len(native_bones) == count and all(type(row) is dict and set(row) == {"name", "parent"}
        and type(row["name"]) is str and len(row["name"].encode("utf-8")) <= 256 and type(row["parent"]) is int for row in native_bones)
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
    if len(_compact(metadata)) > METADATA_LIMIT:
        return {"state": "unavailable", "status": _status("metadata_budget", context)}
    return {"state": "retained", "metadata": metadata}

def plan_report(base_report, inspection, newline="\n"):
    """Pure publication plan; caller must confirm external bytes before report.

    An unchanged result returns report_bytes=None: retain the exact old writer.
    The original caller-owned dictionary is never edited, compacted or trimmed.
    """
    base = copy.deepcopy(base_report)
    if inspection.get("state") == "none":
        return {"state": "unchanged", "report": base, "report_bytes": None, "artifacts": {}, "status_bytes": None, "notes": [], "_base": base, "_newline": newline}
    try:
        base_bytes = report_bytes(base, newline)
    except (ValueError, TypeError, OverflowError):
        status = _status("baseline_unserializable")
        return _fallback(base, status, newline, baseline_unusable=True)
    if len(base_bytes) > REPORT_LIMIT:
        return _fallback(base, _status("baseline_report_over_budget"), newline, baseline_unusable=True)
    if type(base) is not dict or type(base.get("native_parameters")) is not dict or KEY in base["native_parameters"]:
        raise ValueError("Expected the original unaugmented native parameter report")
    if inspection.get("state") == "retained":
        metadata = copy.deepcopy(inspection["metadata"])
        _inert(metadata, base["native_parameters"].get("bones"))
        if base.get("source_sha256") != metadata["original_source_sha256"] or hashlib.sha256(_compact(base["native_parameters"].get("bones"))).hexdigest() != metadata["native_bone_catalogue_sha256"]:
            raise SourceIdentityError("Metadata does not belong to the original report/native bone inventory")
        payload = _compact(metadata)
        if len(payload) > METADATA_LIMIT: return _fallback(base, _status("metadata_budget"), newline)
        full = copy.deepcopy(base); full["native_parameters"][KEY] = metadata
        full_bytes = report_bytes(full, newline)
        if len(full_bytes) <= REPORT_LIMIT:
            return {"state": "embedded", "report": full, "report_bytes": full_bytes, "artifacts": {}, "status_bytes": None, "notes": [], "_base": base, "_newline": newline}
        status = _status("report_budget", {"original_source_sha256": metadata["original_source_sha256"], "native_mdl_sha256": metadata["native_mdl_sha256"],
            "retention": "external_bundle_only_unmanaged", "external_metadata": {"file": METADATA_FILE, "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload), "packed_project_retention": "not_managed"}})
        result = _fallback(base, status, newline)
        result["_pending_report"] = result["report"]
        result["_pending_report_bytes"] = result["report_bytes"]
        result["_pending_status_bytes"] = result["status_bytes"]
        # No publishable external reference escapes before actual write/readback.
        result["report"] = copy.deepcopy(base); result["report_bytes"] = None; result["status_bytes"] = None
        result["state"] = "external_pending_confirmation"; result["artifacts"] = {METADATA_FILE: payload}
        return result
    if inspection.get("state") == "unavailable":
        status = inspection["status"]
        if type(status) is not dict or status.get("reason") not in {"layout_unsupported", "native_inventory_mismatch", "metadata_value_budget", "metadata_budget"} or status.get("applied") is not False or status.get("runtime_support") != "not_implemented" or status.get("binding_status") != "unattempted":
            raise ValueError("Invalid optional inspection failure state")
        return _fallback(base, copy.deepcopy(status), newline)
    raise ValueError("Unexpected optional metadata inspection state")

def _inert(metadata, native_bones):
    if type(metadata) is not dict or metadata.get("format") != FORMAT or metadata.get("status") != "retained_inert" or metadata.get("applied") is not False or metadata.get("runtime_support") != "not_implemented" or metadata.get("binding_status") != "unattempted" or metadata.get("full_native_rule_layout_verified") is not False:
        raise ValueError("Only the exact inert/unbound metadata state is admitted")
    if not _sha(metadata.get("original_source_sha256")) or not _sha(metadata.get("native_mdl_sha256")) or type(metadata.get("native_bone_count")) is not int or not 1 <= metadata["native_bone_count"] <= Raw.MAX_BONES or metadata.get("native_version") != 49 or type(metadata.get("native_version")) is not int or metadata.get("parsed_layout") != LAYOUT or metadata.get("layout_reader_sha256") != READER_SHA256 or metadata.get("sourceio_revision") != SOURCEIO_REVISION:
        raise ValueError("Invalid native metadata identity domain")
    if type(native_bones) is not list or len(native_bones) != metadata["native_bone_count"]: raise ValueError("Native bone catalogue domain differs")
    rules = metadata.get("rules")
    if type(rules) is not list or not 1 <= len(rules) <= Raw.MAX_RULES: raise ValueError("Invalid rule count")
    seen = set()
    for row in rules:
        index = row.get("native_bone_index"); parent = row.get("native_parent_index")
        if type(index) is not int or index in seen or not 0 <= index < metadata["native_bone_count"] or type(parent) is not int or not -1 <= parent < metadata["native_bone_count"] or parent == index or row.get("native_procedure_type") != 5 or type(row.get("native_procedure_type")) is not int or row.get("applied") is not False or row.get("binding_status") != "unattempted":
            raise ValueError("Invalid rule identity/inert binding")
        seen.add(index)
        if native_bones[index] != {"name": row.get("native_bone_name"), "parent": parent} or type(row.get("native_bone_name")) is not str or len(row["native_bone_name"].encode("utf-8")) > 256:
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

def _fallback(base, status, newline, baseline_unusable=False):
    encoded = _compact(status)
    if len(encoded) > STATUS_LIMIT: raise ValueError("Optional status exceeds4KiB")
    candidate = copy.deepcopy(base); payload = None
    if not baseline_unusable:
        candidate["native_parameters"][KEY] = copy.deepcopy(status)
        candidate_bytes = report_bytes(candidate, newline)
        if len(candidate_bytes) <= REPORT_LIMIT: payload = candidate_bytes
    return {"state": "status_in_report" if payload is not None else "external_status_only", "report": candidate if payload is not None else copy.deepcopy(base),
        "report_bytes": payload, "artifacts": {}, "status_bytes": encoded, "notes": [status["detail"]], "_base": copy.deepcopy(base), "_newline": newline}

def confirm_artifacts(plan, receipts):
    """Receipts follow actual exclusive writes+readback; never invent retention.

    Write requested metadata artifacts first, call this, then write the returned
    status_bytes(if any) under STATUS_FILE and publish the mandatory report.
    Log returned notes even if an optional status-sidecar write cannot succeed.
    """
    if plan["state"] != "external_pending_confirmation": return plan
    wanted = plan["artifacts"][METADATA_FILE]
    receipt = receipts.get(METADATA_FILE, {}) if type(receipts) is dict else {}
    if receipt.get("sha256") != hashlib.sha256(wanted).hexdigest() or type(receipt.get("bytes")) is not int or receipt.get("bytes") != len(wanted):
        return _fallback(plan["_base"], _status("sidecar_not_published"), plan["_newline"])
    final = dict(plan); final["state"] = "external_confirmed"; final["artifacts"] = {}
    final["report"] = final.pop("_pending_report")
    final["report_bytes"] = final.pop("_pending_report_bytes")
    final["status_bytes"] = final.pop("_pending_status_bytes")
    return final
