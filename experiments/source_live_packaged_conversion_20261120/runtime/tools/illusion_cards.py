"""Read-only KK/KKS/AI character-card inventory, not a geometry converter.

Only the PNG container and bounded MessagePack block index are decoded. Character
blocks and plugin extensions remain opaque; no game code or .NET objects execute.
Layout references: docs/illusion_import.md. Original implementation, Python stdlib.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import zlib

MAX_FILE = 64 * 1024 * 1024
MARKERS = {"【KoiKatuChara】": "koikatsu", "【KoiKatuCharaS】": "koikatsu-party",
           "【KoiKatuCharaSP】": "koikatsu-party-special",
           "【KoiKatuCharaSun】": "koikatsu-sunshine", "【AIS_Chara】": "ai-shoujo"}


class CardError(ValueError):
    pass


class Reader:
    def __init__(self, data):
        self.data, self.pos, self.nodes = data, 0, 0

    def take(self, count):
        if count < 0 or count > len(self.data) - self.pos:
            raise CardError("Truncated card field")
        start = self.pos
        self.pos += count
        return self.data[start:self.pos]

    def number(self, fmt):
        return struct.unpack(fmt, self.take(struct.calcsize(fmt)))[0]

    def dotnet_string(self):
        size = 0
        for shift in range(0, 35, 7):
            byte = self.number("B")
            size |= (byte & 127) << shift
            if byte < 128:
                if size > 4096:
                    raise CardError("Card string exceeds limit")
                return self.take(size).decode("utf-8", errors="strict")
        raise CardError("Invalid 7-bit string length")

    def msgpack(self, depth=0):
        self.nodes += 1
        if depth > 12 or self.nodes > 4096:
            raise CardError("Block index is too complex")
        code = self.number("B")
        if code <= 127: return code
        if code >= 224: return code - 256
        if 160 <= code <= 191:
            return self.take(code & 31).decode("utf-8", errors="strict")
        if 144 <= code <= 159: kind, count = "array", code & 15
        elif 128 <= code <= 143: kind, count = "map", code & 15
        elif code in (220, 221, 222, 223):
            kind = "array" if code < 222 else "map"
            count = self.number(">H" if code in (220, 222) else ">I")
        elif code in (204, 205, 206, 207, 208, 209, 210, 211):
            return self.number({204: ">B", 205: ">H", 206: ">I", 207: ">Q",
                                208: ">b", 209: ">h", 210: ">i", 211: ">q"}[code])
        elif code in (217, 218, 219):
            size = self.number({217: ">B", 218: ">H", 219: ">I"}[code])
            if size > 4096: raise CardError("Block index string exceeds limit")
            return self.take(size).decode("utf-8", errors="strict")
        else:
            raise CardError("Unsupported block-index MessagePack type")
        if count > 256: raise CardError("Block index collection exceeds limit")
        if kind == "array": return [self.msgpack(depth + 1) for _ in range(count)]
        result = {}
        for _ in range(count):
            key = self.msgpack(depth + 1)
            if not isinstance(key, str) or key in result:
                raise CardError("Invalid or duplicate block index key")
            result[key] = self.msgpack(depth + 1)
        return result


def png_end(data):
    r = Reader(data)
    if r.take(8) != b"\x89PNG\r\n\x1a\n": raise CardError("Not a PNG card")
    seen_header = False
    for index in range(100000):
        size, kind = r.number(">I"), r.take(4)
        payload = r.take(size)
        crc = r.number(">I")
        if zlib.crc32(kind + payload) & 0xffffffff != crc:
            raise CardError("PNG chunk CRC mismatch")
        if index == 0:
            if kind != b"IHDR" or size != 13: raise CardError("PNG header missing")
            width, height = struct.unpack(">II", payload[:8])
            if not width or not height or width * height > 64000000:
                raise CardError("PNG dimensions exceed limit")
            seen_header = True
        if kind == b"IEND":
            if size != 0 or not seen_header: raise CardError("Invalid PNG end")
            return r.pos
    raise CardError("PNG chunk count exceeds limit")


def inventory(path):
    path = Path(path).resolve(strict=True)
    if not 0 < path.stat().st_size <= MAX_FILE: raise CardError("Card exceeds 64 MiB limit")
    data = path.read_bytes()
    if len(data) > MAX_FILE: raise CardError("Card exceeds 64 MiB limit")
    end = png_end(data)
    if end == len(data): raise CardError("Ordinary PNG: no appended character data")
    r = Reader(data[end:])
    product = r.number("<i")
    marker = r.dotnet_string()
    if marker not in MARKERS: raise CardError("Unsupported character-card marker")
    version = r.dotnet_string()
    preview_size = 0
    if MARKERS[marker] == "ai-shoujo":
        r.number("<i")  # language; user/data IDs are intentionally not reported
        r.dotnet_string()
        r.dotnet_string()
    else:
        preview_size = r.number("<i")
        r.take(preview_size)
    header_size = r.number("<i")
    if not 0 < header_size <= 65536: raise CardError("Invalid block-index length")
    header_reader = Reader(r.take(header_size))
    header = header_reader.msgpack()
    if header_reader.pos != header_size or not isinstance(header, dict):
        raise CardError("Invalid block index")
    entries = header.get("lstInfo")
    if not isinstance(entries, list) or not 1 <= len(entries) <= 128:
        raise CardError("Invalid character block list")
    payload_size = r.number("<q")
    if not 0 <= payload_size <= len(r.data) - r.pos: raise CardError("Truncated character payload")
    payload_start = r.pos
    blocks, names, spans = [], set(), []
    for item in entries:
        if not isinstance(item, dict): raise CardError("Invalid character block")
        name, block_version = item.get("name"), item.get("version")
        offset, size = item.get("pos"), item.get("size")
        if not isinstance(name, str) or not 0 < len(name) <= 256 or name in names:
            raise CardError("Invalid or duplicate character block name")
        if not isinstance(block_version, str) or len(block_version) > 128:
            raise CardError("Invalid character block version")
        if type(offset) is not int or type(size) is not int or min(offset, size) < 0 or offset + size > payload_size:
            raise CardError("Character block outside payload")
        if size and any(offset < b and a < offset + size for a, b in spans):
            raise CardError("Overlapping character blocks")
        names.add(name)
        if size: spans.append((offset, offset + size))
        block = r.data[payload_start + offset:payload_start + offset + size]
        blocks.append({"name": name, "version": block_version, "offset": offset,
                       "size": size, "sha256": hashlib.sha256(block).hexdigest()})
    return {"path": str(path), "sha256": hashlib.sha256(data).hexdigest(), "size": len(data),
            "family": MARKERS[marker], "product": product, "marker": marker, "version": version,
            "png_bytes": end, "embedded_preview_bytes": preview_size, "payload_bytes": payload_size,
            "trailing_bytes": len(r.data) - payload_start - payload_size, "blocks": blocks,
            "geometry_imported": False, "status": "inventory_only",
            "limitation": "Requires installed-game assets and compatible character assembly/export; plugin blocks remain opaque."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cards", type=Path, nargs="+")
    args = parser.parse_args()
    reports = []
    for card in args.cards:
        try: reports.append(inventory(card))
        except (OSError, ValueError, struct.error) as error:
            reports.append({"path": str(card), "error": str(error)})
    print(json.dumps(reports, ensure_ascii=True, indent=2))
    return int(any("error" in report for report in reports))


if __name__ == "__main__": raise SystemExit(main())
