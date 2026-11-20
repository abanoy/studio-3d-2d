"""UNRUN future Root-only Blender probe: fresh SourceIO IDs/current RNA weights.

No B open, library append, exporter, image pixels, carrier, blend save or Studio.
Import is stdlib only. main() requires an authenticated fresh Root lease; Root
alone owns launching/placement/retained Popen/job closure after the full suite.
"""
import argparse
import ast
import copy
import datetime
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import struct
import sys
import tempfile
import types
from contextlib import ExitStack

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
SOURCEIO = Path(r'C:\a\Programming\cloudflare\has-neon-review-20261116-c2d52ff\output\dependencies\sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647')
BLENDER = Path(r'C:\Program Files\Blender Foundation\Blender 5.1\blender.exe')
BLENDER_PIN = (108687824, '1e6624af112b3c936f4b038b025ebd2bf00ae72c4b62881a6787166d71c58fa5')
JOIN = PROJECT / 'experiments/source_saved_weight_join_20261120/join_saved_weights.py'
JOIN_PIN = (20860, 'f838e0d893969aa1ad884a1c1d92e28ba019454f313632855f2a33c55fc3415c')
NATIVE = PROJECT / 'experiments/native_point_expectation_bone_state_fix_20261118/native_point_expectation.py'
NATIVE_PIN = (27615, 'cbb4eca98a6cf5045211dc10bd8e060b79492ec306d61a4d29679fc0d5cc184d')
INSTRUMENTATION = PROJECT / 'experiments/normal_setter_boundary_sentinel_20261117/instrumentation.py'
INSTRUMENTATION_PIN = (3306, '361fcad3dbff79bfd5367cd71ac5a769fc8155d6f38a1b061d5ce6e631f5a895')
SENTINEL = PROJECT / 'experiments/normal_setter_boundary_sentinel_20261117/setter_probe.py'
SENTINEL_PIN = (17989, '034122697e8fa0e7a855ea42b51eddc351b647ae5f7641cad8d02994a51fc3c3')
IMPORTER = SOURCEIO / 'blender_bindings/models/mdl49/import_mdl.py'
IMPORTER_PIN = (12880, '173a34ecae50e0b7a9d467908f238c02d5d7e19df3c7f52387534914d703233b')
APPROVED_LOCK = PROJECT / 'experiments/replay_audio_fix_20261115/builder/input-lock.json'
APPROVED_LOCK_SHA = '3bb7c2ce75f55dcb53143aab0df5ab8b39c68180617092664a579126fb09cfb6'
MODELS = {'hair.smd': (8011, 34332), 'Hat.smd': (1650, 8370)}
MAX_FILE = 128 * 1024 * 1024


class ControlledRefusal(ValueError):
    pass


def need(ok, code):
    if not ok:
        raise ControlledRefusal(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def stamp(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)


def safe(path):
    path = Path(path).absolute()
    need('..' not in path.parts, 'PATH_PARENT_TRAVERSAL')
    for parent in (path, *path.parents):
        info = parent.lstat()
        need(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400,
             'PATH_LINK_OR_REPARSE')
    return path


def pinned_read(path, count, digest):
    path = safe(path)
    before = path.stat()
    need(stat.S_ISREG(before.st_mode) and type(count) is int and 0 <= count <= MAX_FILE and before.st_size == count and
         type(digest) is str and len(digest) == 64 and all(c in '0123456789abcdef' for c in digest), 'PIN_SCHEMA_OR_SIZE')
    with path.open('rb') as stream:
        need(stamp(os.fstat(stream.fileno())) == stamp(before), 'INPUT_CHANGED_BEFORE_OPEN')
        raw = stream.read(count + 1)
        opened = os.fstat(stream.fileno())
    need(stamp(before) == stamp(opened) == stamp(path.stat()) and len(raw) == count and sha(raw) == digest,
         'INPUT_HASH_SIZE_OR_STAMP_DIFFERS')
    return raw, stamp(before)


def strict_json(raw):
    def pairs(items):
        row = {}
        for key, value in items:
            need(key not in row, 'DUPLICATE_JSON_KEY')
            row[key] = value
        return row
    def invalid(_value): raise ControlledRefusal('NONFINITE_JSON')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)


