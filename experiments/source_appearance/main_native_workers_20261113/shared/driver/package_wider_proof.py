"""Freeze wider11 actual source/log metadata, preserving the frozen core14 packet."""
from collections import Counter
from pathlib import Path
import json

import package_core_proof as C

TASK, ROOT, PACKET = C.TASK, C.ROOT, C.PACKET
RUN = TASK / "conversion-run-1794613615624323200"
DEST = PACKET / "wider11"
RAW_SHA = "4cea157b747ebf9876efa1dc210c9da2e5ba594227927258ae48b38410cd7c5f"

def main():
    assert not DEST.exists()
    core_index = C.identity(PACKET / "core14/CORE_INDEX.json")
    DEST.mkdir(exist_ok=False)
    report_path = RUN / "verification.json"; report = C.read(report_path)
    assert C.identity(report_path)["sha256"] == RAW_SHA
    assert report["passed"] and report["all_eleven_passed"] and len(report["results"]) == 11
    assert report["protected_main_python_runtime_original_stage_request_inputs_unchanged"] and report["lock_file_unchanged"]
    release = C.read(RUN / "graphics-lease-released.json")
    assert release["lease_released"] and release["all_11_case_isolation_verified"] and release["coordinator_and_owned_graphics_absent"] and release["no_process_killed"]
    lock = C.read(TASK / "conversion-inputs-wide2.json")
    assert report["root_revision"] == lock["root_revision"] == "cf7a805dd6ec76890da048ff28aa0080757e7c34"
    compressed = C.compressed(report_path, DEST / "verification.json.gz")
    C.copy(RUN / "graphics-lease-released.json", DEST / "graphics-lease-released.json")
    C.copy(Path(__file__), PACKET / "shared/driver/package_wider_proof.py")
    rows = []; witnessed = []; preserved = {}
    scope_files = ("private-receipt.json", "background-isolation-verification.json", "background-outer-launch.json", "python-desktop-attestation.json",
        "blender-desktop-attestation.json", "blender-spawn.json", "python-background-completion.json", "blender-background-completion.json",
        "background-request.json", "blender-observer-request.json", "command.json", "exit.json", "process.log", "bundle/conversion.log", "bundle/worker.json", "bundle/conversion-request.json")
    for i, result in enumerate(report["results"]):
        folder = Path(result["folder"])
        assert folder.parent == RUN and result["passed"]
        isolation = C.read(folder / "background-isolation-verification.json")
        private = C.read(folder / "private-receipt.json")
        python = C.read(folder / "python-desktop-attestation.json")
        blender = C.read(folder / "blender-desktop-attestation.json")
        assert C.identity(folder / "background-isolation-verification.json") == result["background_isolation_receipt"]
        assert isolation["passed"] and isolation["independent_python_and_blender_self_attestation"] and not isolation["original_private_receipt_edited"]
        assert private["job_closed"] and private["desktop_closed"] and not private["foreground_child_observed"] and not private["desktop_switch_requested"]
        assert private["exit"] == result["exit"] == (0 if result["expected_success"] else 1)
        assert private["desktop"] == isolation["desktop"] == python["self"]["desktop"] == blender["self"]["desktop"]
        for name, expected in isolation["evidence_hashes"].items(): assert C.identity(folder / name) == expected
        assert C.identity(folder / "bundle/worker.json") == isolation["native_worker_pid_file"]
        native = lock["native"][result["case"]]
        row = {"index": i + 1, "case": result["case"], "variant": result["variant"], "expected_success": result["expected_success"],
            "exit": result["exit"], "seconds": result["seconds"], "passed": True,
            "native_inventory_only": {"bones": len(native["bones"]), "flex_descriptors": len(native["flex_names"]), "controllers": len(native["controllers"]),
                "flex_rule_ops": native["rule_op_counts"], "procedural_bones": len(native["procedural_bones"])},
            "isolation": {key: isolation[key] for key in ("desktop", "window_station", "python_pid", "blender_pid", "private_monitor_child_desktop_confirmed", "independent_python_and_blender_self_attestation", "original_private_receipt_edited")}}
        if result["expected_success"]:
            parameters = C.read(folder / "bundle/parameters.json"); saved = parameters["native_parameters"]
            assert C.identity(folder / "bundle/parameters.json") == result["parameters"]
            assert C.identity(folder / "bundle/dependencies.json") == result["dependencies"]
            assert C.identity(folder / "bundle/scene.glb")["sha256"] == result["glb_structure"]["sha256"]
            row.update(selected_skin=saved["selected_skin"], selected_named_bodygroups=saved["selected_bodygroup_indices"],
                selected_native_bodygroups=saved.get("selected_native_bodygroup_indices"), explicit_catalogue="native_appearance_choices" in saved,
                skin_families=len(saved["skin_groups"]), native_bones=len(saved["bones"]), glb={key: result["glb_structure"][key] for key in ("sha256", "bytes")},
                meshes=[{"name": mesh["node"], "primitives": mesh["primitives"]} for mesh in result["glb_structure"]["meshes"]],
                active_materials=result["glb_structure"]["active_materials"], dependency_classification=result["dependency_classification"])
            resolved = C.read(folder / "bundle/dependencies.json")["resolved"]
            for path in (folder / "bundle/resolved-native").rglob("*"):
                if not path.is_file(): continue
                absolute = str(path.absolute()); relative = path.relative_to(folder / "bundle/resolved-native").as_posix()
                matching = [item for item in resolved if item["path"].replace("\\", "/").casefold() == relative.casefold()]
                assert len(matching) == 1
                observed = C.identity(path)
                assert observed["sha256"] == matching[0]["sha256"] and observed["bytes"] == matching[0]["bytes"]
                witnessed.append({"case": result["case"], "variant": result["variant"], "absolute_path": absolute,
                    "characters": len(absolute), "utf16_code_units": len(absolute.encode("utf-16-le")) // 2,
                    "logical_dependency_path": matching[0]["path"], "provider": matching[0]["provider"], **observed})
        else:
            assert result["explicit_all_blank_refusal"]
            row["explicit_all_blank_refusal"] = True
        for name in scope_files:
            source = folder / name
            preserved[str(source)] = C.copy(source, DEST / "cases" / folder.name / name)
        rows.append(row)
    longest = max(witnessed, key=lambda item: (item["utf16_code_units"], item["absolute_path"]))
    C.save(DEST / "LONG_PATH_WITNESS.json", {"format": "has_actual_native_archival_long_path_witness_1", "longest": longest,
        "resolved_native_files_checked": len(witnessed), "files_over_259_utf16_units": sum(row["utf16_code_units"] > 259 for row in witnessed),
        "scope": "Actual successful archival copy/provider SHA correspondence; shader/render fidelity separate"})
    C.save(DEST / "ACTUAL_RESULTS.json", {"format": "has_main_source_static_appearance_wider11_actual_1", "root_revision": report["root_revision"],
        "raw_aggregate": {"local_path": str(report_path), **C.identity(report_path)}, "aggregate_gzip": compressed, "results": rows, "passed_cases": 11,
        "successful_bundles": sum(row["expected_success"] for row in rows), "expected_allblank_refusals": sum(not row["expected_success"] for row in rows),
        "independent_dual_attestation_cases": 11, "all_private_jobs_desktops_closed": True, "release": release, "protected_inputs_preserved": True,
        "artifact_payloads_copied": False, "mima_head_conversion": "UNRUN: retained metadata only",
        "limits": ["Static main worker metadata/structure/dependency checks only; no app/GPU or independent native geometry/flex/material fidelity.", "Native procedural/jiggle and controller/rule inventory does not establish simulated/evaluated native behavior.", "Junko components and Mima body/head/dress remain distinct rigs; no assembly acceptance."]})
    assert all(C.identity(Path(path)) == value for path, value in preserved.items())
    assert C.identity(PACKET / "core14/CORE_INDEX.json") == core_index
    C.save(DEST / "WIDER_INDEX.json", {"format": "has_wider11_metadata_packet_index_1", "files": {p.relative_to(DEST).as_posix(): C.identity(p) for p in sorted(DEST.rglob("*")) if p.is_file()},
        "raw_native_models_textures_glb_media_copied": False})
    print(json.dumps({"wider_index": C.identity(DEST / "WIDER_INDEX.json"), "path_witness": C.identity(DEST / "LONG_PATH_WITNESS.json"), "longest_utf16": longest["utf16_code_units"], "files_checked": len(witnessed), "gzip": compressed["deterministic_gzip"]}))

if __name__ == "__main__": main()
