"""Root-only empty-request B-library census worker; import uses stdlib only.

No SourceIO, scene opening, append requests, image getters, labels or export.
Root alone launches the private native job and proves its later physical closure.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
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
REVISION = '9e3b039039833adce4723bbb70681595cd4eef16'
ROLES = {'probe', 'support_worker', 'sentinel', 'blend', 'full_completion', 'graphics_release', 'blender_exe'}
SUCCESS = 'BOUNDED_EMPTY_LIBRARY_ENUMERATION_MATCHED_2'
MAX_COLLECTIONS, MAX_IDS, MAX_NAMES = 128, 4096, 16_384
MAX_SOURCE_MATERIALS = 256


class Refusal(ValueError):
    pass


def need(ok, code):
    if not ok:
        raise Refusal(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


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


def _bootstrap_support():
    """Authenticate before import; execute verified raw text, never cached pyc."""
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
    need(identity(opened) == identity(before) == identity(path.stat()) and
         len(raw) == SUPPORT_PIN[0] and sha(raw) == SUPPORT_PIN[1], 'SUPPORT_LITERAL_HASH_OR_STAMP')
    name = '_has_empty_library_pinned_support'
    need(name not in sys.modules, 'SUPPORT_MODULE_COLLISION')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(raw, str(path), 'exec', dont_inherit=True), module.__dict__)
    return module, (path, *SUPPORT_PIN, identity(before))


def _name(value):
    need(type(value) is str and 0 < len(value) <= 1024 and len(value.encode('utf-8')) <= 4096,
         'BOUNDED_ID_OR_LIBRARY_NAME')
    return value


def _pointer(value):
    result = value.as_pointer()
    need(type(result) is int and 0 < result < 2**64, 'ACTUAL_ID_POINTER_REQUIRED')
    return result


def _id_collection_property(prop):
    fixed = prop.fixed_type
    seen = set()
    for _ in range(32):
        need(fixed is not None and id(fixed) not in seen, 'UNKNOWN_BLENDDATA_COLLECTION_TYPE')
        seen.add(id(fixed))
        if fixed.identifier == 'ID':
            return True
        fixed = fixed.base
    raise Refusal('RNA_TYPE_DEPTH_BUDGET')


def _census(bpy):
    """Private actual refs/pointers/names/libraries; never geometry/image values."""
    properties = tuple(bpy.data.bl_rna.properties)
    need(0 < len(properties) <= MAX_COLLECTIONS + 8, 'BLENDDATA_RNA_PROPERTY_BUDGET')
    names = []
    for prop in properties:
        if prop.type != 'COLLECTION':
            continue
        name = _name(prop.identifier)
        need(not name.startswith('_') and name not in names and _id_collection_property(prop),
             'UNIQUE_COMPLETE_ID_COLLECTION_DOMAIN')
        names.append(name)
    need(0 < len(names) <= MAX_COLLECTIONS, 'ID_COLLECTION_COUNT_BUDGET')
    rows, pointers, total = {}, set(), 0
    for name in sorted(names):
        records = []
        for value in getattr(bpy.data, name):
            total += 1
            need(total <= MAX_IDS and isinstance(value, bpy.types.ID) and value.original is value,
                 'BOUNDED_ORIGINAL_BLENDDATA_IDS_REQUIRED')
            pointer = _pointer(value)
            need(pointer not in pointers, 'ID_POINTER_ALIAS_ACROSS_COLLECTIONS')
            pointers.add(pointer)
            library = value.library
            need(library is None or isinstance(library, bpy.types.ID) and library.original is library,
                 'ACTUAL_LIBRARY_REFERENCE_REQUIRED')
            records.append((value, pointer, type(value), _name(value.name), _name(value.name_full),
                            library, None if library is None else _pointer(library)))
        rows[name] = tuple(sorted(records, key=lambda row: row[1]))
    return rows, total


def _unchanged(before, after):
    if set(before) != set(after):
        return False
    for key in before:
        if len(before[key]) != len(after[key]):
            return False
        for old, new in zip(before[key], after[key]):
            if not (old[0] is new[0] and old[1:5] == new[1:5] and old[5] is new[5] and old[6] == new[6]):
                return False
    return True


def _library_keys(value):
    keys = tuple(sorted(dir(value)))
    need(0 < len(keys) <= MAX_COLLECTIONS + 1 and len(set(keys)) == len(keys) and
         all(type(key) is str and key.isidentifier() and not key.startswith('_') for key in keys),
         'BOUNDED_PUBLIC_LIBRARY_DIR_REQUIRED')
    return keys


def _empty_requests(destination, expected):
    need(_library_keys(destination) == expected, 'DESTINATION_LIBRARY_SCHEMA_CHANGED')
    count = 0
    for key in expected:
        value = getattr(destination, key)
        if key == 'version':
            need(type(value) is tuple and len(value) == 3 and all(type(v) is int and v >= 0 for v in value),
                 'LIBRARY_VERSION_SCHEMA')
            continue
        need(type(value) is list and len(value) == 0, 'NONEMPTY_LIBRARY_REQUEST_REFUSED')
        count += 1
    return count


def validate_source_material_count(value):
    need(type(value) is int and 1 <= value <= MAX_SOURCE_MATERIALS, 'BOUNDED_SOURCE_MATERIAL_CATALOGUE_COUNT')


def record_summary(result, summary):
    """Retain completed enumeration evidence before any later scope refusal."""
    need(type(summary) is dict and summary.get('format') == 'has_empty_library_enumeration_summary_2',
         'ENUMERATION_SUMMARY_SCHEMA')
    result.update(summary=summary, library_enumeration_executed=True,
                  complete_actual_ID_census_observed=True)


def enumerate_library(bpy, owned_path, summary_sink=None):
    """Return RAM-only material names plus public scalar/hash summary.

    The caller authenticates owned_path. No destination ID list is assigned.
    The actual all-ID census must remain unchanged; no transient-read claim.
    """
    before, before_count = _census(bpy)
    catalogue, destination, keys = {}, None, None
    with bpy.data.libraries.load(str(owned_path), link=False) as (source, destination):
        keys = _library_keys(destination)
        request_types = _empty_requests(destination, keys)
        need(_library_keys(source) == keys, 'SOURCE_DESTINATION_LIBRARY_SCHEMA_DIFFERS')
        total = 0
        for key in keys:
            value = getattr(source, key)
            if key == 'version':
                need(type(value) is tuple and len(value) == 3 and all(type(v) is int and v >= 0 for v in value),
                     'LIBRARY_VERSION_SCHEMA')
                continue
            need(type(value) is list, 'SOURCE_LIBRARY_NAME_LIST_REQUIRED')
            total += len(value)
            need(total <= MAX_NAMES, 'SOURCE_LIBRARY_NAME_BUDGET')
            catalogue[key] = tuple(_name(name) for name in value)
        need('materials' in catalogue and len(set(catalogue['materials'])) == len(catalogue['materials']),
             'UNIQUE_SOURCE_MATERIAL_NAME_LIST_REQUIRED')
        _empty_requests(destination, keys)
    _empty_requests(destination, keys)
    after, after_count = _census(bpy)
    unchanged = _unchanged(before, after)
    encoded = lambda value: json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(',', ':')).encode()
    summary = dict(format='has_empty_library_enumeration_summary_2', before_id_count=before_count,
                   after_id_count=after_count, id_collections=len(before), source_id_types=len(catalogue),
                   source_catalogue_name_count=sum(map(len, catalogue.values())), source_materials=len(catalogue['materials']),
                   source_material_names_sha256=sha(encoded(catalogue['materials'])), source_catalogue_sha256=sha(encoded(catalogue)),
                   destination_request_types=request_types, all_destination_requests_empty=True,
                   actual_id_census_unchanged=unchanged)
    if summary_sink is not None:
        summary_sink(summary)
    need(unchanged, 'ACTUAL_ID_CENSUS_CHANGED')
    validate_source_material_count(summary['source_materials'])
    return dict(material_names=catalogue['materials'], summary=summary)


def _request(support, path, digest):
    path = support.safe(path)
    need(path.is_relative_to(PROJECT / 'output') and path.stat().st_size <= 2 * 1024 * 1024, 'ROOT_REQUEST_PATH_OR_BUDGET')
    raw, before = support.pinned_read(path, path.stat().st_size, digest)
    lease = strict_json(raw)
    need(type(lease) is dict and lease.get('format') == 'has_owned_B_empty_library_census_request_2' and
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
    need(type(lease.get('files')) is dict and set(lease['files']) == ROLES, 'EXACT_SEVEN_ROOT_FILE_ROLES')
    stage = support.safe(lease['owned_stage'])
    output, temporary = support.safe(lease['owned_output']), support.safe(lease['owned_temp'])
    need(stage.is_dir() and stage.is_relative_to(PROJECT / 'output') and stage != HERE and
         output == stage / 'result' and output.is_dir() and temporary == stage / 'temp' and temporary.is_dir(),
         'OWNED_STAGE_OUTPUT_TEMP_BOUNDARY')
    need(support.safe(os.environ.get('TEMP', '')) == temporary and support.safe(os.environ.get('TMP', '')) == temporary and
         support.safe(tempfile.gettempdir()) == temporary,
         'OWNED_TEMP_ENVIRONMENT_REQUIRED')
    need(not (output / 'PUBLIC_LIBRARY_CENSUS2.json').exists() and not (output / 'PLACEMENT_LIBRARY_CENSUS2.json').exists(),
         'FRESH_PUBLIC_RESULT_REQUIRED')
    return lease, output, (path, len(raw), digest, before)


def main():
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--request-sha256', required=True)
    options = parser.parse_args(args)
    support, support_read = _bootstrap_support()
    lease, target, request_read = _request(support, options.request, options.request_sha256)
    reads = {'root_request': request_read, 'support_worker': support_read}
    result = dict(format='has_owned_B_empty_library_census_result_2', status='REFUSED', original_B_scene_opened=False,
                  material_append_requested=False, image_pixels_read=False, blend_saved=False, exporter_invoked=False,
                  native_arrays_published=False, native_or_historical_point_identity_qualified=False,
                  resource_or_export_qualified=False, normal_fidelity_qualified=False,
                  application_adoption_qualified=False, material_binding_qualified=False,
                  transient_ID_or_C_level_read_absence_qualified=False, library_enumeration_attempted=False,
                  no_transient_IDs_or_C_level_reads_claimed=True, outer_physical_closure_verified_by_worker=False)
    placement, stack = None, ExitStack()
    phase = 'AUTHENTICATE_ROOT_FILES'
    try:
        buffers = {}
        for role, row in lease['files'].items():
            need(type(row) is dict and set(row) == {'path', 'bytes', 'sha256'}, 'ROOT_FILE_ROW_SCHEMA')
            path = support.safe(row['path'])
            literal = {'support_worker': (SUPPORT, SUPPORT_PIN), 'sentinel': (SENTINEL, SENTINEL_PIN),
                       'blend': (Path(lease['owned_stage']) / 'inputs/material-source.blend', B_PIN),
                       'blender_exe': (BLENDER, BLENDER_PIN)}.get(role)
            if literal:
                need(path == literal[0] and (row['bytes'], row['sha256']) == literal[1], 'ROOT_LITERAL_INPUT_DIFFERS')
            if role == 'probe':
                need(path == Path(__file__).absolute(), 'ROOT_WORKER_ALIAS_DIFFERS')
            if role == 'support_worker':
                need(path == support_read[0], 'ROOT_SUPPORT_ALIAS_DIFFERS')
                raw, before = support.pinned_read(path, row['bytes'], row['sha256'])
                need(before == support_read[3], 'SUPPORT_CHANGED_SINCE_BOOTSTRAP')
            else:
                raw, before = support.pinned_read(path, row['bytes'], row['sha256'])
            reads[role] = (path, row['bytes'], row['sha256'], before)
            buffers[role] = raw
        for role in ('full_completion', 'graphics_release'):
            need(lease['source_context'].get(role + '_sha256') == lease['files'][role]['sha256'], 'ROOT_CONTEXT_HASH_ALIAS')
        need(strict_json(buffers['full_completion']).get('whole_verifier_pass') is True and
             strict_json(buffers['graphics_release']).get('full_suite_passed') is True, 'HASH_BOUND_FULL_PASS_REQUIRED')
        placement = stack.enter_context(support.placement_sentinel(buffers['sentinel'].decode('utf-8'))())
        time.sleep(.5)  # Allow the unchanged outer private-desktop observer to see the owned sentinel.
        phase = 'EMPTY_REQUEST_LIBRARY_ENUMERATION'
        import bpy
        need(sys.platform == 'win32' and sys.byteorder == 'little' and sys.version_info[:2] == (3, 13) and
             bpy.app.background is True and bpy.app.online_access is False and bpy.data.filepath == '' and
             bpy.context.preferences.filepaths.use_scripts_auto_execute is False and
             Path(bpy.app.binary_path).resolve() == BLENDER.resolve(), 'COLD_FACTORY_OFFLINE_BLENDER_CONTEXT')
        result['library_enumeration_attempted'] = True
        observation = enumerate_library(bpy, Path(lease['files']['blend']['path']),
                                        summary_sink=lambda summary: record_summary(result, summary))
        need(bpy.data.filepath == '' and bpy.app.online_access is False and
             bpy.context.preferences.filepaths.use_scripts_auto_execute is False, 'FACTORY_CONTEXT_CHANGED')
        result.update(status=SUCCESS)
    except BaseException as error:
        result.update(status='REFUSED', phase=phase, error_type=type(error).__name__,
                      error_code=str(error) if isinstance(error, (Refusal, support.ControlledRefusal)) else 'PINNED_API_OR_SCHEMA_REFUSAL')
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
        stable = len(reads) == 8
        for _role, (path, count, digest, before) in reads.items():
            try:
                _raw, after = support.pinned_read(path, count, digest)
                stable = stable and before == after
            except BaseException:
                stable = False
        result['all_read_inputs_hash_size_stamp_unchanged'] = stable
        if not stable:
            result['status'] = 'REFUSED_PRESERVATION'
        result['input_identities'] = {role: dict(bytes=count, sha256=digest) for role, (_path, count, digest, _stamp) in sorted(reads.items())}
        placement_result = dict(format='has_owned_B_empty_library_placement_2', policy=placement,
                                worker_verified_hidden_sentinel_closed=result['hidden_placement_verified'])
        for name, value in (('PLACEMENT_LIBRARY_CENSUS2.json', placement_result), ('PUBLIC_LIBRARY_CENSUS2.json', result)):
            raw = (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()
            need(len(raw) <= 64 * 1024, 'COMPACT_PUBLIC_RESULT_BUDGET')
            with (target / name).open('xb') as stream:
                stream.write(raw)
    print('HAS_EMPTY_LIBRARY_CENSUS2 ' + json.dumps(dict(status=result['status'])))
    return 0 if result['status'] == SUCCESS else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (Refusal, OSError, ValueError, KeyError, TypeError):
        print('HAS_EMPTY_LIBRARY_CENSUS2 {"status":"REFUSED_ROOT_LEASE_OR_PUBLICATION"}')
        raise SystemExit(1)
