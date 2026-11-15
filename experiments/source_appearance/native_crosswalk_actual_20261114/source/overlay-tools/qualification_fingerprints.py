import hashlib,json
import secondary_helpers as H
import stage_resources as S

def glb_structure(path, active_names, native):
    S.no_reparse(path)
    glb = H.GLB(path)
    doc = glb.doc
    S.require(not doc.get("animations") and not doc.get("cameras"), "Static conversion unexpectedly exports animation/cameras")
    nodes = doc.get("nodes", [])
    mesh_nodes = [node for node in nodes if "mesh" in node]
    S.require(sorted(node.get("name", "") for node in mesh_nodes) == sorted(active_names), "GLB selected mesh-node membership differs")
    parents = {}
    for parent, node in enumerate(nodes):
        for child in node.get("children", []):
            H.integer(child, len(nodes)); S.require(child not in parents, "GLB multiple node parents")
            parents[child] = parent
    native_names = {bone["name"] for bone in native["bones"]}
    joints_by_name = {}
    used_skins = {H.integer(node.get("skin"), len(doc.get("skins", []))) for node in mesh_nodes}
    for skin_index in sorted(used_skins):
        skin = doc["skins"][skin_index]
        joints = skin.get("joints", [])
        S.require(joints and len(set(joints)) == len(joints), "Invalid GLB joint list")
        binds = glb.accessor(skin["inverseBindMatrices"], "MAT4", maximum=4096)
        S.require(len(binds) == len(joints), "GLB inverse-bind count differs")
        for joint in joints:
            H.integer(joint, len(nodes))
            name = nodes[joint].get("name", "")
            S.require(name not in joints_by_name or joints_by_name[name] == joint, "Ambiguous GLB native joint names")
            joints_by_name[name] = joint
    S.require(native_names <= set(joints_by_name), "GLB lost native joint bindings")
    for bone in native["bones"]:
        node = joints_by_name[bone["name"]]
        visited = set()
        parent = parents.get(node)
        while parent is not None and nodes[parent].get("name") not in native_names:
            S.require(parent not in visited, "GLB parent cycle")
            visited.add(parent); parent = parents.get(parent)
        expected = native["bones"][bone["parent"]]["name"] if bone["parent"] >= 0 else None
        S.require((nodes[parent].get("name") if parent is not None else None) == expected, "GLB native parent hierarchy differs")
    for image in doc.get("images", []):
        S.require("uri" not in image and type(image.get("bufferView")) is int, "Expected embedded GLB image buffer")
        H.integer(image["bufferView"], len(doc.get("bufferViews", [])))
    def local_transform(node):
        if "matrix" in node:
            S.require(not any(key in node for key in ["translation", "rotation", "scale"])
                      and isinstance(node["matrix"], list) and len(node["matrix"]) == 16, "Invalid GLB matrix/TRS transform")
            return {"matrix": [H.finite(value) for value in node["matrix"]]}
        result = {}
        for key, default in [("translation", [0., 0., 0.]), ("rotation", [0., 0., 0., 1.]), ("scale", [1., 1., 1.])]:
            value = node.get(key, default)
            S.require(isinstance(value, list) and len(value) == len(default), "Invalid GLB rest transform")
            result[key] = [H.finite(component) for component in value]
        return result
    def chain(index):
        result, visited = [], set()
        while index is not None:
            S.require(index not in visited, "GLB rest-transform parent cycle")
            visited.add(index)
            node = nodes[index]
            result.append({"name": node.get("name", ""), "local_transform": local_transform(node)})
            index = parents.get(index)
        return result
    meshes, used_materials = [], set()
    for node in mesh_nodes:
        mesh = glb.ref("meshes", node["mesh"])
        S.require(type(node.get("skin")) is int, "Selected native mesh lost its skin")
        skin = glb.ref("skins", node["skin"])
        target_count = len(mesh.get("primitives", [{}])[0].get("targets", []))
        defaults = node.get("weights", mesh.get("weights", [0.] * target_count))
        S.require(isinstance(defaults, list) and len(defaults) == target_count, "GLB default morph-weight count differs")
        deformation = {"mesh_rest_chain": chain(nodes.index(node)),
                       "ordered_joints": [{"name": nodes[joint].get("name", ""), "rest_chain": chain(joint)} for joint in skin["joints"]],
                       "inverse_bind_matrices": glb.accessor(skin["inverseBindMatrices"], "MAT4", maximum=4096),
                       "effective_default_morph_weights": [H.finite(value) for value in defaults]}
        primitives = []
        for primitive in mesh.get("primitives", []):
            S.require(primitive.get("mode", 4) == 4, "Expected triangle primitive")
            attrs = primitive["attributes"]
            S.require({"POSITION", "JOINTS_0", "WEIGHTS_0"} <= set(attrs) and not ({"JOINTS_1", "WEIGHTS_1"} & set(attrs)), "Unsupported/missing native skin attributes")
            positions = glb.accessor(attrs["POSITION"], "VEC3")
            joints = glb.accessor(attrs["JOINTS_0"], "VEC4")
            weights = glb.accessor(attrs["WEIGHTS_0"], "VEC4")
            S.require(len(joints) == len(weights) == len(positions), "GLB skin attribute count differs")
            S.require(all(all(type(value) is int and 0 <= value < len(skin["joints"]) for value in row) for row in joints), "GLB vertex joint out of range")
            S.require(all(all(0 <= value <= 1 for value in row) and abs(sum(row) - 1) <= 1e-4 for row in weights), "GLB weights not normalized")
            indices = glb.accessor(primitive["indices"], "SCALAR", maximum=600000)
            S.require(len(indices) % 3 == 0 and all(type(row[0]) is int and 0 <= row[0] < len(positions) for row in indices), "GLB triangle indices out of range")
            decoded = {name: glb.accessor(index) for name, index in attrs.items()}
            S.require(all(len(values) == len(positions) for values in decoded.values()), "GLB vertex attribute count differs")
            morphs = []
            for target in primitive.get("targets", []):
                S.require(set(target) <= {"POSITION", "NORMAL", "TANGENT"}, "Unsupported morph semantic")
                morphs.append({name: glb.morph_delta(index, len(positions)) for name, index in target.items()})
            names = mesh.get("extras", {}).get("targetNames", [])
            S.require(len(names) == len(morphs) == target_count, "GLB target names/count differ")
            signature = hashlib.sha256(json.dumps({"attributes": decoded, "indices": indices, "morphs": morphs,
                                                    "target_names": names, "binding_rest_morph_defaults": deformation},
                                                   sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
            material = H.integer(primitive["material"], len(doc.get("materials", [])))
            used_materials.add(material)
            primitives.append({"vertices": len(positions), "indices": len(indices), "target_names": names,
                               "geometry_skin_morph_sha256": signature, "material": material,
                               "nonzero_position_morph_vertices": [sum(any(abs(value) > 1e-12 for value in delta) for delta in target.get("POSITION", [])) for target in morphs]})
        S.require(primitives, "Empty GLB mesh")
        meshes.append({"node": node["name"], "primitives": primitives, "binding_rest_morph_defaults": deformation})
    S.require(meshes and used_materials, "No GLB renderable mesh/material")
    active_materials = []
    for index in sorted(used_materials):
        material = doc["materials"][index]
        texture = material.get("pbrMetallicRoughness", {}).get("baseColorTexture", {})
        texture_row = glb.ref("textures", texture.get("index"))
        image = glb.ref("images", texture_row.get("source"))
        view = glb.ref("bufferViews", image["bufferView"])
        start, count = view.get("byteOffset", 0), view["byteLength"]
        active_materials.append({"index": index, "name": material.get("name", ""), "embedded_base_image_sha256": hashlib.sha256(glb.binary[start:start + count]).hexdigest()})
    return {"sha256": glb.sha, "bytes": len(glb.raw), "meshes": meshes, "native_joint_names_bound": sorted(native_names), "active_materials": active_materials,
            "scope": "Embedded GLB structure, decoded geometry/skin/morph fingerprints and native names/parents; no independent native vertex/material/deformation/render equivalence."}
