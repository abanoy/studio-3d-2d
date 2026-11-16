"""Independent read-only stdlib verifier; never executes frozen source or helpers."""
from pathlib import Path, PurePosixPath
import gzip
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
SHA = re.compile(r'^[0-9a-f]{64}$')
COMMIT = 'dbf0bc1145f74b5bbff814ec6a417ccd23ce0885'
CASES = ['controls-queue-free', 'focus-free', 'setup-free', 'focus-detach']
ANCHORS = {
    'tools/build_owner_review_snapshot.py': '48d6fc852ae16c946431addd39ec152e5db45c7f887bc1ddc941fc332911a0ce',
    'tests/verify_world_selection_teardown.py': '137322921a83fcbb6cee558cb951ede5f3691c4c96e5b1ab7abdb735680f0bfb',
    'tests/test_owner_review_snapshot.py': 'd771929e26202724a0c70918be1a90320d156e724eaa1a3b2e8f63ca22f268b8',
    'tests/world_selection_teardown.gd': '0b536c255e52cd335b5f5f609883b95a1e63b5dbad6faa14d0daf989f5d1afc0',
    'tests/verify.py': '459b90eeeae9d5523654c07fcbb3de27dad0e889943f46947333e8eb5a65437a'}
OLD_ANCHORS = {
    'tools/build_owner_review_snapshot.py': '7c9487ad1d3c5a6c31f66df9f5b7b73effe9c4668e2a6601dff8196dd87a21f9',
    'tests/verify_world_selection_teardown.py': 'bcd1f87c18eff70af0e5d59b1f9ea1dac5e586911082d3d8a4f4fcef6123adbb',
    'tests/test_owner_review_snapshot.py': '46ba929e1e3efc3891e091a383edb69fb86c7606c8016f19ca0103d5a0f3adcb'}
CHECKS = 0

def check(condition, label):
    global CHECKS
    CHECKS += 1
    if not condition:
        raise AssertionError(label)

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def safe_name(name):
    path = PurePosixPath(name)
    check(isinstance(name, str) and bool(name) and not path.is_absolute(), 'relative path')
    check('\\' not in name and ':' not in name and '\x00' not in name,
          'portable path separators')
    check(all(p not in ('', '.', '..') for p in path.parts) and str(path) == name,
          'normalized path')
    return path

def load(name):
    return json.loads((HERE / name).read_bytes())

def catalogue(value, count):
    check(isinstance(value, dict) and len(value) == count, 'exact catalogue count')
    folded = set()
    for name, sha in value.items():
        safe_name(name)
        check(SHA.fullmatch(sha) is not None, 'catalogue SHA256 only')
        check(name.casefold() not in folded, 'catalogue collision')
        folded.add(name.casefold())

def private_receipt(value):
    check(value['format'] == 'studio_private_desktop_1', 'receipt format')
    check(value['exit'] == 0 and value['job_closed'] is True and value['desktop_closed'] is True,
          'private job/desktop closed exit0')
    check(value['private_window_seen'] is True and value['child_desktop_confirmed'] is True,
          'actual private desktop observed')
    check(value['foreground_child_observed'] is False and value['desktop_switch_requested'] is False,
          'no focus/switch')

def privacy_json(value, trail=()):
    # This operates on metadata JSON, not source code. No geometry/PCM payloads
    # or encoded binary fields belong in these exact retained records.
    forbidden = {'vertices', 'vertex_data', 'positions', 'normals', 'tangents',
                 'indices', 'rest_matrices', 'rest_transforms', 'inverse_bind_matrices',
                 'pcm', 'pcm_samples', 'audio_samples', 'image_base64', 'binary_blob',
                 'buffer_bytes', 'geometry', 'image_data', 'data_uri'}
    if isinstance(value, dict):
        for key, item in value.items():
            check(isinstance(key, str) and key.casefold() not in forbidden,
                  'metadata key privacy: ' + '/'.join(trail + (str(key),)))
            privacy_json(item, trail + (key,))
    elif isinstance(value, list):
        check(not (len(value) > 16 and all(isinstance(x, (int, float)) for x in value)),
              'no numeric payload arrays')
        for item in value:
            privacy_json(item, trail)
    elif isinstance(value, str):
        check(not value.startswith(('data:', 'iVBORw0KGgo', 'UklGR')),
              'no encoded binary media')

