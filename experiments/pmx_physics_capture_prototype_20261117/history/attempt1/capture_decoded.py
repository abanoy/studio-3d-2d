"""Inactive CPU experiment: preserve fields from a decoded MMD Tools PMX model.

This does not parse a native PMX file, establish that the model came from the
fingerprinted bytes, bind HAS bones, convert units, or activate any simulation.
Only this experimental packet imports it. No installed module is imported here.
"""
from dataclasses import dataclass
import hashlib
import json
import math
import struct


PINNED_READER_SHA256 = "fb9aafe369025f221bc5a1c952d868260b1a4bb950dc33bca62645b4da454e5a"
PINNED_READER_BYTES = 51956
HARD_SOURCE_BYTES = 128 * 1024 * 1024
HARD_LIMITS = {"bones": 4096, "rigids": 512, "joints": 1024,
               "name_bytes": 1024, "capsule_bytes": 128 * 1024}
F32_MAX = struct.unpack("<f", bytes.fromhex("ffff7f7f"))[0]
VERSIONS = {bytes.fromhex("00000040"): "2.0", bytes.fromhex("66660640"): "2.1"}

RIGID_FIELDS = ("name", "name_e", "bone", "collision_group_number",
                "collision_group_mask", "type", "size", "location", "rotation",
                "mass", "velocity_attenuation", "rotation_attenuation", "bounce",
                "friction", "mode")
JOINT_FIELDS = ("name", "name_e", "mode", "src_rigid", "dest_rigid", "location",
                "rotation", "minimum_location", "maximum_location",
                "minimum_rotation", "maximum_rotation", "spring_constant",
                "spring_rotation_constant")
MODEL_FIELDS = {"filepath", "header", "name", "name_e", "comment", "comment_e",
                "vertices", "faces", "textures", "materials", "bones", "morphs",
                "display", "rigids", "joints"}
RIGID_VECTORS = {"size", "location", "rotation"}
RIGID_FLOATS = {"mass", "velocity_attenuation", "rotation_attenuation", "bounce", "friction"}
JOINT_VECTORS = set(JOINT_FIELDS) - {"name", "name_e", "mode", "src_rigid", "dest_rigid"}


class CaptureError(ValueError):
    pass


@dataclass(frozen=True)
class Limits:
    bones: int = 4096
    rigids: int = 512
    joints: int = 1024
    name_bytes: int = 1024
    capsule_bytes: int = 128 * 1024


def _limits(value):
    if type(value) is not Limits:
        raise CaptureError("Expected exact Limits object")
    for field, maximum in HARD_LIMITS.items():
        _integer(vars(value)[field], 0, maximum, "limits." + field)


def _integer(value, minimum, maximum, path):
    if type(value) is not int or not minimum <= value <= maximum:
        raise CaptureError("Invalid integer: " + path)
    return value


def _name(value, maximum, path):
    if type(value) is not str:
        raise CaptureError("Invalid text: " + path)
    try:
        size = len(value.encode("utf-8", errors="strict"))
    except UnicodeError as error:
        raise CaptureError("Unencodable text: " + path) from error
    if size > maximum:
        raise CaptureError("Text byte budget exceeded: " + path)
    return value


def _fields(obj, required, path):
    # Actual upstream models are ordinary Python instances. Read their stored
    # attributes, rather than call properties or arbitrary conversion methods.
    try:
        fields = vars(obj)
    except TypeError as error:
        raise CaptureError("Expected decoded object: " + path) from error
    if type(fields) is not dict or len(fields) > 128:
        raise CaptureError("Attribute budget exceeded: " + path)
    for name in fields:
        _name(name, 128, path + ".attribute")
    if not set(required) <= fields.keys():
        raise CaptureError("Missing decoded fields: " + path)
    return fields.copy()


def _sequence(value, maximum, path):
    if type(value) not in (list, tuple) or len(value) > maximum:
        raise CaptureError("Invalid or excessive list: " + path)
    return value


def _float(value, path):
    # FileReadStream.readFloat/readVector return Python floats expanded from
    # binary32. Refuse bool/int coercion and values not exactly representable by
    # that reader. Keep signed zero and every original float value unchanged.
    if type(value) is not float or not math.isfinite(value) or abs(value) > F32_MAX:
        raise CaptureError("Invalid native binary32 float: " + path)
    if struct.unpack("<f", struct.pack("<f", value))[0] != value:
        raise CaptureError("Value is not decoded binary32: " + path)
    return value


