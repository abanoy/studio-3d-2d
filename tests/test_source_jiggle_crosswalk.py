"""Authored byte/RNA/exporter mocks only; never import Blender or SourceIO."""
import copy
from dataclasses import replace
import hashlib
import itertools
import json
import math
from pathlib import Path
import struct
import sys
from types import ModuleType, SimpleNamespace as NS
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import source_jiggle_crosswalk as M


class RNA:
    sequence = itertools.count(100)
    def __init__(self, **fields): self.__dict__.update(fields); self.identity = next(self.sequence)
    def as_pointer(self): return self.identity


class Collection:
    def __init__(self, values): self.values = list(values)
    def __iter__(self): return iter(self.values)
    def __len__(self): return len(self.values)
    def get(self, name):
        found = [value for value in self.values if value.name == name]
        return found[0] if len(found) == 1 else None


def authored(names=("Root+(Anchor)", "FrontHair1", "SecondHair")):
    parents = (-1, 0, 1)
    half = struct.unpack("<f", struct.pack("<f", math.sqrt(.5)))[0]
    positions = ((1., 2., 3.), (0., 4., 0.), (0., 0., 2.))
    quats = ((0., 0., 0., 1.), (0., 0., half, half), (half, 0., 0., half))
    start = 408; names_at = start+3*216
    raw = bytearray(names_at + sum(len(name.encode())+1 for name in names))
    raw[:4] = b"IDST"; struct.pack_into("<i", raw, 4, 49)
    struct.pack_into("<I", raw, 76, len(raw)); struct.pack_into("<II", raw, 156, 3, start)
    cursor = names_at
    for index in range(3):
        at = start+216*index; encoded = names[index].encode()
        struct.pack_into("<ii", raw, at, cursor-at, parents[index])
        struct.pack_into("<7f", raw, at+32, *positions[index], *quats[index])
        raw[cursor:cursor+len(encoded)+1] = encoded+b"\0"; cursor += len(encoded)+1
    return bytes(raw), positions, quats, parents


def nested(flat): return [list(flat[i:i+4]) for i in range(0, 16, 4)]


def host_fixture(scale=.1):
    raw, positions, quats, parents = authored()
    armature = RNA(type="ARMATURE", mode="OBJECT", matrix_world=nested(M.IDENTITY))
    armature.data = RNA(); armature.pose = NS()
    # Independent hand-calculated world-rest matrices: Rz90 then Rx90.
    matrices = [
        (1,0,0,scale, 0,1,0,2*scale, 0,0,1,3*scale, 0,0,0,1),
        (0,-1,0,scale, 1,0,0,6*scale, 0,0,1,3*scale, 0,0,0,1),
        (0,0,1,scale, 1,0,0,6*scale, 0,1,0,5*scale, 0,0,0,1)]
    data = []; pose = []
    names = ("Root+(Anchor)", "FrontHair1", "SecondHair")
    for index, name in enumerate(names):
        data.append(RNA(name=name, id_data=armature.data, matrix_local=nested(matrices[index]),
                        parent=None if index == 0 else data[parents[index]]))
        pose.append(RNA(name=name, id_data=armature, bone=data[-1], matrix=nested(matrices[index]),
                        parent=None if index == 0 else pose[parents[index]]))
    # Both Blender collections and loaded SourceIO objects deliberately differ
    # from native order. Native bone_id and exact constructor keys drive proof.
    armature.data.bones = Collection([data[2], data[0], data[1]])
    armature.pose.bones = Collection([pose[1], pose[2], pose[0]])
    mdl_bones = [NS(bone_id=i, name=names[i], parent_id=parents[i], position=positions[i], quat=quats[i]) for i in range(3)]
    mdl = NS(header=NS(version=49), bones=[mdl_bones[2], mdl_bones[0], mdl_bones[1]])
    sha = hashlib.sha256(raw).hexdigest()
    return NS(raw=raw, sha=sha, profile=M.Profile(sha, 3), mdl=mdl, armature=armature, data=data, pose=pose, scale=scale)


def prove(value):
    return M.prove_native_blender(value.raw, value.sha, value.mdl, value.armature, value.scale, dict(M.SOURCEIO_PINS), value.profile)


