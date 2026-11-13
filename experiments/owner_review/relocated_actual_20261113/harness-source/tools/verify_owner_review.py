"""Private six-package replay preparation and explicitly invoked GPU validation.

No Studio is created here. The committed-source builder must finish first.
Default action reads bounded JSON metadata only; --run-gpu is opt-in.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import re
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import time
import zipfile

SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parents[1]
OUTPUT_ROOT = ROOT / "output"
REPLAY_SCRIPT = ROOT / "tests/owner_review_replay.gd"
GUIDE = ROOT / "docs/owner_review_validation.md"
EVIDENCE_ROOT: Path | None = None
MAX_META = 1024 * 1024
sys.dont_write_bytecode = True


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def no_reparse(path: Path):
    """Reject links/junctions from this checkout boundary down to the target."""
    require(path.is_absolute(), f"Expected absolute path: {path}")
    require(path.is_relative_to(ROOT), f"Path escaped this checkout: {path}")
    for item in [ROOT, *reversed(path.relative_to(ROOT).parents), path]:
        candidate = item if item.is_absolute() else ROOT / item
        try:
            info = candidate.lstat()
        except FileNotFoundError:
            continue
        require(not stat.S_ISLNK(info.st_mode) and not (getattr(info, "st_file_attributes", 0) & 0x400), f"Reparse path refused: {candidate}")
    require(path.resolve().is_relative_to(ROOT.resolve()), f"Resolved path escaped checkout: {path}")


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stamp(path):
    no_reparse(path)
    info = path.stat()
    require(path.is_file(), f"Expected file: {path}")
    return {"bytes": info.st_size, "mtime_ns": info.st_mtime_ns, "sha256": sha(path)}


def read_json(path):
    no_reparse(path)
    require(path.stat().st_size <= 4 * MAX_META, f"Oversized JSON: {path}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path, value):
    no_reparse(path)
    require(EVIDENCE_ROOT is not None and path.is_relative_to(EVIDENCE_ROOT), f"Evidence must remain under the fresh run folder: {EVIDENCE_ROOT}")
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def metadata(package):
    # In-memory bounded metadata read only: no GLB/art/audio payload is extracted.
    with zipfile.ZipFile(package) as archive:
        names = archive.namelist()
        require(names.count("project.json") == 1 and names.count("has.json") == 1, "Missing/duplicate metadata member")
        for name in ["project.json", "has.json"]:
            entry = archive.getinfo(name)
            require(entry.file_size <= MAX_META, f"Oversized {name}")
        header = json.loads(archive.read("has.json"))
        project = json.loads(archive.read("project.json"))
    require(header["storage"] == "packed", "Review package must be packed")
    require(project.get("schema_version") == 4, "Only the six observed schema4 packages are accepted; no implicit migration")
    require(set(project) <= {"schema_version", "world", "camera_keys", "video", "editor", "layers", "audio", "palette"}, "Unreviewed saved field requires an explicit comparison contract")
    # Schema4 permits no palette property; the current loader materializes [].
    project.setdefault("palette", [])
    return project


def prepare(folder, review):
    copies = read_json(review / "project-copies.json")
    preflight = read_json(review / "project-package-verification.json")
    require(len(copies) == 6 and len({row["name"].casefold() for row in copies}) == 6, "Expected six distinct review copies")
    indexed = {row["name"]: row for row in preflight["projects"]}
    packages = []
    for index, row in enumerate(copies):
        name = row["name"]
        require(Path(name).name == name and name.endswith(".has"), "Unsafe package name")
        package = review / name
        baseline = stamp(package)
        require(baseline["sha256"] == row["sha256"].lower() and baseline["bytes"] == row["bytes"], f"Copy manifest mismatch: {name}")
        proof = indexed[name]
        require(proof["sha256"].lower() == baseline["sha256"] and proof["source_unchanged"] and proof["all_payload_sha256_and_crc_readback"], f"Missing package preflight: {name}")
        expected = metadata(package)
        case = folder / f"{index + 1:02d}-{Path(name).stem.replace(' ', '-').lower()}"
        case.mkdir()
        write_json(case / "expected.json", expected)
        request = {"format": "has_owner_review_replay_request_1", "package": str(package).replace("\\", "/"), "folder": str(case).replace("\\", "/"), "result": str(case / "result.json").replace("\\", "/")}
        write_json(case / "request.json", request)
        packages.append({"name": name, "path": str(package), "case": str(case), "before": baseline, "origin": row.get("origin", "Existing native owner-review package"), "evidence": row.get("evidence")})
    write_json(folder / "package-baseline.json", packages)
    return packages


def source_manifest(studio):
    result = {}
    for base, dirs, files in os.walk(studio, followlinks=False):
        base = Path(base)
        for name in list(dirs):
            no_reparse(base / name)
        dirs[:] = sorted(name for name in dirs if name not in {"output", ".godot", "__pycache__"})
        for name in sorted(files):
            if name.endswith((".pyc", ".pyo")):
                continue
            path = base / name
            result[path.relative_to(studio).as_posix()] = stamp(path)
    return result


def compare(expected, actual, at="$", mismatches=None):
    if mismatches is None:
        mismatches = []
    if len(mismatches) >= 100:
        return mismatches
    if isinstance(expected, bool) or isinstance(actual, bool):
        equal = type(expected) is type(actual) and expected == actual
    elif isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        # JSON may decode a saved integer as a Godot float. IDs remain strings.
        equal = math.isfinite(expected) and math.isfinite(actual) and (expected == actual or (abs(expected) < 2**53 and abs(actual) < 2**53 and math.isclose(expected, actual, rel_tol=0, abs_tol=1e-12)))
    elif isinstance(expected, dict) and isinstance(actual, dict):
        if set(expected) != set(actual):
            mismatches.append({"at": at, "reason": "dictionary keys", "missing": sorted(set(expected) - set(actual)), "added": sorted(set(actual) - set(expected))})
        for key in sorted(set(expected) & set(actual)):
            compare(expected[key], actual[key], at + "." + key, mismatches)
        return mismatches
    elif isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            mismatches.append({"at": at, "reason": "array length", "expected": len(expected), "actual": len(actual)})
        for index, (left, right) in enumerate(zip(expected, actual)):
            compare(left, right, f"{at}[{index}]", mismatches)
        return mismatches
    else:
        equal = type(expected) is type(actual) and expected == actual
    if not equal:
        # Keep private art-derived metadata out of console logs; exact differences
        # stay in the owned evidence JSON, whose upload is not authorized.
        mismatches.append({"at": at, "reason": "value", "expected": expected, "actual": actual})
    return mismatches


def load_runner(studio):
    spec = importlib.util.spec_from_file_location("owner_review_validation_runner", studio / "run.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(module.ROOT.resolve() == studio.resolve(), "Runner is not rooted in the review Studio")
    return module


def write_replay_scene(case):
    scene = case / "replay.tscn"
    no_reparse(scene)
    require(EVIDENCE_ROOT is not None and scene.is_relative_to(EVIDENCE_ROOT), "Replay scene must stay in the fresh evidence directory")
    require(not scene.exists(), "Replay scene must be fresh")
    script_path = json.dumps(str(REPLAY_SCRIPT).replace("\\", "/"), ensure_ascii=False)
    scene.write_text('[gd_scene load_steps=2 format=3]\n\n'
                     '[ext_resource type="Script" path=' + script_path + ' id="1_replay"]\n\n'
                     '[node name="OwnerReviewReplay" type="Node"]\n'
                     'script = ExtResource("1_replay")\n', encoding="utf-8")
    return scene


def cache_containment(case, value):
    result = {"reported": value, "expected_cache": str(case / "has-cache"), "contained": False}
    try:
        require(isinstance(value, str) and bool(value), "Replay did not report its unpacked project folder")
        actual = Path(value)
        no_reparse(actual)
        actual = actual.resolve(strict=True)
        expected = (case / "has-cache").resolve(strict=True)
        require(actual.is_dir() and actual != expected and actual.is_relative_to(expected), "Unpacked project escaped the fresh owned cache")
        result.update(contained=True, resolved_project_folder=str(actual), resolved_cache=str(expected))
    except (OSError, RuntimeError, ValueError) as error:
        result["error"] = str(error)
    return result


def run_gpu(folder, packages, revision, review):
    require(os.name == "nt", "This replay requires the approved Windows private desktop launcher")
    studio = review / "Studio"
    no_reparse(studio)
    require(studio.is_dir(), "Builder-owned Studio is absent; run the approved snapshot builder first")
    built = read_json(review / "source-snapshot-verification.json")
    require(built["source_mode"] == "git_revision" and built["source_commit"].startswith(revision), "Builder revision does not match the requested canonical checkpoint")
    require(Path(built["target"]).resolve() == studio.resolve(), "Builder target does not match review Studio")
    startup = built["normal_startup"]
    require(startup["home_visible"] and startup["simple"] and startup["empty"] and built["profile"] in startup["profile"], "Builder's normal startup proof is missing")
    private = built["private_receipt"]
    require(private["exit"] == 0 and private["child_desktop_confirmed"] and not private["foreground_child_observed"] and private["job_closed"] and private["desktop_closed"], "Builder's private startup receipt is not clean")
    before = source_manifest(studio)
    for name, digest in built["source_hashes"].items():
        parts = PurePosixPath(name)
        require(not parts.is_absolute() and ".." not in parts.parts, "Unsafe source proof path")
        require(name in before and before[name]["sha256"] == digest, f"Committed source mismatch before replay: {name}")
    write_json(folder / "source-before.json", before)
    write_json(folder / "snapshot-context.json", {"source_commit": built["source_commit"], "source_mode": built["source_mode"], "builder_profile": built["profile"], "source_snapshot_proof": str(review / "source-snapshot-verification.json"), "common_os_profile": True, "per_project_fresh_process_and_app_paths": True})
    harness_paths = {"tools/verify_owner_review.py": SCRIPT, "tests/owner_review_replay.gd": REPLAY_SCRIPT, "docs/owner_review_validation.md": GUIDE}
    harness_before = {name: stamp(path) for name, path in harness_paths.items()}
    write_json(folder / "harness-before.json", harness_before)
    results = []
    try:
        runner = load_runner(studio)
        for row in packages:
            case = Path(row["case"])
            require(stamp(Path(row["path"])) == row["before"], f"Package changed before open: {row['name']}")
            scene = write_replay_scene(case)
            args = runner.command(extra=[str(scene), "--audio-driver", "Dummy", "--log-file", str(case / "engine.log"), "--", str(case / "request.json")])
            require("--receipt" in args and "private_desktop.py" in args[1], "Runner did not select the approved private desktop")
            require("--script" not in args, "Replay must use the ordinary scene startup path")
            receipt_path = case / "private-receipt.json"
            args[args.index("--receipt") + 1] = str(receipt_path)
            write_json(case / "command.json", args)
            process = subprocess.run(args, cwd=studio, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=200)
            log = process.stdout + process.stderr
            (case / "process.log").write_text(log, encoding="utf-8")
            report = read_json(case / "result.json") if (case / "result.json").is_file() else {}
            receipt = read_json(receipt_path) if receipt_path.is_file() else {}
            problems = []
            if process.returncode != 0 or "OWNER_REVIEW_REPLAY " not in log:
                problems.append("Replay process failed or completion marker absent")
            if any(marker in log for marker in ["ERROR:", "FAIL ", "ObjectDB instances leaked", "_set_transient_exclusive_child"]):
                problems.append("Engine log contains an error/failure/leak marker")
            if not (receipt.get("exit") == 0 and receipt.get("child_desktop_confirmed") and not receipt.get("foreground_child_observed", True) and receipt.get("job_closed") and receipt.get("desktop_closed")):
                problems.append("Private desktop receipt is not clean")
            if report.get("failures", 1) != 0 or built["profile"] not in report.get("profile", ""):
                problems.append("Replay checks/profile mismatch")
            if Path(report.get("project_root", "")).resolve() != studio.resolve():
                problems.append("Replay loaded a different project root")
            startup_replay = report.get("normal_startup", {})
            recovery = startup_replay.get("result", {})
            if not (startup_replay.get("signal_seen") and startup_replay.get("home_visible") and startup_replay.get("empty") and startup_replay.get("simple") and not recovery.get("restored", True) and not recovery.get("cancelled", True)):
                problems.append("Ordinary fresh recovery/Home startup proof is missing")
            cache = cache_containment(case, report.get("project_folder"))
            write_json(case / "cache-containment.json", cache)
            if not cache["contained"]:
                problems.append("Resolved unpacked project folder is outside its fresh owned cache")
            expected = read_json(case / "expected.json")
            differences = {}
            for phase in ["before", "after"]:
                observed = case / f"observed-{phase}.json"
                differences[phase] = compare(expected, read_json(observed)) if observed.is_file() else [{"at": "$", "reason": "missing observed state"}]
            write_json(case / "state-comparison.json", {"contract": "Exact dictionaries/strings/bools/array order; finite numeric JSON tolerance 1e-12 absolute, no relative tolerance; IDs exact strings. Only absent schema4 palette materializes []. Runtime source paths and raster ownership omitted by explicit portable projection.", "differences": differences})
            if any(differences.values()):
                problems.append("Saved metadata differs from normally loaded state")
            after_package = stamp(Path(row["path"]))
            if after_package != row["before"]:
                problems.append("Input package bytes/mtime changed")
            item = {"name": row["name"], "passed": not problems, "problems": problems, "case": str(case), "package_after": after_package, "private_receipt": str(receipt_path)}
            write_json(case / "verification.json", item)
            results.append(item)
            print(f"{'PASS' if item['passed'] else 'FAIL'} {row['name']}")
    finally:
        after = source_manifest(studio)
        write_json(folder / "source-after.json", after)
        changed = [name for name in sorted(set(before) | set(after)) if before.get(name) != after.get(name)]
        package_after = {row["name"]: stamp(Path(row["path"])) for row in packages}
        package_changed = [row["name"] for row in packages if package_after[row["name"]] != row["before"]]
        harness_after = {name: stamp(path) for name, path in harness_paths.items()}
        final = {"format": "has_owner_review_validation_1", "source_commit": built["source_commit"], "results": results, "all_six_passed": len(results) == 6 and all(row["passed"] for row in results), "source_hash_size_mtime_changes": changed, "source_before": str(folder / "source-before.json"), "source_after": str(folder / "source-after.json"), "package_changes": package_changed, "package_after": package_after, "harness_unchanged": harness_before == harness_after, "scope": "Actual runnable committed-source copy, normal .has worker loading, saved-state preservation and native GPU captures/Setup/Focus. No artist-fidelity approval, clean-machine/install portability, real-time performance or six-movie claim.", "private_art_uploaded": False}
        final["passed"] = final["all_six_passed"] and not changed and not package_changed and final["harness_unchanged"]
        write_json(folder / "verification.json", final)
    require(final["passed"], f"Review replay did not pass; inspect {folder / 'verification.json'}")


def scoped_output_path(value: Path, label: str) -> Path:
    path = value.expanduser()
    require(".." not in path.parts, f"Parent traversal refused for {label}: {path}")
    if not path.is_absolute():
        path = ROOT / path
    no_reparse(path)
    resolved = path.resolve()
    output = OUTPUT_ROOT.resolve()
    require(resolved.is_relative_to(output) and resolved != output,
            f"{label} must be a child of {output}: {resolved}")
    return resolved


def main(argv=None):
    global EVIDENCE_ROOT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-gpu", action="store_true", help="Explicitly run six private GPU processes after the snapshot builder succeeds")
    parser.add_argument("--expected-revision", help="Required for GPU replay: 4 to 40 hex characters of the verified builder commit")
    parser.add_argument("--review", type=Path, default=Path("output/owner-review-verified"), help="Existing six-package review directory inside this checkout/output")
    parser.add_argument("--output", type=Path, help="Fresh evidence directory inside this checkout/output; must not exist or overlap the review")
    options = parser.parse_args(argv)
    if options.run_gpu and not options.expected_revision:
        parser.error("--run-gpu requires --expected-revision")
    if options.expected_revision and not re.fullmatch(r"[0-9a-fA-F]{4,40}", options.expected_revision):
        parser.error("--expected-revision must contain 4 to 40 hexadecimal characters")
    review = scoped_output_path(options.review, "Review")
    require(review.is_dir(), f"Existing review directory is absent: {review}")
    target = options.output or Path("output/owner-review-validation") / (("replay-" if options.run_gpu else "prepare-") + str(time.time_ns()))
    folder = scoped_output_path(target, "Evidence")
    require(not folder.is_relative_to(review) and not review.is_relative_to(folder), "Evidence and review directories must be separate")
    require(not folder.exists(), f"Evidence directory must be fresh: {folder}")
    folder.mkdir(parents=True, exist_ok=False)
    EVIDENCE_ROOT = folder
    packages = prepare(folder, review)
    if options.run_gpu:
        run_gpu(folder, packages, options.expected_revision.lower(), review)
    else:
        write_json(folder / "preparation.json", {"format": "has_owner_review_replay_preparation_1", "packages": len(packages), "metadata_only": True, "gpu_run": False, "source_or_review_project_changes": False, "runtime_validation_pending": True})
        print(f"Prepared six metadata baselines only: {folder}")


if __name__ == "__main__":
    main()
