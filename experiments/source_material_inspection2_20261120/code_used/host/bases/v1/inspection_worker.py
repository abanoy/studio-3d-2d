"""Root-only bounded material append inspection; stdlib-only import bootstrap.

No SourceIO, native geometry, old-scene opening, image buffer, export or save.
Only Root's separate retained private job can qualify physical closure.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
import time
from contextlib import ExitStack

sys.dont_write_bytecode = True
HERE = Path(__file__).absolute().parent
PROJECT = HERE.parents[1]
SUPPORT = PROJECT / 'experiments/source_current_native_ids_20261120/fresh_current_id_probe.py'
SUPPORT_PIN = (35572, 'd78369585463dcc2a511e00889f7e768e10c61004cf4f3fac0df3885b7d60c93')
SENTINEL = PROJECT / 'experiments/normal_setter_boundary_sentinel_20261117/setter_probe.py'
SENTINEL_PIN = (17989, '034122697e8fa0e7a855ea42b51eddc351b647ae5f7641cad8d02994a51fc3c3')
BLENDER = Path(r'C:\Program Files\Blender Foundation\Blender 5.1\blender.exe')
BLENDER_PIN = (108687824, '1e6624af112b3c936f4b038b025ebd2bf00ae72c4b62881a6787166d71c58fa5')
B_PIN = (2423175, 'ead1f1913812593abd69e353fed375944a15f280738784886fcef7fda3ee65c6')
MODULES = {
    'enumeration_module': ('library_enumeration.py', 18845, '6c3aeff6a56b22a448d3ca093997ca866e76ac6ec2fb3948c811abad9c86f903'),
    'inspection_module': ('material_inspection.py', 21539, '1cf59c563150028fb9a61ae00944bfcbe71d12a0bf167bdf38eb0a6ec8cfe05d'),
    'metadata_reader': ('material_metadata.py', 13818, 'c04c4e20705b490ed7633855b2e3bdde14350adec35c8b2a25afc42b69508395'),
}
NATIVE = {
    'mdl': ('native/junko hair.mdl', 37644, '8da09c905227ddc8eef73a3f83594a4eb1c3a6d5304ee41ba5471bef834bc716'),
    'vvd': ('native/junko hair.vvd', 618368, '2bfa2a363eea586d06d4fd0e28c7751c10276da5cc0c46c310ffa9dedbb159e0'),
    'vtx': ('native/junko hair.dx90.vtx', 173309, '924954f27574fc83945934a13e6b4e90049b5d46356053dc4b41ec43d3ce364a'),
}
REVISION = '9e3b039039833adce4723bbb70681595cd4eef16'
ROLES = {'probe', 'support_worker', 'sentinel', 'blend', 'full_completion', 'graphics_release',
         'blender_exe', *MODULES, *('native_' + key for key in NATIVE)}
SUCCESS = 'MATERIAL_ONLY_NARROW_GRAPH_AND_PACKED_HEADER_INSPECTION_MATCHED_1'
FALSE_FLAGS = ('original_B_scene_opened', 'image_pixels_read', 'image_buffer_getters_used', 'blend_saved',
               'exporter_invoked', 'native_arrays_published', 'native_or_historical_point_identity_qualified',
               'resource_or_export_qualified', 'resource_equivalence_qualified', 'normal_fidelity_qualified',
               'application_adoption_qualified', 'material_binding_qualified', 'dependency_closure_qualified',
               'non_normal_semantic_equivalence_qualified', 'transient_ID_or_C_level_read_absence_qualified',
               'outer_physical_closure_verified_by_worker')


class Refusal(ValueError):
    pass


def need(ok, code):
    if not ok:
        raise Refusal(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(value):
    return sha(json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False,
                          separators=(',', ':')).encode())


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, 'DUPLICATE_JSON_KEY')
            result[key] = value
        return result
    def invalid(_value):
        raise Refusal('NONFINITE_JSON')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)


def load_verified_module(path, raw, name):
    need(name not in sys.modules, 'PRIVATE_MODULE_COLLISION')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        exec(compile(raw, str(path), 'exec', dont_inherit=True), module.__dict__)
    except BaseException:
        del sys.modules[name]
        raise
    return module


def _bootstrap_support():
    path = SUPPORT.absolute()
    for item in (path, *path.parents):
        info = item.lstat()
        need(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400,
             'BOOTSTRAP_LINK_OR_REPARSE')
    before = path.stat()
    identity = lambda value: (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns)
    need(stat.S_ISREG(before.st_mode) and before.st_size == SUPPORT_PIN[0], 'SUPPORT_LITERAL_SIZE')
    with path.open('rb') as stream:
        need(identity(os.fstat(stream.fileno())) == identity(before), 'SUPPORT_CHANGED_BEFORE_READ')
        raw = stream.read(SUPPORT_PIN[0] + 1)
        opened = os.fstat(stream.fileno())
    need(identity(opened) == identity(before) == identity(path.stat()) and len(raw) == SUPPORT_PIN[0] and
         sha(raw) == SUPPORT_PIN[1], 'SUPPORT_LITERAL_HASH_OR_STAMP')
    return load_verified_module(path, raw, '_has_material_inspection_support'), (path, *SUPPORT_PIN, identity(before))


def select_native_subset(metadata, available):
    """Exact independently parsed native table order, never a name heuristic."""
    need(type(metadata) is dict and metadata.get('format') == 'has_private_mdl49_material_skin_metadata_candidate_1',
         'NATIVE_METADATA_CANDIDATE_SCHEMA')
    need(type(metadata.get('metadata')) is dict, 'NATIVE_METADATA_TABLE_SCHEMA')
    rows = metadata['metadata'].get('materials')
    need(type(rows) is list and len(rows) == 4 and all(type(row) is dict and row.get('index') == index and
         type(row.get('index')) is int and type(row.get('name')) is str and 0 < len(row['name']) <= 256
         for index, row in enumerate(rows)), 'FOUR_ORDERED_NATIVE_MATERIAL_NAMES_REQUIRED')
    names = tuple(row['name'] for row in rows)
    need(len(set(names)) == 4, 'DISTINCT_NATIVE_MATERIAL_NAMES_REQUIRED')
    need(type(available) is tuple and 1 <= len(available) <= 256 and
         all(type(name) is str and 0 < len(name) <= 1024 for name in available) and
         len(set(available)) == len(available), 'BOUNDED_UNIQUE_B_MATERIAL_CATALOGUE_REQUIRED')
    need(all(available.count(name) == 1 for name in names), 'EXACT_NATIVE_NAME_SUBSET_NOT_AVAILABLE')
    return names, dict(format='has_native_material_name_subset_1', native_materials=4,
                       available_materials=len(available), unrequested_catalogue_materials=len(available) - 4,
                       requested_names_sha256=digest(names), exact_native_name_subset=True,
                       native_geometry_decoded=False, native_engine_semantics_qualified=False)


def node_type_diagnostic(bpy, originals):
    """Bounded RNA type names only, even when the deliberately narrow graph refuses."""
    counts, materials, nodes = {}, 0, 0
    original_ids = {id(value) for value in originals}
    for material in bpy.data.materials:
        if id(material) in original_ids:
            need(any(material is original for original in originals), 'DIAGNOSTIC_ORIGINAL_REF_CHANGED')
            continue
        need(type(material) is bpy.types.Material and material.original is material and material.library is None,
             'DIAGNOSTIC_LOCAL_ORIGINAL_MATERIAL_REQUIRED')
        materials += 1
        need(materials <= 4, 'DIAGNOSTIC_MATERIAL_BUDGET')
        tree = material.node_tree
        if tree is None:
            continue
        need(type(tree) is bpy.types.ShaderNodeTree and tree.original is tree and tree.library is None and
             tree.is_embedded_data is True and len(tree.nodes) <= 128, 'DIAGNOSTIC_EMBEDDED_NODE_TREE_BUDGET')
        for node in tree.nodes:
            nodes += 1
            need(nodes <= 512 and isinstance(node, bpy.types.Node) and node.id_data is tree,
                 'DIAGNOSTIC_GENUINE_NODE_OWNER_REQUIRED')
            kind = node.bl_idname
            need(type(kind) is str and re.fullmatch('[A-Za-z][A-Za-z0-9_]{0,127}', kind) is not None,
                 'DIAGNOSTIC_NODE_TYPE_NAME_SCHEMA')
            counts[kind] = counts.get(kind, 0) + 1
    return dict(format='has_material_node_type_counts_1', materials=materials, nodes=nodes,
                node_type_counts=dict(sorted(counts.items())), image_buffer_getters_used=False)


def inspect_once(bpy, owned, buffers, enumeration, inspection, metadata_reader, result):
    refs = {key: dict(raw=buffers['native_' + key], bytes=count, sha256=hash_) for key, (_path, count, hash_) in NATIVE.items()}
    metadata = metadata_reader.derive_material_metadata(refs)
    result['native_metadata_derived_without_geometry'] = True
    result['library_enumeration_attempted'] = True
    def summary_sink(summary):
        need(type(summary) is dict and summary.get('format') == 'has_empty_library_enumeration_summary_2',
             'ENUMERATION_SUMMARY_SCHEMA')
        result.update(enumeration_summary=summary, library_enumeration_executed=True,
                      complete_actual_ID_census_observed=True)
    observation = enumeration.enumerate_library(bpy, owned, summary_sink=summary_sink)
    names, selection = select_native_subset(metadata, observation['material_names'])
    result['native_subset_summary'] = selection
    originals = tuple(bpy.data.materials)
    result['material_inspection_attempted'] = True
    try:
        private = inspection.inspect_material_library(bpy, owned, names, enumeration)
    except inspection.Refusal as error:
        if error.summary is not None:
            result['inspection_summary'] = error.summary
        try:
            result['node_type_diagnostic'] = node_type_diagnostic(bpy, originals)
        except BaseException:
            result['node_type_diagnostic'] = dict(status='REFUSED_BOUNDED_TYPE_DIAGNOSTIC')
        raise
    result['inspection_summary'] = private['summary']
    result['node_type_diagnostic'] = node_type_diagnostic(bpy, originals)
    result['material_inspection_executed'] = True


def _request(support, path, digest_):
    path = support.safe(path)
    need(path.is_relative_to(PROJECT / 'output') and path.stat().st_size <= 2 * 1024 * 1024, 'ROOT_REQUEST_PATH_OR_BUDGET')
    raw, before = support.pinned_read(path, path.stat().st_size, digest_)
    lease = strict_json(raw)
    need(type(lease) is dict and lease.get('format') == 'has_owned_B_material_inspection_request_1' and
         lease.get('phase') == 'ROOT_APPROVED_AFTER_FULL_PHYSICALLY_CLOSED' and lease.get('private_arrays_public') is False,
         'ROOT_REQUEST_FORMAT_OR_SCOPE')
    now = datetime.datetime.now(datetime.timezone.utc)
    created, expiry = (datetime.datetime.fromisoformat(lease[key]) for key in ('created_utc', 'expires_utc'))
    need(created.tzinfo is not None and expiry.tzinfo is not None and created <= now < expiry and
         datetime.timedelta(0) < expiry - created <= datetime.timedelta(minutes=30), 'FRESH_ROOT_REQUEST_REQUIRED')
    context = lease['source_context']
    need(type(context) is dict and all(context.get(key) is True for key in
         ('full_suite_passed', 'full_job_physically_closed', 'exclusive_runtime_lease')) and
         type(context.get('observed_owned_processes')) is int and context['observed_owned_processes'] == 0 and
         type(context.get('functional_file_count')) is int and context['functional_file_count'] == 1061 and
         context.get('tested_revision') == REVISION, 'ROOT_FULL_9E_CLOSED_CONTEXT')
    need(type(lease.get('files')) is dict and set(lease['files']) == ROLES, 'EXACT_THIRTEEN_ROOT_FILE_ROLES')
    stage = support.safe(lease['owned_stage'])
    output, temporary = support.safe(lease['owned_output']), support.safe(lease['owned_temp'])
    need(stage.is_dir() and stage.is_relative_to(PROJECT / 'output') and stage != HERE and
         output == stage / 'result' and output.is_dir() and temporary == stage / 'temp' and temporary.is_dir(),
         'OWNED_STAGE_OUTPUT_TEMP_BOUNDARY')
    need(support.safe(os.environ.get('TEMP', '')) == temporary and support.safe(os.environ.get('TMP', '')) == temporary and
         support.safe(tempfile.gettempdir()) == temporary, 'OWNED_TEMP_ENVIRONMENT_REQUIRED')
    need(not (output / 'PUBLIC_MATERIAL_INSPECTION.json').exists() and
         not (output / 'PLACEMENT_MATERIAL_INSPECTION.json').exists(), 'FRESH_PUBLIC_RESULT_REQUIRED')
    return lease, output, (path, len(raw), digest_, before)


def literal_inputs(stage):
    result = {'support_worker': (SUPPORT, SUPPORT_PIN), 'sentinel': (SENTINEL, SENTINEL_PIN),
              'blend': (stage / 'inputs/material-source.blend', B_PIN), 'blender_exe': (BLENDER, BLENDER_PIN)}
    result.update({role: (HERE / name, (count, hash_)) for role, (name, count, hash_) in MODULES.items()})
    result.update({'native_' + key: (stage / 'inputs' / name, (count, hash_))
                   for key, (name, count, hash_) in NATIVE.items()})
    return result


def main():
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--request-sha256', required=True)
    options = parser.parse_args(args)
    support, support_read = _bootstrap_support()
    lease, target, request_read = _request(support, options.request, options.request_sha256)
    reads = {'root_request': request_read, 'support_worker': support_read}
    result = dict(format='has_owned_B_material_inspection_result_1', status='REFUSED',
                  **{key: False for key in FALSE_FLAGS})
    placement, stack = None, ExitStack()
    phase = 'AUTHENTICATE_ROOT_FILES'
    controlled = (Refusal, support.ControlledRefusal)
    try:
        buffers = {}
        literals = literal_inputs(Path(lease['owned_stage']))
        for role, row in lease['files'].items():
            need(type(row) is dict and set(row) == {'path', 'bytes', 'sha256'}, 'ROOT_FILE_ROW_SCHEMA')
            path = support.safe(row['path'])
            literal = literals.get(role)
            if literal:
                need(path == literal[0] and (row['bytes'], row['sha256']) == literal[1], 'ROOT_LITERAL_INPUT_DIFFERS')
            if role == 'probe':
                need(path == Path(__file__).absolute(), 'ROOT_WORKER_ALIAS_DIFFERS')
            raw, before = support.pinned_read(path, row['bytes'], row['sha256'])
            if role == 'support_worker':
                need(path == support_read[0] and before == support_read[3], 'SUPPORT_CHANGED_SINCE_BOOTSTRAP')
            reads[role] = (path, row['bytes'], row['sha256'], before)
            buffers[role] = raw
        for role in ('full_completion', 'graphics_release'):
            need(lease['source_context'].get(role + '_sha256') == lease['files'][role]['sha256'], 'ROOT_CONTEXT_HASH_ALIAS')
        need(strict_json(buffers['full_completion']).get('whole_verifier_pass') is True and
             strict_json(buffers['graphics_release']).get('full_suite_passed') is True, 'HASH_BOUND_FULL_PASS_REQUIRED')
        modules = {role: load_verified_module(literals[role][0], buffers[role], '_has_inspection_' + role)
                   for role in MODULES}
        controlled += tuple(modules[role].Refusal for role in MODULES)
        placement = stack.enter_context(support.placement_sentinel(buffers['sentinel'].decode('utf-8'))())
        time.sleep(.5)
        phase = 'COLD_ENUMERATE_AND_MATERIAL_ONLY_INSPECTION'
        import bpy
        need(sys.platform == 'win32' and sys.byteorder == 'little' and sys.version_info[:2] == (3, 13) and
             bpy.app.background is True and bpy.app.online_access is False and bpy.data.filepath == '' and
             bpy.context.preferences.filepaths.use_scripts_auto_execute is False and
             Path(bpy.app.binary_path).resolve() == BLENDER.resolve(), 'COLD_FACTORY_OFFLINE_BLENDER_CONTEXT')
        inspect_once(bpy, Path(lease['files']['blend']['path']), buffers, modules['enumeration_module'],
                     modules['inspection_module'], modules['metadata_reader'], result)
        need(bpy.data.filepath == '' and bpy.app.online_access is False and
             bpy.context.preferences.filepaths.use_scripts_auto_execute is False, 'FACTORY_CONTEXT_CHANGED')
        result['status'] = SUCCESS
    except BaseException as error:
        result.update(status='REFUSED', phase=phase, error_type=type(error).__name__,
                      error_code=str(error) if isinstance(error, controlled) else 'PINNED_API_OR_SCHEMA_REFUSAL')
    finally:
        try:
            stack.close()
            need(placement is not None and placement['destroyed_in_finally'] is True and
                 placement['visible_at_creation'] is False and placement['visible_before_destruction'] is False and
                 placement['owned_pid_and_thread_verified'] is True, 'HIDDEN_PLACEMENT_NOT_CLOSED')
            result['hidden_placement_verified'] = True
        except BaseException:
            result['hidden_placement_verified'] = False
            result['status'] = 'REFUSED_PLACEMENT'
        stable = len(reads) == 14
        for _role, (path, count, hash_, before) in reads.items():
            try:
                _raw, after = support.pinned_read(path, count, hash_)
                stable = stable and before == after
            except BaseException:
                stable = False
        result['all_read_inputs_hash_size_stamp_unchanged'] = stable
        if not stable:
            result['status'] = 'REFUSED_PRESERVATION'
        result['input_identities'] = {role: dict(bytes=count, sha256=hash_) for role, (_path, count, hash_, _stamp) in sorted(reads.items())}
        placement_result = dict(format='has_owned_B_material_inspection_placement_1', policy=placement,
                                worker_verified_hidden_sentinel_closed=result['hidden_placement_verified'])
        for name, value in (('PLACEMENT_MATERIAL_INSPECTION.json', placement_result), ('PUBLIC_MATERIAL_INSPECTION.json', result)):
            raw = (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()
            need(len(raw) <= 64 * 1024, 'COMPACT_PUBLIC_RESULT_BUDGET')
            with (target / name).open('xb') as stream:
                stream.write(raw)
    print('HAS_MATERIAL_INSPECTION ' + json.dumps(dict(status=result['status'])))
    return 0 if result['status'] == SUCCESS else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (Refusal, OSError, ValueError, KeyError, TypeError):
        print('HAS_MATERIAL_INSPECTION {"status":"REFUSED_ROOT_LEASE_OR_PUBLICATION"}')
        raise SystemExit(1)