class Node(NS):
    # Equality is deliberately useless: collector joins must use identity.
    def __eq__(self, other): return True


class Mesh:
    def __init__(self, value=None):
        self.value = value if value is not None else {"name": "authored skinned mesh", "primitives": [
            {"attributes": {"POSITION": 0, "JOINTS_0": 1, "WEIGHTS_0": 2}, "mode": 4}]}
    def to_dict(self): return copy.deepcopy(self.value)


def node(**kwargs):
    values = dict(camera=None, children=[], extensions=None, extras=None, matrix=None, mesh=None,
                  name="same label", rotation=None, scale=None, skin=None, translation=None, weights=None)
    values.update(kwargs); return Node(**values)


def export_fixture(proof):
    # Final node order: mesh, native2, armature object, native0, native1.
    nodes = [node(mesh=0, skin=0), node(), node(children=[3]), node(children=[4]), node(children=[1])]
    skin = NS(extras=None, inverse_bind_matrices=0, joints=[nodes[1], nodes[3], nodes[4]],
              name="same label", skeleton=None, extensions=None)
    settings = {"gltf_user_extensions": None, "gltf_extras": False, "gltf_skins": True, "gltf_yup": True,
                "gltf_animations": False, "gltf_armature_object_remove": False, "gltf_rest_position_armature": True,
                "gltf_flatten_bones_hierarchy": False, "gltf_flatten_obj_hierarchy": False,
                "gltf_leaf_bone": False, "gltf_gpu_instances": False, "gltf_use_gltfpack": False,
                "gltf_draco_mesh_compression": False, "pre_export_callbacks": [], "post_export_callbacks": [],
                "vtree": NS(nodes={"owner": NS(node=nodes[2], blender_bone=None, blender_object=proof.armature)})}
    gltf = NS(nodes=nodes, skins=[skin], scene=0,
              scenes=[NS(name="selected", nodes=[2,0], extensions=None, extras=None)], meshes=[Mesh()])
    collector = M.ExportCollector(proof, dict(M.EXPORTER_PINS)); settings["gltf_user_extensions"] = [collector]
    return NS(nodes=nodes, skin=skin, settings=settings, gltf=gltf, collector=collector)


def begin_export(value, proof):
    value.collector.pre_export_hook(value.settings)
    for native, node_index in ((2, 1), (0, 3), (1, 4)):
        value.collector.gather_joint_hook(value.nodes[node_index], proof.bindings[native].pose_bone, value.settings)
    value.collector.gather_skin_hook(value.skin, proof.armature, value.settings)


def final_hook(value):
    value.skin.joints = [1, 3, 4]  # Real traversal replaces object refs with numbers.
    value.collector.gather_gltf_extensions_hook(value.gltf, value.settings)


def glb(value, change=None):
    data = M.emitted_json({"asset": {"version": "2.0"}, "nodes": [M.node_dict(n) for n in value.gltf.nodes],
            "skins": [M.skin_dict(s) for s in value.gltf.skins], "scene": value.gltf.scene,
            "scenes": [M.scene_dict(s) for s in value.gltf.scenes], "meshes": [m.to_dict() for m in value.gltf.meshes]})
    if change: change(data)
    encoded = json.dumps(data, allow_nan=False, separators=(",", ":")).encode()
    encoded += b" "*((-len(encoded)) % 4)
    return struct.pack("<4sIIII", b"glTF", 2, 20+len(encoded), len(encoded), 0x4e4f534a)+encoded


