"""UNRUN Root-only successor: owned B Materials before fresh current IDs/RNA.

Only owned B Material requests; no B geometry requests/point reads or scene save.
One bounded selected carrier GLB export follows the qualified fresh import.
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
import marshal
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
METADATA = HERE / 'material_metadata.py'
METADATA_PIN = (13818, 'c04c4e20705b490ed7633855b2e3bdde14350adec35c8b2a25afc42b69508395')
BINDING = HERE / 'material_binding.py'
BINDING_PIN = (27946, '0e2b8cae2f376615e6d038c5f888e06aa31f9595345f54863be9a3e3c013afe0')
ENUMERATION = HERE / 'library_enumeration.py'
ENUMERATION_PIN = (18845, '6c3aeff6a56b22a448d3ca093997ca866e76ac6ec2fb3948c811abad9c86f903')
INSPECTION = HERE / 'material_inspection.py'
INSPECTION_PIN = (24579, '5efd488d7912e7b032f5590a85e1a20419913f5f6736d906b126c4e8a6280d17')
OWNED_B_PIN = (2423175, 'ead1f1913812593abd69e353fed375944a15f280738784886fcef7fda3ee65c6')
RESOLVED_PROFILE = HERE / 'resolved_profile.py'
RESOLVED_PIN = (30378, '82359c33b116278fb5f12ad75e49ecdfcda00c7fa2e6d283a5677867438d602f')
CARRIER_MODULES = {
    'export_hook': ('export_hook_proposal.py', 38816, 'ba99e86dedd019fd89457b593ff5540e7ae5a1f5c651c586438b2229535cbcad'),
    'resource_gate': ('resource_gate_proposal.py', 35869, 'bc4fd1ff719e43618cd0984a73fc9c950d502e52c762ac4cb6e042ff1464fba3'),
    'shared_cache': ('shared_image_cache_proposal.py', 23263, 'e903c871d53769d7dfc92e1ecdec75f316cf34ea8e8c5113116861cafefe6c0e'),
    'extract_observer': ('observer_instrumentation.py', 7829, '15145030fab5b662be490e519ff59f870c4e9c0352766ff59bf3da3f12198f7b'),
    'gather_binder': ('gather_binding.py', 17534, '617c062b516ecefa5fab0a6ec8f98163a3b13f76896969cb22102f859323b850'),
    'semantic_compare': ('semantic_compare.py', 22754, 'c7e1e9d323bb7f35fffa38731a67b0099f173167bcb65d857a7cd6165698ff00'),
    'cold_readiness': ('cold_image_readiness.py', 11578, 'dc7b917c78bf808c661c60bb33f437720e0fe787f04f293a8d14924d517d2aff'),
    'carrier_export': ('carrier_export.py', 14661, '3325f52aa43117549af97a196009e65234abb262393242c30e82918b8deec04d'),
}



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
    need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and type(count) is int and 0 <= count <= MAX_FILE and before.st_size == count and
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
    need(lease.get('format') == 'has_fresh_source_native_carrier_export_request_1' and
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
        'probe', 'ledger', 'full_state', 'graphics_release', 'physical_closure', 'approved_runtime_lock',
        'metadata_reader', 'material_binding', 'enumeration_module', 'inspection_module', 'owned_B', 'resolved_profile',
        'qualified_creation', *CARRIER_MODULES}, 'ROOT_LEASE_FILES')
    need(type(lease.get('sourceio_catalogue')) is dict and len(lease['sourceio_catalogue']) == 574,
         'COMPLETE_SOURCEIO574_CATALOGUE_REQUIRED')
    need(lease.get('sourceio_root') == str(SOURCEIO), 'APPROVED_SOURCEIO_ROOT_DIFFERS')
    stage = safe(lease['owned_stage'])
    need(stage.is_relative_to(PROJECT / 'output') and stage != HERE and stage.is_dir(), 'OWNED_STAGE_REQUIRED')
    output = safe(lease['owned_output'])
    need(output.is_relative_to(stage) and output.is_dir() and
         not (output / 'PUBLIC_CARRIER_EXPORT.json').exists() and not (output / 'PLACEMENT_CARRIER_EXPORT.json').exists(),
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
        if role in CARRIER_MODULES:
            name,count,digest=CARRIER_MODULES[role]
            need(path==HERE/name and (row['bytes'],row['sha256'])==(count,digest),'PINNED_CARRIER_HELPER_ALIAS_OR_IDENTITY')
        if role == 'qualified_creation':
            need(path.is_relative_to(PROJECT/'experiments'),'COMMITTED_CREATION_RECEIPT_PATH_REQUIRED')
        if role == 'resolved_profile':
            need(path == RESOLVED_PROFILE and (row['bytes'], row['sha256']) == RESOLVED_PIN,
                 'PINNED_RESOLVED_PROFILE_ALIAS_OR_IDENTITY')
        if role in ('enumeration_module', 'inspection_module', 'owned_B'):
            expected_path, expected_pin = {
                'enumeration_module': (ENUMERATION, ENUMERATION_PIN),
                'inspection_module': (INSPECTION, INSPECTION_PIN),
                'owned_B': (safe(Path(lease['owned_stage']) / 'inputs/material-source.blend'), OWNED_B_PIN)}[role]
            need(path == expected_path and (row['bytes'], row['sha256']) == expected_pin,
                 'PINNED_OWNED_B_OR_INSPECTION_ALIAS_OR_IDENTITY')
        if role in ('metadata_reader', 'material_binding'):
            expected_path, expected_pin = (METADATA, METADATA_PIN) if role == 'metadata_reader' else (BINDING, BINDING_PIN)
            need(path == expected_path and (row['bytes'], row['sha256']) == expected_pin,
                 'PINNED_MATERIAL_HELPER_ALIAS_OR_IDENTITY')
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


def direct_function_code(module_code, name):
    """Extract one direct top-level function code without executing the module."""
    need(type(module_code) is types.CodeType, 'MODULE_CODE_REQUIRED')
    matches = [value for value in module_code.co_consts
               if type(value) is types.CodeType and value.co_name == name]
    need(len(matches) == 1, 'UNIQUE_DIRECT_FUNCTION_CODE_REQUIRED')
    return matches[0]


def code_comparison(left, right):
    """Bounded code-only hashes/counts; never source constants or model data."""
    need(type(left) is types.CodeType and type(right) is types.CodeType, 'CODE_COMPARISON_TYPES')
    fields = ('co_argcount', 'co_posonlyargcount', 'co_kwonlyargcount', 'co_nlocals',
              'co_stacksize', 'co_flags', 'co_firstlineno', 'co_name', 'co_qualname',
              'co_filename', 'co_code', 'co_linetable', 'co_exceptiontable',
              'co_consts', 'co_names', 'co_varnames', 'co_freevars', 'co_cellvars')
    differences = [name for name in fields if getattr(left, name) != getattr(right, name)]
    def scalar(code):
        return dict(code_sha256=sha(code.co_code), linetable_sha256=sha(code.co_linetable),
                    exceptiontable_sha256=sha(code.co_exceptiontable),
                    marshalled_code_sha256=sha(marshal.dumps(code)),
                    flags=code.co_flags, firstlineno=code.co_firstlineno,
                    positional_arguments=code.co_argcount, keyword_arguments=code.co_kwonlyargcount,
                    locals=code.co_nlocals, stacksize=code.co_stacksize,
                    constants=len(code.co_consts), names=len(code.co_names),
                    variable_names=len(code.co_varnames), free_variables=len(code.co_freevars),
                    cell_variables=len(code.co_cellvars))
    return dict(complete_code_equal=left == right, differing_fields=differences,
                left=scalar(left), right=scalar(right))


def observed_clone(module, source, instrumentation, callback, diagnostics=None):
    original = module.import_model
    need(type(original) is types.FunctionType and original.__globals__ is module.__dict__ and
         not original.__code__.co_freevars and original.__code__.co_filename == module.__file__, 'ACTUAL_PLAIN_IMPORTER_FUNCTION')
    full_ast = ast.parse(source, filename=module.__file__)
    definitions = [node for node in full_ast.body if isinstance(node, ast.FunctionDef) and node.name == 'import_model']
    need(len(definitions) == 1 and not definitions[0].decorator_list, 'PINNED_IMPORTER_DEFINITION')
    # SourceFileLoader compiles the ENTIRE raw module with dont_inherit=True and
    # optimize=-1. An isolated FunctionDef is not its compilation context: Root
    # proved different code/exception/line tables on this exact173a source even
    # in plain CPython313, without importing SourceIO or Blender. No module code
    # is executed here, and complete code-object equality remains mandatory.
    raw_code = compile(source.encode('utf-8'), module.__file__, 'exec', dont_inherit=True, optimize=-1)
    expected = direct_function_code(raw_code, 'import_model')
    full_ast_code = direct_function_code(compile(copy.deepcopy(full_ast), module.__file__, 'exec',
                                                dont_inherit=True, optimize=-1), 'import_model')
    isolated_code = direct_function_code(compile(ast.fix_missing_locations(ast.Module(
        body=[copy.deepcopy(definitions[0])], type_ignores=[])), module.__file__, 'exec',
        dont_inherit=True, optimize=-1), 'import_model')
    attestation = dict(format='has_full_module_importer_code_attestation_1',
                       source_sha256=sha(source.encode('utf-8')),
                       python_version=sys.version, optimize=sys.flags.optimize,
                       dont_write_bytecode=sys.dont_write_bytecode,
                       pycache_prefix_set=sys.pycache_prefix is not None,
                       loader_type=type(getattr(module, '__loader__', None)).__module__ + '.' +
                                   type(getattr(module, '__loader__', None)).__qualname__,
                       original_vs_full_source=code_comparison(original.__code__, expected),
                       raw_full_source_vs_full_AST=code_comparison(expected, full_ast_code),
                       full_source_vs_isolated_AST=code_comparison(expected, isolated_code),
                       module_top_level_executed_for_clone=False,
                       function_annotations_reevaluated=False,
                       original_module_attribute_patched=False)
    if diagnostics is not None:
        need(type(diagnostics) is dict, 'BOUNDED_DIAGNOSTIC_CONTAINER')
        diagnostics['importer_code_attestation'] = attestation
    need(original.__code__ == expected, 'IMPORTER_RUNTIME_FULL_MODULE_CODE_DIFFERS')
    need(full_ast_code == expected, 'FULL_SOURCE_AST_COMPILATION_DIFFERS')
    changed, proof = instrumentation.observed_import_function(source)
    need(proof == {'setter_sites': 1, 'validate_sites': 1, 'observer_calls': 4, 'original_function_AST_restored': True},
         'IMPORTER_OBSERVER_AST_INVERSE')
    namespace = dict(module.__dict__)
    need(instrumentation.CALLBACK not in namespace, 'IMPORTER_OBSERVER_GLOBAL_COLLISION')
    namespace[instrumentation.CALLBACK] = callback
    need(type(changed) is ast.Module and len(changed.body) == 1 and
         isinstance(changed.body[0], ast.FunctionDef) and changed.body[0].name == 'import_model',
         'EXACT_OBSERVED_FUNCTION_AST_REQUIRED')
    observed_ast = copy.deepcopy(full_ast)
    slots = [index for index, node in enumerate(observed_ast.body)
             if isinstance(node, ast.FunctionDef) and node.name == 'import_model']
    need(len(slots) == 1, 'UNIQUE_OBSERVED_FULL_MODULE_SLOT')
    observed_ast.body[slots[0]] = copy.deepcopy(changed.body[0])
    phases = []
    class RemoveOnlyObserver(ast.NodeTransformer):
        def visit_Expr(self, node):
            call = node.value
            if isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == instrumentation.CALLBACK:
                need(not call.keywords and len(call.args) == 6 and isinstance(call.args[0], ast.Constant) and
                     type(call.args[0].value) is str and all(isinstance(arg, ast.Name) and arg.id == expected_name
                         for arg, expected_name in zip(call.args[1:], ('model', 'mesh_obj', 'mesh_data', 'vertices', 'vtx_vertices'))),
                     'OBSERVED_CALLBACK_SIGNATURE_DIFFERS')
                phases.append(call.args[0].value)
                return None
            return self.generic_visit(node)
    restored_ast = RemoveOnlyObserver().visit(copy.deepcopy(observed_ast))
    need(phases == ['before_setter', 'after_setter', 'before_validate', 'after_validate'] and
         ast.dump(restored_ast, include_attributes=True) == ast.dump(full_ast, include_attributes=True),
         'COMPLETE_MODULE_OBSERVER_AST_INVERSE_DIFFERS')
    transformed = direct_function_code(compile(ast.fix_missing_locations(observed_ast), module.__file__, 'exec',
                                               dont_inherit=True, optimize=-1), 'import_model')
    need(not transformed.co_freevars and transformed.co_name == original.__code__.co_name and
         transformed.co_qualname == original.__code__.co_qualname, 'TRANSFORMED_FUNCTION_IDENTITY_DIFFERS')
    clone = types.FunctionType(transformed, namespace, original.__name__, original.__defaults__)
    clone.__kwdefaults__ = None if original.__kwdefaults__ is None else dict(original.__kwdefaults__)
    clone.__annotations__ = dict(original.__annotations__)
    clone.__dict__.update(original.__dict__)
    clone.__module__ = original.__module__
    clone.__qualname__ = original.__qualname__
    need(module.import_model is original and clone.__code__ is transformed and clone.__globals__ is namespace,
         'ORIGINAL_IMPORTER_OR_PRIVATE_CLONE_CHANGED')
    attestation['complete_module_AST_inverse_exact'] = True
    attestation['observed_function_uses_full_module_compiler_context'] = True
    return original, clone, proof


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


def capture_material_snapshot(mdl, obj, mesh, *, classes, baseline_materials,
                              material_domain, object_domain, mesh_domain, idprop_types):
    """Read genuine parser/RNA references; never mutate or resolve skin semantics.

    main supplies exact imported classes/collections. Synthetic tests may supply
    fabricated classes; those tests cannot qualify an actual Blender boundary.
    All names, indices and reference tuples remain private RAM-only snapshots.
    """
    need(type(classes) is dict and set(classes) == {
        'source_material', 'source_body', 'source_model', 'source_mesh',
        'object', 'mesh', 'material', 'material_slot', 'polygon'}, 'HOST_CLASS_DOMAIN')
    need(type(obj) is classes['object'] and type(mesh) in classes['mesh'] and
         obj.data is mesh and obj.original is obj and mesh.original is mesh and
         sum(item is obj for item in object_domain) == 1 and
         sum(item is mesh for item in mesh_domain) == 1, 'HOST_ACTUAL_OBJECT_MESH_OWNERSHIP')
    source_materials = []
    need(type(mdl.materials) is list and 0 < len(mdl.materials) <= 256, 'HOST_SOURCE_MATERIAL_LIST')
    for source in mdl.materials:
        need(type(source) is classes['source_material'], 'HOST_ACTUAL_SOURCE_MATERIAL_TYPE')
        material = source.bpy_material
        need(type(material) is classes['material'] and material.original is material and
             sum(item is material for item in material_domain) == 1 and
             all(material is not item for item in baseline_materials), 'HOST_FRESH_MATERIAL_OWNERSHIP')
        need(type(material.name) is str and type(material.get('full_path')) is str, 'HOST_MATERIAL_NAME_PATH_TYPES')
        source_materials.append((source, source.name, source.flags, source.used, material,
                                 material.name, material.get('full_path')))
    source_skins = []
    need(type(mdl.skin_groups) is list and 0 < len(mdl.skin_groups) <= 256, 'HOST_SOURCE_SKIN_LIST')
    for group in mdl.skin_groups:
        need(type(group) is list and len(group) <= 256 and
             all(type(item) is classes['source_material'] and any(item is row[0] for row in source_materials)
                 for item in group), 'HOST_ACTUAL_SKIN_MATERIAL_REFERENCES')
        source_skins.append(tuple(group))
    parts = []
    need(type(mdl.body_parts) is list and 0 < len(mdl.body_parts) <= 256, 'HOST_SOURCE_PART_LIST')
    for part in mdl.body_parts:
        need(type(part) is classes['source_body'] and type(part.models) is list and len(part.models) <= 1024,
             'HOST_ACTUAL_PART_MODEL_LIST')
        models = []
        for model in part.models:
            need(type(model) is classes['source_model'] and type(model.meshes) is list and len(model.meshes) <= 65536,
                 'HOST_ACTUAL_MODEL_MESH_LIST')
            source_meshes = []
            for source_mesh in model.meshes:
                need(type(source_mesh) is classes['source_mesh'], 'HOST_ACTUAL_SOURCE_MESH_TYPE')
                source_meshes.append((source_mesh, source_mesh.material_index,
                                      source_mesh.vertex_index_start, source_mesh.vertex_count))
            models.append((model, model.name, model.vertex_offset, model.vertex_count, tuple(source_meshes)))
        parts.append((part, part.name, tuple(models)))
    slots = tuple(mesh.materials)
    need(len(slots) <= 256 and all(type(item) is classes['material'] for item in slots), 'HOST_MESH_SLOT_TYPES')
    object_slots = []
    for slot in obj.material_slots:
        need(type(slot) is classes['material_slot'] and slot.id_data is obj and slot.link == 'DATA' and
             type(slot.material) is classes['material'], 'HOST_DATA_LINKED_OBJECT_SLOT')
        object_slots.append(slot.material)
    faces = []
    need(len(mesh.polygons) <= 1_000_000, 'HOST_FACE_BUDGET')
    for polygon in mesh.polygons:
        need(type(polygon) is classes['polygon'] and polygon.id_data is mesh, 'HOST_ACTUAL_POLYGON_OWNERSHIP')
        faces.append((polygon.index, polygon.loop_start, polygon.loop_total, polygon.material_index))
    raw_skins = obj.get('skin_groups')
    skin_groups = None
    if raw_skins is not None:
        need(type(raw_skins) is idprop_types['group'] and len(raw_skins) <= 256, 'HOST_IDPROPERTY_SKIN_GROUP')
        rows = []
        for key in raw_skins.keys():
            need(type(key) is str and type(raw_skins[key]) in idprop_types['sequences'] and len(raw_skins[key]) <= 256,
                 'HOST_IDPROPERTY_SKIN_ROW')
            rows.append((key, tuple(raw_skins[key])))
        skin_groups = tuple(rows)
    return dict(source_materials=tuple(source_materials), source_skins=tuple(source_skins), source_parts=tuple(parts),
                slots=slots, object_slots=tuple(object_slots), faces=tuple(faces), skin_groups=skin_groups,
                active_skin=obj.get('active_skin'), model_type=obj.get('model_type'))


def select_owned_native_names(metadata, available):
    need(type(metadata) is dict and metadata.get('format') == 'has_private_mdl49_material_skin_metadata_candidate_1' and
         type(metadata.get('metadata')) is dict, 'NATIVE_MATERIAL_METADATA_REQUIRED')
    rows = metadata['metadata'].get('materials')
    need(type(rows) is list and len(rows) == 4 and all(type(row) is dict and type(row.get('index')) is int and
         row['index'] == index and type(row.get('name')) is str and 0 < len(row['name']) <= 256
         for index, row in enumerate(rows)), 'FOUR_ORDERED_NATIVE_NAMES_REQUIRED')
    names = tuple(row['name'] for row in rows)
    need(len(set(names)) == 4 and type(available) is tuple and 4 <= len(available) <= 256 and
         all(type(name) is str and 0 < len(name) <= 1024 for name in available) and
         len(set(available)) == len(available) and all(available.count(name) == 1 for name in names),
         'UNIQUE_NATIVE_NAME_SUBSET_REQUIRED')
    return names


def admit_existing_materials(bpy, materials, names, tiny_path_type):
    need(type(materials) is tuple and type(names) is tuple and len(materials) == len(names) == 4 and
         len({id(value) for value in materials}) == 4 and len(set(names)) == 4, 'EXACT_FOUR_OWNED_MATERIAL_REFS')
    domain = tuple(bpy.data.materials)
    need(4 <= len(domain) <= 256 and all(type(value) is bpy.types.Material for value in domain),
         'BOUNDED_ACTUAL_MATERIAL_DOMAIN')
    for material, name in zip(materials, names):
        need(type(name) is str and 0 < len(name) <= 256 and type(material) is bpy.types.Material and
             material.original is material and material.library is None and material.name == name and
             sum(value is material for value in domain) == 1, 'EXACT_LOCAL_NATIVE_NAMED_B_MATERIAL')
        expected = name.lstrip('/').casefold()
        need(type(material.get('full_path')) is str and material.get('full_path') == expected,
             'B_MATERIAL_FULL_PATH_DIFFERS_FROM_ORDINARY_IMPORTER')
        candidates = []
        for value in domain:
            path = value.get('full_path', '')
            need(type(path) is str and len(path) <= 4096, 'MATERIAL_LOOKUP_PATH_TYPE_OR_BUDGET')
            if tiny_path_type(path.casefold()) == tiny_path_type(expected): candidates.append(value)
        need(len(candidates) == 1 and candidates[0] is material, 'ORDINARY_IMPORTER_MATERIAL_LOOKUP_AMBIGUOUS')
    return dict(format='has_owned_B_ordinary_material_lookup_preflight_1', materials=4,
                exact_full_path_rule=True, unique_actual_refs=True, material_names_sha256=sha(
                    json.dumps(names,sort_keys=True,ensure_ascii=True,separators=(',',':')).encode()),
                material_renames=0, material_swaps=0, native_imports_before_append=0)


def prepare_owned_materials(bpy, owned_B, metadata, enumeration, inspection, tiny_path_type, result):
    result['owned_B_enumeration_attempted'] = True
    def sink(summary): result['owned_B_enumeration'] = dict(summary)
    observation = enumeration.enumerate_library(bpy, owned_B, summary_sink=sink)
    names = select_owned_native_names(metadata, observation['material_names'])
    result['owned_B_material_append_attempted'] = True
    try:
        private = inspection.inspect_material_library(bpy, owned_B, names, enumeration)
    except inspection.Refusal as error:
        if error.summary is not None: result['owned_B_inspection'] = error.summary
        raise ControlledRefusal('OWNED_B_' + error.code) from error
    result['owned_B_inspection'] = dict(private['summary'])
    result['material_library_appended'] = True
    result['material_resources_loaded'] = True
    need(type(private) is dict and type(private.get('materials')) is tuple and len(private['materials']) == 4,
         'INSPECTOR_RETURNED_MATERIAL_REFS_REQUIRED')
    result['ordinary_importer_material_reuse_preflight'] = admit_existing_materials(
        bpy, private['materials'], names, tiny_path_type)
    private['names'] = names
    private['post_append_images'] = tuple(bpy.data.images)
    private['post_append_libraries'] = tuple(bpy.data.libraries)
    private['library_snapshot'] = (None if private['retained_owned_source_library'] is None else
        inspection._owned_library(private['retained_owned_source_library'], bpy.types, owned_B))
    return private


def recheck_owned_materials(bpy, owned_B, private, inspection, tiny_path_type):
    expected_libraries = private['post_append_libraries']
    need(type(expected_libraries) is tuple and len(bpy.data.libraries) == len(expected_libraries) <= 1,
         'OWNED_B_LIBRARY_DOMAIN_CHANGED_AFTER_IMPORT')
    current_libraries = tuple(bpy.data.libraries)
    need(len(current_libraries) == len(expected_libraries) and all(actual is expected for actual, expected in
         zip(current_libraries, expected_libraries)), 'OWNED_B_LIBRARY_DOMAIN_CHANGED_AFTER_IMPORT')
    admit_existing_materials(bpy, private['materials'], private['names'], tiny_path_type)
    serial = []
    for material, prior in zip(private['materials'], private['graphs']):
        current, row = inspection._graph(material, bpy.types)
        need(current['tree'] is prior['tree'] and all(current[key] == prior[key]
             for key in ('node_keys','link_keys','edge_keys')) and len(current['images']) == len(prior['images']) and
             all(a is b for a,b in zip(current['images'],prior['images'])), 'OWNED_B_GRAPH_REFS_CHANGED_AFTER_IMPORT')
        serial.append(row)
    need(inspection._digest(serial) == private['summary']['graph_metadata_sha256'], 'OWNED_B_GRAPH_METADATA_CHANGED_AFTER_IMPORT')
    images = private['images']
    need(type(images) is tuple and len(images) <= 128, 'OWNED_B_IMAGE_BUDGET')
    packets=[]
    for row in images:
        image=row['image']; parts=tuple(image.packed_files); packed=image.packed_file
        need(image.original is image and image.library is None and image.name==row['name'] and
             image.filepath==row['filepath'] and image.source=='FILE' and image.type=='IMAGE' and len(parts)==1 and
             inspection._nonid_key(parts[0],bpy.types.ImagePackedFile,image)==row['packed_part_key'] and
             inspection._nonid_key(packed,bpy.types.PackedFile,image)==row['packed_key'] and
             inspection._nonid_key(parts[0].packed_file,bpy.types.PackedFile,image)==row['packed_key'] and
             type(packed.size) is int and packed.size==row['encoded_bytes'], 'OWNED_B_PACKED_REFERENCE_CHANGED_AFTER_IMPORT')
        packets.append((packed,row))
    need(sum(row['encoded_bytes'] for _packed,row in packets)<=128*1024*1024 and
         all(33<=row['encoded_bytes']<=64*1024*1024 for _packed,row in packets), 'OWNED_B_PACKED_RECHECK_BUDGET')
    for packed,row in packets:
        raw=packed.data
        need(type(raw) is bytes and len(raw)==row['encoded_bytes'] and sha(raw)==row['encoded_sha256'],
             'OWNED_B_PACKED_BYTES_CHANGED_AFTER_IMPORT')
    prior=private['library_snapshot']
    if prior is not None:
        current=inspection._owned_library(prior['library'],bpy.types,owned_B)
        need(current['library'] is prior['library'] and all(current[key]==prior[key]
             for key in ('pointer','filepath','key')), 'OWNED_B_SOURCE_LIBRARY_CHANGED_AFTER_IMPORT')


def attest_preloaded_resolution(importer, resolver, utilities, tiny_path_type, bpy, reads, result):
    functions = []
    for module, relative, names in (
        (resolver, 'blender_bindings/models/materials.py', ('resolve_model_material','get_model_material_names')),
        (utilities, 'blender_bindings/utils/bpy_utils.py', ('get_or_create_material',))):
        role='sourceio/'+relative
        need(role in reads and safe(module.__file__)==safe(SOURCEIO/relative),'ADMITTED_RESOLUTION_HELPER_PATH_REQUIRED')
        path,count,digest,before=reads[role]
        raw,after=pinned_read(path,count,digest)
        need(after==before,'RESOLUTION_HELPER_SOURCE_STAMP_CHANGED')
        compiled=compile(raw,module.__file__,'exec',dont_inherit=True,optimize=-1)
        for name in names:
            function=vars(module).get(name)
            need(type(function) is types.FunctionType and function.__globals__ is vars(module) and
                 function.__defaults__ is None and function.__kwdefaults__ is None and function.__closure__ is None and
                 function.__code__==direct_function_code(compiled,name),'RESOLUTION_HELPER_RUNTIME_CODE_OR_GLOBALS_DIFFERS')
            functions.append(function)
    resolve,get_names,lookup=functions
    need(vars(importer).get('get_model_material_names') is get_names and
         vars(importer).get('get_or_create_material') is lookup and
         get_names.__globals__.get('resolve_model_material') is resolve and
         resolve.__globals__.get('TinyPath') is tiny_path_type and lookup.__globals__.get('TinyPath') is tiny_path_type and
         lookup.__globals__.get('bpy') is bpy,'ACTUAL_RESOLUTION_HELPER_ALIASES_DIFFER')
    result['preloaded_resolver_runtime_attestation']=dict(format='has_preloaded_material_resolver_runtime_attestation_1',
        complete_module_code_equal=True,actual_globals_and_aliases_equal=True,source_catalogue_helpers=2,
        genuine_functions=3,original_importer_attribute_unchanged=True,no_resolver_replacement=True)
    return resolve,get_names,lookup


def prepare_owned_resolved_materials(bpy, owned_B, native, metadata, mdl, enumeration, inspection,
                                     profile, tiny_path_type, source_material_type, result):
    result['owned_B_enumeration_attempted']=True
    def sink(summary):result['owned_B_enumeration']=dict(summary)
    observed=enumeration.enumerate_library(bpy,owned_B,summary_sink=sink)
    names=select_owned_native_names(metadata,observed['material_names'])
    result['owned_B_material_append_attempted']=True
    try:
        private=inspection.inspect_material_library(bpy,owned_B,names,enumeration)
    except inspection.Refusal as error:
        if error.summary is not None:result['owned_B_inspection']=error.summary
        raise ControlledRefusal('OWNED_B_'+error.code) from error
    result['owned_B_inspection']=dict(private['summary'])
    result['material_library_appended']=result['material_resources_loaded']=True
    need(type(private) is dict and type(private.get('materials')) is tuple and len(private['materials'])==4,
         'INSPECTOR_RETURNED_MATERIAL_REFS_REQUIRED')
    try:
        witness=profile.ResolvedMaterialPaths(native,metadata,mdl,private['materials'],
            source_material_type=source_material_type,material_type=bpy.types.Material,tiny_path_type=tiny_path_type,
            material_domain_supplier=lambda:tuple(bpy.data.materials))
    except profile.ProfileRefusal as error:
        result['native_material_path_witness']=dict(error.summary)
        raise ControlledRefusal(str(error)) from error
    result['native_material_path_witness']=dict(witness.summary)
    result['readonly_preloaded_material_adaptation']=dict(format='has_readonly_preloaded_material_adaptation_1',
        no_metadata_writes=True,no_material_renames=True,no_material_swaps=True,native_imports_before_append=0)
    private['path_witness']=witness
    private['names']=names
    private['post_append_images']=tuple(bpy.data.images)
    private['post_append_libraries']=tuple(bpy.data.libraries)
    private['library_snapshot']=(None if private['retained_owned_source_library'] is None else
        inspection._owned_library(private['retained_owned_source_library'],bpy.types,owned_B))
    return private


def recheck_resolved_material_resources(bpy, owned_B, private, inspection, tiny_path_type):
    expected_libraries = private['post_append_libraries']
    need(type(expected_libraries) is tuple and len(bpy.data.libraries) == len(expected_libraries) <= 1,
         'OWNED_B_LIBRARY_DOMAIN_CHANGED_AFTER_IMPORT')
    current_libraries = tuple(bpy.data.libraries)
    need(len(current_libraries) == len(expected_libraries) and all(actual is expected for actual, expected in
         zip(current_libraries, expected_libraries)), 'OWNED_B_LIBRARY_DOMAIN_CHANGED_AFTER_IMPORT')
    private['path_witness'].check(require_resolution=True)
    serial = []
    for material, prior in zip(private['materials'], private['graphs']):
        current, row = inspection._graph(material, bpy.types)
        need(current['tree'] is prior['tree'] and all(current[key] == prior[key]
             for key in ('node_keys','link_keys','edge_keys')) and len(current['images']) == len(prior['images']) and
             all(a is b for a,b in zip(current['images'],prior['images'])), 'OWNED_B_GRAPH_REFS_CHANGED_AFTER_IMPORT')
        serial.append(row)
    need(inspection._digest(serial) == private['summary']['graph_metadata_sha256'], 'OWNED_B_GRAPH_METADATA_CHANGED_AFTER_IMPORT')
    images = private['images']
    need(type(images) is tuple and len(images) <= 128, 'OWNED_B_IMAGE_BUDGET')
    packets=[]
    for row in images:
        image=row['image']; parts=tuple(image.packed_files); packed=image.packed_file
        need(image.original is image and image.library is None and image.name==row['name'] and
             image.filepath==row['filepath'] and image.source=='FILE' and image.type=='IMAGE' and len(parts)==1 and
             inspection._nonid_key(parts[0],bpy.types.ImagePackedFile,image)==row['packed_part_key'] and
             inspection._nonid_key(packed,bpy.types.PackedFile,image)==row['packed_key'] and
             inspection._nonid_key(parts[0].packed_file,bpy.types.PackedFile,image)==row['packed_key'] and
             type(packed.size) is int and packed.size==row['encoded_bytes'], 'OWNED_B_PACKED_REFERENCE_CHANGED_AFTER_IMPORT')
        packets.append((packed,row))
    need(sum(row['encoded_bytes'] for _packed,row in packets)<=128*1024*1024 and
         all(33<=row['encoded_bytes']<=64*1024*1024 for _packed,row in packets), 'OWNED_B_PACKED_RECHECK_BUDGET')
    for packed,row in packets:
        raw=packed.data
        need(type(raw) is bytes and len(raw)==row['encoded_bytes'] and sha(raw)==row['encoded_sha256'],
             'OWNED_B_PACKED_BYTES_CHANGED_AFTER_IMPORT')
    prior=private['library_snapshot']
    if prior is not None:
        current=inspection._owned_library(prior['library'],bpy.types,owned_B)
        need(current['library'] is prior['library'] and all(current[key]==prior[key]
             for key in ('pointer','filepath','key')), 'OWNED_B_SOURCE_LIBRARY_CHANGED_AFTER_IMPORT')


def validate_qualified_creation(value):
    need(type(value) is dict and value.get('format') == 'has_root_fresh_source_owned_B_resolved_material_creation_run_1' and
         value.get('status') == 'CURRENT_IDS_RNA_WITH_OWNED_B_RESOLVED_MATERIALS_MATCHED',
         'COMMITTED_REAL_MODEL_CREATION_NOT_QUALIFIED')
    for key in ('whole_full_pass_required','private_job_closed','launcher_reaped','hidden_placement_verified',
                'original_and_staged_hash_bytes_nsmtime_unchanged','source_and_head_unchanged',
                'material_library_appended','material_resources_loaded','all_four_source_materials_reuse_admitted_B_refs'):
        need(value.get(key) is True,'QUALIFIED_CREATION_REQUIRED_'+key.upper())
    need(type(value.get('functional_source_count')) is int and value['functional_source_count']==1061 and
         type(value.get('exact_authenticated_reads')) is int and value['exact_authenticated_reads']==596,
         'QUALIFIED_CREATION_SOURCE_AND_INPUT_DOMAIN')
    physical=value.get('fresh_physical_after')
    need(type(physical) is dict and type(physical.get('owned_processes')) is int and physical['owned_processes']==0 and
         physical.get('observer_retained_waited_reaped') is True and physical.get('full_pids_absent') is True,
         'QUALIFIED_CREATION_PHYSICALLY_CLOSED')
    for key in ('historical_saved_B_native_causality_qualified','normal_fidelity_qualified','exporter_qualified',
                'carrier_qualified','non_normal_semantic_equivalence_qualified','application_adoption_qualified',
                'original_B_scene_opened','exporter_invoked','blend_saved','native_arrays_published'):
        need(value.get(key) is False,'QUALIFIED_CREATION_SCOPE_'+key.upper())
    witness=value.get('native_material_path_witness')
    need(type(witness) is dict and witness.get('status')=='RETURNED_BINDING_OBSERVED' and
         witness.get('resolution_complete') is True and witness.get('no_metadata_writes') is True and
         witness.get('no_file_existence_claim') is True,'QUALIFIED_CREATION_NATIVE_PATH_WITNESS')
    return value


def load_carrier_helpers(buffers):
    for name,path in (('experiments',PROJECT/'experiments'),
                      ('experiments.carrier_input_domain_20261118',PROJECT/'experiments/carrier_input_domain_20261118')):
        need(name not in sys.modules,'COLD_CARRIER_NAMESPACE_REQUIRED')
        package=types.ModuleType(name);package.__path__=[str(path)];package.__package__=name;sys.modules[name]=package
    semantic=loaded_source('experiments.carrier_input_domain_20261118.semantic_compare',
        HERE/'semantic_compare.py',buffers['semantic_compare'])
    binder=loaded_source('private_carrier_gather_binding',HERE/'gather_binding.py',buffers['gather_binder'])
    observer=loaded_source('private_carrier_extract_observer',HERE/'observer_instrumentation.py',buffers['extract_observer'])
    # Authenticate all three sources before resolving their deliberate import cycle.
    names_roles=(('export_hook_proposal','export_hook'),('resource_gate_proposal','resource_gate'),
                 ('shared_image_cache_proposal','shared_cache'))
    cyclic={}
    for name,role in names_roles:
        need(name not in sys.modules,'COLD_AUTHENTICATED_CARRIER_MODULE_NAMESPACE_REQUIRED')
        path=HERE/CARRIER_MODULES[role][0]
        spec=importlib.util.spec_from_file_location(name,path)
        module=importlib.util.module_from_spec(spec)
        sys.modules[name]=module
        cyclic[name]=module
    # Hook imports the registered cache module only as an alias; no cache APIs
    # execute at import. Resource can then import completed hook definitions,
    # and cache can import the completed resource module, without loader IO.
    for name,role in names_roles:
        module=cyclic[name]
        exec(compile(buffers[role],module.__file__,'exec',dont_inherit=True),module.__dict__)
    hook=cyclic['export_hook_proposal'];resources=cyclic['resource_gate_proposal']
    cache=cyclic['shared_image_cache_proposal']
    need(hook.shared_images is cache and cache.R is resources and resources.Refusal is hook.Refusal,
         'AUTHENTICATED_CARRIER_CYCLE_ALIAS_DIFFERS')
    cold=loaded_source('private_carrier_cold_readiness',HERE/'cold_image_readiness.py',buffers['cold_readiness'])
    export=loaded_source('private_carrier_export',HERE/'carrier_export.py',buffers['carrier_export'])
    return hook,resources,observer,binder,cold,export


def admit_identity_normal_frame(container):
    identity=tuple(tuple(float(row==column) for column in range(4)) for row in range(4))
    objects=tuple(container.objects)
    need(len(objects)==2 and len({id(obj) for obj in objects})==2,'NORMAL_FRAME_TWO_ACTUAL_OBJECTS_REQUIRED')
    for obj in (*objects,container.armature):
        matrix=tuple(tuple(row) for row in obj.matrix_world)
        need(len(matrix)==4 and all(len(row)==4 for row in matrix) and
             all(type(value) is float for row in matrix for value in row) and matrix==identity,
             'NORMAL_FRAME_NONIDENTITY_WORLD_UNQUALIFIED')
    return dict(format='has_actual_identity_source_to_yup_normal_frame_1',mesh_world_identity=True,
        armature_world_identity=True,mesh_count=2,export_yup=True,export_apply=False,
        signed_axis_permutation=[1,3,-2],
        source_coordinate_policy='sourceio_mdl49_standalone_01905_identity_standard_vtx7_1',
        source_unit_conversion_changed=False,six_foot_normalization_applied=False)


def perform_carrier_export(bpy,np,container,ledger,facts,snapshot,binding,owned_materials,inspection_module,
                           TinyPath,owned_B,target,buffers,result):
    result['normal_transport_frame']=admit_identity_normal_frame(container)
    hook,resources,observer,binder,cold,export=load_carrier_helpers(buffers)
    try:
        tickets,readiness=cold.acquire_packed_png_buffers(bpy,owned_materials['images'],inspection_module)
    except cold.Refusal as error:
        result['bounded_image_buffer_readiness']=dict(error.summary)
        raise ControlledRefusal(str(error)) from error
    recheck_resolved_material_resources(bpy,owned_B,owned_materials,inspection_module,TinyPath)
    result['bounded_image_buffer_readiness']=readiness
    result['image_buffer_getters_used']=readiness['image_buffer_getters_used']
    primitive_counts={name:len(binding.facts['models'][name]['slots']) for name in facts}
    carrier_path=target/'carrier.glb'
    result['exporter_attempted']=True
    try:
        exported=export.export_once(bpy,np,container,ledger,facts,snapshot,primitive_counts,
            owned_materials['materials'],tickets,hook,resources,observer,binder,carrier_path,owned_output=target,activity=result)
    except (hook.Refusal,resources.Refusal,export.Refusal) as error:
        raise ControlledRefusal(str(error)) from error
    recheck_resolved_material_resources(bpy,owned_B,owned_materials,inspection_module,TinyPath)
    result['native_material_path_witness']=dict(owned_materials['path_witness'].summary)
    relation_bytes=exported.pop('private_relation_bytes')
    with (target/'PRIVATE_PRIMITIVE_IDS.json').open('xb') as stream:stream.write(relation_bytes)
    observation=exported['export_observation']
    observation['source_normal_threshold_unchanged']=observation.pop('source_normal_max_error_unchanged')
    observation['source_normal_error_measured']=False
    result['carrier_export']=exported
    result['carrier_written']=True
    result['host_image_pixels_getter_used']=False
    result['C_encoded_pixel_decode_may_have_occurred']=True
    result['C_external_access_absence_proven']=False
    result['status']='MATCHED_FRESH_NATIVE_IDS_OWNED_MATERIALS_AND_CARRIER_EXPORT'


def main():
    arguments = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--request-sha256', required=True)
    args = parser.parse_args(arguments)
    lease, target = request_read(args.request, args.request_sha256)
    reads, phase, result = {}, 'AUTHENTICATE_ROOT_CONTEXT', {
        'format': 'has_fresh_source_native_carrier_export_probe_1', 'status': 'REFUSED',
        'historical_saved_B_native_causality_qualified': False, 'original_B_scene_opened': False,
        'material_library_appended': False, 'exporter_invoked': False, 'carrier_written': False,
        'host_image_pixels_getter_used': False, 'blend_saved': False, 'native_arrays_published': False,
        'normal_fidelity_qualified': False, 'original_source_normal_threshold': 2e-5,
        'outer_physical_closure_verified_by_worker': False}
    importer_module = original_import = ledger_module = binding_module = metadata_module = placement = None
    enumeration_module = inspection_module = None
    sentinel_stack = ExitStack()
    try:
        _request_raw, request_stamp = pinned_read(args.request, Path(args.request).stat().st_size, args.request_sha256)
        reads['root_request'] = (Path(args.request), len(_request_raw), args.request_sha256, request_stamp)
        buffers = verify_file_table(lease, reads)
        validate_qualified_creation(strict_json(buffers['qualified_creation']))
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
        metadata_module = loaded_source('material_binding_native_metadata', METADATA, buffers['metadata_reader'])
        bare_binding_module = loaded_source('material_binding', BINDING, buffers['material_binding'])
        binding_module = loaded_source('fresh_resolved_material_candidate', RESOLVED_PROFILE, buffers['resolved_profile'])
        enumeration_module = loaded_source('combined_owned_B_enumeration', ENUMERATION, buffers['enumeration_module'])
        inspection_module = loaded_source('combined_owned_B_inspection', INSPECTION, buffers['inspection_module'])
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
        material_metadata = metadata_module.derive_material_metadata(refs)
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
        from SourceIO.library.models.mdl.structs.material import MaterialV49
        from SourceIO.library.models.mdl.structs.bodygroup import BodyPart
        from SourceIO.library.models.mdl.structs.model import ModelV36Plus
        from SourceIO.library.models.mdl.structs.mesh import MeshV36Plus
        from idprop.types import IDPropertyGroup, IDPropertyArray
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
        baseline_objects, baseline_meshes = tuple(bpy.data.objects), tuple(bpy.data.meshes)
        baseline_materials = tuple(bpy.data.materials)  # FACTORY, before any B append.
        phase = 'OWNED_B_MATERIALS_BEFORE_NATIVE_IMPORT'
        owned_B = safe(lease['files']['owned_B']['path'])
        owned_materials = prepare_owned_resolved_materials(bpy, owned_B, native, material_metadata, mdl,
            enumeration_module, inspection_module, binding_module, TinyPath, MaterialV49, result)
        baseline_images = owned_materials['post_append_images']  # POST-APPEND; importer must add no Images.
        binding = binding_module.ResolvedMaterialBinding(native, material_metadata,
            witness=owned_materials['path_witness'],
            source_material_type=MaterialV49, source_model_type=ModelV36Plus,
            source_body_type=BodyPart, source_mesh_type=MeshV36Plus,
            object_type=bpy.types.Object, mesh_types=(FastMesh, bpy.types.Mesh), material_type=bpy.types.Material)
        binding_classes = dict(source_material=MaterialV49, source_body=BodyPart,
            source_model=ModelV36Plus, source_mesh=MeshV36Plus, object=bpy.types.Object,
            mesh=(FastMesh, bpy.types.Mesh), material=bpy.types.Material,
            material_slot=bpy.types.MaterialSlot, polygon=bpy.types.MeshPolygon)
        def material_snapshot(obj, mesh):
            return capture_material_snapshot(mdl, obj, mesh, classes=binding_classes,
                baseline_materials=baseline_materials, material_domain=tuple(bpy.data.materials),
                object_domain=tuple(bpy.data.objects), mesh_domain=tuple(bpy.data.meshes),
                idprop_types=dict(group=IDPropertyGroup, sequences=(list, tuple, IDPropertyArray)))
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
            owned_materials['path_witness'].check(require_resolution=True)
            result['native_material_path_witness'] = dict(owned_materials['path_witness'].summary)
            binding.observe(phase, model, obj, mesh, material_snapshot(obj, mesh))
        original_import, observed, ast_proof = observed_clone(importer_module, buffers['importer'].decode('utf-8'), instrument, observe,
                                                            diagnostics=result)
        resolver_module = importlib.import_module('SourceIO.blender_bindings.models.materials')
        utils_module = importlib.import_module('SourceIO.blender_bindings.utils.bpy_utils')
        resolution_functions = attest_preloaded_resolution(importer_module, resolver_module, utils_module,
            TinyPath, bpy, reads, result)
        owned_materials['path_witness'].bind_resolver(*resolution_functions, observed)
        no_material_io = owned_materials['path_witness'].provider
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
        owned_materials['path_witness'].check(require_resolution=True)
        material_observation = binding.returned(container, [(obj, material_snapshot(obj, obj.data)) for obj in container.objects])
        source_bpy_materials = tuple(source.bpy_material for source in mdl.materials)
        need(len(source_bpy_materials) == 4 and all(actual is expected for actual, expected in
             zip(source_bpy_materials, owned_materials['materials'])), 'IMPORTER_DID_NOT_REUSE_ADMITTED_B_MATERIALS')
        recheck_resolved_material_resources(bpy, owned_B, owned_materials, inspection_module, TinyPath)
        result['native_material_path_witness'] = dict(owned_materials['path_witness'].summary)
        attest_preloaded_resolution(importer_module,resolver_module,utils_module,TinyPath,bpy,reads,result)
        result['owned_B_resources_unchanged_after_native_import'] = True
        result['all_four_source_materials_reuse_admitted_B_refs'] = True
        fresh_materials = tuple(item for item in bpy.data.materials if all(item is not before for before in baseline_materials))
        need(len(fresh_materials) == len(source_bpy_materials) and
             all(sum(item is actual for item in fresh_materials) == 1 for actual in source_bpy_materials),
             'UNOBSERVED_EXTRA_OR_MISSING_NEW_MATERIAL')
        result.update(status='MATCHED_FRESH_NATIVE_IDS_OWNED_MATERIALS_AND_CARRIER_EXPORT', observation=observation,
                      material_binding=material_observation, original_current_ID_RNA_controls_retained=True,
                      metadata_candidate_sha256=sha(json.dumps(material_metadata, sort_keys=True, separators=(',', ':')).encode()),
                      inherited_authenticated_reads=590, exact_authenticated_reads=605,
                      resolved_native_default_skin_equivalence_qualified=False,
                      material_resources_loaded=True, material_library_appended=True,
                      B_dependency_closure_qualified=False, owned_B_materials_precede_native_import=True,
                      sourceio_import_executed=True, importer_attribute_never_patched=True,
                      observer_ast_inverse=ast_proof, preloaded_material_query_checks=True,
                      sourceio_material_files_opened=0, sourceio_image_datablocks_created=0,
                      image_creation_counter_scope='SourceIO import after the admitted B append',
                      pure_observation_IO_scope='Ledger and binder perform no B or file IO; this outer host appended owned B Materials')
        phase='ONE_QUALIFIED_CARRIER_EXPORT'
        perform_carrier_export(bpy,np,container,ledger,facts,snapshot,binding,owned_materials,inspection_module,
            TinyPath,owned_B,target,buffers,result)
    except BaseException as error:
        result.update(status='REFUSED', phase=phase, error_type=type(error).__name__,
                      error_code=str(error) if isinstance(error, ControlledRefusal) or
                      (ledger_module is not None and isinstance(error, ledger_module.Refusal)) or
                      (binding_module is not None and isinstance(error, binding_module.Refusal)) or
                      (metadata_module is not None and isinstance(error, metadata_module.Refusal)) or
                      (inspection_module is not None and isinstance(error, inspection_module.Refusal)) or
                      (enumeration_module is not None and isinstance(error, enumeration_module.Refusal)) else 'PINNED_API_OR_SCHEMA_REFUSAL')
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
        result['all_read_inputs_hash_size_stamp_unchanged'] = unchanged and len(reads) == 605
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
        placement_encoded = (json.dumps({'format': 'has_carrier_export_hidden_placement_1', 'policy': placement,
                                         'worker_verified_hidden_sentinel_closed': result['hidden_placement_verified']},
                                        sort_keys=True, allow_nan=False, indent=2) + '\n').encode()
        with (target / 'PLACEMENT_CARRIER_EXPORT.json').open('xb') as stream:
            stream.write(placement_encoded)
        with (target / 'PUBLIC_CARRIER_EXPORT.json').open('xb') as stream:
            stream.write(encoded)
    print('HAS_CURRENT_ID_PROBE ' + json.dumps({'status': result['status']}))
    return 0 if result['status'] == 'MATCHED_FRESH_NATIVE_IDS_OWNED_MATERIALS_AND_CARRIER_EXPORT' else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ControlledRefusal, OSError, ValueError, KeyError, TypeError):
        # No unsanitized private exception values/traceback enter public stdout.
        print('HAS_CURRENT_ID_PROBE {"status":"REFUSED_ROOT_LEASE_OR_PUBLICATION"}')
        raise SystemExit(1)
