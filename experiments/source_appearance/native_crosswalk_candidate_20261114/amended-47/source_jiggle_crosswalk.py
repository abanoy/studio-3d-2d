"""OUTPUT-ONLY restricted native/Blender/glTF proof; no product imports or writes.

Actual Blender5.1/SourceIO/Junko qualification is UNRUN. The caller supplies the
independently frozen selected-MDL SHA and source-file pins. Native rest, parent,
constructor-name and exporter-object identities are separate admission gates.
Nothing here edits a bone, node, model extras, native file, or solver setting.
"""
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import json
import math
import struct
import sys

JUNKO_SHA256 = "8da09c905227ddc8eef73a3f83594a4eb1c3a6d5304ee41ba5471bef834bc716"
SOURCEIO_PINS = {
    "blender_bindings/models/mdl44/import_mdl.py": "080b91589e0fec462e3eea4b55793aec41399ff95f6d9f2d561d5cda9dddada8",
    "blender_bindings/models/mdl49/import_mdl.py": "173a34ecae50e0b7a9d467908f238c02d5d7e19df3c7f52387534914d703233b",
    "library/models/mdl/v49/mdl_file.py": "a30f5fae981dedff47de4ce56152b876acd734bbb03e0df59ec9d320351f10ed",
    "library/models/mdl/structs/bone.py": "a61a3e0378e7b2d2d070f2b9ef138b78516db4a9830144cd6a6d907295b7d085",
}
EXPORTER_PINS = {
    "__init__.py": "dddd7d2362b937f34a5d4a1978259317720a9bc647bb3b4dc113f9d5c38cbf56",
    "blender/exp/joints.py": "af59a7d9bc077cdc945fe0a7ee3f14a053a087d0b30b5aacbd47902c5ca1d410",
    "blender/exp/nodes.py": "6c77f1ec3f13bd4636ca72f766429abc9cd4353ff218fdb088db1e41f184b7c3",
    "blender/exp/skins.py": "a78da3934beab9c6edbafe7dea2b3bcee36a7299e6064e12bf93d3243c09ca89",
    "blender/exp/tree.py": "3276867329b2ad11f4d0d2cede54e537c93cd9c0eb32a6c9386d22c548fe73eb",
    "blender/exp/exporter.py": "49c1e0174a65efd6d411b906cd154b6b04502c4840c9b31a7bfac87e0888f242",
    "blender/exp/export.py": "d6ae39bf861fc3db7662bc8e7063aadfbe116b8a5de81b40ba027a679f8435a8",
    "io/exp/user_extensions.py": "25d27cebbfce855dd5ac34928582ac5ab7f0e84d9a1d1862492ba3b82f523186",
    "io/exp/export.py": "3831bcad523bfe12bc970c0491203a06b2859a2c52df55a4bfcde570d832df6c",
    "io/com/gltf2_io.py": "d0bad0c89e40c0975ed9e435656151e353240134011f69602e473e0a5f1592f4",
}
IDENTITY = (1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1.)
REPORT_LIMIT = 128 * 1024


class CrosswalkError(ValueError): pass
class SourceIdentityError(CrosswalkError): pass
class UnsupportedScope(CrosswalkError): pass


@dataclass(frozen=True)
class Profile:
    native_sha256: str
    bone_count: int


JUNKO = Profile(JUNKO_SHA256, 69)


def require(condition, code):
    if not condition:
        raise CrosswalkError(code)


def compact(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def pointer(value):
    result = value.as_pointer()
    require(type(result) is int and result > 0, "unobservable_RNA_identity")
    return result


def matrix(value):
    values = tuple(float(value[r][c]) for r in range(4) for c in range(4))
    require(all(math.isfinite(v) and abs(v) <= 1e9 for v in values), "invalid_matrix")
    return values


def multiply(a, b):
    return tuple(sum(a[r*4+k] * b[k*4+c] for k in range(4)) for r in range(4) for c in range(4))


def close(a, b):
    return len(a) == len(b) and all(abs(x-y) <= 2e-5 * max(1., abs(y)) for x, y in zip(a, b))


def local_rest(position, quat, scale):
    # Independent row-major reference for SourceIO's XYZW -> WXYZ quaternion
    # and LocRotScale(position*scale, quaternion, unit scale) construction.
    x, y, z, w = quat
    norm = math.sqrt(sum(v*v for v in quat))
    require(abs(norm-1.) <= 1e-4, "nonunit_native_quaternion_outside_subset")
    x, y, z, w = (v/norm for v in (x, y, z, w))
    return (1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w), position[0]*scale,
            2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w), position[1]*scale,
            2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y), position[2]*scale,
            0., 0., 0., 1.)


