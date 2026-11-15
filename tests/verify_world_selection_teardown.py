"""Freeze source and verify pending GPU-pick teardown on a private desktop."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.build_owner_review_snapshot import freeze_source

CASES = ("controls-queue-free", "focus-free", "setup-free", "focus-detach")
BAD_LOG = ("ERROR:", "WARNING:", "FAIL ", "ObjectDB instances leaked",
           "Leaked instance:", "unclaimed string names at exit", "Orphan StringName:",
           "Pages in use exist at exit", "_set_transient_exclusive_child")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def receipt_for(command):
    path = Path(command[command.index("--receipt") + 1])
    return path, json.loads(path.read_bytes()) if path.exists() else {}


def private_closed(receipt):
    return (receipt.get("exit") == 0 and receipt.get("child_desktop_confirmed") is True
            and receipt.get("foreground_child_observed") is False
            and receipt.get("job_closed") is True and receipt.get("desktop_closed") is True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", help="Exact old-source counterfactual; the current test is shared")
    parser.add_argument("--case", action="append", choices=CASES)
    options = parser.parse_args()
    selected = list(dict.fromkeys(options.case or CASES))
    revision = (subprocess.check_output(["git", "rev-parse", "--verify", "--end-of-options",
                                        options.revision + "^{commit}"], cwd=ROOT, text=True).strip()
                if options.revision else None)
    folder = ROOT / "output/world-selection-teardown" / str(time.time_ns())
    folder.mkdir(parents=True)
    project = folder / "shipped-source"
    commit, hashes = freeze_source(ROOT, project, revision)
    if revision:
        assert commit == revision
    baseline = hashes.copy()
    profile = "HAS Pick Teardown " + str(time.time_ns())
    override = project / "override.cfg"
    override.write_text("[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name="
                        + json.dumps(profile) + "\n", encoding="utf-8")
    test = ROOT / "tests/world_selection_teardown.gd"
    target = project / "tests" / test.name
    target.parent.mkdir(exist_ok=True)
    target.write_bytes(test.read_bytes())
    hashes[target.relative_to(project).as_posix()] = digest(target)
    proof = {"revision": commit, "source_mode": "git_revision" if revision else "working_tree",
             "folder": str(folder), "profile": profile, "selected_cases": selected,
             "source_sha256": hashes, "baseline_source_sha256": baseline,
             "shared_test_sha256": digest(test), "driver_sha256": digest(Path(__file__)),
             "override_sha256": digest(override)}
    write_json(folder / "provenance.json", proof)
    spec = importlib.util.spec_from_file_location("pick_teardown_runner", project / "run.py")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)

    def execute(command, label, timeout):
        write_json(folder / (label + "-command.json"), command)
        process = subprocess.run(command, cwd=project, capture_output=True, text=True,
                                 encoding="utf-8", errors="replace", timeout=timeout)
        log = process.stdout + process.stderr
        (folder / (label + ".log")).write_text(log, encoding="utf-8")
        receipt_path, receipt = receipt_for(command)
        proof[label] = {"exit": process.returncode, "receipt_path": str(receipt_path), "receipt": receipt}
        proof["unchanged_source"] = all(digest(project / name) == value for name, value in hashes.items())
        proof["unchanged_override"] = digest(override) == proof["override_sha256"]
        write_json(folder / "verification.json", proof)
        return process, log

    startup_path = folder / "normal-startup.json"
    startup_command = runner.command(extra=["--verbose", "res://tests/current_candidate_startup.tscn",
                                            "--", str(startup_path)])
    startup_process, startup_log = execute(startup_command, "normal-startup", 60)
    startup = json.loads(startup_path.read_bytes()) if startup_path.exists() else {}
    proof["startup_result"] = startup
    write_json(folder / "verification.json", proof)
    assert startup_process.returncode == 0 and "CURRENT_REVIEW_STARTUP " in startup_log, startup_log
    assert not any(marker in startup_log for marker in BAD_LOG), startup_log
    assert startup.get("home_visible") and startup.get("simple") and startup.get("empty") and profile in startup.get("profile", ""), startup
    assert private_closed(proof["normal-startup"]["receipt"]), proof["normal-startup"]
    assert proof["unchanged_source"] and proof["unchanged_override"], proof

    command = runner.command("tests/" + test.name,
                             extra=["--verbose", "--log-file", str(folder / "engine.log"),
                                    "--", str(folder), *selected])
    process, log = execute(command, "process", 110)
    result_path = folder / "result.json"
    proof["result"] = json.loads(result_path.read_bytes()) if result_path.exists() else {}
    write_json(folder / "verification.json", proof)
    assert process.returncode == 0 and "WORLD_SELECTION_TEARDOWN " in log, log
    assert not any(marker in log for marker in BAD_LOG), log
    result = proof["result"]
    assert result.get("failures") == 0 and result.get("checks", 0) > 0, result
    assert [case["case"] for case in result.get("cases", [])] == [case for case in CASES if case in selected], result
    assert proof["unchanged_source"] and proof["unchanged_override"], proof
    assert private_closed(proof["process"]["receipt"]), proof["process"]
    write_json(ROOT / "output/world-selection-teardown-latest.json", proof)
    print(json.dumps({key: value for key, value in proof.items()
                      if key not in ("source_sha256", "baseline_source_sha256")}, indent=2))


if __name__ == "__main__":
    main()