class CrosswalkTests(unittest.TestCase):
    def setUp(self): self.value = host_fixture()
    def export(self):
        proof = prove(self.value); value = export_fixture(proof); begin_export(value, proof); final_hook(value)
        return proof, value

    def test_complete_factory_bijection_ignores_collection_ordinals(self):
        proof = prove(self.value); evidence = proof.evidence()
        self.assertEqual([b.native_index for b in proof.bindings], [0,1,2])
        self.assertEqual([b.data_bone for b in proof.bindings], self.value.data)
        self.assertTrue(all(row["maximum_reference_matrix_error"] < 1e-6 for row in evidence["bones"]))
        self.assertFalse(evidence["applied"]); proof.recheck()

    def test_default_profile_never_accepts_authored_bytes_as_Junko(self):
        with self.assertRaises(M.UnsupportedScope):
            M.native_rest(self.value.raw, self.value.sha)

    def test_wrong_frozen_native_sha_precedes_profile_fallback(self):
        with self.assertRaises(M.SourceIdentityError):
            M.native_rest(self.value.raw, "0"*64)
        with self.assertRaises(M.SourceIdentityError):
            M.native_rest(bytearray(self.value.raw), self.value.sha, self.value.profile)

    def test_factory_or_reader_pin_changes_refuse(self):
        for key in M.SOURCEIO_PINS:
            pins = dict(M.SOURCEIO_PINS); pins[key] = "0"*64
            with self.assertRaises(M.CrosswalkError):
                M.prove_native_blender(self.value.raw, self.value.sha, self.value.mdl, self.value.armature, .1, pins, self.value.profile)

    def test_native_name_collision_or_truncation_refuses(self):
        for names in (("same", "same", "other"), ("a"*63, "short", "other"), ("nonascii\u00e9", "short", "other")):
            raw, *_ = authored(names); sha = hashlib.sha256(raw).hexdigest()
            with self.assertRaises(M.CrosswalkError): M.native_rest(raw, sha, M.Profile(sha,3))

    def test_native_parent_cycles_and_bad_indices_refuse(self):
        for parent in (2, 3, -2):
            raw = bytearray(self.value.raw); struct.pack_into("<i", raw, 408+4, parent)
            raw = bytes(raw); sha = hashlib.sha256(raw).hexdigest()
            with self.assertRaises(M.CrosswalkError): M.native_rest(raw, sha, M.Profile(sha,3))

    def test_nonfinite_native_rest_and_nonunit_quaternion_refuse(self):
        for offset, value in ((32, float("nan")), (44, 10.)):
            raw = bytearray(self.value.raw); struct.pack_into("<f", raw, 408+offset, value)
            raw = bytes(raw); sha = hashlib.sha256(raw).hexdigest()
            if math.isnan(value):
                with self.assertRaises(M.CrosswalkError): M.native_rest(raw, sha, M.Profile(sha,3))
            else:
                with self.assertRaises(M.CrosswalkError): M.local_rest((0,0,0), (10,0,0,1), .1)

    def test_loaded_bone_id_parent_and_exact_rest_words_are_independent_gates(self):
        for field, value in (("bone_id", 0), ("bone_id", True), ("parent_id", -1), ("position", (0.,0.,2.001)), ("position", (False,0.,2.))):
            case = host_fixture(); setattr(case.mdl.bones[0], field, value)
            with self.subTest(field=field, value=value), self.assertRaises(M.CrosswalkError): prove(case)

    def test_extra_missing_or_generated_suffix_bones_refuse(self):
        for action in (lambda v: v.armature.data.bones.values.pop(),
                       lambda v: v.armature.data.bones.values.append(v.data[0]),
                       lambda v: setattr(v.data[1], "name", "FrontHair1.001")):
            case = host_fixture(); action(case)
            with self.assertRaises(M.CrosswalkError): prove(case)

    def test_actual_parent_pointer_and_matrix_mismatches_refuse(self):
        for action in (lambda v: setattr(v.data[2], "parent", v.data[0]),
                       lambda v: v.data[1].matrix_local[0].__setitem__(3, 2.),
                       lambda v: v.pose[1].matrix[1].__setitem__(3, 9.)):
            case = host_fixture(); action(case)
            with self.assertRaises(M.CrosswalkError): prove(case)

    def test_pose_owner_data_pointer_and_data_owner_mismatches_refuse(self):
        for action in (lambda v: setattr(v.pose[1], "id_data", RNA()),
                       lambda v: setattr(v.pose[1], "bone", v.data[0]),
                       lambda v: setattr(v.data[1], "id_data", RNA())):
            case = host_fixture(); action(case)
            with self.assertRaises(M.CrosswalkError): prove(case)

    def test_scale_bool_nonfinite_and_transformed_factory_owner_refuse(self):
        for scale in (True, 0, -1, float("nan"), float("inf")):
            case = host_fixture(); case.scale = scale
            with self.assertRaises(M.CrosswalkError): prove(case)
        self.value.armature.matrix_world[0][3] = .1
        with self.assertRaises(M.CrosswalkError): prove(self.value)

    def test_same_native_coordinates_prove_at_two_scales(self):
        for scale in (.01, .3):
            proof = prove(host_fixture(scale)); self.assertEqual(proof.scale, scale)

    def test_three_hooks_join_reordered_nodes_and_skin_slots_by_identity(self):
        proof, value = self.export(); result = value.collector.finish(glb(value))
        self.assertEqual([r["gltf_node_index"] for r in result["bones"]], [3,4,1])
        self.assertEqual([r["skin_memberships"][0]["joint_slot"] for r in result["bones"]], [1,2,0])
        self.assertEqual(result["status"], "observed_inactive")
        self.assertEqual(result["HAS_runtime_binding"], "unattempted")
        self.assertFalse(result["export_extras"]); self.assertFalse(result["native_simulation"])
        self.assertEqual(self.value.data[1].name, "FrontHair1")

    def test_exporter_pin_change_refuses_before_hooks(self):
        pins = dict(M.EXPORTER_PINS); pins["blender/exp/joints.py"] = "0"*64
        with self.assertRaises(M.CrosswalkError): M.ExportCollector(prove(self.value), pins)

    def test_hook_failures_latch_and_finish_refuses_instead_of_swallowed_success(self):
        proof = prove(self.value); value = export_fixture(proof)
        value.collector.gather_joint_hook(value.nodes[3], NS(), value.settings)
        self.assertIsNotNone(value.collector.failure)
        begin_export(value, proof); final_hook(value)
        with self.assertRaisesRegex(M.CrosswalkError, "latched_export_hook_failure"):
            value.collector.finish(glb(value))

    def test_distinct_node_for_same_native_bone_latches_ambiguity(self):
        proof = prove(self.value); value = export_fixture(proof); begin_export(value, proof)
        value.collector.gather_joint_hook(node(), proof.bindings[0].pose_bone, value.settings)
        self.assertIsNotNone(value.collector.failure)

    def test_wrong_export_pose_owner_or_identity_refuses(self):
        for owner in (None, "same_owner_wrong_pose"):
            proof = prove(self.value); value = export_fixture(proof)
            pb = RNA(bone=proof.bindings[0].data_bone, id_data=RNA() if owner is None else proof.armature)
            value.collector.gather_joint_hook(value.nodes[3], pb, value.settings)
            self.assertIsNotNone(value.collector.failure)

    def test_missing_or_duplicate_final_object_identity_refuses_even_with_equal_labels(self):
        for action in (lambda v: v.gltf.nodes.__setitem__(3, copy.copy(v.nodes[3])),
                       lambda v: v.gltf.nodes.append(v.nodes[3])):
            proof = prove(self.value); value = export_fixture(proof); begin_export(value, proof); action(value); final_hook(value)
            self.assertIsNotNone(value.collector.failure)

    def test_unobserved_joint_missing_hooks_and_changed_hierarchy_refuse(self):
        for action in (lambda v: v.collector.nodes.pop(2), lambda v: v.nodes[4].children.clear()):
            proof = prove(self.value); value = export_fixture(proof); begin_export(value, proof); action(value); final_hook(value)
            self.assertIsNotNone(value.collector.failure)

    def test_skin_without_mesh_use_or_foreign_joint_refuses(self):
        for action in (lambda v: setattr(v.nodes[0], "skin", None), lambda v: setattr(v.nodes[0], "mesh", None)):
            proof = prove(self.value); value = export_fixture(proof); begin_export(value, proof); action(value); final_hook(value)
            self.assertIsNotNone(value.collector.failure)
        proof = prove(self.value); value = export_fixture(proof); begin_export(value, proof)
        value.skin.joints = [1,3,0]
        value.collector.gather_gltf_extensions_hook(value.gltf, value.settings)
        self.assertIsNotNone(value.collector.failure)

    def test_extra_settings_or_extras_never_enable_broad_export(self):
        for key in ("gltf_extras", "gltf_leaf_bone", "gltf_gpu_instances", "gltf_use_gltfpack"):
            proof = prove(self.value); value = export_fixture(proof); begin_export(value, proof)
            value.settings[key] = True; final_hook(value)
            self.assertIsNotNone(value.collector.failure)
        proof = prove(self.value); value = export_fixture(proof); begin_export(value, proof)
        value.nodes[3].extras = {"arbitrary_model_property": "must_not_escape"}; final_hook(value)
        self.assertIsNotNone(value.collector.failure)

    def test_final_GLB_reconciliation_rejects_changed_node_or_skin(self):
        proof, value = self.export()
        for change in (lambda data: data["nodes"][3].update(name="changed"),
                       lambda data: data["skins"][0].update(joints=[3,4,1])):
            with self.assertRaises(M.CrosswalkError): value.collector.finish(glb(value, change))

    def test_final_snapshot_is_frozen_against_later_export_mutation(self):
        proof, value = self.export(); value.nodes[3].children.clear()
        with self.assertRaises(M.CrosswalkError): value.collector.finish(glb(value))

    def test_source_pose_mutation_after_hook_refuses_publication(self):
        proof, value = self.export(); self.value.pose[1].matrix[0][3] += .01
        with self.assertRaises(M.CrosswalkError): value.collector.finish(glb(value))

    def test_missing_final_hook_and_changed_GLB_length_refuse(self):
        proof = prove(self.value); value = export_fixture(proof); begin_export(value, proof)
        with self.assertRaises(M.CrosswalkError): value.collector.finish(b"glTF")
        final_hook(value); raw = glb(value)
        with self.assertRaises(M.CrosswalkError): value.collector.finish(raw+b"x")

    def test_complete_report_budget_is_inclusive_and_never_truncates(self):
        proof, value = self.export(); raw = glb(value)
        result = value.collector.finish(raw); size = len(M.compact(result))
        with patch.object(M, "REPORT_LIMIT", size): self.assertEqual(value.collector.finish(raw), result)
        with patch.object(M, "REPORT_LIMIT", size-1):
            with self.assertRaises(M.CrosswalkError): value.collector.finish(raw)

    def test_scoped_extension_registration_restores_on_success_and_exception(self):
        module = ModuleType("authored_exporter_module")
        with patch.dict(sys.modules, {module.__name__: module}):
            with M.temporary_export_extension(module, [module.__name__], self):
                self.assertIs(module.glTF2ExportUserExtension(), self)
            self.assertFalse(hasattr(module, "glTF2ExportUserExtension"))
            with self.assertRaises(RuntimeError):
                with M.temporary_export_extension(module, [module.__name__], self): raise RuntimeError("authored export error")
            self.assertFalse(hasattr(module, "glTF2ExportUserExtension"))

    def test_scoped_registration_refuses_existing_or_unloaded_addon(self):
        module = ModuleType("authored_exporter_module")
        with self.assertRaises(M.CrosswalkError):
            with M.temporary_export_extension(module, [module.__name__], self): pass
        with patch.dict(sys.modules, {module.__name__: module}):
            module.glTF2ExportUserExtension = object()
            before = module.glTF2ExportUserExtension
            with self.assertRaises(M.CrosswalkError):
                with M.temporary_export_extension(module, [module.__name__], self): pass
            self.assertIs(module.glTF2ExportUserExtension, before)

    def test_cpu_module_import_does_not_load_product_or_host_packages(self):
        self.assertFalse(any(name == "bpy" or name == "mathutils" or name.startswith("SourceIO") or name.startswith("io_scene_gltf2") for name in sys.modules))

    def test_selected_scene_one_is_admitted_without_assuming_scene_zero(self):
        proof = prove(self.value); value = export_fixture(proof)
        selected = value.gltf.scenes[0]
        value.gltf.scenes = [NS(name="other", nodes=[], extensions=None, extras=None), selected]
        value.gltf.scene = 1
        begin_export(value, proof); final_hook(value)
        result = value.collector.finish(glb(value))
        self.assertEqual(result["selected_scene"], 1)
        self.assertEqual(result["selected_scene_roots"], [2,0])
        self.assertEqual(result["target_skin_mesh_nodes"], [{"skin_index": 0, "reachable_skinned_mesh_nodes": [0]}])

    def test_removed_or_changed_scene_roots_refuse_final_GLB(self):
        proof, value = self.export()
        for change in (lambda data: data["scenes"][0].update(nodes=[]),
                       lambda data: data["scenes"][0].update(nodes=[2]),
                       lambda data: data["scenes"][0].update(nodes=[0]),
                       lambda data: data["scenes"][0].update(name="changed selected scene")):
            with self.subTest(change=change), self.assertRaises(M.CrosswalkError):
                value.collector.finish(glb(value, change))

    def test_changed_selected_scene_or_missing_scene_container_refuses_final_GLB(self):
        proof = prove(self.value); value = export_fixture(proof)
        value.gltf.scenes.append(NS(name="other", nodes=[2,0], extensions=None, extras=None))
        begin_export(value, proof); final_hook(value)
        for change in (lambda data: data.update(scene=1), lambda data: data.pop("scene"),
                       lambda data: data.pop("scenes"), lambda data: data.update(scene=False)):
            with self.subTest(change=change), self.assertRaises(M.CrosswalkError):
                value.collector.finish(glb(value, change))

    def test_nonselected_scene_does_not_make_mesh_or_joints_reachable(self):
        for selected_roots, other_roots in (([2], [0]), ([0], [2]), ([], [2,0])):
            proof = prove(self.value); value = export_fixture(proof)
            value.gltf.scenes[0].nodes = selected_roots
            value.gltf.scenes.append(NS(name="nonselected", nodes=other_roots, extensions=None, extras=None))
            begin_export(value, proof); final_hook(value)
            self.assertIsNotNone(value.collector.failure)
            with self.assertRaises(M.CrosswalkError): value.collector.finish(glb(value))

    def test_invalid_selected_indices_and_root_domains_refuse(self):
        for selected in (None, False, -1, 1, "0"):
            proof = prove(self.value); value = export_fixture(proof); value.gltf.scene = selected
            begin_export(value, proof); final_hook(value)
            self.assertIsNotNone(value.collector.failure)
        for roots in ([False], [-1], [99], ["2"], [2,2], [3]):
            proof = prove(self.value); value = export_fixture(proof); value.gltf.scenes[0].nodes = roots
            begin_export(value, proof); final_hook(value)
            self.assertIsNotNone(value.collector.failure)

    def test_unreachable_node_cycle_refuses_whole_scene_proof(self):
        proof = prove(self.value); value = export_fixture(proof)
        value.gltf.nodes.extend([node(children=[6]), node(children=[5])])
        begin_export(value, proof); final_hook(value)
        self.assertIsNotNone(value.collector.failure)
        self.assertEqual(value.collector.failure[2], "exported_node_cycle")

    def test_scene_snapshot_survives_later_root_list_mutation(self):
        proof, value = self.export(); value.gltf.scenes[0].nodes.remove(0)
        with self.assertRaises(M.CrosswalkError): value.collector.finish(glb(value))

    def test_target_mesh_must_resolve_and_have_skin_attributes(self):
        for mesh_index in (False, -1, 1, "0"):
            proof = prove(self.value); value = export_fixture(proof); value.nodes[0].mesh = mesh_index
            begin_export(value, proof); final_hook(value)
            self.assertIsNotNone(value.collector.failure)
        for replacement in ([], [Mesh({"primitives": []})], [Mesh({"primitives": [{"attributes": {"POSITION": 0}}]})]):
            proof = prove(self.value); value = export_fixture(proof); value.gltf.meshes = replacement
            begin_export(value, proof); final_hook(value)
            self.assertIsNotNone(value.collector.failure)

    def test_removed_or_replaced_final_mesh_definition_refuses(self):
        proof, value = self.export()
        for change in (lambda data: data.update(meshes=[]),
                       lambda data: data["meshes"][0].update(name="foreign replacement"),
                       lambda data: data["meshes"][0]["primitives"][0]["attributes"].update(POSITION=99)):
            with self.subTest(change=change), self.assertRaises(M.CrosswalkError):
                value.collector.finish(glb(value, change))

    def test_optional_aligned_BIN_is_admitted_to_exact_EOF(self):
        proof, value = self.export(); raw = glb(value)
        raw += struct.pack("<II", 4, 0x004e4942)+b"\x00\x01\x02\x03"
        raw = raw[:8]+struct.pack("<I", len(raw))+raw[12:]
        self.assertEqual(value.collector.finish(raw)["glb_sha256"], hashlib.sha256(raw).hexdigest())

    def test_trailing_one_to_seven_bytes_refuse_even_when_header_length_matches(self):
        proof, value = self.export(); original = glb(value)
        for count in range(1,8):
            raw = original+b"x"*count
            raw = raw[:8]+struct.pack("<I", len(raw))+raw[12:]
            with self.subTest(count=count), self.assertRaises(M.CrosswalkError): value.collector.finish(raw)

    def test_duplicate_JSON_truncated_BIN_unknown_and_unaligned_chunks_refuse(self):
        proof, value = self.export(); original = glb(value)
        tails = [original[12:], struct.pack("<II", 8, 0x004e4942)+b"1234",
                 struct.pack("<II", 4, 0x12345678)+b"1234", struct.pack("<II", 3, 0x004e4942)+b"123"]
        for tail in tails:
            raw = original+tail
            raw = raw[:8]+struct.pack("<I", len(raw))+raw[12:]
            with self.subTest(tail=tail[:8]), self.assertRaises(M.CrosswalkError): value.collector.finish(raw)

    def test_preflight_latches_independent_export_callbacks_before_proof(self):
        for key in ("pre_export_callbacks", "post_export_callbacks"):
            proof = prove(self.value); value = export_fixture(proof)
            value.settings[key] = [lambda settings: None]
            value.collector.pre_export_hook(value.settings)
            self.assertFalse(value.collector.preflight_seen)
            self.assertEqual(value.collector.failure[0], "preflight")
            self.assertEqual(value.collector.failure[2], "uncontrolled_"+key)

    def test_missing_preflight_or_later_callback_registration_refuses(self):
        proof = prove(self.value); value = export_fixture(proof)
        value.collector.gather_gltf_extensions_hook(value.gltf, value.settings)
        self.assertEqual(value.collector.failure[2], "export_preflight_not_observed")
        proof = prove(self.value); value = export_fixture(proof); begin_export(value, proof)
        value.settings["post_export_callbacks"].append(lambda settings: None); final_hook(value)
        self.assertEqual(value.collector.failure[2], "uncontrolled_post_export_callbacks")

    def test_rest_mutation_during_export_cannot_hide_behind_post_export_restoration(self):
        proof = prove(self.value); value = export_fixture(proof); begin_export(value, proof)
        original = self.value.pose[1].matrix[0][3]
        self.value.pose[1].matrix[0][3] += .01; final_hook(value)
        self.value.pose[1].matrix[0][3] = original
        self.assertIsNotNone(value.collector.failure)
        self.assertEqual(value.collector.failure[0], "final")
        with self.assertRaises(M.CrosswalkError): value.collector.finish(glb(value))

    def test_preflight_refuses_other_extension_before_identity_collection(self):
        proof = prove(self.value); value = export_fixture(proof)
        value.settings["gltf_user_extensions"].append(object())
        value.collector.pre_export_hook(value.settings)
        self.assertFalse(value.collector.preflight_seen)
        self.assertEqual(value.collector.failure[2], "uncontrolled_export_extensions")

    def test_two_pass_nested_empty_pruning_matches_pinned_policy(self):
        source = {"extensions": {"unused": {}}}
        self.assertEqual(M.pruned_mesh_json(source), {"extensions": {}})
        self.assertEqual(M.emitted_json(source), {})
        proof = prove(self.value); value = export_fixture(proof)
        value.gltf.meshes[0].value["extensions"] = {"unused": {}}
        begin_export(value, proof); final_hook(value)
        self.assertEqual(value.collector.finish(glb(value))["status"], "observed_inactive")


if __name__ == "__main__":
    unittest.main(verbosity=2)
