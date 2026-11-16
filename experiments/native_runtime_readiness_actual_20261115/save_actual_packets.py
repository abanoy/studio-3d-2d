"""Save closed actual metadata as two fresh packets; no runtime/Git actions."""
from pathlib import Path, PurePosixPath
import gzip
import hashlib
import io
import json
import math
import stat

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
FULL_DEST = ROOT / "experiments/windows_bone_binding_full_actual_20261115"
PUB = ROOT / "output/resume-full-publication-f0dd57a-20261115"
FULL = PUB / "review-ready"
FK = ROOT / "output/native-jiggle-headless-transport-prep-20261115/runtime-post-full-f0dd57a"
PREP = ROOT / "output/native-jiggle-headless-transport-prep-20261115/private-preparation-f0dd57a-post-full"
MATH = ROOT / "output/source-0x31-godot-math-20261115-attempt1"
REVISION = "f0dd57a2e568089d396fecba819ab987da658bf0"
MAXIMUM = 64 * 1024 * 1024


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    path = Path(path)
    for parent in [path, *path.parents]:
        info = parent.lstat()
        require(not stat.S_ISLNK(info.st_mode) and not getattr(info, "st_file_attributes", 0) & 0x400, "Reparse input refused")
    before = path.stat()
    require(path.is_file() and before.st_size <= MAXIMUM, "Bounded regular metadata/source required")
    raw = path.read_bytes()
    after = path.stat()
    require((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns), "Input changed while reading")
    return raw


def load(path):
    return json.loads(read(path))


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False) + "\n").encode("utf-8")


def safe(base, name):
    relative = PurePosixPath(name)
    require(not relative.is_absolute() and ".." not in relative.parts and "\\" not in name and ":" not in name, "Unsafe packet member")
    return base.joinpath(*relative.parts)


def unpack(raw):
    with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
        result = stream.read(MAXIMUM + 1)
        require(len(result) <= MAXIMUM and stream.read(1) == b"", "Over-budget gzip metadata")
        return result


def inspect_json(value):
    forbidden = {"Blender_matrix_local_row_major", "native_rest_words_uint32", "native_rest_matrices", "expected_world_bones", "expected_native_Z_tips", "rest_by_root_id", "vertex_positions", "vertex_buffer", "index_buffer", "image_data", "audio_data", "base64", "pcm"}
    if isinstance(value, dict):
        for key, child in value.items():
            require(not (key in forbidden and child), "Private raw payload refused: " + key)
            require(not (key in {"vertices", "indices", "triangles"} and isinstance(child, (list, dict))), "Geometry array refused")
            inspect_json(child)
    elif isinstance(value, list):
        for child in value:
            inspect_json(child)


def inspect(name, raw):
    suffix = Path(name).suffix.lower()
    require(suffix in {".json", ".gz", ".py", ".gd", ".ps1", ".md", ".txt", ".log"}, "Nonmetadata packet member")
    if suffix == ".json":
        inspect_json(json.loads(raw))
    elif suffix == ".gz":
        decoded = unpack(raw)
        if name.endswith(".json.gz"):
            inspect_json(json.loads(decoded))


def put(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)


def freeze_index(base, name):
    rows = []
    for path in sorted(base.rglob("*")):
        if path.is_file() and path != base / name:
            raw = read(path)
            rows.append({"path": path.relative_to(base).as_posix(), "bytes": len(raw), "sha256": sha(raw)})
    put(base / name, encode({"format": "has_actual_metadata_outer_index_1", "source_commit": REVISION, "files": rows, "file_count": len(rows), "bytes": sum(row["bytes"] for row in rows)}))


