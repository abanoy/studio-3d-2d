"""Inspect a narrow source rebind; materialize only after the tested fix commit.

Never prepares an execution lock or launches Blender, Godot, a native viewer or
the converter. Old native resources/evidence remain read-only and checksum-bound.
"""
import argparse
import copy
import difflib
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
TASK = Path(__file__).absolute().parent
ROOT = TASK.parents[1]
OLD = ROOT / "output/sfm-broader-native-cases-20261113"
sys.path.insert(0, str(OLD / "source"))
import stage_resources as S

OLD_HEAD = "76f89e82af583001af8cd16260b441555feb2fe2"
SIX = ("tools/prepare_source.py", "tools/blender_source_bridge.py", "tools/source_appearance.py",
       "tools/source_mdl_choices.py", "tools/source_choice_io.py", "tools/source_archive.py")
APPROVED_CHANGED = {"tools/blender_source_bridge.py", "tools/source_archive.py"}
COPIED = ("stage_resources.py", "win_desktop_attestation.py", "background_python_bootstrap.py",
          "background_blender_observer.py", "background_route.py", "background_conversion_driver.py")

def read(path):
    S.no_reparse(path)
    raw = path.read_bytes()
    S.require(len(raw) <= 8 * 1024 * 1024, "Metadata exceeds bound")
    return json.loads(raw, object_pairs_hook=S.unique_object)

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    S.save(path, data)

def head():
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()

def inspect():
    old_plan = read(OLD / "RESOURCE_PLAN.json")
    scope = {str(Path(path).relative_to(ROOT)).replace("\\", "/"): value
             for path, value in old_plan["protected_inputs_before_after"].items()
             if Path(path).is_relative_to(ROOT / "tools") or Path(path).is_relative_to(ROOT / "tests")}
    S.require(len(scope) == 17 and set(SIX) <= set(scope), "Original main Python scope differs")
    current = {name: S.identity(ROOT / name) for name in scope}
    changed = {name for name in scope if current[name] != scope[name]}
    S.require(changed == APPROVED_CHANGED, "Only the reviewed bridge/archive long-path changes may rebind")
    for name in set(scope) - APPROVED_CHANGED:
        S.require(current[name] == scope[name], "Unreviewed scoped source changed")
    old_paths = [OLD / "RESOURCE_PLAN.json", OLD / "CORE_FAMILIES.json", OLD / "CORE_VMT_CLOSURE.json",
        OLD / "CORE_COMMANDS.json", OLD / "native-core-cases.json", OLD / "WIDER_FAMILIES.json",
        OLD / "WIDER_METADATA_RECEIPT.json", OLD / "WIDER_COMMANDS.json", OLD / "native-wider-cases.json",
        OLD / "empty-mount-plan.json", OLD / "conversion-inputs-main_core1.json", OLD / "conversion-inputs-wide1.json",
        OLD / "runs/wider-execute-1794612147814048100/verification.json"]
    old_paths += [OLD / directory / name for directory in ("source", "wider-source") for name in COPIED]
    old_paths += list((OLD / "requests").glob("*.json")) + list((OLD / "wider-requests").glob("*.json"))
    originals = {str(path): S.identity(path) for path in old_paths}
    return old_plan, current, {"format": "has_native_main_longpath_rebind_plan_1", "historical_revision": OLD_HEAD,
        "observed_revision": head(), "allowed_changed_sources": sorted(APPROVED_CHANGED),
        "old_scoped_main_python": scope, "current_scoped_main_python": current,
        "six_explicit_worker_source_expectations": {name: current[name] for name in SIX},
        "preserved_old_metadata_driver_request_lock_inputs": originals,
        "core_input_stage": str(ROOT / "output/sfm-next-cases-20261112/stage"),
        "wider_input_stage": str(OLD / "stage"), "new_output_task": str(TASK),
        "new_driver_directories": ["core-source", "wider-source"],
        "requests": "Fresh exact request bytes copied into this task; no old request is edited",
        "materialization_gate": "Exact new root-supplied committed HEAD distinct from76f89e and six source hashes matching these expectations; old15scoped files exact",
        "fresh_lock_created": False, "converter_or_gpu_launched": False,
        "limits": ["Read-only native resource reuse, no staging/extraction or original/Steam writes.",
            "No source/metadata expectation is silently refreshed to accept a new change.",
            "Root must review new copies, then separately prepare fresh locks and grant conversion lease.",
            "Previous Keiki Win206 failure and historical locks remain unchanged."]}

