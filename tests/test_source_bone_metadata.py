"""Authored69-row compact proof, exact wire and final nested budget controls."""
import ast
import contextlib
import copy
import hashlib
import io
import json
import math
import os
from pathlib import Path
import struct
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import source_bone_metadata as M
import source_bone_export as E
import source_jiggle_metadata as J
import source_jiggle_crosswalk as C
import source_mdl_snapshot as S
from source_jiggle_fixtures import authored, base_report, ORIGINAL


def fixture():
    raw, bones = authored(count=68)
    raw = bytearray(raw)
    for index in range(50, 69): struct.pack_into("<2I", raw, 408+index*216+164, 0, 0)
    raw = bytes(raw); native = hashlib.sha256(raw).hexdigest()
    report = base_report(bones)
    inspection = J.inspect(raw, ORIGINAL, native, bones, M.SCALE)
    plan = J.plan_report(report, inspection, "\r\n", expected_native_mdl_sha256=native)
    observed = {"native_mdl_sha256": native, "native_bone_count": 69, "source_scale": M.SCALE,
                "status": "observed_inactive", "applied": False, "HAS_runtime_binding": "unattempted",
                "native_simulation": False, "export_extras": False, "glb_sha256": "c"*64,
                "private_scene_mesh_rest_data": [2., 3., 4.], "bones": []}
    for index, bone in reversed(list(enumerate(bones))):
        observed["bones"].append({"native_index": index, "native_name": bone["name"],
            "native_parent_index": bone["parent"], "gltf_node_index": 3+(index*7)%69,
            "skin_memberships": [{"skin_index": 2, "joint_slot": 68-index}],
            "maximum_reference_matrix_error": 5e-6, "native_rest_words_uint32": [0]*7,
            "Blender_matrix_local_row_major": [1.]*16})
    return SimpleNamespace(raw=raw, sha=native, base=report, inspection=inspection, plan=plan, observed=observed)


