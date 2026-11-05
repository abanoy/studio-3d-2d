"""Authored card containers; no game assets or third-party serialization library."""
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from illusion_cards import CardError, Reader, inventory


def pack(value):
    if isinstance(value, str):
        data = value.encode()
        return bytes([0xa0 + len(data)]) + data
    if isinstance(value, int): return b"\xd3" + struct.pack(">q", value)
    if isinstance(value, list): return bytes([0x90 + len(value)]) + b"".join(map(pack, value))
    return bytes([0x80 + len(value)]) + b"".join(pack(k) + pack(v) for k, v in value.items())


def string(value):
    data = value.encode()
    return bytes([len(data)]) + data


def chunk(kind, payload):
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xffffffff)


PNG = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(b"\0\0\0\0\0")) + chunk(b"IEND", b"")


def card(marker="【KoiKatuChara】", entries=None, payload=b"abc", declared=None):
    if entries is None: entries = [{"name": "Custom", "version": "0.0.0", "pos": 0, "size": len(payload)}]
    header = pack({"lstInfo": entries})
    prefix = struct.pack("<i", 100) + string(marker) + string("0.0.0")
    prefix += struct.pack("<i", 0) + string("private-user") + string("private-data") if marker == "【AIS_Chara】" else struct.pack("<i", 0)
    return PNG + prefix + struct.pack("<i", len(header)) + header + struct.pack("<q", len(payload) if declared is None else declared) + payload


class Cards(unittest.TestCase):
    def inspect(self, data):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "card.png"
            path.write_bytes(data)
            result = inventory(path)
            self.assertEqual(path.read_bytes(), data)
            return result

    def test_kk_kks_ai_and_opaque_payload(self):
        for marker, family in [("【KoiKatuChara】", "koikatsu"), ("【KoiKatuCharaSun】", "koikatsu-sunshine"), ("【AIS_Chara】", "ai-shoujo")]:
            with self.subTest(marker=marker):
                result = self.inspect(card(marker, payload=b"not executable or decoded"))
                self.assertEqual(result["family"], family)
                self.assertFalse(result["geometry_imported"])
                self.assertNotIn("private-user", str(result))
                self.assertEqual(result["blocks"][0]["size"], len(b"not executable or decoded"))

    def test_ordinary_png_and_unknown_marker(self):
        for data in (PNG, card("Unknown")):
            with self.assertRaises(CardError): self.inspect(data)

    def test_png_crc(self):
        damaged = bytearray(card())
        damaged[29] ^= 1
        with self.assertRaisesRegex(CardError, "CRC"): self.inspect(damaged)

    def test_truncated_and_excessive_payload(self):
        for data in (card()[:-1], card(declared=100000), card(declared=-1)):
            with self.assertRaises(CardError): self.inspect(data)

    def test_block_bounds(self):
        for offset, size in [(-1, 1), (0, -1), (2, 2)]:
            with self.assertRaises(CardError):
                self.inspect(card(entries=[{"name": "X", "version": "0", "pos": offset, "size": size}]))

    def test_duplicate_and_overlapping_blocks(self):
        first = {"name": "X", "version": "0", "pos": 0, "size": 2}
        for second in ({**first, "pos": 2, "size": 1}, {**first, "name": "Y", "pos": 1}):
            with self.assertRaises(CardError): self.inspect(card(entries=[first, second]))

    def test_reject_complex_or_executable_types(self):
        for data in (b"\x91" * 20 + b"\0", b"\xc7\0\0", b"\xdd\xff\xff\xff\xff"):
            with self.assertRaises(CardError): Reader(data).msgpack()

    def test_duplicate_map_key(self):
        with self.assertRaises(CardError): Reader(b"\x82\xa1x\0\xa1x\0").msgpack()

    def test_dotnet_length_bound(self):
        for data in (b"\x80" * 5, b"\xff\x7f"):
            with self.assertRaises(CardError): Reader(data).dotnet_string()


if __name__ == "__main__": unittest.main()
