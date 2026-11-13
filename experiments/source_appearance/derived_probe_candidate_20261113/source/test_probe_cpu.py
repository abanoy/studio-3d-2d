"""Synthetic CPU safety/independent-reference controls. Never starts an engine."""
import copy
import hashlib
import json
import math
from pathlib import Path
import struct
import time
import unittest
from unittest.mock import patch
import zlib

import glb_reference as R
import probe_driver as D


def glb_document(data, binary):
    text = json.dumps(data).encode()
    text += b" "*((-len(text)) % 4)
    padded = binary+b"\0"*((-len(binary)) % 4)
    return struct.pack("<III", 0x46546c67, 2, 28+len(text)+len(padded))+struct.pack("<II", len(text), 0x4e4f534a)+text+struct.pack("<II", len(padded), 0x004e4942)+padded


def fixture():
    binary = bytearray()
    views, accessors = [], []
    def add(values, fmt, kind, component):
        while len(binary) % 4:
            binary.append(0)
        start = len(binary)
        for value in values:
            binary.extend(struct.pack("<"+fmt*len(value), *value))
        views.append({"buffer": 0, "byteOffset": start, "byteLength": len(binary)-start})
        accessors.append({"bufferView": len(views)-1, "componentType": component, "count": len(values), "type": kind})
        return len(accessors)-1
    pos = add([(1., 0., 0.), (0., 1., 0.), (0., 0., 0.)], "f", "VEC3", 5126)
    delta = add([(0., 1., 0.)]*3, "f", "VEC3", 5126)
    joints = add([(0, 0, 0, 0)]*3, "H", "VEC4", 5123)
    weights = add([(1., 0., 0., 0.)]*3, "f", "VEC4", 5126)
    indices = add([(0,), (1,), (2,)], "H", "SCALAR", 5123)
    binds = add([R.IDENTITY], "f", "MAT4", 5126)
    data = {"asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": [0]}],
            "nodes": [{"translation": [2, 3, 4], "children": [1, 2]},
                      {"name": "joint", "translation": [1, 0, 0]},
                      {"name": "tools.dmx", "translation": [7, 0, 0], "mesh": 0, "skin": 0}],
            "skins": [{"joints": [1], "inverseBindMatrices": binds}],
            "meshes": [{"extras": {"targetNames": ["Tools"]}, "primitives": [{"attributes": {"POSITION": pos, "JOINTS_0": joints, "WEIGHTS_0": weights}, "indices": indices, "material": 0, "targets": [{"POSITION": delta}]}]}],
            "materials": [{"name": "fixture"}], "buffers": [{"byteLength": len(binary)}],
            "bufferViews": views, "accessors": accessors}
    return data, bytes(binary)


def png(width, height, packed):
    def chunk(kind, data):
        return struct.pack(">I", len(data))+kind+data+struct.pack(">I", zlib.crc32(kind+data) & 0xffffffff)
    return b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))+chunk(b"IDAT", zlib.compress(packed))+chunk(b"IEND", b"")


def sparse_fixture(indices=(0, 1)):
    data, raw = fixture()
    binary = bytearray(raw)
    index_view = len(data["bufferViews"])
    data["bufferViews"].append({"buffer": 0, "byteOffset": len(binary), "byteLength": 2})
    binary.extend(bytes(indices))
    while len(binary) % 4:binary.append(0)
    value_view = len(data["bufferViews"])
    data["bufferViews"].append({"buffer": 0, "byteOffset": len(binary), "byteLength": 24})
    binary.extend(struct.pack("<6f", 1, 0, 0, 0, 1, 0))
    data["accessors"][0].pop("bufferView")
    data["accessors"][0]["sparse"] = {"count": 2, "indices": {"bufferView": index_view, "componentType": 5121},
                                        "values": {"bufferView": value_view}}
    data["buffers"][0]["byteLength"] = len(binary)
    return data, bytes(binary)


def binding_fixture():
    data, raw = fixture()
    data["nodes"][0]["name"] = "rootJoint"
    data["skins"][0]["joints"] = [1, 0]  # Explicit different table order.
    data["accessors"][-1]["count"] = 2
    data["bufferViews"][-1]["byteLength"] = 128
    raw += struct.pack("<16f", *R.IDENTITY)
    data["buffers"][0]["byteLength"] = len(raw)
    return data, raw, [{"name": "rootJoint", "parent": -1}, {"name": "joint", "parent": 0}]


