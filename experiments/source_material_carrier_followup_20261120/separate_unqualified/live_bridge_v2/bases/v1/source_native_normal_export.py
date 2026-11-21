"""UNRUN live Source bridge candidate for one exact Junko native family.

No bpy import or process launch at module import. Unknown profiles return None
before toolkit/native reads. The candidate uses the live VMT graph built by the
existing bridge, never an editable.blend fixture. It is not yet app adoption.
"""
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import struct
import sys
import types

HERE = Path(__file__).resolve().parent
KNOWN_MDL = '8da09c905227ddc8eef73a3f83594a4eb1c3a6d5304ee41ba5471bef834bc716'
REVISION = 'fe24260b97ac03b899d9b5d4f0fd7b34772f3647'
NATIVE = {
    'mdl': (37644, KNOWN_MDL),
    'vvd': (618368, '2bfa2a363eea586d06d4fd0e28c7751c10276da5cc0c46c310ffa9dedbb159e0'),
    'vtx': (173309, '924954f27574fc83945934a13e6b4e90049b5d46356053dc4b41ec43d3ce364a'),
}
IMPORTER_PIN = (12880, '173a34ecae50e0b7a9d467908f238c02d5d7e19df3c7f52387534914d703233b')
MAX_FILE = 128 * 1024 * 1024
TOOLKIT = {
    "creation_support": {
        "file": "creation_support.py",
        "bytes": 72518,
        "sha256": "2c890e5065203473802fd799d21f274eb6d4c8d0c4644d8ecf767b411afd58ea"
    },
    "current_id_ledger": {
        "file": "current_id_ledger.py",
        "bytes": 14885,
        "sha256": "ab2d0d3076f63d6a398b209a5a39c2334f3b00664c0fa38d152d4587a54ffee9"
    },
    "native_point_expectation": {
        "file": "native_point_expectation.py",
        "bytes": 27615,
        "sha256": "cbb4eca98a6cf5045211dc10bd8e060b79492ec306d61a4d29679fc0d5cc184d"
    },
    "weight_policy": {
        "file": "weight_policy.py",
        "bytes": 20860,
        "sha256": "f838e0d893969aa1ad884a1c1d92e28ba019454f313632855f2a33c55fc3415c"
    },
    "import_instrumentation": {
        "file": "import_instrumentation.py",
        "bytes": 3306,
        "sha256": "361fcad3dbff79bfd5367cd71ac5a769fc8155d6f38a1b061d5ce6e631f5a895"
    },
    "normal_export_adapter": {
        "file": "normal_export_adapter.py",
        "bytes": 23576,
        "sha256": "5d19134b9a4fbfd7a93777d9eb3026173d52b6380e3beb80a8211dedf9afc24e"
    },
    "vvd_normals": {
        "file": "vvd_normals.py",
        "bytes": 4184,
        "sha256": "f3a959cc8dff0bd03528b20886984857b16a21944d2f5ef627cf4c4c05ebcdfb"
    },
    "normal_identity_carrier": {
        "file": "normal_identity_carrier.py",
        "bytes": 17632,
        "sha256": "37be746c21274e9844a532698078423a0b4f156dcb546135d18b0217daf0fb08"
    },
    "material_inspection": {
        "file": "material_inspection.py",
        "bytes": 24579,
        "sha256": "5efd488d7912e7b032f5590a85e1a20419913f5f6736d906b126c4e8a6280d17"
    },
    "export_hook_proposal": {
        "file": "export_hook_proposal.py",
        "bytes": 48895,
        "sha256": "cad4213ed8f55ac060a2f7b2387637a466ef751b36ac26769dbda93e7e343511"
    },
    "resource_gate_proposal": {
        "file": "resource_gate_proposal.py",
        "bytes": 55481,
        "sha256": "4ce714dc84712384d089fc2d0b5b5a93c25c1f3dfe90f53ccee76477a3d1cee8"
    },
    "shared_image_cache_proposal": {
        "file": "shared_image_cache_proposal.py",
        "bytes": 36158,
        "sha256": "b4aed0a276e5a469274e961e11bddff6183e6d56d4ff91af9e339af4712617e6"
    },
    "observer_instrumentation": {
        "file": "observer_instrumentation.py",
        "bytes": 7829,
        "sha256": "15145030fab5b662be490e519ff59f870c4e9c0352766ff59bf3da3f12198f7b"
    },
    "gather_binding": {
        "file": "gather_binding.py",
        "bytes": 17534,
        "sha256": "617c062b516ecefa5fab0a6ec8f98163a3b13f76896969cb22102f859323b850"
    },
    "carrier_export": {
        "file": "carrier_export.py",
        "bytes": 33129,
        "sha256": "867b8ca6dbd11818edca22d6dc8a0e0671e0855d7d9c7c87ba317e5059868941"
    },
    "cold_image_readiness": {
        "file": "cold_image_readiness.py",
        "bytes": 14496,
        "sha256": "eac159fa9c31f9a0bc600025f27a3e988dd486d1e38497698814f3121399bbd9"
    },
    "semantic_compare": {
        "file": "semantic_compare.py",
        "bytes": 22754,
        "sha256": "c7e1e9d323bb7f35fffa38731a67b0099f173167bcb65d857a7cd6165698ff00"
    },
    "input_domain": {
        "file": "input_domain.py",
        "bytes": 16109,
        "sha256": "c679d873aa45aac4fad553f014e83c8e42a9a458c8189151e9e3695072be8c74"
    }
}


