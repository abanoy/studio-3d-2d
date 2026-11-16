"""Prepare new context-bound recipes; never import them or run a test/app.

Reads only old committed preparation/source and root-owned initial run metadata.
Writes only this reserved experiment folder. Final reports/receipts/closure are
not read: those are still future terminal gates owned by the root worker.
"""
from pathlib import Path
import ast
import difflib
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OLD = ROOT / "experiments/owner_pause_20261114/prepared-unrun"
REVISION = "f0dd57a2e568089d396fecba819ab987da658bf0"
RUN_NAME = "windows-canonical-bone-binding-20261115T225514304"
RUN = ROOT / "output" / RUN_NAME
FINAL = ROOT.parent / ("HAS-Review-20261115-SFM-Joints-" + REVISION[:7])
OLD_REVISION = "f380729cb170682068017b0d4c29b5f8425cdd14"
OLD_RUN_NAME = "windows-canonical-bone-binding-20261114T040946652"
NAMES = {
    "publication": "windows-canonical-bone-binding-retry-publication-prep-20261114",
    "builder": "sfm-joints-review-builder-amendment-20261114",
    "replay": "sfm-joints-final-validator-amendment-20261114",
}


def require(value, detail):
    if not value:
        raise ValueError(detail)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def packed(value):
    return (json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False) + "\n").encode("utf-8")


def replace_once(text, before, after):
    require(text.count(before) == 1, "Unexpected substitution count: " + before)
    return text.replace(before, after)


