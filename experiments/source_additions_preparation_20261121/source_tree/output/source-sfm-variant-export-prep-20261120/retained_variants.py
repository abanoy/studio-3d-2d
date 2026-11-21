"""Unadopted opt-in Source variant capture/export observer.

No bpy/SourceIO imports, filesystem access, process work or operator registration.
The host supplies authenticated actual SDK classes, ordinary material resolver,
current geometry/skeleton fingerprint, resource guard and existing JSON helpers.
Only the two fixed supplied MDL49 profiles are accepted. Default imports do no
new work. Native geometry, weights, skeleton and source material assignments are
never written here; temporary selection/visibility is restored in finally.
"""
from contextlib import contextmanager
import copy
import hashlib
import json
import sys

PROFILES = {
    '44cece1f44dfc3d7b32b91b5acfdae53ec9f6f90a0220a422ace92e323da7b32': (66, 3, (2,)),
    'd8b32165bef2ec4f1c09acd19b3b136b3492b556fcfb9da98fb01826c5e279ff': (31, 1, (2, 2, 2)),
}
REVISION = 'fe24260b97ac03b899d9b5d4f0fd7b34772f3647'
EXT = 'KHR_materials_variants'


class Refusal(ValueError):
    pass


def need(ok, code):
    if not ok:
        raise Refusal(code)


def same(a, b):
    return len(a) == len(b) and all(x is y for x, y in zip(a, b))


def unique_index(rows, value):
    indices = [i for i, row in enumerate(rows) if row is value]
    need(len(indices) == 1, 'export_reference_not_unique')
    return indices[0]


