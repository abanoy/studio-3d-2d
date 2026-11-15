"""Read-only GLB/native metadata inventory for a future ordinary shape-UI probe.

Pure stdlib. No SourceIO/Godot/Blender/model script import or conversion. Only
counts, identities and derived-target hashes are written, never mesh buffers.
"""
import hashlib
import json
import math
from pathlib import Path
import stat
import struct

TASK = Path(__file__).absolute().parent
ROOT = TASK.parents[1]
CORE = ROOT / "output/sfm-native-main-rebind-20261113/conversion-run-1794613497806249400"
WIDER = ROOT / "output/sfm-native-main-rebind-20261113/WIDER_FAMILIES.json"
INVENTORY = ROOT / "output/sfm-extra-native-inventory/portable-root-639301165838922272/metadata.json"

def identity(path):
    for parent in (path, *path.parents):
        info = parent.lstat(); assert not stat.S_ISLNK(info.st_mode) and not (getattr(info, "st_file_attributes", 0) & 0x400)
    before = path.stat()
    with path.open("rb") as stream: sha = hashlib.file_digest(stream, "sha256").hexdigest()
    assert (before.st_size, before.st_mtime_ns) == (path.stat().st_size, path.stat().st_mtime_ns)
    return {"sha256": sha, "bytes": before.st_size, "mtime_ns": before.st_mtime_ns}

class GLB:
    def __init__(self, path):
        self.path = path; self.identity = identity(path); raw = path.read_bytes()
        assert len(raw) <= 128 * 1024 * 1024 and struct.unpack_from("<4sII", raw) == (b"glTF", 2, len(raw))
        cursor = 12; doc = binary = None
        while cursor < len(raw):
            length, kind = struct.unpack_from("<II", raw, cursor); cursor += 8
            assert length % 4 == 0 and cursor + length <= len(raw)
            value = raw[cursor:cursor + length]; cursor += length
            if kind == 0x4E4F534A: assert doc is None; doc = json.loads(value)
            elif kind == 0x004E4942: assert binary is None; binary = value
            else: raise ValueError("Unexpected GLB chunk")
        assert doc is not None and binary is not None and len(doc.get("buffers", [])) == 1
        assert "uri" not in doc["buffers"][0] and len(binary) - 3 <= doc["buffers"][0]["byteLength"] <= len(binary)
        self.doc, self.binary = doc, binary

    def region(self, view_id, offset, length):
        view = self.doc["bufferViews"][view_id]
        assert view.get("buffer", 0) == 0 and type(offset) is int and type(length) is int and min(offset, length) >= 0
        assert offset + length <= view["byteLength"]
        at = view.get("byteOffset", 0) + offset
        assert 0 <= at <= len(self.binary) - length
        return self.binary[at:at + length]

    def vec3(self, index):
        accessor = self.doc["accessors"][index]; count = accessor["count"]
        assert accessor["type"] == "VEC3" and accessor["componentType"] == 5126 and not accessor.get("normalized", False)
        assert type(count) is int and 0 < count <= 200000
        result = [(0.0, 0.0, 0.0)] * count
        if "bufferView" in accessor:
            view = self.doc["bufferViews"][accessor["bufferView"]]; stride = view.get("byteStride", 12)
            assert type(stride) is int and stride >= 12 and stride % 4 == 0
            offset = accessor.get("byteOffset", 0)
            for i in range(count): result[i] = struct.unpack("<3f", self.region(accessor["bufferView"], offset + i * stride, 12))
        if "sparse" in accessor:
            sparse = accessor["sparse"]; number = sparse["count"]; assert 0 <= number <= count
            indices = sparse["indices"]; widths = {5121: (1, "B"), 5123: (2, "H"), 5125: (4, "I")}
            width, code = widths[indices["componentType"]]
            previous = -1
            for i in range(number):
                target, = struct.unpack("<" + code, self.region(indices["bufferView"], indices.get("byteOffset", 0) + i * width, width))
                assert previous < target < count; previous = target
                values = sparse["values"]
                result[target] = struct.unpack("<3f", self.region(values["bufferView"], values.get("byteOffset", 0) + i * 12, 12))
        assert all(math.isfinite(value) for row in result for value in row)
        return result

    def targets(self, wanted):
        result = []
        for node_id, node in enumerate(self.doc["nodes"]):
            if "mesh" not in node: continue
            mesh_id = node["mesh"]; mesh = self.doc["meshes"][mesh_id]
            names = mesh.get("extras", {}).get("targetNames", [])
            weights = node.get("weights", mesh.get("weights", [0.0] * len(names)))
            assert len(weights) == len(names)
            for target_id, name in enumerate(names):
                if name not in wanted: continue
                primitives = []
                for p, primitive in enumerate(mesh["primitives"]):
                    assert len(primitive["targets"]) == len(names)
                    base = self.vec3(primitive["attributes"]["POSITION"])
                    target = primitive["targets"][target_id]
                    delta = self.vec3(target["POSITION"]) if "POSITION" in target else [(0.0, 0.0, 0.0)] * len(base)
                    assert len(delta) == len(base)
                    binary = b"".join(struct.pack("<3f", *row) for row in delta)
                    primitives.append({"primitive": p, "vertices": len(base), "position_accessor": primitive["attributes"]["POSITION"],
                        "target_position_accessor": target.get("POSITION"), "nonzero_delta_vertices": sum(any(value != 0 for value in row) for row in delta),
                        "maximum_abs_delta": max(abs(value) for row in delta for value in row), "decoded_delta_float32_sha256": hashlib.sha256(binary).hexdigest(),
                        "sparse": bool("POSITION" in target and "sparse" in self.doc["accessors"][target["POSITION"]])})
                result.append({"source_node": node_id, "node_name": node.get("name"), "mesh_index": mesh_id, "mesh_name": mesh.get("name"),
                    "target_index": target_id, "native_target_name": name, "target_count": len(names), "effective_declared_default": weights[target_id],
                    "declared_defaults_all_zero": all(value == 0 for value in weights), "primitives": primitives})
        return result

