"""Read-only CPU joins against retained local proof; writes compact audit only.

No Blender/Godot/SourceIO import, export, solver, media or native launch. Private
native rest arrays and geometry remain in their existing local files and RAM.
"""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/"tools")); sys.path.insert(0, str(ROOT/"tests"))
import source_bone_metadata as M
import source_jiggle_crosswalk as C
import secondary_helpers as H
import verify_source_jiggle_native_report as V

BASE = ROOT/"output/sfm-extra-native-launch-20261114T013526736/run"
PRIVATE = ROOT/"output/crosswalk-qualification-20261114T0240/case-junko-default/diagnostics/crosswalk-proof.json"
EXPORTER = Path(r"C:\Program Files\Blender Foundation\Blender 5.1\5.1\scripts\addons_core\io_scene_gltf2")
SOURCEIO = ROOT/"output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647"
MANIFEST = ROOT/"output/sfm-bone-bindings-native-inputs-20261114.json"


def digest(raw): return hashlib.sha256(raw).hexdigest()


def identity(path):
    before = path.stat(); sha = digest(path.read_bytes()); after = path.stat()
    assert (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns)
    return {"bytes": after.st_size, "mtime_ns": after.st_mtime_ns, "sha256": sha}


def eligible(row, owners, parents):
    proposal = row.get("existing_chain", {}); center = proposal.get("center_node")
    joints = proposal.get("joint_nodes", [])
    if center not in parents or center in owners or not 0 < len(joints) <= 64: return False
    seen = {center}; previous = center
    for node in joints:
        if node in seen or node not in owners or parents.get(node) != previous: return False
        seen.add(node); previous = node
    return True