def main():
    require(not FULL_DEST.exists(), "Preserve existing full packet")
    require({p.name for p in HERE.iterdir()} == {Path(__file__).name}, "Preserve existing runtime packet or partial attempt")
    head_ref = read(ROOT / ".git/HEAD").decode("ascii").strip()
    require(head_ref.startswith("ref: ") and read(ROOT / ".git" / head_ref[5:]).decode("ascii").strip() == REVISION, "Current source revision changed")
    full_index_raw = read(FULL / "INDEX.json")
    require(sha(full_index_raw) == "113c39f6e93c684c62f70ca1d38a5f7243c4582f370cf60205d1131d74ecefb2", "Reviewed full INDEX changed")
    full_index = json.loads(full_index_raw)
    require(len(full_index["files"]) == 468, "Reviewed full payload membership changed")
    full_files = {}
    for row in full_index["files"]:
        raw = read(safe(FULL, row["path"]))
        require(len(raw) == row["bytes"] and sha(raw) == row["sha256"], "Full payload changed")
        inspect(row["path"], raw)
        full_files["full/" + row["path"]] = raw
    full_files["full/INDEX.json"] = full_index_raw
    for name in ["COPY-PROVENANCE.json", "SOURCE-RECIPE-INDEX.json"]:
        raw = read(PUB / name)
        inspect(name, raw)
        full_files["execution/" + name] = raw
    require(sha(full_files["execution/SOURCE-RECIPE-INDEX.json"]) == "f4965594eb313b0ac07ac9d49041cba8cc9f520c99b099115fd5666ae05da873", "Execution recipe source INDEX changed")
    publication = load(FULL / "PUBLICATION.json")
    require(publication["passed"] is True and publication["source_commit"] == REVISION and publication["private_jobs"] == 192, "Wrong actual full publication")
    full_files["BENCHMARK.json"] = encode({
        "format": "has_published_actual_bone_binding_full_20261115_1", "source_commit": REVISION, "passed": True,
        "elapsed_seconds": publication["elapsed_seconds"], "functional_source_files": 1008, "named_result_groups": 157, "core_process_groups": 36,
        "root_movie_metadata_groups": 21, "private_jobs": 192, "normal_exit0": 191, "registered_Krita_cancellation_exit2": 1,
        "original_payload_files": 468, "original_payload_bytes": sum(row["bytes"] for row in full_index["files"]),
        "original_INDEX_sha256": sha(full_index_raw), "exact_original_tree": "full", "original_INDEX_modified": False,
        "execution_source_INDEX_sha256": sha(full_files["execution/SOURCE-RECIPE-INDEX.json"]),
        "independent_audit": "experiments/resume_root_20261115/audit_full_independent.json",
        "prior_failures": "EE and c4d remain FAILED; owner-paused f380 remains USER_CANCELLED_INCOMPLETE.",
        "scope": "Fresh complete default on this Windows PC. Native Source dynamics, artist/novice/learner/device and clean-install observations remain separate.",
    })
    full_files["SOURCE_PROOF.json"] = encode({
        "format": "has_actual_full_copy_source_proof_1", "source_commit": REVISION, "original": FULL.relative_to(ROOT).as_posix(),
        "original_INDEX_sha256": sha(full_index_raw), "copy_mode": "Exact bytes, no metadata rewriting or filtering inside full/", "original_payloads": 468,
        "copied_execution_provenance_sha256": sha(full_files["execution/COPY-PROVENANCE.json"]),
        "copied_recipe_source_INDEX_sha256": sha(full_files["execution/SOURCE-RECIPE-INDEX.json"]),
        "all_original_alias_and_gzip_verification": "experiments/resume_root_20261115/audit_full_independent.json",
    })
    full_files["README.md"] = (
        "# Actual complete Windows bone-binding verification — November 15, 2026\n\n"
        "`full/` is a byte-exact copy of the independently reviewed 468-file consolidated packet plus its original INDEX. That INDEX is unchanged. `execution/` separately preserves the actual recipe-copy provenance and reviewed source index. OUTER_INDEX covers the complete new wrapper.\n\n"
        "Retrieve this directory from the saved Git checkpoint, verify every OUTER_INDEX length/hash, then verify full/INDEX.json. Use full/provenance/LOSSLESS_ALIAS_MAP.json and its retained original summary/audit indices to restore raw metadata: gzip_decode means lossless gzip decompression followed by the declared raw size/SHA check. Original absolute paths remain historical provenance; they are not instructions to execute old launchers. App source is recoverable at f0dd57a2e568089d396fecba819ab987da658bf0. Follow the current pickup for fresh tests.\n\n"
        "This is evidence and reproduction metadata, not an app, artwork or media bundle. Original models, projects, native coordinates, outputs and tools remain protected locally. Earlier failures and the interrupted run are not relabelled. Formal acceptance counts do not change from this packet alone.\n"
    ).encode("utf-8")

    common = [phase + suffix for phase in ["parse", "run"] for suffix in ["-command.json", "-engine.log", "-process.json", "-stderr.log", "-stdout.log"]]
    whitelists = {"FK": (FK, common + ["authoritative-closure.json", "locked-launch-context.json", "result.json", "verification.json"]),
                  "math": (MATH, common + ["authoritative-closure.json", "result.json", "verification.json"])}
    runtime_files = {}
    source_rows = []
    for scope, (folder, names) in whitelists.items():
        for name in names:
            require(name not in {"PRIVATE_ORACLE.json", "INPUT_LOCK.json", "ROOT-LEASE.json", "PUBLIC_SYNTHETIC_ORACLE.json"}, "Private/full case input refused")
            raw = read(folder / name)
            inspect(name, raw)
            runtime_files[scope + "/" + name] = raw
            source_rows.append({"source": (folder / name).relative_to(ROOT).as_posix(), "stored": scope + "/" + name, "bytes": len(raw), "sha256": sha(raw)})
    preparation_raw = read(PREP / "PUBLIC_PREPARATION.json")
    inspect("PUBLIC_PREPARATION.json", preparation_raw)
    runtime_files["FK/PUBLIC_PREPARATION.json"] = preparation_raw
    source_rows.append({"source": (PREP / "PUBLIC_PREPARATION.json").relative_to(ROOT).as_posix(), "stored": "FK/PUBLIC_PREPARATION.json", "bytes": len(preparation_raw), "sha256": sha(preparation_raw)})
    fk = json.loads(runtime_files["FK/verification.json"])
    fk_result = json.loads(runtime_files["FK/result.json"])
    require(fk["passed"] is True and fk["HEAD"] == fk["qualified_full_revision"] == REVISION and fk["source_runtime_inputs_preserved"] is True and fk["result"] == fk_result, "Actual FK verification failed")
    require(fk_result["checks"] == 41588 and fk_result["configurations"] == 220 and fk_result["failures"] == 0 and fk_result["authored_source_reset_preserved"] is True, "Wrong actual FK domain")
    require(len(fk_result["case_rows"]) == 220 and len(fk_result["numeric_native_runtime_joins"]) == 69, "Wrong actual FK aggregate rows")
    for row in fk_result["case_rows"]:
        require(set(row) == {"case", "root_uniform_scale", "bone_world_max_error", "skeleton_global_rest_max_error", "tip_world_max_distance", "tolerance"}, "Raw coordinate row refused")
        require(all(math.isfinite(row[key]) and 0 <= row[key] <= row["tolerance"] for key in ["bone_world_max_error", "skeleton_global_rest_max_error", "tip_world_max_distance"]), "Actual FK tolerance failure")
    for row in fk_result["numeric_native_runtime_joins"]:
        require(set(row) == {"native_index", "gltf_node_index", "skeleton_bone_index"} and all(type(value) is int for value in row.values()), "Only numeric ID joins admitted")
    math_verification = json.loads(runtime_files["math/verification.json"])
    math_result = json.loads(runtime_files["math/result.json"])
    require(math_verification["passed"] is True and math_verification["source_HEAD"] == REVISION and math_verification["result"] == math_result and math_verification["application_integration"] is False, "Actual standalone math verification failed")
    require(math_result["checks"] == 8994 and math_result["failures"] == 0 and math_result["integration_steps"] == 1440 and math_result["sample_output_sets"] == 48, "Wrong actual math domain")
    require(math_result["scope"]["native_geometry_loaded"] is False and math_result["scope"]["native_SDK_executed"] is False, "Math scope must stay synthetic")
    for label, verification in [("FK", fk), ("math", math_verification)]:
        require(len(verification["phases"]) == 2 and {row["phase"] for row in verification["phases"]} == {"parse", "run"}, "Separate parse/run required")
        require(all(row["passed"] is True and row["exit"] == 0 and row["retained_Popen_reaped"] is True and row["timed_out"] is False and not row["error_markers"] for row in verification["phases"]), "Actual phase closure/error gate failed")
        closure = json.loads(runtime_files[label + "/authoritative-closure.json"])
        require(closure["verification_sha256"] == sha(runtime_files[label + "/verification.json"]) and closure["runtime_lease_released"] is True and closure["owned_runtime_commands_absent"] is True and closure["no_process_killed"] is True and closure["source_commit"] == REVISION, "Actual authoritative closure differs")

    code_references = []
    for name in ["headless_transport.gd", "oracle_math.py", "prepare_private_oracle.py", "run_headless_transport.py"]:
        path = ROOT / "experiments/resume_transport_20261115" / name
        raw = read(path)
        code_references.append({"source": path.relative_to(ROOT).as_posix(), "bytes": len(raw), "sha256": sha(raw)})
    math_source = Path(math_verification["packet"])
    require(sha(read(math_source / "INDEX.json")) == math_verification["packet_index_sha256"], "Public math source packet INDEX changed")
    for name, expected in [("candidate.gd", math_result["candidate_sha256"]), ("harness.gd", math_result["harness_sha256"]), ("PUBLIC_SYNTHETIC_ORACLE.json", math_result["oracle_sha256"])]:
        source_raw = read(math_source / name)
        require(sha(source_raw) == expected and read(MATH / name) == source_raw, "Actual math source/case bytes differ")
        code_references.append({"source": (math_source / name).relative_to(ROOT).as_posix(), "bytes": len(source_raw), "sha256": expected, "copied_here": False})
    runtime_files["SOURCE_PROOF.json"] = encode({
        "format": "has_actual_native_readiness_source_proof_1", "source_commit": REVISION, "actual_metadata_sources": source_rows,
        "source_and_case_references_only": code_references, "math_source_packet_INDEX_sha256": math_verification["packet_index_sha256"],
        "private_input_lock_sha256": "47ed1b5a4772ca74040374180a22479b7892b351265a54bbee9ce7f1f1d4cfaa",
        "private_oracle_sha256": "4065a47ed7da9a53d18f42e326d668d82060028301cd691864b1e92ea9dcdfe4",
        "private_input_lock_or_oracle_contents_copied": False, "actual_root_lease_contents_copied": False,
        "independent_private_input_review": "experiments/resume_root_20261115/audit_transport_lock_independent.json",
    })
    runtime_files["BENCHMARK.json"] = encode({
        "format": "has_actual_native_runtime_readiness_20261115_1", "source_commit": REVISION,
        "FK": {"passed": True, "checks": 41588, "configurations": 220, "native_bones": 69, "native_Z_tips": 49,
               "source_conversion_scales": [0.01905], "model_root_uniform_scales": [1.0, 2.0], "bone_world_max_error": fk_result["maximum_bone_matrix_error"],
               "rest_world_max_error": fk_result["maximum_skeleton_global_rest_error"], "native_Z_tip_max_error": fk_result["maximum_native_Z_tip_distance"], "authored_rest_reset_preserved": True,
               "scope": "Actual SceneIO/Model FK, immutable rests, native-Z tips; posed skin, normals, rendered geometry, world parenting/save and dynamics remain outside this probe."},
        "standalone_math": {"passed": True, "checks": 8994, "failures": 0, "integration_steps": 1440, "sample_output_sets": 48,
                            "candidate_sha256": math_result["candidate_sha256"], "harness_sha256": math_result["harness_sha256"], "public_synthetic_oracle_sha256": math_result["oracle_sha256"],
                            "scalar64_max_vector_error": math_result["scalar64_max_vector_error"], "zero_cone_max_rest_displacement": math_result["zero_cone_max_rest_displacement"],
                            "scope": "Standalone synthetic Godot scalar64 math and Vector3/Basis boundary only. No native geometry/SDK execution or application integration."},
        "closures": "Both parse/run retained children reaped; exact authoritative metadata records released leases and no matching owned runtimes. No process was killed.",
        "private_data": "Original private oracle, INPUT_LOCK, actual ROOTLEASE and native/media assets remain LOCAL. This packet contains only selected actual metadata and source/case hash references.",
        "application_solver_integrated": False, "native_artist_fidelity_claim": False, "formal_acceptance_changed": False,
    })
    runtime_files["README.md"] = (
        "# Actual native runtime readiness — November 15, 2026\n\n"
        "This packet retains an explicit metadata whitelist: actual FK and standalone math parse/run commands, engine/stdout/stderr logs, retained-process proofs, aggregate results/verification and authoritative closure; FK also retains the original PUBLIC_PREPARATION.json. That preparation's UNRUN wording is historical and unchanged; subsequent actual PASS is recorded separately in results. No actual private oracle, INPUT_LOCK, ROOTLEASE, native geometry or media is copied. Numeric FK ID joins and aggregate error rows are admitted; they contain no native coordinate arrays.\n\n"
        "Verify OUTER_INDEX hashes after retrieving from Git. SOURCE_PROOF maps every copied file to its original byte identity and records source/case hashes without copying full inputs. App code is the f0dd57a source checkpoint. The accompanying public experiments/resume_transport_20261115 and experiments/source_0x31_godot_candidate_20261115 provide the exact source and synthetic case producer; verify their recorded hashes. Private source models remain necessary for the native probe and must be supplied through the protected local inputs. Regenerate a fresh private lock/oracle with the documented producer; never edit an archived lock or reuse an old lease.\n\n"
        "Do not execute historical command arrays as a new authorized run. Follow the current pickup, inspect source, obtain a fresh root-owned exclusive runtime lease and retain fresh identities/results. The scalar64 synthetic pass does not establish native solver equivalence, application integration, fan/Record/Off/portable rendering or artist/device acceptance. FK qualifies only one conversion scale .01905; root scales1/2 are separate. Prior normal-fidelity failures remain unqualified and preserved.\n"
    ).encode("utf-8")
    for name, raw in full_files.items():
        inspect(name, raw)
    for name, raw in runtime_files.items():
        inspect(name, raw)
    FULL_DEST.mkdir(exist_ok=False)
    for name, raw in full_files.items():
        put(safe(FULL_DEST, name), raw)
    for name, raw in runtime_files.items():
        put(safe(HERE, name), raw)
    for name, raw in full_files.items():
        require(read(safe(FULL_DEST, name)) == raw, "Full destination copy differs")
    for name, raw in runtime_files.items():
        require(read(safe(HERE, name)) == raw, "Runtime destination copy differs")
    require(read(FULL / "INDEX.json") == full_index_raw and read(FULL_DEST / "full/INDEX.json") == full_index_raw, "Original INDEX changed")
    freeze_index(FULL_DEST, "OUTER_INDEX.json")
    freeze_index(HERE, "OUTER_INDEX.json")
    print(json.dumps({"full_packet": str(FULL_DEST), "full_outer_INDEX_sha256": sha(read(FULL_DEST / "OUTER_INDEX.json")),
                      "runtime_packet": str(HERE), "runtime_outer_INDEX_sha256": sha(read(HERE / "OUTER_INDEX.json")),
                      "full_original_payload_count": 468, "runtime_metadata_whitelist_count": len(source_rows),
                      "runtime_launches": False, "private_oracle_or_lock_or_lease_copied": False, "originals_modified_or_deleted": False}, indent=2))


if __name__ == "__main__":
    main()
