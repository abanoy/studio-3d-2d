"""Independent stdlib-only audit of one terminal fresh native app report.

Reads MDL/GLB/report bytes; never imports a production parser, model runtime or
native application. Only compact counts/index joins/hashes/state flags are saved.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/"output/sfm-extra-native-launch-20261114T013526736/run"
REFERENCE = ROOT/"experiments/source_appearance/native_jiggle_values_20261113/actual/RAW_VALUES.json"
REFERENCE_SHA = "e9665ad604b10932ea6ea7398acafe39ed224dc3be8e37ff287be3786a06dfc6"
JUNKO_SHA = "8da09c905227ddc8eef73a3f83594a4eb1c3a6d5304ee41ba5471bef834bc716"
FIELDS = ("length", "tip_mass", "yaw_stiffness", "yaw_damping", "pitch_stiffness", "pitch_damping", "along_stiffness", "along_damping", "angle_limit", "min_yaw", "max_yaw", "yaw_friction", "yaw_bounce", "min_pitch", "max_pitch", "pitch_friction", "pitch_bounce", "base_mass", "base_stiffness", "base_damping", "base_min_left", "base_max_left", "base_left_friction", "base_min_up", "base_max_up", "base_up_friction", "base_min_forward", "base_max_forward", "base_forward_friction")


def sha(raw): return hashlib.sha256(raw).hexdigest()


def identity(path):
    before = path.stat(); digest = sha(path.read_bytes()); after = path.stat()
    assert (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns)
    return {"bytes": after.st_size, "mtime_ns": after.st_mtime_ns, "sha256": digest}


def pairs(items):
    result = {}
    for key, value in items:
        assert key not in result
        result[key] = value
    return result


def load(path): return json.loads(path.read_bytes(), object_pairs_hook=pairs)


def mdl(raw):
    assert 408 <= len(raw) <= 16*1024*1024 and raw[:4] == b"IDST"
    assert struct.unpack_from("<i", raw, 4)[0] == 49 and struct.unpack_from("<I", raw, 76)[0] == len(raw)
    count, start = struct.unpack_from("<II", raw, 156)
    assert 1 <= count <= 4096 and 408 <= start <= len(raw)-count*216
    bones = []; rules = []
    for index in range(count):
        at = start+index*216; relative, parent = struct.unpack_from("<ii", raw, at)
        name_at = at+relative; end = raw.index(b"\0", name_at)
        assert start+count*216 <= name_at < end < len(raw)
        name = raw[name_at:end].decode("latin-1")
        bones.append({"name": name, "parent": parent})
        flags, kind, offset = struct.unpack_from("<III", raw, at+160)
        if kind == 5:
            target = at+offset; prefix = raw[target:target+120]
            assert len(prefix) == 120
            bits = struct.unpack("<30I", prefix)
            rules.append({"index": index, "parent": parent, "name": name, "bone_flags": flags,
                          "kind": kind, "offset": offset, "at": at, "target": target,
                          "flags": bits[0], "words": list(bits[1:]), "prefix_sha": sha(prefix)})
    return bones, rules


def glb(raw):
    assert 28 <= len(raw) <= 128*1024*1024 and struct.unpack_from("<4sII", raw) == (b"glTF", 2, len(raw))
    offset = 12; chunks = []; value = None
    while offset < len(raw):
        assert offset+8 <= len(raw)
        count, kind = struct.unpack_from("<II", raw, offset); assert count%4 == 0 and offset+8+count <= len(raw)
        if not chunks:
            assert kind == 0x4e4f534a and 0 < count <= 16*1024*1024
            value = json.loads(raw[offset+8:offset+8+count].decode("utf-8"), object_pairs_hook=pairs)
        else: assert len(chunks) == 1 and kind == 0x004e4942
        chunks.append(kind); offset += 8+count
    assert offset == len(raw) and len(chunks) == 2
    return value


def check_jiggle(meta, bones, rules, native_sha):
    assert len(rules) == len(meta["rules"]) == 49
    assert meta["status"] == "retained_inert" and meta["applied"] is False and meta["binding_status"] == "unattempted"
    assert meta["runtime_support"] == "not_implemented" and meta["full_native_rule_layout_verified"] is False
    assert meta["native_mdl_sha256"] == native_sha and meta["native_bone_count"] == len(bones) == 69
    assert meta["source_scale"] == .01905
    reference_raw = REFERENCE.read_bytes(); assert sha(reference_raw) == REFERENCE_SHA
    reference = json.loads(reference_raw); assert reference["wire_field_order"] == list(FIELDS)
    wire = "studio_source_jiggle_binding_1\nnative_mdl_sha256="+native_sha+"\nnative_bone_count=69\nrule_count=49\n"
    joins = 0
    for row, raw, frozen in zip(meta["rules"], rules, reference["rules"]):
        proof = row["binary_provenance"]
        assert row["native_bone_index"] == raw["index"] == frozen["index"]
        assert row["native_bone_name"] == raw["name"] and row["native_parent_index"] == raw["parent"]
        assert row["native_bone_flags"] == raw["bone_flags"] and row["native_procedure_type"] == raw["kind"] == 5
        assert row["raw_rule_flags"] == raw["flags"] == frozen["flags_uint32"] == 0x31
        assert row["applied"] is False and row["binding_status"] == "unattempted"
        assert proof["float32_words_uint32"] == raw["words"] == frozen["float32_words_uint32"]
        assert proof["prefix_sha256"] == raw["prefix_sha"] == frozen["prefix_sha256"] and proof["prefix_bytes"] == 120
        assert (proof["bone_record_offset"], proof["bone_relative_rule_offset"], proof["rule_absolute_offset"]) == (raw["at"], raw["offset"], raw["target"])
        values = [row["parameters"][name] for name in FIELDS]
        assert all(type(v) in (int, float) and math.isfinite(v) for v in values)
        assert list(struct.unpack("<29I", struct.pack("<29f", *values))) == raw["words"]
        assert row["parameters"] == frozen["parameters"]
        wire += "rule=%d\t%d\t%s\t%d\t5\t49\t%s\n" % (raw["index"], raw["parent"], raw["name"], raw["bone_flags"], raw["prefix_sha"])
        wire += "words="+"\t".join(str(word) for word in raw["words"])+"\n"; joins += 29
    return sha(wire.encode("ascii")), joins


def check_crosswalk(crosswalk, bones, doc, native_sha, original_sha, glb_sha, jiggle_sha):
    assert crosswalk["format"] == "studio_source_bone_crosswalk_1" and crosswalk["profile"] == "junko_hair_mdl49_fe242_blender51_1"
    assert crosswalk["status"] == "retained_inert" and crosswalk["applied"] is False
    assert crosswalk["runtime_binding"] == "unattempted" and crosswalk["native_solver"] == "not_implemented"
    assert crosswalk["source_scale"] == .01905 and crosswalk["native_bone_count"] == len(crosswalk["bones"]) == 69
    assert type(crosswalk["max_rest_matrix_error"]) in (int, float) and math.isfinite(crosswalk["max_rest_matrix_error"]) and 0 <= crosswalk["max_rest_matrix_error"] <= 2e-5
    catalogue = sha(json.dumps(bones, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode()+b"\n")
    expected = {"original_source_sha256": original_sha, "native_mdl_sha256": native_sha, "glb_sha256": glb_sha,
                "native_bone_catalogue_sha256": catalogue, "jiggle_wire_sha256": jiggle_sha}
    wire = "studio_source_bone_crosswalk_binding_1\n"
    for key, value in expected.items(): assert crosswalk[key] == value; wire += key+"="+value+"\n"
    wire += "native_bone_count=69\n"; rows = sorted(crosswalk["bones"], key=lambda row: row["native_index"])
    assert [row["native_index"] for row in rows] == list(range(69))
    nodes = doc["nodes"]; skins = doc["skins"]; parent_map = {}
    for index, node in enumerate(nodes):
        for child in node.get("children", []):
            assert type(child) is int and 0 <= child < len(nodes) and child not in parent_map
            parent_map[child] = index
    selected = doc["scene"]; roots = doc["scenes"][selected]["nodes"]; reachable = set(); queue = list(roots)
    while queue:
        node = queue.pop(); assert node not in reachable
        reachable.add(node); queue.extend(nodes[node].get("children", []))
    source_nodes = {row["gltf_node_index"] for row in rows}; assert len(source_nodes) == 69 and source_nodes <= reachable
    numeric = []; memberships_count = 0
    for index, row in enumerate(rows):
        assert set(row) == {"native_index", "native_name", "native_parent_index", "gltf_node_index", "skin_memberships"}
        assert row["native_name"] == bones[index]["name"] and row["native_parent_index"] == bones[index]["parent"]
        node = row["gltf_node_index"]; assert nodes[node]["name"] == row["native_name"]
        parent = parent_map.get(node, -1)
        while parent >= 0 and parent not in source_nodes: parent = parent_map.get(parent, -1)
        assert parent == (-1 if row["native_parent_index"] < 0 else rows[row["native_parent_index"]]["gltf_node_index"])
        members = sorted(row["skin_memberships"], key=lambda m: (m["skin_index"], m["joint_slot"]))
        assert len(members) == len(skins) == 1
        wire += "bone=%d\t%d\t%d\t%s\t%d\n" % (index, row["native_parent_index"], node, row["native_name"], len(members))
        for member in members:
            assert set(member) == {"skin_index", "joint_slot"}
            skin = skins[member["skin_index"]]; assert len(skin["joints"]) == len(set(skin["joints"])) == 69
            assert skin["joints"][member["joint_slot"]] == node
            assert any(i in reachable and n.get("skin") == member["skin_index"] and "mesh" in n for i, n in enumerate(nodes))
            wire += "skin=%d\t%d\n" % (member["skin_index"], member["joint_slot"])
            numeric.append([index, row["native_parent_index"], node, member["skin_index"], member["joint_slot"]]); memberships_count += 1
    assert sha(wire.encode("ascii")) == crosswalk["proof_sha256"]
    return {"rows": 69, "skin_slots": memberships_count, "reachable_nodes": len(reachable), "skins": len(skins),
            "proof_sha256": crosswalk["proof_sha256"], "jiggle_wire_sha256": jiggle_sha,
            "max_rest_matrix_error": crosswalk["max_rest_matrix_error"], "numeric_index_parent_node_skin_slot_rows": numeric,
            "opaque_observed_proof_sha256_not_reconstructed": crosswalk["observed_proof_sha256"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--run", type=Path, required=True); args = parser.parse_args()
    run = args.run.resolve(strict=True); assert run.parent.parent == ROOT/"output"
    suite_path = run/"verification.json"; suite = load(suite_path)
    assert suite["passed"] is True and not suite["errors"] and all(suite["preservation"].values())
    assert suite["writer"]["strict_result_binding"] and all(reader["strict_result_binding"] for reader in suite["readers"])
    manifest = load(run/"input-manifest.json"); source_cases = {row["name"]: row for row in manifest["cases"]}
    baseline = {row["name"]: row for row in load(BASE/"writer/result.json")["cases"]}
    before = {str(suite_path): identity(suite_path), str(REFERENCE): identity(REFERENCE), str(Path(__file__)): identity(Path(__file__))}; results = []
    for case in suite["writer"]["result"]["cases"]:
        bundle = Path(case["bundle"]); report_path = bundle/"parameters.json"; request_path = bundle/"conversion-request.json"
        report = load(report_path); request = load(request_path); native_path = Path(request["source"])
        original = Path(source_cases[case["name"]]["source"]); baseline_folder = Path(baseline[case["name"]]["bundle"])
        selected = [report_path, request_path, native_path, original, bundle/"scene.glb", baseline_folder/"parameters.json", baseline_folder/"scene.glb"]
        before.update({str(path): identity(path) for path in selected})
        original_sha = sha(original.read_bytes()); native_sha = sha(native_path.read_bytes()); glb_sha = sha((bundle/"scene.glb").read_bytes())
        assert original_sha == request["sha256"] == report["source_sha256"] == native_sha
        bones, rules = mdl(native_path.read_bytes()); native = report["native_parameters"]; assert native["bones"] == bones
        assert len(report_path.read_bytes()) <= 256*1024
        summary = {"name": case["name"], "native_bones": len(bones), "native_sha256": native_sha, "GLB_sha256": glb_sha,
                   "report_bytes": report_path.stat().st_size, "report_sha256": before[str(report_path)]["sha256"]}
        old = load(baseline_folder/"parameters.json"); old["original_source"] = report["original_source"]
        if native_sha == JUNKO_SHA:
            wire, joins = check_jiggle(native["source_jiggle"], bones, rules, native_sha)
            assert joins == 1421
            summary.update(check_crosswalk(native["source_export_crosswalk"], bones, glb((bundle/"scene.glb").read_bytes()), native_sha, original_sha, glb_sha, wire))
            summary["exact_float32_word_joins"] = joins
            without = json.loads(json.dumps(report)); del without["native_parameters"]["source_export_crosswalk"]
            assert without == old
            summary["only_report_changes_crosswalk_and_original_alias"] = True
        else:
            assert "source_export_crosswalk" not in native
            summary["crosswalk_absent"] = True
            if source_cases[case["name"]].get("expected_jiggle_rules") == 0:
                assert not rules and "source_jiggle" not in native and report == old
                legacy = json.dumps(old, ensure_ascii=True, indent=2).replace("\n", "\r\n").encode("utf-8")
                assert legacy == report_path.read_bytes()
                summary["exact_legacy_report_bytes_after_alias_relocation"] = True
        if case["name"] != "mima_head-ordinary-shape-ui":
            assert (bundle/"scene.glb").read_bytes() == (baseline_folder/"scene.glb").read_bytes()
            summary["raw_GLB_equal_previous_actual_baseline"] = True
        results.append(summary)
    assert before == {path: identity(Path(path)) for path in before}
    runtime = load(run/"runtimes-before.json")
    writer_named = suite["writer"]["result"]["named_checks"]
    reader_named = [reader["result"]["named_checks"] for reader in suite["readers"]]
    assert all(writer_named.values()) and all(all(row.values()) for row in reader_named)
    result = {"format": "has_source_bone_actual_independent_audit_1", "passed": True, "run": str(run),
              "actual_native_conversion": True, "actual_runtime_binding_observed_by_strict_harness": True,
              "native_solver": "not_implemented", "writer_named_checks": len(writer_named),
              "reader_named_checks": sum(len(row) for row in reader_named), "cases": results,
              "installed_exporter_noncache_source_count": len(runtime["blender_exporter_noncache_sources"]),
              "preservation_gates": suite["preservation"], "inputs_preserved_during_audit": True,
              "file_identities": before, "no_production_parser_imported": True,
              "publication": "Counts/hashes/numeric index-parent-node-skin-slot joins only; no rest arrays, mesh values or media"}
    target = Path(__file__).with_name("AUDIT.json")
    with target.open("x", encoding="utf-8", newline="\n") as stream: json.dump(result, stream, indent=2); stream.write("\n")
    print(json.dumps({"audit": str(target), "sha256": sha(target.read_bytes()), "passed": True}))


if __name__ == "__main__": main()