def _vector(value, path):
    values = _sequence(value, 3, path)
    if len(values) != 3:
        raise CaptureError("Expected three native coordinates: " + path)
    return [_float(v, path + "[" + str(i) + "]") for i, v in enumerate(values)]


def _reference(value, count, path):
    # The pinned reader normalizes -1 to None. Rigid.load also normalizes every
    # other negative bone index to None: that loss cannot be repaired here.
    if value is None:
        return None
    if count == 0:
        raise CaptureError("Reference to empty table: " + path)
    return _integer(value, 0, count - 1, path)


def _unknown(fields, known, path, issues):
    for name in sorted(set(fields) - set(known)):
        value = fields[name]
        info = {"path": path + "." + name, "code": "unsupported_decoded_attribute",
                "python_type": type(value).__name__, "values_captured": False}
        if type(value) in (list, tuple):
            _sequence(value, 1024, info["path"])
            info["item_count"] = len(value)
        issues.append(info)


def source_fingerprint(source_bytes):
    """Fingerprint supplied bytes and validate only the fixed PMX header."""
    if type(source_bytes) is not bytes or not 17 <= len(source_bytes) <= HARD_SOURCE_BYTES:
        raise CaptureError("Invalid source byte type/size")
    if source_bytes[:4] != b"PMX " or source_bytes[4:8] not in VERSIONS:
        raise CaptureError("Expected exact PMX signature and binary32 2.0/2.1 version")
    settings = source_bytes[9:17]
    if source_bytes[8] != 8 or settings[0] not in (0, 1) or settings[1] > 4 or any(v not in (1, 2, 4) for v in settings[2:]):
        raise CaptureError("Unsupported PMX fixed header")
    return {"sha256": hashlib.sha256(source_bytes).hexdigest(), "bytes": len(source_bytes),
            "version_label": VERSIONS[source_bytes[4:8]],
            "version_word_le_hex": source_bytes[4:8].hex(),
            "fixed_header_hex": source_bytes[:17].hex(),
            "validation_scope": "FIXED_HEADER_ONLY_NOT_A_NATIVE_FILE_DECODER"}