def native_rest(raw, expected_native_mdl_sha256, profile=JUNKO):
    """Diagnostic-only independent MDL49 position/quaternion oracle.

    Offsets are pinned Bone.from_buffer: name0, parent4, controllers8..31,
    position32..43 and XYZW quaternion44..59. This is no metadata-parser port.
    """
    if type(raw) is not bytes or hashlib.sha256(raw).hexdigest() != expected_native_mdl_sha256:
        raise SourceIdentityError("frozen_native_identity_differs")
    if expected_native_mdl_sha256 != profile.native_sha256:
        raise UnsupportedScope("only_the_explicit_SHA_profile_is_admitted")
    require(408 <= len(raw) <= 16*1024*1024 and raw[:4] == b"IDST", "native_header")
    require(struct.unpack_from("<i", raw, 4)[0] == 49 and struct.unpack_from("<I", raw, 76)[0] == len(raw), "native_version_length")
    count, start = struct.unpack_from("<II", raw, 156)
    require(type(profile.bone_count) is int and 1 <= count == profile.bone_count <= 4096, "native_count")
    require(408 <= start <= len(raw)-count*216 and start % 4 == 0, "native_table")
    rows = []
    for index in range(count):
        at = start + index*216
        relative, parent = struct.unpack_from("<ii", raw, at)
        name_at = at+relative
        require(start+count*216 <= name_at < len(raw), "native_name_offset")
        end = raw.find(b"\0", name_at, min(len(raw), name_at+63))
        require(name_at < end < name_at+63, "native_constructor_key_length")
        try:
            name = raw[name_at:end].decode("ascii")
        except UnicodeError as error:
            raise UnsupportedScope("only_injective_short_ASCII_constructor_keys") from error
        values = struct.unpack_from("<7f", raw, at+32)
        require(all(math.isfinite(v) and abs(v) <= 1e6 for v in values), "native_rest_number")
        require(-1 <= parent < count and parent != index, "native_parent_domain")
        rows.append({"index": index, "name": name, "parent": parent,
                     "position": values[:3], "quat": values[3:],
                     "rest_words_uint32": struct.unpack_from("<7I", raw, at+32)})
    require(len({r["name"] for r in rows}) == count, "native_constructor_key_collision")
    for row in rows:
        visited = set(); current = row["index"]
        while current != -1:
            require(current not in visited, "native_parent_cycle")
            visited.add(current); current = rows[current]["parent"]
    return rows


@dataclass(frozen=True)
class BoundBone:
    native_index: int
    native_parent: int
    data_bone: object
    pose_bone: object
    data_pointer: int
    pose_pointer: int


@dataclass(frozen=True)
class NativeProof:
    raw: bytes
    native_sha256: str
    mdl: object
    armature: object
    scale: float
    profile: Profile
    source_pins: tuple
    bindings: tuple
    evidence_bytes: bytes

    def evidence(self):
        return json.loads(self.evidence_bytes)

    def recheck(self):
        value = prove_native_blender(self.raw, self.native_sha256, self.mdl, self.armature,
                                     self.scale, dict(self.source_pins), self.profile)
        require(value.evidence_bytes == self.evidence_bytes, "native_Blender_evidence_changed")
        require([(b.data_pointer, b.pose_pointer) for b in value.bindings] ==
                [(b.data_pointer, b.pose_pointer) for b in self.bindings], "native_Blender_identity_changed")