def loaded_source(name, path, raw):
    need(name not in sys.modules, 'HELPER_MODULE_COLLISION')
    module = types.ModuleType(name)
    module.__file__ = str(path)
    module.__package__ = ''
    sys.modules[name] = module
    exec(compile(raw, str(path), 'exec', dont_inherit=True), module.__dict__)
    return module


def request_read(path, expected_sha):
    path = safe(path)
    need(path.is_relative_to(PROJECT / 'output') and path.stat().st_size <= 2 * 1024 * 1024,
         'FRESH_ROOT_LEASE_PATH_OR_SIZE')
    raw, _ = pinned_read(path, path.stat().st_size, expected_sha)
    lease = strict_json(raw)
    need(lease.get('format') == 'has_fresh_current_native_id_request_1' and
         lease.get('phase') == 'ROOT_APPROVED_AFTER_FULL_PHYSICALLY_CLOSED' and
         lease.get('private_arrays_public') is False, 'ROOT_LEASE_SCOPE')
    now = datetime.datetime.now(datetime.timezone.utc)
    created = datetime.datetime.fromisoformat(lease['created_utc'])
    expiry = datetime.datetime.fromisoformat(lease['expires_utc'])
    need(created.tzinfo is not None and expiry.tzinfo is not None and created <= now < expiry and
         datetime.timedelta(0) < expiry - created <= datetime.timedelta(minutes=30), 'ROOT_LEASE_NOT_FRESH')
    gate = lease['source_context']
    need(gate.get('full_suite_passed') is True and gate.get('full_job_physically_closed') is True and
         gate.get('exclusive_runtime_lease') is True and type(gate.get('observed_owned_processes')) is int and
         gate['observed_owned_processes'] == 0 and type(gate.get('functional_file_count')) is int and
         gate['functional_file_count'] == 1061, 'ROOT_BOUND_FULL_CLOSURE_ATTESTATION')
    need(type(lease.get('files')) is dict and set(lease['files']) == {
        'probe', 'ledger', 'full_state', 'graphics_release', 'physical_closure', 'approved_runtime_lock'}, 'ROOT_LEASE_FILES')
    need(type(lease.get('sourceio_catalogue')) is dict and len(lease['sourceio_catalogue']) == 574,
         'COMPLETE_SOURCEIO574_CATALOGUE_REQUIRED')
    need(lease.get('sourceio_root') == str(SOURCEIO), 'APPROVED_SOURCEIO_ROOT_DIFFERS')
    stage = safe(lease['owned_stage'])
    need(stage.is_relative_to(PROJECT / 'output') and stage != HERE and stage.is_dir(), 'OWNED_STAGE_REQUIRED')
    output = safe(lease['owned_output'])
    need(output.is_relative_to(stage) and output.is_dir() and
         not (output / 'PUBLIC_CURRENT_IDS.json').exists() and not (output / 'PLACEMENT_CURRENT_IDS.json').exists(),
         'FRESH_OWNED_RESULT_REQUIRED')
    temporary = safe(lease['owned_temp'])
    need(temporary.is_relative_to(stage) and temporary.is_dir() and
         safe(os.environ.get('TEMP', '')) == temporary and safe(os.environ.get('TMP', '')) == temporary and
         safe(tempfile.gettempdir()) == temporary, 'OWNED_TEMP_CONTEXT_REQUIRED')
    return lease, output


def verify_file_table(lease, reads):
    result = {}
    for role, row in lease['files'].items():
        need(type(row) is dict and set(row) == {'path', 'bytes', 'sha256'}, 'LEASE_FILE_SCHEMA')
        path = safe(row['path'])
        if role == 'approved_runtime_lock':
            need(path == APPROVED_LOCK and row['sha256'] == APPROVED_LOCK_SHA, 'IMMUTABLE_APPROVED_LOCK_DIFFERS')
        raw, before = pinned_read(path, row['bytes'], row['sha256'])
        reads[role] = (path, row['bytes'], row['sha256'], before)
        result[role] = raw
    need(Path(lease['files']['probe']['path']) == Path(__file__).absolute() and
         Path(lease['files']['ledger']['path']) == HERE / 'current_id_ledger.py', 'CURRENT_PREP_SOURCE_ALIASES')
    for key, role in (('full_state_sha256', 'full_state'), ('graphics_release_sha256', 'graphics_release'),
                      ('physical_closure_sha256', 'physical_closure')):
        need(lease['source_context'].get(key) == lease['files'][role]['sha256'], 'ROOT_CONTEXT_RECEIPT_HASH_ALIAS')
    # Physical closure was checked by Root before launch and is hash-bound here.
    # This worker intentionally performs no process/Git probe and cannot itself
    # certify the outer job's subsequent closure. Root must combine both receipts.
    return result


