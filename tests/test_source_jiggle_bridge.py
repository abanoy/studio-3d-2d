"""Execute the real bridge seams with authored files and CPU host stubs only."""
import ast
import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import source_jiggle_metadata as M
import source_mdl_snapshot as S
from source_jiggle_fixtures import authored, base_report, legacy_bytes, padded, ORIGINAL

BRIDGE = ROOT / "tools/blender_source_bridge.py"
TREE = ast.parse(BRIDGE.read_text(encoding="utf-8"), filename=str(BRIDGE))
PUBLISH = next(node for node in TREE.body if isinstance(node, ast.FunctionDef) and node.name == "publish_parameters")
SELECTED = next(node for node in TREE.body if isinstance(node, ast.If)
                and ast.unparse(node.test) == "source.suffix.lower() == '.mdl'")
PUBLICATION = next(node for node in TREE.body if isinstance(node, ast.Assign)
                   and isinstance(node.value, ast.Call)
                   and isinstance(node.value.func, ast.Name) and node.value.func.id == "publish_parameters")


def execute(nodes, namespace):
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), str(BRIDGE), "exec"), namespace)


class SourceJiggleBridgeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="has-jiggle-bridge-")
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        self.out = self.folder / "converted"
        self.out.mkdir()
        self.path = self.folder / "authored.mdl"
        self.raw, self.bones = authored()
        self.path.write_bytes(self.raw)
        self.capture = S.capture_selected_mdl(str(self.path))
        self.base = base_report(self.bones)
        self.inspection = M.inspect(self.raw, ORIGINAL, self.capture.native_sha256, self.bones, self.base["scale"])
        self.namespace = {"source_jiggle_metadata": M, "source_mdl_snapshot": S,
                          "json": json, "os": os, "out": self.out}
        execute([PUBLISH], self.namespace)

    def publish(self, report=None, capture=None, inspection=None):
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            result = self.namespace["publish_parameters"](
                self.base if report is None else report,
                self.capture if capture is None else capture,
                self.inspection if inspection is None else inspection)
        return result, stream.getvalue()

    def note(self, text):
        lines = text.splitlines()
        self.assertEqual(len(lines), 1)
        prefix, encoded = lines[0].split(" ", 1)
        self.assertEqual(prefix, "STUDIO_SOURCE_JIGGLE_OMITTED")
        self.assertLessEqual(len(encoded.encode("utf-8")), M.STATUS_LIMIT)
        return json.loads(encoded)

    def test_embedded_report_uses_exact_final_windows_bytes_without_double_cr(self):
        # Include adjacent native data to exercise the actual nested report.
        baseline = copy.deepcopy(self.base)
        baseline["native_parameters"]["flex_controllers"] = [{"name": "adjacent", "min": 0.0, "max": 1.0}] * 100
        before = copy.deepcopy(baseline)
        self.namespace["os"] = SimpleNamespace(linesep="\r\n")
        expected = M.plan_report(baseline, self.inspection, "\r\n", expected_native_mdl_sha256=self.capture.native_sha256)
        result, text = self.publish(baseline)
        actual = (self.out / "parameters.json").read_bytes()
        self.assertEqual(actual, expected["report_bytes"])
        self.assertIn(b"\r\n", actual)
        self.assertNotIn(b"\r\r\n", actual)
        self.assertLessEqual(len(actual), M.REPORT_LIMIT)
        self.assertEqual(text, "")
        self.assertEqual(baseline, before)
        self.assertEqual(result["native_parameters"][M.KEY]["rules"], self.inspection["metadata"]["rules"])
        self.assertEqual(self.path.read_bytes(), self.raw)
        self.assertEqual(set(self.out.iterdir()), {self.out / "parameters.json"})

    def test_no_rule_capture_retains_exact_legacy_bytes_and_no_log(self):
        raw, bones = authored(jiggle=False)
        self.path.write_bytes(raw)
        capture = S.capture_selected_mdl(str(self.path))
        report = base_report(bones)
        inspection = M.inspect(raw, ORIGINAL, capture.native_sha256, bones, report["scale"])
        result, text = self.publish(report, capture, inspection)
        self.assertEqual((result, text), (report, ""))
        self.assertEqual((self.out / "parameters.json").read_bytes(), legacy_bytes(report, os.linesep))
        self.assertNotIn(M.KEY, result["native_parameters"])

    def test_bsp_none_capture_never_calls_native_helpers_and_keeps_legacy_bytes(self):
        report = {"source_sha256": ORIGINAL, "native_parameters": {"props_loaded": 2}}
        stream = io.StringIO()
        with patch.object(S, "recheck_selected_mdl", side_effect=AssertionError("BSP recheck forbidden")), \
                patch.object(M, "plan_report", side_effect=AssertionError("BSP plan forbidden")), contextlib.redirect_stdout(stream):
            result = self.namespace["publish_parameters"](report, None, {"state": "none"})
        self.assertEqual((result, stream.getvalue()), (report, ""))
        self.assertEqual((self.out / "parameters.json").read_bytes(), legacy_bytes(report, os.linesep))

    def test_not_inspected_logs_bounded_reason_without_inventing_native_hash(self):
        capture = S.NotInspected("selected-mdl-exceeds-16-mib-capture-limit")
        with patch.object(S, "recheck_selected_mdl", side_effect=AssertionError("no captured identity")), \
                patch.object(M, "plan_report", side_effect=AssertionError("no metadata identity")):
            result, text = self.publish(capture=capture)
        note = self.note(text)
        self.assertEqual(note["status"], "not_inspected")
        self.assertEqual(note["reason"], capture.reason)
        self.assertEqual(note["original_source_sha256"], ORIGINAL)
        self.assertNotIn("native_mdl_sha256", note)
        self.assertEqual(note["retained_rule_count"], 0)
        self.assertEqual(result, self.base)
        self.assertEqual((self.out / "parameters.json").read_bytes(), legacy_bytes(self.base, os.linesep))

    def test_full_report_omission_uses_planned_bytes_and_complete_log_reason(self):
        baseline = padded(self.base, M.REPORT_LIMIT + 1, self.inspection["metadata"])
        self.namespace["os"] = SimpleNamespace(linesep="\r\n")
        result, text = self.publish(baseline)
        note = self.note(text)
        self.assertEqual((note["reason"], note["retained_rule_count"]), ("report_budget", 0))
        self.assertEqual(note["full_report_candidate_bytes"], M.REPORT_LIMIT + 1)
        self.assertEqual(note["full_report_line_ending"], "CRLF")
        self.assertNotIn("rules", result["native_parameters"][M.KEY])
        self.assertEqual((self.out / "parameters.json").read_bytes(), M.report_bytes(result, "\r\n"))

    def test_no_status_headroom_keeps_exact_original_report_with_log(self):
        baseline = padded(self.base, M.REPORT_LIMIT)
        self.namespace["os"] = SimpleNamespace(linesep="\r\n")
        result, text = self.publish(baseline)
        self.assertEqual(self.note(text)["reason"], "report_budget")
        self.assertEqual(result, baseline)
        self.assertEqual((self.out / "parameters.json").read_bytes(), legacy_bytes(baseline, os.linesep))

    def test_real_source_byte_change_with_restored_size_mtime_refuses_publication(self):
        before = self.path.stat()
        raw = bytearray(self.raw)
        raw[-1] ^= 1
        self.path.write_bytes(raw)
        os.utime(self.path, ns=(before.st_atime_ns, before.st_mtime_ns))
        with self.assertRaises(S.SourceIdentityError):
            self.publish(report=padded(self.base, M.REPORT_LIMIT + 1))
        self.assertFalse((self.out / "parameters.json").exists())

    def test_metadata_identity_error_cannot_fall_back_to_oversized_legacy_report(self):
        inspection = copy.deepcopy(self.inspection)
        inspection["metadata"]["native_mdl_sha256"] = "0" * 64
        with self.assertRaises(M.SourceIdentityError):
            self.publish(report=padded(self.base, M.REPORT_LIMIT + 1), inspection=inspection)
        self.assertFalse((self.out / "parameters.json").exists())

    def test_final_recheck_precedes_planning_and_the_only_binary_write(self):
        events = []
        recheck, plan, write = S.recheck_selected_mdl, M.plan_report, Path.write_bytes
        def checked(capture):
            events.append("recheck")
            return recheck(capture)
        def planned(*args, **kwargs):
            events.append("plan")
            self.assertEqual(kwargs["expected_native_mdl_sha256"], self.capture.native_sha256)
            return plan(*args, **kwargs)
        def written(path, raw):
            events.append("write")
            return write(path, raw)
        with patch.object(S, "recheck_selected_mdl", side_effect=checked), \
                patch.object(M, "plan_report", side_effect=planned), patch.object(Path, "write_bytes", written):
            self.publish()
        self.assertEqual(events, ["recheck", "plan", "write"])

    def selected_namespace(self, events):
        mdl = SimpleNamespace(bones=[SimpleNamespace(name=row["name"], parent_id=row["parent"]) for row in self.bones],
                              skin_groups=[], flex_names=[], flex_controllers=[], body_parts=[])
        container = SimpleNamespace(mdl=mdl, bodygroups={})
        def file_buffer(path):
            events.append("FileBuffer")
            self.assertEqual(path, str(self.path))
            return path
        def load(path, buffer, scale, **kwargs):
            events.append("load_model")
            self.assertEqual((path, buffer, scale), (self.path, str(self.path), self.base["scale"]))
            return container
        return {"source": self.path, "request": {"sha256": ORIGINAL, "scale": self.base["scale"]},
                "source_mdl_snapshot": S, "source_jiggle_metadata": M, "source_appearance": SimpleNamespace(),
                "FileBuffer": file_buffer, "TinyPath": str, "load_model": load, "warnings": [],
                "CaseResolver": lambda _: SimpleNamespace(find=lambda _: None),
                "is_dataclass": lambda _: False, "native_parameters": {}, "jiggle_inspection": {"state": "none"},
                "selected_mdl_capture": None}

    def test_selected_mdl_captures_original_path_before_sourceio_and_inspects_complete_inventory(self):
        events = []
        namespace = self.selected_namespace(events)
        capture, inspect = S.capture_selected_mdl, M.inspect
        def captured(path):
            events.append("capture")
            self.assertEqual(path, str(self.path))
            return capture(path)
        def inspected(raw, original, native, bones, scale):
            events.append("inspect")
            self.assertEqual((raw, original, native, bones, scale),
                             (self.raw, ORIGINAL, self.capture.native_sha256, self.bones, self.base["scale"]))
            return inspect(raw, original, native, bones, scale)
        with patch.object(S, "capture_selected_mdl", side_effect=captured), patch.object(M, "inspect", side_effect=inspected):
            execute([SELECTED], namespace)
        self.assertEqual(events, ["capture", "FileBuffer", "load_model", "inspect"])
        self.assertEqual(namespace["jiggle_inspection"], self.inspection)
        self.assertEqual(namespace["selected_mdl_capture"].file.path, str(self.path))

    def test_selected_mdl_not_inspected_still_converts_without_numeric_inspection(self):
        events = []
        namespace = self.selected_namespace(events)
        unavailable = S.NotInspected("initial-selected-mdl-unreadable")
        with patch.object(S, "capture_selected_mdl", return_value=unavailable), \
                patch.object(M, "inspect", side_effect=AssertionError("not captured")):
            execute([SELECTED], namespace)
        self.assertEqual(events, ["FileBuffer", "load_model"])
        self.assertIs(namespace["selected_mdl_capture"], unavailable)
        self.assertEqual(namespace["jiggle_inspection"], {"state": "none"})

    def test_selected_capture_identity_error_prevents_sourceio_read(self):
        events = []
        namespace = self.selected_namespace(events)
        with patch.object(S, "capture_selected_mdl", side_effect=S.SourceIdentityError("authored source changed")):
            with self.assertRaises(S.SourceIdentityError):
                execute([SELECTED], namespace)
        self.assertEqual(events, [])

    def test_selected_inspection_identity_error_escapes_after_sourceio_read(self):
        events = []
        namespace = self.selected_namespace(events)
        namespace["request"]["sha256"] = "A" * 64
        with self.assertRaises(M.SourceIdentityError):
            execute([SELECTED], namespace)
        self.assertEqual(events, ["FileBuffer", "load_model"])
        self.assertFalse((self.out / "parameters.json").exists())

    def test_actual_final_publication_assignment_uses_the_frozen_context(self):
        self.namespace.update(report=self.base, selected_mdl_capture=self.capture, jiggle_inspection=self.inspection,
                              crosswalk_inspection=None)
        execute([PUBLICATION], self.namespace)
        retained = self.namespace["report"]["native_parameters"][M.KEY]
        self.assertEqual(retained["native_mdl_sha256"], hashlib.sha256(self.raw).hexdigest())
        self.assertEqual(retained["original_source_sha256"], ORIGINAL)
        self.assertFalse(retained["applied"])
        self.assertEqual(retained["binding_status"], "unattempted")


if __name__ == "__main__":
    unittest.main(verbosity=2)
