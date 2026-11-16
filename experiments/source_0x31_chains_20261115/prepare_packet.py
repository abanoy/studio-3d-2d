"""Read-only originals, stdlib-only aggregate profile and staging instructions.

No engine/parser, native geometry export, installed runtime changes, or Git.
All writes are fresh files in this script's own experiment directory.
"""
from pathlib import Path
import ast
import hashlib
import json
import re
import struct

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LEAF = ROOT / "experiments/source_0x31_native_leaf_compat_20261115"
BUNDLE = ROOT / "output/sfm-bone-bindings-native-launch-20261114T033026205/run/Studio/output/compatibility/source-1794627119-888-34370685"
MATH = ROOT / "experiments/source_0x31_godot_candidate_20261115/candidate.gd"
SELECTED = (17,18,26,27)


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,value):
    with (HERE/name).open("x",encoding="utf-8",newline="\n") as f:
        json.dump(value,f,indent=2,allow_nan=False);f.write("\n")


def main():
    pins = {
        "candidate":(MATH,"14053abf4b00c50909468d41372ce77c826bf0ec0b895bec19418a5961b4fae3"),
        "adapter":(LEAF/"leaf_adapter.gd","6945153a65741f65f15505a1b840ddbf530c483790824d8a98e90a4d53e539e8"),
        "capture":(LEAF/"weighted_capture.gd","1ffecc00666a7e9e6957b7354fd0b862eac07b0f16b79200345370348e91aacb"),
        "harness":(LEAF/"leaf_harness.gd","2abbb08831586323878cabb504e5400406144ad34e4b890791539b68633f722c"),
        "glb":(BUNDLE/"scene.glb","4e6ac7c2a7a84dea4b46b0bcb5724af68781243f57737e555b4cc82f2628b90d"),
        "parameters":(BUNDLE/"parameters.json","b807fc82ac1b1d1658b659b41250001e3bdecde99c3d32764122c2add6b51eed"),
    }
    for path,expected in pins.values():
        if sha(path)!=expected: raise ValueError("Retained qualified input changed: "+str(path))
    original_capture=(LEAF/"weighted_capture.gd").read_text(encoding="utf-8-sig")
    capture=original_capture.replace("static func capture(actor: RefCounted, leaf_binding: RefCounted) -> Dictionary:\n",
        "static func capture(actor: RefCounted, selected_bindings: Array) -> Dictionary:\n"
        "\tif selected_bindings.is_empty(): return {\"error\":\"Explicit selected bindings required\"}\n"
        "\tvar leaf_binding: RefCounted = selected_bindings[0]\n"
        "\tvar selected_indices: Array = []\n"
        "\tfor binding in selected_bindings:\n"
        "\t\tif binding.skeleton != leaf_binding.skeleton: return {\"error\":\"Selected bindings span Skeletons\"}\n"
        "\t\tselected_indices.append(binding.skeleton_bone_index)\n")
    capture=capture.replace("if slot_bones[slot] == leaf_binding.skeleton_bone_index:","if selected_indices.has(slot_bones[slot]):")
    if capture==original_capture or capture.count("selected_indices.has")!=1: raise ValueError("Expected exact capture derivation failed")
    capture_path=HERE/"chain_capture.gd"
    if capture_path.exists():
        if capture_path.read_text(encoding="utf-8")!=capture: raise ValueError("Existing derived capture changed")
    else:
        with capture_path.open("x",encoding="utf-8",newline="\n") as f:f.write(capture)
    request=json.loads((BUNDLE/"conversion-request.json").read_bytes())
    mdl=Path(request["source"]);vvd=mdl.with_suffix(".vvd")
    if sha(mdl)!="8da09c905227ddc8eef73a3f83594a4eb1c3a6d5304ee41ba5471bef834bc716": raise ValueError("Native source changed")
    pins.update({"mdl":(mdl,sha(mdl)),"vvd":(vvd,sha(vvd))})
    report=json.loads((BUNDLE/"parameters.json").read_bytes())
    native=report["native_parameters"]
    bones=native["bones"];rules=native["source_jiggle"]["rules"]
    assert len(bones)==69 and len(rules)==49 and report["scale"]==.01905
    rows=[]
    for index in SELECTED:
        r=next(row for row in rules if row["native_bone_index"]==index)
        expected_parent={17:7,18:17,26:25,27:26}[index]
        children=[j for j,b in enumerate(bones) if b["parent"]==index]
        assert bones[index]["parent"]==expected_parent and children==({17:[18],26:[27]}.get(index,[]))
        assert r["raw_rule_flags"]==49 and r["unknown_rule_flag_bits"]==0
        rows.append({"native_index":index,"name":bones[index]["name"],"parent":expected_parent,"children":children,"raw_flags":49,
                     "active_and_along_parameters":{k:r["parameters"][k] for k in ("length","tip_mass","yaw_stiffness","yaw_damping","pitch_stiffness","pitch_damping","angle_limit","along_stiffness","along_damping")},
                     "native_prefix_sha256":r["binary_provenance"]["prefix_sha256"]})
    raw=(BUNDLE/"scene.glb").read_bytes();jsize,jkind=struct.unpack_from("<II",raw,12)
    assert jkind==0x4e4f534a
    gltf=json.loads(raw[20:20+jsize]);offset=20+jsize
    bsize,bkind=struct.unpack_from("<II",raw,offset);assert bkind==0x004e4942
    binary=raw[offset+8:offset+8+bsize]
    assert len(gltf["skins"])==1
    by_node={row["gltf_node_index"]:row["native_index"] for row in native["source_export_crosswalk"]["bones"]}
    slots=[by_node[n] for n in gltf["skins"][0]["joints"]]
    def accessor(index,permitted):
        a=gltf["accessors"][index];assert a["componentType"] in permitted and a["type"]=="VEC4" and not a.get("normalized",False) and "sparse" not in a
        fmt,size=permitted[a["componentType"]];view=gltf["bufferViews"][a["bufferView"]]
        start=view.get("byteOffset",0)+a.get("byteOffset",0);stride=view.get("byteStride",4*size)
        assert start+(a["count"]-1)*stride+4*size<=view.get("byteOffset",0)+view["byteLength"]<=len(binary)
        return [struct.unpack_from("<"+fmt*4,binary,start+i*stride) for i in range(a["count"])]
    groups={"union":set(SELECTED),"pair17_18":{17,18},"pair26_27":{26,27}}
    counts={k:{"vertices":0,"weighted_to_selected":0,"shared_with_other_bones":0,"unaffected":0} for k in groups}
    surfaces=0
    for mesh in gltf["meshes"]:
        for primitive in mesh["primitives"]:
            surfaces+=1
            joints=accessor(primitive["attributes"]["JOINTS_0"],{5121:("B",1),5123:("H",2)})
            weights=accessor(primitive["attributes"]["WEIGHTS_0"],{5126:("f",4)})
            assert len(joints)==len(weights)
            for js,ws in zip(joints,weights):
                for key,selected in groups.items():
                    a=sum(w for j,w in zip(js,ws) if slots[j] in selected)
                    b=sum(w for j,w in zip(js,ws) if slots[j] not in selected)
                    count=counts[key];count["vertices"]+=1;count["weighted_to_selected"]+=a>0
                    count["shared_with_other_bones"]+=a>0 and b>0;count["unaffected"]+=a==0
    save("PUBLIC_PROFILE.json",{"status":"CPU_METADATA_AND_WEIGHT_COUNTS_ONLY_ACTUAL_CHAIN_ENGINE_UNPARSED_UNRUN","source_context_declared_by_root":"9de4e6c",
        "bones":69,"rules":49,"source_scale":.01905,"selected":rows,"surfaces":surfaces,"influence_counts":counts,
        "native_arrays_published":False,"native_metadata_activation_changed":False,"pins":{k:v[1] for k,v in pins.items()}})
    source_paths=[ROOT/p for p in ("src/model.gd","src/secondary_spring.gd","src/secondary_live.gd","src/source_bone_bindings.gd","src/pose_bounds.gd","src/source_shape.gd","src/shape_comparison_bounds.gd")]
    source_paths += [ROOT/"experiments/source_0x31_candidate_20261115/candidate.py"]
    source_paths += [ROOT/"output/source-sdk-jiggle-reference-20261114"/n for n in ("jigglebones.cpp","jigglebones.h","studio.h")]
    save("READ_SOURCE_HASHES.json",{"root_declared_HEAD":"9de4e6c","Git_not_invoked":True,"files":[{"path":p.relative_to(ROOT).as_posix(),"sha256":sha(p),"bytes":p.stat().st_size} for p in source_paths]})
    src=[p for p in (ROOT/"src").rglob("*") if p.is_file() and p.suffix!=".pyc" and "__pycache__" not in p.parts]
    src += [ROOT/p for p in ("run.py","project.godot","main.tscn")]
    save("SOURCE_LOCK.json",{"format":"has_native_pair_source_lock_1","source_HEAD_declared_context":"9de4e6c","files":[{"path":p.relative_to(ROOT).as_posix(),"sha256":sha(p),"bytes":p.stat().st_size} for p in sorted(src)]})
    helpers={k:{"path":str(p),"sha256":h} for k,(p,h) in pins.items()}
    helpers["source_lock"]={"path":str(HERE/"SOURCE_LOCK.json"),"sha256":sha(HERE/"SOURCE_LOCK.json")}
    for name in ("chain_solver","model_adapter","chain_capture","chain_harness"):
        helpers[name]={"path":str(HERE/(name+".gd")),"sha256":sha(HERE/(name+".gd"))}
    for name in ("full_receipt","FK_receipt","math_receipt","leaf_receipt","root_closure"):
        helpers[name]={"path":"REPLACE_WITH_ELIGIBLE_ABSOLUTE_"+name,"sha256":"0"*64}
    save("ROOT_LEASE_TEMPLATE.json",{"format":"has_native_two_pair_readiness_lease_1","phase":"UNAPPROVED_SOURCE_ONLY_TEMPLATE","full_status":"UNRUN","FK_status":"UNRUN","math_status":"UNRUN","leaf_status":"UNRUN","root_closed_all":False,"expires_unix":0,
        "engine_sha256":"REPLACE_WITH_ROOT_VERIFIED_APPROVED_ENGINE_SHA256","files":helpers,"public_result":"REPLACE_WITH_FRESH_ABSOLUTE_ROOT_RESULT"})
    for path in HERE.glob("*.py"):ast.parse(path.read_text(encoding="utf-8-sig"))
    for path in HERE.glob("*.gd"):
        assert not re.search(r"(?m)^\s*(class_name\b|@tool\b)",path.read_text(encoding="utf-8-sig"))
    for path,expected in pins.values():assert sha(path)==expected
    print(json.dumps({"status":"SOURCE_ONLY_PACKET_PREPARED","counts":counts,"GDScript":"UNPARSED_UNRUN","source_files_locked":len(src)}))


if __name__=="__main__":main()
