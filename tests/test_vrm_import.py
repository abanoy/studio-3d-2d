from pathlib import Path
import copy
import json
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from prepare_vrm import prepare, read_vrm


def document(family="1.0"):
    native = {"specVersion": "1.0" if family == "1.0" else "0.0", "meta": {"name": "Authored fixture"},
              "humanoid": {"humanBones": {"hips": {"node": 0}} if family == "1.0" else [{"bone": "hips", "node": 0}]}}
    return {"asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": [0]}],
            "nodes": [{"name": "Hip"}], "buffers": [{"byteLength": 4}],
            "extensions": {"VRMC_vrm" if family == "1.0" else "VRM": native}}


def glb(doc, binary=b"\0\0\0\0"):
    text = json.dumps(doc, separators=(",", ":")).encode()
    text += b" " * (-len(text) % 4)
    return struct.pack("<4sIIII", b"glTF", 2, 28 + len(text) + len(binary), len(text), 0x4e4f534a) + text + struct.pack("<II", len(binary), 0x004e4942) + binary


class VRM(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.source = self.folder / "input.vrm"
        self.output = self.folder / "prepared"

    def test_versions_preserve_data_and_normalize_forward(self):
        for family in ("1.0", "0.x"):
            with self.subTest(family=family):
                doc = document(family)
                self.source.write_bytes(glb(doc))
                before = self.source.read_bytes()
                result = prepare(self.source, self.folder / family)
                _, normalized, binary, _, native, bones = read_vrm(Path(result["glb"]))
                self.assertEqual(binary, b"\0" * 4)
                self.assertEqual(normalized["extensions"], doc["extensions"])
                self.assertEqual(normalized["nodes"][0], doc["nodes"][0])
                self.assertEqual(bones["hips"]["node_name"], "Hip")
                wrapper = normalized["nodes"][-1]
                self.assertEqual(wrapper.get("rotation"), [0, 1, 0, 0] if family == "0.x" else None)
                self.assertEqual(self.source.read_bytes(), before)

    def test_shared_scene_roots_reuse_wrapper(self):
        doc = document();doc["scenes"].append(copy.deepcopy(doc["scenes"][0]))
        self.source.write_bytes(glb(doc))
        result = prepare(self.source, self.output)
        _, normalized, *_ = read_vrm(Path(result["glb"]))
        self.assertEqual(len(normalized["nodes"]), 2)
        self.assertEqual(normalized["scenes"][0]["nodes"], normalized["scenes"][1]["nodes"])

    def test_external_images_and_buffers_fail_before_output(self):
        for group in ("images", "buffers"):
            doc = document();doc[group] = [{"uri": "../outside.png", "byteLength": 4}]
            self.source.write_bytes(glb(doc))
            with self.assertRaisesRegex(ValueError, "embed"): prepare(self.source, self.output)
            self.assertFalse(self.output.exists())

    def test_truncated_chunks_and_declared_size(self):
        raw = glb(document())
        for broken in (raw[:-1], raw[:12] + struct.pack("<I", 0xffffffff) + raw[16:]):
            self.source.write_bytes(broken)
            with self.assertRaises(ValueError): prepare(self.source, self.output)

    def test_unsupported_version_and_ambiguous_family(self):
        for extra in ({"VRMC_vrm": {"specVersion": "9.0"}}, {"VRMC_vrm": {}, "VRM": {}}):
            doc = document();doc["extensions"] = extra;self.source.write_bytes(glb(doc))
            with self.assertRaises(ValueError): prepare(self.source, self.output)
            self.assertFalse(self.output.exists())

    def test_missing_humanoid_node(self):
        doc = document();doc["extensions"]["VRMC_vrm"]["humanoid"]["humanBones"]["hips"]["node"] = 5
        self.source.write_bytes(glb(doc))
        with self.assertRaisesRegex(ValueError, "missing node"): prepare(self.source, self.output)

    def test_cancel_and_bad_scale_keep_original_and_no_output(self):
        raw = glb(document());self.source.write_bytes(raw)
        cancel = self.folder / "cancel";cancel.write_text("cancel")
        with self.assertRaises(RuntimeError): prepare(self.source, self.output, cancel_file=cancel)
        for scale in (float("nan"), 0, 10001):
            with self.assertRaises(ValueError): prepare(self.source, self.output, scale)
        self.assertFalse(self.output.exists());self.assertEqual(self.source.read_bytes(), raw)

    def test_existing_output_not_overwritten(self):
        self.source.write_bytes(glb(document()));self.output.mkdir();(self.output / "keep").write_text("owner")
        with self.assertRaises(FileExistsError): prepare(self.source, self.output)
        self.assertEqual((self.output / "keep").read_text(), "owner")


if __name__ == "__main__": unittest.main()
