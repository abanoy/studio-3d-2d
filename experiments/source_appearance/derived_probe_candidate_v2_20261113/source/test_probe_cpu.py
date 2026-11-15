"""Synthetic CPU safety/independent-reference controls. Never starts an engine."""
import copy
import hashlib
import json
import math
import os
import sys
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

    def test_nonidentity_imported_rotation_composes_delta_before_scale(self):
        self.data["nodes"][1]["rotation"] = [0., 0., math.sqrt(.5), math.sqrt(.5)]
        delta = [math.sqrt(.5), 0., 0., math.sqrt(.5)]
        g = R.GLB(glb_document(self.data, self.binary))
        # Root translation + joint translation + Rz90 * Rx90 * (1,0,0).
        actual = g.positions(0., 1, delta)[0]["positions"][0]
        for a, expected in zip(actual, [3., 4., 4.]):self.assertAlmostEqual(a, expected)
        # Replacing imported Rz90 by delta alone yields the wrong (4,3,4).
        direct = copy.deepcopy(self.data);direct["nodes"][1]["rotation"] = delta
        wrong = R.GLB(glb_document(direct, self.binary)).positions()[0]["positions"][0]
        self.assertGreater(math.dist(actual, wrong), 1.)
        self.data["nodes"][1]["scale"] = [2., 3., 4.]
        scaled = R.GLB(glb_document(self.data, self.binary)).positions(0., 1, delta)[0]["positions"]
        for actual, expected in zip(scaled[:2], ([3., 5., 4.], [3., 3., 7.])):
            for a, e in zip(actual, expected):self.assertAlmostEqual(a, e)
        wrong_matrix = R.mul(R.local(self.data["nodes"][1]), R.rotation(delta))
        # T*R*S*delta incorrectly rotates through the original Z scale.
        wrong_point = R.point(R.mul(R.local(self.data["nodes"][0]), wrong_matrix), [0., 1., 0.])
        self.assertAlmostEqual(wrong_point[2], 8.)
        self.assertGreater(math.dist(scaled[1], wrong_point), .99)

    def test_pose_matrix_target_refused_without_decomposition(self):
        self.data["nodes"][1] = {"name": "joint", "matrix": list(R.IDENTITY)}
        g = R.GLB(glb_document(self.data, self.binary))
        g.positions()
        with self.assertRaisesRegex(ValueError, "unproved TRS decomposition"):
            g.positions(0., 1, [0., 0., 0., 1.])

    def test_pose_reflected_or_singular_scale_refused(self):
        for scale in ([-1., 1., 1.], [0., 1., 1.]):
            self.data["nodes"][1]["scale"] = scale
            with self.assertRaisesRegex(ValueError, "scale decomposition"):
                R.GLB(glb_document(self.data, self.binary)).positions(0., 1, [0., 0., 0., 1.])

    def test_raw_pose_source_retains_imported_rotation_channel(self):
        source = (D.TASK / "source/raw_probe.gd").read_text()
        self.assertIn("var base_rotation:=skeleton.get_bone_pose_rotation(index)", source)
        self.assertIn("set_bone_pose_rotation(index,(base_rotation*delta).normalized())", source)
        self.assertNotIn("set_bone_pose_rotation(index,Quaternion(", source)

    def test_same_image_positive_content_rejects_blank_and_dithering(self):
        width = height = 128
        blank = bytearray([40, 50, 60, 255]*(width*height))
        self.assertEqual(R.significant_content_rgba(width, height, blank)["significant_content_samples"], 0)
        noise = blank.copy()
        for y in range(4, 100, 4):
            for x in range(4, 100, 4):noise[(y*width+x)*4] += 1
        self.assertEqual(R.significant_content_rgba(width, height, noise)["significant_content_samples"], 0)
        for y in range(4, 100, 4):
            for x in range(4, 100, 4):noise[(y*width+x)*4] += 5
        content = R.significant_content_rgba(width, height, noise)
        self.assertGreater(content["significant_content_samples"], content["required_samples_exclusive"])

    def test_app_capture_checks_its_existing_image_without_second_capture(self):
        source = (D.TASK / "source/app_probe.gd").read_text()
        body = source.split("func _capture(", 1)[1].split("func _writer(", 1)[0]
        self.assertEqual(body.count("renderer.capture("), 1)
        self.assertIn("var content:=_content_observation(image)", body)
        self.assertIn("int(content.significant_content_samples)>100", body)
        self.assertIn('return {"content":content,', body)
        helper = source.split("func _content_observation(", 1)[1].split("func _capture(", 1)[0]
        self.assertIn("range(0,image.get_height(),4)", helper)
        self.assertIn("range(0,image.get_width(),4)", helper)
        self.assertIn(")>.02:changed+=1", helper)

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

    def test_pinned_interpreters_override_and_restore_inherited_environment(self):
        with patch.dict(os.environ, {"HYBRID_PYTHON": "unapproved-python", "HYBRID_GODOT": "unapproved-engine"}):
            with D.pinned_runtime_environment() as child:
                self.assertEqual(child["HYBRID_PYTHON"], str(D.PYTHON))
                self.assertEqual(child["HYBRID_GODOT"], str(D.GODOT))
                self.assertEqual(os.environ["HYBRID_PYTHON"], str(D.PYTHON))
                self.assertNotEqual(child["HYBRID_PYTHON"], "unapproved-python")
            self.assertEqual(os.environ["HYBRID_PYTHON"], "unapproved-python")
            self.assertEqual(os.environ["HYBRID_GODOT"], "unapproved-engine")
        with patch.dict(os.environ, clear=True):
            with self.assertRaisesRegex(RuntimeError, "mock child failure"):
                with D.pinned_runtime_environment():raise RuntimeError("mock child failure")
            self.assertNotIn("HYBRID_PYTHON", os.environ)
            self.assertNotIn("HYBRID_GODOT", os.environ)

    def test_captured_child_receives_explicit_pinned_python_environment(self):
        with D.pinned_runtime_environment() as child:
            with patch.object(D.subprocess, "run", return_value=object()) as mocked:
                D.captured_process(["not-a-runtime"], self.folder, self.folder, 1, env=child)
        self.assertEqual(mocked.call_args.kwargs["env"]["HYBRID_PYTHON"], str(D.PYTHON))
        source = (D.TASK / "source/probe_driver.py").read_text()
        self.assertIn("stamp(PYTHON), stamp(PYTHONW), stamp(GODOT)", source)
        self.assertIn("env=child_environment", source)

    def preservation_fixture(self, key):
        folder = self.folder / key;folder.mkdir()
        protected = folder / "protected.txt";protected.write_text("unchanged")
        reference = folder / "reference.json";reference.write_text("{}")
        projects = {}
        for mode in ("writer", "reader"):
            project = folder / mode;project.mkdir();(project / "source.gd").write_text("frozen")
            projects[mode] = {"path": str(project), "files": D.source_members(project)}
        return folder, {"protected": [D.stamp(protected)], "root_revision": "a"*40,
                        "root_functional": {"fixture": True}, "derived_reference": D.stamp(reference), "projects": projects}

    def test_final_pass_receipt_retained_with_all_preservation_gates(self):
        folder, manifest = self.preservation_fixture("preserved")
        with patch.object(D, "head", return_value="a"*40), patch.object(D, "root_functional", return_value={"fixture": True}), patch.object(D, "preflight", return_value=manifest):
            result = D.final_preservation(manifest, folder / "manifest.json", "b"*64, True)
        self.assertTrue(result["passed"]);self.assertTrue(result["inputs_offline"])
        outcome = {"status": "DERIVED_RENDER_APP_PASS_NOT_NATIVE_FIDELITY"}
        path = folder / "receipt.json";D.retain_and_require_preservation(path, outcome, result)
        self.assertEqual(json.loads(path.read_bytes())["status"], outcome["status"])

    def test_every_false_or_missing_final_gate_retains_failure_and_refuses_success(self):
        scenarios = ("changed_protected", "missing_protected", "head", "functional", "reference", "writer", "reader", "context")
        for key in scenarios:
            with self.subTest(key=key):
                folder, manifest = self.preservation_fixture(key)
                if key == "changed_protected":(folder / "protected.txt").write_text("changed")
                if key == "missing_protected":(folder / "protected.txt").unlink()  # Owned synthetic file only.
                if key == "reference":(folder / "reference.json").write_text("changed")
                if key in ("writer", "reader"):(folder / key / "unexpected.gd").write_text("injected")
                context_error = ValueError("stale manifest or owned inputs") if key == "context" else None
                with patch.object(D, "head", return_value="c"*40 if key == "head" else "a"*40), patch.object(D, "root_functional", return_value={} if key == "functional" else {"fixture": True}), patch.object(D, "preflight", return_value=manifest, side_effect=context_error):
                    result = D.final_preservation(manifest, folder / "manifest.json", "b"*64, False)
                self.assertFalse(result["passed"])
                self.assertIn("private_source_reader", result["gates"])  # Missing early inputs do not suppress later checks.
                outcome = {"status": "DERIVED_RENDER_APP_PASS_NOT_NATIVE_FIDELITY", "error": "earlier evidence remains"}
                path = folder / "receipt.json"
                with self.assertRaisesRegex(ValueError, "receipt and all evidence retained"):
                    D.retain_and_require_preservation(path, outcome, result)
                retained = json.loads(path.read_bytes())
                self.assertEqual(retained["status"], "FAILED_PRESERVATION_RETAIN_ALL")
                self.assertEqual(retained["status_before_final_preservation"], "DERIVED_RENDER_APP_PASS_NOT_NATIVE_FIDELITY")
                self.assertEqual(retained["error"], "earlier evidence remains")
                if key == "missing_protected":
                    self.assertIn("ValueError: Required file missing:", next(iter(result["gates"]["protected_originals_runtimes_candidate"]["files"].values()))["error"])

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
    before = {name: D.stamp(D.TASK / "source" / name) for name in D.CODE}
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    after = {name: D.stamp(D.TASK / "source" / name) for name in D.CODE}
    source_preserved = before == after
    receipt = {"scope": "Synthetic stdlib CPU/reference/source-contract checks only; no preparation or engines",
               "tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
               "failure_details": [{"test": str(test), "traceback": detail} for test, detail in result.failures+result.errors],
               "source_preserved": source_preserved, "source_before": before, "source_after": after,
               "all_failed_evidence_retained": True, "fixture_folder": str(DriverControls.folder),
               "gpu": "UNRUN", "app": "UNRUN", "native_fidelity": "UNTESTED"}
    D.write_new(D.TASK / ("cpu-checks-"+str(time.time_ns())+".json"), receipt)
    raise SystemExit(0 if result.wasSuccessful() and source_preserved else 1)
