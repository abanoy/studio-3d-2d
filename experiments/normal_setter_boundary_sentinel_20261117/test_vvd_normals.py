"""Synthetic-only VVD normal/LOD0 mapping tests; no native files or subprocesses."""
import hashlib
import math
import struct
import unittest
from pathlib import Path

from vvd_normals import decode_lod0_normals


def fixture(normals=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
            fixups=None, checksum=0x12345678, tangents=False, lod_count=1, other_counts=()):
    count = len(normals)
    fixups = list(fixups or [])
    table = b"".join(struct.pack("<3I", *row) for row in fixups)
    vertex_offset = 64 + len(table)
    vertices = bytearray(count * 48)
    for index, normal in enumerate(normals):
        # Distinct synthetic adjacent channels prove offset/stride selection.
        struct.pack_into("<3f", vertices, index * 48 + 16, 200.0 + index, 300.0, 400.0)
        struct.pack_into("<3f", vertices, index * 48 + 28, *normal)
        struct.pack_into("<2f", vertices, index * 48 + 40, 10.0 + index, 20.0)
    counts = (count, *other_counts)
    counts += (0,) * (8 - len(counts))
    tangent_offset = vertex_offset + len(vertices) if tangents else 0
    header = struct.pack("<4s15I", b"IDSV", 4, checksum, lod_count, *counts,
                         len(fixups), 64 if fixups else 0, vertex_offset, tangent_offset)
    return header + table + vertices + (b"\x00" * (count * 16) if tangents else b"")


def change_word(raw, offset, value):
    result = bytearray(raw)
    struct.pack_into("<I", result, offset, value)
    return bytes(result)


class ReaderTests(unittest.TestCase):
    def test_stride_and_offset_do_not_read_adjacent_channels(self):
        row = decode_lod0_normals(fixture())
        self.assertEqual(row["normals"], ((1, 0, 0), (0, 1, 0), (0, 0, 1)))
        self.assertEqual(row["raw_vertex_indices"], (0, 1, 2))
        self.assertEqual((row["vertex_stride"], row["normal_offset"]), (48, 28))

    def test_fixup_permutation_is_preserved(self):
        row = decode_lod0_normals(fixture(fixups=[(0, 2, 1), (0, 0, 2)]))
        self.assertEqual(row["raw_vertex_indices"], (2, 0, 1))
        self.assertEqual(row["normals"], ((0, 0, 1), (1, 0, 0), (0, 1, 0)))

    def test_higher_lod_tag_is_included_in_lod0(self):
        row = decode_lod0_normals(fixture(fixups=[(7, 0, 1), (3, 1, 2)]))
        self.assertEqual(row["raw_vertex_indices"], (0, 1, 2))

    def test_duplicate_source_ids_are_not_silently_repaired(self):
        row = decode_lod0_normals(fixture(fixups=[(0, 0, 1), (0, 0, 2)]))
        self.assertEqual(row["raw_vertex_indices"], (0, 0, 1))
        self.assertEqual(row["normals"][0], row["normals"][1])

    def test_fixup_output_must_fill_declared_lod0(self):
        for fixups in ([(0, 0, 2)], [(0, 0, 3), (0, 0, 1)]):
            with self.subTest(fixups=fixups), self.assertRaises(ValueError):
                decode_lod0_normals(fixture(fixups=fixups))

    def test_fixup_source_and_tag_ranges_are_bounded(self):
        for fixups in ([(0, 2, 2)], [(8, 0, 3)], [(0, 4, 0)]):
            with self.subTest(fixups=fixups), self.assertRaises(ValueError):
                decode_lod0_normals(fixture(fixups=fixups))

    def test_header_magic_version_and_type(self):
        for raw in (None, "IDSV", [], b"", b"IDSV", b"X" * 64,
                    change_word(fixture(), 4, 3)):
            with self.subTest(kind=type(raw).__name__), self.assertRaises(ValueError):
                decode_lod0_normals(raw)

    def test_checksum_zero_and_explicit_mismatch(self):
        self.assertEqual(decode_lod0_normals(fixture(checksum=0), 0)["checksum"], 0)
        for expected in (0, -1, 2 ** 32, True, "305419896"):
            with self.subTest(expected=expected), self.assertRaises(ValueError):
                decode_lod0_normals(fixture(), expected)

    def test_header_count_budgets_before_allocating(self):
        for offset, value in ((12, 0), (12, 9), (16, 0), (16, 200001), (48, 200001)):
            with self.subTest(offset=offset, value=value), self.assertRaises(ValueError):
                decode_lod0_normals(change_word(fixture(), offset, value))

    def test_truncated_vertex_and_fixup_tables(self):
        for raw in (fixture()[:-1], change_word(fixture(), 56, 10 ** 6),
                    change_word(fixture(fixups=[(0, 0, 3)]), 52, 10 ** 6)):
            with self.subTest(length=len(raw)), self.assertRaises(ValueError):
                decode_lod0_normals(raw)

    def test_overlapping_tables_are_refused(self):
        raw = fixture(fixups=[(0, 0, 3)])
        with self.assertRaises(ValueError):
            decode_lod0_normals(change_word(raw, 52, 80))
        with self.assertRaises(ValueError):
            decode_lod0_normals(change_word(fixture(tangents=True), 60, 64))

    def test_tangent_table_declaration_is_bounded_but_not_decoded(self):
        row = decode_lod0_normals(fixture(tangents=True))
        self.assertEqual(row["normals"][1], (0, 1, 0))
        with self.assertRaises(ValueError):
            decode_lod0_normals(fixture(tangents=True)[:-1])

    def test_zero_and_nonunit_values_are_preserved(self):
        row = decode_lod0_normals(fixture(normals=((0, 0, 0), (2, 0, 0))))
        self.assertEqual(row["normals"], ((0, 0, 0), (2, 0, 0)))

    def test_negative_zero_words_survive(self):
        row = decode_lod0_normals(fixture(normals=((-0.0, 0, 1),)))
        self.assertEqual(struct.pack("<f", row["normals"][0][0]), b"\x00\x00\x00\x80")

    def test_nonfinite_normal_values_refused(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value), self.assertRaises(ValueError):
                decode_lod0_normals(fixture(normals=((value, 0, 1),)))

    def test_input_snapshot_is_immutable(self):
        raw = bytearray(fixture())
        row = decode_lod0_normals(raw)
        raw[:] = b"\x00" * len(raw)
        self.assertEqual(row["normals"][0], (1, 0, 0))
        with self.assertRaises(TypeError):
            row["normals"][0][0] = 2

    def test_unused_lod_slots_do_not_change_lod0(self):
        raw = change_word(fixture(), 44, 0xFFFFFFFF)
        self.assertEqual(decode_lod0_normals(raw)["raw_vertex_indices"], (0, 1, 2))
        self.assertEqual(decode_lod0_normals(fixture(lod_count=2, other_counts=(2,)))["vertex_count"], 3)


if __name__ == "__main__":
    result = unittest.main(verbosity=1, exit=False).result
    print({"synthetic_methods": result.testsRun, "passed": result.wasSuccessful(),
           "failures": len(result.failures), "errors": len(result.errors),
           "native_files_read": False, "engines_CIM_Git_subprocesses": False})
    raise SystemExit(0 if result.wasSuccessful() else 1)