def main():
    require(ROOT == Path(r"C:\a\Programming\cloudflare\has-acceptance-session-20261111"), "Wrong owned checkout")
    require(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == REVISION, "HEAD changed")
    require(not any((HERE / name).exists() for name in NAMES), "Preserve previous successor outputs")
    require(not FINAL.exists(), "Preserve existing final review")
    raw_inputs = {name: (RUN / name).read_bytes() for name in ("launch.json", "source-before.json", "coordinator-children-observed.json")}
    launch, sources, live = (json.loads(raw_inputs[name]) for name in ("launch.json", "source-before.json", "coordinator-children-observed.json"))
    require(launch["source_commit"] == sources["commit"] == live["source_commit"] == REVISION, "Initial source context differs")
    require(launch["pid"] == live["coordinator"]["pid"] == 15824 and launch["creation_utc"] == live["coordinator"]["creation_utc"] == "2026-11-15T22:55:14.3418333Z", "Coordinator identity differs")
    require(live["python"]["pid"] == 16040 and live["python"]["parent_pid"] == 15824 and live["python"]["creation_utc"] == "2026-11-15T22:55:28.0068371Z", "Python identity differs")
    require(live["python"]["command_line"] == '"C:\\Program Files\\Python313\\python.exe" -u tests/verify.py' and Path(live["canonical_run"]) == RUN, "Live command/run differs")
    require(len(sources["source_sha256"]) == 1008, "Functional membership changed; re-review before preparing")
    changed = subprocess.check_output(["git", "diff", "--name-only", OLD_REVISION, REVISION, "--", "src", "tests", "tools", "data", "examples", "project.godot", "main.tscn", "run.py", "launch.pyw"], cwd=ROOT, text=True).splitlines()
    require(not changed, "Current functional Git source differs from the reviewed predecessor")
    for name, digest in sources["source_sha256"].items():
        require(sha((ROOT / name).read_bytes()) == digest, "Current functional source changed: " + name)

    files = {}
    originals = {}
    comparisons = []

    def copy(group, name):
        raw = (OLD / NAMES[group] / name).read_bytes()
        files[group + "/" + name] = raw
        originals[group + "/" + name] = {"path": (OLD / NAMES[group] / name).relative_to(ROOT).as_posix(), "bytes": len(raw), "sha256": sha(raw)}
        return raw

    publication_modules = ("preflight_terminal.py", "publication_gates.py", "summarize_canonical.py", "audit_receipts.py", "finalize_receipt_index.py", "build_consolidated_packet.py")
    for name in publication_modules:
        copy("publication", name)
    gates = files["publication/publication_gates.py"].decode("utf-8")
    gates = replace_once(gates, "and value['python']['command'] == context['suite_python_command'], 'Exact coordinator/Python observation differs')", "and value['python']['command_line'] == context['suite_python_command']\n            and value['checked_utc'] == context['children_observation_checked_utc']\n            and Path(value['canonical_run']) == run, 'Exact coordinator/Python observation differs')")
    files["publication/publication_gates.py"] = gates.encode("utf-8")
    registry = json.loads(copy("publication", "RESULT_REGISTRY.json"))
    require(registry["verifier_sha256"] == sources["source_sha256"]["tests/verify.py"], "Source registry verifier pin changed")
    registry["source_commit"] = REVISION
    files["publication/RESULT_REGISTRY.json"] = packed(registry)
    context = json.loads(copy("publication", "RUN_EXPECTATIONS.json"))
    context.update({
        "source_commit": REVISION, "run_name": RUN_NAME,
        "source_before_sha256": sha(raw_inputs["source-before.json"]),
        "launch_sha256": sha(raw_inputs["launch.json"]),
        "children_observation_sha256": sha(raw_inputs["coordinator-children-observed.json"]),
        "children_observation_checked_utc": live["checked_utc"],
        "children_observation_command_field": "command_line",
        "coordinator_pid": 15824, "coordinator_creation_utc": launch["creation_utc"],
        "python_pid": 16040, "python_creation_utc": live["python"]["creation_utc"],
        "result_registry_sha256": sha(files["publication/RESULT_REGISTRY.json"]),
        "prior_paused_full_status": "USER_CANCELLED_INCOMPLETE_NOT_PASS; preserve original raw failed/exit-1",
    })
    files["publication/RUN_EXPECTATIONS.json"] = packed(context)

    for name in ("build_after_full.py", "input-lock.json", "README.template.md"):
        copy("builder", name)
    builder = files["builder/build_after_full.py"].decode("utf-8")
    builder = replace_once(builder, "ROOT = HERE.parents[1]", "ROOT = HERE.parents[2]  # experiments/resume_full_20261115/builder")
    builder = replace_once(builder, OLD_REVISION, REVISION)
    builder = replace_once(builder, OLD_RUN_NAME, RUN_NAME)
    builder = replace_once(builder, "Only the reviewed f380 revision and exact040946652 full run are admitted", "Only the reviewed f0dd57a revision and exact225514304 full run are admitted")
    builder = replace_once(builder, '"HAS-Review-20261113-SFM-Joints-"', '"HAS-Review-20261115-SFM-Joints-"')
    files["builder/build_after_full.py"] = builder.encode("utf-8")
    files["builder/command.json"] = packed({"status": "UNRUN_requires_exact_fresh_full_PASS_and_root_release", "command": [r"C:\Program Files\Python313\python.exe", "-B", str(HERE / "builder/build_after_full.py"), "--revision", REVISION, "--canonical-run", str(RUN), "--canonical-host-proof", str(RUN / "authoritative-host-termination.json"), "--final", str(FINAL), "--execute-after-full", "--allow-checkout-eol"]})

    for name in ("validate_after_full.py", "replay.gd", "reference-lock.json", "release-context.json"):
        copy("replay", name)
    replay = files["replay/validate_after_full.py"].decode("utf-8")
    replay = replace_once(replay, "ROOT = HERE.parents[1]", "ROOT = HERE.parents[2]  # experiments/resume_full_20261115/replay")
    replay = replace_once(replay, 'BUILDER = ROOT/"output/sfm-joints-review-builder-amendment-20261114"', 'BUILDER = HERE.parent/"builder"')
    replay = replace_once(replay, '"HAS-Review-20261113-SFM-Joints-"', '"HAS-Review-20261115-SFM-Joints-"')
    files["replay/validate_after_full.py"] = replay.encode("utf-8")
    release = json.loads(files["replay/release-context.json"])
    release.update({"source_commit": REVISION, "canonical_run": str(RUN), "status_at_preparation": "RUNNING_NOT_ELIGIBLE", "prior_paused_full": "output/" + OLD_RUN_NAME, "prior_paused_full_status": "USER_CANCELLED_INCOMPLETE_NOT_PASS"})
    files["replay/release-context.json"] = packed(release)
    files["replay/command.json"] = packed({"status": "UNRUN_requires_built_review_exact_PASS_and_new_root_private_lease", "command": [r"C:\Program Files\Python313\python.exe", "-B", str(HERE / "replay/validate_after_full.py"), "--review", str(FINAL), "--output", str(ROOT / "output/sfm-joints-final-validation-f0dd57a-20261115"), "--expected-revision", REVISION, "--run-gpu", "--lease-confirmed"]})

    for name, old in originals.items():
        new = files[name]
        comparisons.append({"path": name, "original": old, "successor_bytes": len(new), "successor_sha256": sha(new), "byte_identical": old["sha256"] == sha(new)})
        if name.endswith(".py"):
            ast.parse(new.decode("utf-8"), filename=name)
            before = (ROOT / old["path"]).read_text(encoding="utf-8").splitlines(keepends=True)
            after = new.decode("utf-8").splitlines(keepends=True)
            files["diffs/" + name.replace("/", "__") + ".diff"] = "".join(difflib.unified_diff(before, after, fromfile=old["path"], tofile=name)).encode("utf-8")
    files["SOURCE_REVIEW.json"] = packed({
        "format": "has_resumed_full_successor_static_review_1", "source_commit": REVISION, "canonical_run": str(RUN),
        "status": "PREPARED_UNRUN_NOT_TERMINAL_AUTHORIZATION", "functional_source_entries_observed": 1008,
        "functional_git_delta_from_f380": changed, "frozen_working_functional_source_match": True,
        "initial_root_metadata": {name: {"bytes": len(raw), "sha256": sha(raw)} for name, raw in raw_inputs.items()},
        "python_AST_parsed_only": True, "recipe_modules_imported_or_executed": False, "GDScript_parsed_or_run": False,
        "proposed_final_replay_checks": 168, "controller_predicates_or_counts_changed": False,
        "live_proof_schema_change": "Root raw manifest is preserved: command_line and checked_utc replace predecessor command/observed_utc. Exact raw SHA, PID/birth/parent/command still required; new checked_utc/run-path checks tighten admission.",
        "source_context": "Current docs-only f0dd revision retains all f380 functional code. Prior incomplete/failed fulls stay separate; no report or terminal PASS read during preparation.",
        "comparisons": comparisons,
    })
    files["README.md"] = ("# Fresh full and SFM review successor preparations — November 15, 2026\n\n"
        "Prepared against the actual running full at `output/" + RUN_NAME + "`, revision `" + REVISION + "`. No terminal PASS, source-after, final verification, raw canonical log, receipt audit, publication, builder or replay execution is claimed. The interrupted November 14 full stays USER_CANCELLED_INCOMPLETE; earlier failed fulls remain failed.\n\n"
        "`publication` preserves all preceding terminal/source/result/receipt/host/release gates. Its fresh context pins root-written launch, source-before and live child metadata. The root's live child record uses `command_line` and `checked_utc`; the successor checks those exact fields plus the canonical path. No raw record is rewritten. Five publication modules are byte-identical; only the live-proof field admission changes in publication_gates.py.\n\n"
        "`builder` pins only this revision and exact run. Its root derivation accounts for the deeper experiment folder. Final target is the new sibling `" + FINAL.name + "`; old reviews/installations are preserved. Runtime, source-family, native verification, SourceIO, exporter, source-context, Git-byte/text-EOL and fresh-target gates remain unchanged. Current HEAD must still match the tested revision when it executes.\n\n"
        "`replay` uses that builder/final target, exact future passed full, unchanged replay.gd and reference-lock.json. Proposed counts remain 41/43/46/38 = 168; no runtime predicate changed. Runtime parsing/graphics and actual immutable input checks remain UNRUN. No controller shim or source edit is introduced.\n\n"
        "Root must review SOURCE_REVIEW.json and diffs, then supply exact terminal host hashes before preflight/audit/summary; supply a genuine graphics release before finalizing/consolidating evidence. Build only after actual PASS/closure and before advancing HEAD. Final-location replay needs its own new private graphics lease after the build. Commands in builder/command.json and replay/command.json are future actions, not permission granted by preparation.\n\n"
        "Publication order: preflight_terminal.py; audit_receipts.py; summarize_canonical.py into publication/actual-summary; root-written genuine graphics release; finalize_receipt_index.py; build_consolidated_packet.py. Every invocation needs its existing explicit CLI hashes/terminal flags. Retain generated outputs and failed attempts; do not run against running/failed/source-changed state. No original artwork/HAS/GLB/media/native coordinate oracle/runtime binary is included here.\n").encode("utf-8")
    for name, raw in files.items():
        target = HERE / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(raw)
    for group in NAMES:
        rows = [{"path": name.removeprefix(group + "/"), "bytes": len(raw), "sha256": sha(raw)} for name, raw in sorted(files.items()) if name.startswith(group + "/")]
        with (HERE / group / "INDEX.json").open("xb") as stream:
            stream.write(packed({"format": "has_prepared_successor_index_1", "source_commit": REVISION, "status": "PREPARED_UNRUN", "files": rows, "file_count": len(rows), "bytes": sum(row["bytes"] for row in rows)}))
    for name, raw in raw_inputs.items():
        require((RUN / name).read_bytes() == raw, "Root initial metadata changed during preparation")
    print(json.dumps({"prepared": str(HERE), "source_commit": REVISION, "status": "UNRUN", "compared_originals": len(comparisons), "byte_identical_originals": sum(row["byte_identical"] for row in comparisons), "replay_gd_identical": files["replay/replay.gd"] == (OLD / NAMES["replay"] / "replay.gd").read_bytes(), "final_target": str(FINAL)}, indent=2))


if __name__ == "__main__":
    main()