def main():
    index = load('INDEX.json')
    check(index['format'] == 'has_runtime_snapshot_repair_actual_index_1', 'index format')
    check(isinstance(index['files'], list), 'this packet list index schema')
    rows = index['files']
    expected = {r['path'] for r in rows}
    actual = {p.relative_to(HERE).as_posix() for p in HERE.rglob('*') if p.is_file()}
    check(len(rows) == len(expected) and actual == expected | {'INDEX.json'}, 'exact file inventory')
    check(len({n.casefold() for n in expected}) == len(expected), 'packet path collision')
    for path in HERE.rglob('*'):
        check(not path.is_symlink(), 'packet no symlink')
    forbidden_suffixes = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg', '.glb', '.gltf',
                          '.has', '.mdl', '.vvd', '.vtx', '.bsp', '.gma', '.pcf', '.wav',
                          '.mp3', '.mp4', '.ogg', '.bin', '.blend', '.pmx', '.vrm', '.vpk'}
    for row in rows:
        name = row['path']
        path = safe_name(name)
        check(path.suffix not in forbidden_suffixes, 'no media/native extension')
        check('shipped-source' not in path.parts and 'stage' not in path.parts,
              'no stage tree packet paths')
        raw = (HERE / name).read_bytes()
        check(len(raw) == row['bytes'] and digest(raw) == row['sha256'], 'index raw bytes/hash')
        check(not raw.startswith((b'\x89PNG', b'glTF', b'RIFF', b'IDST', b'IDSV', b'PK\x03\x04')),
              'no binary media/native/container magic')

    manifest = load('SOURCE_MANIFEST.json')
    check(manifest['format'] == 'has_runtime_snapshot_exact_copy_manifest_1', 'copy manifest format')
    copies = {r['path']: r for r in manifest['files']}
    check(len(copies) == len(manifest['files']), 'copy manifest no duplicate')
    originals = {}
    for name, row in copies.items():
        check(name in expected, 'copy indexed')
        safe_name(row['source'])
        stored = (HERE / name).read_bytes()
        check(digest(stored) == row['sha256'] and len(stored) == row['bytes'], 'copy storage hash')
        if row['encoding'] == 'deterministic_gzip':
            check(name.endswith('.json.gz') and stored[4:8] == b'\x00\x00\x00\x00', 'deterministic JSON gzip')
            raw = gzip.decompress(stored)
            check(gzip.compress(raw, compresslevel=9, mtime=0) == stored, 'exact deterministic compression')
        else:
            check(row['encoding'] == 'raw', 'raw encoding enum')
            raw = stored
        check(digest(raw) == row['raw_sha256'] and len(raw) == row['raw_bytes'], 'raw original hash/size')
        originals[name.removesuffix('.gz')] = raw
        if row['source'].endswith('.json'):
            privacy_json(json.loads(raw))
    def raw(name):
        return originals[name]
    def data(name):
        return json.loads(raw(name))

    state = data('raw/failed_full/state.json')
    check(state['status'] == 'failed' and state['suite_exit'] == 1 and state['source_commit'] == COMMIT,
          'full failure preserved')
    check(state['source_unchanged'] is True, 'full source unchanged')
    log = raw('raw/failed_full/canonical.log').decode('utf-8')
    check(len(re.findall(r'^PASS ', log, re.M)) == 36, 'exact36 core pass lines')
    check('subprocess.TimeoutExpired' in log and 'timed out after 180 seconds' in log
          and 'verify_world_selection_teardown.py' in log, 'exact outer timeout trace')
    old_before = data('raw/failed_full/source-before.json')
    check(old_before['commit'] == COMMIT, 'failed source commit')
    check(raw('raw/failed_full/source-before.json') == raw('raw/failed_full/source-after.json'),
          'failed exact before-after raw')
    catalogue(old_before['source_sha256'], 1014)
    current_before = data('raw/scoped_replay/source-before.json')
    catalogue(current_before, 1015)
    check(raw('raw/scoped_replay/source-before.json') == raw('raw/scoped_replay/source-after.json'),
          'scoped exact before-after raw')
    check(set(current_before) - set(old_before['source_sha256']) == {'dependencies.json'} and
          not (set(old_before['source_sha256']) - set(current_before)), 'observation coverage difference')
    changed = {n for n, sha in old_before['source_sha256'].items() if current_before[n] != sha}
    check(changed == set(OLD_ANCHORS), 'only reviewed3 overlapping source changes')

    for folder, count in (('failed_teardown', 6023), ('scoped_teardown', 1024)):
        p = data('raw/' + folder + '/provenance.json')
        v = data('raw/' + folder + '/verification.json')
        catalogue(p['source_sha256'], count)
        check(p['source_sha256'] == p['baseline_source_sha256'] == v['source_sha256'] == v['baseline_source_sha256'],
              'exact frozen baseline/catalogues')
        check(p['selected_cases'] == CASES and p['shared_test_sha256'] == ANCHORS['tests/world_selection_teardown.gd'],
              'all4cases/shared script unchanged')
        check(p['revision'] == COMMIT and p['source_mode'] == 'working_tree', 'working bytes atop commit')
        check(v['unchanged_source'] is True and v['unchanged_override'] is True, 'snapshot unchanged')
        private_receipt(v['normal-startup']['receipt'])
        result = data('raw/' + folder + '/result.json')
        check(result['checks'] == 28 and result['failures'] == 0 and [r['case'] for r in result['cases']] == CASES,
              '28 actual assertions/all4cases')
        if folder == 'failed_teardown':
            check('process' not in v and 'result' not in v, 'failed partial wrapper verification')
            check(sum(n.startswith('experiments/') for n in p['source_sha256']) == 4551,
                  'failed experiment count4551')
            check(sum(n.startswith('docs/') for n in p['source_sha256']) == 436, 'failed docs count436')
            for name, sha in OLD_ANCHORS.items():
                check(p['source_sha256'][name] == old_before['source_sha256'][name] == sha, 'old source anchor')
        else:
            check(p['snapshot_scope'] == 'runtime_dependency_closure', 'runtime dependency scope')
            check(not any(n.startswith('experiments/') for n in p['source_sha256']), 'no experiments in runtime snapshot')
            check(sum(n.startswith('docs/') for n in p['source_sha256']) == 1, 'one runtime license doc')
            check(v['result'] == result and v['process']['exit'] == 0, 'completed actual wrapper verification')
            private_receipt(v['process']['receipt'])
            for name, sha in ANCHORS.items():
                check(p['source_sha256'][name] == current_before[name] == sha, 'new source anchor')
    check(raw('raw/failed_teardown/result.json') == raw('raw/scoped_teardown/result.json'), 'unchanged actual28result bytes')

    prior_index = data('prior_failure_review/INDEX.json')
    check(digest(raw('prior_failure_review/INDEX.json')) == '02ac068fc18f177415bd94f8f37909a25e6815a4eea63714fe1652755371f48a',
          'sealed failed review index anchor')
    for row in prior_index['files']:
        content = raw('prior_failure_review/' + row['path'])
        check(len(content) == row['bytes'] and digest(content) == row['sha256'], 'prior sealed file exact')
    audit = data('prior_failure_review/PARTIAL_RECEIPT_AUDIT.json')
    check(audit['physical_receipts'] == audit['unique_desktops'] == audit['exit_0'] == len(audit['rows']) == 46,
          '46 unique closed receipts')
    check(audit['canonical_status'] == 'failed' and audit['full_suite_passed'] is False,
          'receipt audit cannot upgrade full')
    for row in audit['rows']:
        content = raw('prior_failure_review/' + row['stored'])
        check(digest(content) == row['source_sha256'] and len(content) == row['source_bytes'], 'receipt exact source alias')
        check(json.loads(content) == row['receipt'] and row['closed_and_private'] is True, 'receipt embedded equality')
        private_receipt(row['receipt'])
    check(audit['late_receipt_count'] == 1 and audit['late_child_pid'] == 71828 and
          audit['late_child_receipt_after_state_finish_seconds'] == 7.8069579, 'late child distinction')
    closure = data('raw/failed_full/graphics-lease-closed-after-failure.json')
    check(closure['released'] is True and closure['full_suite_passed'] is False and
          closure['observed_partial_private_jobs'] == 46 and closure['all_collected_jobs_desktops_closed_private'] is True,
          'failed lease closed only')
    check(closure['partial_receipt_audit_sha256'] == digest(raw('prior_failure_review/PARTIAL_RECEIPT_AUDIT.json')),
          'failed closure binds receipt audit')
    check(closure['root_manual_or_process_sweep_termination_performed'] is False and
          closure['late_closed_teardown_child_pid'] == 71828, 'termination scope explicit')
    check(closure['released_utc'] == '2026-11-16T02:55:49.6500273Z', 'exact failed release time')
    for label, pid in (('failed_startup', 15912), ('failed_late_child', 71828),
                       ('scoped_startup', 82728), ('scoped_child', 89020)):
        receipt = data('receipts/' + label + '.json')
        private_receipt(receipt)
        check(receipt['child_pid'] == pid, 'explicit child pid')

    replay = data('raw/scoped_replay/verification.json')
    process = data('raw/scoped_replay/process.json')
    check(replay['passed'] is True and replay['full_default_pass_claimed'] is False and
          replay['checks_observed'] == 28 and replay['failures_observed'] == 0 and replay['snapshot_files'] == 1024,
          'scoped pass correctly classified')
    check(replay['process'] == process and process['pid'] == 86500 and process['exit'] == 0 and
          process['retained_Popen_reaped'] is True and process['timed_out'] is False and
          process['owned_wrapper_terminated'] is False and process['timeout_seconds'] == 180 and
          abs(process['seconds'] - 21.763778) < 1e-8, 'actual retained wrapper exit/timing/no timeout')
    check(replay['source_and_runtime_preserved'] is True and replay['runtime_lease_released'] is True,
          'root recorded source/runtime preservation')
    for phase in ('before', 'after'):
        check(data('raw/scoped_replay/' + phase + '-runtime-closure.json')['owned_count'] == 0,
              'recorded scoped owned command absence')
    for row, label in zip(replay['receipts'], ('scoped_startup', 'scoped_child'), strict=True):
        check(row['sha256'] == digest(raw('receipts/' + label + '.json')) and row['passed'] is True,
              'replay binds explicit receipts')

    application = data('raw/application.json')
    check(application['before'] == OLD_ANCHORS and application['after'] == {n: ANCHORS[n] for n in OLD_ANCHORS},
          'exact3file application anchors')
    check(application['packet_index_sha256'] == digest(raw('reviewed_v2/INDEX.json')) ==
          'd7da7eb2c50457d839266eb72d62e277cf3df53b5efe06ce66a2e6d6830091cd', 'sealed v2 exact anchor')
    check(application['timeouts_or_teardown_assertions_changed'] is False, 'unchanged budgets/assertions')
    aliases = load('SOURCE_ALIASES.json')['aliases']
    check(len(aliases) == 10, 'exact five functional/five observer aliases')
    v2 = data('reviewed_v2/INDEX.json')
    check(isinstance(v2['files'], dict), 'actual v2 dictionary schema')
    for name, row in aliases.items():
        content = raw(row['alias'])
        check(digest(content) == row['sha256'], 'frozen source alias hash')
        if name in ANCHORS:
            check(row['sha256'] == ANCHORS[name], 'hard pinned source alias')
        if name in OLD_ANCHORS:
            check(v2['files']['draft/' + name]['sha256'] == row['sha256'], 'v2 draft exact applied bytes')
    driver = raw('source/tests/verify_world_selection_teardown.py').decode('utf-8')
    full = raw('source/tests/verify.py').decode('utf-8')
    check('execute(startup_command, "normal-startup", 60)' in driver and
          'execute(command, "process", 110)' in driver and 'timeout=180' in full,
          'frozen unchanged180/60/110budgets')
    benchmark = data('benchmarks/world_selection_runtime_snapshot_2026-11-15.json')
    check(benchmark['status'] == 'PASSED_SCOPED_REPAIR_FULL_RETRY_REQUIRED' and benchmark['CPU']['checks'] == 27
          and benchmark['CPU']['seconds'] == 4.146 and benchmark['full_default_passed'] is False,
          'root27CPU observation classified separately')
    summary = load('SUMMARY.json')
    privacy_json(summary)
    check(summary['original_full_remains_failed'] is True and summary['full_default_pass_claimed'] is False,
          'summary classifications')
    check(summary['actual_CPU']['basis'] == 'ROOT_REPORTED_OBSERVATION_IN_ROOT_TOOL_TRACE_ONLY' and
          summary['actual_CPU']['raw_stdout_or_PID_claimed'] is False and
          summary['application_preflight']['raw_trace_claimed'] is False, 'no invented CPU/preflight raw evidence')
    check(summary['privacy']['actual_media_copied'] is False and summary['privacy']['actual_stage_source_trees_copied'] is False,
          'privacy scope explicit')
    print(json.dumps({'passed': True, 'checks': CHECKS, 'indexed_files': len(rows),
                      'indexed_bytes': sum(r['bytes'] for r in rows),
                      'exact_copy_files': len(copies), 'failed_full_preserved': True,
                      'scoped_replay_only': True, 'runtime_executed': False,
                      'index_sha256': digest((HERE / 'INDEX.json').read_bytes())}))

if __name__ == '__main__':
    main()
