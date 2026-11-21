"""Bounded, read-only common MDL49 skin/bodypart table catalogue.

This module accepts already acquired bytes. It imports no converter, opens no
files and verifies neither resource closure nor converted/native appearance.
The caller must verify the supplied original-source SHA against its own input.
See README.md for the documented layout scope and conservative refusals.
"""
from __future__ import annotations

import hashlib
import json
import re
import struct


FORMAT = "studio_source_mdl_choices_1"
MAX_FILE_BYTES = 16 * 1024 * 1024
MAX_RESULT_BYTES = 256 * 1024
HEADER_PREFIX_BYTES = 240
MAX_MATERIALS = 2048
MAX_SKIN_REFERENCES = 2048
MAX_SKINS = 256
MAX_BODYGROUPS = 256
MAX_CHOICES = 256
MAX_TOTAL_CHOICES = 4096
MAX_STRING_BYTES = 1024  # Includes the terminating NUL.
MAX_MEMBER_BYTES = 1024

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_WINDOWS_DEVICES = re.compile(r"(?:CON|PRN|AUX|NUL|CONIN\$|CONOUT\$|COM[1-9¹²³]|LPT[1-9¹²³])\Z", re.IGNORECASE)


class CatalogueError(ValueError):
    """An explicit refusal, never a successful incomplete catalogue."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(code + ": " + message)


def _require(condition: bool, code: str, message: str) -> None:
    if not condition:
        raise CatalogueError(code, message)


def _source_sha(value: str) -> str:
    _require(type(value) is str and _SHA256.fullmatch(value) is not None,
             "source_sha256", "Expected the caller-verified lowercase original-source SHA256")
    return value


def _member(value: str) -> str:
    _require(type(value) is str, "member", "Selected member must be a canonical relative string")
    try:
        encoded = value.encode("utf-8", errors="strict")
    except UnicodeError as error:
        raise CatalogueError("member", "Selected member is not valid Unicode") from error
    _require(len(encoded) <= MAX_MEMBER_BYTES, "member", "Selected member exceeds1024 UTF-8 bytes")
    if not value:
        return value  # Loose MDL caller may use its enclosing source identity alone.
    _require(not any(ord(c) < 32 or ord(c) == 127 or c in '\\:<>"|?*' for c in value)
             and not value.startswith("/"),
             "member", "Selected member must use relative forward slashes without controls or ADS")
    for part in value.split("/"):
        _require(part not in ("", ".", "..") and not part.endswith((" ", "."))
                 and not _WINDOWS_DEVICES.fullmatch(part.split(".", 1)[0].rstrip(" ")),
                 "member", "Unsafe, reserved or noncanonical selected-member component")
    return value


def _count(value: int, maximum: int, label: str, minimum: int = 0) -> int:
    _require(type(value) is int and minimum <= value <= maximum,
             "count", f"Unsupported {label} count; expected {minimum}..{maximum}")
    return value


class _Reader:
    def __init__(self, raw: bytes):
        _require(type(raw) is bytes, "input_type", "Native input must be immutable bytes")
        _require(HEADER_PREFIX_BYTES <= len(raw) <= MAX_FILE_BYTES, "file_size",
                 "Native MDL must contain the240-byte inspected prefix and be at most16MiB")
        self.raw = raw
        self.intervals = [(0, HEADER_PREFIX_BYTES, "inspected header prefix")]

    def unpack(self, fmt: str, offset: int):
        size = struct.calcsize("<" + fmt)
        _require(0 <= offset <= len(self.raw) and size <= len(self.raw) - offset,
                 "table_range", "Required native fields lie outside the native file")
        return struct.unpack_from("<" + fmt, self.raw, offset)

    def table(self, base: int, relative: int, count: int, stride: int, label: str,
              maximum: int, minimum: int = 0) -> list[int]:
        _count(count, maximum, label, minimum)
        if count == 0:
            _require(relative == 0, "empty_table_offset",
                     f"Unsupported nonzero offset for empty {label} table")
            return []
        start = base + relative
        size = count * stride
        # Bodypart modelindex is signed and relative. A backward pointer is
        # supported when its entire owned table is in-bounds and disjoint.
        _require(relative != 0 and start >= HEADER_PREFIX_BYTES and start <= len(self.raw)
                 and size <= len(self.raw) - start,
                 "table_range", f"{label} table lies outside the supported file region")
        end = start + size
        for other_start, other_end, other_label in self.intervals:
            _require(end <= other_start or start >= other_end, "table_overlap",
                     f"{label} table aliases or overlaps {other_label}")
        self.intervals.append((start, end, label))
        return list(range(start, end, stride))

    def cstring(self, start: int) -> bytes:
        _require(0 <= start < len(self.raw), "string_range", "Native name pointer lies outside the file")
        end = self.raw.find(b"\0", start, min(len(self.raw), start + MAX_STRING_BYTES))
        _require(end >= start, "string_termination", "Native name is not NUL-terminated within1024 bytes")
        for other_start, other_end, label in self.intervals:
            _require(end + 1 <= other_start or start >= other_end, "string_table_overlap",
                     f"Native name bytes alias or overlap {label}")
        # Exact shared/suffix-pooled strings are allowed outside structural tables.
        # Their native table indices remain distinct.
        return self.raw[start:end]

    def fixed_model_name(self, start: int) -> bytes:
        raw = self.raw[start:start + 64]  # The owning148-byte model table was already checked.
        end = raw.find(b"\0")
        _require(end >= 0, "string_termination", "Native model name is not NUL-terminated within64 bytes")
        return raw[:end]


def _named(raw: bytes, fallback: str) -> dict:
    # Latin-1 is an explicit reversible byte mapping, not an assertion of the
    # author's text encoding. Numeric native indices are the only selection IDs.
    name = raw.decode("latin-1")
    display_name = "".join(f"\\x{ord(c):02x}" if ord(c) < 32 or 127 <= ord(c) < 160 else c for c in name)
    return {"name": name, "raw_name_sha256": hashlib.sha256(raw).hexdigest(),
            "display_name": display_name if raw else fallback}


def _encoded(value: dict, *, pretty: bool) -> bytes:
    encoder = json.JSONEncoder(ensure_ascii=True, sort_keys=True, allow_nan=False,
                               indent=2 if pretty else None,
                               separators=None if pretty else (",", ":"))
    chunks = []
    size = 0
    for chunk in encoder.iterencode(value):
        encoded = chunk.encode("ascii")
        size += len(encoded)
        _require(size <= MAX_RESULT_BYTES, "result_too_large",
                 "Complete metadata JSON exceeds256KiB; no truncated catalogue is returned")
        chunks.append(encoded)
    return b"".join(chunks)


def json_bytes(value: dict) -> bytes:
    """Deterministic two-space ASCII JSON, refusing a result above256KiB."""
    _require(type(value) is dict, "result_type", "Expected a catalogue dictionary")
    return _encoded(value, pretty=True)


def catalogue(raw: bytes, source_sha256: str, member: str = "") -> dict:
    """Return a complete supported table catalogue or raise CatalogueError.

    source_sha256 is caller-verified original-file provenance (for example a
    container SHA). native_mdl_sha256 is independently computed from these exact
    bytes. member is an already selected canonical resource context, not a path
    this module reads. An empty member is permitted for loose native input.
    """
    original_source_sha256 = _source_sha(source_sha256)
    selected_member = _member(member)
    reader = _Reader(raw)
    _require(raw[:4] == b"IDST", "magic", "Only the uncompressed IDST MDL magic is supported")
    version, checksum = reader.unpack("iI", 4)
    _require(version == 49, "version", "Only the documented common MDL49 table layout is supported")
    declared_length, = reader.unpack("I", 76)
    _require(declared_length == len(raw), "declared_length", "Declared native length differs from actual bytes")

    material_count, material_offset = reader.unpack("2i", 204)
    _count(material_count, MAX_MATERIALS, "material")
    _require(material_count > 0, "unsupported_materials", "A nonempty native material table is required")
    columns, families, skin_offset = reader.unpack("3i", 220)
    _count(columns, MAX_SKIN_REFERENCES, "skin reference")
    _count(families, MAX_SKINS, "skin family")
    _require(columns > 0 and families > 0, "unsupported_skins", "A nonempty native skin table is required")
    group_count, group_offset = reader.unpack("2i", 232)

    material_ats = reader.table(0, material_offset, material_count, 64, "material", MAX_MATERIALS, 1)
    skin_ats = reader.table(0, skin_offset, columns * families, 2, "skin entry",
                            MAX_SKIN_REFERENCES * MAX_SKINS, 1)
    group_ats = reader.table(0, group_offset, group_count, 16, "bodygroup", MAX_BODYGROUPS)

    # Reserve ALL structural tables before following ANY external name pointer.
    # Otherwise an early string could alias a not-yet-visited later model table.
    native_groups = []
    total_choices = 0
    for index, group_at in enumerate(group_ats):
        name_offset, choice_count, native_base, model_offset = reader.unpack("4i", group_at)
        _count(choice_count, MAX_CHOICES, "bodygroup choice", 1)
        _require(native_base > 0, "bodygroup_base", "Nonpositive native bodygroup base is unsupported")
        total_choices += choice_count
        _require(total_choices <= MAX_TOTAL_CHOICES, "total_choices", "Native choices exceed4096")
        model_ats = reader.table(group_at, model_offset, choice_count, 148,
                                f"bodygroup{index} model", MAX_CHOICES, 1)
        native_groups.append((group_at, name_offset, native_base, model_ats))

    materials = []
    for index, material_at in enumerate(material_ats):
        name_offset, = reader.unpack("i", material_at)
        name = reader.cstring(material_at + name_offset)
        _require(bool(name), "material_name", "An empty native material name is unsupported")
        materials.append({"index": index, **_named(name, f"Material {index + 1} (empty name)")})

    skins = []
    for family in range(families):
        indices = []
        for at in skin_ats[family * columns:(family + 1) * columns]:
            material_index, = reader.unpack("H", at)
            _require(material_index < material_count, "material_index",
                     "A skin entry refers outside the native material table")
            indices.append(material_index)
        skins.append({"index": family, "material_indices": indices,
                      "material_names": [materials[i]["name"] for i in indices]})

    groups = []
    group_names = set()
    for index, (group_at, name_offset, native_base, model_ats) in enumerate(native_groups):
        name = reader.cstring(group_at + name_offset)
        _require(name not in group_names, "duplicate_bodygroup",
                 "Duplicate exact native bodygroup names make downstream group correspondence ambiguous")
        group_names.add(name)
        choices = []
        for choice, model_at in enumerate(model_ats):
            vertex_count, = reader.unpack("i", model_at + 80)
            _require(vertex_count >= 0, "vertex_count", "Native vertex count is negative")
            choices.append({"index": choice,
                            **_named(reader.fixed_model_name(model_at), f"Choice {choice + 1} (empty name)"),
                            "vertex_count": vertex_count, "true_blank": vertex_count == 0})
        groups.append({"index": index, **_named(name, f"Part {index + 1} (empty name)"),
                       "native_base": native_base, "choices": choices})

    result = {"format": FORMAT, "original_source_sha256": original_source_sha256,
              "selected_member": selected_member,
              "native_mdl_sha256": hashlib.sha256(raw).hexdigest(), "native_mdl_bytes": len(raw),
              "native_version": version, "native_checksum": checksum,
              "name_encoding": "latin-1 (reversible byte mapping; author encoding unverified)",
              "skin_reference_count": columns, "materials": materials, "skins": skins,
              "bodygroups": groups,
              "scope": {"kind": "mdl49_static_table_metadata_only",
                        "inspected_header_prefix_bytes": HEADER_PREFIX_BYTES,
                        "native_fidelity_verified": False, "resources_verified": False,
                        "converted_object_correspondence_verified": False,
                        "excluded": ["geometry", "bones", "mesh material-column correspondence",
                                     "flex evaluation", "native shaders", "jiggle", "animation"]}}
    result["catalogue_sha256"] = hashlib.sha256(_encoded(result, pretty=False)).hexdigest()
    json_bytes(result)  # Enforce the complete pretty-JSON budget including the digest.
    return result