def canonical(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('ascii')


def prepare(request, catalogue, container, *, types, geometry_guard):
    """Ordinary route returns None before inspecting a catalogue/container."""
    need(type(request) is dict, 'request_type')
    if 'retain_variants' not in request or request['retain_variants'] is False:
        return None
    need(request['retain_variants'] is True, 'retain_variants_boolean')
    need(request.get('appearance') is None and request.get('sourceio_revision') == REVISION,
         'incompatible_variant_request')
    need(type(catalogue) is dict and catalogue.get('native_mdl_sha256') in PROFILES,
         'unsupported_variant_native_profile')
    need(request.get('sha256') == catalogue.get('original_source_sha256'), 'original_source_identity')
    return Capture(catalogue, container, types, geometry_guard)


class Capture:
    def __init__(self, catalogue, container, types, geometry_guard):
        self.types, self.container, self.geometry_guard = types, container, geometry_guard
        self.restoration_failed = False
        self.catalogue = catalogue
        need(type(catalogue.get('catalogue_sha256')) is str and len(catalogue['catalogue_sha256']) == 64,
             'catalogue_digest')
        core = {key: value for key, value in catalogue.items() if key != 'catalogue_sha256'}
        need(len(canonical(catalogue)) <= 256 * 1024 and
             hashlib.sha256(canonical(core)).hexdigest() == catalogue['catalogue_sha256'], 'catalogue_digest')
        self.catalogue_bytes = canonical(catalogue)
        need(catalogue.get('format') == 'studio_source_mdl_choices_1' and catalogue.get('native_version') == 49,
             'catalogue_profile')
        need(type(container) is types.ModelContainer and not container.attachments and not container.physics_objects,
             'container_profile')
        self.mdl = container.mdl
        need(type(self.mdl) is types.Mdl and self.mdl.header.version == 49, 'actual_mdl_type')
        bones, skins, choices = PROFILES[catalogue['native_mdl_sha256']]
        self.profile = (bones, skins, choices)
        self.armature = container.armature
        need(type(self.armature) is types.Object and self.armature.type == 'ARMATURE' and
             self.armature.original is self.armature and self.armature.library is None and
             len(self.armature.data.bones) == bones, 'actual_armature_profile')
        need(type(catalogue.get('materials')) is list and type(catalogue.get('skins')) is list and
             len(catalogue['skins']) == skins and len(self.mdl.skin_groups) == skins and
             len(self.mdl.materials) == len(catalogue['materials']), 'skin_catalogue_shape')
        self.native_materials = tuple(self.mdl.materials)
        need(all(row['index'] == i and row['name'] == mat.name
                 for i, (row, mat) in enumerate(zip(catalogue['materials'], self.native_materials))),
             'actual_native_material_catalogue')
        self.materials = tuple(row.bpy_material for row in self.native_materials)
        need(all(type(row) is types.Material and row.original is row and row.library is None
                 for row in self.materials), 'actual_local_materials')
        columns = catalogue['skin_reference_count']
        need(type(columns) is int and 0 < columns <= len(self.materials), 'native_skin_columns')
        self.skin_rows = []
        for index, row in enumerate(catalogue['skins']):
            ids = row['material_indices']
            need(row['index'] == index and type(ids) is list and len(ids) == columns and
                 all(type(v) is int and 0 <= v < len(self.materials) for v in ids), 'native_skin_row')
            need(same(self.mdl.skin_groups[index], [self.native_materials[v] for v in ids]), 'actual_native_skin_refs')
            self.skin_rows.append(tuple(self.materials[v] for v in ids))
        need(catalogue['skins'][0]['material_indices'] == list(range(columns)), 'nonidentity_default_skin_unsupported')
        need(len(self.mdl.body_parts) == len(choices) == len(catalogue['bodygroups']), 'native_part_count')
        need(type(container.bodygroups) is dict and len(container.bodygroups) == len(choices), 'container_groups')
        self.rows, used = [], []
        for group_id, (part, group, count) in enumerate(zip(self.mdl.body_parts, catalogue['bodygroups'], choices)):
            need(group['index'] == group_id and part.name == group['name'] and
                 len(part.models) == len(group['choices']) == count, 'native_part_join')
            actual = container.bodygroups.get(part.name)
            need(type(actual) is list and len(actual) == count, 'actual_part_choices')
            for choice_id, (model, declared, obj) in enumerate(zip(part.models, group['choices'], actual)):
                need(declared['index'] == choice_id and model.name == declared['name'] and
                     type(model.vertex_count) is int and model.vertex_count == declared['vertex_count'] and
                     declared['true_blank'] is (model.vertex_count == 0), 'native_choice_join')
                if model.vertex_count == 0:
                    need(obj is None, 'blank_has_object')
                    self.rows.append((group_id, choice_id, None, None, ()))
                    continue
                need(type(obj) is types.Object and obj.type == 'MESH' and obj.original is obj and obj.library is None and
                     type(obj.data) in (types.Mesh, types.FastMesh) and obj.data.original is obj.data and obj.data.library is None,
                     'actual_original_mesh_object')
                need(not any(old is obj for old in used), 'variant_object_alias')
                need(obj.parent is self.armature and 0 < len(obj.data.vertices) <= 200000 and
                     0 < len(obj.data.polygons) <= 1000000, 'variant_mesh_parent_or_budget')
                slots = tuple(slot.material for slot in obj.material_slots)
                need(0 < len(slots) <= columns and same(slots, tuple(obj.data.materials)), 'default_slot_refs')
                native_columns = []
                for mat in slots:
                    matches = [i for i, value in enumerate(self.skin_rows[0]) if value is mat]
                    need(len(matches) == 1, 'ambiguous_default_material_column')
                    native_columns.append(matches[0])
                need(all(type(poly.material_index) is int and 0 <= poly.material_index < len(slots)
                         for poly in obj.data.polygons), 'polygon_material_domain')
                used.append(obj)
                self.rows.append((group_id, choice_id, obj, obj.data, tuple(native_columns)))
        need(same(container.objects, used), 'container_object_inventory')
        self.objects = tuple(used)
        required = []
        for _, _, obj, _, columns_used in self.rows:
            if obj is None:
                continue
            for column in columns_used:
                for skin in self.skin_rows:
                    if not any(old is skin[column] for old in required): required.append(skin[column])
        self.required_materials = tuple(required)
        self._state = self._live_state()
        self._geometry = self._fingerprint()

    def _fingerprint(self):
        value = self.geometry_guard()
        need(type(value) is bytes and len(value) == 32, 'complete_geometry_guard_required')
        return value

    def _live_state(self):
        c, t = self.container, self.types
        need(c.mdl is self.mdl and c.armature is self.armature and same(c.objects, self.objects), 'source_container_changed')
        need(not c.attachments and not c.physics_objects, 'source_container_features_changed')
        values = [self.mdl.header.version, tuple((id(v), v.name, id(v.bpy_material)) for v in self.mdl.materials),
                  tuple(tuple(id(v) for v in skin) for skin in self.mdl.skin_groups),
                  tuple((id(part), part.name, tuple((id(model), model.name, model.vertex_count)
                         for model in part.models)) for part in self.mdl.body_parts)]
        for group_id, choice_id, obj, mesh, columns in self.rows:
            part = self.mdl.body_parts[group_id]
            need(c.bodygroups[part.name][choice_id] is obj, 'source_choice_ref_changed')
            if obj is None: continue
            need(obj.data is mesh and obj.parent is self.armature and obj.original is obj and mesh.original is mesh,
                 'source_mesh_binding_changed')
            need(same(tuple(slot.material for slot in obj.material_slots), tuple(self.skin_rows[0][n] for n in columns)) and
                 same(tuple(mesh.materials), tuple(self.skin_rows[0][n] for n in columns)), 'source_material_binding_changed')
            values.append((id(obj), id(mesh), len(mesh.vertices), len(mesh.loops), len(mesh.polygons),
                           tuple(poly.material_index for poly in mesh.polygons)))
        return values

    def recheck(self):
        need(not self.restoration_failed, 'source_export_restoration_failed')
        need(canonical(self.catalogue) == self.catalogue_bytes, 'native_catalogue_changed')
        need(self._live_state() == self._state and self._fingerprint() == self._geometry, 'source_geometry_or_inventory_changed')

    @contextmanager
    def visible_export(self, bpy):
        """Fresh owned Blender scene only; no material/mesh/pose assignments."""
        self.recheck()
        all_objects = tuple(bpy.context.scene.objects)
        need(len(all_objects) <= 4096 and all(any(v is obj for v in all_objects) for obj in (*self.objects, self.armature)),
             'scene_membership')
        old = [(obj, obj.select_get(), obj.hide_get(), obj.hide_render) for obj in all_objects]
        active = bpy.context.view_layer.objects.active
        try:
            for obj in all_objects: obj.select_set(False)
            for obj in (*self.objects, self.armature):
                obj.hide_set(False); obj.hide_render = False; obj.select_set(True)
            bpy.context.view_layer.objects.active = self.armature
            self.recheck()
            yield
        finally:
            primary = sys.exc_info()[1]
            errors = []
            for obj, selected, hidden, render in old:
                try:
                    obj.hide_render = render; obj.hide_set(hidden); obj.select_set(selected)
                except Exception as error: errors.append(error)
            try:
                bpy.context.view_layer.objects.active = active
                self.recheck()
            except Exception as error: errors.append(error)
            if errors:
                self.restoration_failed = True
                if primary is None: raise errors[0]


class Collector:
    """One owned extension, to be registered by a separately qualified host.

    material_resolver(mat, mesh, settings) must call the authenticated ordinary
    SDK gather/final-material functions for the admitted UV0 graph profile.
    resource_guard(mat) admits the actual rebuilt local graph/images before that
    resolver can run. This module cannot qualify those callbacks by their names.
    """
    def __init__(self, capture, *, gltf_types, material_resolver, resource_guard, final_resource_guard, contract, planner, bone_proof):
        self.capture, self.t, self.resolve, self.resource_guard = capture, gltf_types, material_resolver, resource_guard
        self.C, self.planner = contract, planner
        self.final_resource_guard = final_resource_guard
        need(type(bone_proof) is contract.NativeProof and bone_proof.armature is capture.armature and
             bone_proof.mdl is capture.mdl and bone_proof.native_sha256 == capture.catalogue['native_mdl_sha256'] and
             len(bone_proof.bindings) == capture.profile[0], 'native_bone_proof_context')
        self.bone_proof = bone_proof
        self.joint_nodes, self.skin_refs = {}, []
        self.bone_pointers = {b.data_pointer: b for b in bone_proof.bindings}
        self.nodes, self.meshes, self.materials, self.primitive_rows = {}, {}, {}, {}
        self.failure = None; self.preflight = False; self.final = None
        self.variant_values = [{'name': 'Skin ' + str(i + 1)} for i in range(capture.profile[1])]
        self.variant_refs = [gltf_types.ChildOfRootExtension(name=EXT, path=['variants'], extension=value, required=False)
                             for value in self.variant_values]

    def _hook(self, stage, action):
        if self.failure is not None: return
        try: action()
        except Exception as error:
            if self.failure is None:
                self.failure = (stage, str(error) if type(error) is Refusal else 'host_api_failure')

    def _settings(self, settings):
        need(type(settings) is dict and type(settings.get('gltf_user_extensions')) is list and
             same(settings['gltf_user_extensions'], [self]), 'sole_owned_extension_required')
        for key, value in {'gltf_apply': False, 'gltf_extras': False, 'gltf_skins': True, 'gltf_yup': True,
                           'gltf_animations': False, 'gltf_current_frame': True, 'gltf_morph': True,
                           'gltf_rest_position_armature': True, 'gltf_def_bones': False, 'gltf_leaf_bone': False,
                           'gltf_unused_images': False, 'gltf_unused_textures': False,
                           'gltf_armature_object_remove': False,
                           'gltf_flatten_bones_hierarchy': False, 'gltf_flatten_obj_hierarchy': False,
                           'gltf_gpu_instances': False, 'gltf_use_gltfpack': False,
                           'gltf_draco_mesh_compression': False}.items():
            need(settings.get(key) is value, 'variant_export_settings')
        for key in ('pre_export_callbacks', 'post_export_callbacks'):
            need(type(settings.get(key)) is list and not settings[key], 'foreign_export_callback')
        self.capture.recheck(); self.bone_proof.recheck()

    def pre_export_hook(self, settings):
        def run():
            need(not self.preflight, 'duplicate_preflight')
            self._settings(settings); self.preflight = True
        self._hook('preflight', run)

    def gather_joint_hook(self, node, pose_bone, settings):
        def run():
            self._settings(settings)
            data_pointer = self.C.pointer(pose_bone.bone)
            need(data_pointer in self.bone_pointers and type(node) is self.t.Node, 'foreign_joint')
            binding = self.bone_pointers[data_pointer]
            need(self.C.pointer(pose_bone.id_data) == self.C.pointer(self.capture.armature) and
                 self.C.pointer(pose_bone) == binding.pose_pointer, 'joint_actual_owner')
            old = self.joint_nodes.get(binding.native_index)
            need(old is None or old is node, 'duplicate_native_joint')
            self.joint_nodes[binding.native_index] = node
        self._hook('joint', run)

    def gather_skin_hook(self, skin, armature, settings):
        def run():
            self._settings(settings)
            need(armature is self.capture.armature and type(skin) is self.t.Skin, 'foreign_skin')
            if not any(old is skin for old in self.skin_refs): self.skin_refs.append(skin)
        self._hook('skin', run)

    def gather_material_hook(self, material, blender_material, settings):
        def run():
            self._settings(settings)
            need(self.preflight and type(material) is self.t.Material, 'material_hook_context')
            need(any(v is blender_material for v in self.capture.required_materials), 'foreign_material_hook')
            need(self.resource_guard(blender_material) is True, 'unprepared_variant_material')
            old = self.materials.get(id(blender_material))
            need(old is None or old is material, 'material_gather_identity_changed')
            self.materials[id(blender_material)] = material
        self._hook('material', run)

    def gather_mesh_hook(self, mesh, data, obj, vertex_groups, modifiers, materials, settings):
        def run():
            self._settings(settings)
            matches = [r for r in self.capture.rows if r[2] is obj]
            need(self.preflight and len(matches) == 1 and type(mesh) is self.t.Mesh, 'mesh_hook_context')
            _, _, _, expected_data, columns = matches[0]
            need(data is expected_data and type(materials) is tuple and
                 same(materials, [self.capture.skin_rows[0][n] for n in columns]), 'mesh_source_material_refs')
            need(id(obj) not in self.meshes and type(mesh.primitives) is list and 0 < len(mesh.primitives) <= 256,
                 'mesh_hook_repeated_or_empty')
            bindings, pending = [], []
            for primitive in mesh.primitives:
                need(type(primitive) is self.t.MeshPrimitive and primitive.mode in (None, 4), 'primitive_profile')
                native = [n for n in columns if self.materials.get(id(self.capture.skin_rows[0][n])) is primitive.material]
                need(len(native) == 1, 'primitive_default_material_identity')
                column = native[0]; mapped = []
                for skin in self.capture.skin_rows:
                    mat = skin[column]
                    need(self.resource_guard(mat) is True, 'unprepared_variant_material')
                    result = self.resolve(mat, data, settings)
                    need(type(result) is self.t.Material and self.materials.get(id(mat)) is result,
                         'resolved_material_not_observed')
                    mapped.append(result)
                need(primitive.extensions is None or type(primitive.extensions) is dict and not primitive.extensions,
                     'foreign_primitive_extensions')
                mapping = [{'material': mat, 'variants': [self.variant_refs[i]]} for i, mat in enumerate(mapped)]
                extension = self.t.Extension(name=EXT, extension={'mappings': mapping}, required=False)
                pending.append((primitive, {EXT: extension})); bindings.append(tuple(mapped))
            # Own temporary glTF objects only, after all primitive plans validate.
            for primitive, extensions in pending: primitive.extensions = extensions
            self.meshes[id(obj)] = mesh; self.primitive_rows[id(obj)] = tuple(bindings)
        self._hook('mesh', run)

    def gather_node_hook(self, node, obj, settings):
        def run():
            if not any(v is obj for v in self.capture.objects): return
            self._settings(settings)
            need(type(node) is self.t.Node and id(obj) in self.meshes and node.mesh is self.meshes[id(obj)],
                 'node_mesh_identity')
            need(id(obj) not in self.nodes, 'duplicate_node_hook')
            self.nodes[id(obj)] = node
        self._hook('node', run)

    def gather_gltf_extensions_hook(self, gltf, settings):
        def run():
            self._settings(settings)
            need(self.preflight and self.final is None and type(gltf) is self.t.Gltf and
                 set(self.nodes) == {id(v) for v in self.capture.objects}, 'final_hook_coverage')
            need(type(gltf.nodes) is list and type(gltf.meshes) is list and type(gltf.materials) is list,
                 'flat_tables')
            need(set(self.materials) == {id(v) for v in self.capture.required_materials}, 'material_hook_coverage')
            indices = {id(obj): unique_index(gltf.nodes, self.nodes[id(obj)]) for obj in self.capture.objects}
            need(set(self.joint_nodes) == set(range(self.capture.profile[0])), 'native_joint_hook_coverage')
            joint_indices = {key: unique_index(gltf.nodes, node) for key, node in self.joint_nodes.items()}
            need(len(set(joint_indices.values())) == self.capture.profile[0], 'native_joint_alias')
            need(type(gltf.skins) is list and len(gltf.skins) == len(self.skin_refs) > 0 and
                 all(any(value is skin for value in gltf.skins) for skin in self.skin_refs), 'actual_skin_coverage')
            for skin in self.skin_refs:
                need(type(skin.joints) is list and len(skin.joints) == self.capture.profile[0] and
                     all(type(v) is int for v in skin.joints) and set(skin.joints) == set(joint_indices.values()),
                     'complete_same_native_skeleton')
            assignments = {}
            for obj in self.capture.objects:
                mesh = self.meshes[id(obj)]
                mesh_index = unique_index(gltf.meshes, mesh)
                need(self.nodes[id(obj)].mesh == mesh_index and type(self.nodes[id(obj)].mesh) is int, 'flat_node_mesh')
                skin_index = self.nodes[id(obj)].skin
                need(type(skin_index) is int and 0 <= skin_index < len(gltf.skins) and
                     any(gltf.skins[skin_index] is skin for skin in self.skin_refs), 'mesh_same_source_skin')
                rows = self.primitive_rows[id(obj)]
                need(len(mesh.primitives) == len(rows), 'primitive_count_changed')
                for surface, materials in enumerate(rows):
                    ids = [unique_index(gltf.materials, mat) for mat in materials]
                    need(type(mesh.primitives[surface].material) is int and mesh.primitives[surface].material == ids[0],
                         'flat_default_material')
                    assignments[(indices[id(obj)], surface)] = ids
            snapshot = {'scene': gltf.scene,
                        'scenes': self.C.emitted_json([self.C.scene_dict(v) for v in gltf.scenes]),
                        'nodes': self.C.emitted_json([self.C.node_dict(v) for v in gltf.nodes]),
                        'meshes': self.C.emitted_json([self.C.mesh_dict(v) for v in gltf.meshes]),
                        'skins': self.C.emitted_json([v.to_dict() for v in gltf.skins])}
            reachable, parents = self.C.scene_graph(snapshot['scene'], snapshot['scenes'], snapshot['nodes'])
            mesh_nodes = {i for i, v in enumerate(snapshot['nodes']) if 'mesh' in v}
            need(mesh_nodes == set(indices.values()) and mesh_nodes <= reachable and
                 set(joint_indices.values()) <= reachable, 'active_scene_mesh_coverage')
            parent_rows = self.bone_proof.evidence()['bones']
            need(len(parent_rows) == self.capture.profile[0], 'native_parent_rows')
            for row in parent_rows:
                node = joint_indices[row['native_index']]
                parent = parents.get(node)
                while parent is not None and parent not in joint_indices.values(): parent = parents.get(parent)
                expected_parent = row['native_parent_index']
                need(parent == (None if expected_parent < 0 else joint_indices[expected_parent]),
                     'native_parent_hierarchy_changed')
            need(type(gltf.extensions) is dict and EXT in gltf.extensions, 'root_variants_missing')
            root_variants = gltf.extensions[EXT]
            need(type(root_variants) is dict and root_variants.get('variants') == self.variant_values,
                 'variant_root_order')
            material_bindings = tuple((mat, self.materials[id(mat)], unique_index(gltf.materials, self.materials[id(mat)]))
                                      for mat in self.capture.required_materials)
            self.final = dict(snapshot=snapshot, indices=indices, assignments=assignments,
                              material_count=len(gltf.materials), material_bindings=material_bindings)
        self._hook('final', run)

    def finish(self, raw_glb):
        need(self.failure is None and self.final is not None, 'latched_or_incomplete_variant_export')
        self.capture.recheck(); self.bone_proof.recheck()
        document = self.C.final_glb_json(raw_glb)
        for key, value in self.final['snapshot'].items():
            need(self.C.compact(document.get(key, [])) == self.C.compact(value), 'final_' + key + '_changed')
        need(document.get('extensions', {}).get(EXT, {}).get('variants') == self.variant_values,
             'final_variant_root_changed')
        need(EXT in document.get('extensionsUsed', []) and EXT not in document.get('extensionsRequired', []),
             'optional_variant_declaration')
        need(len(document.get('materials', [])) == self.final['material_count'], 'final_material_coverage')
        before_resources = self.C.compact(document)
        need(self.final_resource_guard(document, self.final['material_bindings']) is True,
             'final_resource_reconciliation_required')
        need(self.C.compact(document) == before_resources, 'final_resource_consumer_mutated_document')
        self.capture.recheck(); self.bone_proof.recheck()
        asset = hashlib.sha256(raw_glb).hexdigest()
        nodes = document['nodes']; parents = {}
        for at, node in enumerate(nodes):
            for child in node.get('children', []): parents[child] = at
        mesh_ids = set(self.final['indices'].values())
        inventory = {'format': self.planner.INVENTORY, 'asset_sha256': asset,
                     'material_count': self.final['material_count'], 'mesh_nodes': []}
        surfaces = []
        for node in sorted(mesh_ids):
            at = parents.get(node)
            while at is not None and at not in mesh_ids: at = parents.get(at)
            primitives = document['meshes'][nodes[node]['mesh']]['primitives']
            inventory['mesh_nodes'].append({'node': node, 'parent_mesh': at,
                                            'surface_materials': [p['material'] for p in primitives]})
            for surface, primitive in enumerate(primitives):
                ids = self.final['assignments'][(node, surface)]
                mappings = primitive.get('extensions', {}).get(EXT, {}).get('mappings')
                need(mappings == [{'material': mat, 'variants': [i]} for i, mat in enumerate(ids)],
                     'final_primitive_variant_mapping')
                surfaces.append({'node': node, 'surface': surface, 'materials': list(ids)})
        groups = []
        for group in self.capture.catalogue['bodygroups']:
            choices = []
            for declared in group['choices']:
                row = next(r for r in self.capture.rows if r[:2] == (group['index'], declared['index']))
                choices.append({'id': declared['index'], 'name': declared['name'], 'blank': declared['true_blank'],
                                'nodes': [] if row[2] is None else [self.final['indices'][id(row[2])]]})
            groups.append({'id': group['index'], 'name': group['name'], 'default': 0, 'choices': choices})
        manifest = {'format': self.planner.FORMAT, 'asset_sha256': asset, 'default_skin': 0,
                    'skins': [{'id': i, 'name': row['name']} for i, row in enumerate(self.variant_values)],
                    'groups': groups, 'surfaces': surfaces}
        return {'manifest': self.planner.validate_manifest(manifest, inventory), 'inventory': inventory,
                'selection': self.planner.default_selection(manifest, inventory),
                'summary': {'format': 'has_retained_source_variant_export_1', 'source_profile_count': 1,
                            'groups': len(groups), 'skins': len(self.variant_values), 'mesh_nodes': len(mesh_ids),
                            'surfaces': len(surfaces), 'resources_bound_to_flat_material_refs': True,
                            'source_geometry_skeleton_guard_unchanged': True,
                            'actual_same_native_bone_count': self.capture.profile[0],
                            'actual_runtime_or_artist_acceptance': False}}
