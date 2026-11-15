"""Freeze reviewed numeric/source metadata only; no native payload or runtime copy."""
import gzip
import hashlib
import json
from pathlib import Path
import shutil

TASK = Path(__file__).absolute().parent
ROOT = TASK.parents[1]
RUN = TASK / "runs/1794614279712394400"
DEST = TASK / "publication-candidate"
SCHEMA = ROOT / "output/source-jiggle-schema-prep-20261113"

def identity(path):
    raw = path.read_bytes(); st = path.stat()
    return {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "mtime_ns": st.st_mtime_ns}

def read(path): return json.loads(path.read_bytes())

def copy(source, destination):
    assert not destination.exists()
    before = identity(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    assert identity(source) == before and identity(destination) == before

def save(path, value):
    with path.open("x", encoding="utf-8") as stream: json.dump(value, stream, indent=2, allow_nan=False)

def main():
    assert not DEST.exists()
    receipt = read(RUN / "verification.json")
    review = read(TASK / "review/actual-extraction-review.json")
    tests = read(TASK / "cpu-1794614175646897300/verification.json")
    assert receipt["passed"] and review["passed"] and tests["passed"] and tests["checks"] == 26
    assert not review["issues"] and all(review["checks"].values())
    DEST.mkdir(exist_ok=False)
    for source in sorted(RUN.iterdir()):
        assert source.suffix in {".json", ".gz"} and source.is_file()
        copy(source, DEST / "actual" / source.name)
    for source in sorted((TASK / "source").iterdir()):
        assert source.suffix == ".py" and source.is_file()
        copy(source, DEST / "source" / source.name)
    copy(Path(__file__), DEST / "source/package_jiggle.py")
    for source in sorted((TASK / "review").iterdir()):
        assert source.suffix in {".json", ".md", ".txt"} and source.is_file()
        copy(source, DEST / "review" / source.name)
    copy(TASK / "cpu-1794614175646897300/verification.json", DEST / "cpu/verification.json")
    for source in sorted(SCHEMA.iterdir()):
        assert source.is_file() and source.suffix in {".json", ".md"}
        name = "SCHEMA_CONTEXT_INDEX.json" if source.name == "INDEX.json" else source.name
        copy(source, DEST / "schema-reference" / name)
    raw = read(RUN / "RAW_VALUES.json")
    summary = {"format": "has_junko_raw_jiggle_numeric_packet_summary_1", "native_mdl_sha256": raw["native_mdl_sha256"], "native_mdl_bytes": raw["native_mdl_bytes"],
        "native_version": 49, "bones": 69, "rules": 49, "finite_float32_values": 1421,
        "bone_table": {"offset": 664, "stride": 216, "end": 15568}, "observed120byte_prefix_span": [15568, 21448],
        "pointers_monotonic_in_bone_order": False, "rule_flags_all": {"uint32": 49, "hex": "0x00000031", "known_mask": 127, "unknown_bits": 0,
            "pinned_reader_names": ["IS_FLEXIBLE", "HAS_ANGLE_CONSTRAINT", "HAS_LENGTH_CONSTRAINT"]},
        "float32_groups": [{"rules": 17, "yaw_stiffness": 100, "pitch_stiffness": 100}, {"rules": 32, "yaw_stiffness": 50, "pitch_stiffness": 50}],
        "other27fields_same_across_all_rules": True, "raw_values_file": identity(DEST / "actual/RAW_VALUES.json"),
        "inert_proposal_file": identity(DEST / "actual/INERT_METADATA_PROPOSAL.json"),
        "cpu_authored": {"checks": 26, "failures": 0}, "independent_review": {"checks_actual": 24, "row_discrepancies": 0, "independent_authored_checks": 26, "additional_refusals": 2},
        "native_resource_files_preserved": 561, "original_archives_preserved": 5, "sourceio_source_files_preserved": 574,
        "all_protected_files_preserved": 1153, "independent_protected_bytes_rehashed": review["protected_bytes_read"],
        "runtime_support": "not_implemented", "applied": False, "binding_status": "unattempted", "full_native_rule_layout_verified": False,
        "proposed_metadata128KiB_budget_met": True, "proposed_metadata_bytes": 67525, "adjacent_full256KiBreport_admission": "UNTESTED",
        "SourceIO_import_runtime_mutation_converters_GPU_original_writes": False,
        "limits": receipt["limits"], "schema_reference": "Historical read-only design packet, copied exact with its originalINDEX renamedSCHEMA_CONTEXT_INDEX; outerINDEX binds all copied files"}
    save(DEST / "SUMMARY.json", summary)
    readme = """# Junko hair native jiggle values: inert extraction proof

The exact supplied Junko v25 hair MDL (`8da09c905227ddc8eef73a3f83594a4eb1c3a6d5304ee41ba5471bef834bc716`,37,644bytes) contains69bones and49type5JIGGLE declarations. A new output-only stdlib reader decoded every declaration as the locally pinned SourceIO120-byte prefix: raw32-bit flags plus29little-endian float32 values. All1,421values are finite. No SourceIO class, converter, Blender/Godot/native viewer or physics runtime was imported or launched.

All49flags are0x31: the pinned names IS_FLEXIBLE, HAS_ANGLE_CONSTRAINT and HAS_LENGTH_CONSTRAINT. Known mask is0x7f and unknown bits are zero. Two exact float32parameter tuples occur:17rules have yaw/pitch stiffness100 and32have50. The other27fields match: rawlength/tipmass20, yaw/pitch damping5, alongstiffness100, alongdamping0, and anglelimit0.7853981852531433; complete values/ranges are in `actual`. Negative and inactive base limits are preserved. These are raw stored values, without unit/basis conversion, clamping or solver mapping.

The reader validated IDST/version49/declared length, bounded69records at664 with216-byte stride, exact names/parents and an acyclic native index graph. Every rule follows its own bone-relative offset. Their distinct120-byte spans fill[15568,21448), but payload order differs from bone order. Each row records native index/name/parent, separate bone flags/type/rule flags, absolute/relative offsets, record/prefix hashes and all29float32bit patterns. No runtime binding is inferred from names or indices.

Two pinned-code traps are explicitly avoided: pitch friction at prefix+64 precedes pitch bounce at+68, despite opposite dataclass declaration order; the SourceIO Bone constructor puts the rule object into its procedural-type slot. The new reader reads raw numeric type+164 and never changes the approved runtime. The authored unequal pitch sentinel(-7.25,8.5), nonmonotonic pointers/parents, cycles/overlaps/truncation, NaN/Inf, unknownsignedflags and signedzero controls passed26checks. Independent review repeated26checks, added2refusals, matched all49rows and bit patterns with separately decoded bytes, and independently rehashed every1,153protected file. No discrepancy was found.

`INERT_METADATA_PROPOSAL.json` is67,525bytes, below the helper's proposed128KiBmetadata cap. It is explicitly a draft: applied=false, runtime_support=not_implemented, binding unattempted, full native rule layout unverified. The existing adjacent fullparameters256KiBadmission/roundtrip remains untested. Those budgets are product proposals, not native format facts. Reader-only post-bone-table names/payloads, nonnegative signed offsets, unique names and count limits are a narrow supported subset.

The49observed120-byte prefixes do not establish every MDL49 rule's complete size. Official SDK48 has a140-byte struct/BOINGextension not exposed by the pinned reader; unknown bits or extensions must remain unsupported rather than filled with guessed zeroes. This packet does not demonstrate Source's timed solver, full physics constraints, fan response, live Hair&clothes, Off restoration, export determinism, native shader/flex fidelity or component assembly.

Protected before/after evidence covers561native resource files,5original archives,574SourceIO source files, the used approvedPython executable, source/schema/locks and this reader. All1,153entries match SHA/size/nanosecondmtime; independent review read580,637,628bytes to confirm them. The gzip is metadata only, deterministic(empty filename,timestamp0,level9); its raw hash is recorded by `actual/verification.json`. Main production code/HEAD is outside this research's preservation claim and was never edited by this task. Historical local paths in receipts identify owner-PC evidence, not bundled assets.

`schema-reference` copies the helper's earlier design research exactly. Its originalindex is namedSCHEMA_CONTEXT_INDEX as provenance, while this packet's outerINDEX binds every actual copied file. That earlier summary said values were unavailable; this packet supplies them and does not rewrite the historical summary. No nativeMDL/texture/GLB/media or installed runtime is included.

Next bounded work: validate/persist optional inert metadata without enabling a solver; prove native-index→exported source-node→actual imported binding separately; then choose an explicit Source-constrained solver subset or clearly labelled approximation. These49rules enable angle and length constraints, so dropping those would not establish native equivalence. A future dynamic implementation needs scratch ownership, basis/scale provenance, stable stepping and Off/Record/save/export lifecycle checks, followed by a native timed reference before a fidelity claim.
"""
    with (DEST / "README.md").open("x", encoding="utf-8") as stream: stream.write(readme)
    for path in DEST.rglob("*"):
        if path.is_file() and path.name.endswith(".json.gz"): json.loads(gzip.decompress(path.read_bytes()))
    files = {path.relative_to(DEST).as_posix(): identity(path) for path in sorted(DEST.rglob("*")) if path.is_file()}
    assert not any(Path(name).suffix.casefold() in {".mdl", ".vvd", ".vtx", ".vmt", ".vtf", ".glb", ".blend", ".png", ".mp4", ".exe"} for name in files)
    # Preserve the frozen independent index as a real child index.
    child = read(DEST / "review/REVIEW_INDEX.json")
    # Its exact format is retained; the outerindex is the authoritative complete
    # inventory for this publication candidate, independent of context indices.
    save(DEST / "INDEX.json", {"format": "has_junko_raw_jiggle_numeric_packet_index_1", "count": len(files), "bytes": sum(row["bytes"] for row in files.values()),
        "files": files, "native_asset_payloads_or_installed_runtimes": False})
    print(json.dumps({"index": identity(DEST / "INDEX.json"), "files": len(files), "bytes": sum(row["bytes"] for row in files.values()), "rules": 49, "finite_float32values": 1421}))

if __name__ == "__main__": main()
