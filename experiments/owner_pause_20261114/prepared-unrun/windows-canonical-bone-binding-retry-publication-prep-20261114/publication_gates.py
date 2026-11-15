"""Metadata-only gates shared by terminal publication recipes; no runtime actions."""
from pathlib import Path
import gzip
import hashlib
import json
import math
import stat
import re
import calendar
from datetime import datetime

MAXIMUM = 64 * 1024 * 1024


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def utc_ns(value):
    match = re.fullmatch(r'(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d{1,9}))?Z', value or '')
    require(match is not None, 'Exact UTC timestamp required')
    return calendar.timegm(datetime.strptime(match[1], '%Y-%m-%dT%H:%M:%S').timetuple()) * 10**9 + int((match[2] or '').ljust(9, '0'))


def read(path):
    path = Path(path).absolute()
    require('..' not in path.parts and path.suffix.lower() in {'.json', '.gz', '.py', '.gd', '.ps1', '.md', '.txt', '.log'},
            'Only bounded metadata/source files are admitted')
    for part in [path, *path.parents]:
        info = part.lstat()
        require(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400,
                'Metadata reparse path refused')
    before = path.stat()
    require(stat.S_ISREG(before.st_mode) and before.st_size <= MAXIMUM, 'Metadata kind/size refused')
    raw = path.read_bytes()
    after = path.stat()
    require((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns), 'Metadata changed during read')
    return raw


