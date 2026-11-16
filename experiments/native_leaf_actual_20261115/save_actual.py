"""Archive a metadata whitelist for three closed leaf attempts; no runtime/Git."""
from pathlib import Path
import hashlib
import json
import math
import stat

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
HEAD = "f0dd57a2e568089d396fecba819ab987da658bf0"
MAXIMUM = 16 * 1024 * 1024


def need(value, detail):
    if not value:
        raise ValueError(detail)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    path = Path(path)
    for ancestor in [path, *path.parents]:
        info = ancestor.lstat()
        need(not stat.S_ISLNK(info.st_mode) and not getattr(info, "st_file_attributes", 0) & 0x400, "Reparse metadata refused")
    before = path.stat()
    need(path.is_file() and before.st_size <= MAXIMUM, "Bounded regular metadata required")
    raw = path.read_bytes()
    after = path.stat()
    need((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns), "Input changed during read")
    return raw


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False) + "\n").encode("utf-8")


def no_private(value):
    forbidden = {"points", "unaffected", "mask", "pcm", "image_data", "audio_data", "base64", "private_capture", "private_tip", "private_axis", "expected_world_bones", "expected_native_Z_tips", "rest_by_root_id", "native_rest_matrices", "native_rest_words_uint32", "vertex_positions", "vertex_buffer", "index_buffer", "Blender_matrix_local_row_major"}
    if isinstance(value, dict):
        for key, child in value.items():
            need(not (key in forbidden and child), "Private coordinate/media payload refused: " + key)
            need(not (key in {"vertices", "indices", "triangles"} and isinstance(child, (list, dict))), "Geometry arrays refused")
            no_private(child)
    elif isinstance(value, list):
        for child in value:
            no_private(child)


def put(name, raw):
    path = HERE / name
    need(path.resolve().is_relative_to(HERE.resolve()), "Packet path escaped")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)


