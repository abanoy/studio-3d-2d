import copy
import hashlib
import io
import json
import struct
import source_jiggle_metadata as M
ORIGINAL = hashlib.sha256(b"authored original archive identity").hexdigest()

def authored(count=2, jiggle=True, name_length=12):
    bones = count + 1; start = 408; end = start + bones * 216
    payload_end = end + count * 120
    names = [(("bone%03d_" % i) + "x" * name_length)[:name_length] for i in range(bones)]
    raw = bytearray(payload_end + sum(len(n) + 1 for n in names))
    raw[:4] = b"IDST"; struct.pack_into("<iI", raw, 4, 49, 0x1234)
    struct.pack_into("<I", raw, 76, len(raw)); struct.pack_into("<2I", raw, 156, bones, start)
    pointer = payload_end
    for i, name in enumerate(names):
        at = start + i * 216; encoded = name.encode("ascii")
        struct.pack_into("<2i", raw, at, pointer - at, -1 if i == 0 else 0)
        raw[pointer:pointer + len(encoded) + 1] = encoded + b"\0"; pointer += len(encoded) + 1
        target = end + (count - i) * 120 if i else 0
        struct.pack_into("<3I", raw, at + 160, 1284, 5 if i and jiggle else 0, target - at if i and jiggle else 0)
        if i:
            values = [float(j) for j in range(29)]; values[15], values[16] = -7.25, 8.5
            struct.pack_into("<i29f", raw, target, 0x31, *values)
    native_bones = [{"name": name, "parent": -1 if i == 0 else 0} for i, name in enumerate(names)]
    return bytes(raw), native_bones

def legacy_bytes(value, newline="\r\n"):
    buffer = io.BytesIO()
    stream = io.TextIOWrapper(buffer, encoding="utf-8", newline=newline)
    stream.write(json.dumps(value, ensure_ascii=True, indent=2)); stream.flush()
    raw = buffer.getvalue(); stream.detach(); return raw

def base_report(bones):
    return {"source_sha256": ORIGINAL, "source_file": "authored.mdl", "scale": 0.01905, "native_parameters": {"bones": copy.deepcopy(bones), "selected_skin": 0}, "warnings": [], "limits": ["existing static limitation"], "padding": ""}

def padded(base, target, metadata=None):
    result = copy.deepcopy(base)
    candidate = copy.deepcopy(result)
    if metadata is not None: candidate["native_parameters"][M.KEY] = metadata
    count = target - len(legacy_bytes(candidate))
    assert count >= 0
    result["padding"] = "x" * count
    return result