def prove_native_blender(raw, expected_native_mdl_sha256, mdl, armature, scale, observed_source_pins, profile=JUNKO):
    rows = native_rest(raw, expected_native_mdl_sha256, profile)
    require(observed_source_pins == SOURCEIO_PINS, "SourceIO_factory_or_reader_pin_differs")
    require(type(scale) in (int, float) and math.isfinite(scale) and 0 < scale <= 1e6, "source_scale")
    require(mdl.header.version == 49 and len(mdl.bones) == len(rows), "loaded_native_domain")
    require(armature.type == "ARMATURE" and armature.mode == "OBJECT", "armature_domain")
    owner = pointer(armature); data_owner = pointer(armature.data)
    require(close(matrix(armature.matrix_world), IDENTITY), "factory_armature_not_identity")
    expected_names = {r["name"] for r in rows}
    data_bones = list(armature.data.bones); pose_bones = list(armature.pose.bones)
    require(len(data_bones) == len(pose_bones) == len(rows), "complete_Blender_bijection_count")
    require({b.name for b in data_bones} == {b.name for b in pose_bones} == expected_names, "complete_constructor_key_bijection")
    native = {}
    for bone in mdl.bones:
        index = bone.bone_id
        require(type(index) is int and 0 <= index < len(rows) and index not in native, "loaded_native_index")
        row = rows[index]
        require(bone.name == row["name"] and type(bone.parent_id) is int and bone.parent_id == row["parent"], "loaded_native_name_parent")
        require(all(type(v) in (int, float) and math.isfinite(v) for v in (*bone.position, *bone.quat)), "loaded_native_rest_number_type")
        require(struct.pack("<7f", *bone.position, *bone.quat) == struct.pack("<7I", *row["rest_words_uint32"]), "loaded_native_rest_words")
        native[index] = bone
    require(set(native) == set(range(len(rows))), "loaded_native_complete_indices")
    # Lookups use exact constructor keys only inside this pinned, SHA-specific
    # fresh-armature/injective-name domain. No collection ordinal is a join.
    data = {r["index"]: armature.data.bones.get(r["name"]) for r in rows}
    pose = {r["index"]: armature.pose.bones.get(r["name"]) for r in rows}
    require(len({pointer(b) for b in data.values()}) == len(rows), "data_bone_pointer_collision")
    expected_global = {}
    def global_rest(index):
        if index not in expected_global:
            row = rows[index]; local = local_rest(row["position"], row["quat"], scale)
            expected_global[index] = local if row["parent"] == -1 else multiply(global_rest(row["parent"]), local)
        return expected_global[index]
    bindings = []; evidence_rows = []
    for row in rows:
        index = row["index"]; db = data[index]; pb = pose[index]
        require(pointer(db.id_data) == data_owner and pointer(pb.id_data) == owner, "bone_owner_mismatch")
        require(pointer(pb.bone) == pointer(db), "PoseBone_dataBone_pointer_mismatch")
        expected_parent = row["parent"]
        require((db.parent is None and expected_parent == -1) or
                (db.parent is not None and expected_parent >= 0 and pointer(db.parent) == pointer(data[expected_parent])), "Blender_native_parent_pointer_mismatch")
        require((pb.parent is None and expected_parent == -1) or
                (pb.parent is not None and expected_parent >= 0 and pointer(pb.parent) == pointer(pose[expected_parent])), "PoseBone_parent_pointer_mismatch")
        expected = global_rest(index); actual = matrix(db.matrix_local)
        require(close(actual, expected), "native_Blender_rest_matrix_mismatch")
        require(close(matrix(pb.matrix), actual), "PoseBone_not_in_factory_rest")
        bindings.append(BoundBone(index, expected_parent, db, pb, pointer(db), pointer(pb)))
        evidence_rows.append({"native_index": index, "native_name": row["name"], "native_parent_index": expected_parent,
                              "native_rest_words_uint32": row["rest_words_uint32"],
                              "actual_Blender_bone_name": db.name, "Blender_matrix_local_row_major": actual,
                              "maximum_reference_matrix_error": max(abs(x-y) for x, y in zip(actual, expected))})
    evidence = {"format": "has_source_native_Blender_proof_draft_1", "native_mdl_sha256": expected_native_mdl_sha256,
                "native_bone_count": len(rows), "source_scale": float(scale), "applied": False,
                "constructor_domain": "SHA_and_factory_pinned_complete_injective_short_ASCII_keys",
                "sourceio_source_sha256": dict(observed_source_pins), "bones": evidence_rows,
                "scope": "Observed identity,parent,rest proof only; no Source-rule semantics or simulation"}
    return NativeProof(raw, expected_native_mdl_sha256, mdl, armature, float(scale), profile,
                       tuple(sorted(observed_source_pins.items())), tuple(bindings), compact(evidence))


