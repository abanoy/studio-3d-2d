"""Pure scoped joins for the completed authored Source foundation follow-up."""
from pathlib import PureWindowsPath
import hashlib
import json

ROOT_RUN = 'output/neon-foundation-fe9aace-20261117-attempt1/'
REVISION = 'fe9aace86f7a349c90a951ff26d76f746d1e4701'
FIXTURE_SOURCE = '80764dea7982a11f1d42a9bcbfb36b74c44edb6e620ddb585fa37dc1c8ab1e09'
GOLDEN = '39637fa34e53c81708329ab963659e8100a285a92e25a22a92ab5e708c0154c1'


def require(ok, message):
    if not ok: raise ValueError(message)


def same(a, b):
    if type(a) is not type(b): return False
    if type(a) is dict: return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if type(a) is list: return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def load(raw):
    def pairs(rows):
        value = {}
        for key, item in rows:
            require(key not in value, 'Duplicate JSON key'); value[key] = item
        return value
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def relative(value, review):
    return PureWindowsPath(value).relative_to(PureWindowsPath(review)).as_posix()


def check(raw, review):
    def body(path): return raw['REVIEW:' + path]
    def obj(path): return load(body(path))
    result = obj(ROOT_RUN + 'verification.json')
    require(result['format'] == 'has_root_workspace_followup_1' and result['passed'] is True and result['full_suite_pass_claimed'] is False
            and result['all_functional_source_unchanged'] is True and result['functional_source_files'] == 1029 and result['host_scopes_closed'] is True, 'Root scoped result')
    before = obj(ROOT_RUN + 'source-before.json')
    require(len(before) == 1029 and same(before, obj(ROOT_RUN + 'source-after.json')) and before['tests/source_bone_bindings_unit.gd'] == FIXTURE_SOURCE, 'Root exact1029 source preservation')
    for label in ('before', 'foundation-after', 'after'):
        scope = obj(ROOT_RUN + label + '-closure.json')
        require(scope['format'] == 'has_root_workspace_scope_observation_1' and type(scope['owned_count']) is int and scope['owned_count'] == 0
                and scope['owned_matches'] == [] and scope['termination_issued'] is False and scope['matcher_positive_cases'] == 4 and scope['matcher_negative_cases'] == 3, 'Recorded main/review scope')
    require(len(result['rows']) == 1, 'One focused foundation row')
    row = result['rows'][0]
    require(row['label'] == 'foundation' and type(row['exit']) is int and row['exit'] == 0 and row['retained_Popen_reaped'] is True
            and row['timed_out'] is False and row['seconds'] == 12.0645659, 'Exact root process/elapsed result')
    require(same({k: v for k, v in row.items() if k != 'report'}, obj(ROOT_RUN + 'foundation-process.json')), 'Direct root process join')
    report = row['report']; child = relative(report['folder'], review) + '/'
    require(child == ROOT_RUN + 'source-choices/' and same(report, obj(ROOT_RUN + 'foundation-report.json')) and same(report, obj(child + 'verification.json')), 'Root/report/child exact copies')
    command = obj(ROOT_RUN + 'foundation-command.json')
    require(command.count('--output') == 1 and PureWindowsPath(command[command.index('--output') + 1]) == PureWindowsPath(report['folder']), 'Root command output join')
    require(report['format'] == 'has_source_choice_foundation_1' and report['passed'] is True and type(report['checks']) is int and report['checks'] == 167
            and report['source_unchanged'] is True and report['native_conversion'] is False and same(report['separate_checks'], {'crosswalk_cpu': 77, 'bone_bindings_headless': 96}), 'Foundation scope/counts')
    projected = {PureWindowsPath(name).as_posix(): digest for name, digest in report['source_sha256'].items()}
    require(len(projected) == len(report['source_sha256']) and all(before[name] == digest for name, digest in projected.items()), 'Foundation separator-only scoped source projection')
    reports = report['reports']
    require(set(reports) == {'catalogue', 'appearance', 'resource_write', 'bridge_bootstrap', 'jiggle_cpu', 'crosswalk_cpu', 'bone_bindings_headless', 'unit', 'ui'}, 'Original report membership')
    for label, count in [('catalogue', 53), ('appearance', 29)]:
        proof = reports[label]
        require(type(proof['tests']) is int and proof['tests'] == count and type(proof['failures']) is int and proof['failures'] == 0 and type(proof['errors']) is int and proof['errors'] == 0 and proof['passed'] is True and proof['source_preserved'] is True, 'Original CPU table controls')
        status = [load(line) for line in body(child + label + '.log').splitlines() if line.startswith(b'{')]
        require(len(status) == 1, 'Original CPU report-path line')
        folder = relative(status[0]['folder' if label == 'catalogue' else 'run'], review)
        require(folder.startswith('output/source-mdl-choices-cpu/' if label == 'catalogue' else 'output/source-appearance-cpu/'), 'Closed derived CPU domain')
        require(same(proof, obj(folder + '/result.json')), 'Original CPU raw result join')
    require(reports['catalogue']['actual_native_inputs_read'] is False and reports['catalogue']['actual_models_tested'] == 0, 'Authored table scope')
    resource = reports['resource_write']
    require(same([resource['tests'], resource['passed'], resource['skipped']], [7, 6, 1]) and len(resource['long_path_proofs']) == 1, 'Preserve explicit resource-writer skip')
    path_proof = resource['long_path_proofs'][0]
    require(path_proof['logical_path_characters'] > 320 and path_proof['exact_layout'] is True and path_proof['exclusive_refusal_preserved'] is True, 'Original long-path scalar proof')
    require(same([reports['bridge_bootstrap']['tests'], reports['bridge_bootstrap']['passed']], [2, 2]), 'Bridge bootstrap controls')
    for label, count in [('jiggle_cpu', 66), ('crosswalk_cpu', 77)]:
        proof = reports[label]
        require(proof['passed'] is True and type(proof['checks']) is int and proof['checks'] == count and proof['source_unchanged'] is True
                and proof['native_conversion'] is False and proof['graphics'] is False and same(proof, obj(child + label.replace('_', '-') + '/verification.json')), 'Separate CPU result copies/scope')
    unit = reports['unit']; require(same(unit, obj(child + 'unit/result.json')) and unit['checks'] == 65 and unit['failures'] == 0 and unit['headless'] is True and unit['graphics'] is False and unit['native_conversion'] is False, 'Headless unit65 result')
    bindings = reports['bone_bindings_headless']; bound = relative(bindings['folder'], review) + '/'
    require(bound == child + 'bindings-headless/' and same(bindings, obj(bound + 'verification.json')) and bindings['passed'] is True and bindings['checks'] == 96
            and bindings['source_revision'] == REVISION and bindings['functional_source_files'] == 1029 and bindings['source_unchanged'] is True and bindings['runtime_unchanged'] is True
            and bindings['headless'] is True and bindings['graphics'] is False and bindings['native_conversion'] is False and bindings['native_simulation'] is False, 'Separate authored headless96 scope')
    source_before = obj(bound + 'source-before.json'); source_after = obj(bound + 'source-after.json')
    require(same(source_before, source_after) and source_before['commit'] == REVISION and set(source_before['files']) == set(before)
            and all(source_before['files'][name]['sha256'] == digest for name, digest in before.items()), 'Headless exact1029 identity projection')
    require(hashlib.sha256(body(bound + 'source-before.json')).hexdigest() == bindings['source_before_sha256']
            and hashlib.sha256(body(bound + 'source-after.json')).hexdigest() == bindings['source_after_sha256'], 'Headless source snapshot hashes')
    headless_processes = []
    for case, count, script in [('bindings', 79, 'tests/source_bone_bindings_unit.gd'), ('helper', 17, 'tests/source_native_helper_choice_unit.gd')]:
        entry = bindings['reports'][case]; base = bound + case + '/'
        require(entry['checks'] == count and entry['failures'] == 0 and same(entry['result'], obj(base + 'verified.json')), 'Authored headless raw result')
        if case == 'bindings':
            require(same(entry['result'], obj(base + 'fixture/result.json')) and entry['result']['fixture_glb_sha256'] == GOLDEN
                    and entry['result']['source_profile_claim_is_authored_fixture_only'] is True and entry['result']['native_conversion'] is False and entry['result']['native_simulation'] is False, 'Independent authored golden byte identity')
        for stage in ('parse', 'run'):
            process = obj(base + stage + '-process.json'); cmd = obj(base + stage + '-command.json')
            require(same(process, entry[stage]) and process['headless'] is True and process['graphics'] is False and process['native_conversion'] is False and type(process['exit']) is int and process['exit'] == 0
                    and process['timed_out'] is False and process['owned_headless_terminated_on_timeout'] is False, 'Owned headless parse/run metadata')
            require('--headless' in cmd and '--receipt' not in cmd and cmd.count('--script') == 1 and cmd[cmd.index('--script') + 1] == script, 'Headless command/script/no invented private receipt')
            for key, suffix in [('console', '-console.log'), ('engine_log', '-engine.log')]:
                payload = body(base + stage + suffix); require(len(payload) == process[key]['bytes'] and hashlib.sha256(payload).hexdigest() == process[key]['sha256'], 'Headless ordered log identities')
            headless_processes.append({'case': case, 'stage': stage, 'pid': process['pid'], 'exit': 0})
    ui = reports['ui']; require(same(ui, obj(child + 'ui/verification.json')) and same(ui['result'], obj(child + 'ui/result.json')) and ui['result']['checks'] == 20 and ui['result']['failures'] == 0
                              and ui['result']['actual_app'] is True and ui['result']['native_conversion'] is False and ui['source_unchanged'] is True and ui['originals_unchanged'] is True, 'Original private UI20 scope')
    require([x['phase'] for x in ui['result']['actual_metadata_children']] == ['success', 'cancel', 'refusal'], 'Original metadata child phases')
    require('exit' not in ui['result']['actual_metadata_children'][1], 'Do not invent cancellation exit metadata')
    receipt_path = relative(ui['private_receipt'], review)
    require(receipt_path.startswith('output/private-desktop/') and same(obj(receipt_path), ui['receipt'])
            and PureWindowsPath(report['private_receipt']) == PureWindowsPath(ui['private_receipt']), 'One physical/direct/inline private receipt')
    cmd = obj(child + 'ui/command.json')
    require(cmd.count('--receipt') == 1 and PureWindowsPath(cmd[cmd.index('--receipt') + 1]) == PureWindowsPath(ui['private_receipt']), 'Private UI saved command receipt join')
    for key, expected in {'format': 'studio_private_desktop_1', 'exit': 0, 'private_window_seen': True, 'child_desktop_confirmed': True,
                          'foreground_child_observed': False, 'desktop_switch_requested': False, 'job_closed': True, 'desktop_closed': True}.items():
        require(same(ui['receipt'].get(key), expected), 'Strict private UI placement/closure')
    for key, data in raw.items():
        if key.startswith('REVIEW:') and key[7:] in before: require(hashlib.sha256(data).hexdigest() == before[key[7:]], 'Selected original source body differs')
    return {'format': 'has_foundation_fe9_compact_actual_summary_1', 'qualification': 'SCOPED_AUTHORED_FOUNDATION_NO_COMPLETE_FULL_OR_NATIVE_FIDELITY', 'revision': REVISION,
            'root_seconds': 12.0645659, 'foundation_checks': 167, 'foundation_members': {'catalogue': 53, 'appearance': 29, 'headless_unit': 65, 'private_UI': 20},
            'separate_checks': {'crosswalk_cpu': 77, 'bone_bindings_headless': 96}, 'authored_bindings': 79, 'authored_helper': 17, 'jiggle_cpu': 66,
            'resource_write': {'attempted': 7, 'passed': 6, 'explicitly_skipped': 1}, 'bridge_bootstrap': 2, 'functional_source_entries_unchanged': 1029,
            'real_private_desktop_jobs': 1, 'recorded_headless_parse_run_processes': headless_processes, 'headless_private_receipts_fabricated': False,
            'private_receipt_path': receipt_path, 'recorded_main_review_zero_scope_observations': ['before', 'foundation-after', 'after'],
            'metadata_child_scope': 'Original success/cancel/refusal scalar records preserved; cancel has no exit field. No new per-worker physical completion receipt is invented.',
            'full_suite_pass_claimed': False, 'native_fidelity_or_solver_or_adoption_claimed': False, 'decoded_golden_model_art_media_or_native_arrays_included': False,
            'upcoming_full_output_read': False}
