"""UNRUN one-case qualification driver. Default is lock validation, never launch.

Requires a freshly generated exact lock and root-confirmed exclusive native lease.
Reuses dual independent Python/Blender self-attestation and original receipts.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import background_route as BG


def read(path):
    BG.S.no_reparse(path)
    BG.S.require(path.stat().st_size <= 16*1024*1024, "Bounded metadata required")
    return json.loads(path.read_bytes(), object_pairs_hook=BG.S.unique_object)


def members(folder):
    values = []
    for base, dirs, files in os.walk(folder, followlinks=False):
        for name in dirs+files: BG.S.no_reparse(Path(base)/name)
        dirs[:] = sorted(name for name in dirs if name not in {".git", "__pycache__"})
        values.extend(str(Path(base)/name) for name in files if not name.endswith((".pyc", ".pyo")))
    return sorted(values)


def check(lock):
    BG.S.require(lock["format"] == "has_Junko_crosswalk_qualification_lock_draft_1" and
                 Path(lock["task"]) == BG.TASK and Path(lock["root"]) == BG.ROOT, "Wrong fresh diagnostic lock context")
    BG.S.require(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=BG.ROOT, text=True).strip() == lock["root_revision"], "Root HEAD changed")
    BG.S.require(all(BG.S.identity(Path(path)) == value for path, value in lock["files"].items()), "Frozen source/input/runtime/baseline changed")
    main_members = sorted(str(path) for folder in ("src", "tests", "tools", "data", "examples")
                          for path in (BG.ROOT/folder).rglob("*") if path.is_file() and path.suffix != ".pyc" and "__pycache__" not in path.parts)
    main_members = sorted([*main_members, *[str(BG.ROOT/name) for name in ("project.godot", "main.tscn", "run.py", "launch.pyw")]])
    BG.S.require(main_members == lock["main_members"] and len(main_members) == lock["canonical_functional_source_count"] == 996,
                 "Canonical functional-source membership changed")
    for folder, key in ((BG.TASK/"driver", "driver_members"), (BG.PROTOTYPE, "overlay_members"),
                        (lock["input_stage"], "native_members"), (BG.SOURCEIO, "runtime_members"),
                        (lock["baseline"], "baseline_members"), (lock["exporter_root"], "exporter_members")):
        BG.S.require(members(Path(folder)) == lock[key], "Frozen input/runtime/baseline membership changed")
    BG.source_observation(lock["background_sources"])


def fingerprint(path, native):
    sys.path.insert(0, str(BG.PROTOTYPE/"tools"))
    import qualification_fingerprints as F
    value = F.H.GLB(path)
    active = [node.get("name", "") for node in value.doc["nodes"] if "mesh" in node]
    result = F.glb_structure(path, active, native)
    # Also retain every material/texture/sampler and embedded image byte digest;
    # the inherited verifier's active-base-image checks are narrower than this.
    images = []
    for image in value.doc.get("images", []):
        view = value.doc["bufferViews"][image["bufferView"]]
        start = view.get("byteOffset", 0); count = view["byteLength"]
        images.append({"mimeType": image.get("mimeType"), "sha256": hashlib.sha256(value.binary[start:start+count]).hexdigest()})
    result["all_material_texture_state"] = {key: value.doc.get(key, []) for key in ("materials", "textures", "samplers")}
    result["all_embedded_images"] = images
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", type=Path, required=True); parser.add_argument("--lock-sha256", required=True)
    parser.add_argument("--run-conversion", action="store_true"); parser.add_argument("--lease-confirmed", action="store_true")
    args = parser.parse_args(); lock_path = args.lock.resolve(strict=True)
    BG.S.require(lock_path == BG.TASK/"fresh-input-lock.json" and BG.S.identity(lock_path)["sha256"] == args.lock_sha256, "Wrong fresh lock bytes")
    lock = read(lock_path); check(lock)
    if not args.run_conversion:
        print(json.dumps({"mode": "preflight_only", "lock_valid": True, "native_conversion": False})); return
    BG.S.require(args.lease_confirmed and os.name == "nt", "Root exclusive Windows lease required")
    case = BG.TASK/"case-junko-default"; BG.S.require(not case.exists(), "Never reuse a diagnostic case")
    case.mkdir(); bundle = case/"bundle"
    command = [str(BG.PYTHON), "-B", "-u", str(BG.PREPARE), lock["mdl"], "--output", str(bundle),
               "--sourceio", str(BG.SOURCEIO), "--blender", str(BG.BLENDER),
               "--mount-plan", str(BG.TASK/"empty-mount-plan.json"), "--gmod", str(case/"absent-gmod"),
               "--workshop", str(case/"absent-workshop")]
    environment = os.environ.copy()
    for key in ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "BLENDER_SYSTEM_SCRIPTS", "BLENDER_SYSTEM_DATAFILES", "BLENDER_SYSTEM_EXTENSIONS", "BLENDER_USER_RESOURCES"):
        environment.pop(key, None)
    environment.update(PYTHONDONTWRITEBYTECODE="1", NO_BPY="1")
    for key, relative in {"TEMP":"temp", "TMP":"temp", "APPDATA":"appdata", "LOCALAPPDATA":"localappdata",
                          "BLENDER_USER_CONFIG":"blender-config", "BLENDER_USER_SCRIPTS":"blender-scripts",
                          "BLENDER_USER_DATAFILES":"blender-datafiles", "BLENDER_USER_EXTENSIONS":"blender-extensions"}.items():
        path = case/relative; path.mkdir(exist_ok=True); environment[key] = str(path)
    result = {"format":"has_Junko_crosswalk_qualification_draft_1", "passed":False, "source_context":"diagnostic_overlay_not_main_port",
              "native_conversion_requested":True, "attested_Blender_spawn_observed":False, "case":str(case), "automatic_cleanup":False,
              "HAS_runtime_binding":"unattempted", "app_adoption":"UNRUN", "native_solver":"UNRUN"}
    try:
        launch = BG.prepare(case, command, lock["files"], lock["root_revision"], args.lock_sha256, BG.Win.capture_self())
        BG.S.save(case/"command.json", {"native":command, "private":launch["private_command"], "request_sha256":launch["request_sha256"]})
        code, seconds = BG.run_outer(launch, case, bundle, environment, lease_confirmed=True)
        result.update(exit=code, seconds=seconds)
        isolation = BG.verify_case(case, launch, code, BG.Win.system_filetime())
        BG.S.save(case/"background-isolation-verification.json", isolation)
        BG.S.require(code == 0 and isolation["passed"], "Diagnostic worker/isolation failed; retain all partial evidence")
        proof = read(case/"diagnostics/crosswalk-proof.json"); request = read(bundle/"conversion-request.json")
        BG.S.require(proof["nonce"] == launch["request"]["nonce"] and proof["input_lock_sha256"] == args.lock_sha256 and
                     proof["native_bone_count"] == len(proof["bones"]) == 69 and
                     proof["glb_sha256"] == BG.S.identity(bundle/"scene.glb")["sha256"], "Diagnostic proof join failed")
        validator = runpy.run_path(str(BG.ROOT/"tests/verify_source_jiggle_native_report.py"), run_name="qualification_native_report_validator")
        native_join = validator["verify"](bundle/"conversion-request.json", bundle/"parameters.json", 49)
        BG.S.save(case/"native-report-join.json", native_join)
        parameters = read(bundle/"parameters.json"); baseline = Path(lock["baseline"])
        current_fp = fingerprint(bundle/"scene.glb", parameters["native_parameters"])
        baseline_fp = fingerprint(baseline/"scene.glb", read(baseline/"parameters.json")["native_parameters"])
        for key in ("meshes", "native_joint_names_bound", "active_materials", "all_material_texture_state", "all_embedded_images"):
            BG.S.require(current_fp[key] == baseline_fp[key], "Baseline decoded geometry/skin/morph/material/image state differs: "+key)
        BG.S.save(case/"current-fingerprints.json", current_fp); BG.S.save(case/"baseline-fingerprints.json", baseline_fp)
        result.update(passed=True, exact_native_crosswalk_rows=69, native_float32_joins=native_join["exact_numeric_float32_joins"],
                      baseline_decoded_state_preserved=True, raw_GLB_bytes_equal=current_fp["sha256"] == baseline_fp["sha256"],
                      original_source_sha256=request["sha256"], native_mdl_sha256=proof["native_mdl_sha256"],
                      production_parameters_augmented=proof["production_parameters_augmented"])
    except BaseException as error:
        result["error"] = type(error).__name__+": "+str(error); raise
    finally:
        result["attested_Blender_spawn_observed"] = (case/"blender-spawn.json").is_file()
        try: check(lock); result["locked_inputs_preserved"] = True
        except BaseException as error:
            result.update(passed=False, locked_inputs_preserved=False, preservation_error=str(error))
        result["lock_preserved"] = BG.S.identity(lock_path)["sha256"] == args.lock_sha256
        result["passed"] = result["passed"] and result["lock_preserved"]
        BG.S.save(case/"verification.json", result)
        print(json.dumps(result), flush=True)
    BG.S.require(result["passed"], "Diagnostic verification/preservation failed; retain all evidence")


if __name__ == "__main__": main()