def canonical_bytes(capsule):
    """JSON transport only; callers must not treat this as a HAS reader."""
    return json.dumps(capsule, ensure_ascii=True, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def capture_decoded(model, source_bytes, *, parser_source_bytes, limits=Limits()):
    """Copy exact supported upstream attributes, with incomplete status explicit.

    Requiring pinned parser source bytes establishes a field-contract binding,
    not evidence that this decoded model was produced by it or by source_bytes.
    Failure raises before returning a partial capsule. No input is modified.
    """
    _limits(limits)
    if (type(parser_source_bytes) is not bytes or len(parser_source_bytes) != PINNED_READER_BYTES
            or hashlib.sha256(parser_source_bytes).hexdigest() != PINNED_READER_SHA256):
        raise CaptureError("Pinned upstream field-contract source mismatch")
    source = source_fingerprint(source_bytes)
    fields = _fields(model, {"bones", "rigids", "joints"}, "model")
    bones = _sequence(fields["bones"], limits.bones, "model.bones")
    rigids = _sequence(fields["rigids"], limits.rigids, "model.rigids")
    joints = _sequence(fields["joints"], limits.joints, "model.joints")
    issues = []
    _unknown(fields, MODEL_FIELDS, "model", issues)
    if source["version_label"] == "2.1":
        issues.append({"path": "source", "code": "pmx_2_1_unsupported_by_pinned_reader",
                       "soft_body_table": "UNSUPPORTED_NOT_DECODED", "soft_body_count": None})
    header = fields.get("header")
    if header is not None:
        header_fields = _fields(header, {"version"}, "model.header")
        version = _float(header_fields["version"], "model.header.version")
        if struct.pack("<f", version).hex() != source["version_word_le_hex"]:
            raise CaptureError("Decoded/source header version mismatch")
    native_bones = []
    names = {}
    for i, bone in enumerate(bones):
        values = _fields(bone, {"name", "name_e"}, "bones[" + str(i) + "]")
        row = {"index": i, "name": _name(values["name"], limits.name_bytes, "bone.name"),
               "name_e": _name(values["name_e"], limits.name_bytes, "bone.name_e")}
        native_bones.append(row)
        names.setdefault(row["name"], []).append(i)
    body_rows = []
    for i, body in enumerate(rigids):
        path = "rigids[" + str(i) + "]"
        values = _fields(body, RIGID_FIELDS, path)
        row = {"index": i}
        for name in RIGID_FIELDS:
            value = values[name]
            if name in ("name", "name_e"):
                row[name] = _name(value, limits.name_bytes, path + "." + name)
            elif name == "bone":
                row[name] = _reference(value, len(bones), path + ".bone")
            elif name == "collision_group_number":
                row[name] = _integer(value, 0, 15, path + "." + name)
            elif name == "collision_group_mask":
                row[name] = _integer(value, 0, 65535, path + "." + name)
            elif name in ("type", "mode"):
                row[name] = _integer(value, -128, 127, path + "." + name)
                if value not in (0, 1, 2):
                    issues.append({"path": path + "." + name, "code": "unsupported_rigid_" + name,
                                   "native_value": value})
            elif name in RIGID_VECTORS:
                row[name] = _vector(value, path + "." + name)
            elif name in RIGID_FLOATS:
                row[name] = _float(value, path + "." + name)
        _unknown(values, RIGID_FIELDS, path, issues)
        body_rows.append(row)
    joint_rows = []
    for i, joint in enumerate(joints):
        path = "joints[" + str(i) + "]"
        values = _fields(joint, JOINT_FIELDS, path)
        row = {"index": i}
        for name in JOINT_FIELDS:
            value = values[name]
            if name in ("name", "name_e"):
                row[name] = _name(value, limits.name_bytes, path + "." + name)
            elif name == "mode":
                row[name] = _integer(value, -128, 127, path + ".mode")
                if value != 0:
                    issues.append({"path": path + ".mode", "code": "unsupported_joint_mode",
                                   "native_value": value})
            elif name in ("src_rigid", "dest_rigid"):
                row[name] = _reference(value, len(rigids), path + "." + name)
            elif name in JOINT_VECTORS:
                row[name] = _vector(value, path + "." + name)
        _unknown(values, JOINT_FIELDS, path, issues)
        joint_rows.append(row)
    bindings = []
    for i, row in enumerate(native_bones):
        reason = ("EMPTY_NATIVE_NAME" if not row["name"] else "DUPLICATE_NATIVE_NAME"
                  if len(names[row["name"]]) > 1 else "NO_HAS_CROSSWALK")
        bindings.append({"native_bone_index": i, "native_name": row["name"],
                         "status": "UNRESOLVED", "reason": reason})
    capsule = {
        "prototype_only": True, "applied": False,
        "source_fingerprint": source,
        "upstream_field_contract": {"module": "mmd_tools/core/pmx/__init__.py",
                                    "sha256": PINNED_READER_SHA256, "bytes": PINNED_READER_BYTES},
        "capture_scope": "Exact supported decoded Rigid/Joint fields; bone index/name catalogue only",
        "value_policy": "Unchanged native decoded values; no units, basis, scale or solver conversion",
        "native_file_join": "UNQUALIFIED",
        "native_file_preservation_complete": False,
        "runtime_support": "NONE",
        "decoded_supported_fields_complete": not bool(issues),
        "issues": issues,
        "limitations": [
            "Supplied source fingerprint is not proof that decoded tables came from those bytes",
            "Pinned upstream reader rejects PMX 2.1 and has no soft-body table",
            "Pinned Rigid.load maps all negative bone indices to None; original sentinel is not recoverable here",
            "Pinned Joint.load can fill truncated fields and load() can swallow struct.error",
            "Decoded names can contain upstream replacement characters; original encoded bytes are not reconstructed",
            "No native file, portable HAS, live preview, Off, recording or render integration qualification",
        ],
        "bones": native_bones, "rigids": body_rows, "joints": joint_rows,
        "bone_bindings": bindings,
    }
    if len(canonical_bytes(capsule)) > limits.capsule_bytes:
        raise CaptureError("Complete capsule exceeds byte budget; no partial result returned")
    return capsule
