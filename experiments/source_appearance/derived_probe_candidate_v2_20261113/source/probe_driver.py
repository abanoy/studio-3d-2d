"""Output-only SFM derived render/adoption candidate. Default never launches GPU.

Preparation binds twelve retained bundles and creates fresh exact-commit source
copies. Actual graphics require a reviewed manifest/hash and an exclusive lease.
"""
from __future__ import annotations
import argparse
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import time
import uuid

sys.dont_write_bytecode = True
from glb_reference import GLB, bounds, require, sha

TASK = Path(__file__).absolute().parents[1]
ROOT = TASK.parents[1]
ORIGINAL_RUN = ROOT / "output/sfm-next-cases-20261112/conversion-run-1794546473806155800"
RESULTS = ROOT / "output/sfm-next-cases-20261112/BACKGROUND3-ACTUAL-RESULTS.json"
RESULTS_SHA = "8bfa2071c9cc6846c9972d53ce93ce433fd8b46293b9155409fcef00f8f97478"
NATIVE_REVIEW = ROOT / "experiments/source_appearance/actual_windows_20261113/metadata/next_probe_compact.json"
PYTHON = Path(r"C:\Program Files\Python313\python.exe")
PYTHONW = Path(r"C:\Program Files\Python313\pythonw.exe")
GODOT = Path(r"C:\a\tools\Godot\Godot_v4.6-stable_win64.exe")
HARNESS = ("raw_probe.gd", "app_probe.gd")
CODE = ("probe_driver.py", "glb_reference.py", "test_probe_cpu.py", *HARNESS)
CASES = ((1, "nitori-default"), (2, "keiki-default"), (3, "nitori-skin-0"), (4, "keiki-000"),
         (5, "nitori-skin-1"), (6, "nitori-skin-2"), (7, "keiki-001"), (8, "keiki-010"),
         (9, "keiki-011"), (10, "keiki-100"), (11, "keiki-101"), (12, "keiki-110"))
BAD_LOG = ("ERROR:", "WARNING:", "FAIL ", "ObjectDB instances leaked", "Leaked instance:",
           "unclaimed string names at exit", "Orphan StringName:", "Pages in use exist at exit")


def no_reparse(path):
    path = Path(path).absolute()
    for parent in (path, *path.parents):
        if parent.exists():
            info = parent.lstat()
            require(not stat.S_ISLNK(info.st_mode) and not info.st_file_attributes & 0x400,
                    "Reparse/link path refused: " + str(parent))
    return path


def owned(path):
    path = no_reparse(path)
    require(path.resolve().is_relative_to(TASK.resolve()) and path.resolve() != TASK.resolve(),
            "Output must remain inside the dedicated task")
    return path


def stamp(path):
    path = no_reparse(path)
    require(path.is_file(), "Required file missing: " + str(path))
    info = path.stat()
    return {"path": str(path), "bytes": info.st_size, "mtime_ns": info.st_mtime_ns, "sha256": sha(path.read_bytes())}


def unchanged(record):
    return stamp(Path(record["path"])) == record


def read_json(path, maximum=8*1024*1024):
    path = no_reparse(path)
    require(path.stat().st_size <= maximum, "Metadata byte budget")
    return json.loads(path.read_bytes())


def write_new(path, value):
    path = owned(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def head():
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def root_functional():
    names = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z", "--", "src", "tests", "tools", "run.py",
                                     "launch.pyw", "main.tscn", "project.godot"], cwd=ROOT).decode().split("\0")
    return {name: stamp(ROOT / name) for name in sorted(set(n for n in names if n))}


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def source_members(project):
    no_reparse(project)
    result = {}
    for path in project.rglob("*"):
        no_reparse(path)
        if path.is_file() and not any(p in ("output", ".godot", "__pycache__") for p in path.relative_to(project).parts):
            result[str(path.relative_to(project)).replace("\\", "/")] = sha(path.read_bytes())
    return result


def material_rows(glb):
    return glb.materials()


