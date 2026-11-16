"""Read-only CPU profile/lock preparation; no engine invocation or native arrays output."""
from pathlib import Path
import ast
import hashlib
import json
import re
import struct
import time

ROOT = Path(__file__).resolve().parents[2]
CODE = Path(__file__).resolve().parent
BUNDLE = ROOT / "output/sfm-bone-bindings-native-launch-20261114T033026205/run/Studio/output/compatibility/source-1794627119-888-34370685"
MATH = ROOT / "experiments/source_0x31_godot_candidate_20261115/candidate.gd"
SHA_MATH = "14053abf4b00c50909468d41372ce77c826bf0ec0b895bec19418a5961b4fae3"


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def save(name, value):
    with (CODE/name).open("x",encoding="utf-8",newline="\n") as file:
        json.dump(value,file,indent=2,allow_nan=False); file.write("\n")


def main():
    if (CODE/"PUBLIC_PROFILE.json").exists(): raise ValueError("Fresh preparation paths required")
    ast.parse(Path(__file__).read_text(encoding="utf-8-sig"))
    if sha(MATH) != SHA_MATH: raise ValueError("Qualified mathematical source changed")
    parameter_path = BUNDLE/"parameters.json"
    glb_path = BUNDLE/"scene.glb"
    request = json.loads((BUNDLE/"conversion-request.json").read_bytes())
    mdl = Path(request["source"])
    vvd = mdl.with_suffix(".vvd")
    input_paths = {"glb":glb_path,"parameters":parameter_path,"mdl":mdl,"vvd":vvd}
    pins = {key:{"path":str(path),"sha256":sha(path),"bytes":path.stat().st_size} for key,path in input_paths.items()}
    assert pins["glb"]["sha256"] == "4e6ac7c2a7a84dea4b46b0bcb5724af68781243f57737e555b4cc82f2628b90d"
    assert pins["parameters"]["sha256"] == "b807fc82ac1b1d1658b659b41250001e3bdecde99c3d32764122c2add6b51eed"
    assert pins["mdl"]["sha256"] == "8da09c905227ddc8eef73a3f83594a4eb1c3a6d5304ee41ba5471bef834bc716"
    report = json.loads(parameter_path.read_bytes())
    native = report["native_parameters"]
    bones = native["bones"]
    rules = native["source_jiggle"]["rules"]
    rule = next(row for row in rules if row["native_bone_index"] == 8)
    assert len(bones) == 69 and len(rules) == 49 and bones[8] == {"name":"FrontHair1","parent":7}
    assert not any(row["parent"] == 8 for row in bones)
    assert rule["raw_rule_flags"] == 49 and rule["unknown_rule_flag_bits"] == 0 and report["scale"] == .01905
    raw = glb_path.read_bytes()
    jsize,jkind = struct.unpack_from("<II",raw,12)
    assert jkind == 0x4e4f534a
    gltf = json.loads(raw[20:20+jsize])
    offset = 20+jsize
    bsize,bkind = struct.unpack_from("<II",raw,offset)
    assert bkind == 0x004e4942
    binary = raw[offset+8:offset+8+bsize]
    assert len(gltf["skins"]) == 1
    by_node = {row["gltf_node_index"]:row["native_index"] for row in native["source_export_crosswalk"]["bones"]}
    slots = [by_node[index] for index in gltf["skins"][0]["joints"]]
    def accessor(index, permitted):
        value = gltf["accessors"][index]
        assert value["componentType"] in permitted and value["type"] == "VEC4" and not value.get("normalized",False) and "sparse" not in value
        fmt,size = permitted[value["componentType"]]
        view = gltf["bufferViews"][value["bufferView"]]
        first = view.get("byteOffset",0)+value.get("byteOffset",0)
        stride = view.get("byteStride",4*size)
        assert first+(value["count"]-1)*stride+4*size <= view.get("byteOffset",0)+view["byteLength"] <= len(binary)
        return [struct.unpack_from("<"+fmt*4,binary,first+i*stride) for i in range(value["count"])]
    total = affected = shared = surfaces = 0
    for mesh in gltf["meshes"]:
        for primitive in mesh["primitives"]:
            surfaces += 1
            joints = accessor(primitive["attributes"]["JOINTS_0"],{5121:("B",1),5123:("H",2)})
            weights = accessor(primitive["attributes"]["WEIGHTS_0"],{5126:("f",4)})
            assert len(joints) == len(weights)
            for js,ws in zip(joints,weights):
                leaf_weight = sum(w for j,w in zip(js,ws) if slots[j] == 8)
                other_weight = sum(w for j,w in zip(js,ws) if slots[j] != 8)
                total += 1
                affected += leaf_weight > 0
                shared += leaf_weight > 0 and other_weight > 0
    assert (total,affected,shared,surfaces) == (9661,152,144,4)
    public = {"format":"has_native8_leaf_source_profile_1","status":"CPU_PROFILE_MEASURED_ENGINE_LEAF_UNPARSED_UNRUN",
              "native_bones":69,"retained_rules":49,"native_index":8,"native_parent_index":7,"native_name":"FrontHair1","descendants":0,
              "source_conversion_scale":.01905,"rule_flags_hex":"0x31","parameters":{key:rule["parameters"][key] for key in ["length","tip_mass","yaw_stiffness","yaw_damping","pitch_stiffness","pitch_damping","angle_limit","along_stiffness","along_damping"]},
              "binary_prefix_sha256":rule["binary_provenance"]["prefix_sha256"],"profile_input_hashes":{key:row["sha256"] for key,row in pins.items()},
              "vertices":total,"weighted_to_leaf":affected,"shared_with_other_bones":shared,"unaffected_weight_region":total-affected,"surfaces":surfaces,
              "positions_normals_UVs_or_native_rest_arrays_published":False,"source_metadata_modified":False}
    save("PUBLIC_PROFILE.json",public)
    files = [p for p in (ROOT/"src").rglob("*") if p.is_file() and p.suffix != ".pyc" and "__pycache__" not in p.parts]
    files += [ROOT/name for name in ("run.py","project.godot","main.tscn")]
    rows = [{"path":p.relative_to(ROOT).as_posix(),"bytes":p.stat().st_size,"sha256":sha(p)} for p in sorted(files)]
    save("SOURCE_LOCK.json",{"format":"has_native8_actual_model_source_lock_1","source_HEAD_context":"f0dd57a2e568089d396fecba819ab987da658bf0","files":rows})
    helpers = {"candidate":{"path":"REPLACE_WITH_ABSOLUTE_STAGED_leaf_candidate.gd","sha256":SHA_MATH},
               "adapter":{"path":"REPLACE_WITH_ABSOLUTE_STAGED_leaf_adapter.gd","sha256":sha(CODE/"leaf_adapter.gd")},
               "capture":{"path":"REPLACE_WITH_ABSOLUTE_STAGED_weighted_capture.gd","sha256":sha(CODE/"weighted_capture.gd")},
               "harness":{"path":"REPLACE_WITH_ABSOLUTE_STAGED_leaf_harness.gd","sha256":sha(CODE/"leaf_harness.gd")},
               "source_lock":{"path":str(CODE/"SOURCE_LOCK.json"),"sha256":sha(CODE/"SOURCE_LOCK.json")}}
    for key in ("full_receipt","FK_receipt","math_receipt","root_closure"):
        helpers[key] = {"path":"REPLACE_WITH_ABSOLUTE_ELIGIBLE_"+key,"sha256":"0"*64}
    helpers.update(pins)
    save("ROOT_LEASE_TEMPLATE.json",{"format":"has_native8_leaf_readiness_lease_1","phase":"UNAPPROVED_SOURCE_ONLY_TEMPLATE","full_status":"UNRUN","FK_status":"UNRUN","math_status":"UNRUN","root_closed_all":False,"expires_unix":0,
                                     "engine_sha256":sha(Path(r"C:\a\tools\Godot\Godot_v4.6-stable_win64.exe")),"files":helpers,"public_result":"REPLACE_WITH_FRESH_ABSOLUTE_ROOT_OWNED_AGGREGATE_RESULT"})
    guards = {}
    for p in CODE.glob("*.gd"):
        text = p.read_text(encoding="utf-8-sig")
        assert re.search(r"(?m)^\s*(class_name\b|@tool\b)",text) is None
        guards[p.name] = {"sha256":sha(p),"plain_inheritance":text.splitlines()[0],"engine_parsed":False}
    assert not (CODE/"project.godot").exists()
    for key,path in input_paths.items(): assert sha(path) == pins[key]["sha256"]
    save("STATIC_PREPARATION.json",{"format":"has_native8_leaf_static_preparation_1","status":"SOURCE_ONLY_NATIVE_LEAF_UNPARSED_UNRUN","created_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
        "Python_AST_checked":["prepare_profile.py"],"source_only_guards":guards,"actual_application_source_files_locked":len(rows),"actual_leaf_engine_or_parser_launched":False,"candidate_reference_sha256":SHA_MATH,
        "numeric_gates_preregistered":{"float32_world_basis_reconstruction_and_orientation":2e-5,"tip_and_origin_per_root_scale":2e-5,"meaningful_weighted_displacement_per_root_scale":1e-5,"Off_and_unaffected":"Exact private-byte/hash equality"},
        "authoritative_Godot_source":{"commit":"89cea143987d564363e15d207438530651d943ac","path":"scene/3d/skeleton_3d.cpp","sha256":"a3f1c913ee48a9df1dc417ad3b8e2178a33214c9edb3f76947ab2f6a2cdf75dc","global_parent_local_lines":[1106,1122],"reset_rest_lines":[908,913],"read_in_memory_only_by_independent_agent":True},
        "native_geometry_or_coordinate_oracles_copied":False,"originals_rawmetadata_installations_main_tests_HEAD_modified":False,"future_root_gate":"Actual full/FK/math PASS + authoritative closure; root source review, separate fresh locked lease before any engine parse"})
    print(json.dumps({"profile":public,"source_files_locked":len(rows),"GDScript":"UNPARSED_UNRUN"}))


if __name__ == "__main__": main()
