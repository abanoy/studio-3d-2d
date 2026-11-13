"""Nonlaunching integration controls plus retained unchanged driver guards."""
import hashlib
import json
from pathlib import Path
import sys
import time
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
import background_conversion_driver as Candidate
import background_route as BG
import test_conversion_driver as Previous

ARTIFACTS = BG.TASK / ("background-driver-cpu-" + str(time.time_ns()))
ARTIFACTS.mkdir(exist_ok=False)
BASE_ARTIFACTS = ARTIFACTS / "retained-guards"
BASE_ARTIFACTS.mkdir()


class IntegrationTests(unittest.TestCase):
    def test_previous_driver_private_tool_and_four_worker_files_unchanged(self):
        original = BG.TASK / "source/conversion_driver.py"
        self.assertEqual(BG.S.identity(original)["sha256"], "d8749db85f324f799740c2802a77e7ec6d8640f0752312fe7ecfdf34cee2d127")
        old = json.loads((BG.TASK / "conversion-inputs-reviewed2.json").read_bytes())
        self.assertEqual(BG.S.identity(BG.PRIVATE), old["files"][str(BG.PRIVATE)])
        for source, digest in BG.WORKER_SHA.items():
            self.assertEqual(BG.S.identity(Path(source))["sha256"], digest)

    def test_preflight_vector_requires_fresh_materialization_not_old_graphical_route(self):
        plan = Candidate.read_json(BG.TASK / "plan.json")
        arrays = Candidate.read_json(BG.TASK / "commands-for-owned-stage.json")
        rows = Candidate.schedule(plan, arrays)
        self.assertEqual(len(rows), 14)
        folder = ARTIFACTS / "unmaterialized"
        folder.mkdir()
        for index, row in enumerate(rows):
            case, bundle, native, private = Candidate.commands(row, index, folder)
            self.assertIsNone(private)
            self.assertFalse(case.exists())
            BG.native_options(native, case)

    def test_historical_schema2_cannot_launch_background_candidate(self):
        with patch.object(Candidate.subprocess, "Popen", side_effect=AssertionError("must never launch")):
            with self.assertRaisesRegex(ValueError, "Input-lock schema changed"):
                Candidate.main(["--input-lock", str(BG.TASK / "conversion-inputs-reviewed2.json"),
                                "--lock-sha256", "04f512123be32356b637b67fd83b78dda8a842469c4a367739d02e482b4f51c6",
                                "--run-conversions", "--lease-confirmed"])

    def test_refusal_needs_independent_background_proof(self):
        folder = ARTIFACTS / "refusal"
        folder.mkdir(); (folder / "conversion.log").write_text(Candidate.REFUSAL)
        receipt = {"exit": 1, "child_desktop_confirmed": False}
        for proof in [{}, {"passed": False}, {"passed": True, "expected_worker_exit": 0}]:
            with self.subTest(proof=proof), self.assertRaisesRegex(ValueError, "dual background"):
                Candidate.refused(1, receipt, folder, Candidate.REFUSAL, proof)
        proof = {"passed": True, "expected_worker_exit": 1}
        Candidate.refused(1, receipt, folder, Candidate.REFUSAL, proof)
        with self.assertRaises(ValueError): Candidate.refused(1, receipt, folder, "different failure", proof)


if __name__ == "__main__":
    excluded = {"test_candidate_commands_are_fresh_owned_and_private",
                "test_private_receipt_requires_owned_closed_job_and_desktop",
                "test_all_blank_refusal_needs_exact_reason_and_no_glb"}
    retained = [name for name in unittest.defaultTestLoader.getTestCaseNames(Previous.DriverTests) if name not in excluded]
    suite = unittest.TestSuite([Previous.DriverTests(name) for name in retained])
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(IntegrationTests))
    with patch.object(Previous, "D", Candidate), patch.object(Previous, "ARTIFACTS", BASE_ARTIFACTS):
        result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {"format": "has_background_candidate_driver_cpu_1", "checks": result.testsRun, "retained_guard_checks": len(retained),
              "failures": len(result.failures), "errors": len(result.errors), "skips": len(result.skipped),
              "artifact_folder": str(ARTIFACTS), "private_desktop_blender_gpu_native_worker_launched": False,
              "synthetic_geometry_and_dependency_data_only": True, "automatic_cleanup": False}
    BG.S.save(ARTIFACTS / "verification.json", report); print(json.dumps(report), flush=True)
    raise SystemExit(0 if result.wasSuccessful() else 1)
