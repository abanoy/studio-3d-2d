"""CPU preparation/argument/preservation/metadata/GLB safety controls only."""
import copy
import hashlib
import json
from pathlib import Path
import struct
import sys
import time
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
import conversion_driver as D

ARTIFACTS = D.TASK / ("conversion-cpu-tests-" + str(time.time_ns()))
ARTIFACTS.mkdir(exist_ok=False)


def native_case():
    case = D.read_json(D.TASK / "plan.json")["cases"][1]
    native = {"bones": [{"name": "Root", "parent": -1}], "flex_names": ["Tools"],
              "controllers": [{"name": "Tools", "group": "Tools", "min": 0.0, "max": 1.0}]}
    row = {"case": case["case"], "variant": "groups-000", "selection": {"skin": 0, "bodygroups": {"0": 0, "1": 0, "2": 0}},
           "request": str(D.TASK / "requests/keiki_tools_chisels-groups-000.json")}
    saved = {"skin_groups": case["skin_table"], "bones": [{"name": "Root", "parent": -1}], "flex_names": ["Tools"],
             "flex_controllers": [{"name": "Tools", "group": "Tools", "min": 0., "max": 1., "local_to_global": -1}],
             "bodygroups": {group["name"]: [choice["name"] if not choice["blank"] else None for choice in group["choices"]] for group in case["actual_metadata"]["bodygroups"]},
             "selected_skin": 0, "selected_bodygroup_indices": {"tools": 0, "box": 0, "flame": 0},
             "selected_native_bodygroup_indices": {"0": 0, "1": 0, "2": 0}, "native_appearance_choices": D.catalogue(case),
             "appearance_request": D.read_json(Path(row["request"]))}
    parameters = {"source_sha256": case["native_mdl_sha256"], "source_member": None, "sourceio_revision": D.PIN,
                  "source_profile": "standalone", "native_parameters": saved}
    return row, case, native, parameters


