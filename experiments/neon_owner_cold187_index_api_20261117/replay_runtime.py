"""Concrete four-case cold replay, disabled until validation_admission admits it.
Own pinned public references are read at import; no functional/native inputs are.
"""
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
from types import SimpleNamespace

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
WORKSPACE = ROOT.parent
NATIVE = ROOT / "output/sfm-bone-bindings-native-launch-20261114T033026205/run"
REFERENCE_SHA = "f6e87e8eb239bc08843ef1b3f369b449509bae98128db770b3835639185f8514"
REFERENCE_PINS = {"reference_validator.py": REFERENCE_SHA,
    "reference-lock.json": "e5dbbbd1cc21d143fc9c6d56996b6aec97b1b0f9167f334c274a77d246ab9413",
    "input-lock.json": "3bb7c2ce75f55dcb53143aab0df5ab8b39c68180617092664a579126fb09cfb6",
    "replay.gd": "d9259db293e1abc9809636ec461b9d2888778b5d57b1faa78a76026aea746450",
    "audio_contract.py": "4e4351d82293fd6156712c1c81bd532c35cd7a13e0a091f3dca26628a1d0ec93"}
HELPERS = ("need", "no_links", "identity", "tree", "shipped_tree", "exporter_tree", "load", "save", "module", "extra_names", "execute")
_reference = (HERE / "reference_validator.py").read_bytes()
if hashlib.sha256(_reference).hexdigest() != REFERENCE_SHA:
    raise RuntimeError("Pinned public replay reference differs")
_tree = ast.parse(_reference)
_nodes = [node for node in _tree.body if isinstance(node, ast.FunctionDef) and node.name in HELPERS]
if {node.name for node in _nodes} != set(HELPERS):
    raise RuntimeError("Exact replay helper inventory differs")
_nodes += [node for node in _tree.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "BAD" for target in node.targets)]
exec(compile(ast.fix_missing_locations(ast.Module(body=_nodes, type_ignores=[])), str(HERE / "reference_validator.py"), "exec"), globals())
_audio = (HERE / "audio_contract.py").read_bytes()
need(hashlib.sha256(_audio).hexdigest() == REFERENCE_PINS["audio_contract.py"], "Pinned independent audio contract differs")
_audio_globals = {"__name__": "owner_cold187_audio_contract"}
exec(compile(_audio, str(HERE / "audio_contract.py"), "exec"), _audio_globals)
audio_expectations = _audio_globals["audio_expectations"]


def functional(name):
    return (name.split('/')[0] in ('src','tests','tools','data','examples') or name in ('project.godot','main.tscn','run.py','launch.pyw')) and '__pycache__' not in Path(name).parts and not name.endswith('.pyc')


def lexical_layout(d, output):
    """Pure path/receipt boundary check, independent of file or token IO."""
    root, workspace, review = Path(d["root"]), Path(d["workspace"]), Path(d["review"])
    revision = d["merged_revision"]
    need(type(revision) is str and len(revision) == 40 and all(c in "0123456789abcdef" for c in revision), "Exact merged revision required")
    need(root == ROOT and workspace == WORKSPACE and review.parent == workspace and review.name == "HAS-Review-Neon-" + revision[:7] + "-native", "Exact qualified review sibling required")
    output = Path(output)
    need(output.is_absolute() and ".." not in output.parts and output != root / "output" and output.is_relative_to(root / "output"), "New owned evidence boundary required")
    built = d["built"]
    need(built.get("passed") is True and built.get("source_commit") == revision and built.get("native_sources_included") is True and built.get("graphics_launched") is False, "Qualified copy-only build receipt required")
    need(built.get("source_delta_admission") == d["source_delta_admission"] and built.get("full_run_gate") == d["full_gate"], "Exact copy/admission gate joins")
    return root, workspace, review, output, revision


