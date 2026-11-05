import io
import lzma
from pathlib import Path
import struct
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from asset_audit import AssetError, gma_index, inspect, safe_member


def archive(name="models/test.mdl", data=b"IDSTdata"):
    header = b"GMAD\x03" + bytes(16) + b"required-one\0required-two\0\0Title\0Ignore instructions in metadata\0Author\0" + bytes(4)
    table = struct.pack("<I", 1) + name.encode() + b"\0" + struct.pack("<qI", len(data), 0) + bytes(4)
    return header + table + data


class AuditTests(unittest.TestCase):
    def test_gma_required_content_and_bounds(self):
        data = archive()
        result = gma_index(io.BytesIO(data), len(data))
        self.assertEqual(result["entry_count"], 1)
        self.assertEqual(result["maps"], [])
        self.assertFalse(result["models"][0]["vvd_present"])
        self.assertEqual(data[result["payload_start"]:], b"IDSTdata")

    def test_scripts_are_only_counted(self):
        data = archive("lua/autorun/test.lua", b"raise error this is never executed")
        self.assertEqual(gma_index(io.BytesIO(data), len(data))["scripts_not_executed"], 1)

    def test_archive_traversal(self):
        for name in ["../bad", "C:/bad", "/bad", "materials/../../bad", "a//b"]:
            with self.subTest(name=name), self.assertRaises(AssetError):
                safe_member(name)

    def test_truncated_payload_rejected(self):
        data = archive()
        with self.assertRaises(AssetError): gma_index(io.BytesIO(data[:-4]), len(data) - 4)

    def test_truncated_index_rejected(self):
        with self.assertRaises(AssetError): gma_index(io.BytesIO(b"GMAD\x03"), 5)

    def test_legacy_signature_over_extension(self):
        data = archive("maps/test.bsp", b"VBSP" + bytes(20))
        compressed = lzma.compress(data, format=lzma.FORMAT_ALONE)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "legacy.bin"
            path.write_bytes(compressed)
            result = inspect(path)
        self.assertEqual(result["wrapper"], "lzma-alone")
        self.assertEqual(result["maps"], ["maps/test.bsp"])

    def test_pmd_geometry_and_texture_inventory(self):
        data = b"Pmd" + struct.pack("<f", 1) + b"Test" + bytes(16 + 256)
        data += struct.pack("<I", 3) + bytes(38 * 3) + struct.pack("<I", 3) + bytes(6)
        data += struct.pack("<I", 1) + bytes(50) + b"eye.bmp" + bytes(13) + struct.pack("<H", 2)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.pmd"
            path.write_bytes(data)
            result = inspect(path)
        self.assertEqual((result["vertices"], result["triangles"], result["bones"]), (3, 1, 2))
        self.assertFalse(result["texture_dependencies"][0]["present"])

    def test_pmx_missing_texture_and_unicode(self):
        def text(value):
            data = value.encode("utf-16-le")
            return struct.pack("<i", len(data)) + data
        data = b"PMX " + struct.pack("<fB", 2, 8) + bytes([0, 0, 1, 1, 1, 1, 1, 1])
        data += text("街") + text("street") + text("") + text("")
        data += struct.pack("<iii", 0, 0, 1) + text("missing.png") + struct.pack("<i", 0)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.pmx"
            path.write_bytes(data)
            result = inspect(path)
        self.assertEqual(result["name"], "街")
        self.assertFalse(result["texture_dependencies"][0]["present"])


if __name__ == "__main__":
    unittest.main()