class Refusal(ValueError): pass


def need(value, code):
    if not value: raise Refusal(code)


def sha(raw): return hashlib.sha256(raw).hexdigest()


def eligible(request, capture):
    return (type(request) is dict and getattr(capture, 'native_sha256', None) == KNOWN_MDL and
            request.get('sourceio_revision') == REVISION and type(request.get('scale')) is float and
            request['scale'] == .01905 and request.get('appearance') is None and
            request.get('source_member') is None)


def stamp(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_nlink,
            getattr(info, 'st_file_attributes', 0) & ~0x40000)


def no_alias(path, *, directory=False):
    path = Path(path).absolute()
    need('..' not in path.parts, 'LIVE_PATH_PARENT_TRAVERSAL')
    for ancestor in (path, *path.parents):
        row = ancestor.lstat()
        need(not stat.S_ISLNK(row.st_mode) and not getattr(row, 'st_file_attributes', 0) & 0x400,
             'LIVE_PATH_LINK_OR_REPARSE')
    row = path.lstat()
    need((stat.S_ISDIR(row.st_mode) if directory else stat.S_ISREG(row.st_mode) and row.st_nlink == 1),
         'LIVE_REGULAR_SINGLE_LINK_REQUIRED')
    return path


def read_pin(path, count, digest):
    path = no_alias(path)
    before = path.lstat()
    need(type(count) is int and 0 <= count <= MAX_FILE and before.st_size == count and
         type(digest) is str and len(digest) == 64, 'LIVE_INPUT_SIZE_OR_PIN_SCHEMA')
    with path.open('rb') as stream:
        need(stamp(os.fstat(stream.fileno())) == stamp(before), 'LIVE_INPUT_CHANGED_BEFORE_READ')
        raw = stream.read(count + 1)
        opened = os.fstat(stream.fileno())
    need(len(raw) == count and sha(raw) == digest and
         stamp(before) == stamp(opened) == stamp(path.lstat()), 'LIVE_INPUT_IDENTITY_OR_BYTES_CHANGED')
    return raw, stamp(before)