def prepare(expected_revision, working_source=False, working_context=None):
    require(len(expected_revision) == 40 and all(c in "0123456789abcdef" for c in expected_revision), "Exact commit required")
    require(head() == expected_revision, "Root HEAD differs from reviewed preparation checkpoint")
    require(not working_source or bool(working_context), "Working-source preparation requires its explicit reviewed context")
    no_reparse(TASK)
    require(TASK == ROOT / "output/sfm-static-appearance-probe-20261113-v2", "Unexpected dedicated layout")
    proof = read_json(RESULTS)
    require(stamp(RESULTS)["sha256"] == RESULTS_SHA, "Exact retained fourteen-case proof hash differs")
    require(proof["passed_cases"] == 14 and proof["successful_bundles"] == 12 and proof["failed_cases"] == 0,
            "Retained actual conversion result is not accepted fourteen-case evidence")
    token = str(time.time_ns())+"-"+uuid.uuid4().hex
    folder = owned(TASK / "runs" / token)
    folder.mkdir(parents=True, exist_ok=False)
    protected = [stamp(RESULTS), stamp(NATIVE_REVIEW), stamp(ROOT / "tools/build_owner_review_snapshot.py"),
                 stamp(PYTHON), stamp(PYTHONW), stamp(GODOT), *(stamp(TASK / "source" / name) for name in CODE)]
    manifest = {"format": "has_sfm_derived_probe_candidate_2", "status": "PREPARED_NOT_RUN",
                "run_folder": str(folder), "root": str(ROOT), "root_revision": expected_revision,
                "source_mode": "working_tree_at_git_base" if working_source else "exact_git_revision",
                "working_context": working_context if working_source else None,
                "copied_source_is_exact_git_revision": not working_source,
                "nonce": token, "actual_conversion_root": proof["root_revision"],
                "scope": {"structure": "retained actual derived GLBs", "render": "UNRUN",
                          "app": "UNRUN", "native_fidelity": "UNTESTED",
                          "limits": ["missing Nitori native hairbump", "native additive/Phong/envmap/warp not reproduced",
                                     "coincident opaque glow retained, may obscure base", "no Source VTX/VVD/VTF independent oracle",
                                     "raw reference is derived glTF, not original SFM"]},
                "cases": [], "projects": {}, "render_cases": [], "profiles": {}, "protected": protected,
                "root_functional": root_functional()}
    selected = [case for case in proof["cases"] if case["expected_success"]]
    require(len(selected) == len(CASES), "Expected exact twelve successful bundles")
    glbs = {}
    for (number, key), actual in zip(CASES, selected):
        matches = list(ORIGINAL_RUN.glob(f"{number:02d}-*"))
        require(len(matches) == 1 and matches[0].is_dir(), "Ambiguous retained bundle folder")
        original = matches[0]
        verification = original / "verification.json"
        require(stamp(verification)["sha256"] == actual["verification"]["sha256"], "Case verification differs")
        verified = read_json(verification)
        target = owned(folder / "inputs" / key)
        target.mkdir(parents=True, exist_ok=False)
        inputs = {}
        for filename, expected in (("scene.glb", actual["glb"]), ("parameters.json", verified["parameters"]),
                                   ("dependencies.json", verified["dependencies"])):
            path = original / "bundle" / filename
            before = stamp(path)
            require(before["sha256"] == expected["sha256"] and before["bytes"] == expected["bytes"], "Bundle input differs")
            protected.append(before)
            destination = target / filename
            with destination.open("xb") as output:
                output.write(path.read_bytes())
            require(sha(destination.read_bytes()) == before["sha256"], "Input copy changed")
            inputs[filename] = stamp(destination)
        protected.append(stamp(verification))
        parameters = read_json(target / "parameters.json")
        glb = GLB((target / "scene.glb").read_bytes())
        glbs[key] = glb
        native_bones = parameters["native_parameters"]["bones"]
        bindings = glb.native_bindings(native_bones)
        native_index = 8 if key.startswith("nitori") else 23
        bone_name = "bip_hand_L" if key.startswith("nitori") else "box"
        require(native_bones[native_index]["name"] == bone_name, "Chosen native binding differs")
        summary = [{k: v for k, v in p.items() if k != "positions"} | {"used_vertices": len(p["positions"])}
                   for p in glb.positions()]
        manifest["cases"].append({"key": key, "input_glb": str(target / "scene.glb"), "inputs": inputs,
                                  "glb_sha256": inputs["scene.glb"]["sha256"], "parameters": parameters,
                                  "selected_skin": actual.get("selected_skin"),
                                  "selected_bodygroups": actual.get("selected_native_bodygroup_indices"),
                                  "bones": len(native_bones), "pose_bone_name": bone_name,
                                  "pose_native_index": native_index, "pose_source_node": bindings[native_index]["source_node"],
                                  "native_to_actual_glb_bindings": bindings,
                                  "materials": material_rows(glb), "primitives": summary})
    for key in ("nitori-skin-0", "nitori-skin-1", "nitori-skin-2"):
        manifest["render_cases"].append({"key": key+"-rest", "case": key})
    for weight in (0., .5, 1.):
        manifest["render_cases"].append({"key": "keiki-tools-"+str(weight), "case": "keiki-000", "morph_weight": weight})
    for key in ("keiki-000", "nitori-skin-0"):
        row = next(c for c in manifest["cases"] if c["key"] == key)
        manifest["render_cases"].append({"key": key+"-pose", "case": key, "pose_node": row["pose_source_node"],
                                         "pose_quaternion": [math.sin(math.radians(10)), 0., 0., math.cos(math.radians(10))]})
    references = {}
    for capture in manifest["render_cases"]:
        refs = glbs[capture["case"]].positions(capture.get("morph_weight"), capture.get("pose_node"), capture.get("pose_quaternion"))
        references[capture["key"]] = refs
        capture["bounds"] = bounds(refs)
    reference_observations = []
    pairs = [("keiki-tools-0.0", "keiki-tools-1.0", "tools.dmx"),
             ("keiki-tools-0.0", "keiki-000-pose", "box.smd"),
             ("nitori-skin-0-rest", "nitori-skin-0-pose", "gloves.dmx")]
    for before_key, after_key, affected_mesh in pairs:
        before, after = references[before_key], references[after_key]
        require([(p["source_node"], p["primitive"]) for p in before] ==
                [(p["source_node"], p["primitive"]) for p in after], "Reference primitive identity changed")
        moved, unchanged_count, maximum = 0, 0, 0.
        for first, last in zip(before, after):
            require(len(first["positions"]) == len(last["positions"]), "Reference point count changed")
            for p0, p1 in zip(first["positions"], last["positions"]):
                distance = math.dist(p0, p1)
                if first["source_name"] != affected_mesh:
                    require(p0 == p1, "Unrelated reference component changed")
                moved += int(distance > 1e-8)
                unchanged_count += int(distance <= 1e-8)
                maximum = max(maximum, distance)
        require(moved > 0 and maximum > .001 and unchanged_count > 0, "Chosen actual reference lacks a useful moved/control region")
        reference_observations.append({"before": before_key, "after": after_key, "affected_mesh": affected_mesh,
                                       "moved_used_vertex_records": moved, "unchanged_used_vertex_records": unchanged_count,
                                       "maximum_world_delta": maximum, "scope": "Actual derived GLB CPU reference, not native Source"})
    manifest["derived_reference_observations"] = reference_observations
    reference_path = folder / "derived-reference.json"
    write_new(reference_path, {"scope": "Independent stdlib decoded derived GLB positions; not native Source fidelity", "captures": references})
    manifest["derived_reference"] = stamp(reference_path)
    builder = load_module("sfm_probe_freezer", ROOT / "tools/build_owner_review_snapshot.py")
    for mode in ("writer", "reader"):
        project = owned(folder / (mode+"-source"))
        revision, hashes = builder.freeze_source(ROOT, project, None if working_source else expected_revision)
        require(revision == expected_revision, "Source snapshot revision differs")
        for name in HARNESS:
            destination = project / "tests" / ("sfm_probe_"+name)
            require(not destination.exists(), "Harness name collides with committed source")
            destination.write_bytes((TASK / "source" / name).read_bytes())
            hashes[destination.relative_to(project).as_posix()] = sha(destination.read_bytes())
        profile = "HAS SFM Derived Probe "+mode+" "+token
        override = project / "override.cfg"
        require(not override.exists(), "Snapshot has an unexpected preference override")
        override.write_text('[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name='+json.dumps(profile)+'\n', encoding="utf-8")
        hashes["override.cfg"] = sha(override.read_bytes())
        manifest["projects"][mode] = {"path": str(project), "files": hashes}
        manifest["profiles"][mode] = profile
    require(all(unchanged(s) for s in protected) and root_functional() == manifest["root_functional"]
            and head() == expected_revision, "Inputs changed during prepare")
    path = folder / "manifest.json"
    write_new(path, manifest)
    return path, stamp(path)["sha256"]