def unique_identity_index(values, target):
    matches = [i for i, value in enumerate(values) if value is target]
    require(len(matches) == 1, "export_object_identity_missing_or_duplicated")
    return matches[0]


def node_dict(node):
    require(getattr(node, "extras", None) is None, "joint_or_object_extras_must_stay_disabled")
    keys = ("camera", "children", "extensions", "matrix", "mesh", "name", "rotation", "scale", "skin", "translation", "weights")
    return {k: getattr(node, k) for k in keys if getattr(node, k, None) not in (None, [], {})}


def skin_dict(skin):
    require(getattr(skin, "extras", None) is None, "skin_extras_must_stay_disabled")
    pairs = [("inverseBindMatrices", "inverse_bind_matrices"), ("joints", "joints"), ("name", "name"),
             ("skeleton", "skeleton"), ("extensions", "extensions")]
    return {key: getattr(skin, attr) for key, attr in pairs if getattr(skin, attr, None) not in (None, [], {})}


def scene_dict(scene):
    require(getattr(scene, "extras", None) is None, "scene_extras_must_stay_disabled")
    require(scene.nodes is None or type(scene.nodes) is list, "scene_root_list_domain")
    return {key: getattr(scene, key) for key in ("name", "nodes", "extensions")
            if getattr(scene, key, None) not in (None, [], {})}


def pruned_mesh_json(value):
    # The pinned exporter preserves extras as a complete value; other empty
    # fields are pruned recursively (KHR_materials_unlit is the admitted empty
    # extension exception). Integral-float normalization preserves JSON value.
    if type(value) is dict:
        result = {}
        for key, item in value.items():
            if key == "extras" and item is not None:
                result[key] = json.loads(compact(item))
            elif item is not None and (item not in ([], {}) or key == "KHR_materials_unlit"):
                result[key] = pruned_mesh_json(item)
        return result
    if type(value) is list:
        return [pruned_mesh_json(item) for item in value]
    if type(value) is float and math.isfinite(value) and value.is_integer():
        return int(value)
    return value


def mesh_dict(mesh):
    # Actual use of the pinned Mesh.to_dict implementation remains a runtime
    # qualification target. CPU controls supply an authored plain Mesh mock.
    value = mesh.to_dict()
    require(type(value) is dict, "flat_mesh_JSON_domain")
    require(type(value.get("primitives")) is list and 0 < len(value["primitives"]) <= 100000 and
            all(type(p) is dict for p in value["primitives"]), "mesh_primitive_domain")
    return emitted_json(value)


def emitted_json(value):
    # Pinned blender/exp/export.py invokes __fix_json twice. Do not turn this
    # into arbitrary fixed-point pruning or leave a one-pass outer empty dict.
    return pruned_mesh_json(pruned_mesh_json(value))


