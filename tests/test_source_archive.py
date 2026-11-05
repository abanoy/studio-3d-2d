import io
import lzma
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from source_archive import stage_archive, unpack_legacy, resource_path, AssetError


def archive(entries):
    header = b"GMAD\3" + bytes(16) + b"\0Test\0Description\0Author\0" + bytes(4)
    index, payload = b"", b""
    for n, (name, data) in enumerate(entries, 1):
        index += struct.pack("<I", n) + name.encode() + b"\0" + struct.pack("<qI", len(data), zlib.crc32(data))
        payload += data
    return header + index + bytes(4) + payload


class SourceArchiveTests(unittest.TestCase):
    def stage(self, payload):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        source = root / "input.gma"
        source.write_bytes(payload)
        return root, source, root / "prepared"

    def test_resources_only_crc_and_original_bytes(self):
        data = archive([("models/test.mdl", b"IDST"), ("materials/test.vmt", b"shader {}"),
                        ("lua/autorun/test.lua", b"DO NOT EXECUTE"), ("models/test.exe", b"MZ")])
        root, source, output = self.stage(data)
        report = stage_archive(source, output)
        self.assertEqual(report["entries_verified"], 4)
        self.assertEqual(report["skipped_files"], 2)
        self.assertEqual(report["models"], ["models/test.mdl"])
        self.assertFalse((output / "native/lua").exists())
        self.assertFalse((output / "native/models/test.exe").exists())
        self.assertEqual(source.read_bytes(), data)

    def test_crc_failure_in_skipped_lua_is_detected(self):
        data = archive([("lua/test.lua", b"abc")])[:-1] + b"x"
        _, source, output = self.stage(data)
        with self.assertRaisesRegex(AssetError, "CRC"):
            stage_archive(source, output)

    def test_case_duplicate_rejected(self):
        _, source, output = self.stage(archive([("models/Test.mdl", b"a"), ("models/test.mdl", b"b")]))
        with self.assertRaisesRegex(AssetError, "Duplicate"):
            stage_archive(source, output)

    def test_windows_devices_and_traversal_rejected(self):
        for name in ["../escape.mdl", "models/CON.mdl", "models/nul/a.mdl", "C:/x.mdl", "models/a. /b.mdl", "a//b", "a/../b", "maps/LPT1.bsp"]:
            with self.subTest(name=name), self.assertRaises(AssetError): resource_path(name)

    def test_existing_output_preserved(self):
        _, source, output = self.stage(archive([("maps/test.bsp", b"VBSP")]))
        output.mkdir()
        marker = output / "keep.txt"; marker.write_text("keep")
        with self.assertRaises(FileExistsError): stage_archive(source, output)
        self.assertEqual(marker.read_text(), "keep")

    def test_legacy_stream_and_measured_steam_footer(self):
        data = archive([("maps/test.bsp", b"VBSP")])
        for footer in (b"", struct.pack("<II", len(data), 0xBEEFCACE)):
            with self.subTest(footer=footer):
                _, source, output = self.stage(lzma.compress(data, format=lzma.FORMAT_ALONE) + footer)
                self.assertEqual(stage_archive(source, output)["maps"], ["maps/test.bsp"])

    def test_unrecognized_footer_and_short_stream_rejected(self):
        compressed = lzma.compress(archive([]), format=lzma.FORMAT_ALONE)
        for payload in (compressed + b"arbitrary", compressed[:-8], compressed + struct.pack("<II", 123, 0xBEEFCACE)):
            _, source, output = self.stage(payload)
            with self.assertRaises((AssetError, lzma.LZMAError)): stage_archive(source, output)

    def test_decompression_output_bound(self):
        _, source, output = self.stage(lzma.compress(bytes(10000), format=lzma.FORMAT_ALONE))
        with patch("source_archive.MAX_ARCHIVE", 100), self.assertRaisesRegex(AssetError, "exceeds"):
            unpack_legacy(source, output)


if __name__ == "__main__": unittest.main()