def sourceio_file_names():
    actual_names = set()
    for path in SOURCEIO.rglob('*'):
        relative = path.relative_to(SOURCEIO)
        safe(path)
        if path.is_file():
            actual_names.add(relative.as_posix())
            need(len(actual_names) <= 574, 'EXTRA_SOURCEIO_FILE_DOMAIN')
    return actual_names


def sourceio_catalogue(lease, reads, lock):
    expected = lease['sourceio_catalogue']
    trusted = lock['sourceio_files']
    need(len(trusted) == 574 and len(lock['runtime_executables']) == 6 and len(lock['exporter_noncache_sources']) == 120 and
         expected == {name: {'bytes': row['bytes'], 'sha256': row['sha256']} for name, row in trusted.items()},
         'REQUEST_SOURCEIO_CATALOGUE_NOT_IMMUTABLE_LOCK_PROJECTION')
    actual_names = sourceio_file_names()
    need(actual_names == set(expected), 'SOURCEIO_COMPLETE_NONCACHE_FILE_DOMAIN')
    for relative, row in expected.items():
        need(type(relative) is str and not Path(relative).is_absolute() and not Path(relative).drive and '..' not in Path(relative).parts and
             type(row) is dict and set(row) == {'bytes', 'sha256'}, 'SOURCEIO_CATALOGUE_SCHEMA')
        path = SOURCEIO / relative
        _raw, before = pinned_read(path, row['bytes'], row['sha256'])
        need(before[3] == trusted[relative]['mtime_ns'], 'SOURCEIO_IMMUTABLE_LOCK_NSMTIME_DIFFERS')
        reads['sourceio/' + relative] = (path, row['bytes'], row['sha256'], before)


def observed_clone(module, source, instrumentation, callback):
    original = module.import_model
    need(type(original) is types.FunctionType and original.__globals__ is module.__dict__ and
         not original.__code__.co_freevars and original.__code__.co_filename == module.__file__, 'ACTUAL_PLAIN_IMPORTER_FUNCTION')
    definitions = [node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef) and node.name == 'import_model']
    need(len(definitions) == 1 and not definitions[0].decorator_list, 'PINNED_IMPORTER_DEFINITION')
    clean_namespace = dict(module.__dict__)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(definitions[0])], type_ignores=[])),
                 module.__file__, 'exec', dont_inherit=True), clean_namespace)
    need(original.__code__ == clean_namespace['import_model'].__code__, 'IMPORTER_RUNTIME_CODE_DIFFERS')
    changed, proof = instrumentation.observed_import_function(source)
    need(proof == {'setter_sites': 1, 'validate_sites': 1, 'observer_calls': 4, 'original_function_AST_restored': True},
         'IMPORTER_OBSERVER_AST_INVERSE')
    namespace = dict(module.__dict__)
    need(instrumentation.CALLBACK not in namespace, 'IMPORTER_OBSERVER_GLOBAL_COLLISION')
    namespace[instrumentation.CALLBACK] = callback
    exec(compile(changed, module.__file__, 'exec', dont_inherit=True), namespace)
    return original, namespace['import_model'], proof


def placement_sentinel(source):
    from contextlib import contextmanager
    import ctypes
    from ctypes import wintypes
    definitions = [node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef) and
                   node.name == '_hidden_placement_sentinel']
    need(len(definitions) == 1, 'PINNED_PLACEMENT_SENTINEL_DEFINITION')
    namespace = dict(contextmanager=contextmanager, C=ctypes, W=wintypes, sys=sys)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(definitions[0])], type_ignores=[])),
                 str(SENTINEL), 'exec', dont_inherit=True), namespace)
    return namespace['_hidden_placement_sentinel']


