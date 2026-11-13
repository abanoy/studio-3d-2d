"""CPU controls only: no private desktop, Blender, worker or GPU launch."""
import copy
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
import time
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
import background_route as BG
import conversion_driver as D

ARTIFACTS = BG.TASK / ("background-route-cpu-" + str(time.time_ns()))
ARTIFACTS.mkdir(exist_ok=False)


def fixture():
    case = BG.TASK / "synthetic-contract-case"
    native = [str(BG.PYTHON), "-B", "-u", str(BG.PREPARE), str(BG.TASK / "stage/multi_skin_glove/pkg/models/glove.mdl"),
              "--output", str(case / "bundle"), "--sourceio", str(BG.SOURCEIO), "--blender", str(BG.BLENDER),
              "--mount-plan", str(BG.TASK / "empty-mount-plan.json"), "--gmod", str(case / "absent-gmod"), "--workshop", str(case / "absent-workshop")]
    request = {"format": "has_background_python_request_1", "case": str(case), "nonce": "1" * 32,
               "root_revision": "2" * 40, "input_lock_sha256": "3" * 64, "earliest_filetime": 1000,
               "expected_window_station": "WinSta0", "native_command": native,
               "sources": {source: BG.WORKER_SHA.get(source, "4" * 64) for source in BG.REQUIRED_SOURCES},
               "executables": {"python": {"path": str(BG.PYTHON), "sha256": "5" * 64}, "blender": {"path": str(BG.BLENDER), "sha256": "6" * 64}}}
    private = {"format": "studio_private_desktop_1", "desktop": "HAS_Test_" + "7" * 32, "exit": 0, "child_pid": 20,
               "job_closed": True, "desktop_closed": True, "foreground_child_observed": False,
               "desktop_switch_requested": False, "child_desktop_confirmed": False, "private_window_seen": False}
    def attest(role, pid, parent, created, parent_created, observed, digest):
        return {"format": "has_background_desktop_attestation_1", "role": role, "nonce": request["nonce"],
                "root_revision": request["root_revision"], "input_lock_sha256": request["input_lock_sha256"],
                "request_sha256": digest, "sources": request["sources"],
                "self": {"api": "WinAPI self observation", "pid": pid, "thread_id": pid + 1, "parent_pid": parent,
                         "creation_filetime": created, "parent_creation_filetime": parent_created, "observed_filetime": observed,
                         "desktop": private["desktop"], "window_station": "WinSta0", "executable": request["executables"][role]["path"],
                         "executable_sha256": request["executables"][role]["sha256"], "observation_created_windows": False, "observation_switched_desktop": False}}
    python = attest("python", 20, 10, 2000, 1500, 3000, "8" * 64)
    blender = attest("blender", 30, 20, 4000, 2000, 5000, "9" * 64)
    command = BG.blender_command(request, case / "bundle/conversion-request.json")
    changed = list(command); changed[changed.index("--python") + 1] = str(BG.OBSERVER)
    spawn = {"format": "has_background_blender_spawn_1", "nonce": request["nonce"], "python_request_sha256": "8" * 64,
             "python_pid": 20, "python_creation_filetime": 2000, "blender_pid": 30, "blender_creation_filetime": 4000,
             "observer_request_sha256": "9" * 64, "conversion_request_sha256": "a" * 64,
             "original_command": command, "observed_command": changed, "observed_filetime": 4500}
    outer = {"format": "has_background_outer_launch_1", "nonce": request["nonce"], "pid": 10, "creation_filetime": 1500}
    python_done = {"format": "has_background_completion_1", "role": "python", "nonce": request["nonce"], "worker_exit": 0,
                   "intercepted_blender_commands": 1, "exception": None, "observed_filetime": 7000, "sources_after": request["sources"]}
    blender_done = {"format": "has_background_completion_1", "role": "blender", "nonce": request["nonce"], "status": "ok",
                    "exception": None, "observed_filetime": 6000, "sources_after": request["sources"], "conversion_request_sha256": "a" * 64}
    python_done["native_import_origins"] = BG.expected_native_imports("python", request["sources"])
    blender_done["native_import_origins"] = BG.expected_native_imports("blender", request["sources"])
    return [request, "8" * 64, private, python, blender, spawn, outer, python_done, blender_done, {"blender_pid": 30}, 10000]


