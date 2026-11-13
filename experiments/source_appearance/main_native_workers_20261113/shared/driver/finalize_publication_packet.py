"""Finish the source/metadata-only25-case publication candidate without native art."""
from pathlib import Path
import gzip
import json

import package_core_proof as C

TASK, ROOT, PACKET = C.TASK, C.ROOT, C.PACKET
OLD = ROOT / "output/sfm-broader-native-cases-20261113"

def main():
    assert not (PACKET / "INDEX.json").exists()
    core = C.read(PACKET / "core14/ACTUAL_RESULTS.json")
    wider = C.read(PACKET / "wider11/ACTUAL_RESULTS.json")
    assert core["passed_cases"] == 14 and wider["passed_cases"] == 11
    assert core["root_revision"] == wider["root_revision"] == "cf7a805dd6ec76890da048ff28aa0080757e7c34"
    # Retain failures separately; neither partial conversion nor rejected
    # coordinator output name becomes one of the25accepted cases.
    failed = OLD / "conversion-run-20261113T232338350"
    failed_report = C.read(failed / "verification.json")
    assert not failed_report["passed"] and len(failed_report["results"]) == 1 and failed_report["failed_case"]["case"] == "keiki_tools_chisels"
    C.compressed(failed / "verification.json", PACKET / "historical-failures/win206/verification.json.gz")
    C.copy(failed / "graphics-lease-released.json", PACKET / "historical-failures/win206/graphics-lease-released.json")
    failed_case = failed / "02-keiki_tools_chisels-default-no-appearance"
    explicit_files = ("background-outer-launch.json", "background-request.json", "blender-background-completion.json", "blender-desktop-attestation.json",
        "blender-observer-request.json", "blender-spawn.json", "command.json", "exit.json", "private-receipt.json", "process.log",
        "python-background-completion.json", "python-desktop-attestation.json", "verification.json", "bundle/conversion.log", "bundle/worker.json", "bundle/conversion-request.json")
    for name in explicit_files:
        C.copy(failed_case / name, PACKET / "historical-failures/win206/failed-case" / name)
    for name in ("background_route.py", "background_conversion_driver.py", "background_python_bootstrap.py", "background_blender_observer.py", "stage_resources.py", "win_desktop_attestation.py"):
        C.copy(OLD / "source" / name, PACKET / "historical-failures/win206/driver" / name)
    invalid = TASK / "core2-launch-20261113T234201905"
    for name in ("launch.json", "stderr.log", "stdout.log", "closure.json"):
        C.copy(invalid / name, PACKET / "historical-failures/invalid-output-coordinator" / name)
    C.copy(TASK / "metadata-audit/WIDER_GO_AUDIT.json", PACKET / "shared/metadata/WIDER_GO_AUDIT.json")
    C.copy(TASK / "metadata-audit/audit_wider_ready.py", PACKET / "shared/driver/audit_wider_ready.py")
    C.copy(Path(__file__), PACKET / "shared/driver/finalize_publication_packet.py")
    for name in ("rebind-cpu-core-1794613242127697500", "rebind-cpu-wider-1794613242128972700"):
        C.copy(TASK / name / "verification.json", PACKET / "shared/cpu" / (name + ".json"))
    for name in ("conversion-run-1794613244382131500", "conversion-run-1794613244337061700"):
        C.copy(TASK / name / "verification.json", PACKET / "shared/preflight" / (name + ".json"))
    # Reference full original staging provenance losslessly, without its files.
    C.compressed(OLD / "runs/wider-execute-1794612147814048100/verification.json", PACKET / "shared/metadata/wider-staging.json.gz")
    C.copy(OLD / "stage_wider.py", PACKET / "shared/driver/stage_wider.py")
    C.copy(OLD / "prepare_wider_metadata.py", PACKET / "shared/driver/prepare_wider_metadata.py")
    C.copy(OLD / "source/archive_safety.py", PACKET / "shared/driver/archive_safety.py")
    C.copy(OLD / "source/vmt_reference.py", PACKET / "shared/driver/vmt_reference.py")
    longest = C.read(PACKET / "core14/LONG_PATH_WITNESS.json")["longest"]
    summary = {"format": "has_main_static_appearance_native25_summary_1", "root_revision": core["root_revision"],
        "actual_passed_cases": 25, "successful_glb_bundles": 22, "explicit_expected_allblank_refusals": 3,
        "core_cases": 14, "wider_cases": 11, "actual_converted_native_mdls": 6,
        "native_resource_files": 561, "native_resource_bytes": 469130387, "pinned_sourceio_files": 574, "frozen_main_python_files": 17,
        "private_conversion_desktops": 25, "independent_python_blender_selfattestation_cases": 25,
        "conversion_leases_authoritatively_closed": {"core": core["release"], "wider": wider["release"]},
        "whole_host_current_runtime_absence_claimed": False,
        "sum_case_worker_seconds": {"core": sum(row["seconds"] for row in core["results"]), "wider": sum(row["seconds"] for row in wider["results"])},
        "actual_longest_resolved_native_path": longest,
        "raw_native_model_texture_glb_media_payloads_in_packet": False,
        "claims": "Main static variant conversion, native index/catalogue provenance, decoded GLB structural consistency, owned resource closure and private job isolation",
        "unrun_or_separate": ["Native app adoption/Undo/pose/persistence and rendered pixels for these new runs", "Native shader/material parity and independent native flex/controller evaluation", "Native procedural jiggle, animation and compound rig assembly", "Mima head conversion in this wider batch"],
        "broader_inventory_reminder": {"archives": 22, "native_mdl_headers": 82, "distinct_native_mdl_hashes": 71,
            "source": "docs/benchmarks/sfm_native_feature_inventory_2026-11-12.json", "scope": "Metadata inventory, not a claim that all82models/features now work"},
        "retained_failures": ["Original76f89e Win206 run: one accepted native case then Keiki archival-copy failure; remains failed", "Root invalid explicit-output coordinator: name refused before private conversion; remains a failed coordinator attempt"],
        "context": "READY/preflight/goaudit are historical admission evidence. ACTUAL_RESULTS and aggregate gzips are terminal converter evidence. Root may run separate native app checks under a later lease."}
    C.save(PACKET / "SUMMARY.json", summary)
    readme = """# Actual main static appearance native conversions

At main commit `cf7a805dd6ec76890da048ff28aa0080757e7c34`, Core14 and Wider11 both passed:25cases,22successful GLB bundles and3explicit expected allblank refusals. The batches converted6native MDLs across Nitori, Keiki, Junko main/hair, Mima body and Kanako props. Core covers3Nitori skins and all7nonempty Keiki tools/box/flame combinations; wider covers Junko skin15/Belt/Hat choices, Mima skin3/Socks choices and Kanako BatL/allblank choices. Default no-appearance requests remain distinct from explicit defaults.

Each accepted case has a closed private desktop/job receipt and independent Python plus Blender desktop, PID/creation, nonce, request, source and native-import provenance checks. The driver also checked exact native selected indices/catalogues, bone names/parents, decoded GLB structure, retained geometry/skin/morph fingerprints against its batch default and owned active material providers. The original native resources, archives, runtimes,17scoped main Python files and locks remained exact. The574-file SourceIO runtime is pinned. These are converter checks; native app adoption, Undo/persistence, pose and rendered pixels are separate.

The longest actual successful archival copy is261UTF16codeunits, at Keiki `materials/models/touhou/tamo/Keiki Haniyashin/excl mark.vmt`. Its513bytes and SHA match the declared owned provider. The core witness covers120actual resolved-native files, the wider witness198. This exercises the Windows long-path fix with real native input. No native texture/model/GLB/media payload is copied into this packet.

`core14` and `wider11` each contain a compact actual-results file, per-case raw protocol receipts/logs, a long-path witness and a lossless deterministic gzip of the exact terminal aggregate verification. Gzip uses an empty stored filename, timestamp0 and compression level9. The aggregate metadata contains skeletal transforms, provenance, counts and fingerprints; it has no vertex/image buffers or embedded media. The gzip raw hashes are recorded in each actual-results file. The detailed raw aggregate files remain on the owner PC.

`shared` contains the exact main Python/driver source snapshots, hashed locks/plans, focused CPU and no-conversion preflight proof, provenance and the bounded resource-staging recipe. Paths inside raw receipts, locks and commands are historical local evidence, not relocatable download locations. No installed Blender/SourceIO binary or private resource is bundled. The preflight READY/goaudit status preceded the terminal runs; `SUMMARY.json`, terminal ACTUAL_RESULTS and aggregate gzips state the final converter outcome.

`historical-failures` preserves the76f89e Win206 archival-copy failure and the rejected explicit output-name coordinator attempt. Neither is counted as a success or relabeled by the later passing runs. The fix keeps logical resource paths/provenance and returns the original MemoryBuffer bytes while using extended-length Windows IO for archival copying.

Limits remain: Nitori's native hairbump is absent and the additive glow material is approximated; static PBR conversion does not establish native shader pixels. Native jiggle declarations are metadata, not simulated behavior. Native flex/controller semantics, animated sequences, compound rig assembly and Mima head conversion are not accepted by these25checks. The broader supplied corpus remains82headers/71distinctMDLhashes across22archives; six converted MDLs do not cover every model or extra feature.

`INDEX.json` binds every actual file below this packet, excluding itself. Child indices bind their child packet files; the outer index also binds those indices. No source, lock, original, native resource or existing receipt was edited to produce this candidate.
"""
    with (PACKET / "README.md").open("x", encoding="utf-8") as stream: stream.write(readme)
    files = {path.relative_to(PACKET).as_posix(): C.identity(path) for path in sorted(PACKET.rglob("*")) if path.is_file()}
    assert not any(Path(name).suffix.casefold() in {".mdl", ".vtf", ".vmt", ".vvd", ".vtx", ".glb", ".blend", ".png", ".mp4", ".wav"} for name in files)
    # Validate every compressed metadata representation and both child indices.
    for name in files:
        if name.endswith(".json.gz"): json.loads(gzip.decompress((PACKET / name).read_bytes()))
    for child, name in (("core14", "CORE_INDEX.json"), ("wider11", "WIDER_INDEX.json")):
        index = C.read(PACKET / child / name)
        assert all(C.identity(PACKET / child / path) == row for path, row in index["files"].items())
    C.save(PACKET / "INDEX.json", {"format": "has_main_static_appearance_native25_packet_index_1", "files": files,
        "count": len(files), "bytes": sum(row["bytes"] for row in files.values()), "native_art_payloads": False})
    print(json.dumps({"index": C.identity(PACKET / "INDEX.json"), "count": len(files), "bytes": sum(row["bytes"] for row in files.values()), "longest_utf16": longest["utf16_code_units"]}))

if __name__ == "__main__": main()
