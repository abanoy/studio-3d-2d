"""Read one bounded MDL49 appearance table without extracting or launching tools.

The ordinary converter remains authoritative for geometry/material correspondence.
Legacy LZMA .bin appearance inspection is intentionally unavailable in this draft.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zlib

from asset_audit import gma_index
from source_archive import resource_path
from source_content import vpk_index, vpk_read
from source_mdl_choices import catalogue

MAX_INPUT = 512 * 1024 * 1024
MAX_MDL = 16 * 1024 * 1024
MAX_RESULT = 256 * 1024
MAX_GMA_INDEX = 4 * 1024 * 1024


class _IndexWindow:
    """Cap hostile GMA strings/index reads before the shared inventory parser."""
    def __init__(self, stream, size):
        self.stream = stream
        self.limit = min(size, MAX_GMA_INDEX)

    def tell(self):
        return self.stream.tell()

    def read(self, count):
        if count < 0 or self.tell() + count > self.limit:
            raise ValueError("GMA appearance index exceeds4MiB or the admitted input")
        return self.stream.read(count)


def identity(path):
    """Bind bytes and nanosecond timestamps; never trust a size-only input check."""
    path = Path(path)
    before = path.stat()
    if not path.is_file() or before.st_size > MAX_INPUT:
        raise ValueError("Appearance input must be a file no larger than512MiB")
    sha, count = hashlib.sha256(), 0
    with path.open("rb") as stream:
        while True:
            block = stream.read(min(1024 * 1024, before.st_size + 1 - count))
            if not block:
                break
            count += len(block)
            if count > before.st_size:
                raise ValueError("Appearance input grew beyond its admitted size")
            sha.update(block)
    after = path.stat()
    if count != before.st_size or (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError("Appearance input changed while hashing")
    return {"sha256": sha.hexdigest(), "bytes": after.st_size, "mtime_ns": after.st_mtime_ns}


def _selected(rows, member, path_key):
    wanted = resource_path(member)
    if not wanted.lower().endswith(".mdl"):
        raise ValueError("Choose one MDL member for appearance inspection")
    seen, selected = set(), None
    for row in rows:
        name = resource_path(row[path_key])
        if "\ufffd" in name:
            raise ValueError("Archive member names must decode without replacement")
        key = name.casefold()
        if key in seen:
            raise ValueError("Duplicate case-insensitive archive path")
        seen.add(key)
        if name == wanted:
            selected = row
    if selected is None:
        raise ValueError("Selected MDL is absent from the archive index")
    return selected, wanted


def inspect_choices(source, member=""):
    """Return metadata plus independently checked native checksum, with no writes.

    VPK original checksum covers the directory file; selected MDL checksum also
    binds segmented payload. Every file actually read is checked before/after.
    """
    source = Path(source).resolve(strict=True)
    originals = {source: identity(source)}
    try:
        extension = source.suffix.lower()
        if extension == ".mdl":
            if member not in ("", source.name):
                raise ValueError("Loose MDL selection must match its filename")
            if originals[source]["bytes"] > MAX_MDL:
                raise ValueError("Selected MDL exceeds16MiB")
            with source.open("rb") as stream:
                raw = stream.read(MAX_MDL + 1)
            selected_member = source.name
        elif extension == ".gma":
            with source.open("rb") as stream:
                index = gma_index(_IndexWindow(stream, originals[source]["bytes"]), originals[source]["bytes"])
                entry, selected_member = _selected(index["entries"], member, "name")
                if not 0 < entry["size"] <= MAX_MDL:
                    raise ValueError("Selected MDL must be no larger than16MiB")
                stream.seek(index["payload_start"] + entry["relative_offset"])
                raw = stream.read(entry["size"])
                if len(raw) != entry["size"] or zlib.crc32(raw) & 0xFFFFFFFF != entry["crc32"]:
                    raise ValueError("Selected GMA MDL length or CRC differs")
        elif extension == ".vpk":
            entry, selected_member = _selected(vpk_index(source), member, "path")
            if not 0 < entry["bytes"] <= MAX_MDL:
                raise ValueError("Selected MDL must be no larger than16MiB")
            if entry["length"] and entry["archive"] != 0x7FFF:
                segment = source.with_name(source.name.removesuffix("_dir.vpk") + f'_{entry["archive"]:03}.vpk')
                originals[segment] = identity(segment)
            raw = vpk_read(source, entry)
        else:
            raise ValueError("Static appearance inspection currently supports loose MDL, GMA or VPK; default preparation is still available")
        if not 0 < len(raw) <= MAX_MDL:
            raise ValueError("Selected MDL is empty or exceeds16MiB")
        result = catalogue(raw, originals[source]["sha256"], selected_member)
        if len(json.dumps(result, ensure_ascii=True, indent=2).encode("utf-8")) > MAX_RESULT:
            raise ValueError("Appearance catalogue exceeds256KiB")
        return result
    finally:
        for path, before in originals.items():
            if identity(path) != before:
                raise ValueError("Appearance input changed during metadata inspection: " + str(path))