def main():
    arguments = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--request-sha256', required=True)
    args = parser.parse_args(arguments)
    lease, target = request_read(args.request, args.request_sha256)
    reads, phase, result = {}, 'AUTHENTICATE_ROOT_CONTEXT', {
        'format': 'has_fresh_sourceio_current_id_probe_1', 'status': 'REFUSED',
        'historical_saved_B_native_causality_qualified': False, 'B_opened': False,
        'material_library_appended': False, 'exporter_invoked': False, 'carrier_written': False,
        'image_pixels_read': False, 'blend_saved': False, 'native_arrays_published': False,
        'normal_fidelity_qualified': False, 'original_source_normal_threshold': 2e-5,
        'outer_physical_closure_verified_by_worker': False}
    importer_module = original_import = ledger_module = placement = None
    sentinel_stack = ExitStack()
    try:
        _request_raw, request_stamp = pinned_read(args.request, Path(args.request).stat().st_size, args.request_sha256)
        reads['root_request'] = (Path(args.request), len(_request_raw), args.request_sha256, request_stamp)
        buffers = verify_file_table(lease, reads)
        for role, path, pin in (('join_policy', JOIN, JOIN_PIN), ('native_helper', NATIVE, NATIVE_PIN),
                                ('instrumentation', INSTRUMENTATION, INSTRUMENTATION_PIN),
                                ('sentinel_source', SENTINEL, SENTINEL_PIN), ('importer', IMPORTER, IMPORTER_PIN),
                                ('blender_exe', BLENDER, BLENDER_PIN)):
            buffers[role], before = pinned_read(path, *pin)
            reads[role] = (path, *pin, before)
        need(sys.platform == 'win32' and sys.byteorder == 'little' and sys.version_info[:2] == (3, 13), 'PINNED_WINDOWS_PYTHON313_CONTEXT')
        sourceio_catalogue(lease, reads, strict_json(buffers['approved_runtime_lock']))
        policy = loaded_source('current_native_join_policy', JOIN, buffers['join_policy'])
        native_helper = loaded_source('current_native_independent_helper', NATIVE, buffers['native_helper'])
        instrument = loaded_source('current_native_instrumentation', INSTRUMENTATION, buffers['instrumentation'])
        ledger_module = loaded_source('current_native_id_ledger', HERE / 'current_id_ledger.py', buffers['ledger'])
        phase = 'PIN_THREE_STAGED_NATIVE_INPUTS'
        need(type(lease.get('native')) is dict and set(lease['native']) == {'mdl', 'vvd', 'vtx'}, 'EXACT_STAGED_THREE_FILE_FAMILY')
        for role in ('mdl', 'vvd', 'vtx'):
            row = lease['native'][role]
            _relative, count, digest = policy.PINS[role]
            need(type(row) is dict and set(row) == {'path', 'bytes', 'sha256'} and
                 row['bytes'] == count and row['sha256'] == digest, 'STAGED_NATIVE_LITERAL_PIN_DIFFERS')
            path = safe(row['path'])
            need(path.parent == safe(Path(lease['owned_stage']) / 'inputs'), 'STAGED_NATIVE_INPUT_DIRECTORY_DIFFERS')
            buffers[role], before = pinned_read(path, count, digest)
            reads['staged/' + role] = (path, count, digest, before)
        need(type(lease.get('provenance_root_hashes')) is dict and set(lease['provenance_root_hashes']) == {'blend', 'glb', 'parameters'},
             'ROOT_HASH_ONLY_PROVENANCE_REQUIRED')
        for role, row in lease['provenance_root_hashes'].items():
            need(type(row) is dict and set(row) == {'bytes', 'sha256'} and
                 row['bytes'] == policy.PINS[role][1] and row['sha256'] == policy.PINS[role][2], 'ROOT_HASH_ONLY_PROVENANCE_DIFFERS')
        result['root_attested_hash_only_provenance'] = lease['provenance_root_hashes']
        refs = {role: {'raw': buffers[role], 'bytes': policy.PINS[role][1], 'sha256': policy.PINS[role][2]}
                for role in ('mdl', 'vvd', 'vtx')}
        native = native_helper.derive_native_point_rows(refs)
        mdl_meta = native_helper._mdl(buffers['mdl'])
        vvd_meta = native_helper._vvd(buffers['vvd'], mdl_meta['checksum'])
        need(set(native['models']) == set(MODELS) and native['native_lod0_row_count'] == native['native_raw_row_count'] == 9661 and
             len(native['vertex_groups']) == 69, 'EXACT_JUNKO_NATIVE_FAMILY_PROFILE')
        facts = ledger_module.facts_from_independent(native, mdl_meta, vvd_meta['raw_indices'], native_helper, policy)
        ledger = ledger_module.CurrentIDLedger(facts)
        sentinel_factory = placement_sentinel(buffers['sentinel_source'].decode('utf-8'))
        placement = sentinel_stack.enter_context(sentinel_factory())
        phase = 'LOAD_APPROVED_SOURCEIO_WITHOUT_OWNER_SCENE'
        import bpy
        import numpy as np
        need(bpy.app.background is True and bpy.data.filepath == '' and
             bpy.app.online_access is False and bpy.context.preferences.filepaths.use_scripts_auto_execute is False and
             Path(bpy.app.binary_path).resolve() == BLENDER.resolve(), 'FACTORY_BACKGROUND_OFFLINE_NO_AUTOEXEC_BLENDER_CONTEXT')
        need('SourceIO' not in sys.modules, 'SOURCEIO_ALREADY_LOADED')
        os.environ['NO_BPY'] = '1'
        spec = importlib.util.spec_from_file_location('SourceIO', SOURCEIO / '__init__.py', submodule_search_locations=[str(SOURCEIO)])
        package = importlib.util.module_from_spec(spec)
        sys.modules['SourceIO'] = package
        spec.loader.exec_module(package)
        from SourceIO.library.utils import MemoryBuffer
        from SourceIO.library.models.mdl.v49 import MdlV49
        from SourceIO.library.models.vvd import Vvd
        from SourceIO.library.models.vtx import open_vtx
        from SourceIO.blender_bindings.operators.import_settings_base import ModelOptions
        from SourceIO.library.utils.tiny_path import TinyPath
        from SourceIO.blender_bindings.utils.fast_mesh import FastMesh
        importer_module = importlib.import_module('SourceIO.blender_bindings.models.mdl49.import_mdl')
        need(Path(importer_module.__file__).resolve() == IMPORTER.resolve(), 'ACTUAL_APPROVED_IMPORTER_PATH')
        class VTXBuffer(MemoryBuffer):
            def seek(self, *values):
                try: return super().seek(*values)
                except BufferError as error: raise struct.error('Bounded VTX seek') from error
        class NoMaterialIO:
            def __init__(self): self.calls = 0
            def check(self, path):
                need(type(path) is TinyPath and not path.is_absolute() and len(path.as_posix()) <= 1024,
                     'UNEXPECTED_MATERIAL_CHECK_PATH')
                self.calls += 1
                need(self.calls <= 256, 'MATERIAL_CHECK_COUNT_BUDGET')
                return False
            def __getattr__(self, name): raise ControlledRefusal('UNEXPECTED_MATERIAL_IO_METHOD')
        mdl = MdlV49.from_buffer(MemoryBuffer(buffers['mdl']))
        vvd = Vvd.from_buffer(MemoryBuffer(buffers['vvd']))
        vtx = open_vtx(VTXBuffer(buffers['vtx']))
        need(vtx is not None and mdl.header.checksum == vvd.header.checksum == vtx.header.checksum == native['checksum'],
             'SOURCEIO_NATIVE_CHECKSUMS_DIFFER')
        logical = [model for body in mdl.body_parts for model in body.models if model.vertex_count]
        need(len(logical) == 2 and {model.name for model in logical} == set(MODELS) and
             all(not model.has_flexes and not model.has_eyeballs for model in logical) and not vvd.extra_data,
             'SOURCEIO_NO_MORPH_EYEBALL_EXTRAUV_PROFILE')
        options = ModelOptions.default()
        options.scale = .01905
        for name in ('import_textures', 'create_flex_drivers', 'bodygroup_vis_switches', 'bodygroup_grouping',
                     'generate_wrinkle_map_node_group', 'import_physics', 'import_animations', 'import_include_animations',
                     'load_refpose', 'debug_stereo_balance'):
            setattr(options, name, False)
        # Root launched factory startup with no owner file. Delete only these
        # disposable factory objects; no B or user scene is ever loaded/saved.
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        baseline_objects, baseline_meshes, baseline_images = tuple(bpy.data.objects), tuple(bpy.data.meshes), tuple(bpy.data.images)
        original_payload_refs = {}
        def snapshot(obj, mesh):
            need(type(obj) is bpy.types.Object and type(mesh) in (FastMesh, bpy.types.Mesh) and obj.data is mesh and
                 obj.original is obj and mesh.original is mesh, 'ACTUAL_NON_EVALUATED_OBJECT_MESH_REQUIRED')
            points, corners = len(mesh.vertices), len(mesh.loops)
            need(0 < points <= 200_000 and 0 < corners <= 1_000_000, 'CURRENT_RNA_CARDINALITY_BUDGET')
            positions = np.empty(points * 3, dtype=np.float32)
            loops = np.empty(corners, dtype=np.int32)
            mesh.vertices.foreach_get('co', positions)
            mesh.loops.foreach_get('vertex_index', loops)
            need(bool(np.all(loops >= 0)) and bool(np.all(loops < points)), 'CURRENT_RNA_LOOP_INDEX_DOMAIN')
            groups = tuple(obj.vertex_groups)
            need(all(type(group.index) is int and group.index == index and type(group.name) is str
                     for index, group in enumerate(groups)), 'CURRENT_RNA_GROUP_INDEX_ORDER')
            weights = []
            for index, vertex in enumerate(mesh.vertices):
                need(type(vertex.index) is int and vertex.index == index, 'CURRENT_RNA_VERTEX_INDEX_ORDER')
                pairs = [[element.group, element.weight] for element in vertex.groups]
                weights.append(policy.stored_weight_words(pairs, len(groups)))
            return dict(positions=positions.tobytes(), loops=loops.tobytes(), groups=tuple(group.name for group in groups),
                        weights=tuple(weights), parent=obj.parent)
        def observe(phase, model, obj, mesh, vertices, mapping):
            need(model.name in facts and type(model.vertex_offset) is int and type(model.vertex_count) is int and
                 type(vertices) is np.ndarray and len(vertices) == len(facts[model.name]['ids']) and
                 type(mapping) is list and len(mapping) == len(vertices) and
                 all(type(value) is np.uint32 and value.ndim == 0 for value in mapping), 'EXACT_TYPED_SELECTED_MAPPING_REQUIRED')
            need(all(obj is not prior for prior in baseline_objects) and all(mesh is not prior for prior in baseline_meshes),
                 'CREATION_REUSED_PREEXISTING_OBJECT_OR_MESH')
            if phase == 'before_setter':
                need(model.name not in original_payload_refs, 'REPEATED_NATIVE_LOGICAL_CREATION')
                original_payload_refs[model.name] = (vertices, mapping)
            need(model.name in original_payload_refs and original_payload_refs[model.name][0] is vertices and
                 original_payload_refs[model.name][1] is mapping, 'SELECTED_VVD_OR_MAPPING_REFERENCE_CHANGED')
            payload = {}
            for key, field, scalar in (('positions', 'vertex', np.float32), ('normals', 'normal', np.float32),
                                        ('bones', 'bone_id', np.uint8), ('weights', 'weight', np.float32)):
                value = vertices[field]
                need(type(value) is np.ndarray and value.dtype == np.dtype(scalar) and
                     value.ndim == 2 and value.shape == (len(vertices), 3), 'EXACT_TYPED_VVD_SELECTED_FIELD_REQUIRED')
                payload[key] = value.tobytes(order='C')
            ledger.observe(phase, model, model.name, model.vertex_offset, model.vertex_count, obj, mesh,
                           [value.item() for value in mapping], payload, snapshot(obj, mesh))
        original_import, observed, ast_proof = observed_clone(importer_module, buffers['importer'].decode('utf-8'), instrument, observe)
        no_material_io = NoMaterialIO()
        phase = 'ONE_FRESH_SOURCEIO_IMPORT_FOUR_STAGE_RNA_OBSERVATION'
        container = observed(no_material_io, mdl, vtx, vvd, options)
        need(importer_module.import_model is original_import, 'ORIGINAL_IMPORTER_ATTRIBUTE_CHANGED')
        need(not container.physics_objects and not container.attachments and container.master_collection is None,
             'UNQUALIFIED_EXTRA_CONTAINER_FEATURES')
        need(len(bpy.data.images) == len(baseline_images) and
             all(a is b for a, b in zip(tuple(bpy.data.images), baseline_images)), 'IMAGE_DATABLOCK_DOMAIN_CHANGED')
        actual_meshes = [mesh for mesh in bpy.data.meshes if all(mesh is not prior for prior in baseline_meshes)]
        need(len(actual_meshes) == 2 and all(any(mesh is row['mesh'] for row in ledger.records.values()) for mesh in actual_meshes),
             'UNOBSERVED_EXTRA_OR_MISSING_NEW_MESH')
        need(all(not any(name.casefold() == '_has_native_normal_id' for name in obj.data.attributes.keys())
                 for obj in container.objects), 'UNEXPECTED_CARRIER_ATTRIBUTE')
        observation = ledger.returned(container, [(obj, snapshot(obj, obj.data)) for obj in container.objects])
        result.update(status='MATCHED_FRESH_NATIVE_IDS_AND_CURRENT_RNA_WEIGHTS', observation=observation,
                      sourceio_import_executed=True, importer_attribute_never_patched=True,
                      observer_ast_inverse=ast_proof, material_existence_checks=no_material_io.calls,
                      material_files_opened=0, image_datablocks_created=0)
    except BaseException as error:
        result.update(status='REFUSED', phase=phase, error_type=type(error).__name__,
                      error_code=str(error) if isinstance(error, ControlledRefusal) or
                      (ledger_module is not None and isinstance(error, ledger_module.Refusal)) else 'PINNED_API_OR_SCHEMA_REFUSAL')
    finally:
        try:
            sentinel_stack.close()
            need(placement is not None and placement['destroyed_in_finally'] is True and
                 placement['visible_at_creation'] is False and placement['visible_before_destruction'] is False and
                 placement['owned_pid_and_thread_verified'] is True, 'OWNED_HIDDEN_PLACEMENT_SENTINEL_NOT_CLOSED')
            result['hidden_placement_verified'] = True
        except BaseException:
            result['hidden_placement_verified'] = False
            result['status'] = 'REFUSED_PLACEMENT'
        unchanged = True
        for role, (path, count, digest, before) in reads.items():
            try:
                _raw, after = pinned_read(path, count, digest)
                unchanged = unchanged and before == after
            except BaseException:
                unchanged = False
        try:
            unchanged = unchanged and sourceio_file_names() == set(lease['sourceio_catalogue'])
        except BaseException:
            unchanged = False
        original_stable = importer_module is None or original_import is None or importer_module.import_model is original_import
        result['all_read_inputs_hash_size_stamp_unchanged'] = unchanged and len(reads) == 590
        result['original_importer_attribute_unchanged'] = original_stable
        if not result['all_read_inputs_hash_size_stamp_unchanged'] or not original_stable:
            result['status'] = 'REFUSED_PRESERVATION'
        result['input_identities'] = {role: {'bytes': count, 'sha256': digest} for role, (_, count, digest, _) in sorted(reads.items())}
        # Catalogue is a single hash/count summary, avoiding a huge public table.
        source_rows = {key: result['input_identities'].pop(key) for key in list(result['input_identities']) if key.startswith('sourceio/')}
        result['sourceio_catalogue_files'] = len(source_rows)
        result['sourceio_catalogue_summary_sha256'] = sha(json.dumps(source_rows, sort_keys=True, separators=(',', ':')).encode())
        encoded = (json.dumps(result, sort_keys=True, allow_nan=False, indent=2) + '\n').encode()
        need(len(encoded) <= 64 * 1024, 'COMPACT_PUBLIC_REPORT_BUDGET')
        placement_encoded = (json.dumps({'format': 'has_current_native_hidden_placement_1', 'policy': placement,
                                         'worker_verified_hidden_sentinel_closed': result['hidden_placement_verified']},
                                        sort_keys=True, allow_nan=False, indent=2) + '\n').encode()
        with (target / 'PLACEMENT_CURRENT_IDS.json').open('xb') as stream:
            stream.write(placement_encoded)
        with (target / 'PUBLIC_CURRENT_IDS.json').open('xb') as stream:
            stream.write(encoded)
    print('HAS_CURRENT_ID_PROBE ' + json.dumps({'status': result['status']}))
    return 0 if result['status'] == 'MATCHED_FRESH_NATIVE_IDS_AND_CURRENT_RNA_WEIGHTS' else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ControlledRefusal, OSError, ValueError, KeyError, TypeError):
        # No unsanitized private exception values/traceback enter public stdout.
        print('HAS_CURRENT_ID_PROBE {"status":"REFUSED_ROOT_LEASE_OR_PUBLICATION"}')
        raise SystemExit(1)
