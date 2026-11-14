"""CPU-only source-bound numeric extraction. No SourceIO/runtime imports."""
import collections
import gzip
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import time

sys.dont_write_bytecode = True
import jiggle_values as J

TASK = Path(__file__).absolute().parents[1]
ROOT = TASK.parents[1]
NATIVE_STAGE = ROOT / "output/sfm-broader-native-cases-20261113/stage"
CORE_STAGE = ROOT / "output/sfm-next-cases-20261112/stage"
MDL = NATIVE_STAGE / "junko_v25/models/touhou/tamo/junko hair.mdl"
MDL_SHA = "8da09c905227ddc8eef73a3f83594a4eb1c3a6d5304ee41ba5471bef834bc716"
STATIC = ROOT / "output/sfm-native-main-rebind-20261113"
SOURCEIO = ROOT / "output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647"
SCHEMA = ROOT / "output/source-jiggle-schema-prep-20261113"
DOCS = {"library/models/mdl/structs/bone.py": "a61a3e0378e7b2d2d070f2b9ef138b78516db4a9830144cd6a6d907295b7d085",
        "library/models/mdl/structs/header.py": "03fe4f685c3818785c9b5ff81356f91aa9ab8160d1a17ca27e57520a1c37f57f",
        "library/models/mdl/structs/jiggle_bone.py": "a06cd6e0234fd29894c702003015fad7d0601839572b4fe3dbbfb4b9b082feec"}
PYTHON_SHA = "03573716a7fcbd8b7fed8fe0163bbfbd3a852546920d6a666123f307c8dac7d9"

def identity(path):
    path = Path(path)
    for parent in (path, *path.parents):
        info = parent.lstat()
        J.require(not stat.S_ISLNK(info.st_mode) and not (getattr(info, "st_file_attributes", 0) & 0x400), "Reparse input refused")
    before = path.stat()
    with path.open("rb") as stream: sha = hashlib.file_digest(stream, "sha256").hexdigest()
    after = path.stat()
    J.require((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns), "Input changed during hashing")
    return {"sha256": sha, "bytes": before.st_size, "mtime_ns": before.st_mtime_ns}

def read(path):
    J.require(path.stat().st_size <= 8 * 1024 * 1024, "Metadata exceeds reader budget")
    return json.loads(path.read_bytes())

