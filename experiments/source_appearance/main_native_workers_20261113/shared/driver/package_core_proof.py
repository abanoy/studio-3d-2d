"""Freeze successful core14 metadata/source/log proof; never copy native art."""
import gzip
import hashlib
import io
import json
from pathlib import Path
import shutil
import stat

TASK = Path(__file__).absolute().parent
ROOT = TASK.parents[1]
RUN = TASK / "conversion-run-1794613497806249400"
PACKET = TASK / "publication-candidate"
CORE = PACKET / "core14"
RAW_SHA = "fd0ba6b83b8bb68a277bb41d31c56687af9009702da3c75d46ef30b9167687f7"

def identity(path):
    path = Path(path)
    for parent in (path, *path.parents):
        info = parent.lstat()
        assert not stat.S_ISLNK(info.st_mode) and not (getattr(info, "st_file_attributes", 0) & 0x400)
    before = path.stat()
    with path.open("rb") as stream: sha = hashlib.file_digest(stream, "sha256").hexdigest()
    assert (before.st_size, before.st_mtime_ns) == (path.stat().st_size, path.stat().st_mtime_ns)
    return {"sha256": sha, "bytes": before.st_size, "mtime_ns": before.st_mtime_ns}

def read(path): return json.loads(path.read_bytes())

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream: json.dump(value, stream, indent=2, allow_nan=False)

