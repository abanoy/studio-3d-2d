"""Bounded Source resource staging; GMod Lua and executable add-on files are never extracted."""
from pathlib import Path
import hashlib
import lzma
import struct
import zlib

from asset_audit import AssetError, gma_index, safe_member, digest

MAX_ARCHIVE = 512 * 1024 * 1024
RESOURCE_EXTENSIONS = {".mdl", ".vvd", ".vtx", ".phy", ".ani", ".vmt", ".vtf", ".bsp"}
WINDOWS_DEVICES = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}


def resource_path(name):
    name = safe_member(name)
    for part in name.split("/"):
        if part.rstrip(" .") != part or part.split(".")[0].upper() in WINDOWS_DEVICES or any(ord(c) < 32 for c in part):
            raise AssetError("Unsafe Windows resource name")
    return name


def unpack_legacy(source, target):
    decoder = lzma.LZMADecompressor(format=lzma.FORMAT_ALONE, memlimit=128 * 1024 * 1024)
    written = 0
    with Path(source).open("rb") as inp, Path(target).open("xb") as out:
        while not decoder.eof:
            block = inp.read(65536) if decoder.needs_input else b""
            if decoder.needs_input and not block:
                raise AssetError("Incomplete legacy LZMA stream")
            data = decoder.decompress(block, max_length=min(1024 * 1024, MAX_ARCHIVE - written + 1))
            written += len(data)
            if written > MAX_ARCHIVE:
                raise AssetError("Legacy archive exceeds 512 MiB")
            out.write(data)
        trailer = decoder.unused_data + inp.read(9)
        # The owner's Steam legacy sample has an eight-byte length/magic footer.
        # Accept only that measured footer (or no footer), never arbitrary trailing data.
        if trailer and trailer != struct.pack("<II", written, 0xBEEFCACE):
            raise AssetError("Unexpected trailing data after legacy stream")
    return written


def stage_archive(source, output):
    source, output = Path(source).resolve(strict=True), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    raw = source
    with source.open("rb") as f:
        signature = f.read(4)
    if signature != b"GMAD":
        raw = output / "container.gma"
        unpack_legacy(source, raw)
    if raw.stat().st_size > MAX_ARCHIVE:
        raise AssetError("GMA exceeds 512 MiB")
    native = output / "native"
    native.mkdir()
    rows, names = [], set()
    with raw.open("rb") as stream:
        index = gma_index(stream, raw.stat().st_size)
        for entry in index["entries"]:
            name = resource_path(entry["name"])
            key = name.casefold()
            if key in names:
                raise AssetError("Duplicate case-insensitive archive path")
            names.add(key)
            wanted = Path(name).suffix.lower() in RESOURCE_EXTENSIONS and name.split("/")[0].lower() in {"models", "materials", "maps"}
            target = native / name
            assert target.resolve().is_relative_to(native)
            crc, left = 0, entry["size"]
            stream.seek(index["payload_start"] + entry["relative_offset"])
            if wanted:
                target.parent.mkdir(parents=True, exist_ok=True)
                sink = target.open("xb")
            else:
                sink = None
            sha = hashlib.sha256()
            try:
                while left:
                    block = stream.read(min(left, 1024 * 1024))
                    if not block:
                        raise AssetError("Truncated archive payload")
                    left -= len(block)
                    crc = zlib.crc32(block, crc)
                    sha.update(block)
                    if sink:
                        sink.write(block)
            finally:
                if sink:
                    sink.close()
            if crc & 0xFFFFFFFF != entry["crc32"]:
                raise AssetError("GMA file CRC differs: " + name)
            if wanted:
                rows.append({"path": name, "bytes": entry["size"], "sha256": sha.hexdigest()})
    return {"root": str(native), "source": str(source), "source_sha256": digest(source),
            "entries_verified": len(index["entries"]), "resources": rows,
            "models": [r["path"] for r in rows if r["path"].lower().endswith(".mdl")],
            "maps": [r["path"] for r in rows if r["path"].lower().endswith(".bsp")],
            "skipped_files": len(index["entries"]) - len(rows)}