class ReferenceControls(unittest.TestCase):
    def setUp(self):
        self.data, self.binary = fixture()

    def test_hand_computed_skin_morph_and_pose_order(self):
        g = R.GLB(glb_document(self.data, self.binary))
        p = g.positions()[0]["positions"][0]
        self.assertEqual(p, [4., 3., 4.])
        q = [0., 0., math.sqrt(.5), math.sqrt(.5)]
        p = g.positions(.5, 1, q)[0]["positions"][0]
        for actual, expected in zip(p, [2.5, 4., 4.]):
            self.assertAlmostEqual(actual, expected)

    def test_half_morph_is_linear_and_pose_does_not_mutate_base(self):
        g = R.GLB(glb_document(self.data, self.binary))
        a, b, c = (g.positions(w)[0]["positions"] for w in (0, .5, 1))
        for first, middle, last in zip(a, b, c):
            for x, y, z in zip(first, middle, last):
                self.assertAlmostEqual(y, (x+z)*.5)
        g.positions(1, 1, [0, 0, 1, 0])
        self.assertEqual(a, g.positions(0)[0]["positions"])

    def test_truncated_glb_refused(self):
        with self.assertRaises(ValueError):R.GLB(glb_document(self.data, self.binary)[:-1])

    def test_external_buffer_refused(self):
        self.data["buffers"][0]["uri"] = "other.bin"
        with self.assertRaises(ValueError):R.GLB(glb_document(self.data, self.binary))

    def test_required_extension_refused(self):
        self.data["extensionsRequired"] = ["unknown"]
        with self.assertRaises(ValueError):R.GLB(glb_document(self.data, self.binary))

    def test_cycle_refused(self):
        self.data["nodes"][1]["children"] = [0]
        with self.assertRaises(ValueError):R.GLB(glb_document(self.data, self.binary))

    def test_malformed_sparse_accessor_refused(self):
        self.data["accessors"][0]["sparse"] = {"count": 1}
        with self.assertRaises(ValueError):R.GLB(glb_document(self.data, self.binary)).positions()

    def test_sparse_implicit_zero_base_matches_dense(self):
        data, raw = sparse_fixture()
        dense = R.GLB(glb_document(self.data, self.binary)).positions(.5)
        sparse = R.GLB(glb_document(data, raw)).positions(.5)
        self.assertEqual(dense, sparse)

    def test_sparse_duplicate_indices_refused(self):
        data, raw = sparse_fixture((0, 0))
        with self.assertRaises(ValueError):R.GLB(glb_document(data, raw)).positions()

    def test_sparse_out_of_range_indices_refused(self):
        data, raw = sparse_fixture((0, 3))
        with self.assertRaises(ValueError):R.GLB(glb_document(data, raw)).positions()

    def test_sparse_truncated_values_refused(self):
        data, raw = sparse_fixture()
        data["bufferViews"][-1]["byteLength"] = 2
        with self.assertRaises(ValueError):R.GLB(glb_document(data, raw)).positions()

    def test_accessor_overrun_refused(self):
        self.data["accessors"][0]["count"] = 999999
        with self.assertRaises(ValueError):R.GLB(glb_document(self.data, self.binary)).positions()

    def test_nonfinite_position_refused(self):
        changed = bytearray(self.binary);struct.pack_into("<f", changed, 0, float("nan"))
        with self.assertRaises(ValueError):R.GLB(glb_document(self.data, changed)).positions()

    def test_native_readers_are_not_imported(self):
        import sys
        self.assertFalse(any(n == "bpy" or n.startswith("SourceIO") for n in sys.modules))

    def test_native_binding_table_is_joined_not_assumed_palette_order(self):
        data, raw, bones = binding_fixture()
        result = R.GLB(glb_document(data, raw)).native_bindings(bones)
        self.assertEqual([(r["native_index"], r["glb_palette_index"], r["source_node"]) for r in result], [(0, 1, 0), (1, 0, 1)])

    def test_native_binding_parent_mismatch_refused(self):
        data, raw, bones = binding_fixture();bones[1]["parent"] = -1
        with self.assertRaises(ValueError):R.GLB(glb_document(data, raw)).native_bindings(bones)

    def test_native_binding_duplicate_name_refused(self):
        data, raw, bones = binding_fixture();data["nodes"][0]["name"] = "joint"
        with self.assertRaises(ValueError):R.GLB(glb_document(data, raw)).native_bindings(bones)

    def test_crc_checked_png_independent_rgba(self):
        raw = png(1, 2, b"\0\x28\x28\x28\xff\x02\x50\x50\x50\0")
        result = R.png_rgba(raw)
        self.assertEqual(result["rgba8_sha256"], hashlib.sha256(bytes([40, 40, 40, 255, 120, 120, 120, 255])).hexdigest())
        self.assertEqual((result["width"], result["height"]), (1, 2))

    def test_png_crc_corruption_refused(self):
        changed = bytearray(png(1, 1, b"\0\0\0\0\xff"));changed[29] ^= 1
        with self.assertRaises(ValueError):R.png_rgba(changed)

    def test_png_excess_decoded_bytes_refused(self):
        with self.assertRaises(ValueError):R.png_rgba(png(1, 1, b"\0\0\0\0\xffEXCESS"))

    def test_png_trailing_payload_refused(self):
        with self.assertRaises(ValueError):R.png_rgba(png(1, 1, b"\0\0\0\0\xff")+b"extra")


class DriverControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = D.TASK / "cpu-fixtures" / str(time.time_ns())
        cls.folder.mkdir(parents=True, exist_ok=False)

    def test_output_sibling_escape_refused(self):
        with self.assertRaises(ValueError):D.owned(D.TASK.parent / (D.TASK.name+"-other") / "new")

    def test_output_parent_escape_refused(self):
        with self.assertRaises(ValueError):D.owned(D.TASK / ".." / "other")

    def test_refuses_task_root_as_file_destination(self):
        with self.assertRaises(ValueError):D.owned(D.TASK)

    def test_refuses_overwrite(self):
        path = self.folder / "no-overwrite.json"
        D.write_new(path, {"first": True})
        before = path.read_bytes()
        with self.assertRaises(FileExistsError):D.write_new(path, {"second": True})
        self.assertEqual(before, path.read_bytes())

    def test_stale_manifest_hash_refused_before_launch(self):
        path = self.folder / "stale.json";D.write_new(path, {})
        with patch.object(D.subprocess, "run", side_effect=AssertionError("must not launch")):
            with self.assertRaisesRegex(ValueError, "Manifest hash mismatch"):D.preflight(path, "0"*64)

    def test_changed_input_detected(self):
        path = self.folder / "identity.txt";path.write_bytes(b"first")
        identity = D.stamp(path);path.write_bytes(b"other")
        self.assertFalse(D.unchanged(identity))

    def test_timeout_preserves_partial_output_without_retry(self):
        output = self.folder / "timeout-case";output.mkdir()
        failure = D.subprocess.TimeoutExpired(["not-a-runtime"], 1, output=b"before timeout\n", stderr=b"partial stderr\n")
        with patch.object(D.subprocess, "run", side_effect=failure) as mocked:
            with self.assertRaises(D.subprocess.TimeoutExpired):D.captured_process(["not-a-runtime"], output, output, 1)
            self.assertEqual(mocked.call_count, 1)
        self.assertEqual((output / "process.log").read_text(), "before timeout\npartial stderr\n")
        record = json.loads((output / "execution.json").read_bytes())
        self.assertEqual(record["status"], "TIMEOUT_UNACCEPTED_RETAIN_ALL")
        self.assertFalse(record["retry_attempted"])

    def test_private_isolation_fails_closed_for_every_required_field(self):
        good = {"exit": 0, "child_desktop_confirmed": True, "foreground_child_observed": False,
                "job_closed": True, "desktop_closed": True}
        self.assertTrue(D.strict_private(good, 0))
        for key in good:
            missing = good.copy();missing.pop(key)
            self.assertFalse(D.strict_private(missing, 0), key)
        for key in ("child_desktop_confirmed", "job_closed", "desktop_closed"):
            changed = good.copy();changed[key] = False
            self.assertFalse(D.strict_private(changed, 0), key)
        changed = good.copy();changed["foreground_child_observed"] = True
        self.assertFalse(D.strict_private(changed, 0))
        self.assertFalse(D.strict_private(good, 2))


if __name__ == "__main__":
    unittest.main(verbosity=2)