def run(value, output):
    import validation_admission as V
    d = V.assert_validated(value)  # First action before review/native/functional reads.
    root, workspace, review, output, expected_revision = lexical_layout(d, output)
    need(os.name == "nt", "Approved Windows private route required")
    args = SimpleNamespace(expected_revision=expected_revision)
    need(all(identity(HERE / name)["sha256"] == digest for name, digest in REFERENCE_PINS.items()), "Pinned cold replay/Gd/audio/reference inputs differ")
    review = review.resolve(strict=True); output = output.absolute(); no_links(review); no_links(output)
    need(not output.exists() and output.resolve().is_relative_to((root / "output").resolve()), "Fresh owned replay evidence required")
    studio = review / "Studio"; built = d["built"]; lock = d["lock"]
    need(load(HERE / "input-lock.json") == lock and load(review / "BUILD-VERIFICATION.json") == built, "Immutable lock/exact copy receipt changed")
    preparation = d["preparation"]; full_gate = d["full_gate"]
    need(full_gate and all(identity(Path(path)) == expected for path, expected in full_gate.items()), "Qualified full/run/release inputs changed")
    canonical_run = Path(d["canonical_run"]).resolve()
    full_states = [Path(path) for path in full_gate if Path(path).name == "state.json" and Path(path).parent.resolve() == canonical_run]
    need(len(full_states) == 1, "Exactly one qualified current full state required")
    full_state = load(full_states[0])
    need(full_state.get("source_commit") == d["candidate_commit"] and full_state.get("status") == "passed" and full_state.get("suite_exit") == 0 and full_state.get("source_unchanged") is True, "Exact qualified candidate full PASS required")
    need(not tree(studio / "output") and not tree(studio / ".godot"), "Review is no longer fresh; retain owner work/output")
    need(tree(review / "Dependencies" / ("sourceio-" + built["sourceio_revision"])) == lock["sourceio_files"], "Copied SourceIO differs")
    for row in lock["source_chooser"]:
        need(tree(review / "Native sources" / row["folder"]) == lock["native_families"][row["resource_root"]], "Copied native family differs: " + row["name"])
    ship_before = shipped_tree(review)
    for name, digest in built["source_hashes"].items(): need(identity(studio / name)["sha256"] == digest, "Frozen Studio source/support differs")
    native_path = NATIVE / "verification.json"
    need(identity(native_path) == lock["native_verification"], "Frozen actual native DATA verification differs")
    native = load(native_path)
    need(identity(native_path) == lock["native_verification"] and native.get("passed") is True and native.get("preservation") and all(value is True for value in native["preservation"].values()), "Exact original native DATA preservation required")
    source_delta_admission = d["source_delta_admission"]
    admitted_changes = set(d["legacy_admitted_changes"])
    production_context = [name for name in native["source_before"]["files"] if functional(name) and name not in admitted_changes]
    native_cases = {row["name"]: row for row in native["writer"]["result"]["cases"]}
    original_families = {folder: tree(Path(folder)) for folder in lock["native_families"]}
    need(original_families == lock["native_families"], "Original native source family changed")
    runtimes_before = {path: identity(Path(path)) for path in lock["runtime_executables"]}
    need(runtimes_before == lock["runtime_executables"], "Approved runtime changed")
    exporter_before = exporter_tree(Path(lock["exporter_root"])); need(exporter_before == lock["exporter_noncache_sources"], "Installed exporter differs")
    original_sourceio = root / "output/dependencies" / ("sourceio-" + built["sourceio_revision"])
    original_sourceio_before = tree(original_sourceio); need(original_sourceio_before == lock["sourceio_files"], "Original approved SourceIO differs")
    old_reviews = {str(path): tree(path) for path in workspace.glob("HAS-Review-*") if path.is_dir() and path != review}
    harness_before = {str(path): identity(path) for path in (Path(__file__), HERE / "reference_validator.py", HERE / "replay.gd", HERE / "reference-lock.json", HERE / "audio_contract.py", HERE / "input-lock.json")}
    harness_before.update(preparation); harness_before.update(d["protected_gate"])
    need(all(identity(Path(path)) == expected for path, expected in harness_before.items()), "Admitted protected/harness inputs changed")
    references = [native_path]
    for item in native_cases.values():
        expected_path = Path(item["expected"]); actual = load(expected_path)
        references += [expected_path, expected_path.parent / "catalogue.json", Path(item["conversion_request"])]
        references += [Path(row["path"]) for row in actual["pictures"].values()]
    reference_before = {str(path): identity(path) for path in references}
    need(reference_before == load(HERE / "reference-lock.json")["files"], "Frozen native reference metadata/pixels changed")
    V.recheck(value)
    output.mkdir(exist_ok=False); save(output / "shipped-before.json", ship_before)
    save(output / "source-delta-admission.json", source_delta_admission)
    save(output / "runtime-generated-before.json", {"output": {}, ".godot": {}})
    save(output / "harness-before.json", harness_before); save(output / "reference-inputs-before.json", reference_before)
    environment = os.environ.copy(); runtime = lock["runtime_paths"]
    need(Path(sys.executable).resolve() == Path(runtime["python"]).resolve(), "Use approved pinned Python coordinator")
    environment.update(HYBRID_GODOT=runtime["godot"], HYBRID_PYTHON=runtime["python"], HYBRID_FFMPEG=runtime["ffmpeg"], HYBRID_SOURCE_BLENDER=runtime["blender"], HYBRID_SOURCEIO=str(review / "Dependencies" / ("sourceio-" + built["sourceio_revision"])), PYTHONDONTWRITEBYTECODE="1")
    os.environ["HYBRID_GODOT"] = runtime["godot"]
    runner = module(studio / "run.py", "final_SFM_review_runner")
    pure = module(studio / "tools/verify_owner_review.py", "final_SFM_review_metadata_contract")
    results = []; errors = []; attempts = 0
    try:
        for index, project in enumerate(lock["projects"]):
            case = output/("%02d-" % (index+1)+project["name"]); case.mkdir()
            package = review/"Examples"/(project["title"]+".has")
            need(identity(package) == project["identity"], "Fresh packed example differs")
            expected = pure.metadata(package); save(case/"expected.json", expected)
            actual = load(Path(native_cases[project["name"]]["expected"]))
            chooser = next(row for row in lock["source_chooser"] if row["name"] == project["title"])
            mdl = review/"Native sources"/chooser["folder"]/chooser["relative_MDL"]
            catalogue = load(Path(native_cases[project["name"]]["expected"]).parent/"catalogue.json")
            need(identity(mdl)["sha256"] == catalogue["native_mdl_sha256"] == catalogue["original_source_sha256"], "Copied native MDL identity differs")
            details = {key: actual[key] for key in ("object_id", "parameters", "source_binding", "pictures")}
            for key in ("shape_ui", "native_helper_preview"):
                if key in actual: details[key] = actual[key]
            request = {"format": "has_final_SFM_review_request_1", "package": str(package).replace("\\", "/"),
                       "folder": str(case).replace("\\", "/"), "result": str(case/"result.json").replace("\\", "/"),
                       "source_manifest_sha256": identity(output/"shipped-before.json")["sha256"], "native": details,
                       "audio_sources": audio_expectations(package, expected["audio"]),
                       "chooser": {"MDL": str(mdl).replace("\\", "/"), "sha256": identity(mdl)["sha256"], "catalogue": catalogue,
                                   "mount_overrides": {provider["path"]: False for provider in load(Path(native_cases[project["name"]]["conversion_request"]))["mount_discovery"]["providers"]}}}
            attempts += 1
            results.append(execute(runner, studio, case, request, environment, expected, pure, built["profile"]))
    except BaseException as exc:
        errors.append({"type": type(exc).__name__, "detail": str(exc)})
    finally:
        def capture(label, action):
            try: return action()
            except BaseException as exc:
                errors.append({"phase": label, "type": type(exc).__name__, "detail": str(exc)})
                return None
        capture("validation-recheck", lambda: V.recheck(value))
        ship_after = capture("shipped-after", lambda: shipped_tree(review))
        generated = {name: capture("generated-"+name, lambda name=name: tree(studio/name)) for name in ("output", ".godot")}
        save(output/"shipped-after.json", ship_after); save(output/"runtime-generated-after.json", generated)
        gates = {"shipped_source_projects_dependencies_native_families": ship_before == ship_after,
                 "original_native_families": original_families == capture("originals", lambda: {folder: tree(Path(folder)) for folder in original_families}),
                 "shared_runtime_executables": runtimes_before == capture("executables", lambda: {path: identity(Path(path)) for path in runtimes_before}),
                 "installed_exporter120sources": exporter_before == capture("exporter", lambda: exporter_tree(Path(lock["exporter_root"]))),
                 "original_SourceIO574files": original_sourceio_before == capture("SourceIO", lambda: tree(original_sourceio)),
                 "previous_reviews": old_reviews == capture("previous-reviews", lambda: {path: tree(Path(path)) for path in old_reviews}),
                 "harness": harness_before == capture("harness", lambda: {path: identity(Path(path)) for path in harness_before}),
                 "native_reference_metadata_and_private_frame_inputs": reference_before == capture("native-references", lambda: {path: identity(Path(path)) for path in reference_before}),
                 "full_run_gate": full_gate == capture("full-run-gate", lambda: {path: identity(Path(path)) for path in full_gate})}
        result = {"format": "has_final_SFM_review_validation_1", "source_commit": args.expected_revision, "review": str(review),
                  "passed": not errors and len(results) == 4 and all(row["passed"] for row in results) and all(gates.values()),
                  "results": results, "errors": errors, "preservation": gates, "graphics_processes_requested": attempts,
                  "runtime_generated_files_retained": {name: len(rows) if rows is not None else None for name, rows in generated.items()},
                  "runtime_generated_before_empty": True, "automatic_cleanup": False,
                  "owner_changes_policy": "Retain every output if any shipped/owner change is detected; root reviews exact new generated paths before any later cleanup.",
                  "native_solver": "bounded_five_of49_runtime; actual_relocated_on_fixed_tick_off_here; prior266state102UI_qualified_separately", "no_mock_or_controller_replacement": True,
                  "unchanged_production_and_native_harness_files": len(production_context), "explicit_native_DATA_current_runtime_changes_admitted": sorted(admitted_changes), "source_delta_admission":source_delta_admission,
                  "scope": "Exactly four newly copied examples: ordinary Home/Simple/Open/render, strict saved state, Junko69binding/helpercancel/real_native5OnTickOff, Keiki/Mima shape availability, real four-MDL chooser metadata/cancel. No conversion or clean-install/artist claim."}
        software_checks = sum(row["observed_checks"] for row in results)
        expected_software_checks = sum(row["expected_checks"] for row in results)
        result["passed"] = result["passed"] and software_checks == expected_software_checks == 187
        result.update(software_checks=software_checks, expected_software_checks=expected_software_checks, software_cold187_only=True, owner_manual_review="DEFERRED_no_owner_interruption", portable_acceptance_claimed=False, source_admission_chain="immutable_native_to52_then_explicit_reviewed52_to_qualified_candidate_and_merged_tested_raw")
        save(output/"verification.json", result)
    need(result["passed"], "Final-location validation failed; retain "+str(output))
    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--run-gpu', action='store_true', required=True)
    parser.add_argument('--lease-confirmed', action='store_true', required=True)
    args = parser.parse_args()
    import validation_admission as V
    value = V.require_validated_inputs()
    result = run(value, args.output)
    print(json.dumps({"passed": result["passed"], "software_checks": result["software_checks"], "automatic_cleanup": False}))


if __name__ == "__main__": main()