def main():
    need({p.name for p in HERE.iterdir()} == {Path(__file__).name}, "Preserve an existing packet/partial attempt")
    full_map_path = ROOT / "output/windows-canonical-bone-binding-20261115T225514304/source-before.json"
    full_map = json.loads(read(full_map_path))
    need(full_map["commit"] == HEAD and len(full_map["source_sha256"]) == 1008, "Wrong source catalogue")
    common = [phase + suffix for phase in ["parse", "run"] for suffix in ["-command.json", "-engine.log", "-owned-start.json", "-process.json", "-stderr.log", "-stdout.log"]]
    whitelist = common + ["result.json", "verification.json", "authoritative-closure.json", "COPY-PROVENANCE.json"]
    files = {}
    copies = []
    observations = []
    sources = []
    for number in [1, 2, 3]:
        folder = ROOT / ("output/source-0x31-native-leaf-20261115-attempt" + str(number))
        for name in whitelist:
            raw = read(folder / name)
            if name.endswith(".json"):
                no_private(json.loads(raw))
            files["attempt" + str(number) + "/" + name] = raw
            copies.append({"source": (folder / name).relative_to(ROOT).as_posix(), "stored": "attempt" + str(number) + "/" + name, "bytes": len(raw), "sha256": sha(raw)})
        result = json.loads(files[f"attempt{number}/result.json"])
        verification = json.loads(files[f"attempt{number}/verification.json"])
        closure = json.loads(files[f"attempt{number}/authoritative-closure.json"])
        need(verification["source_HEAD"] == HEAD and verification["result"] == result and verification["inputs_preserved"] is True, "Actual source/result preservation differs")
        need(closure["source_commit"] == HEAD and closure["attempt"] == number and closure["inputs_preserved"] is True and closure["verification_sha256"] == sha(files[f"attempt{number}/verification.json"]), "Closure binding differs")
        need(all(closure[key] is True for key in ["runtime_lease_released", "owned_headless_children_reaped", "no_process_killed", "owned_runtime_commands_absent"]), "Authoritative closure incomplete")
        need(len(verification["phases"]) == 2 and all(row["retained_Popen_reaped"] is True and row["timed_out"] is False for row in verification["phases"]), "Actual parse/run retained process proof differs")
        need(verification["phases"][0]["exit"] == 0 and verification["phases"][0]["passed"] is True, "Parse did not pass")
        if number < 3:
            need(verification["passed"] is False and closure["validation_passed"] is False and result["checks"] == 2 and result["failures"] == 1 and result["dynamics_steps"] == 0 and not result["cases"], "Preserve original pre-dynamics failure")
        else:
            need(verification["passed"] is True and closure["validation_passed"] is True and result["status"] == "PASSED_NATIVE8_LEAF_READINESS_ONLY", "Actual compatibility successor did not pass")
            need(result["checks"] == 7289 and result["failures"] == 0 and result["dynamics_steps"] == 1440 and len(result["cases"]) == 12, "Preregistered result domain differs")
            need(all(row["passed"] is True and row["exit"] == 0 and not row["error_markers"] for row in verification["phases"]), "Successful phases have errors")
            need(sha(files[f"attempt{number}/verification.json"]) == "dcda15bbd1938b60cc7ce3bd8f8745a75bbedef2a28d90533bc5478f259e2261", "Reviewed actual successor changed")
        packet = Path(verification["packet"])
        index_raw = read(packet / "INDEX.json")
        need(sha(index_raw) == verification["packet_index_sha256"], "Source packet identity differs")
        code_rows = []
        for alias, origin in [("leaf_candidate.gd", ROOT / "experiments/source_0x31_godot_candidate_20261115/candidate.gd"), ("leaf_adapter.gd", packet / "leaf_adapter.gd"), ("weighted_capture.gd", packet / "weighted_capture.gd"), ("leaf_harness.gd", packet / "leaf_harness.gd")]:
            raw = read(folder / "Studio" / alias)
            need(raw == read(origin), "Staged source differs from referenced packet")
            code_rows.append({"staged_alias": alias, "source": origin.relative_to(ROOT).as_posix(), "bytes": len(raw), "sha256": sha(raw)})
        source_lock = json.loads(read(packet / "SOURCE_LOCK.json"))
        need(len(source_lock["files"]) == 200, "Actual application source lock differs")
        for row in source_lock["files"]:
            need(row["sha256"] == full_map["source_sha256"][row["path"]] and sha(read(folder / "Studio" / row["path"])) == row["sha256"], "Staged application source/full join differs")
        provenance = json.loads(files[f"attempt{number}/COPY-PROVENANCE.json"])
        need(provenance["application_files"] == 200 and len(provenance["support"]) == 3, "Actual source/support provenance differs")
        sources.append({"attempt": number, "packet": packet.relative_to(ROOT).as_posix(), "INDEX_sha256": sha(index_raw), "source_lock_sha256": sha(read(packet / "SOURCE_LOCK.json")), "app_full_joins": 200, "staged_code_references_only": code_rows})
        observations.append({"attempt": number, "status": result["status"], "passed": verification["passed"], "checks": result["checks"], "failures": result["failures"], "dynamics_steps": result["dynamics_steps"], "cases": len(result["cases"]), "reason": result["reason"], "verification_sha256": sha(files[f"attempt{number}/verification.json"]), "closure_sha256": sha(files[f"attempt{number}/authoritative-closure.json"]), "closure_utc": closure["checked_utc"]})
    result = json.loads(files["attempt3/result.json"])
    rows = result["cases"]
    for row in rows:
        need(row["vertices"] == 9661 and row["weighted_to_leaf"] == 152 and row["shared_influence_vertices"] == 144 and row["unaffected_vertices"] == 9509, "Actual weighted domains differ")
        need(row["unaffected_exact"] is True and row["Off_all_weighted_points_exact"] is True and row["ticks"] == 120, "Exact unaffected/reset/tick proof failed")
        need(math.isfinite(row["basis_error_max"]) and row["basis_error_max"] <= 2e-5 and row["tip_error_max"] <= 2e-5 * row["world_scale"], "Preregistered transport bound failed")
        need(row["import_context"]["private_compatibility_flag"] == "UNMEASURED" and row["import_context"]["matches_engine_default_structure"] is True and row["import_context"]["is_simulating_physics"] is False and row["import_context"]["actor_PhysicalBone3D_count"] == 0, "Compatibility scope changed")
    groups = [rows[:6], rows[6:]]
    for group in groups:
        by_name = {row["profile"]: row for row in group}
        need(set(by_name) == {"control", "positive3", "negative3", "positive12", "positive50", "repeat12"}, "Exact temporary-input profiles differ")
        need(by_name["positive12"]["final_weighted_sha256"] == by_name["repeat12"]["final_weighted_sha256"], "Repeated cleared-state result differs")
        need(len({row["restored_weighted_sha256"] for row in group}) == 1, "Exact restored weighted baseline differs")
        need(all(by_name[name]["weighted_vertices_moved"] > 0 for name in ["positive3", "negative3", "positive12", "positive50"]), "External-input weighted effect absent")
    benchmark = {
        "format": "has_actual_native8_leaf_readiness_benchmark_20261115_1", "source_HEAD": HEAD, "attempts": observations,
        "actual_success": {"attempt": 3, "checks": 7289, "failures": 0, "dynamics_steps": 1440, "cases": 12,
                           "native_index": 8, "native_parent_index": 7, "native_name": "FrontHair1", "native_yaw_pitch_stiffness": 100,
                           "source_conversion_scale": 0.01905, "nominal_root_scales": [1.0, 2.0], "actual_bone_basis_norms": sorted({row["world_scale"] for row in rows}),
                           "vertices": 9661, "weighted_to_leaf": 152, "shared_with_other_bones": 144, "zero_leaf_weight_region": 9509,
                           "all_unaffected_regions_exact": True, "all_Off_weighted_points_exact": True, "Off_style_frames": [12, 24],
                           "repeat12_final_weighted_hashes_exact_per_root": True, "weighted_vertices_moved_range": [min(row["weighted_vertices_moved"] for row in rows), max(row["weighted_vertices_moved"] for row in rows)],
                           "weighted_displacement_range": [min(row["weighted_displacement_max"] for row in rows), max(row["weighted_displacement_max"] for row in rows)],
                           "maximum_basis_error": max(row["basis_error_max"] for row in rows), "maximum_tip_error": max(row["tip_error_max"] for row in rows),
                           "maximum_boundary_adapter_error": max(row["boundary_adapter_error_max"] for row in rows), "maximum_parent_local_closure_error": max(row["parent_local_closure_error_max"] for row in rows),
                           "angle_projection_steps_by_root": [{row["profile"]: row["angle_projection_steps"] for row in group} for group in groups],
                           "opposite_input_signal": "The preregistered harness opposite-tip projection check passed in both root contexts; raw private tips/axes are not published.",
                           "compatible_internal_simulator": "Measured direct/internal native node, no script or physical bodies, simulation false. Active may be true; private compatibility flag remains unmeasured."},
        "limits": ["Actual external native8 leaf readiness only, using original retained rule100 and actual CPU weighted geometry.", "Synthetic temporary world accelerations3/12/50 are not HAS fan-speed or Source wind units.", "Direct live_pose clear/apply restoration is not the product Hair & clothes GUI toggle.", "No GPU/render/native-SDK/artist parity, multiple procedural chains, body/fan coexistence, Record/Undo/HAS/movie integration is certified.", "Original attempts1/2 remain pre-dynamics failures. Source flags/native metadata and original assets stay unchanged.", "Nominal root1/2 is not two conversion scales or the new six-foot-at-scale1 standard."],
    }
    files["BENCHMARK.json"] = encode(benchmark)
    files["SOURCE_PROOF.json"] = encode({"format": "has_actual_native_leaf_copy_and_source_proof_1", "source_HEAD": HEAD, "actual_metadata_copies": copies,
                                        "source_packets_and_alias_references_only": sources, "full_source_catalogue_sha256": sha(read(full_map_path)),
                                        "actual_ROOTLEASE_or_original_geometry_copied": False,
                                        "independent_source_driver_and_API_review": "experiments/resume_root_20261115/audit_native_leaf_source_independent.json"})
    files["README.md"] = (
        "# Actual native8 leaf readiness — November 15, 2026\n\n"
        "This metadata-only archive preserves attempts1/2 as failures and attempt3 as a separately pinned success: 7,289 checks, 1,440 dynamics steps, 12 cases. Every copied JSON was inspected before inclusion. Only explicit command/process/owned-start/log/result/verification/closure/COPY-PROVENANCE files are admitted. Actual ROOT-LEASE, private points/rests/geometry, GLB/HAS/media and copied application sources are excluded. Absolute private input paths in historical commands are provenance, not their contents.\n\n"
        "Verify INDEX.json after retrieving the repository. SOURCE_PROOF maps every raw copied byte identity and points to each separately preserved original/diagnostic/compatibility source packet. The base application source is f0dd57a2e568089d396fecba819ab987da658bf0; source200 and the three support files are joined to that full catalogue. No source/controller was patched in place. BENCHMARK records aggregate errors, actual measured basis norms, shared influences, repeated/reset hashes and explicit limits; full point arrays remain private in memory/local assets.\n\n"
        "Restore source from the accompanying Git packets; retain the original native model family locally and verify the recorded hashes. Do not run archived command arrays or reuse actual leases. A fresh experiment requires current source review, exact staged hashes, root-owned exclusive authority and fresh identity/closure evidence. The initial broad guard refused an engine-created internal simulator; the diagnostic established its structure. The compatibility successor accepts only the measured empty, nonsimulating native profile and retains the other safeguards. Neither prior failure is relabelled.\n\n"
        "This external harness proves actual leaf live-pose transport and CPU weighted deformation/restoration, not a completed Studio native solver, full Source fidelity, GPU appearance or GUI fan/Record/HAS/export behavior. Formal artist/device/novice/clean-install acceptance is separate. Original outputs and private inputs were neither changed nor deleted.\n"
    ).encode("utf-8")
    for name, raw in files.items():
        if name.endswith(".json"):
            no_private(json.loads(raw))
        put(name, raw)
    for name, raw in files.items():
        need(read(HERE / name) == raw, "Published copy differs")
    index_rows = []
    for path in sorted(HERE.rglob("*")):
        if path.is_file() and path != HERE / "INDEX.json":
            raw = read(path)
            index_rows.append({"path": path.relative_to(HERE).as_posix(), "bytes": len(raw), "sha256": sha(raw)})
    put("INDEX.json", encode({"format": "has_actual_native_leaf_metadata_index_1", "source_HEAD": HEAD, "files": index_rows, "file_count": len(index_rows), "bytes": sum(row["bytes"] for row in index_rows)}))
    print(json.dumps({"packet": str(HERE), "INDEX_sha256": sha(read(HERE / "INDEX.json")), "payloads": len(index_rows), "bytes": sum(row["bytes"] for row in index_rows), "raw_actual_metadata_files": len(copies), "preserved_failed_attempts": 2, "actual_success_checks": 7289, "actual_success_cases": 12, "actual_runtime_or_Git_action": False}, indent=2))


if __name__ == "__main__":
    main()
