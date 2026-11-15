"""Freeze the reviewed output-only minimal source/metadata adapter proposal."""
import hashlib
import json
from pathlib import Path
import shutil

TASK = Path(__file__).absolute().parent
DEST = TASK / "publication-candidate"

def identity(path):
    raw = path.read_bytes(); st = path.stat()
    return {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "mtime_ns": st.st_mtime_ns}

def read(path): return json.loads(path.read_bytes())

def copy(source, destination):
    observed = identity(source); assert not destination.exists()
    destination.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(source, destination)
    assert identity(source) == observed and identity(destination) == observed

def save(path, value):
    with path.open("x", encoding="utf-8") as stream: json.dump(value, stream, indent=2, allow_nan=False)

def main():
    assert not DEST.exists()
    tests = read(TASK / "minimal-cpu-1794615484594165400/verification.json")
    assert tests["passed"] and tests["checks"] == 22 and tests["failures"] == tests["errors"] == 0
    module_path = TASK / "minimal-source/source_jiggle_metadata.py"
    assert identity(module_path)["sha256"] == "f49d4ab9051e69d16a5ce0adb699b5698d6bfbb9147a69050014a11295e33ffe"
    DEST.mkdir(exist_ok=False)
    for source in sorted((TASK / "minimal-source").iterdir()):
        assert source.is_file() and source.suffix == ".py"
        copy(source, DEST / "minimal-source" / source.name)
    for name in ("PLAN.md", "PLAN_SOURCE_CONTEXT.json", "HISTORICAL_SIDECAR_DRAFT.md", "MINIMAL_REBASE.json", "build_minimal.py", "minimal_report_functions.txt", "package_minimal.py"):
        copy(TASK / name, DEST / name)
    copy(TASK / "minimal-cpu-1794615484594165400/verification.json", DEST / "cpu/verification.json")
    for source in sorted((TASK / "review").iterdir()):
        assert source.is_file() and source.suffix in {".json", ".md", ".txt"}
        copy(source, DEST / "review" / source.name)
    # Historical source/CPU snapshots retain rejected design and known defects.
    for source in sorted((TASK / "source").iterdir()):
        if source.is_file(): copy(source, DEST / "historical-sidecar/source" / source.name)
    for name in ("cpu-1794615138714466800", "cpu-1794615267063983400"):
        copy(TASK / name / "verification.json", DEST / "historical-sidecar/cpu" / (name + ".json"))
    for source in sorted((TASK / "before-publication-confirm-guard").iterdir()):
        copy(source, DEST / "historical-sidecar/before-confirm-guard" / source.name)
    summary = {"format": "has_minimal_inert_source_jiggle_main_candidate_1", "status": "OUTPUT_ONLY_UNSHIPPED_DRAFT",
        "candidate": "minimal-source", "metadata_adapter_sha256": identity(DEST / "minimal-source/source_jiggle_metadata.py")["sha256"],
        "raw_reader_sha256": identity(DEST / "minimal-source/source_jiggle_values.py")["sha256"], "authored_cpu_checks": 22, "authored_cpu_failures": 0,
        "independent_authored_checks": 22, "independent_additional_checks": 16, "independent_review_issues": [],
        "metadata_cap_bytes": 131072, "final_report_cap_bytes": 262144, "bounded_log_status_cap_bytes": 4096,
        "policy": "Exact full inline metadata or explicit whole-branch omission; no sidecar files, no partial arrays, no clamping",
        "identity_priority": "Original/native/catalogue/scale validation before optional serialization or budget fallback",
        "known_static_baseline": "NoJIGGLE/BSP preserve old report and writer; valid original report is not enlarged beyond256KiB by optional metadata",
        "runtime_support": "not_implemented", "binding_status": "unattempted", "applied": False,
        "source_original_models_SourceIO_import_converters_graphics_newtools_Git_or_production_changes": False,
        "actual_Junko_full_report_fit_bridge_emission_Godot_adoption_saved_roundtrip": "UNRUN_requires_separate_fresh_source_conversion_app_lease",
        "project_json_cap": {"bytes": 1048576, "changed": False, "multi_model_save_admission": "UNTESTED_separate_from256KiBreport"},
        "historical_alternative": "Retained separately with review-found identity-order and malformed-receipt defects; not a port candidate",
        "broader_limits": ["No native140byte/BOING layout acceptance", "No native index-to-runtime binding or simulation", "No native flex/shader/assembly fidelity"]}
    save(DEST / "SUMMARY.json", summary)
    text = """# Minimal inert jiggle metadata adapter — unshipped draft

Only `minimal-source` is the current candidate. It adds no production/runtime/Git change and has no sidecar or confirmation API. Two prospective tools provide inert exact native-prefix metadata and pure report admission; the other two files are authored fixture/tests. The verified raw reader is byte-identical to the49-rule numeric proof. No SourceIO class, original model, converter, Godot/Blender/native viewer or graphics process is imported/launched by these tests.

The candidate passed22authored CPU tests; independent review repeated22and16additional checks with no actionable finding. Original/native hashes, bone catalogue and conversion scale are checked before all optional budget fallback. Both namespace hashes remain distinct for archive imports. All metadata stays unapplied, unbound and runtime_support=not_implemented. Unknown flags and the120-byte-prefix/full-layout boundary remain explicit.

Full metadata must fit128KiB in its canonical compact encoding, and the **final nested parameter report** must fit256KiB in its actual ASCII-escaped, indented UTF8 LF/CRLF byte encoding. Otherwise the entire numeric branch is omitted with a bounded reason, candidate digest/bytes/counts and original/native hashes. No rules are truncated or clamped. If status itself cannot fit, the original report/writer remains exact and the reason is emitted to the existing conversion log. The retained MDL/preparation bundle remains the source of truth; no new external metadata asset or portable-HAS sidecar is promised. Existing invalid/oversized original reports are not silently repaired.

`PLAN.md` locates the import-after-sys.path, selected-MDL inspection and final report publication seams, including binary publication of measured bytes and no post-measurement report mutation. The actor adopter stores the whole report under its native_parameters metadata. Whole-project JSON still has a separate1MiB cap; report admission does not establish multi-model save admission. Source snapshots in PLAN_SOURCE_CONTEXT are read-only observations, not a whole-source freeze claim.

Actual Junko full-report fit, real bridge emission/bootstrap, app adoption and packed/linked saved metadata are UNRUN. Its earlier67,525byte inert proposal and this authored suite do not prove them. A future port needs a fresh exact source checkpoint, ordinary bootstrap and no-jiggle/BSP baselines, converter ownership/source pins, and separate real import/reopen checks. No solver or automatic Hair&clothes activation is proposed.

`historical-sidecar` and historical review files retain the rejected larger design and its25/26case results. They have known edge defects and are not approved port source. No failure or earlier source was erased. `review/MINIMAL_FINAL_REVIEW.md` is the current read-only review; old sidecar findings remain historical.

For CPU reproduction, copy the four minimal-source files into a fresh disposable output directory, then run the test file there with approvedPython -B. Do not run tests inside this frozen packet: their fresh evidence directory is relative to the source copy. Tests construct their native byte fixtures in memory and need no private model or experiment cache. Native integration remains separate.

The outerINDEX binds every actual file below this candidate, excluding itself. Context/review indices retain their original bytes; the outer index is the complete publication inventory. The raw49-rule packet is already separately archived under experiments/native_jiggle_values_20261113 and is not duplicated here.
"""
    with (DEST / "README.md").open("x", encoding="utf-8") as stream: stream.write(text)
    files = {path.relative_to(DEST).as_posix(): identity(path) for path in sorted(DEST.rglob("*")) if path.is_file()}
    assert not any(Path(name).suffix.casefold() in {".mdl", ".vvd", ".vtx", ".vtf", ".vmt", ".glb", ".blend", ".exe", ".png", ".mp4"} for name in files)
    save(DEST / "INDEX.json", {"format": "has_minimal_inert_jiggle_candidate_index_1", "files": files, "count": len(files), "bytes": sum(value["bytes"] for value in files.values()), "native_asset_payloads": False})
    print(json.dumps({"index": identity(DEST / "INDEX.json"), "files": len(files), "bytes": sum(value["bytes"] for value in files.values()), "candidate": "minimal-source", "actual_native_fit": "UNRUN"}))

if __name__ == "__main__": main()