def copy(source, destination):
    assert not destination.exists()
    observed = identity(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    assert identity(destination) == observed and identity(source) == observed
    return observed

def compressed(source, destination):
    raw = source.read_bytes(); observed = identity(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as stream:
        with gzip.GzipFile(filename="", mode="wb", fileobj=stream, compresslevel=9, mtime=0) as output: output.write(raw)
    assert gzip.decompress(destination.read_bytes()) == raw and identity(source) == observed
    return {"raw": observed, "deterministic_gzip": identity(destination)}

def main():
    assert not PACKET.exists()
    CORE.mkdir(parents=True, exist_ok=False)
    report_path = RUN / "verification.json"; report = read(report_path)
    assert identity(report_path)["sha256"] == RAW_SHA
    assert report["passed"] and report["all_fourteen_passed"] and len(report["results"]) == 14
    assert report["protected_main_python_runtime_original_stage_request_inputs_unchanged"] and report["lock_file_unchanged"]
    release = read(RUN / "graphics-lease-released.json")
    assert release["lease_released"] and release["all_14_case_isolation_verified"] and release["coordinator_and_owned_graphics_absent"] and release["no_process_killed"]
    lock = read(TASK / "conversion-inputs-core2.json")
    assert report["root_revision"] == lock["root_revision"] == "cf7a805dd6ec76890da048ff28aa0080757e7c34"
    compressed(report_path, CORE / "verification.json.gz")
    copy(RUN / "graphics-lease-released.json", CORE / "graphics-lease-released.json")
    for name in ("READY.json", "SOURCE_INDEX.json", "MATERIALIZED.json", "REBIND_PLAN.json", "REBIND_NORMALIZED_DIFF.patch", "RUN_COMMANDS.json"):
        copy(TASK / name, PACKET / "shared/metadata" / name)
    for name in ("RESOURCE_PLAN.json", "conversion-inputs-core2.json", "conversion-inputs-wide2.json"):
        compressed(TASK / name, PACKET / "shared/metadata" / (name + ".gz"))
    for name in ("native-core-cases.json", "native-wider-cases.json"):
        copy(TASK / name, PACKET / "shared/metadata" / name)
    for name in ("core-source", "wider-source"):
        for source in sorted((TASK / name).iterdir()):
            if source.is_file(): copy(source, PACKET / "shared/driver" / name / source.name)
    for name in ("prepare_rebind.py", "test_rebind.py", "freeze_ready.py", "package_core_proof.py"):
        copy(TASK / name, PACKET / "shared/driver" / name)
    for name, expected in lock["main_python_sources"].items():
        assert identity(ROOT / name) == expected
        copy(ROOT / name, PACKET / "shared/main-source" / name)
    cases = []; path_witnesses = []; preserved = {}
    scope_files = ("private-receipt.json", "background-isolation-verification.json", "background-outer-launch.json", "python-desktop-attestation.json",
        "blender-desktop-attestation.json", "blender-spawn.json", "python-background-completion.json", "blender-background-completion.json",
        "background-request.json", "blender-observer-request.json", "command.json", "exit.json", "process.log", "bundle/conversion.log", "bundle/worker.json", "bundle/conversion-request.json")
    for i, result in enumerate(report["results"]):
        folder = Path(result["folder"])
        assert folder.parent == RUN and result["passed"]
        isolation = read(folder / "background-isolation-verification.json")
        private = read(folder / "private-receipt.json")
        python = read(folder / "python-desktop-attestation.json")
        blender = read(folder / "blender-desktop-attestation.json")
        assert identity(folder / "background-isolation-verification.json") == result["background_isolation_receipt"]
        assert isolation["passed"] and isolation["independent_python_and_blender_self_attestation"] and not isolation["original_private_receipt_edited"]
        assert private["job_closed"] and private["desktop_closed"] and not private["foreground_child_observed"] and not private["desktop_switch_requested"]
        assert private["exit"] == result["exit"] == (0 if result["expected_success"] else 1)
        assert private["desktop"] == isolation["desktop"] == python["self"]["desktop"] == blender["self"]["desktop"]
        for name, expected in isolation["evidence_hashes"].items(): assert identity(folder / name) == expected
        assert identity(folder / "bundle/worker.json") == isolation["native_worker_pid_file"]
        entry = {"index": i + 1, "case": result["case"], "variant": result["variant"], "expected_success": result["expected_success"],
            "exit": result["exit"], "seconds": result["seconds"], "passed": True,
            "isolation": {key: isolation[key] for key in ("desktop", "window_station", "python_pid", "blender_pid", "private_monitor_child_desktop_confirmed", "independent_python_and_blender_self_attestation", "original_private_receipt_edited")}}
        if result["expected_success"]:
            parameters = read(folder / "bundle/parameters.json"); native = parameters["native_parameters"]
            assert identity(folder / "bundle/parameters.json") == result["parameters"]
            assert identity(folder / "bundle/dependencies.json") == result["dependencies"]
            assert identity(folder / "bundle/scene.glb")["sha256"] == result["glb_structure"]["sha256"]
            entry.update(selected_skin=native["selected_skin"], selected_named_bodygroups=native["selected_bodygroup_indices"],
                selected_native_bodygroups=native.get("selected_native_bodygroup_indices"), explicit_catalogue="native_appearance_choices" in native,
                skin_families=len(native["skin_groups"]), native_bones=len(native["bones"]), glb={key: result["glb_structure"][key] for key in ("sha256", "bytes")},
                meshes=[{"name": m["node"], "primitives": m["primitives"]} for m in result["glb_structure"]["meshes"]],
                active_materials=result["glb_structure"]["active_materials"], dependency_classification=result["dependency_classification"])
            resolved = read(folder / "bundle/dependencies.json")["resolved"]
            for path in (folder / "bundle/resolved-native").rglob("*"):
                if not path.is_file(): continue
                absolute = str(path.absolute()); rel = path.relative_to(folder / "bundle/resolved-native").as_posix()
                matching = [row for row in resolved if row["path"].replace("\\", "/").casefold() == rel.casefold()]
                assert len(matching) == 1
                observed = identity(path)
                assert observed["sha256"] == matching[0]["sha256"] and observed["bytes"] == matching[0]["bytes"]
                path_witnesses.append({"case": result["case"], "variant": result["variant"], "absolute_path": absolute,
                    "characters": len(absolute), "utf16_code_units": len(absolute.encode("utf-16-le")) // 2,
                    "logical_dependency_path": matching[0]["path"], "provider": matching[0]["provider"], **observed})
        else:
            assert result["explicit_all_blank_refusal"]
            entry["explicit_all_blank_refusal"] = True
        for name in scope_files:
            source = folder / name
            preserved[str(source)] = copy(source, CORE / "cases" / folder.name / name)
        cases.append(entry)
    longest = max(path_witnesses, key=lambda row: (row["utf16_code_units"], row["absolute_path"]))
    save(CORE / "LONG_PATH_WITNESS.json", {"format": "has_actual_native_archival_long_path_witness_1", "longest": longest,
        "resolved_native_files_checked": len(path_witnesses), "files_over_259_utf16_units": sum(row["utf16_code_units"] > 259 for row in path_witnesses),
        "scope": "Actual successful archival filesystem copy+provider SHA correspondence; not shader/render fidelity"})
    save(CORE / "ACTUAL_RESULTS.json", {"format": "has_main_source_static_appearance_core14_actual_1", "root_revision": report["root_revision"],
        "raw_aggregate": {"local_path": str(report_path), **identity(report_path)}, "results": cases, "passed_cases": 14,
        "successful_bundles": sum(r["expected_success"] for r in cases), "expected_allblank_refusals": sum(not r["expected_success"] for r in cases),
        "independent_dual_attestation_cases": 14, "all_private_jobs_desktops_closed": True, "release": release,
        "protected_inputs_preserved": True, "artifact_payloads_copied": False,
        "limits": ["Actual main worker metadata/structure/dependency acceptance only; no app/GPU or independent native fidelity claim.", "Nitori native missinghairbump and additiveglow approximation retained.", "Original Win206 failure and invalid explicit-output coordinator attempt remain preserved failures."]})
    assert all(identity(Path(path)) == row for path, row in preserved.items())
    save(CORE / "CORE_INDEX.json", {"format": "has_core14_metadata_packet_index_1", "files": {p.relative_to(CORE).as_posix(): identity(p) for p in sorted(CORE.rglob("*")) if p.is_file()},
        "raw_native_models_textures_glb_media_copied": False})
    print(json.dumps({"core_index": identity(CORE / "CORE_INDEX.json"), "path_witness": identity(CORE / "LONG_PATH_WITNESS.json"), "longest_utf16": longest["utf16_code_units"], "files_checked": len(path_witnesses)}))

if __name__ == "__main__": main()
