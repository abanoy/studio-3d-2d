"""Read-only legacy asset inventory. Never loads Lua, runs models, or extracts archives."""
from pathlib import Path, PurePosixPath
import argparse
import collections
import hashlib
import io
import json
import lzma
import struct


class AssetError(ValueError):
    pass


class Reader:
    def __init__(self, stream):
        self.stream = stream

    def read(self, count):
        if not 0 <= count <= 16 * 1024 * 1024:
            raise AssetError("Invalid field size")
        data = self.stream.read(count)
        if len(data) != count:
            raise AssetError("Truncated asset header/index")
        return data

    def unpack(self, fmt):
        return struct.unpack("<" + fmt, self.read(struct.calcsize("<" + fmt)))

    def zero(self):
        data = bytearray()
        while len(data) < 65536:
            value = self.read(1)
            if value == b"\0":
                return data.decode("utf-8", "replace")
            data += value
        raise AssetError("Unterminated archive string")


def safe_member(name):
    name = name.replace("\\", "/")
    parts = name.split("/")
    if not name or name.startswith("/") or ":" in name or any(p in ("", ".", "..") for p in parts):
        raise AssetError("Unsafe archive/resource path")
    return name


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def gma_index(stream, total_size):
    r = Reader(stream)
    if r.read(4) != b"GMAD":
        raise AssetError("Not a GMAD container")
    version, = r.unpack("B")
    if version not in (1, 2, 3):
        raise AssetError("Unsupported GMA version")
    r.read(16)  # owner/timestamp are not needed for asset conversion.
    if version > 1:
        for _ in range(1024):
            if not r.zero():
                break
        else:
            raise AssetError("Excessive required-content records")
    title = r.zero()
    r.zero()  # untrusted description
    r.zero()  # untrusted author metadata
    r.read(4)
    entries = []
    relative_offset = 0
    while True:
        number, = r.unpack("I")
        if number == 0:
            break
        if number != len(entries) + 1 or len(entries) >= 100000:
            raise AssetError("Invalid/excessive GMA index")
        name = safe_member(r.zero())
        length, crc = r.unpack("qI")
        if length < 0 or length > total_size:
            raise AssetError("Invalid GMA entry length")
        entries.append({"name": name, "size": length, "crc32": crc, "relative_offset": relative_offset})
        relative_offset += length
    payload_start = stream.tell()
    if payload_start + relative_offset > total_size:
        raise AssetError("GMA payload exceeds container size")
    suffixes = collections.Counter(PurePosixPath(e["name"]).suffix.lower() for e in entries)
    models = [e["name"] for e in entries if e["name"].lower().endswith(".mdl")]
    names = {e["name"].lower() for e in entries}
    dependencies = []
    for model in models:
        base = model[:-4].lower()
        dependencies.append({"model": model, "vvd_present": base + ".vvd" in names,
                             "vtx_present": any(n.startswith(base + ".") and n.endswith(".vtx") for n in names)})
    return {"kind": "gma", "version": version, "title": title[:200], "entry_count": len(entries),
            "file_types": dict(suffixes), "models": dependencies,
            "maps": [e["name"] for e in entries if e["name"].lower().endswith((".bsp", ".vmf"))],
            "scripts_not_executed": suffixes.get(".lua", 0), "payload_start": payload_start,
            "entries": entries}


def legacy_prefix(path):
    with Path(path).open("rb") as stream:
        header = stream.read(13)
        if len(header) != 13:
            raise AssetError("Short LZMA header")
        size = int.from_bytes(header[5:13], "little")
        if size == 0xFFFFFFFFFFFFFFFF: size = None  # standard unknown-size LZMA-Alone stream
        if size is not None and size > 512 * 1024 * 1024:
            raise AssetError("Legacy container exceeds 512 MiB inventory limit")
        stream.seek(0)
        decoder = lzma.LZMADecompressor(format=lzma.FORMAT_ALONE, memlimit=128 * 1024 * 1024)
        prefix = bytearray()
        while len(prefix) < 8 * 1024 * 1024 and not decoder.eof:
            block = stream.read(65536) if decoder.needs_input else b""
            if decoder.needs_input and not block:
                break
            prefix.extend(decoder.decompress(block, max_length=8 * 1024 * 1024 - len(prefix)))
        return io.BytesIO(prefix), size