def materialize(revision):
    expected_path = TASK / "REBIND_PLAN.json"
    expected = read(expected_path)
    S.require(re.fullmatch("[0-9a-f]{40}", revision or "") and revision != OLD_HEAD and head() == revision, "Wait for the exact tested fix commit from root")
    old_plan, current, observed = inspect()
    S.require(current == expected["current_scoped_main_python"], "Source expectations changed; explicit reviewed replan required")
    S.require(observed["preserved_old_metadata_driver_request_lock_inputs"] == expected["preserved_old_metadata_driver_request_lock_inputs"], "Historical metadata/source/request/locks changed")
    for directory in ("core-source", "wider-source", "inputs", "requests", "wider-requests"):
        S.require(not (TASK / directory).exists(), "New task materialization must be fresh; retain partial failures")
    # Retain the exact old plan as provenance. Fresh plan updates only the two
    # explicitly approved main source observations; resource/runtime records stay.
    write(TASK / "inputs/historical-resource-plan.json", old_plan)
    fresh = copy.deepcopy(old_plan)
    for name in APPROVED_CHANGED:
        fresh["protected_inputs_before_after"][str(ROOT / name)] = current[name]
    fresh["source_rebind"] = {"revision": revision, "expectations": str(expected_path), "allowed_changed_sources": sorted(APPROVED_CHANGED)}
    write(TASK / "RESOURCE_PLAN.json", fresh)
    for name in ("CORE_FAMILIES.json", "CORE_VMT_CLOSURE.json", "native-core-cases.json", "WIDER_FAMILIES.json", "WIDER_METADATA_RECEIPT.json", "empty-mount-plan.json"):
        shutil.copy2(OLD / name, TASK / name)
    (TASK / "inputs").mkdir(exist_ok=True)
    shutil.copy2(OLD / "runs/wider-execute-1794612147814048100/verification.json", TASK / "inputs/wider-staging.json")
    for directory in ("requests", "wider-requests"):
        (TASK / directory).mkdir(exist_ok=False)
        for path in sorted((OLD / directory).glob("*.json")):
            shutil.copy2(path, TASK / directory / path.name)
    wide_manifest = read(OLD / "native-wider-cases.json")
    for row in wide_manifest["cases"]:
        if row.get("appearance_request"):
            row["appearance_request"] = str(TASK / "wider-requests" / Path(row["appearance_request"]).name)
    write(TASK / "native-wider-cases.json", wide_manifest)
    for name in ("CORE_COMMANDS.json", "WIDER_COMMANDS.json"):
        data = read(OLD / name)
        for row in data["commands"]:
            row["command"] = [value.replace(str(OLD), str(TASK)) if isinstance(value, str) and ("requests" in value or value == str(OLD / "empty-mount-plan.json") or "native-conversions" in value or "wider-conversions" in value) else value for value in row["command"]]
        write(TASK / name, data)
    workers = {name: current[name]["sha256"] for name in SIX}
    receipt = {"format": "has_native_main_longpath_rebind_materialized_1", "root_revision": revision,
        "six_explicit_source_sha256": workers, "sources": {}, "fresh_locks_created": False, "converter_or_gpu_launched": False}
    differences = []
    for old_dir, new_dir in (("source", "core-source"), ("wider-source", "wider-source")):
        (TASK / new_dir).mkdir(exist_ok=False)
        for name in COPIED:
            old_path = OLD / old_dir / name
            raw = old_path.read_bytes(); text = raw.decode("utf-8")
            if name in {"background_route.py", "background_conversion_driver.py"}:
                if old_dir == "wider-source":
                    text = text.replace('INPUT_STAGE = TASK / "stage"', 'INPUT_STAGE = ROOT / "output/sfm-broader-native-cases-20261113/stage"')
                if name == "background_route.py":
                    start = text.index("WORKER_SHA = "); end = text.index("\nNATIVE_MODULES = ", start)
                    text = text[:start] + "WORKER_SHA = {str(ROOT / name): value for name, value in " + repr(workers) + ".items()}\n" + text[end:]
                else:
                    start = text.index("WORKERS = "); end = text.index("\nORDER = ", start)
                    text = text[:start] + "WORKERS = " + repr(workers) + "\n" + text[end:]
                    text = text.replace('TASK / "runs/wider-execute-1794612147814048100/verification.json"', 'TASK / "inputs/wider-staging.json"')
                differences.extend(difflib.unified_diff(raw.decode("utf-8").splitlines(True), text.splitlines(True), fromfile="historical/" + old_dir + "/" + name, tofile=new_dir + "/" + name))
                raw = text.encode("utf-8")
            target = TASK / new_dir / name; target.write_bytes(raw)
            receipt["sources"][new_dir + "/" + name] = S.identity(target)
    (TASK / "REBIND_NORMALIZED_DIFF.patch").write_text("".join(differences), encoding="utf-8")
    S.require(all(S.identity(Path(path)) == value for path, value in expected["preserved_old_metadata_driver_request_lock_inputs"].items()), "Historical proof changed during copying")
    S.require({name: S.identity(ROOT / name) for name in current} == current and head() == revision, "Main source/revision changed during materialization")
    write(TASK / "MATERIALIZED.json", receipt)
    print(json.dumps({"materialized": True, "root_revision": revision, "worker_sources": len(workers), "fresh_locks_created": False, "converter_launched": False}))

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--materialize", action="store_true")
    parser.add_argument("--expected-revision")
    options = parser.parse_args(argv)
    if options.materialize:
        materialize(options.expected_revision)
    else:
        S.require(options.expected_revision is None, "Inspection cannot finalize a revision")
        _, _, report = inspect()
        write(TASK / "REBIND_PLAN.json", report)
        print(json.dumps({"plan": str(TASK / "REBIND_PLAN.json"), "changed": report["allowed_changed_sources"], "fresh_lock_created": False, "converter_launched": False}))

if __name__ == "__main__": main()