def scene_graph(selected, scenes, nodes):
    require(type(scenes) is list and 1 <= len(scenes) <= 128 and
            type(nodes) is list and 0 < len(nodes) <= 100000, "scene_node_domain")
    require(type(selected) is int and 0 <= selected < len(scenes), "selected_scene_domain")
    parents = {}; children = []
    for index, node in enumerate(nodes):
        require(type(node) is dict, "node_JSON_domain")
        values = node.get("children", [])
        require(type(values) is list, "node_children_domain")
        for child in values:
            require(type(child) is int and 0 <= child < len(nodes) and child not in parents,
                    "exported_parent_domain")
            parents[child] = index
        children.append(values)
    # Inspect every component, including unreachable nodes, without recursion.
    colors = [0] * len(nodes)
    for first in range(len(nodes)):
        if colors[first]: continue
        pending = [(first, False)]
        while pending:
            index, leaving = pending.pop()
            if leaving:
                colors[index] = 2
                continue
            require(colors[index] != 1, "exported_node_cycle")
            if colors[index] == 2: continue
            colors[index] = 1; pending.append((index, True))
            pending.extend((child, False) for child in children[index])
    all_roots = []
    for scene in scenes:
        require(type(scene) is dict, "scene_JSON_domain")
        roots = scene.get("nodes", [])
        require(type(roots) is list and all(type(i) is int and 0 <= i < len(nodes) for i in roots),
                "scene_root_domain")
        require(len(roots) == len(set(roots)) and all(i not in parents for i in roots), "scene_root_parent_or_duplicate")
        all_roots.append(roots)
    reachable = set(); pending = list(all_roots[selected])
    while pending:
        index = pending.pop()
        if index in reachable: continue
        reachable.add(index); pending.extend(children[index])
    return reachable, parents


def final_glb_json(raw):
    require(type(raw) is bytes and 20 <= len(raw) <= 128*1024*1024, "final_GLB_size")
    require(raw[:4] == b"glTF" and struct.unpack_from("<II", raw, 4) == (2, len(raw)), "final_GLB_header")
    offset = 12; kinds = []; value = None
    while offset < len(raw):
        require(offset+8 <= len(raw), "incomplete_GLB_chunk_header")
        size, kind = struct.unpack_from("<II", raw, offset)
        require(size % 4 == 0 and size <= len(raw)-offset-8, "GLB_chunk_alignment_or_bounds")
        start = offset+8; end = start+size
        if not kinds:
            require(kind == 0x4e4f534a and 0 < size <= 16*1024*1024, "first_GLB_chunk_must_be_JSON")
            value = json.loads(raw[start:end].decode("utf-8"))
            require(type(value) is dict, "GLB_JSON_object_required")
        else:
            require(len(kinds) == 1 and kind == 0x004e4942, "only_one_optional_BIN_chunk_is_admitted")
        kinds.append(kind); offset = end
    require(offset == len(raw) and kinds, "GLB_exact_EOF_required")
    return value