def pmd_summary(path):
    with Path(path).open("rb") as stream:
        r = Reader(stream)
        if r.read(3) != b"Pmd": raise AssetError("Not PMD")
        version, = r.unpack("f")
        if abs(version - 1.0) > 0.0001: raise AssetError("Unsupported PMD version")
        name = r.read(20).split(b"\0")[0].decode("cp932", "replace")
        r.read(256)
        vertices, = r.unpack("I")
        if vertices > 2000000: raise AssetError("Excessive PMD vertices")
        stream.seek(vertices * 38, 1)
        indices, = r.unpack("I")
        if indices > 12000000: raise AssetError("Excessive PMD indices")
        stream.seek(indices * 2, 1)
        count, = r.unpack("I")
        if count > 10000: raise AssetError("Excessive PMD materials")
        textures = []
        for _ in range(count):
            r.read(50)
            texture = r.read(20).split(b"\0")[0].decode("cp932", "replace")
            textures.extend(t for t in texture.split("*") if t)
        bones, = r.unpack("H")
    return {"kind": "pmd", "version": version, "name": name, "vertices": vertices,
            "triangles": indices // 3, "materials": count, "bones": bones, "textures": sorted(set(textures))}


def pmx_summary(path):
    with Path(path).open("rb") as stream:
        r = Reader(stream)
        if r.read(4) != b"PMX ": raise AssetError("Not PMX")
        version, = r.unpack("f")
        if min(abs(version - 2.0), abs(version - 2.1)) > 0.0001: raise AssetError("Unsupported PMX version")
        length, = r.unpack("B")
        globals_ = r.read(length)
        if length != 8 or globals_[0] not in (0, 1) or globals_[1] > 4 or any(v not in (1, 2, 4) for v in globals_[2:]):
            raise AssetError("Unsupported PMX header")
        encoding = "utf-16-le" if globals_[0] == 0 else "utf-8"

        def text():
            count, = r.unpack("i")
            return r.read(count).decode(encoding)

        name = text(); english = text(); text(); text()
        vertices, = r.unpack("i")
        if not 0 <= vertices <= 2000000: raise AssetError("Excessive PMX vertices")
        bone_size = globals_[5]
        for _ in range(vertices):
            r.read(32 + globals_[1] * 16)
            deform, = r.unpack("B")
            sizes = {0: bone_size, 1: bone_size * 2 + 4, 2: bone_size * 4 + 16,
                     3: bone_size * 2 + 40, 4: bone_size * 4 + 16}
            if deform not in sizes: raise AssetError("Unknown PMX deformation")
            r.read(sizes[deform] + 4)
        indices, = r.unpack("i")
        if not 0 <= indices <= 12000000: raise AssetError("Excessive PMX indices")
        stream.seek(indices * globals_[2], 1)
        count, = r.unpack("i")
        if not 0 <= count <= 10000: raise AssetError("Excessive PMX textures")
        textures = [text() for _ in range(count)]
        materials, = r.unpack("i")
    return {"kind": "pmx", "version": version, "name": name, "english_name": english,
            "vertices": vertices, "triangles": indices // 3, "materials": materials, "textures": textures}


def inspect(path):
    path = Path(path).resolve(strict=True)
    with path.open("rb") as stream:
        head = stream.read(16)
        stream.seek(0)
        if head[:4] == b"GMAD":
            result = gma_index(stream, path.stat().st_size)
        elif head[:4] == b"PMX ": result = pmx_summary(path)
        elif head[:3] == b"Pmd": result = pmd_summary(path)
        elif head[:4] == b"VBSP": result = {"kind": "bsp", "version": struct.unpack("<i", head[4:8])[0]}
        elif path.suffix.lower() == ".bin":
            prefix, size = legacy_prefix(path)
            result = gma_index(prefix, size if size is not None else 512 * 1024 * 1024)
            result.update({"wrapper": "lzma-alone", "uncompressed_size": size,
                           "note": "Index only; full payload integrity has not been verified."})
        else: raise AssetError("Unknown asset signature")
    if "textures" in result:
        result["texture_dependencies"] = []
        for texture in result["textures"]:
            try:
                relative = safe_member(texture)
                target = (path.parent / relative).resolve()
                target.relative_to(path.parent.resolve())
                result["texture_dependencies"].append({"name": texture, "present": target.is_file()})
            except (ValueError, OSError):
                result["texture_dependencies"].append({"name": texture, "present": False, "unsafe": True})
    result.update({"file": path.name, "bytes": path.stat().st_size, "sha256": digest(path)})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("assets", nargs="+")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = []
    for path in args.assets:
        try: report.append(inspect(path))
        except (OSError, ValueError, lzma.LZMAError) as error: report.append({"file": Path(path).name, "error": str(error)})
    text = json.dumps(report, ensure_ascii=True, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream: stream.write(text)
    else: print(text)
    return int(any("error" in item for item in report))


if __name__ == "__main__":
    raise SystemExit(main())