class BoneMetadataTests(unittest.TestCase):
    def setUp(self):
        self.value = fixture()
        self.profile = patch.object(C, "JUNKO_SHA256", self.value.sha)
        self.profile.start(); self.addCleanup(self.profile.stop)

    def plan(self, plan=None, observed=None, **kwargs):
        return M.plan_report(self.value.plan if plan is None else plan,
            self.value.observed if observed is None else observed,
            expected_original_sha256=kwargs.get("original", ORIGINAL),
            expected_native_sha256=kwargs.get("native", self.value.sha),
            expected_glb_sha256=kwargs.get("glb", "c"*64), newline="\r\n")

    def test_compact_projection_complete_inactive_and_excludes_all_private_arrays(self):
        result = self.plan(); metadata = result["report"]["native_parameters"][M.KEY]
        self.assertEqual([row["native_index"] for row in metadata["bones"]], list(range(69)))
        self.assertEqual(metadata["status"], "retained_inert")
        self.assertEqual(metadata["runtime_binding"], "unattempted")
        self.assertEqual(metadata["native_solver"], "not_implemented")
        self.assertFalse(metadata["applied"])
        self.assertNotIn("private_scene_mesh_rest_data", metadata)
        self.assertTrue(all(set(row) == {"native_index", "native_name", "native_parent_index", "gltf_node_index", "skin_memberships"}
                            for row in metadata["bones"]))
        self.assertEqual(metadata["observed_proof_sha256"], hashlib.sha256(C.compact(self.value.observed)).hexdigest())
        self.assertEqual(metadata["max_rest_matrix_error"], 5e-6)
        self.assertEqual(result["report_bytes"], J.report_bytes(result["report"], "\r\n"))
        self.assertNotIn(b"\r\r\n", result["report_bytes"])
        self.assertEqual(result["report"]["native_parameters"][J.KEY], self.value.inspection["metadata"])

    def test_ascii_wire_has_fixed_header_sha_order_and_no_float_fields(self):
        metadata = self.plan()["report"]["native_parameters"][M.KEY]
        wire = M.proof_wire_bytes(metadata)
        self.assertEqual(wire.splitlines()[:7], [b"studio_source_bone_crosswalk_binding_1",
            ("original_source_sha256="+ORIGINAL).encode(), ("native_mdl_sha256="+self.value.sha).encode(),
            b"glb_sha256="+b"c"*64, ("native_bone_catalogue_sha256="+metadata["native_bone_catalogue_sha256"]).encode(),
            ("jiggle_wire_sha256="+metadata["jiggle_wire_sha256"]).encode(), b"native_bone_count=69"])
        self.assertIn(b"bone=0\t-1\t3\tbone000_xxxx\t1\nskin=2\t68\n", wire)
        changed = copy.deepcopy(metadata); changed["source_scale"] = 9.; changed["max_rest_matrix_error"] = 1.
        self.assertEqual(M.proof_wire_bytes(changed), wire)
        self.assertEqual(metadata["proof_sha256"], hashlib.sha256(wire).hexdigest())

    def test_wire_is_row_and_membership_order_independent_but_binds_nodes_and_words(self):
        metadata = self.plan()["report"]["native_parameters"][M.KEY]
        initial = M.proof_wire_bytes(metadata)
        metadata["bones"].reverse()
        self.assertEqual(M.proof_wire_bytes(metadata), initial)
        metadata["bones"][0]["gltf_node_index"] += 100
        self.assertNotEqual(M.proof_wire_bytes(metadata), initial)
        jiggle = copy.deepcopy(self.value.inspection["metadata"])
        jiggle["rules"].reverse()
        self.assertEqual(M.jiggle_wire_sha256(jiggle, self.value.base["native_parameters"]["bones"]),
                         self.plan()["report"]["native_parameters"][M.KEY]["jiggle_wire_sha256"])
        jiggle["rules"][0]["binary_provenance"]["float32_words_uint32"][0] ^= 1
        with self.assertRaises(ValueError): M.jiggle_wire_sha256(jiggle, self.value.base["native_parameters"]["bones"])

    def test_duplicate_missing_alias_and_unbounded_names_omit_whole_proof(self):
        actions = [lambda p: p["bones"].pop(), lambda p: p["bones"].append(copy.deepcopy(p["bones"][0])),
                   lambda p: p["bones"][1].update(gltf_node_index=p["bones"][0]["gltf_node_index"]),
                   lambda p: p["bones"][0].update(native_name="bad\tname"),
                   lambda p: p["bones"][0]["skin_memberships"].append({"skin_index": 2, "joint_slot": 0})]
        for action in actions:
            observed = copy.deepcopy(self.value.observed); action(observed)
            with self.subTest(action=action):
                result = self.plan(observed=observed)
                self.assertEqual(result["report_bytes"], self.value.plan["report_bytes"])
                self.assertNotIn(M.KEY, result["report"]["native_parameters"])
                self.assertEqual(json.loads(result["crosswalk_note_bytes"])["reason"], "proof_unavailable")

    def test_max_error_nonfinite_over_profile_and_applied_state_omit(self):
        for field, bad in (("maximum_reference_matrix_error", float("nan")),
                           ("maximum_reference_matrix_error", .1), ("maximum_reference_matrix_error", True)):
            observed = copy.deepcopy(self.value.observed); observed["bones"][0][field] = bad
            self.assertEqual(self.plan(observed=observed)["report_bytes"], self.value.plan["report_bytes"])
        observed = copy.deepcopy(self.value.observed); observed["applied"] = True
        self.assertEqual(self.plan(observed=observed)["report_bytes"], self.value.plan["report_bytes"])

    def test_actual_final_nested_windows_budget_accepts_exact_limit(self):
        first = self.plan(); padding = J.REPORT_LIMIT-len(first["report_bytes"])
        plan = copy.deepcopy(self.value.plan); plan["report"]["padding"] = "x"*padding
        plan["report_bytes"] = J.report_bytes(plan["report"], "\r\n")
        result = self.plan(plan=plan)
        self.assertEqual(len(result["report_bytes"]), J.REPORT_LIMIT)
        self.assertIn(M.KEY, result["report"]["native_parameters"])

    def test_one_byte_over_keeps_existing_jiggle_priority_and_exact_bytes(self):
        first = self.plan(); padding = J.REPORT_LIMIT-len(first["report_bytes"])+1
        plan = copy.deepcopy(self.value.plan); plan["report"]["padding"] = "x"*padding
        plan["report_bytes"] = J.report_bytes(plan["report"], "\r\n")
        before = copy.deepcopy(plan)
        result = self.plan(plan=plan)
        self.assertEqual(result["report"], before["report"])
        self.assertEqual(result["report_bytes"], before["report_bytes"])
        self.assertEqual(result["report"]["native_parameters"][J.KEY]["rules"], self.value.inspection["metadata"]["rules"])
        self.assertEqual(json.loads(result["crosswalk_note_bytes"])["reason"], "report_budget")
        self.assertEqual(plan, before)

    def test_identity_failure_precedes_every_optional_size_or_missing_jiggle_gate(self):
        plan = copy.deepcopy(self.value.plan); plan["state"] = "omitted_log_only"; plan["report"]["padding"] = "x"*(J.REPORT_LIMIT+1)
        for field in ("original", "native", "glb"):
            with self.subTest(field=field), self.assertRaises(C.SourceIdentityError): self.plan(plan=plan, **{field: "0"*64})

    def test_jiggle_not_embedded_preserves_exact_plan_without_status_branch(self):
        plan = copy.deepcopy(self.value.plan); plan["state"] = "omitted_status_inline"
        result = self.plan(plan=plan)
        self.assertEqual(result["report_bytes"], plan["report_bytes"])
        self.assertNotIn(M.KEY, result["report"]["native_parameters"])
        self.assertEqual(json.loads(result["crosswalk_note_bytes"])["reason"], "jiggle_not_retained")

    def test_source_scale_parent_and_jiggle_named_value_mismatch_refuse_complete_proof(self):
        for action in (lambda p: p.update(source_scale=.02),
                       lambda p: p["bones"][0].update(native_parent_index=1)):
            observed = copy.deepcopy(self.value.observed); action(observed)
            self.assertEqual(self.plan(observed=observed)["report_bytes"], self.value.plan["report_bytes"])
        plan = copy.deepcopy(self.value.plan)
        rule = plan["report"]["native_parameters"][J.KEY]["rules"][0]
        rule["parameters"][next(iter(rule["parameters"]))] += 1.
        self.assertEqual(self.plan(plan=plan)["report_bytes"], plan["report_bytes"])

    def test_real_bridge_publication_writes_only_measured_combined_bytes(self):
        tree = ast.parse((ROOT/"tools/blender_source_bridge.py").read_text(encoding="utf-8"))
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "publish_parameters")
        with tempfile.TemporaryDirectory(prefix="has-crosswalk-publish-") as folder:
            out = Path(folder); path = out/"authored.mdl"; path.write_bytes(self.value.raw)
            capture = S.capture_selected_mdl(str(path))
            observation = SimpleNamespace(capture=capture, original_sha256=ORIGINAL,
                                          publication_identity=lambda: "c"*64)
            state = {"observation": observation, "observed": self.value.observed, "reason": None}
            namespace = {"source_jiggle_metadata": J, "source_mdl_snapshot": S, "source_bone_export": E,
                         "out": out, "os": SimpleNamespace(linesep="\r\n"), "json": json}
            exec(compile(ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[])), "bridge-cpu", "exec"), namespace)
            text = io.StringIO()
            with contextlib.redirect_stdout(text):
                report = namespace["publish_parameters"](self.value.base, capture, self.value.inspection, state)
            self.assertEqual((out/"parameters.json").read_bytes(), self.plan()["report_bytes"])
            self.assertEqual(text.getvalue(), "")
            self.assertEqual(set(out.iterdir()), {path, out/"parameters.json"})
            self.assertIn(M.KEY, report["native_parameters"])


if __name__ == "__main__": unittest.main(verbosity=2)