class BackgroundTests(unittest.TestCase):
    def folder(self):
        value = ARTIFACTS / self._testMethodName; value.mkdir(exist_ok=False); return value

    def test_complete_dual_attestation_does_not_forge_monitor_flag(self):
        args = fixture(); original = copy.deepcopy(args[2]); result = BG.validate_proof(*args)
        self.assertTrue(result["passed"])
        self.assertFalse(result["private_monitor_child_desktop_confirmed"])
        self.assertFalse(result["original_private_receipt_edited"])
        self.assertEqual(args[2], original)

    def test_old_exit2_never_becomes_clean(self):
        args = fixture(); args[2].update(exit=2, error="No owned graphical window was verified on the private desktop")
        with self.assertRaisesRegex(ValueError, "exit was not clean"): BG.validate_proof(*args)
        old = BG.TASK / "conversion-run-1794544819819957800/01-multi_skin_glove-default-no-appearance/private-receipt.json"
        args = fixture(); args[2] = json.loads(old.read_bytes())
        with self.assertRaises(ValueError): BG.validate_proof(*args)

    def test_missing_python_or_blender_attestation_refuses(self):
        for index in [3, 4]:
            args = fixture(); args[index] = {}
            with self.subTest(index=index), self.assertRaises(ValueError): BG.validate_proof(*args)

    def test_wrong_desktop_or_station_refuses_both_roles(self):
        for index in [3, 4]:
            for key, value in [("desktop", "Default"), ("desktop", "HAS_Test_" + "b" * 32), ("window_station", "Other")]:
                args = fixture(); args[index]["self"][key] = value
                with self.subTest(index=index, key=key), self.assertRaises(ValueError): BG.validate_proof(*args)

    def test_wrong_nonce_checkpoint_request_or_source_hash_refuses(self):
        for index in [3, 4]:
            for key in ["nonce", "root_revision", "input_lock_sha256", "request_sha256", "sources"]:
                args = fixture(); args[index] = copy.deepcopy(args[index]); args[index][key] = {} if key == "sources" else "wrong"
                with self.subTest(index=index, key=key), self.assertRaises(ValueError): BG.validate_proof(*args)

    def test_stale_future_creation_or_observation_refuses(self):
        for index in [3, 4]:
            for key, value in [("creation_filetime", 999), ("creation_filetime", 10001), ("observed_filetime", 10001), ("observed_filetime", 100)]:
                args = fixture(); args[index]["self"][key] = value
                with self.subTest(index=index, key=key, value=value), self.assertRaises(ValueError): BG.validate_proof(*args)

    def test_wrong_pid_parent_thread_or_creation_identity_refuses(self):
        for index, key in [(3, "pid"), (3, "parent_pid"), (3, "parent_creation_filetime"), (4, "pid"), (4, "parent_pid"), (4, "parent_creation_filetime"), (4, "creation_filetime"), (4, "thread_id")]:
            args = fixture(); args[index]["self"][key] = 0
            with self.subTest(index=index, key=key), self.assertRaises(ValueError): BG.validate_proof(*args)

    def test_executable_path_or_hash_refuses(self):
        for index in [3, 4]:
            for key, value in [("executable", r"C:\unexpected.exe"), ("executable_sha256", "f" * 64)]:
                args = fixture(); args[index]["self"][key] = value
                with self.subTest(index=index, key=key), self.assertRaises(ValueError): BG.validate_proof(*args)

    def test_unclosed_job_desktop_foreground_or_switch_refuses(self):
        for key, value in [("job_closed", False), ("desktop_closed", False), ("foreground_child_observed", True), ("desktop_switch_requested", True)]:
            args = fixture(); args[2][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): BG.validate_proof(*args)

    def test_wrong_spawn_or_native_worker_pid_refuses(self):
        for index, key, value in [(5, "blender_pid", 31), (5, "python_request_sha256", "wrong"), (5, "nonce", "wrong"), (6, "pid", 11), (9, "blender_pid", 31)]:
            args = fixture(); args[index][key] = value
            with self.subTest(index=index, key=key), self.assertRaises(ValueError): BG.validate_proof(*args)

    def test_changed_native_command_or_observer_instrumentation_refuses(self):
        for key in ["original_command", "observed_command"]:
            args = fixture(); args[5][key].append("--unexpected")
            with self.subTest(key=key), self.assertRaises(ValueError): BG.validate_proof(*args)

    def test_missing_stale_or_wrong_completion_refuses(self):
        for index in [7, 8]:
            for key, value in [("nonce", "wrong"), ("sources_after", {}), ("observed_filetime", 10001)]:
                args = fixture(); args[index][key] = value
                with self.subTest(index=index, key=key), self.assertRaises(ValueError): BG.validate_proof(*args)
        args = fixture(); args[7]["intercepted_blender_commands"] = 2
        with self.assertRaises(ValueError): BG.validate_proof(*args)

    def test_expected_refusal_still_requires_dual_observation_and_exception(self):
        args = fixture(); args[2]["exit"] = args[7]["worker_exit"] = 1
        args[8].update(status="exception", exception={"type": "ValueError", "message": D.REFUSAL})
        self.assertEqual(BG.validate_proof(*args)["expected_worker_exit"], 1)
        args[8]["exception"] = None
        with self.assertRaises(ValueError): BG.validate_proof(*args)
        args = fixture(); args[7]["worker_exit"] = True
        with self.assertRaises(ValueError): BG.validate_proof(*args)

    def test_frozen_source_hash_guard_reads_without_executing(self):
        hashes = {source: BG.S.identity(Path(source))["sha256"] for source in BG.REQUIRED_SOURCES}
        self.assertEqual(BG.source_observation(hashes), hashes)
        bad = dict(hashes); bad[str(BG.BRIDGE)] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source changed"): BG.source_observation(bad)

    def test_original_script_import_path_and_cached_helpers_are_restored(self):
        hashes = {source: BG.S.identity(Path(source))["sha256"] for source in BG.REQUIRED_SOURCES}
        original_path = list(sys.path); original_archive = sys.modules.get("source_archive")
        with BG.native_import_context("python", hashes) as observe:
            for name in BG.NATIVE_MODULES["python"]:
                importlib.import_module(name)
            self.assertEqual(observe(), BG.expected_native_imports("python", hashes))
            self.assertIsNot(sys.modules["source_archive"], original_archive)
        self.assertEqual(sys.path, original_path)
        self.assertIs(sys.modules.get("source_archive"), original_archive)

    def test_changed_import_provenance_refuses(self):
        args = fixture(); args[7]["native_import_origins"] = {}
        with self.assertRaisesRegex(ValueError, "import provenance"): BG.validate_proof(*args)

    def test_exact_native_argument_guard_rejects_extra_content_or_runtime(self):
        request = fixture()[0]; case = Path(request["case"])
        BG.native_options(request["native_command"], case)
        bad = request["native_command"] + ["--content", r"C:\installed"]
        with self.assertRaises(ValueError): BG.native_options(bad, case)
        bad = list(request["native_command"]); bad[bad.index("--blender") + 1] = r"C:\other.exe"
        with self.assertRaises(ValueError): BG.native_options(bad, case)

    def test_only_observation_script_and_two_environment_keys_change(self):
        folder = self.folder(); (folder / "bundle").mkdir(); BG.S.save(folder / "bundle/conversion-request.json", {"fixture": True})
        request = fixture()[0]; python = fixture()[3]
        command = BG.blender_command(request, folder / "bundle/conversion-request.json")
        environment = {"UNCHANGED": "value"}
        changed, env, digest = BG.instrument_blender(command, request, folder, python, "8" * 64, environment)
        differences = [index for index, pair in enumerate(zip(command, changed)) if pair[0] != pair[1]]
        self.assertEqual(differences, [command.index("--python") + 1])
        self.assertEqual(env["UNCHANGED"], "value")
        self.assertEqual(set(env) - set(environment), {"HAS_BACKGROUND_OBSERVER_REQUEST", "HAS_BACKGROUND_OBSERVER_SHA256"})
        self.assertEqual(len(digest), 64)

    def test_observer_refuses_nonexact_subprocess_before_launch(self):
        request = fixture()[0]; folder = self.folder()
        with self.assertRaisesRegex(ValueError, "Unreviewed subprocess"):
            BG.instrument_blender([str(BG.BLENDER), "--background"], request, folder, fixture()[3], "8" * 64, {})

    def test_fresh_file_guard_rejects_stale_copy(self):
        folder = self.folder(); path = folder / "proof.json"; BG.S.save(path, {"synthetic": True})
        now = time.time_ns() // 100 + 116444736000000000
        BG.read_fresh(folder, "proof.json", now - 10000000, now + 10000000)
        old = time.time_ns() - 10 * 1000000000; os.utime(path, ns=(old, old))
        with self.assertRaisesRegex(ValueError, "Stale"): BG.read_fresh(folder, "proof.json", now - 10000000, now + 10000000)

    def test_actual_default_desktop_probe_is_not_private_proof(self):
        path = BG.TASK / "background-own-desktop-self-probe.json"
        probe = json.loads(path.read_bytes())
        self.assertTrue(probe["self_probe_only"])
        self.assertFalse(probe["private_desktop_or_blender_launched"])
        self.assertEqual(probe["observation"]["desktop"], "Default")
        request = fixture()[0]
        with patch.object(BG.Win, "capture_self", return_value=probe["observation"]):
            with self.assertRaisesRegex(ValueError, "not on a fresh private desktop"):
                # Match executable actual hash so the desktop condition is reached.
                request["executables"]["python"]["sha256"] = probe["observation"]["executable_sha256"]
                BG.observation("python", request, "8" * 64)

    def test_background_run_without_lease_never_launches(self):
        with patch.object(BG.subprocess, "Popen", side_effect=AssertionError("must not launch")):
            with self.assertRaisesRegex(ValueError, "explicit Windows conversion lease"):
                BG.run_outer({}, Path("unused"), Path("unused"), {}, lease_confirmed=False)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(BackgroundTests))
    report = {"format": "has_background_route_cpu_controls_1", "checks": result.testsRun, "failures": len(result.failures),
              "errors": len(result.errors), "skips": len(result.skipped), "artifact_folder": str(ARTIFACTS),
              "private_desktop_blender_gpu_native_worker_launched": False, "synthetic_attestations": True,
              "own_readonly_default_desktop_probe_separate": True, "automatic_cleanup": False}
    BG.S.save(ARTIFACTS / "verification.json", report); print(json.dumps(report), flush=True)
    raise SystemExit(0 if result.wasSuccessful() else 1)
