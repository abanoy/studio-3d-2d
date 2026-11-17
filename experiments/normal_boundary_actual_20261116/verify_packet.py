"""Read-only normal diagnostic archive verifier; no engines, CIM, or source writes."""
from pathlib import Path
import ast, gzip, hashlib, json, math, re
HERE = Path(__file__).resolve().parent
HEAD = '52f63c944ded7a651da871524d23a345b606424d'
PRIVATE_SHA = '0ef144f3ffe093d6c01f31e5e6fadf98e87a5c7de2b4013c27d42809dabd6921'
def sha(raw): return hashlib.sha256(raw).hexdigest()
def read(name):
    path = HERE / name
    assert path.resolve().is_relative_to(HERE) and not path.is_symlink()
    return path.read_bytes()
def load(name): return json.loads(read(name))
def privacy(value, path='$'):
    if isinstance(value, dict):
        for key, item in value.items():
            assert key not in {'vertex_positions', 'vertex_buffer', 'index_buffer', 'image_data', 'audio_data', 'PCM', 'base64',
                               'Blender_matrix_local_row_major', 'native_rest_words_uint32', 'native_rest_matrices', 'rest_matrices', 'world_vertices'}
            assert not (key in {'vertices', 'indices', 'triangles', 'pose', 'poses', 'normal', 'normals', 'basis', 'transform', 'transforms'} and isinstance(item, (list, dict)))
            privacy(item, path + '.' + key)
    elif isinstance(value, list):
        if value and all(type(x) in (int, float) for x in value):
            allowed = (path.endswith('.requested_size_pixels') and value == [0, 0]) or (path == '$.shared_catalogue_counts' and value == [6, 574, 120])
            allowed = allowed or bool(re.fullmatch(r'\$\.samples\[\d+\]\.stamps_before_open_after_final\[\d+\]', path)) and len(value) == 6 and all(type(x) is int for x in value)
            assert allowed, ('Unapproved numeric array', path)
        for index, item in enumerate(value): privacy(item, path + '[' + str(index) + ']')
    elif isinstance(value, float): assert math.isfinite(value)

