"""UNRUN final-location four-example validator; root private lease required.

No review is built or altered here. Frozen production controllers stay unchanged.
Unavoidable generated output/.godot files in the NEW review are inventoried and
retained; this coordinator never deletes, moves or cleans them automatically.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
WORKSPACE = ROOT.parent
NATIVE = ROOT/"output/sfm-bone-bindings-native-launch-20261114T033026205/run"
BUILDER = ROOT/"output/sfm-joints-review-builder-amendment-20261114"
BAD = ("ERROR:", "WARNING:", "SCRIPT ERROR", "SHADER ERROR", "FAIL ", "ObjectDB instances leaked",
       "unclaimed string names", "Pages in use exist at exit", "resources still in use", "_set_transient_exclusive_child")


def need(condition, detail):
    if not condition: raise RuntimeError(detail)


def no_links(path):
    for item in (path, *path.parents):
        try: info = item.lstat()
        except FileNotFoundError: continue
        need(not stat.S_ISLNK(info.st_mode) and not getattr(info, "st_file_attributes", 0)&0x400, "Link/reparse path refused")


def identity(path):
    no_links(path); before = path.stat()
    with path.open("rb") as stream: digest = hashlib.file_digest(stream, "sha256").hexdigest()
    after = path.stat(); need((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns), "Input changed during hashing")
    return {"bytes": after.st_size, "mtime_ns": after.st_mtime_ns, "sha256": digest}


def tree(folder):
    if not folder.exists(): return {}
    no_links(folder); result = {}
    for base, dirs, files in os.walk(folder, followlinks=False):
        for name in dirs+files: no_links(Path(base)/name)
        for name in sorted(files):
            path = Path(base)/name; result[path.relative_to(folder).as_posix()] = identity(path)
    return result


def shipped_tree(review):
    result = {}
    for base, dirs, files in os.walk(review, followlinks=False):
        base = Path(base)
        for name in dirs+files: no_links(base/name)
        if base == review/"Studio": dirs[:] = [n for n in dirs if n not in ("output", ".godot")]
        for name in files:
            path = base/name
            result[path.relative_to(review).as_posix()] = identity(path)
    return result


def exporter_tree(folder):
    return {name: value for name, value in tree(folder).items()
            if "__pycache__" not in Path(name).parts and not name.endswith(".pyc")}


def load(path):
    need(path.stat().st_size <= 16*1024*1024, "Bounded JSON required")
    return json.loads(path.read_bytes())


def save(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=True, allow_nan=False, indent=2); stream.write("\n")


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path); result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result); return result


def extra_names(native):
    names = ["extras.target_available", "extras.unchanged"]
    names += ["render.frame_0", "render.frame_24"]
    names += ["source_binding.relocated."+name for name in ("report_identity", "runtime_bindings", "no_mutation", "no_simulation")]
    names += ["chooser."+name for name in ("file_picker", "dialog", "metadata", "native_catalogue", "default_request", "cancel", "unchanged")]
    if native.get("native_helper_preview"):
        names += ["native_helper."+name for name in ("available", "native_current", "suggested", "existing_mode", "weights_unchanged", "cancelled", "protected_state", "no_simulation")]
    if "shape_ui" in native:
        names += ["shapes.available", "shapes.unchanged"]
        names += ["shapes.binding_"+str(i) for i in range(len(native["shape_ui"]["controls"]))]
    return names


def execute(runner, studio, folder, request, environment, expected, pure, profile):
    request_path = folder/"request.json"; save(request_path, request)
    script = HERE/"replay.gd"; scene = folder/"replay.tscn"
    scene.write_text('[gd_scene load_steps=2 format=3]\n[ext_resource type="Script" path='+json.dumps(script.as_posix())+' id="1"]\n[node name="FinalSFMReviewReplay" type="Node"]\nscript=ExtResource("1")\n', encoding="utf-8", newline="\n")
    args = runner.command(extra=[str(scene), "--audio-driver", "Dummy", "--log-file", str(folder/"engine.log"), "--", str(request_path)])
    need("--script" not in args and "--headless" not in args and all("smoke" not in str(v) for v in args), "Ordinary scene startup required")
    need("--receipt" in args and Path(args[1]).resolve() == studio/"tools/private_desktop.py" and
         Path(args[args.index("--path")+1]).resolve() == studio, "Frozen final private route required")
    receipt_path = folder/"private-receipt.json"; args[args.index("--receipt")+1] = str(receipt_path)
    # The wrapper's own timeout is shorter than the retained Popen wait. Its Job
    # owns the graphical process tree and records its normal closure first.
    args[2:2] = ["--timeout", "405"]
    save(folder/"command.json", args)
    process = subprocess.Popen(args, cwd=studio, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               creationflags=subprocess.CREATE_NO_WINDOW)
    error = None; timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=450)
    except BaseException as exc:
        timed_out = isinstance(exc, subprocess.TimeoutExpired); error = {"type": type(exc).__name__, "detail": str(exc)}
        stdout, stderr = getattr(exc, "stdout", None) or b"", getattr(exc, "stderr", None) or b""
        try:
            if process.poll() is None: process.kill()  # only this retained owned launcher
            stdout, stderr = process.communicate(timeout=20)
        except BaseException as closing: error["closure"] = {"type": type(closing).__name__, "detail": str(closing)}
    (folder/"stdout.log").write_bytes(stdout); (folder/"stderr.log").write_bytes(stderr)
    engine = (folder/"engine.log").read_text(encoding="utf-8", errors="replace") if (folder/"engine.log").is_file() else ""
    texts = [stdout.decode("utf-8", "replace"), stderr.decode("utf-8", "replace"), engine]
    markers = [line for text in texts for line in text.splitlines() if any(token in line for token in BAD)]
    result = load(folder/"result.json") if (folder/"result.json").is_file() else {}
    receipt = load(receipt_path) if receipt_path.is_file() else {}
    expected_extras = extra_names(request["native"])
    checks = result.get("checks", []); ledger = result.get("extra_checks", {})
    cels = sum(len(layer.get("cels", [])) for layer in expected["layers"])
    expected_checks = 20+len(expected["world"]["objects"])+cels+len(expected_extras)
    startup = result.get("normal_startup", {}); recovery = startup.get("result", {})
    result_ok = (result.get("format") == "has_owner_review_replay_1" and result.get("failures") == 0 and
                 type(result.get("native_readbacks_at_finish")) is int and result["native_readbacks_at_finish"] == 0 and
                 len(checks) == expected_checks and all(row.get("ok") is True for row in checks) and
                 set(ledger) == set(expected_extras) and all(value is True for value in ledger.values()) and
                 result.get("request_sha256") == identity(request_path)["sha256"] and
                 result.get("source_manifest_sha256") == request["source_manifest_sha256"] and
                 Path(result.get("project_root", "")).resolve() == studio and result.get("package") == request["package"] and
                 profile in result.get("profile", "") and startup.get("signal_seen") is True and
                 startup.get("home_visible") is True and startup.get("empty") is True and startup.get("simple") is True and
                 recovery.get("restored") is False and recovery.get("cancelled") is False)
    cache = Path(result.get("project_folder", "")).resolve()
    result_ok = result_ok and cache != folder/"has-cache" and cache.is_relative_to((folder/"has-cache").resolve())
    configured = result.get("configured_paths", {})
    result_ok = result_ok and set(configured) == {"recovery", "recent", "display", "HAS_cache", "reference_cache", "source_paths", "workspace"}
    result_ok = result_ok and all(Path(value).resolve().is_relative_to(folder.resolve()) for value in configured.values())
    comparisons = {}
    for phase in ("before", "after", "extra"):
        path = folder/("observed-"+phase+".json")
        comparisons[phase] = pure.compare(expected, load(path)) if path.is_file() else [{"at": "$", "reason": "missing state"}]
    save(folder/"state-comparison.json", {"contract": "Existing owner-review exact data projection; finite numbers1e-12 absolute, no relative tolerance", "differences": comparisons})
    receipt_ok = (receipt.get("format") == "studio_private_desktop_1" and receipt.get("exit") == 0 and
                  all(receipt.get(key) is True for key in ("private_window_seen", "child_desktop_confirmed", "job_closed", "desktop_closed")) and
                  all(receipt.get(key) is False for key in ("foreground_child_observed", "desktop_switch_requested")))
    passed = error is None and not timed_out and process.poll() is not None and process.returncode == 0 and not markers and result_ok and receipt_ok and not any(comparisons.values()) and any("OWNER_REVIEW_REPLAY " in text for text in texts[:2])
    proof = {"passed": passed, "retained_Popen_reaped": process.poll() is not None, "exit": process.returncode,
             "timed_out": timed_out, "execution_error": error, "error_markers": markers, "strict_result_binding": result_ok,
             "expected_checks": expected_checks, "observed_checks": len(checks), "named_extra_checks": len(expected_extras),
             "private_receipt_passed": receipt_ok, "private_receipt": str(receipt_path), "cache_contained": cache.is_relative_to((folder/"has-cache").resolve()),
             "normal_scene_startup": True, "controllers_unmodified": True}
    save(folder/"process-verification.json", proof)
    need(passed, "Final review case failed; retain "+str(folder))
    return proof


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", type=Path, required=True); parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-revision", required=True)
    parser.add_argument("--run-gpu", action="store_true", required=True); parser.add_argument("--lease-confirmed", action="store_true", required=True)
    args = parser.parse_args(); need(os.name == "nt", "Approved Windows private route required")
    release_context = load(HERE/"release-context.json")
    need(args.expected_revision == release_context["source_commit"], "Use the newly declared post-manifest-fix full revision")
    review = args.review.resolve(strict=True); output = args.output.absolute(); no_links(review); no_links(output)
    need(review.parent == WORKSPACE and review.name == "HAS-Review-20261113-SFM-Joints-"+args.expected_revision[:7], "Exact new review boundary required")
    need(output.resolve().is_relative_to((ROOT/"output").resolve()) and output != ROOT/"output" and not output.exists(), "New owned evidence boundary required")
    studio = review/"Studio"; built = load(review/"BUILD-VERIFICATION.json"); lock = load(BUILDER/"input-lock.json")
    need(built.get("passed") is True and built.get("source_commit") == args.expected_revision and built.get("native_sources_included") is True,
         "New exact source build with copied native sources required")
    preparation = {str(BUILDER/name): identity(BUILDER/name) for name in ("build_after_full.py", "input-lock.json", "README.template.md")}
    need(built.get("builder_preparation") == preparation, "Reviewed successor builder/template/input identities differ")
    full_gate = built.get("full_run_gate", {})
    need(full_gate and all(identity(Path(path)) == expected for path, expected in full_gate.items()), "Builder full-run gate files changed")
    full_states = [Path(path) for path in full_gate if Path(path).name == "state.json"]
    need(len(full_states) == 1, "Exactly one passed full-run state required")
    full_state = load(full_states[0])
    need(full_state.get("source_commit") == args.expected_revision and full_state.get("status") == "passed" and
         full_state.get("suite_exit") == 0 and full_state.get("source_unchanged") is True, "Full suite did not pass; validator cannot launch")
    need(full_states[0].parent.resolve() == Path(release_context["canonical_run"]).resolve(), "Wrong eventual full run")
    need(not tree(studio/"output") and not tree(studio/".godot"), "Review is no longer fresh; preserve any owner work and retain outputs")
    need(tree(review/"Dependencies"/("sourceio-"+built["sourceio_revision"])) == lock["sourceio_files"], "Copied SourceIO no longer matches the builder input")
    for row in lock["source_chooser"]:
        need(tree(review/"Native sources"/row["folder"]) == lock["native_families"][row["resource_root"]],
             "Copied native family no longer matches the immutable original: "+row["name"])
    ship_before = shipped_tree(review)
    for name, digest in built["source_hashes"].items(): need(identity(studio/name)["sha256"] == digest, "Frozen Studio source differs")
    native_path = NATIVE/"verification.json"
    need(identity(native_path) == lock["native_verification"], "Frozen actual native verification identity differs")
    native = load(native_path)
    need(identity(native_path) == lock["native_verification"] and native.get("passed") is True and
         all(value is True for value in native.get("preservation", {}).values()) and native.get("preservation"),
         "Current exact four-case native verification/preservation required")
    admitted_changes = set(release_context["test_only_followup_files"])
    production_context = []
    def functional(name):
        return name.split("/", 1)[0] in ("src", "tests", "tools", "data", "examples") or name in ("main.tscn", "project.godot", "run.py", "launch.pyw")
    native_members = {name for name in native["source_before"]["files"] if functional(name)}
    final_members = {name for name in built["source_hashes"] if functional(name)}
    need(native_members == final_members, "Production/native-harness functional source membership differs")
    text_suffixes = {".py", ".pyw", ".gd", ".gdshader", ".tscn", ".tres", ".json", ".godot", ".cfg", ".uid", ".txt", ".md", ".svg"}
    text_paths = {"tests/blank", "tests/krita_fixture/has_fixture.desktop", "tools/docker/sourceio_metadata.Dockerfile",
                  "tools/docker/sourceio_worker.Dockerfile", "tools/krita-runtime.Dockerfile"}
    for name, row in native["source_before"]["files"].items():
        if name in admitted_changes or not functional(name):
            continue
        original = NATIVE/"Studio"/name; final = studio/name
        need(identity(original)["sha256"] == row["sha256"], "Retained actual native source snapshot changed")
        original_bytes = original.read_bytes(); final_bytes = final.read_bytes()
        need(original_bytes == final_bytes or (original.suffix in text_suffixes or name in text_paths) and
             original_bytes.replace(b"\r\n", b"\n") == final_bytes.replace(b"\r\n", b"\n"),
             "Final production/native-harness content differs from actual four-case source: "+name)
        production_context.append(name)
    native_cases = {row["name"]: row for row in native["writer"]["result"]["cases"]}
    original_families = {folder: tree(Path(folder)) for folder in lock["native_families"]}
    need(original_families == lock["native_families"], "Original source family changed")
    runtimes_before = {path: identity(Path(path)) for path in lock["runtime_executables"]}
    need(runtimes_before == lock["runtime_executables"], "Approved runtime changed")
    exporter_before = exporter_tree(Path(lock["exporter_root"])); need(exporter_before == lock["exporter_noncache_sources"], "Installed exporter differs")
    original_sourceio = ROOT/"output/dependencies"/("sourceio-"+built["sourceio_revision"])
    original_sourceio_before = tree(original_sourceio); need(original_sourceio_before == lock["sourceio_files"], "Original approved SourceIO differs")
    old_reviews = {str(path): tree(path) for path in WORKSPACE.glob("HAS-Review-*") if path.is_dir() and path != review}
    harness_before = {str(path): identity(path) for path in (Path(__file__), HERE/"replay.gd", HERE/"release-context.json", HERE/"reference-lock.json", BUILDER/"input-lock.json")}
    harness_before.update(preparation)
    references = [NATIVE/"verification.json"]
    for item in native_cases.values():
        expected_path = Path(item["expected"]); actual = load(expected_path)
        references += [expected_path, expected_path.parent/"catalogue.json", Path(item["conversion_request"])]
        references += [Path(row["path"]) for row in actual["pictures"].values()]
    reference_before = {str(path): identity(path) for path in references}
    need(reference_before == load(HERE/"reference-lock.json")["files"], "Frozen native reference metadata/pixels changed")
    output.mkdir(exist_ok=False); save(output/"shipped-before.json", ship_before)
    save(output/"runtime-generated-before.json", {"output": {}, ".godot": {}})
    save(output/"harness-before.json", harness_before)
    save(output/"reference-inputs-before.json", reference_before)
    environment = os.environ.copy(); runtime = lock["runtime_paths"]
    need(Path(sys.executable).resolve() == Path(runtime["python"]).resolve(), "Use the approved pinned Python coordinator")
    environment.update(HYBRID_GODOT=runtime["godot"], HYBRID_PYTHON=runtime["python"], HYBRID_FFMPEG=runtime["ffmpeg"],
                       HYBRID_SOURCE_BLENDER=runtime["blender"], HYBRID_SOURCEIO=str(review/"Dependencies"/("sourceio-"+built["sourceio_revision"])),
                       PYTHONDONTWRITEBYTECODE="1")
    os.environ["HYBRID_GODOT"] = runtime["godot"]
    runner = module(studio/"run.py", "final_SFM_review_runner")
    pure = module(studio/"tools/verify_owner_review.py", "final_SFM_review_metadata_contract")
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
                  "native_solver": "not_implemented", "no_mock_or_controller_replacement": True,
                  "unchanged_production_and_native_harness_files": len(production_context), "test_only_followup_files_admitted": sorted(admitted_changes),
                  "scope": "Exactly four newly copied examples: ordinary Home/Simple/Open/render, strict saved state, Junko69binding/helpercancel, Keiki/Mima shape availability, real four-MDL chooser metadata/cancel. No conversion or clean-install/artist claim."}
        save(output/"verification.json", result)
    need(result["passed"], "Final-location validation failed; retain "+str(output))
    print(json.dumps({"passed": True, "verification": str(output/"verification.json"), "automatic_cleanup": False}))


if __name__ == "__main__": main()