def preflight(path, expected_sha, offline=False):
    path = owned(path)
    require(stamp(path)["sha256"] == expected_sha, "Manifest hash mismatch")
    m = read_json(path)
    require(m["format"] == "has_sfm_derived_probe_candidate_2" and m["root"] == str(ROOT)
            and Path(m["run_folder"]) == path.parent, "Manifest identity/layout mismatch")
    require(head() == m["root_revision"], "Root HEAD changed; prepare a fresh candidate")
    require(root_functional() == m["root_functional"], "Root functional files changed; prepare a fresh candidate")
    require(len(m["cases"]) == 12 and len(m["render_cases"]) == 8, "Bounded case count changed")
    require(all(unchanged(s) for s in m["protected"]), "Protected original, runtime or candidate source changed")
    require(unchanged(m["derived_reference"]), "Derived reference changed")
    inputs_root = path.parent / ("inputs.offline" if offline else "inputs")
    input_members = list(inputs_root.rglob("*"))
    for member in input_members:
        no_reparse(member)
    actual_files = {str(p.relative_to(inputs_root)).replace("\\", "/") for p in input_members if p.is_file()}
    expected_files = {c["key"]+"/"+n for c in m["cases"] for n in ("scene.glb", "parameters.json", "dependencies.json")}
    require(actual_files == expected_files, "Owned input membership changed")
    for c in m["cases"]:
        for filename, identity in c["inputs"].items():
            actual = stamp(inputs_root / c["key"] / filename)
            require(all(actual[k] == identity[k] for k in ("bytes", "sha256", "mtime_ns")), "Owned input changed")
    for project in m["projects"].values():
        require(source_members(Path(project["path"])) == project["files"], "Frozen private source membership/hash changed")
    return m


