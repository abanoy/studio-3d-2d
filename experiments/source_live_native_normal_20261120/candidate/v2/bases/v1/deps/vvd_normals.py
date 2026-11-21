"""Independent bounded VVD v4 LOD0 normal/vertex-index reader.

Only normal words and the raw-record index mapping are returned. Positions,
weights, UVs, tangents, other LOD arrays and optional extra attributes are not
decoded. The result is native-derived private data; do not publish its arrays.
"""
import math
import struct

HEADER_BYTES = 64
VERTEX_BYTES = 48
NORMAL_OFFSET = 28
MAX_VERTICES = 200_000
MAX_FIXUPS = 200_000


def _require(value, message):
    if not value:
        raise ValueError(message)


def _span(offset, count, stride, size, label):
    _require(type(offset) is int and type(count) is int and offset >= HEADER_BYTES
             and count >= 0 and stride > 0, "Invalid " + label + " declaration")
    end = offset + count * stride
    _require(offset <= size and end <= size, "Truncated " + label)
    return offset, end


def decode_lod0_normals(raw, expected_checksum=None):
    """Return immutable LOD0 normal tuples and matching raw VVD record indices.

    Fixups are applied in file order. For LOD0 every unsigned fixup's LOD tag
    qualifies, including a tag above zero. Exact declared LOD0 output coverage
    is required, but duplicated source indices are retained rather than treated
    as an undocumented invalidity. Unused LOD-count slots are not interpreted.
    """
    _require(type(raw) in (bytes, bytearray, memoryview), "VVD bytes required")
    raw = bytes(raw)
    _require(len(raw) >= HEADER_BYTES, "Truncated VVD header")
    header = struct.unpack_from("<4s15I", raw)
    magic, version, checksum, lod_count = header[:4]
    counts = header[4:12]
    fixup_count, fixup_offset, vertex_offset, tangent_offset = header[12:16]
    _require(magic == b"IDSV" and version == 4, "VVD v4 IDSV required")
    _require(1 <= lod_count <= 8, "Supported VVD LOD count required")
    count = counts[0]
    _require(1 <= count <= MAX_VERTICES, "Bounded nonempty LOD0 required")
    _require(all(value <= MAX_VERTICES for value in counts[:lod_count]),
             "Active LOD vertex-count budget exceeded")
    if expected_checksum is not None:
        _require(type(expected_checksum) is int and 0 <= expected_checksum <= 0xFFFFFFFF,
                 "Explicit uint32 checksum required")
        _require(checksum == expected_checksum, "VVD checksum differs")
    vertex_span = _span(vertex_offset, count, VERTEX_BYTES, len(raw), "vertex table")
    if tangent_offset:
        tangent_span = _span(tangent_offset, count, 16, len(raw), "tangent table")
        _require(tangent_span[1] <= vertex_span[0] or vertex_span[1] <= tangent_span[0],
                 "Overlapping vertex/tangent tables")
    _require(fixup_count <= MAX_FIXUPS, "Fixup-count budget exceeded")
    if fixup_count:
        fixup_span = _span(fixup_offset, fixup_count, 12, len(raw), "fixup table")
        _require(fixup_span[1] <= vertex_span[0] or vertex_span[1] <= fixup_span[0],
                 "Overlapping fixup/vertex tables")
        indices = []
        for index in range(fixup_count):
            lod, start, length = struct.unpack_from("<3I", raw, fixup_offset + index * 12)
            _require(lod < 8, "Fixup LOD tag outside supported range")
            _require(start <= count and length <= count - start,
                     "Fixup source range outside vertex table")
            _require(len(indices) + length <= count, "Fixup output exceeds LOD0 count")
            indices.extend(range(start, start + length))
        _require(len(indices) == count, "Incomplete LOD0 fixup coverage")
    else:
        indices = list(range(count))
    normals = []
    for index in indices:
        normal = struct.unpack_from("<3f", raw, vertex_offset + index * VERTEX_BYTES + NORMAL_OFFSET)
        _require(all(math.isfinite(value) for value in normal), "Nonfinite source normal")
        normals.append(normal)
    return {"format": "has_independent_vvd_lod0_normals_1", "version": version,
            "checksum": checksum, "lod_count": lod_count, "vertex_count": count,
            "fixup_count": fixup_count, "vertex_stride": VERTEX_BYTES,
            "normal_offset": NORMAL_OFFSET, "normals": tuple(normals),
            "raw_vertex_indices": tuple(indices)}