class ExportCollector:
    """Three identity hooks plus preflight; errors latch as Blender swallows hooks.

    finish(final_glb_bytes) MUST run after bpy export returns and after any owned
    GLB postprocessing, before optional report publication. No partial proof.
    """
    def __init__(self, proof, observed_exporter_pins):
        require(observed_exporter_pins == EXPORTER_PINS, "exporter_source_pin_differs")
        proof.recheck(); self.proof = proof
        self.owner = pointer(proof.armature)
        self.by_data = {b.data_pointer: b for b in proof.bindings}
        self.nodes = {}; self.skins = []; self.failure = None; self.final = None; self.preflight_seen = False

    def _hook(self, stage, action):
        if self.failure is not None: return
        try:
            action()
        except Exception as error:
            self.failure = (stage, type(error).__name__, str(error) if isinstance(error, CrosswalkError) else "host_attribute_failure")

    def pre_export_hook(self, export_settings):
        def admit():
            require(not self.preflight_seen, "multiple_export_preflight_calls")
            extensions = export_settings.get("gltf_user_extensions")
            require(type(extensions) is list and len(extensions) == 1 and extensions[0] is self, "uncontrolled_export_extensions")
            for key in ("pre_export_callbacks", "post_export_callbacks"):
                require(type(export_settings.get(key)) is list and not export_settings[key], "uncontrolled_"+key)
            self.proof.recheck(); self.preflight_seen = True
        self._hook("preflight", admit)

    def gather_joint_hook(self, node, blender_bone, export_settings):
        def collect():
            data_pointer = pointer(blender_bone.bone)
            if data_pointer not in self.by_data: return
            binding = self.by_data[data_pointer]
            require(pointer(blender_bone.id_data) == self.owner and pointer(blender_bone) == binding.pose_pointer, "export_PoseBone_owner_or_identity_differs")
            previous = self.nodes.get(binding.native_index)
            require(previous is None or previous is node, "one_native_bone_emitted_as_multiple_nodes")
            self.nodes[binding.native_index] = node
        self._hook("joint", collect)

    def gather_skin_hook(self, skin, blender_armature_object, export_settings):
        def collect():
            if pointer(blender_armature_object) != self.owner: return
            if not any(value is skin for value in self.skins): self.skins.append(skin)
        self._hook("skin", collect)

    def gather_gltf_extensions_hook(self, gltf, export_settings):
        def collect():
            require(self.final is None, "multiple_final_export_hook_calls")
            require(self.preflight_seen, "export_preflight_not_observed")
            self.proof.recheck()
            extensions = export_settings.get("gltf_user_extensions")
            require(type(extensions) is list and len(extensions) == 1 and extensions[0] is self, "uncontrolled_export_extensions")
            for key in ("pre_export_callbacks", "post_export_callbacks"):
                require(type(export_settings.get(key)) is list and not export_settings[key], "uncontrolled_"+key)
            for key, expected in {"gltf_extras": False, "gltf_skins": True, "gltf_yup": True,
                                  "gltf_animations": False, "gltf_armature_object_remove": False,
                                  "gltf_rest_position_armature": True,
                                  "gltf_flatten_bones_hierarchy": False, "gltf_flatten_obj_hierarchy": False,
                                  "gltf_leaf_bone": False, "gltf_gpu_instances": False,
                                  "gltf_use_gltfpack": False, "gltf_draco_mesh_compression": False}.items():
                require(export_settings.get(key) is expected, "unsupported_export_setting_"+key)
            nodes_snapshot = json.loads(compact(emitted_json([node_dict(n) for n in gltf.nodes])))
            scenes_snapshot = json.loads(compact(emitted_json([scene_dict(s) for s in gltf.scenes])))
            reachable, parents = scene_graph(gltf.scene, scenes_snapshot, nodes_snapshot)
            require(type(gltf.meshes) is list and len(gltf.meshes) <= 100000, "flat_mesh_list_domain")
            meshes_snapshot = json.loads(compact([mesh_dict(m) for m in gltf.meshes]))
            for node in nodes_snapshot:
                if "mesh" in node:
                    require(type(node["mesh"]) is int and 0 <= node["mesh"] < len(meshes_snapshot), "node_mesh_reference_domain")
            require(set(self.nodes) == {b.native_index for b in self.proof.bindings}, "incomplete_joint_hooks")
            node_indices = {native: unique_identity_index(gltf.nodes, node) for native, node in self.nodes.items()}
            require(len(set(node_indices.values())) == len(node_indices), "native_nodes_alias")
            owner_nodes = [value.node for value in export_settings["vtree"].nodes.values()
                           if value.blender_bone is None and value.blender_object is not None and
                           pointer(value.blender_object) == self.owner]
            require(len(owner_nodes) == 1, "unique_exported_armature_object_required")
            owner_node = unique_identity_index(gltf.nodes, owner_nodes[0])
            require(owner_node in reachable and set(node_indices.values()).issubset(reachable), "native_armature_or_joints_unreachable_in_selected_scene")
            for binding in self.proof.bindings:
                expected_parent = owner_node if binding.native_parent == -1 else node_indices[binding.native_parent]
                require(parents.get(node_indices[binding.native_index]) == expected_parent, "exported_native_parent_differs")
            require(0 < len(self.skins) <= 128, "missing_or_excessive_target_skins")
            memberships = {native: [] for native in node_indices}; skin_mesh_nodes = []
            for skin in self.skins:
                skin_index = unique_identity_index(gltf.skins, skin)
                require(type(skin.joints) is list and all(type(i) is int for i in skin.joints) and
                        len(skin.joints) == len(set(skin.joints)) and set(skin.joints) == set(node_indices.values()), "skin_joint_domain_differs")
                mesh_nodes = [index for index, node in enumerate(nodes_snapshot)
                              if index in reachable and type(node.get("skin")) is int and node["skin"] == skin_index and "mesh" in node]
                require(mesh_nodes, "target_skin_has_no_reachable_exported_mesh")
                for mesh_node in mesh_nodes:
                    mesh = meshes_snapshot[nodes_snapshot[mesh_node]["mesh"]]
                    for primitive in mesh["primitives"]:
                        attributes = primitive.get("attributes")
                        require(type(attributes) is dict and all(type(attributes.get(key)) is int and attributes[key] >= 0
                                for key in ("POSITION", "JOINTS_0", "WEIGHTS_0")), "target_mesh_skin_attribute_domain")
                skin_mesh_nodes.append({"skin_index": skin_index, "reachable_skinned_mesh_nodes": mesh_nodes})
                for native, node_index in node_indices.items():
                    memberships[native].append({"skin_index": skin_index, "joint_slot": skin.joints.index(node_index)})
            self.final = {"nodes": nodes_snapshot, "scene": gltf.scene, "scenes": scenes_snapshot,
                          "meshes": meshes_snapshot, "skin_mesh_nodes": skin_mesh_nodes,
                          "skins": json.loads(compact(emitted_json([skin_dict(s) for s in gltf.skins]))),
                          "armature_node_index": owner_node, "node_indices": node_indices, "memberships": memberships}
        self._hook("final", collect)

    def finish(self, final_glb):
        require(self.failure is None, "latched_export_hook_failure_"+repr(self.failure))
        require(self.final is not None, "final_export_hook_missing")
        self.proof.recheck()
        value = final_glb_json(final_glb)
        scene_graph(value.get("scene"), value.get("scenes"), value.get("nodes"))
        require(value.get("scene") == self.final["scene"] and compact(value.get("scenes")) == compact(self.final["scenes"]), "final_GLB_scene_reconciliation_failed")
        require(compact(value.get("nodes")) == compact(self.final["nodes"]) and compact(value.get("skins")) == compact(self.final["skins"]), "final_GLB_node_skin_reconciliation_failed")
        require(compact(value.get("meshes")) == compact(self.final["meshes"]), "final_GLB_mesh_reconciliation_failed")
        proof = self.proof.evidence()
        for row in proof["bones"]:
            index = row["native_index"]
            row["gltf_node_index"] = self.final["node_indices"][index]
            row["skin_memberships"] = self.final["memberships"][index]
        proof.update(format="has_source_export_crosswalk_draft_1", status="observed_inactive",
                     glb_sha256=hashlib.sha256(final_glb).hexdigest(), glb_bytes=len(final_glb),
                     armature_gltf_node_index=self.final["armature_node_index"],
                     selected_scene=self.final["scene"],
                     selected_scene_roots=self.final["scenes"][self.final["scene"]].get("nodes", []),
                     scene_container_sha256=hashlib.sha256(compact({"scene": self.final["scene"], "scenes": self.final["scenes"]})).hexdigest(),
                     target_skin_mesh_nodes=self.final["skin_mesh_nodes"],
                     exporter_source_sha256=dict(EXPORTER_PINS), export_extras=False,
                     HAS_runtime_binding="unattempted", native_simulation=False)
        encoded = compact(proof)
        require(len(encoded) <= REPORT_LIMIT, "complete_crosswalk_report_budget_exceeded")
        return proof


@contextmanager
def temporary_export_extension(exporter_module, enabled_addon_names, collector):
    """Scoped runtime-only registration through the exporter's addon discovery.

    Caller must verify this is the pinned loaded io_scene_gltf2 module. No addon
    enabling, preferences save, installed-file change or function replacement.
    """
    require(exporter_module.__name__ in enabled_addon_names and sys.modules.get(exporter_module.__name__) is exporter_module, "exporter_addon_not_observably_loaded")
    require(not hasattr(exporter_module, "glTF2ExportUserExtension") and
            not hasattr(exporter_module, "glTF2ExportUserExtensions"), "existing_export_extension_registration")
    constructor = lambda: collector
    exporter_module.glTF2ExportUserExtension = constructor
    try:
        yield
    finally:
        require(getattr(exporter_module, "glTF2ExportUserExtension", None) is constructor, "export_registration_owner_changed")
        del exporter_module.glTF2ExportUserExtension
