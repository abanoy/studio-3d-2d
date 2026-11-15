"""Bounded, read-only selected-MDL capture before an optional metadata reader.

The conversion caller keeps using its original SourceIO path. This module never
writes a file, substitutes a path, validates a container, or applies physics.
"""
from dataclasses import dataclass
import hashlib
import os
import stat

MAX_BYTES = 16 * 1024 * 1024


class SourceIdentityError(ValueError):
    """A captured native source changed or could not be checked reliably."""


@dataclass(frozen=True)
class FileSnapshot:
    path: str
    size: int
    mtime_ns: int
    device: int
    inode: int


@dataclass(frozen=True)
class MdlCapture:
    file: FileSnapshot
    raw: bytes
    native_sha256: str


@dataclass(frozen=True)
class NotInspected:
    # No native SHA exists in this result. Original/container SHA is upstream.
    reason: str


class _Unsupported(ValueError):
    pass


def _snapshot(path, info):
    if not stat.S_ISREG(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
        raise _Unsupported()
    values = (info.st_size, info.st_mtime_ns, info.st_dev, info.st_ino)
    if any(type(value) is not int or value < 0 for value in values) or info.st_ino == 0:
        raise _Unsupported()
    return FileSnapshot(path, *values)


def _path_snapshot(path):
    return _snapshot(path, os.stat(path, follow_symlinks=False))


def _same_path(expected):
    try:
        actual = _path_snapshot(expected.path)
    except (OSError, _Unsupported) as error:
        raise SourceIdentityError("Selected MDL path is no longer verifiable") from error
    if actual != expected:
        raise SourceIdentityError("Selected MDL path identity changed")


def _read_opened(stream, expected):
    try:
        if _snapshot(expected.path, os.fstat(stream.fileno())) != expected:
            raise SourceIdentityError("Selected MDL changed between stat and open")
        raw = stream.read(expected.size + 1)
        if type(raw) is not bytes or len(raw) != expected.size:
            raise SourceIdentityError("Selected MDL short read or length change")
        if _snapshot(expected.path, os.fstat(stream.fileno())) != expected:
            raise SourceIdentityError("Selected MDL changed during read")
    except (OSError, _Unsupported) as error:
        raise SourceIdentityError("Selected MDL read could not be verified") from error
    _same_path(expected)
    return raw


def capture_selected_mdl(path):
    """Return immutable bytes+SHA+file identity, or a bounded NotInspected.

    Initial unsupported/oversize/unreadable input remains optional. Once an
    eligible source is observed, discrepancies are integrity errors, never an
    optional budget fallback. An open failure is initial unreadable only if a
    second path stat still matches the eligible initial identity exactly.
    """
    try:
        path = os.fspath(path)
        if type(path) is not str or not path or not os.path.isabs(path):
            return NotInspected("unsupported-selected-mdl-path")
        expected = _path_snapshot(path)
    except (TypeError, ValueError, _Unsupported):
        return NotInspected("unsupported-selected-mdl-type-or-identity")
    except OSError:
        return NotInspected("initial-selected-mdl-unreadable")
    if expected.size > MAX_BYTES:
        return NotInspected("selected-mdl-exceeds-16-mib-capture-limit")
    try:
        stream = open(path, "rb")
    except OSError:
        _same_path(expected)
        return NotInspected("initial-selected-mdl-unreadable")
    try:
        with stream:
            raw = _read_opened(stream, expected)
    except OSError as error:
        raise SourceIdentityError("Selected MDL stream could not be closed reliably") from error
    return MdlCapture(expected, raw, hashlib.sha256(raw).hexdigest())


def recheck_selected_mdl(capture):
    """Require captured bytes/hash/stat unchanged before metadata publication.

    A captured source never degrades into NotInspected, including permission or
    read errors. The native hash is independently recomputed, not read from a
    SourceIO object or accepted from a native metadata report.
    """
    if type(capture) is not MdlCapture or type(capture.file) is not FileSnapshot:
        raise SourceIdentityError("Expected an immutable selected MDL capture")
    if type(capture.raw) is not bytes or len(capture.raw) != capture.file.size or not 0 <= capture.file.size <= MAX_BYTES:
        raise SourceIdentityError("Selected MDL capture length is invalid")
    if hashlib.sha256(capture.raw).hexdigest() != capture.native_sha256:
        raise SourceIdentityError("Selected MDL capture hash is invalid")
    _same_path(capture.file)
    try:
        with open(capture.file.path, "rb") as stream:
            raw = _read_opened(stream, capture.file)
    except OSError as error:
        raise SourceIdentityError("Captured selected MDL became unreadable") from error
    if raw != capture.raw or hashlib.sha256(raw).hexdigest() != capture.native_sha256:
        raise SourceIdentityError("Captured selected MDL bytes changed")