def write(path, value, limit=256 * 1024):
    raw = json.dumps(value, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode("utf-8") + b"\n"
    J.require(len(raw) <= limit, "Output metadata exceeds explicit byte budget")
    with path.open("xb") as stream: stream.write(raw)
    return identity(path)

def main():
    run = TASK / "runs" / str(time.time_ns()); run.mkdir(parents=True, exist_ok=False)
    core_lock_path = STATIC / "conversion-inputs-core2.json"
    wide_lock_path = STATIC / "conversion-inputs-wide2.json"
    core, wider = read(core_lock_path), read(wide_lock_path)
    before = {}
    # Protect native resources and original containers only. Historical cf7main
    # Python pins are not reinterpreted after root's separate bridge boot fix.
    for lock in (core, wider):
        for path, expected in lock["files"].items():
            candidate = Path(path)
            if candidate.is_relative_to(CORE_STAGE) or candidate.is_relative_to(NATIVE_STAGE):
                observed = identity(candidate)
                J.require(observed == expected, "Checksum-bound native stage changed")
                before[path] = observed
    plan_path = STATIC / "RESOURCE_PLAN.json"; plan = read(plan_path)
    for path, expected in plan["original_archives"].items():
        observed = identity(Path(path)); J.require(observed == expected, "Original native archive changed"); before[path] = observed
    sourceio = {}
    for base, dirs, files in os.walk(SOURCEIO, followlinks=False):
        dirs[:] = sorted(name for name in dirs if name not in {".git", "__pycache__"})
        for name in sorted(files):
            path = Path(base) / name
            if path.suffix not in {".pyc", ".pyo"}: sourceio[path.relative_to(SOURCEIO).as_posix()] = identity(path)
    J.require(sourceio == core["sourceio_tree"], "Pinned SourceIO source tree changed")
    for relative, value in sourceio.items(): before[str(SOURCEIO / relative)] = value
    for relative, sha in DOCS.items(): J.require(before[str(SOURCEIO / relative)]["sha256"] == sha, "Pinned layout documentation differs")
    files = [MDL, core_lock_path, wide_lock_path, plan_path, Path(J.__file__), Path(__file__), Path(__file__).with_name("test_jiggle_values.py"), Path(sys.executable)]
    files += [SCHEMA / name for name in ("INDEX.json", "SOURCEIO_SDK_SCHEMA.md", "SUMMARY.json", "HAS_MAPPING.md", "JUNKO_CASES.json")]
    for path in files: before[str(path)] = identity(path)
    J.require(before[str(Path(sys.executable))]["sha256"] == PYTHON_SHA, "Approved Python executable changed")
    J.require(before[str(MDL)]["sha256"] == MDL_SHA and before[str(MDL)]["bytes"] == 37644, "Selected native MDL changed")
    parsed = J.parse(MDL.read_bytes())
    J.require(parsed["bone_count"] == 69 and len(parsed["rules"]) == 49 and not parsed["unsupported"], "Actual Junko declaration scope differs")
    # Exact independent historical identity join; no name/order substitution.
    families_path = STATIC / "WIDER_FAMILIES.json"
    before[str(families_path)] = identity(families_path)
    historical = read(families_path)["families"]["junko_v25"]["models"]["junko_hair"]["historical_full_native_metadata"]
    J.require(historical["sha256"] == MDL_SHA, "Historical native join differs")
    J.require([(b["index"], b["name"], b["parent"], b["bone_flags_uint32"]) for b in parsed["bones"]] == [(b["index"], b["name"], b["parent"], b["flags"]) for b in historical["bones"]], "Native bone identity/parent join differs")
    J.require([(b["index"], b["name"], b["procedural_type_uint32"]) for b in parsed["rules"]] == [(b["index"], b["name"], b["type"]) for b in historical["procedural_bones"]], "Native procedural declarations differ")
    parsed["sourceio_layout_documentation"] = {relative: before[str(SOURCEIO / relative)] for relative in DOCS}
    parsed["schema_reference"] = {name: before[str(SCHEMA / name)] for name in ("INDEX.json", "SOURCEIO_SDK_SCHEMA.md", "SUMMARY.json", "HAS_MAPPING.md", "JUNKO_CASES.json")}
    raw_proof = write(run / "RAW_VALUES.json", parsed)
    metadata_rules = []
    for row in parsed["rules"]:
        metadata_rules.append({"native_bone_index": row["index"], "native_bone_name": row["name"], "native_parent_index": row["parent"],
            "native_bone_flags": row["bone_flags_uint32"], "native_procedure_type": row["procedural_type_uint32"],
            "raw_rule_flags": row["flags_uint32"], "known_rule_flags": row["known_flags"], "unknown_rule_flag_bits": row["unknown_flags_mask"],
            "parameters": row["parameters"], "binary_provenance": {"bone_record_offset": row["record_offset"], "bone_relative_rule_offset": row["procedure_relative_offset_uint32"],
                "rule_absolute_offset": row["payload_offset"], "prefix_bytes": 120, "prefix_sha256": row["prefix_sha256"], "float32_words_uint32": row["float32_words_uint32"]},
            "binding_status": "unattempted", "applied": False})
    archive_path = next(path for path in plan["original_archives"] if Path(path).name == "Junko_Tamo_sfm_v25.zip")
    proposal = {"format": "studio_source_jiggle_metadata_1", "schema_status": "PROPOSAL_NOT_IMPLEMENTED", "applied": False, "runtime_support": "not_implemented",
        "original_source_sha256": before[archive_path]["sha256"], "native_mdl_sha256": MDL_SHA, "native_version": 49, "native_bone_count": 69,
        "parser_revision": "output_only_jiggle_prefix_reader_20261113", "parser_file_sha256": before[str(Path(J.__file__))]["sha256"],
        "sourceio_revision": "fe24260b97ac03b899d9b5d4f0fd7b34772f3647", "parsed_layout": "sourceio_flags_plus_29_float_prefix_120",
        "full_native_rule_layout_verified": False, "source_scale": None, "units": "Unconverted raw native values; no scale/basis or solver mapping applied",
        "rules": metadata_rules, "unsupported": [],
        "layout_limits": ["All49observed120byte prefixes are separately bounded; complete MDL49/140byte BOING layout not inferred.",
            "Flags0x31 enable flexible/angle/length bits; noHASsolver equivalence or native runtime binding is established.",
            "Bone/procedure/rule flags remain separate namespaces; declared SourceIO Bone constructor and pitch dataclass order defects are not copied."]}
    proposed_identity = write(run / "INERT_METADATA_PROPOSAL.json", proposal, 128 * 1024)
    groups = {}
    for row in parsed["rules"]:
        key = tuple(row["float32_words_uint32"])
        groups.setdefault(key, []).append(row["index"])
    distributions = {"format": "has_junko_raw_jiggle_distributions_1", "native_mdl_sha256": MDL_SHA, "bones": 69, "rules": 49, "finite_float_count": 49 * 29,
        "rule_flags": dict(collections.Counter(str(row["flags_uint32"]) for row in parsed["rules"])),
        "unknown_rule_flag_bits": sorted({row["unknown_flags_mask"] for row in parsed["rules"]}),
        "values_by_field": {name: {"min": min(r["parameters"][name] for r in parsed["rules"]), "max": max(r["parameters"][name] for r in parsed["rules"]),
            "distinct_values": sorted({r["parameters"][name] for r in parsed["rules"]})} for name in J.FIELDS},
        "exact_float32_parameter_groups": [{"bone_indices": indices, "count": len(indices), "parameters": parsed["rules"][next(i for i,r in enumerate(parsed["rules"]) if r["index"] == indices[0])]["parameters"]} for words, indices in groups.items()],
        "selected_cases": [next(row for row in parsed["rules"] if row["index"] == index) for index in (8, 17, 18, 26, 27)],
        "observed_payload_prefix_span": [min(row["payload_offset"] for row in parsed["rules"]), max(row["payload_offset"] + 120 for row in parsed["rules"])],
        "observed120byte_packing_contiguous": parsed["observed_prefix_ranges_contiguous"], "runtime_binding_or_simulation": "UNATTEMPTED"}
    write(run / "DISTRIBUTIONS.json", distributions)
    after = {path: identity(Path(path)) for path in before}
    J.require(after == before, "Protected native/archive/runtime/schema/source/lock inputs changed")
    preservation = {"format": "has_jiggle_raw_extraction_preservation_1", "before": before, "after": after, "unchanged": True,
        "scope": "561native resource files,5original archives,574SourceIO source files,usedPython+layout/schema/locks/parser. No currentproduction source freeze claim."}
    preservation_raw = json.dumps(preservation, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    with (run / "PRESERVATION.json.gz").open("xb") as stream:
        with gzip.GzipFile(filename="", mode="wb", compresslevel=9, fileobj=stream, mtime=0) as output: output.write(preservation_raw)
    receipt = {"format": "has_junko_raw_jiggle_extraction_actual_1", "passed": True, "run": str(run), "native_mdl_sha256": MDL_SHA,
        "raw_values": raw_proof, "inert_proposal": proposed_identity, "raw_rule_flags_all": 49, "known_rule_flags_mask": 127, "unknown_bits_all": 0,
        "bone_count": 69, "rule_count": 49, "finite_float_count": 1421, "exact_parameter_groups": [len(indices) for indices in groups.values()],
        "native_resources_preserved": 561, "original_archives_preserved": len(plan["original_archives"]), "sourceio_source_files_preserved": len(sourceio),
        "all_declared_protected_inputs_unchanged": True, "protected_file_count": len(before),
        "preservation_gzip": identity(run / "PRESERVATION.json.gz"), "preservation_raw_sha256": hashlib.sha256(preservation_raw).hexdigest(),
        "proposed128KiBmetadata_budget_met": proposed_identity["bytes"] <= 128 * 1024,
        "proposed256KiBfull_parameters_report_admission": "UNTESTED; existing importerreport size/roundtrip not changed here",
        "runtime_import_or_modification_converter_Godot_Blender_GPU_newtools_Steamwrites": False,
        "limits": ["Pinned reader120byte prefix and exact raw native offsets only; fullrule extension/BOING/other MDL layouts unproven.",
            "Reader's afterbone names/payloads,nonnegativeoffset,unique-name128rule/4096bone limits are narrow admission policies,not universalnativeformat facts.",
            "All values preserved; no unit conversion, clamp, runtimebinding, physics mapping, simulation or UI integration.",
            "SourceIO Bone constructor and pitch field ordering discrepancies are documented,not fixed in approvedruntime."]}
    write(run / "verification.json", receipt)
    print(json.dumps({key: receipt[key] for key in ("passed", "run", "rule_count", "finite_float_count", "exact_parameter_groups", "protected_file_count", "proposed128KiBmetadata_budget_met")}))

if __name__ == "__main__": main()