def load_toolkit():
    """Execute only adjacent literal-hash-authenticated source, with cold aliases."""
    need(all(name not in sys.modules for name in TOOLKIT), 'LIVE_TOOLKIT_MODULE_COLLISION')
    raw = {name: read_pin(HERE / 'deps' / row['file'], row['bytes'], row['sha256'])[0]
           for name, row in TOOLKIT.items()}
    modules = {}
    for name in TOOLKIT:
        module = types.ModuleType(name)
        module.__file__ = str(HERE / 'deps' / TOOLKIT[name]['file'])
        module.__package__ = ''
        modules[name] = module
        sys.modules[name] = module
    for package_name in ('experiments', 'experiments.carrier_input_domain_20261118'):
        need(package_name not in sys.modules, 'LIVE_COLD_GLTF_PARSER_NAMESPACE_REQUIRED')
        package = types.ModuleType(package_name); package.__path__ = [str(HERE / 'deps')]
        package.__package__ = package_name; sys.modules[package_name] = package
    sys.modules['experiments.carrier_input_domain_20261118.semantic_compare'] = modules['semantic_compare']
    order = ('semantic_compare', 'input_domain', 'vvd_normals', 'normal_identity_carrier', 'normal_export_adapter',
             'native_point_expectation', 'weight_policy', 'import_instrumentation',
             'creation_support', 'current_id_ledger', 'material_inspection',
             'export_hook_proposal', 'resource_gate_proposal', 'shared_image_cache_proposal',
             'observer_instrumentation', 'gather_binding', 'carrier_export', 'cold_image_readiness')
    for name in order:
        exec(compile(raw[name], modules[name].__file__, 'exec', dont_inherit=True), modules[name].__dict__)
    need(modules['export_hook_proposal'].shared_images is modules['shared_image_cache_proposal'] and
         modules['shared_image_cache_proposal'].R is modules['resource_gate_proposal'] and
         modules['resource_gate_proposal'].Refusal is modules['export_hook_proposal'].Refusal,
         'LIVE_TOOLKIT_CYCLE_ALIAS_DIFFERS')
    return modules


def prepare_import(request, capture, bpy, content_manager, options, source, resolve_sidecar):
    """Unknown models retain the unchanged bridge call and trigger no new IO."""
    if not eligible(request, capture): return None
    workflow = Workflow(request, capture, bpy, content_manager, options, source, resolve_sidecar)
    workflow.import_native()
    return workflow