def load(path):
    return json.loads(read(path), parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite metadata')))


def registry(base, context):
    raw = read(base / 'RESULT_REGISTRY.json')
    require(sha(raw) == context['result_registry_sha256'], 'Source-derived result registry changed')
    value = json.loads(raw)
    require(value['source_commit'] == context['source_commit'] and len(value['expected_result_keys']) == 157
            and len(set(value['expected_result_keys'])) == 157
            and len(value['expected_core_process_keys']) == 36 and len(value['expected_movie_keys']) == 21,
            'Wrong result registry context')
    return value


def validate_result(value, context, expected):
    require(set(value) == set(expected['expected_result_keys']),
            'Canonical named result registry differs (missing/extra): ' + repr(sorted(set(value) ^ set(expected['expected_result_keys']))))
    core = {name: row for name, row in value.items() if isinstance(row, dict) and set(row) == {'exit', 'seconds'}}
    require(set(core) == set(expected['expected_core_process_keys']) and all(type(row['exit']) is int and row['exit'] == 0
            and type(row['seconds']) in (int, float) and math.isfinite(row['seconds']) and row['seconds'] >= 0 for row in core.values()),
            'Actual named core process registry differs')
    movies = {name: row for name, row in value.items() if isinstance(row, dict) and set(row) == {'frames', 'fps', 'duration'}}
    require(set(movies) == set(expected['expected_movie_keys']) and all(type(row['frames']) is int and row['frames'] == 48
            and row['fps'] == '24/1' and math.isfinite(float(row['duration'])) and abs(float(row['duration']) - 2) < .01 for row in movies.values()),
            'Actual named movie registry differs')
    foundation = value['source_choice_foundation']
    require(foundation['checks'] == 167 and foundation['passed'] is True and foundation['source_unchanged'] is True
            and foundation['native_conversion'] is False, 'Foundation167 failed')
    reports = foundation['reports']
    for key, count in [('jiggle_cpu', 66), ('crosswalk_cpu', 77), ('bone_bindings_headless', 96)]:
        row = reports[key]
        require(row['checks'] == count and row['passed'] is True and row['source_unchanged'] is True
                and row['native_conversion'] is False and row['graphics'] is False, 'Separate named scope failed: ' + key)
    require({name: row['checks'] for name, row in reports['crosswalk_cpu']['reports'].items()}
            == {'collector': 47, 'metadata': 11, 'adapter': 19}, 'Python crosswalk77 split differs')
    headless = reports['bone_bindings_headless']
    require(headless['headless'] is True and headless['runtime_unchanged'] is True
            and {name: row['checks'] for name, row in headless['reports'].items()} == {'bindings': 79, 'helper': 17},
            'Authored headless96 split differs')
    for row in headless['reports'].values():
        require(row['failures'] == 0 and row['result']['failures'] == 0
                and all(row[phase]['exit'] == 0 and row[phase]['timed_out'] is False for phase in ['parse', 'run']),
                'Headless parse/run gate failed')
    require(foundation['separate_checks'] == {'crosswalk_cpu': 77, 'bone_bindings_headless': 96}, 'Foundation separate ledger differs')
    owner = value['source_import_owner']
    require(owner.get('skipped') is not True and owner['passed'] is True and owner['headless'] is True
            and owner['native_conversion'] is False and owner['source_unchanged'] is True
            and owner['result']['checks'] == 53 and owner['result']['failures'] == 0 and len(owner['result']['cases']) == 6,
            'Windows owner53 was skipped or failed')
    require(value['actual_mmd_tested'] is True, 'Actual MMD/posed movie scope missing')
    contact = value['contact_selection']
    require(contact['checks'] == 67 and contact['failures'] == 0 and len(contact['native_reports']) == 5
            and contact['audio_driver'] == 'Dummy', 'Silent geometric selection driver scope differs')
    for mode, split in [('cpu', [('transport', 11), ('adapter', 128), ('host', 69)]),
                        ('graphical', [('focused', 221), ('peers', 45)])]:
        row = value['helper_preview_' + mode]
        require(row['passed'] is True and row['mode'] == mode and row['source_context'] == 'main_source_snapshot'
                and row['source_state']['revision'] == context['source_commit'] and row['source_state']['working_status'] == []
                and row['overlay_files'] == 0 and row['native_requested'] is False and row['native_inputs_checked'] is False
                and row['native_fidelity'] is False and row['gpu_used'] is (mode == 'graphical')
                and [(child['label'], child['checks']) for child in row['results']] == split
                and row['checks'] == sum(count for _, count in split)
                and all(flag is True for flag in row['preservation'].values()), 'Fresh committed helper scope differs: ' + mode)
        for child in row['results']:
            require(child['passed'] is True and child['exit'] == 0 and child['timed_out'] is False
                    and child['retained_Popen_reaped'] is True and child['error_markers'] == []
                    and child['result_source_context_bound'] is True, 'Helper child closure/errors differ')
            if mode == 'graphical':
                receipt = child['private_receipt']
                require(child['clean_private_receipt'] is True and receipt['exit'] == 0
                        and all(receipt.get(key) is True for key in ['private_window_seen', 'child_desktop_confirmed', 'job_closed', 'desktop_closed'])
                        and all(receipt.get(key) is False for key in ['desktop_switch_requested', 'foreground_child_observed']),
                        'Fresh helper private receipt differs')
    reject_native_payload(value)


def reject_native_payload(value):
    if isinstance(value, dict):
        forbidden = {'Blender_matrix_local_row_major', 'native_rest_words_uint32', 'native_rest_matrices',
                     'vertex_positions', 'vertex_buffer', 'index_buffer', 'image_data', 'audio_data', 'base64'}
        for key, child in value.items():
            require(not (key in forbidden and child), 'Private native/art payload refused: ' + key)
            require(not (key in {'vertices', 'indices', 'triangles'} and isinstance(child, (list, dict))), 'Mesh payload refused')
            reject_native_payload(child)
    elif isinstance(value, list):
        for child in value:
            reject_native_payload(child)


def validate_live(run, context):
    raw = read(run / 'coordinator-children-observed.json')
    require(sha(raw) == context['children_observation_sha256'], 'Live identity observation changed')
    value = json.loads(raw)
    require(value['format'] == context['children_observation_format'] and value['source_commit'] == context['source_commit']
            and value['coordinator']['pid'] == context['coordinator_pid']
            and value['coordinator']['creation_utc'] == context['coordinator_creation_utc']
            and value['python']['pid'] == context['python_pid'] and value['python']['parent_pid'] == context['coordinator_pid']
            and value['python']['creation_utc'] == context['python_creation_utc']
            and value['python']['command'] == context['suite_python_command'], 'Exact coordinator/Python observation differs')


def validate_raw_host(run, context, state, flat):
    raw = read(run / 'authoritative-host-terminal.json')
    require(sha(raw) == flat['raw_observation_sha256'], 'Raw/flat host receipt hash differs')
    value = json.loads(raw)
    checked = value.get('checked_utc', value.get('observed_utc'))
    require(utc_ns(flat['observed_utc']) >= utc_ns(checked) >= utc_ns(state['finished_utc']), 'Host observation predates terminal completion')
    require(value['source_commit'] == context['source_commit'] and value['suite_exit'] == 0
            and value['state_status'] == 'passed' and Path(value['canonical_run']) == run
            and value['owned_runtime_command_matches_absent'] is True and value['owned_runtime_matches'] == []
            and value['no_process_killed'] is True, 'Raw host closure differs')
    for role, pid_key, birth_key in [('coordinator', 'coordinator_pid', 'coordinator_creation_utc'),
                                     ('python', 'python_pid', 'python_creation_utc')]:
        row = value[role]
        require(row['pid'] == context[pid_key] and row['expected_creation_utc'] == context[birth_key]
                and row['original_absent'] is True, 'Wrong exact host birth/absence: ' + role)
        require((row['pid_present'] is False and row['current_creation_utc'] is None)
                or (row['pid_present'] is True and utc_ns(row['current_creation_utc']) != utc_ns(row['expected_creation_utc'])),
                'Live original identity or unsupported PID observation: ' + role)
    validate_live(run, context)
    return value


def validate_scoped(root, context, canonical_sources):
    packet = root / context['scoped_native_packet']
    raw = read(packet / 'INDEX.json')
    require(sha(raw) == context['scoped_native_packet_index_sha256'], 'Scoped native packet INDEX changed')
    index = json.loads(raw)
    require(len(index['files']) == context['scoped_native_payload_files'] and sum(row['bytes'] for row in index['files'])
            == context['scoped_native_payload_bytes'], 'Scoped native packet catalogue differs')
    for row in index['files']:
        relative = Path(row['path'])
        require(not relative.is_absolute() and '..' not in relative.parts, 'Scoped packet path escaped')
        basename = relative.name.removesuffix('.gz')
        require(basename not in {'expected.json', 'parameters.json', 'crosswalk-proof.json'}
                and not any(part in {'fixture', 'fixtures', 'inputs', 'assets'} or part.endswith('.assets') for part in relative.parts),
                'Private scoped fixture/full report refused')
        value = read(packet / relative)
        require(len(value) == row['bytes'] and sha(value) == row['sha256'], 'Scoped packet payload changed')
        if relative.suffix == '.json': reject_native_payload(json.loads(value))
        elif relative.name.endswith('.json.gz'): reject_native_payload(json.loads(gzip.decompress(value)))
    aliases = load(packet / 'ALIASES.json')['files']
    for row in aliases:
        stored = Path(row['stored'])
        require(not stored.is_absolute() and '..' not in stored.parts and row['raw_bytes'] <= MAXIMUM
                and Path(row['logical']).name not in {'expected.json', 'parameters.json', 'crosswalk-proof.json'}, 'Invalid scoped alias')
        value = read(packet / stored)
        if stored.suffix == '.gz': value = gzip.decompress(value)
        require(len(value) == row['raw_bytes'] and sha(value) == row['raw_sha256'], 'Scoped raw alias roundtrip failed')
    source_alias = next(row for row in aliases if row['logical'] == 'native/source-before.json')
    source_raw = read(packet / source_alias['stored'])
    if source_alias['stored'].endswith('.gz'): source_raw = gzip.decompress(source_raw)
    scoped_sources = json.loads(source_raw)
    require(all(name in scoped_sources['files'] for name in canonical_sources['source_sha256']),
            'Scoped native packet omits a canonical functional file')
    delta_proof = validate_reviewed_delta(root, context, canonical_sources, scoped_sources)
    return {'INDEX_sha256': context['scoped_native_packet_index_sha256'], 'payload_files': len(index['files']),
            'payload_bytes': context['scoped_native_payload_bytes'], 'raw_aliases_verified': len(aliases),
            'functional_source_hashes_equal': delta_proof['byte_equal_files'],
            'reviewed_provenance_test_delta': delta_proof,
            'scoped_run_revision': scoped_sources['revision'], 'canonical_revision': context['source_commit'],
            'source_context': 'Scoped native working matrix and fresh canonical are distinct runs. All1006 remaining functional files match exactly; only two independently reviewed default provenance-test files differ. No full native fidelity claim.'}


def validate_reviewed_delta(root, context, canonical_sources, scoped_sources):
    """Admit exactly the pinned provenance correction, never a wildcard repin."""
    expected = context['reviewed_provenance_delta']
    packet = root / expected['packet']
    raw = read(packet / 'INDEX.json')
    require(sha(raw) == expected['INDEX_sha256'], 'Reviewed provenance packet INDEX differs')
    index = json.loads(raw)
    require(index['file_count'] == len(index['files']) == expected['payload_files']
            and index['bytes'] == sum(row['bytes'] for row in index['files']) == expected['payload_bytes'],
            'Reviewed provenance packet catalogue differs')
    for row in index['files']:
        relative = Path(row['path'])
        require(not relative.is_absolute() and '..' not in relative.parts, 'Reviewed provenance path escaped')
        value = read(packet / relative)
        require(len(value) == row['bytes'] and sha(value) == row['sha256'], 'Reviewed provenance payload differs')
        if relative.suffix == '.json': reject_native_payload(json.loads(value))
    aliases = load(packet / 'ALIASES.json')['aliases']
    for row in aliases:
        relative = Path(row['payload'])
        require(not relative.is_absolute() and '..' not in relative.parts and 0 <= row['raw_bytes'] <= MAXIMUM
                and Path(row['original']).suffix in {'.json', '.py', '.gd', '.log', '.txt'},
                'Reviewed provenance alias scope differs')
        packed = read(packet / relative)
        require(len(packed) == row['payload_bytes'] and sha(packed) == row['payload_sha256'] and row['codec'] == 'gzip',
                'Reviewed provenance alias storage differs')
        value = gzip.decompress(packed)
        require(len(value) == row['raw_bytes'] and sha(value) == row['raw_sha256'],
                'Reviewed provenance alias is not lossless')
    summary = load(packet / 'SUMMARY.json')
    delta = load(packet / 'TWO_FILE_DELTA.json')
    names = {'tests/helper_preview_port_files.json', 'tests/verify_helper_preview.py'}
    require(summary['source_baseline'] == delta['baseline'] == expected['source_baseline']
            and set(summary['source_changes']) == names and summary['production_sources_modified'] is False
            and summary['reviewed_rows'] == 25 and summary['unchanged_reviewed_rows'] == 22
            and summary['source_context'] == 'main_working_source_snapshot'
            and summary['checks'] == {'cpu': 208, 'transport': 11, 'adapter': 128, 'host': 69,
                                     'graphical': 266, 'focused': 221, 'peers': 45}
            and summary['verification']['cpu']['passed'] is True and summary['verification']['graphical']['passed'] is True
            and all(flag is True for scope in summary['preservation'].values() for flag in scope.values()),
            'Independent provenance correction review/check scope differs')
    require(delta['changes'] == expected['permitted_changes'] and delta['production_source_changes'] == []
            and delta['other_canonical_source_hashes_identical'] == expected['byte_equal_files'] == 1006
            and delta['source_count'] == expected['canonical_source_files'] == 1008
            and len(canonical_sources['source_sha256']) == 1008 and len(delta['changes']) == 2
            and {row['path'] for row in delta['changes']} == names
            and scoped_sources['revision'] == expected['scoped_source_revision'], 'Pinned two-file delta differs')
    actual = {name for name, value in canonical_sources['source_sha256'].items()
              if scoped_sources['files'][name]['sha256'] != value}
    require(actual == names, 'Unreviewed scoped-native/canonical source difference')
    for row in delta['changes']:
        require(row['changed'] is True and row['failed_full_raw_sha256'] != row['reviewed_retry_raw_sha256']
                and row['failed_full_raw_sha256'] == scoped_sources['files'][row['path']]['sha256']
                and row['reviewed_retry_raw_sha256'] == canonical_sources['source_sha256'][row['path']],
                'Reviewed old/new source hash join differs')
    return {'packet': expected['packet'], 'INDEX_sha256': expected['INDEX_sha256'],
            'payload_files': len(index['files']), 'payload_bytes': index['bytes'],
            'raw_aliases_verified': len(aliases), 'canonical_source_files': 1008, 'byte_equal_files': 1006,
            'reviewed_differences': delta['changes'], 'production_source_differences': 0,
            'scoped_source_revision': scoped_sources['revision'], 'canonical_source_revision': context['source_commit'],
            'scoped_native_checks_rerun_for_new_test_bytes': False,
            'claim': 'Exact app/runtime/harness bytes plus separately reviewed two-file provenance-test correction; distinct source contexts and runs retained.'}
