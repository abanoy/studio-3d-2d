"""Freeze one metadata publication packet from root-supplied final evidence."""
from pathlib import Path
import gzip
import json

from stage_publication import ROOT, TASK, RUN, COMMIT, read, digest

AUDIT = ROOT / "output/canonical-post-save-audit-20261113"
AUDIT_INDEX_SHA = "9d030cb221ab6d1363435e9bf4a1953905841b2a7bac947c2fd56f9e418c50a0"
DUPLICATES = {
    "full-verification.json": ("verification.json.gz", "gzip"),
    "source-before.json": ("canonical/source-before.json", "identity"),
    "source-after.json": ("canonical/source-after.json", "identity"),
    "state.json": ("canonical/state.json", "identity"),
    "authoritative-host-termination.json": ("canonical/authoritative-host-termination.json", "identity"),
    "desktop-enumeration.json": ("canonical/desktop-enumeration.json", "identity"),
}

def main():
    destination = TASK / "publication-candidate"
    if (destination / "INDEX.json").exists(): raise RuntimeError("Final packet already frozen")
    source_inputs = {}
    def acquire(path):
        raw, identity = read(path); source_inputs[str(path)] = identity; return raw
    initial_raw = acquire(TASK / "STAGING_RECEIPT.json"); initial = json.loads(initial_raw)
    before_names = {p.relative_to(destination).as_posix() for p in destination.rglob("*") if p.is_file()}
    if before_names != set(initial["files"]): raise RuntimeError("Initial stage membership changed")
    for name, expected in initial["files"].items():
        if digest((destination / name).read_bytes()) != expected: raise RuntimeError("Initial staged bytes changed")
    # Every earlier source input remains immutable; no dependence on a live
    # process scan or on current owner-review activity is introduced.
    for name, expected in initial["input_identities_preserved"].items():
        if read(Path(name))[1] != expected: raise RuntimeError("An initial source identity changed")
    index_raw = acquire(AUDIT / "INDEX.json")
    if digest(index_raw)["sha256"] != AUDIT_INDEX_SHA: raise RuntimeError("Frozen audit index differs")
    context_index = json.loads(index_raw)
    if context_index["file_count"] != 16 or context_index["total_bytes"] != 2616819:
        raise RuntimeError("Unexpected audit context index counts")
    audit_rows = context_index["files"]
    if {p.relative_to(AUDIT).as_posix() for p in AUDIT.rglob("*") if p.is_file()} != {r["path"] for r in audit_rows} | {"INDEX.json"}:
        raise RuntimeError("Frozen audit membership differs")
    additions = {}; mappings = []
    for row in audit_rows:
        name = row["path"]
        if name != Path(name).name or Path(name).suffix not in {".py", ".md", ".json"}:
            raise RuntimeError("Unexpected audit source/metadata path")
        raw = acquire(AUDIT / name)
        original = {"sha256": row["sha256"], "bytes": row["bytes"]}
        if digest(raw) != original: raise RuntimeError("Audit file identity differs")
        if name in DUPLICATES:
            outer_name, representation = DUPLICATES[name]
            outer_raw = (destination / outer_name).read_bytes()
            decoded = gzip.decompress(outer_raw) if representation == "gzip" else outer_raw
            if decoded != raw: raise RuntimeError("Duplicate-byte mapping differs")
            reason = "Already preserved losslessly by outer gzip" if representation == "gzip" else "Already preserved as exact outer raw bytes"
        else:
            outer_name = "receipt-audit/" + ("ORIGINAL_CONTEXT_README.md" if name == "README.md" else name)
            additions[outer_name] = raw; outer_raw = raw; decoded = raw; representation = "identity"
            reason = "Distinct audit source/metadata file retained"
        mappings.append({"original_context_path": name, "original_identity": original,
            "outer_path": outer_name, "outer_identity": digest(outer_raw), "representation": representation,
            "decoded_identity": digest(decoded), "reason": reason})
    additions["receipt-audit/ORIGINAL_CONTEXT_INDEX.json"] = index_raw
    final_audit = json.loads(additions["receipt-audit/receipt-ready-final.json"])
    release_raw = acquire(RUN / "graphics-lease-released.json"); release = json.loads(release_raw)
    host_raw = acquire(RUN / "authoritative-host-before-review.json"); host = json.loads(host_raw)
    if release.get("released") is not True or release.get("source_commit") != COMMIT or release.get("canonical_run") != RUN.name:
        raise RuntimeError("Root release does not bind this canonical")
    expected_links = {
        "receipt_audit_sha256": digest(additions["receipt-audit/receipt-ready-final.json"])["sha256"],
        "receipt_inventory_sha256": digest(additions["receipt-audit/receipt-inventory.json"])["sha256"],
        "host_proof_sha256": digest(host_raw)["sha256"],
        "canonical_state_sha256": digest((destination / "canonical/state.json").read_bytes())["sha256"],
    }
    if any(release.get(key) != expected for key, expected in expected_links.items()): raise RuntimeError("Release hash link differs")
    state = json.loads((destination / "canonical/state.json").read_bytes())
    if release.get("coordinator_pid") != state["pid"] or host.get("coordinator_pid") != state["pid"] or host.get("expected_creation_utc") != state["process_started"]:
        raise RuntimeError("Release/host process identity differs")
    if not host.get("coordinator_absent") or not host.get("owned_runtime_command_matches_absent") or not host.get("no_process_killed"):
        raise RuntimeError("Root host proof is not the expected absent/no-kill observation")
    if final_audit.get("passed") is not True or final_audit.get("source_commit") != COMMIT or final_audit.get("unexpected_failures") != []:
        raise RuntimeError("Final receipt audit does not pass")
    counts = {"fresh_root_receipt_files": 176, "unique_receipt_files": 190, "success_exit_0_files": 189, "expected_krita_cancel_exit_2_files": 1}
    if any(final_audit.get(key) != expected for key, expected in counts.items()) or not final_audit.get("all_receipts_private_closed"):
        raise RuntimeError("Final expected-outcome/closure classification differs")
    additions["canonical/graphics-lease-released.json"] = release_raw
    additions["canonical/authoritative-host-before-review.json"] = host_raw
    mapping = {"format": "studio_canonical_audit_context_mapping_1", "original_context_index_sha256": AUDIT_INDEX_SHA,
        "original_context_index_outer_path": "receipt-audit/ORIGINAL_CONTEXT_INDEX.json",
        "not_a_local_directory_index": True, "original_entries": len(audit_rows),
        "distinct_files_copied": len(audit_rows) - len(DUPLICATES), "duplicate_entries_represented": len(DUPLICATES),
        "mappings": mappings, "reconstruction": "For each original_context_path, write exact outer bytes or gzip-decompressed bytes to a fresh owned context folder, verify original_identity, then copy ORIGINAL_CONTEXT_INDEX.json as INDEX.json"}
    additions["receipt-audit/CONTEXT_MAPPING.json"] = json.dumps(mapping, indent=2).encode("utf-8")
    additions["provenance/INITIAL_STAGING_RECEIPT.json"] = initial_raw
    additions["recipe/finalize_publication.py"] = acquire(Path(__file__))
    additions["README.md"] = acquire(TASK / "README_CANDIDATE.md")
    if any(read(Path(path))[1] != expected for path, expected in source_inputs.items()): raise RuntimeError("Final source inputs changed")
    additions["provenance/FINAL_INPUTS.json"] = json.dumps({"format": "studio_canonical_final_input_receipt_1",
        "source_commit": COMMIT, "source_inputs_preserved": source_inputs,
        "initial_stage_file_count": len(initial["files"]), "release_hash_links_verified": expected_links,
        "audit_context_entries_all_mapped": True, "expected_krita_cancel_exit_2_retained": True,
        "no_live_process_graphics_test_or_release_action": True}, indent=2).encode("utf-8")
    if set(additions) & before_names: raise RuntimeError("Finalization would overwrite initial stage")
    for name, raw in additions.items():
        if b"\0" in raw or raw.startswith((b"glTF", b"IDST", b"\x89PNG", b"PK\x03\x04", b"MZ")):
            raise RuntimeError("Unexpected binary asset in source/metadata addition")
        raw.decode("utf-8-sig")
        target = destination / name
        if not target.resolve().is_relative_to(destination.resolve()): raise RuntimeError("Escaped final destination")
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream: stream.write(raw)
    expected_names = before_names | set(additions)
    payloads = {p.relative_to(destination).as_posix(): digest(p.read_bytes()) for p in sorted(destination.rglob("*")) if p.is_file()}
    if set(payloads) != expected_names: raise RuntimeError("Final packet has unlisted payloads")
    for name, expected in initial["files"].items():
        if payloads[name] != expected: raise RuntimeError("Initial stage changed during finalization")
    for name, raw in additions.items():
        if payloads[name] != digest(raw): raise RuntimeError("Final addition copy differs")
    for name, original in initial["gzip_originals"].items():
        if digest(gzip.decompress((destination / name).read_bytes())) != original: raise RuntimeError("Gzip original differs")
        payloads[name]["raw_original"] = original
    if any(read(Path(path))[1] != expected for path, expected in source_inputs.items()): raise RuntimeError("Final metadata sources changed")
    index = {"format": "studio_full_canonical_post_save_publication_1", "source_commit": COMMIT,
        "canonical_run": RUN.name, "status": "passed", "suite_exit": 0, "files": payloads,
        "file_count": len(payloads), "total_bytes": sum(row["bytes"] for row in payloads.values()),
        "index_self_not_included": True, "audit_context_index_is_provenance_only": True,
        "all_original_audit_entries_reconstructible": True, "expected_cancellation_count": 1,
        "unexpected_failures": 0, "root_supplied_release_preserved": True,
        "metadata_only_no_art_native_assets_or_media": True, "packager_graphics_test_or_release_action": False}
    index_path = destination / "INDEX.json"
    with index_path.open("x", encoding="utf-8") as stream: json.dump(index, stream, indent=2)
    receipt = {"format": "studio_canonical_publication_frozen_1", "path": str(destination),
        "index": digest(index_path.read_bytes()), "file_count": index["file_count"], "total_bytes": index["total_bytes"],
        "physical_files_including_index": len(payloads) + 1, "audit_mapping": {"distinct": 10, "duplicate": 6},
        "all_source_inputs_preserved": True, "no_tests_graphics_source_git_or_release_action": True}
    with (TASK / "FINALIZATION_RECEIPT.json").open("x", encoding="utf-8") as stream: json.dump(receipt, stream, indent=2)
    print(json.dumps(receipt))

if __name__ == "__main__": main()