def glb_document():
    binary, views, accessors = bytearray(), [], []
    def view(data):
        binary.extend(b"\0" * (-len(binary) % 4)); start = len(binary); binary.extend(data)
        views.append({"buffer": 0, "byteOffset": start, "byteLength": len(data)})
        return len(views) - 1
    def accessor(rows, kind, fmt="f", component=5126):
        index = view(b"".join(struct.pack("<" + fmt * len(row), *row) for row in rows))
        accessors.append({"bufferView": index, "componentType": component, "count": len(rows), "type": kind})
        return len(accessors) - 1
    pos = accessor([(0., 0., 0.), (1., 0., 0.), (0., 1., 0.)], "VEC3")
    joints = accessor([(0, 0, 0, 0)] * 3, "VEC4", "H", 5123)
    weights = accessor([(1., 0., 0., 0.)] * 3, "VEC4")
    indices = accessor([(0,), (1,), (2,)], "SCALAR", "H", 5123)
    binds = accessor([D.H.IDENTITY, D.H.IDENTITY], "MAT4")
    morph = accessor([(.1, 0., 0.)] * 3, "VEC3")
    image = view(b"synthetic-image-bytes-not-decoded")
    doc = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": len(binary)}], "bufferViews": views, "accessors": accessors,
           "nodes": [{"name": "Root", "children": [1, 2]}, {"name": "tools.dmx", "mesh": 0, "skin": 0}, {"name": "Child"}],
           "skins": [{"joints": [0, 2], "inverseBindMatrices": binds}],
           "meshes": [{"extras": {"targetNames": ["Tools"]}, "primitives": [{"attributes": {"POSITION": pos, "JOINTS_0": joints, "WEIGHTS_0": weights}, "indices": indices, "material": 0, "targets": [{"POSITION": morph, "NORMAL": morph}]}]}],
           "materials": [{"name": "m", "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}}}],
           "textures": [{"source": 0}], "images": [{"bufferView": image, "mimeType": "image/png"}], "scenes": [{"nodes": [0]}], "scene": 0}
    return doc, bytes(binary)


def write_glb(path, doc, binary):
    data = json.dumps(doc, separators=(",", ":")).encode(); data += b" " * (-len(data) % 4)
    binary += b"\0" * (-len(binary) % 4)
    raw = struct.pack("<4sII", b"glTF", 2, 28 + len(data) + len(binary)) + struct.pack("<II", len(data), 0x4E4F534A) + data + struct.pack("<II", len(binary), 0x004E4942) + binary
    path.write_bytes(raw)


class DriverTests(unittest.TestCase):
    def folder(self):
        path = ARTIFACTS / self._testMethodName; path.mkdir(exist_ok=False); return path

    def arrays(self):
        return D.read_json(D.TASK / "plan.json"), D.read_json(D.TASK / "commands-for-owned-stage.json")

    def test_exact_fourteen_order_baselines_first_refusals_last(self):
        rows = D.schedule(*self.arrays())
        self.assertEqual([(row["case"], row["variant"]) for row in rows], D.ORDER)
        self.assertTrue(all(row["selection"] is None for row in rows[:2]))
        self.assertTrue(all(not row["expected_success"] for row in rows[-2:]))

    def test_duplicate_case_and_appended_mount_option_refuse(self):
        plan, arrays = self.arrays(); arrays["commands"].append(arrays["commands"][0])
        with self.assertRaises(ValueError): D.schedule(plan, arrays)
        plan, arrays = self.arrays(); arrays["commands"][0]["command"] += ["--content", r"C:\installed"]
        with self.assertRaisesRegex(ValueError, "unexpected"): D.schedule(plan, arrays)

    def test_changed_worker_runtime_source_and_request_paths_refuse(self):
        for index in [0, 1, 2, 4, 8, 10]:
            plan, arrays = self.arrays()
            args = arrays["commands"][0]["command"]
            if index >= len(args): continue
            args[index] = r"C:\unexpected"
            with self.subTest(index=index), self.assertRaises(ValueError): D.schedule(plan, arrays)

    def test_duplicate_option_and_wrong_expected_result_refuse(self):
        plan, arrays = self.arrays(); arrays["commands"][0]["command"] += ["--output", "other"]
        with self.assertRaises(ValueError): D.schedule(plan, arrays)
        plan, arrays = self.arrays(); arrays["commands"][0]["expected_prepare_success"] = False
        with self.assertRaises(ValueError): D.schedule(plan, arrays)

    def test_candidate_commands_are_fresh_owned_and_private(self):
        rows = D.schedule(*self.arrays()); folder = self.folder()
        case, bundle, native, private = D.commands(rows[0], 0, folder)
        self.assertTrue(bundle.is_relative_to(folder)); self.assertFalse(case.exists())
        self.assertEqual(native[1:3], ["-B", "-u"])
        self.assertIn("--gmod", native); self.assertIn("--workshop", native)
        self.assertEqual(private[1], str(D.PRIVATE)); self.assertIn("--cancel-file", private)
        self.assertNotIn("--content", native)

    def test_owned_path_traversal_or_outside_refuses(self):
        folder = self.folder()
        for path in [folder, folder.parent / "other", folder / ".." / "other"]:
            with self.subTest(path=path), self.assertRaises(ValueError): D.owned(path, folder)

    def test_functional_snapshot_detects_bytes_and_added_files(self):
        folder = self.folder()
        for name in ["src", "tests", "tools", "data", "examples"]: (folder / name).mkdir()
        for name in ["project.godot", "main.tscn", "run.py", "launch.pyw"]: (folder / name).write_text("source")
        first = D.functional(folder)
        (folder / "src/new.gd").write_text("new")
        self.assertNotEqual(first, D.functional(folder))
        (folder / "run.py").write_text("changed")
        self.assertNotEqual(first["run.py"], D.functional(folder)["run.py"])

    def test_exact_native_catalogue_and_selected_indices(self):
        row, case, native, parameters = native_case()
        self.assertEqual(D.verify_parameters(parameters, row, case, native), ["tools.dmx", "box.smd", "flame.smd"])
        for field, bad in [("selected_skin", 1), ("selected_native_bodygroup_indices", {"0": 1, "1": 0, "2": 0}),
                           ("native_appearance_choices", {}), ("flex_names", []), ("bones", [])]:
            changed = copy.deepcopy(parameters); changed["native_parameters"][field] = bad
            with self.subTest(field=field), self.assertRaises(ValueError): D.verify_parameters(changed, row, case, native)

    def test_native_blank_not_inferred_from_label(self):
        row, case, native, parameters = native_case()
        parameters["native_parameters"]["bodygroups"]["tools"][1] = "blank"
        with self.assertRaisesRegex(ValueError, "blank/variant"): D.verify_parameters(parameters, row, case, native)

    def test_no_request_baseline_has_ordinary_report_contract(self):
        row, case, native, parameters = native_case()
        row["selection"] = None
        with self.assertRaisesRegex(ValueError, "Default native report"): D.verify_parameters(parameters, row, case, native)
        for key in ["selected_native_bodygroup_indices", "native_appearance_choices", "appearance_request"]: parameters["native_parameters"].pop(key)
        self.assertEqual(len(D.verify_parameters(parameters, row, case, native)), 3)

    def test_embedded_glb_decodes_skin_geometry_morph_fingerprints(self):
        folder = self.folder(); doc, binary = glb_document(); path = folder / "scene.glb"; write_glb(path, doc, binary)
        result = D.glb_structure(path, ["tools.dmx"], {"bones": [{"name": "Root", "parent": -1}]})
        self.assertEqual(result["meshes"][0]["primitives"][0]["vertices"], 3)
        self.assertEqual(result["meshes"][0]["primitives"][0]["nonzero_position_morph_vertices"], [3])
        self.assertEqual(len(result["active_materials"]), 1)

    def test_external_image_and_wrong_membership_refuse(self):
        folder = self.folder(); doc, binary = glb_document(); doc["images"][0]["uri"] = "https://invalid/image.png"
        path = folder / "external.glb"; write_glb(path, doc, binary)
        with self.assertRaises(ValueError): D.glb_structure(path, ["tools.dmx"], {"bones": [{"name": "Root", "parent": -1}]})
        doc, binary = glb_document(); path = folder / "wrong.glb"; write_glb(path, doc, binary)
        with self.assertRaisesRegex(ValueError, "membership"): D.glb_structure(path, ["box.smd"], {"bones": [{"name": "Root", "parent": -1}]})

    def test_missing_native_joint_and_bad_triangle_refuse(self):
        folder = self.folder(); doc, binary = glb_document(); path = folder / "joint.glb"; write_glb(path, doc, binary)
        with self.assertRaisesRegex(ValueError, "lost native"): D.glb_structure(path, ["tools.dmx"], {"bones": [{"name": "Missing", "parent": -1}]})
        doc, binary = glb_document(); index = doc["meshes"][0]["primitives"][0]["indices"]; view = doc["bufferViews"][doc["accessors"][index]["bufferView"]]
        data = bytearray(binary); struct.pack_into("<H", data, view["byteOffset"], 7); path = folder / "triangle.glb"; write_glb(path, doc, bytes(data))
        with self.assertRaisesRegex(ValueError, "indices out of range"): D.glb_structure(path, ["tools.dmx"], {"bones": [{"name": "Root", "parent": -1}]})

    def test_private_receipt_requires_owned_closed_job_and_desktop(self):
        receipt = {"format": "studio_private_desktop_1", "exit": 0, "child_desktop_confirmed": True,
                   "foreground_child_observed": False, "job_closed": True, "desktop_closed": True, "desktop_switch_requested": False}
        D.private_ok(receipt, 0)
        for key in ["child_desktop_confirmed", "job_closed", "desktop_closed"]:
            with self.subTest(key=key), self.assertRaises(ValueError): D.private_ok(dict(receipt, **{key: False}), 0)
        with self.assertRaises(ValueError): D.private_ok(dict(receipt, foreground_child_observed=True), 0)

    def test_worker_request_refuses_installed_or_added_mount(self):
        folder = self.folder(); row, case, _, _ = native_case()
        row.update(source=str(D.TASK / "stage" / case["case"] / case["native_member"]))
        native_mount = folder / "native"; content = D.TASK / "stage" / case["case"] / case["native_member"].split("/")[0]
        request = {"original_source": row["source"], "source": str(native_mount / Path(row["source"]).name),
                   "sha256": case["native_mdl_sha256"], "source_member": None, "output": str(folder), "sourceio": str(D.SOURCEIO),
                   "sourceio_revision": D.PIN, "source_profile": "standalone", "gmod_installation": "",
                   "mounts": [str(native_mount), str(content)], "appearance": D.read_json(Path(row["request"]))}
        target = folder / "conversion-request.json"; D.S.save(target, request)
        self.assertEqual(len(D.verify_conversion_request(folder, row, case)[1]), 2)
        changed = dict(request, mounts=request["mounts"] + [r"C:\installed"])
        with patch.object(D, "read_json", side_effect=lambda path, *a, **k: changed if path == target else request["appearance"]):
            with self.assertRaisesRegex(ValueError, "mounted unowned"): D.verify_conversion_request(folder, row, case)

    def test_dependency_classification_preserves_native_gap_and_inactive_missing(self):
        folder = self.folder(); mount = folder / "owned-mount"; bundle = folder / "bundle"; bundle.mkdir()
        rows = []
        for name, data in [("materials/a.vmt", b"vmt"), ("materials/base.vtf", b"vtf")]:
            source = mount / name; source.parent.mkdir(parents=True, exist_ok=True); source.write_bytes(data)
            target = bundle / "resolved-native" / name; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data)
            rows.append({"path": name, "provider": str(mount), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        D.S.save(bundle / "dependencies.json", {"resolved": rows, "missing_requests": ["materials/inactive.vmt", "models/probe.phy"]})
        parameters = {"materials": [{"material": "m", "vmt": "materials/a.vmt", "base_texture": "materials/base.vtf", "status": "PBR approximation"},
                                   {"material": "inactive", "vmt": "materials/inactive.vmt", "status": "fallback gray"}]}
        gap = [{"reference": "materials/hairbump.vtf", "resolved": False}]
        approved = {D.normalized(mount / row["path"]): {"bytes": row["bytes"], "sha256": row["sha256"]} for row in rows}
        result = D.dependencies(bundle, parameters, {"active_materials": [{"name": "m"}]}, [mount], gap, approved)
        self.assertEqual(result["native_preflight_missing_references"], gap)
        self.assertEqual(result["actual_missing_requests"][0]["classification"], "inactive material input")
        self.assertIn("unclassified", result["actual_missing_requests"][1]["classification"])
        with self.assertRaisesRegex(ValueError, "unowned provider"):
            D.dependencies(bundle, parameters, {"active_materials": [{"name": "m"}]}, [folder / "different"], gap, approved)
        with self.assertRaisesRegex(ValueError, "not an approved staged resource"):
            D.dependencies(bundle, parameters, {"active_materials": [{"name": "m"}]}, [mount], gap, {})
        parameters["materials"][0]["status"] = "fallback gray"
        with self.assertRaisesRegex(ValueError, "fallback gray"):
            D.dependencies(bundle, parameters, {"active_materials": [{"name": "m"}]}, [mount], gap, approved)

    def test_added_unlisted_stage_file_refuses_membership(self):
        folder = self.folder(); (folder / "approved.vtf").write_bytes(b"approved")
        expected = D.staged_members(folder); D.verify_stage_members(folder, expected)
        (folder / "unlisted.vtf").write_bytes(b"new")
        with self.assertRaisesRegex(ValueError, "membership changed"):
            D.verify_stage_members(folder, expected)

    def test_binding_rest_joint_order_and_default_weights_change_fingerprint(self):
        folder = self.folder(); native = {"bones": [{"name": "Root", "parent": -1}]}
        def fingerprint(name, doc, binary):
            path = folder / (name + ".glb"); write_glb(path, doc, binary)
            return D.glb_structure(path, ["tools.dmx"], native)["meshes"][0]["primitives"][0]["geometry_skin_morph_sha256"]
        doc, binary = glb_document(); baseline = fingerprint("baseline", doc, binary)
        changed = copy.deepcopy(doc); changed["skins"][0]["joints"].reverse()
        self.assertNotEqual(baseline, fingerprint("joint-order", changed, binary))
        changed = copy.deepcopy(doc); changed["nodes"][0]["translation"] = [.25, 0., 0.]
        self.assertNotEqual(baseline, fingerprint("rest", changed, binary))
        changed = copy.deepcopy(doc); changed["meshes"][0]["weights"] = [.5]
        self.assertNotEqual(baseline, fingerprint("default-weight", changed, binary))
        data = bytearray(binary); accessor = doc["accessors"][doc["skins"][0]["inverseBindMatrices"]]
        view = doc["bufferViews"][accessor["bufferView"]]; struct.pack_into("<f", data, view["byteOffset"] + 12 * 4, .25)
        self.assertNotEqual(baseline, fingerprint("inverse-bind", doc, bytes(data)))

    def test_unused_skin_cannot_supply_missing_native_binding(self):
        folder = self.folder(); doc, binary = glb_document()
        accessor = doc["skins"][0]["inverseBindMatrices"]
        doc["accessors"][accessor]["count"] = 1
        doc["skins"][0]["joints"] = [2]
        doc["skins"].append({"joints": [0], "inverseBindMatrices": accessor})
        path = folder / "unused.glb"; write_glb(path, doc, binary)
        with self.assertRaisesRegex(ValueError, "lost native joint"):
            D.glb_structure(path, ["tools.dmx"], {"bones": [{"name": "Root", "parent": -1}]})

    def test_all_blank_refusal_needs_exact_reason_and_no_glb(self):
        folder = self.folder(); (folder / "conversion.log").write_text(D.REFUSAL)
        receipt = {"format": "studio_private_desktop_1", "exit": 1, "child_desktop_confirmed": True,
                   "foreground_child_observed": False, "job_closed": True, "desktop_closed": True, "desktop_switch_requested": False}
        D.refused(1, receipt, folder, D.REFUSAL)
        with self.assertRaises(ValueError): D.refused(1, receipt, folder, "other failure")
        (folder / "scene.glb").write_bytes(b"wrong")
        with self.assertRaises(ValueError): D.refused(1, receipt, folder, D.REFUSAL)

    def test_no_conversion_lease_or_freeze_execution_combination(self):
        with self.assertRaisesRegex(ValueError, "Freeze mode"):
            D.main(["--freeze-lock", str(D.TASK / "conversion-inputs-invalid.json"), "--run-conversions"])
        with self.assertRaisesRegex(ValueError, "explicit lease"):
            D.main(["--input-lock", str(D.TASK / "unused.json"), "--lock-sha256", "0" * 64, "--run-conversions"])


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(DriverTests))
    report = {"format": "has_sfm_conversion_driver_cpu_1", "checks": result.testsRun, "failures": len(result.failures),
              "errors": len(result.errors), "skips": len(result.skipped), "artifact_folder": str(ARTIFACTS),
              "synthetic_glb_only": True, "native_conversion_blender_private_desktop_gpu_network": False, "automatic_cleanup": False}
    D.S.save(ARTIFACTS / "verification.json", report); print(json.dumps(report), flush=True)
    raise SystemExit(0 if result.wasSuccessful() else 1)