class Workflow:
    def __init__(self, request, capture, bpy, content_manager, options, source, resolve_sidecar):
        self.request, self.capture, self.bpy, self.cm, self.options = request, capture, bpy, content_manager, options
        self.source = Path(source)
        self.modules = load_toolkit()
        self.inputs = {}
        self.raw = {}
        paths = dict(mdl=self.source, vvd=resolve_sidecar(self.source, '.vvd'),
                     vtx=resolve_sidecar(self.source, '.dx90.vtx'))
        for name, path in paths.items():
            need(path is not None, 'LIVE_REQUIRED_NATIVE_SIDECAR_MISSING')
            count, digest = NATIVE[name]
            raw, identity = read_pin(path, count, digest)
            self.raw[name] = raw
            self.inputs[name] = (Path(path), identity)
        need(type(capture.raw) is bytes and capture.raw == self.raw['mdl'], 'LIVE_SELECTED_MDL_CAPTURE_DIFFERS')
        self.refs = {name: dict(raw=raw, bytes=len(raw), sha256=NATIVE[name][1]) for name, raw in self.raw.items()}
        native = self.modules['native_point_expectation']
        self.native = native.derive_native_point_rows(self.refs)
        mdl_meta = native._mdl(self.raw['mdl'])
        vvd_meta = native._vvd(self.raw['vvd'], mdl_meta['checksum'])
        self.facts = self.modules['current_id_ledger'].facts_from_independent(
            self.native, mdl_meta, vvd_meta['raw_indices'], native, self.modules['weight_policy'])
        need(len(self.facts) == 2 and set(self.facts) == {'hair.smd', 'Hat.smd'} and
             sum(len(row['ids']) for row in self.facts.values()) == 9661 and
             len(self.native['vertex_groups']) == 69, 'LIVE_EXACT_NATIVE_FAMILY_REQUIRED')
        self.ledger = self.modules['current_id_ledger'].CurrentIDLedger(self.facts)
        self.container = None
        self.export_attempted = False
        self.summary = dict(format='has_live_known_native_normal_bridge_candidate_1',
            status='NATIVE_INPUTS_ADMITTED', live_VMT_pipeline_used=True, saved_B_opened=False,
            original_native_files_written=False, application_adoption_qualified=False,
            generic_source_or_renderer_fidelity_qualified=False)

    def recheck_inputs(self):
        for name, (path, expected) in self.inputs.items():
            raw, identity = read_pin(path, *NATIVE[name])
            need(identity == expected and raw == self.raw[name], 'LIVE_ORIGINAL_NATIVE_CHANGED')

    def snapshot(self, obj, mesh):
        bpy, np = self.bpy, self.np
        need(type(obj) is bpy.types.Object and type(mesh) in (self.FastMesh, bpy.types.Mesh) and
             obj.data is mesh and obj.original is obj and mesh.original is mesh,
             'LIVE_ACTUAL_ORIGINAL_OBJECT_MESH_REQUIRED')
        points, corners = len(mesh.vertices), len(mesh.loops)
        need(0 < points <= 200000 and 0 < corners <= 1000000, 'LIVE_CURRENT_RNA_BUDGET')
        positions, loops = np.empty(points * 3, dtype=np.float32), np.empty(corners, dtype=np.int32)
        mesh.vertices.foreach_get('co', positions); mesh.loops.foreach_get('vertex_index', loops)
        need(bool(np.all(loops >= 0)) and bool(np.all(loops < points)), 'LIVE_LOOP_INDEX_DOMAIN')
        groups = tuple(obj.vertex_groups)
        need(all(type(group.index) is int and group.index == index and type(group.name) is str
                 for index, group in enumerate(groups)), 'LIVE_GROUP_INDEX_ORDER')
        weights = []
        for index, vertex in enumerate(mesh.vertices):
            need(type(vertex.index) is int and vertex.index == index, 'LIVE_VERTEX_INDEX_ORDER')
            weights.append(self.modules['weight_policy'].stored_weight_words(
                [[element.group, element.weight] for element in vertex.groups], len(groups)))
        return dict(positions=positions.tobytes(), loops=loops.tobytes(), groups=tuple(g.name for g in groups),
                    weights=tuple(weights), parent=obj.parent)

    def check_native_material_slots(self, obj, mesh, model_name):
        """Native face ordinals determine slots; live shader edits do not rebind IDs."""
        bpy = self.bpy
        raw_faces = self.native['models'][model_name]['materials']
        need(type(raw_faces) is list and 0 < len(raw_faces) <= 1000000 and
             all(type(value) is int and 0 <= value < len(self.mdl.materials) for value in raw_faces),
             'LIVE_NATIVE_FACE_MATERIAL_DOMAIN')
        raw_slots = sorted(set(raw_faces))
        expected = tuple(self.mdl.materials[index].bpy_material for index in raw_slots)
        actual = tuple(mesh.materials)
        need(len(actual) == len(expected) and all(type(material) is bpy.types.Material and
             material.original is material and material.library is None and material is wanted
             for material, wanted in zip(actual, expected)), 'LIVE_SOURCE_MATERIAL_SLOT_REFERENCE_DIFFERS')
        object_slots = tuple(obj.material_slots)
        need(len(object_slots) == len(actual) and all(type(slot) is bpy.types.MaterialSlot and
             slot.id_data is obj and slot.link == 'DATA' and slot.material is material
             for slot, material in zip(object_slots, actual)), 'LIVE_OBJECT_DATA_MATERIAL_SLOT_DIFFERS')
        faces = tuple(mesh.polygons)
        need(len(faces) == len(raw_faces), 'LIVE_NATIVE_FACE_MATERIAL_COUNT_DIFFERS')
        indices = {raw: index for index, raw in enumerate(raw_slots)}
        need(all(type(face) is bpy.types.MeshPolygon and face.id_data is mesh and
             type(face.index) is int and face.index == index and type(face.material_index) is int and
             face.material_index == indices[raw] for index, (face, raw) in enumerate(zip(faces, raw_faces))),
             'LIVE_NATIVE_FACE_MATERIAL_ORDER_DIFFERS')
        return len(raw_slots)

    def import_native(self):
        need(self.container is None, 'LIVE_IMPORT_REPLAY_REFUSED')
        import numpy as np
        from SourceIO.library.utils import MemoryBuffer
        from SourceIO.library.models.mdl.v49 import MdlV49
        from SourceIO.library.models.vvd import Vvd
        from SourceIO.library.models.vtx import open_vtx
        from SourceIO.library.models.mdl.structs.model import ModelV36Plus
        from SourceIO.blender_bindings.utils.fast_mesh import FastMesh
        self.np, self.FastMesh = np, FastMesh
        class VTXBuffer(MemoryBuffer):
            def seek(self, *args):
                try: return super().seek(*args)
                except BufferError as error: raise struct.error('Bounded Source VTX seek') from error
        mdl = MdlV49.from_buffer(MemoryBuffer(self.raw['mdl']))
        vvd, vtx = Vvd.from_buffer(MemoryBuffer(self.raw['vvd'])), open_vtx(VTXBuffer(self.raw['vtx']))
        need(vtx is not None and mdl.header.checksum == vvd.header.checksum == vtx.header.checksum == self.native['checksum'],
             'LIVE_NATIVE_CHECKSUMS_DIFFER')
        models = {model.name: model for part in mdl.body_parts for model in part.models if model.vertex_count}
        need(set(models) == set(self.facts) and all(type(model) is ModelV36Plus and
             not model.has_flexes and not model.has_eyeballs for model in models.values()) and not vvd.extra_data,
             'LIVE_UNQUALIFIED_MODEL_FEATURES')
        self.mdl = mdl
        original_payloads = {}
        baseline_objects, baseline_meshes = tuple(self.bpy.data.objects), tuple(self.bpy.data.meshes)
        def observe(phase, model, obj, mesh, vertices, mapping):
            need(model.name in models and model is models[model.name] and type(model.vertex_offset) is int and
                 type(model.vertex_count) is int and type(vertices) is np.ndarray and
                 len(vertices) == len(self.facts[model.name]['ids']) and type(mapping) is list and
                 len(mapping) == len(vertices) and all(type(value) is np.uint32 and value.ndim == 0 for value in mapping),
                 'LIVE_TYPED_NATIVE_MAPPING_REQUIRED')
            need(all(obj is not prior for prior in baseline_objects) and all(mesh is not prior for prior in baseline_meshes),
                 'LIVE_REUSED_PREEXISTING_OBJECT_OR_MESH')
            if phase == 'before_setter':
                need(model.name not in original_payloads, 'LIVE_LOGICAL_CREATION_REPLAY')
                original_payloads[model.name] = vertices, mapping
            need(original_payloads[model.name][0] is vertices and original_payloads[model.name][1] is mapping,
                 'LIVE_SELECTED_VVD_REFERENCE_CHANGED')
            payload = {}
            for key, field, scalar in (('positions', 'vertex', np.float32), ('normals', 'normal', np.float32),
                                        ('bones', 'bone_id', np.uint8), ('weights', 'weight', np.float32)):
                value = vertices[field]
                need(type(value) is np.ndarray and value.dtype == np.dtype(scalar) and
                     value.ndim == 2 and value.shape == (len(vertices), 3), 'LIVE_TYPED_VVD_FIELD_REQUIRED')
                payload[key] = value.tobytes(order='C')
            self.ledger.observe(phase, model, model.name, model.vertex_offset, model.vertex_count, obj, mesh,
                                [value.item() for value in mapping], payload, self.snapshot(obj, mesh))
            if phase in ('before_validate', 'after_validate'):
                self.check_native_material_slots(obj, mesh, model.name)
        importer = importlib.import_module('SourceIO.blender_bindings.models.mdl49.import_mdl')
        source, source_identity = read_pin(Path(importer.__file__), *IMPORTER_PIN)
        original, observed, proof = self.modules['creation_support'].observed_clone(
            importer, source.decode('utf-8'), self.modules['import_instrumentation'], observe)
        need(self.options.scale == .01905 and self.options.import_textures is False, 'LIVE_KNOWN_IMPORT_OPTIONS_REQUIRED')
        container = observed(self.cm, mdl, vtx, vvd, self.options)
        need(importer.import_model is original and not container.physics_objects and not container.attachments,
             'LIVE_ORIGINAL_IMPORTER_OR_CONTAINER_FEATURE_CHANGED')
        need(read_pin(Path(importer.__file__), *IMPORTER_PIN)[1] == source_identity, 'LIVE_IMPORTER_SOURCE_IDENTITY_CHANGED')
        container.mdl = mdl
        self.mdl, self.container = mdl, container
        self.summary['current_native_ids'] = self.ledger.returned(container, [(obj, self.snapshot(obj, obj.data)) for obj in container.objects])
        for name, record in self.ledger.records.items():
            self.check_native_material_slots(record['obj'], record['mesh'], name)
        self.modules['normal_export_adapter'].admit_identity_normal_frame(container)
        self.recheck_inputs()
        self.summary['status'] = 'FRESH_NATIVE_IDS_OBSERVED'
        return container

    def live_resources(self):
        """Inspect existing live VMT nodes/packed PNGs; no fixture or appearance writes."""
        bpy, inspector = self.bpy, self.modules['material_inspection']
        materials = tuple(material.bpy_material for material in self.mdl.materials)
        need(len(materials) == 4 and len({id(value) for value in materials}) == 4,
             'LIVE_FOUR_ACTUAL_NATIVE_MATERIALS_REQUIRED')
        graphs, serial, unique = [], [], []
        for material in materials:
            graph, row = inspector._graph(material, bpy.types)
            graphs.append(graph); serial.append(row)
            for image in graph['images']:
                if all(image is not prior for prior in unique): unique.append(image)
        need(0 < len(unique) <= 128, 'LIVE_REACHED_IMAGE_DOMAIN')
        image_rows, total, decoded = [], 0, 0
        # All encoded lengths and non-ID owner references precede any packed.data read.
        admissions = []
        for image in unique:
            need(type(image) is bpy.types.Image and image.original is image and image.library is None and
                 image.source == 'FILE' and image.type == 'IMAGE', 'LIVE_PACKED_LOCAL_FILE_IMAGE_REQUIRED')
            parts = tuple(image.packed_files)
            need(len(parts) == 1 and type(parts[0]) is bpy.types.ImagePackedFile and
                 type(image.packed_file) is bpy.types.PackedFile, 'LIVE_SINGLE_PACKED_FILE_REQUIRED')
            part, packed = parts[0], image.packed_file
            part_key = inspector._nonid_key(part, bpy.types.ImagePackedFile, image)
            packed_key = inspector._nonid_key(packed, bpy.types.PackedFile, image)
            need(inspector._nonid_key(part.packed_file, bpy.types.PackedFile, image) == packed_key and
                 type(packed.size) is int and 0 < packed.size <= 64*1024*1024, 'LIVE_ENCODED_PACK_BUDGET')
            total += packed.size
            need(total <= 128*1024*1024, 'LIVE_TOTAL_ENCODED_PACK_BUDGET')
            admissions.append((image, part, packed, part_key, packed_key, packed.size))
        for image, part, packed, part_key, packed_key, count in admissions:
            raw = packed.data
            need(type(raw) is bytes and len(raw) == count, 'LIVE_PACKED_BYTE_COPY_DIFFERS')
            width, height = inspector._png(raw)
            decoded += width * height * 16
            need(decoded <= 128*1024*1024, 'LIVE_PROSPECTIVE_RGBA_BUDGET')
            image_rows.append(dict(image=image, packed_part=part, packed=packed, name=image.name,
                filepath=image.filepath, encoded_bytes=count, encoded_sha256=sha(raw), width=width, height=height,
                packed_part_key=part_key, packed_key=packed_key))
        metadata = tuple(self.modules['cold_image_readiness']._structure(row, bpy.types, inspector)['metadata']
                         for row in image_rows)
        return dict(materials=materials, graphs=tuple(graphs), serial=tuple(serial), images=tuple(image_rows),
                    image_metadata=metadata, libraries=tuple(bpy.data.libraries))

    def recheck_live_resources(self, private):
        bpy, inspector = self.bpy, self.modules['material_inspection']
        need(len(tuple(bpy.data.libraries)) == len(private['libraries']) and all(
             a is b for a, b in zip(tuple(bpy.data.libraries), private['libraries'])), 'LIVE_LIBRARY_DOMAIN_CHANGED')
        for material, prior, expected in zip(private['materials'], private['graphs'], private['serial']):
            actual, serial = inspector._graph(material, bpy.types)
            need(actual['tree'] is prior['tree'] and serial == expected and
                 all(actual[key] == prior[key] for key in ('node_keys', 'link_keys', 'edge_keys')) and
                 len(actual['images']) == len(prior['images']) and all(a is b for a, b in zip(actual['images'], prior['images'])),
                 'LIVE_SHADER_OR_RESOURCE_REFERENCE_CHANGED')
        for row, expected_metadata in zip(private['images'], private['image_metadata']):
            current = self.modules['cold_image_readiness']._structure(row, bpy.types, inspector)
            need(current['metadata'] == expected_metadata, 'LIVE_IMAGE_METADATA_CHANGED')
            image, count = row['image'], row['encoded_bytes']
            need(len(image.packed_files) == 1 and inspector._nonid_key(tuple(image.packed_files)[0], bpy.types.ImagePackedFile, image) == row['packed_part_key'] and
                 inspector._nonid_key(image.packed_file, bpy.types.PackedFile, image) == row['packed_key'] and
                 image.packed_file.size == count, 'LIVE_PACK_REFERENCE_CHANGED')
            raw = image.packed_file.data
            need(type(raw) is bytes and len(raw) == count and sha(raw) == row['encoded_sha256'], 'LIVE_PACKED_BYTES_CHANGED')

    def export_final(self, out, raw_observation, bone_module):
        """One ordinary export, exact NORMAL-only derivative, final sidecar binding."""
        need(not self.export_attempted and raw_observation is not None and raw_observation.capture is self.capture,
             'LIVE_SINGLE_EXPORT_AND_NATIVE_BONE_OBSERVATION_REQUIRED')
        self.export_attempted = True
        self.recheck_inputs(); raw_observation.recheck()
        for name, record in self.ledger.records.items():
            self.check_native_material_slots(record['obj'], record['mesh'], name)
        adapter = self.modules['normal_export_adapter']
        frame = adapter.admit_identity_normal_frame(self.container)
        private = self.live_resources()
        tickets, readiness = self.modules['cold_image_readiness'].acquire_packed_png_buffers(
            self.bpy, private['images'], self.modules['material_inspection'])
        self.recheck_live_resources(private)
        hook, resources_module, carrier = (self.modules[name] for name in
            ('export_hook_proposal', 'resource_gate_proposal', 'carrier_export'))
        addon = importlib.import_module('io_scene_gltf2')
        modules = {key: importlib.import_module('io_scene_gltf2' if key == 'addon' else
                   'io_scene_gltf2.' + relative[:-3].replace('/', '.')) for key, (relative, _digest) in hook.PINS.items()}
        binary = importlib.import_module('io_scene_gltf2.io.exp.binary_data')
        surface = hook.PinnedSurface(modules, self.modules['observer_instrumentation'], self.modules['gather_binding'],
            shared_binary_module=binary, empty_material_extension_module=modules['exporter'].gltf2_io_extensions)
        resources = resources_module.SimplePackedResources(private['materials'], tickets, self.bpy.types,
            modules['search'], modules['encode'], modules['gltf'], allow_shared_images=True,
            empty_material_extension_profile=surface.empty_material_extension_profile)
        counts = {name: len(set(self.native['models'][name]['materials'])) for name in self.facts}
        scene = carrier.CarrierScene(self.bpy, self.np, self.container, self.ledger, self.facts, self.snapshot, counts)
        raw_path, final_path = Path(out) / 'carrier.glb', Path(out) / 'scene.glb'
        carrier.fresh_owned_carrier_path(raw_path, Path(out))
        kwargs, observed_options = carrier.operator_profile(raw_path)
        kwargs.update(bone_module.EXPLICIT_KWARGS)
        combined = adapter.compose_session_class(hook, bone_module.ObservedCollector)
        session = None
        try:
            scene.install()
            session = combined(surface, scene.admissions(), self.np, resources, scene.point_admission, observed_options,
                bone_proof=raw_observation.proof, exporter_source_pins=dict(bone_module.C.EXPORTER_PINS))
            with session.install(addon, tuple(self.bpy.context.preferences.addons.keys())):
                result = self.bpy.ops.export_scene.gltf(**kwargs)
                need(type(result) is set and result == {'FINISHED'}, 'LIVE_ORDINARY_EXPORT_NOT_FINISHED')
            raw = carrier.read_owned_carrier(raw_path, Path(out))
            relation, observed = session.finish(raw, sha(raw))
            self.recheck_live_resources(private)
            source = self.modules['normal_identity_carrier'].source_from_vvd(
                self.raw['vvd'], NATIVE['vvd'][1], self.native['checksum'])
            expected_ids = [identifier + 1 for fact in self.facts.values() for identifier in fact['ids']]
            final, finalization, rebound = adapter.finalize_native_normals(raw,
                correction_module=self.modules['normal_identity_carrier'], native=source, carrier_sha256=sha(raw),
                expected_source_ids=expected_ids, independent_relation=relation, axes=(1, 3, -2),
                expected_vvd_sha256=NATIVE['vvd'][1], bone_collector=types.SimpleNamespace(finish=session.finish_bones))
            need(not final_path.exists() and not final_path.is_symlink(), 'LIVE_FINAL_OUTPUT_EXISTS')
            no_alias(final_path.parent, directory=True)
            with final_path.open('xb') as stream:
                need(stream.write(final) == len(final), 'LIVE_FINAL_SHORT_WRITE')
                stream.flush()
            read_pin(final_path, len(final), sha(final))
            self.recheck_inputs(); raw_observation.recheck()
            def identity_reader(path, expected):
                count = len(raw) if Path(path) == raw_path else len(final)
                read_pin(path, count, expected)
                return path, expected
            publication = adapter.make_publication_state(raw_observation, rebound, finalization,
                raw_path=raw_path, final_path=final_path, identity_reader=identity_reader)
            self.summary.update(status='LIVE_NORMAL_DERIVATIVE_CANDIDATE_COMPLETE', source_models=2,
                source_points=9661, live_materials=len(private['materials']), reached_images=len(private['images']),
                buffer_readiness=readiness, export_observation=observed, normal_finalization=finalization,
                final_glb_sha256=sha(final), one_operator_invocation=True, raw_carrier_retained=True,
                metadata_writes_to_live_materials=False)
            return publication, dict(self.summary)
        finally:
            primary = sys.exc_info()[1]
            try:
                scene.close()
                self.recheck_live_resources(private)
                self.recheck_inputs()
            except BaseException:
                if primary is None: raise
                self.summary['secondary_restoration_or_preservation_failure'] = True
