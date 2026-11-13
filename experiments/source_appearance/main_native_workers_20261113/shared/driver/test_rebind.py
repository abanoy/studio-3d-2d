"""Focused CPU rebind controls; never permit a converter/private/GPU child."""
import argparse
import copy
import json
from pathlib import Path
import sys
import time
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
TASK = Path(__file__).absolute().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("mode", choices=("core", "wider"))
mode = parser.parse_args().mode
sys.path.insert(0, str(TASK / ("core-source" if mode == "core" else "wider-source")))
import background_conversion_driver as D
import background_route as BG

LOCK_PATH = TASK / ("conversion-inputs-core2.json" if mode == "core" else "conversion-inputs-wide2.json")
LOCK = D.read_json(LOCK_PATH)
PLAN = D.read_json(TASK / "REBIND_PLAN.json")
ACTUAL_REVISION = D.head()
OUT = TASK / ("rebind-cpu-" + mode + "-" + str(time.time_ns()))
OUT.mkdir(exist_ok=False)
BEFORE = {str(p): D.S.identity(p) for p in (Path(D.__file__), Path(BG.__file__), Path(__file__), LOCK_PATH)}

class RebindTests(unittest.TestCase):
    def test_actual_new_context_and_committed_revision(self):
        self.assertEqual(D.TASK, TASK)
        self.assertEqual(D.ROOT, TASK.parents[1])
        self.assertEqual(ACTUAL_REVISION, "cf7a805dd6ec76890da048ff28aa0080757e7c34")
        self.assertEqual(LOCK["root_revision"], ACTUAL_REVISION)

    def test_six_explicit_worker_sources_include_new_archive_and_bridge(self):
        self.assertEqual(len(D.WORKERS), 6)
        self.assertEqual(len(BG.WORKER_SHA), 6)
        for name, expected in PLAN["six_explicit_worker_source_expectations"].items():
            self.assertEqual(D.S.identity(D.ROOT / name), expected)
            self.assertEqual(D.WORKERS[name], expected["sha256"])
            self.assertEqual(BG.WORKER_SHA[str(D.ROOT / name)], expected["sha256"])
        self.assertEqual(D.WORKERS["tools/source_archive.py"], "44fc9c9ca6d3b81aa34d72634f3a23d57624d0e96c57599f3c03b9e7af4cc131")
        self.assertEqual(D.WORKERS["tools/blender_source_bridge.py"], "e885074a2cb8c21976b25429e9c09c43c976eca760b835bc4b295fcac6185f4d")

    def test_exact_updated_seventeen_scope_and_only_two_old_changes(self):
        self.assertEqual(len(LOCK["main_python_sources"]), 17)
        self.assertEqual(D.functional(D.ROOT), LOCK["main_python_sources"])
        changed = {name for name, row in PLAN["old_scoped_main_python"].items() if LOCK["main_python_sources"][name] != row}
        self.assertEqual(changed, {"tools/source_archive.py", "tools/blender_source_bridge.py"})

    def test_old_driver_request_metadata_locks_preserved(self):
        for path, expected in PLAN["preserved_old_metadata_driver_request_lock_inputs"].items():
            self.assertEqual(D.S.identity(Path(path)), expected)

    def test_native_inputs_not_relocated_or_restaged(self):
        self.assertEqual(len(LOCK["staged_members"]), 296 if mode == "core" else 265)
        self.assertEqual(str(D.INPUT_STAGE), PLAN["core_input_stage" if mode == "core" else "wider_input_stage"])
        self.assertFalse((TASK / "stage").exists())

    def test_schedule_commands_and_requests_owned_and_nonlaunching(self):
        self.assertEqual(len(LOCK["schedule"]), 14 if mode == "core" else 11)
        self.assertEqual(sum(not row["expected_success"] for row in LOCK["schedule"]), 2 if mode == "core" else 1)
        for i, row in enumerate(LOCK["schedule"]):
            case, bundle, args, private = D.commands(row, i, OUT)
            self.assertIsNone(private)
            self.assertFalse(case.exists())
            BG.native_options(args, case)
            if row["request"]:
                self.assertTrue(Path(row["request"]).is_relative_to(TASK / ("requests" if mode == "core" else "wider-requests")))

    def test_synthetic_worker_request_mount_and_appearance_contract(self):
        cases = {case["case"]: case for case in LOCK["cases"]}
        for i, row in enumerate(LOCK["schedule"]):
            case = cases[row["case"]]; bundle = OUT / ("synthetic-" + str(i)); bundle.mkdir()
            root = D.INPUT_STAGE / row["case"] / case["native_member"].split("/")[0] if mode == "core" else Path(case["resource_root"])
            request = {"original_source": row["source"], "source": str(bundle / "native" / Path(row["source"]).name),
                "sha256": case["native_mdl_sha256"], "source_member": None, "output": str(bundle), "sourceio": str(D.SOURCEIO),
                "sourceio_revision": D.PIN, "source_profile": "standalone", "gmod_installation": None,
                "mounts": [str(bundle / "native"), str(root)]}
            if row["selection"] is not None: request["appearance"] = D.read_json(Path(row["request"]))
            D.S.save(bundle / "conversion-request.json", request)
            D.verify_conversion_request(bundle, row, case)
            foreign = copy.deepcopy(request); foreign["mounts"][-1] = r"C:\Program Files (x86)\Steam\steamapps\common"
            with patch.object(D, "read_json", return_value=foreign):
                with self.assertRaisesRegex(ValueError, "mounted unowned"):
                    D.verify_conversion_request(bundle, row, case)

    def test_changed_archival_source_provenance_refused(self):
        hashes = copy.deepcopy(LOCK["background_sources"])
        hashes[str(D.ROOT / "tools/source_archive.py")] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source changed"):
            BG.source_observation(hashes)

    def test_no_lease_refuses_before_any_process(self):
        with self.assertRaisesRegex(ValueError, "explicit lease"):
            D.main(["--input-lock", str(LOCK_PATH), "--lock-sha256", "0" * 64, "--run-conversions"])

if __name__ == "__main__":
    with patch.object(D.subprocess, "Popen", side_effect=AssertionError("Focused CPU controls cannot launch a process")):
        # Actual Git revision was observed before this no-process boundary.
        with patch.object(D, "head", return_value="cf7a805dd6ec76890da048ff28aa0080757e7c34"):
            result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(RebindTests))
    unchanged = all(D.S.identity(Path(path)) == row for path, row in BEFORE.items())
    report = {"format": "has_native_main_rebind_cpu_1", "mode": mode, "checks": result.testsRun,
        "failures": len(result.failures), "errors": len(result.errors), "passed": result.wasSuccessful() and unchanged,
        "source_lock_test_before_after": BEFORE, "unchanged": unchanged, "converter_private_nativeviewer_gpu_launched": False, "run": str(OUT)}
    D.S.save(OUT / "verification.json", report)
    print(json.dumps({key: report[key] for key in ("mode", "checks", "failures", "errors", "passed", "unchanged", "run")}))
    raise SystemExit(0 if report["passed"] else 1)