def strict_private(receipt, returncode):
    return (returncode == 0 and receipt.get("exit") == 0 and receipt.get("child_desktop_confirmed") is True
            and receipt.get("foreground_child_observed") is False and receipt.get("job_closed") is True
            and receipt.get("desktop_closed") is True)


@contextmanager
def pinned_runtime_environment():
    """Bind the runner and its pack/unpack child to approved executables only."""
    overrides = {"HYBRID_PYTHON": str(PYTHON), "HYBRID_GODOT": str(GODOT)}
    previous = {key: os.environ.get(key) for key in overrides}
    try:
        os.environ.update(overrides)
        yield os.environ.copy()
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def captured_process(command, project, output, timeout, env=None):
    started = time.monotonic()
    try:
        return subprocess.run(command, cwd=project, capture_output=True, text=True, encoding="utf-8", errors="replace",
                              timeout=timeout, env=env, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    except subprocess.TimeoutExpired as error:
        def decoded(value):
            return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value or ""
        log = decoded(error.stdout)+decoded(error.stderr)
        with owned(output / "process.log").open("x", encoding="utf-8") as stream:
            stream.write(log)
        write_new(output / "execution.json", {"status": "TIMEOUT_UNACCEPTED_RETAIN_ALL", "command": command,
                                               "timeout_seconds": timeout, "elapsed_seconds": time.monotonic()-started,
                                               "partial_stdout_stderr_preserved": True, "retry_attempted": False})
        raise


def launch(m, manifest_path, mode, parse_only=False):
    project = Path(m["projects"][mode]["path"])
    runner = load_module("sfm_probe_run_"+mode, project / "run.py")
    output = Path(m["run_folder"]) / mode
    output.mkdir(exist_ok=False)
    extra = ["--verbose", "--log-file", str(output / "engine.log")]
    if parse_only:
        extra.append("--check-only")
    else:
        extra += ["--", str(manifest_path), str(output), mode]
    with pinned_runtime_environment() as child_environment:
        command = runner.command("tests/sfm_probe_raw_probe.gd", headless=parse_only, extra=extra)
        if not parse_only:
            require(command[0] == str(PYTHONW) and "--receipt" in command and "--headless" not in command,
                    "Expected approved private graphical wrapper")
            require(Path(command[1]) == project / "tools/private_desktop.py" and str(GODOT) in command,
                    "Unexpected private helper/runtime")
        write_new(output / "runtime-environment.json", {
            "overrides": {key: child_environment[key] for key in ("HYBRID_PYTHON", "HYBRID_GODOT")},
            "approved_executables": [stamp(PYTHON), stamp(PYTHONW), stamp(GODOT)],
            "other_environment_values_recorded": False})
        write_new(output / "command.json", command)
        completed = captured_process(command, project, output, 210, env=child_environment)
    log = completed.stdout+completed.stderr
    (output / "process.log").write_text(log, encoding="utf-8")
    receipt = {} if parse_only else read_json(Path(command[command.index("--receipt")+1]))
    result = {} if parse_only else read_json(output / "result.json")
    observation = {"exit": completed.returncode, "parse_only": parse_only, "receipt": receipt, "result": result,
                   "forbidden_log_markers": [s for s in BAD_LOG if s in log]}
    write_new(output / "execution.json", observation)
    require(completed.returncode == 0 and not observation["forbidden_log_markers"], "Engine/probe failed; retain all evidence")
    if not parse_only:
        require(strict_private(receipt, completed.returncode), "Private graphical isolation did not pass")
        require(result.get("mode") == mode and result.get("nonce") == m["nonce"] and result.get("failures") == 0
                and result.get("checks", 0) > 0 and "SFM_DERIVED_PROBE " in log, "Missing or failed actual probe result")
        if mode == "writer":
            require(result.get("raw_captures") == [c["key"] for c in m["render_cases"]], "Capture membership differs")
        require(result.get("app_cases") == ["nitori-skin-0", "keiki-000"], "App-case membership differs")
    return observation


def final_preservation(m, manifest_path, manifest_sha, offline):
    """Inspect every class even when an earlier class is missing or changed."""
    gates = {}
    def inspect(name, predicate):
        try:
            gates[name] = {"passed": bool(predicate())}
        except Exception as error:
            gates[name] = {"passed": False, "error": type(error).__name__+": "+str(error)}
    protected = {}
    for index, record in enumerate(m["protected"]):
        name = str(index)+":"+record["path"]
        try:
            protected[name] = {"passed": unchanged(record)}
        except Exception as error:
            protected[name] = {"passed": False, "error": type(error).__name__+": "+str(error)}
    gates["protected_originals_runtimes_candidate"] = {"passed": all(r["passed"] for r in protected.values()), "files": protected}
    inspect("root_head", lambda: head() == m["root_revision"])
    inspect("root_functional", lambda: root_functional() == m["root_functional"])
    inspect("derived_reference", lambda: unchanged(m["derived_reference"]))
    for mode in ("writer", "reader"):
        inspect("private_source_"+mode, lambda mode=mode:
                source_members(Path(m["projects"][mode]["path"])) == m["projects"][mode]["files"])
    # Recheck the exact manifest, input members/stamps, context and all other gates.
    inspect("full_context_and_owned_inputs", lambda: preflight(manifest_path, manifest_sha, offline=offline) == m)
    return {"passed": all(gate["passed"] for gate in gates.values()), "inputs_offline": offline, "gates": gates}


def retain_and_require_preservation(receipt_path, outcome, verification):
    outcome["final_preservation"] = verification
    outcome["protected_originals_unchanged"] = verification["gates"]["protected_originals_runtimes_candidate"]["passed"]
    outcome["root_functional_unchanged"] = verification["gates"]["root_functional"]["passed"]
    if not verification["passed"]:
        outcome["status_before_final_preservation"] = outcome["status"]
        outcome["status"] = "FAILED_PRESERVATION_RETAIN_ALL"
    write_new(receipt_path, outcome)
    require(verification["passed"], "Final preservation/context failed; receipt and all evidence retained")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--prepare", action="store_true")
    p.add_argument("--expected-root-revision")
    p.add_argument("--working-source", action="store_true")
    p.add_argument("--working-context")
    p.add_argument("--manifest", type=Path)
    p.add_argument("--manifest-sha256")
    p.add_argument("--parse-only", action="store_true")
    p.add_argument("--run-gpu", action="store_true")
    p.add_argument("--lease-confirmed", action="store_true")
    args = p.parse_args()
    require(not (args.parse_only and args.run_gpu), "Choose parse or actual graphics")
    if args.prepare:
        require(args.expected_root_revision and not any((args.manifest, args.run_gpu, args.parse_only, args.lease_confirmed)),
                "Preparation is separate from execution")
        path, digest = prepare(args.expected_root_revision, args.working_source, args.working_context)
        print(json.dumps({"status": "PREPARED_NOT_RUN", "manifest": str(path), "sha256": digest}))
        return
    require(args.manifest and args.manifest_sha256, "A reviewed manifest and exact SHA are required")
    require(not args.working_source and not args.working_context, "Source-mode binding belongs to separate preparation")
    m = preflight(args.manifest, args.manifest_sha256)
    if not args.parse_only and not args.run_gpu:
        print(json.dumps({"status": "PREFLIGHT_PASS", "graphics": "UNRUN", "app": "UNRUN", "native_fidelity": "UNTESTED"}))
        return
    require(args.parse_only or args.lease_confirmed, "Actual graphics require explicit exclusive lease confirmation")
    outcome = {"mode": "parse_only" if args.parse_only else "actual_gpu", "status": "STARTED", "nonce": m["nonce"]}
    receipt_path = Path(m["run_folder"]) / ("parse-verification.json" if args.parse_only else "actual-verification.json")
    require(not receipt_path.exists(), "Run already has an execution receipt; prepare fresh")
    offline = False
    try:
        outcome["writer"] = launch(m, args.manifest, "writer", args.parse_only)
        preflight(args.manifest, args.manifest_sha256)
        if not args.parse_only:
            source = owned(Path(m["run_folder"]) / "inputs")
            target = owned(Path(m["run_folder"]) / "inputs.offline")
            require(source.is_dir() and not target.exists(), "Fresh owned offline transition required")
            source.rename(target)  # Only this run's fully checked owned copies; originals never move.
            offline = True
            preflight(args.manifest, args.manifest_sha256, offline=True)
            outcome["reader"] = launch(m, args.manifest, "reader")
            preflight(args.manifest, args.manifest_sha256, offline=True)
        outcome["status"] = "PARSE_PASS_NOT_GPU_PROOF" if args.parse_only else "DERIVED_RENDER_APP_PASS_NOT_NATIVE_FIDELITY"
    except Exception as error:
        outcome["status"] = "FAILED_RETAIN_ALL_EVIDENCE"
        outcome["error"] = str(error)
        raise
    finally:
        verification = final_preservation(m, args.manifest, args.manifest_sha256, offline)
        retain_and_require_preservation(receipt_path, outcome, verification)
    print(json.dumps({"status": outcome["status"], "receipt": str(receipt_path)}))


if __name__ == "__main__":
    main()