def main():
    writer = json.loads((BASE/"writer/result.json").read_bytes())
    cases = {row["name"]: row for row in writer["cases"]}
    junko = Path(cases["junko_hair-default-no-appearance"]["bundle"])
    nitori = Path(cases["multi_skin_glove-default-no-appearance"]["bundle"])
    request = json.loads((junko/"conversion-request.json").read_bytes())
    source_names = ["tools/blender_source_bridge.py", "tools/source_jiggle_crosswalk.py", "tools/source_bone_metadata.py",
                    "tools/source_bone_export.py", "tools/source_jiggle_metadata.py", "tools/source_jiggle_values.py",
                    "tools/source_mdl_snapshot.py", "tools/secondary_helpers.py", "tools/prepare_source.py",
                    "src/source_bone_bindings.gd", "src/secondary_helper_editor.gd", "src/scene3d.gd", "src/model.gd",
                    "tests/native_source_binding_ui.gd", "tests/source_choices_native_smoke.gd",
                    "tests/verify_source_choices_native.py", "tests/verify_source_jiggle_native_report.py"]
    paths = [ROOT/name for name in source_names] + [Path(__file__), PRIVATE, MANIFEST,
             Path(request["source"]), Path(request["original_source"]),
             ROOT/"experiments/source_appearance/native_jiggle_values_20261113/actual/RAW_VALUES.json"]
    paths += [folder/name for folder in (junko, nitori) for name in ("scene.glb", "parameters.json", "conversion-request.json")]
    paths += [SOURCEIO/name for name in C.SOURCEIO_PINS] + [EXPORTER/name for name in C.EXPORTER_PINS]
    before = {str(path): identity(path) for path in paths}
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    proof = json.loads(PRIVATE.read_bytes()); report = json.loads((junko/"parameters.json").read_bytes())
    plan = {"state": "embedded", "report": report, "report_bytes": (junko/"parameters.json").read_bytes(), "note_bytes": None, "omission": None}
    combined = M.plan_report(plan, proof, expected_original_sha256=report["source_sha256"],
                            expected_native_sha256=proof["native_mdl_sha256"], expected_glb_sha256=proof["glb_sha256"], newline="\r\n")
    compact = combined["report"]["native_parameters"][M.KEY]
    raw = Path(request["source"]).read_bytes(); count, start = struct.unpack_from("<2I", raw, 156)
    assert count == 69 and digest(raw) == C.JUNKO_SHA256
    for row in proof["bones"]:
        assert list(struct.unpack_from("<7I", raw, start+row["native_index"]*216+32)) == row["native_rest_words_uint32"]
    value = C.final_glb_json((junko/"scene.glb").read_bytes())
    by = {row["native_index"]: row["gltf_node_index"] for row in proof["bones"]}
    parents = {by[row["native_index"]]: -1 if row["native_parent_index"] < 0 else by[row["native_parent_index"]] for row in proof["bones"]}
    actual_parents = {child: i for i, node in enumerate(value["nodes"]) for child in node.get("children", [])}
    slots = 0
    for row in compact["bones"]:
        node = row["gltf_node_index"]
        assert value["nodes"][node]["name"] == row["native_name"]
        at = actual_parents.get(node, -1)
        while at >= 0 and at not in parents: at = actual_parents.get(at, -1)
        assert at == parents[node]
        for membership in row["skin_memberships"]:
            assert value["skins"][membership["skin_index"]]["joints"][membership["joint_slot"]] == node
            slots += 1
    owners = {by[row["native_bone_index"]] for row in report["native_parameters"]["source_jiggle"]["rules"]}
    assessment = H.inspect(junko/"scene.glb"); options = []
    eligible_count = 0
    for index, row in enumerate(assessment["regions"]):
        native = eligible(row, owners, parents); eligible_count += int(native)
        score = (2 if row["suggested"] else 0)+(1 if row.get("anchor_min_weight", 0) >= .01 else 0)+(8 if native else 0)
        if not row["already_rigged"]: options.append((score, index))
    selected = max(options, key=lambda pair: (pair[0], -pair[1]))[1]
    row = assessment["regions"][selected]; assert eligible(row, owners, parents)
    preview_request = {"source_sha256": proof["glb_sha256"], "segments": 3, "node": row["node"],
                       "primitive": row["primitive"], "component": row["component"], "anchor_node": row["anchor_node"], "review_only": True}
    weighted = H.preview(junko/"scene.glb", preview_request)
    existing = H.preview(junko/"scene.glb", {**preview_request, "use_existing_joints": True})
    joins = [V.verify(junko/"conversion-request.json", junko/"parameters.json", 49),
             V.verify(nitori/"conversion-request.json", nitori/"parameters.json", 0)]
    assert before == {str(path): identity(path) for path in paths}
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == revision
    audit = {"format": "has_source_bone_readonly_real_data_audit_1", "passed": True, "root_revision": revision,
             "source_context": "current_main_working_source_readonly_not_actual_main_conversion",
             "APIs_executed_CPU_only": ["source_bone_metadata.plan_report", "source_bone_metadata.compact_metadata",
                 "source_bone_metadata.jiggle_wire_sha256", "source_bone_metadata.proof_wire_bytes",
                 "source_jiggle_crosswalk.final_glb_json", "secondary_helpers.inspect", "secondary_helpers.preview",
                 "verify_source_jiggle_native_report.verify", "struct.unpack_from(<7I,nativeBone+32)"],
             "producer": {"projected_report_bytes": len(combined["report_bytes"]), "budget_bytes": M.J.REPORT_LIMIT,
                          "headroom_bytes": M.J.REPORT_LIMIT-len(combined["report_bytes"]),
                          "compact_crosswalk_bytes": len(C.compact(compact)), "native_rows": 69,
                          "native_rest_word_joins": 483, "GLB_joint_name_parent_joins": 69, "skin_slot_joins": slots,
                          "glb_sha256": proof["glb_sha256"], "jiggle_wire_sha256": compact["jiggle_wire_sha256"],
                          "proof_sha256": compact["proof_sha256"], "max_rest_matrix_error": compact["max_rest_matrix_error"],
                          "native_values_unchanged": combined["report"]["native_parameters"]["source_jiggle"] == report["native_parameters"]["source_jiggle"]},
             "simple_helper_CPU": {"regions": len(assessment["regions"]), "skipped": len(assessment["skipped"]),
                 "native_eligible_chains": eligible_count, "selected_region": selected,
                 "selected_tuple": {key: row[key] for key in ("node", "primitive", "component")},
                 "selected_native_eligible": True, "initial_weighted_can_apply": weighted["can_apply"],
                 "existing_mode": existing["mode"], "existing_can_apply": existing["can_apply"],
                 "existing_rotating_joint_count": len(existing["existing_chain"]["joint_nodes"]),
                 "affected_regions": len(existing["affected_regions"]), "affected_vertices": existing["affected_vertices"]},
             "independent_native_value_joins": joins, "file_identities": before, "inputs_preserved": True,
             "actual_main_native_conversion": "UNRUN", "actual_HAS_binding": "UNRUN", "actual_Simple_helper_UI": "UNRUN",
             "native_solver": "not_implemented", "publication": "Counts, hashes, numeric joins only; no rest/mesh arrays or media",
             "preservation_boundary": "Native harness maps Blender executable and SourceIOtree; full installed exporter tree needs external fresh guard beyond producer14criticalpins"}
    target = HERE/"AUDIT.json"
    with target.open("x", encoding="utf-8", newline="\n") as stream: json.dump(audit, stream, indent=2); stream.write("\n")
    print(json.dumps({"audit": str(target), "sha256": identity(target)["sha256"], "passed": True}))


if __name__ == "__main__": main()