def main():
    TASK.mkdir(exist_ok=True)
    core_lock_path = ROOT / "output/sfm-native-main-rebind-20261113/conversion-inputs-core2.json"
    core_lock = json.loads(core_lock_path.read_bytes())
    families = json.loads(WIDER.read_bytes())["families"]
    inventory = json.loads(INVENTORY.read_bytes())["models"]
    keiki_native = next(row for row in inventory if row["sha256"] == "d8b32165bef2ec4f1c09acd19b3b136b3492b556fcfb9da98fb01826c5e279ff")
    mima = families["mima"]["models"]["mima_head"]
    sources = {"keiki_tools": CORE / "04-keiki_tools_chisels-groups-000/bundle/scene.glb",
        "keiki_no_tools": CORE / "10-keiki_tools_chisels-groups-100/bundle/scene.glb",
        "mima_head_historical": ROOT / "output/resume-mima-repro/prepared-head/scene.glb"}
    protected = {str(path): identity(path) for path in (WIDER, INVENTORY, core_lock_path, *sources.values())}
    cases = {}
    for name, path in sources.items():
        glb = GLB(path)
        report_path = path.with_name("parameters.json"); protected[str(report_path)] = identity(report_path)
        report = json.loads(report_path.read_bytes())
        wanted = {"ah 1", "ah 2", "EEEE"} if name.startswith("mima") else {"Tools"}
        targets = glb.targets(wanted)
        if name == "keiki_tools": assert len(targets) == 1 and targets[0]["source_node"] == 33 and targets[0]["target_index"] == 0
        if name == "keiki_no_tools": assert not targets
        if name.startswith("mima"): assert len(targets) == 3 and {r["source_node"] for r in targets} == {231}
        cases[name] = {"derived_glb": {"path": str(path), **glb.identity}, "parameters": {"path": str(report_path), **identity(report_path)},
            "derivation_context": "cf7main actual staticworker" if name.startswith("keiki") else "Historical retained native head preparation; not a fresh9f conversion",
            "targets": targets, "mesh_nodes": [{"node": i, "name": n.get("name"), "mesh": n["mesh"]} for i,n in enumerate(glb.doc["nodes"]) if "mesh" in n],
            "embedded_expression_group_count": len(glb.doc.get("asset", {}).get("extras", {}).get("studio_expression_groups", {}).get("entries", [])),
            "parameters_native_counts": {"bones": len(report["native_parameters"]["bones"]), "flex_names": len(report["native_parameters"]["flex_names"]), "controllers": len(report["native_parameters"]["flex_controllers"])}}
    keiki_source = next(row["source"] for row in core_lock["schedule"] if row["case"] == "keiki_tools_chisels")
    protected[keiki_source] = identity(Path(keiki_source)); protected[mima["source"]] = identity(Path(mima["source"]))
    assert protected[keiki_source]["sha256"] == keiki_native["sha256"]
    assert protected[mima["source"]]["sha256"] == mima["source_identity"]["sha256"]
    raw_native = {"keiki_tools": {"native_source": keiki_source, "native_identity": protected[keiki_source],
            "resource_root": next(row["resource_root"] for row in json.loads((ROOT / "output/sfm-native-main-rebind-20261113/CORE_FAMILIES.json").read_bytes())["families"].values() if row["source"] == keiki_source),
            "native_flex_names": keiki_native["flex_names"], "native_controllers": keiki_native["controllers"], "native_rules": keiki_native["flex_rules"],
            "material_closure": core_lock["native_closure"]["keiki_tools_chisels"]},
        "mima_head": {"native_source": mima["source"], "native_identity": protected[mima["source"]], "resource_root": mima["resource_root"],
            "native_flex_descriptor_count": len(mima["historical_full_native_metadata"]["flex_names"]), "native_controller_count": len(mima["historical_full_native_metadata"]["controllers"]),
            "selected_native_rules": [r for r in mima["historical_full_native_metadata"]["flex_rules"] if r["target"] in (100,101,139)],
            "selected_native_controllers": [r for r in mima["historical_full_native_metadata"]["controllers"] if r["index"] in (41,42,70)],
            "material_closure": mima["vmt_closure"], "fresh_current_main_head_conversion": "UNRUN"}}
    assert all(identity(Path(path)) == expected for path,expected in protected.items())
    result = {"format": "has_sfm_ordinary_shape_ui_next_inventory_1", "cases": cases, "native": raw_native, "inputs_before_after": protected,
        "scope": "Read-only exact retainednative/derived target inventory; no ordinaryUI/newconversion/SourceIO/runtime/GPU proof", "new_resources_staged": False}
    with (TASK / "TARGET_INVENTORY.json").open("x", encoding="utf-8") as stream: json.dump(result, stream, indent=2)
    print(json.dumps({"file": str(TASK / "TARGET_INVENTORY.json"), "cases": {name: [{"node": r["source_node"], "target": r["target_index"], "name": r["native_target_name"], "nonzero_delta_vertices": sum(p["nonzero_delta_vertices"] for p in r["primitives"])} for r in value["targets"]] for name,value in cases.items()}, "inputs_preserved": len(protected)}))

if __name__ == "__main__": main()