def main():
    checks = 0
    index = load('INDEX.json')
    expected = {row['path'] for row in index['files']}
    actual = {p.relative_to(HERE).as_posix() for p in HERE.rglob('*') if p.is_file() and p != HERE / 'INDEX.json' and '__pycache__' not in p.parts}
    assert expected == actual and len(expected) == index['payload_files']
    assert sum(row['bytes'] for row in index['files']) == index['payload_bytes']
    for row in index['files']:
        raw = read(row['path'])
        assert len(raw) == row['bytes'] and sha(raw) == row['sha256']; checks += 1
        assert len(raw) < 500_000
        assert not row['path'].lower().endswith(('.glb', '.mdl', '.vvd', '.blend', '.has', '.png', '.jpg', '.wav', '.mp4'))
        assert Path(row['path']).name != 'PRIVATE_NORMALS.json'
        if row['path'].endswith('.json'): privacy(json.loads(raw))
        if row['path'].endswith('.gz'): privacy(json.loads(gzip.decompress(raw)))
        if row['path'].endswith('.py'): ast.parse(raw)
    manifest = load('SOURCE_MANIFEST.json')
    assert not manifest['raw_full_report_copied'] and not manifest['private_normals_copied']
    for row in manifest['copies']:
        packed = read(row['payload']); raw = gzip.decompress(packed) if row['codec'] == 'gzip' else packed
        assert len(packed) == row['payload_bytes'] and sha(packed) == row['payload_sha256']
        assert len(raw) == row['raw_bytes'] and sha(raw) == row['raw_sha256']; checks += 1
    assert len(manifest['copies']) == manifest['exact_copy_count']
    for label in ('original', 'sentinel'):
        assert sha(read('source/' + label + '/INDEX.json')) == manifest['source_packet_indexes'][label]
        source_index = load('source/' + label + '/INDEX.json')['files']
        rows = source_index.items() if isinstance(source_index, dict) else ((row['path'], row) for row in source_index)
        for name, row in rows:
            raw = read('source/' + label + '/' + name)
            assert sha(raw) == row['sha256'] and len(raw) == row['bytes']; checks += 1
    original = ast.parse(read('source/original/capture_blender_normals.py'))
    sentinel = ast.parse(read('source/sentinel/capture_blender_normals.py'))
    old_functions = {n.name: ast.dump(n, include_attributes=False) for n in original.body if isinstance(n, ast.FunctionDef)}
    new_functions = {n.name: ast.dump(n, include_attributes=False) for n in sentinel.body if isinstance(n, ast.FunctionDef)}
    assert set(old_functions) == {'digest', 'main', 'matrix_rows', 'normalized', 'require', 'safe_path'}
    assert all(new_functions[key] == value for key, value in old_functions.items()); checks += len(old_functions)
    for name in ('probe_support.py', 'normal_metrics.py', 'compare_private_normals.py', 'stage_after_full_pass.py', 'test_probe_support.py'):
        assert read('source/original/' + name) == read('source/sentinel/' + name); checks += 1
    source_before = gzip.decompress(read('context/full/source-before.json.gz'))
    assert source_before == gzip.decompress(read('context/full/source-after.json.gz'))
    source_map = json.loads(source_before)
    assert source_map['commit'] == HEAD and len(source_map['source_sha256']) == 1019
    assert source_map['source_sha256']['tools/private_desktop.py'] == sha(read('source/locked/private_desktop.py'))
    lock_raw = gzip.decompress(read('context/input-lock.json.gz')); lock = json.loads(lock_raw)
    assert sha(lock_raw) == '3bb7c2ce75f55dcb53143aab0df5ab8b39c68180617092664a579126fb09cfb6'
    assert len(lock['runtime_executables']) == 6 and len(lock['sourceio_files']) == 574 and len(lock['exporter_noncache_sources']) == 120
    full_names = {'state': 'state.json', 'launch': 'launch.json', 'birth': 'root-birth-observation.json',
                  'source_before': 'source-before.json.gz', 'source_after': 'source-after.json.gz',
                  'host': 'authoritative-host-termination.json', 'raw_host': 'authoritative-host-terminal.json', 'release': 'graphics-lease-released.json'}
    full_state = load('context/full/state.json'); release = load('context/full/graphics-lease-released.json')
    assert full_state['status'] == 'passed' and full_state['suite_exit'] == 0 and full_state['source_unchanged']
    assert release['released'] and release['all_private_jobs_closed'] and release['source_commit'] == HEAD
    assert release['canonical_state_sha256'] == sha(read('context/full/state.json'))
    retention = load('PRIVATE_DATA_RETENTION.json')
    assert retention['exact_private_capture_bytes_equal'] and not retention['private_arrays_published'] and not retention['art_or_raw_full_report_copied']
    required = load('source/sentinel/ROOT_ADDITIONAL_REQUIREMENTS.json')['public_field_required_values']
    records = []
    for number in (1, 2):
        prefix = 'attempt' + str(number) + '/'
        lease = load(prefix + 'lease.json'); staged = load(prefix + 'STAGED.json'); prepared = load(prefix + 'ROOT_COMMANDS.json')
        public = load(prefix + 'capture/PUBLIC_CAPTURE.json'); receipt = load(prefix + 'private-receipt.json')
        verification = load(prefix + 'root-execution/verification.json'); process = load(prefix + 'root-execution/capture-process.json')
        start = load(prefix + 'root-execution/capture-start.json'); command = load(prefix + 'root-execution/capture-command.json')
        assert staged['lease_sha256'] == public['lease_sha256'] == sha(read(prefix + 'lease.json'))
        assert lease['HEAD'] == public['HEAD'] == public['full_source_commit'] == HEAD
        assert lease['full_terminal_status'] == 'PASS' and lease['root_authoritative_closure'] and not lease['publish_private_arrays']
        assert lease['full_context']['functional_count'] == staged['functional_count'] == 1019
        assert len(lease['files']) == staged['exact_primary_file_locks'] == 12 and len(lease['analysis_files']) == staged['supplemental_analysis_sources'] == 4
        assert lease['approved_shared_input_lock_sha256'] == sha(lock_raw)
        for label, name in full_names.items():
            raw = read('context/full/' + name)
            if name.endswith('.gz'): raw = gzip.decompress(raw)
            assert lease['full_context']['files'][label]['sha256'] == sha(raw); checks += 1
        assert lease['full_context']['files']['report']['sha256'] == release['full_report_sha256']
        assert public['input_hashes'] == {k: row['sha256'] for k, row in lease['files'].items()}
        assert public['analysis_hashes'] == {k: row['sha256'] for k, row in lease['analysis_files'].items()}
        assert public['status'] == 'CAPTURE_COMPLETE_COMPARISON_UNRUN' and public['inputs_unchanged']
        assert not any(public[key] for key in ('installed_sources_modified', 'original_blend_saved', 'exporter_invoked', 'SourceIO_imported'))
        assert public['private_sha256'] == PRIVATE_SHA and public['private_bytes'] == 17627667
        assert public['vertices'] == 9661 and public['corners'] == 42702 and public['objects'] == 2
        assert retention['files'][number-1]['sha256'] == PRIVATE_SHA and not retention['files'][number-1]['copied']
        assert command == prepared['capture_command'] and process == verification['capture'] and process['pid'] == start['pid']
        assert process['retained_Popen_reaped'] and not process['timed_out'] and not process['owned_wrapper_terminated']
        assert receipt['exit'] == process['exit'] and receipt['job_closed'] and receipt['desktop_closed']
        assert not receipt['desktop_switch_requested'] and not receipt['foreground_child_observed']
        assert verification['runtime_lease_released'] and verification['lease_and_all_input_context_rechecked'] and not verification['normal_fidelity_pass_claimed']
        assert verification['public_capture_sha256'] == sha(read(prefix + 'capture/PUBLIC_CAPTURE.json'))
        for phase in ('before', 'after'):
            observed = load(prefix + 'root-execution/' + phase + '-closure.json')
            assert observed['owned_count'] == 0 and observed == json.loads(read(prefix + 'root-execution/' + phase + '-inventory-stdout.log'))
            assert not read(prefix + 'root-execution/' + phase + '-inventory-stderr.log')
        assert not read(prefix + 'root-execution/capture-stderr.log')
        stdout = read(prefix + 'root-execution/capture-stdout.log').decode()
        capture_markers = [json.loads(line[len('HAS_NORMAL_CAPTURE '):]) for line in stdout.splitlines() if line.startswith('HAS_NORMAL_CAPTURE ')]
        assert len(capture_markers) == 1
        historical_public = dict(public); historical_public.pop('background_isolation_sentinel', None)
        assert capture_markers[0] == historical_public
        for line in stdout.splitlines():
            if line.startswith('HAS_NORMAL_CAPTURE ') or line.startswith('HAS_NORMAL_ISOLATION_SENTINEL '): privacy(json.loads(line.split(' ', 1)[1]))
            elif line.strip(): assert re.fullmatch(r'\d+:\d+\.\d+\s+blend\s+\| Read blend: ".*editable\.blend"|Blender 5\.1\.2 \(hash [a-z0-9]+ built [0-9-]+ [0-9:]+\)|Blender quit', line)
        if number == 1:
            assert process['exit'] == 2 and not receipt['private_window_seen'] and not receipt['child_desktop_confirmed']
            assert receipt['error'] == 'No owned graphical window was verified on the private desktop'
            assert not verification['diagnostic_completed'] and verification['comparison'] is None and not verification['private_job_desktop_closed']
            assert verification['comparison_sha256'] is None and 'HAS_NORMAL_ISOLATION_SENTINEL ' not in stdout
            assert not any(name.startswith(prefix + 'root-execution/comparison-') for name in expected)
        else:
            assert process['exit'] == 0 and receipt['private_window_seen'] and receipt['child_desktop_confirmed']
            assert verification['diagnostic_completed'] and verification['private_job_desktop_closed']
            policy = public['background_isolation_sentinel']
            assert all(type(policy.get(k)) is type(v) and policy.get(k) == v for k, v in required.items())
            markers = [json.loads(line[len('HAS_NORMAL_ISOLATION_SENTINEL '):]) for line in stdout.splitlines() if line.startswith('HAS_NORMAL_ISOLATION_SENTINEL ')]
            assert markers == [policy]
            comparison_process = load(prefix + 'root-execution/comparison-process.json')
            assert comparison_process == verification['comparison'] and comparison_process['exit'] == 0
            assert comparison_process['retained_Popen_reaped'] and not comparison_process['timed_out'] and not comparison_process['owned_wrapper_terminated']
            assert load(prefix + 'root-execution/comparison-command.json') == prepared['comparison_command']
            assert not read(prefix + 'root-execution/comparison-stderr.log')
            privacy(load(prefix + 'root-execution/comparison-stdout.log'))
        records.append(verification); checks += 25
    comparison = load('attempt2/BLENDER_BOUNDARY_COMPARISON.json')
    assert sha(read('attempt2/BLENDER_BOUNDARY_COMPARISON.json')) == records[1]['comparison_sha256'] == '7548b23cfcad071c167695ef09c747626f9d6e308403ec41d67000df04d5246f'
    assert comparison['status'] == records[1]['comparison_status'] == 'COHERENT_BOUNDARY_MEASUREMENT'
    assert comparison['private_capture_sha256'] == PRIVATE_SHA and not comparison['private_arrays_published'] and not comparison['native_runtime_launched_by_analysis']
    assert comparison['original_raw_gate']['historical_failure_reproduced'] and comparison['original_raw_gate']['threshold'] == 2e-5
    gate = comparison['original_raw_gate']['raw_metrics']
    assert gate['count'] == 9661 and gate['diagnostic_above_2e_5'] == 8364 and gate['max'] == 0.00121654672362075
    assert comparison['matched_exported_vertices'] == 9661 and comparison['unmatched_exported_vertices'] == 0
    assert comparison['exporter_prediction_error']['count'] == 9661 and comparison['exporter_prediction_error']['max'] == 0.0
    assert comparison['metrics']['native_raw_to_blender_transported_raw']['raw_distance']['diagnostic_above_2e_5'] == 2108
    assert comparison['metrics']['blender_transported_raw_to_glb_raw']['raw_distance']['diagnostic_above_2e_5'] == 8249
    assert comparison['multiple_exact_normal_classes'] == 8 and comparison['original_native_match_ambiguities'] == 4
    assert comparison['native_to_blender_all_candidate_bounds']['raw_worst']['diagnostic_above_2e_5'] == 2113
    ffmpeg = load('preflight/normal-preflight-runtime-stamps-20261116.json')
    assert ffmpeg['cause'] == 'UNDETERMINED' and len(ffmpeg['samples']) == 3
    for sample in ffmpeg['samples']:
        assert sample['all_stamps_equal'] and len(sample['stamps_before_open_after_final']) == 4
        assert all(stamp == sample['stamps_before_open_after_final'][0] for stamp in sample['stamps_before_open_after_final'])
        assert sample['sha256'] == lock['runtime_executables'][ffmpeg['path']]['sha256']; checks += 1
    for suffix, passed in (('1794872690018354700', False), ('1794872697847387300', True)):
        trace = load('preflight/normal-runtime-stage-trace-' + suffix + '.json')
        assert trace['all_six_passed'] and trace['no_gate_modified'] and trace['stager_invoked'] and trace['stager_passed'] is passed
        assert len(trace['samples']) == 6
        assert all(row['passed'] and row['identity'] == lock['runtime_executables'][row['path']] for row in trace['samples'])
        if not passed: assert trace['stager_refusal'] == {'error': "No module named 'probe_support'", 'type': 'ModuleNotFoundError'}
        checks += 7
    benchmark = load('BENCHMARK.json')
    assert benchmark['normal_fidelity'] == 'FAILED_UNQUALIFIED' and benchmark['original_failures'] == 8364
    assert benchmark['new_acceptance_checks_claimed'] == 0 and benchmark['human_review'] == 'DEFERRED_NO_RESULT'
    assert benchmark['attempt1']['capture'] == records[0]['capture'] and benchmark['attempt2']['capture'] == records[1]['capture'] and benchmark['attempt2']['comparison'] == records[1]['comparison']
    negatives = [{'vertices': [[0, 0, 0]]}, {'normals': [[0, 0, 1]]}, {'native_rest_matrices': {}}, {'basis': [1, 2, 3]}, {'unexpected': [1, 2, 3]}, {'requested_size_pixels': [1, 2, 3]}]
    for bad in negatives:
        try: privacy(bad)
        except AssertionError: pass
        else: raise AssertionError('Privacy negative control admitted')
    print(json.dumps({'archive_audit_passed': True, 'checks': checks, 'payload_files': len(expected),
                      'exact_copies': len(manifest['copies']), 'privacy_negative_controls': len(negatives),
                      'native_engines_started': 0, 'process_queries': 0, 'product_acceptance_checks_added': 0,
                      'normal_fidelity': 'FAILED_UNQUALIFIED', 'index_sha256': sha(read('INDEX.json'))}))

if __name__ == '__main__': main()
