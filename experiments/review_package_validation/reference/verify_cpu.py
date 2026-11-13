"""Reproduce this proposed port's metadata/guard checks without graphics."""
from pathlib import Path
import ast
import contextlib
import hashlib
import importlib.util
import io
import json
import sys
import time

sys.dont_write_bytecode = True
PROTOTYPE = Path(__file__).resolve().parent
ROOT = PROTOTYPE.parents[1]


def main():
    script = PROTOTYPE / "tools/verify_owner_review.py"
    ast.parse(script.read_text(encoding="utf-8"))
    spec = importlib.util.spec_from_file_location("owner_review_port_probe", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Only this CPU import points at the existing checkout before the proposed
    # ports are installed. Production derives these paths from its own location.
    module.ROOT = ROOT
    module.OUTPUT_ROOT = ROOT / "output"
    module.REPLAY_SCRIPT = PROTOTYPE / "tests/owner_review_replay.gd"
    module.GUIDE = PROTOTYPE / "docs/owner_review_validation.md"
    checks = {}

    def check(name, result):
        checks[name] = bool(result)
        if not result:
            raise AssertionError(name)

    def refused(name, call):
        try:
            call()
        except (RuntimeError, SystemExit):
            checks[name] = True
        else:
            raise AssertionError(name + " accepted")

    check("integer_float_json_equivalence", not module.compare({"frame": 24}, {"frame": 24.0}))
    check("absolute_tolerance_accepted", not module.compare(1., 1. + 5e-13))
    check("absolute_tolerance_not_relative", bool(module.compare(1e8, 1e8 + .1)))
    check("boolean_is_not_number", bool(module.compare(True, 1)))
    check("identity_string_exact", bool(module.compare({"id": "001"}, {"id": "1"})))
    check("array_order_preserved", bool(module.compare([1, 2], [2, 1])))
    check("dictionary_fields_preserved", bool(module.compare({"a": 1}, {"a": 1, "b": 2})))
    check("large_integer_difference_not_lost", bool(module.compare(2**60, 2**60 + 1)))
    check("nan_does_not_compare_equal", bool(module.compare(float("nan"), float("nan"))))
    check("default_review_is_inside_output", module.scoped_output_path(Path("output/owner-review-verified"), "review") == ROOT / "output/owner-review-verified")
    refused("outside_output_refused", lambda: module.scoped_output_path(Path("src"), "review"))
    refused("output_root_itself_refused", lambda: module.scoped_output_path(Path("output"), "review"))
    refused("parent_traversal_refused", lambda: module.scoped_output_path(Path("output/../src"), "review"))
    with contextlib.redirect_stderr(io.StringIO()):
        refused("gpu_requires_explicit_revision", lambda: module.main(["--run-gpu"]))
        refused("invalid_revision_refused", lambda: module.main(["--expected-revision", "HEAD"]))
    for output in ["output/owner-review-verified/nested", "output/owner-review-verified", "output"]:
        refused("separate_evidence_boundary_" + output.replace("/", "_"), lambda output=output: module.main(["--output", output]))
    refused("existing_evidence_refused", lambda: module.main(["--output", "output/review-validation-port-prototype"]))
    baseline = json.loads((PROTOTYPE / "original-harness-baseline.json").read_text())
    source = ROOT / "output/owner-review-validation"

    def old_stamp(path):
        return {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size, "mtime_ns": path.stat().st_mtime_ns}

    check("old_harness_preserved_before", all(old_stamp(source / name) == value for name, value in baseline.items()))
    folder = PROTOTYPE / "metadata-preparation" / str(time.time_ns())
    module.main(["--output", str(folder)])
    preparation = json.loads((folder / "preparation.json").read_text())
    check("all_six_metadata_prepared", preparation["packages"] == 6 and preparation["metadata_only"] and not preparation["gpu_run"])
    packages = json.loads((folder / "package-baseline.json").read_text())
    check("all_six_input_hash_size_mtime_unchanged", all(module.stamp(Path(p["path"])) == p["before"] for p in packages))
    check("evidence_write_stays_in_run", module.EVIDENCE_ROOT == folder)
    refused("sibling_evidence_write_refused", lambda: module.write_json(PROTOTYPE / "outside-run.json", {}))
    check("old_harness_preserved_after", all(old_stamp(source / name) == value for name, value in baseline.items()))
    files = {p.relative_to(PROTOTYPE).as_posix(): {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "bytes": p.stat().st_size} for part in ["tools", "tests", "docs"] for p in (PROTOTYPE / part).rglob("*") if p.is_file()}
    report = {"format": "has_owner_review_port_cpu_1", "checks": checks, "checks_count": len(checks), "all_passed": all(checks.values()), "python_ast_parse": True, "source_paths_overridden_only_for_this_cpu_import": {"ROOT": str(ROOT), "REPLAY_SCRIPT": str(module.REPLAY_SCRIPT), "GUIDE": str(module.GUIDE)}, "proposed_files": files, "preparation": str(folder), "gpu_run": False, "studio_created": False, "reproduction": str(Path(__file__).resolve()), "limits": "Metadata/guard/comparator checks only. Runtime replay and private receipts are pending root port/build/GPU lease."}
    (PROTOTYPE / "cpu-verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"checks": len(checks), "all_passed": report["all_passed"], "preparation": str(folder), "files": files}, indent=2))


if __name__ == "__main__":
    main()
