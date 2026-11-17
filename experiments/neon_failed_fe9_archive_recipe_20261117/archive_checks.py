"""Pure admission of one closed failed full run; no original/native file access."""
from pathlib import PureWindowsPath
import hashlib
import json
import re

REVISION = 'fe9aace86f7a349c90a951ff26d76f746d1e4701'
RUN = 'windows-neon-fe9aace-20261117T040348'
SOURCE = '9792946c73c594e7ff93a8504f842a045f6823d20b789a7b88b9a550deb589fe'
INVENTORY = '90a3c1b10a5fc4fed2196be7c720e26ff899b41b0b47b0a12248dddfe7729cb6'
BIRTHS = {'coordinator': (19668, '2026-11-17T04:04:17.2421226Z'), 'python': (28396, '2026-11-17T04:04:18.1277602Z')}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def same(a, b):
    if type(a) is not type(b):
        return False
    if type(a) is dict:
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if type(a) is list:
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def parse(raw):
    def pairs(rows):
        value = {}
        for key, item in rows:
            need(key not in value, 'Duplicate JSON key')
            value[key] = item
        return value
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def check(raw):
    """Keys name fixed archive aliases; raw receipt bytes stay unmodified."""
    def obj(name):
        return parse(raw[name])
    state, launch, birth = (obj(n) for n in ('state.json', 'launch.json', 'root-birth-observation.json'))
    release, inventory, host = (obj(n) for n in ('graphics-lease-closed.json', 'receipt-inventory.json', 'host-observation.json'))
    need(state['status'] == 'failed' and state['source_commit'] == REVISION and type(state['suite_exit']) is int and state['suite_exit'] == 1 and state['source_unchanged'] is True, 'Exact closed failed state')
    need(state['finished_utc'] == '2026-11-17T04:27:26.4771603Z' and state['pid'] == 19668 and state['process_started'] == BIRTHS['coordinator'][1], 'Closed state identity/time')
    before = obj('source-before.json')
    need(raw['source-before.json'] == raw['source-after.json'] and before['commit'] == REVISION and len(before['source_sha256']) == 1029, 'Exact raw1029 before/after preservation')
    need(all(type(n) is str and type(d) is str and re.fullmatch('[a-f0-9]{64}', d) for n, d in before['source_sha256'].items()), 'Source map types')
    need(before['source_sha256']['tests/verify_shape_catalog.py'] == SOURCE == sha(raw['original-verify_shape_catalog.py']), 'Exact captured failing public wrapper')
    capture = obj('SOURCE_CAPTURE.json')
    need(capture['sha256'] == SOURCE and capture['bytes'] == len(raw['original-verify_shape_catalog.py']) and capture['source_before_sha256'] == sha(raw['source-before.json']), 'Original source witness binding')
    need(launch['source_commit'] == REVISION and launch['functional_source_files'] == 1029 and launch['main_merged'] is False and launch['coordinator_pid'] == 19668 and launch['runner_sha256'] == state['script_sha256'], 'Launch source/tool identity')
    need(sha(raw['runner.ps1']) == launch['runner_sha256'], 'Exact public coordinator source identity')
    need(PureWindowsPath(launch['run_folder']).name == RUN and launch['run_folder'] == state['run_folder'], 'Exact run folder')
    for role, (pid, stamp) in BIRTHS.items():
        need(type(birth[role]['pid']) is int and birth[role]['pid'] == pid and birth[role]['creation_utc'] == stamp, 'Actual GetProcess birth identity')
    need(birth['python']['parent_pid'] == 19668 and birth['python']['command_line'] == '"C:\\Program Files\\Python313\\python.exe" -u tests/verify.py', 'Python parent/command identity')
    api = obj('root-birth-api-detail.json')
    need(api['identity_api'] == 'Get-Process.StartTime' and api['python_get_process_birth'] == BIRTHS['python'][1] and api['CIM_birth_not_used_for_identity'] is True, 'Preserve API precision distinction')
    need(release['released'] is True and release['release_kind'] == 'closed_failed_partial_run' and release['source_commit'] == REVISION and release['canonical_run'] == RUN and release['functional_sources'] == 1029, 'Exact failed release scope')
    need(release['suite_exit'] == 1 and release['full_suite_passed'] is False and release['final_full_report_used'] is False and release['physical_jobs'] == release['physical_receipt_files'] == 68, 'Failed release never uses stale full report')
    need(release['terminal_state_sha256'] == sha(raw['state.json']) and release['receipt_inventory_sha256'] == sha(raw['receipt-inventory.json']) == INVENTORY, 'Raw state/inventory release bindings')
    need(release['released_utc'] == '2026-11-17T04:29:31.8232736Z', 'Actual root release time')
    need(inventory['source_commit'] == REVISION and inventory['suite_status'] == 'failed' and inventory['suite_exit'] == 1 and inventory['full_suite_passed'] is False and inventory['final_full_report_used'] is False, 'Terminal inventory failed domain')
    need(same([inventory[k] for k in ('physical_receipt_files', 'unique_physical_jobs', 'normal_exit0', 'registered_cancel_exit2', 'failed_partial_nonzero', 'duplicate_physical_copies')], [68, 68, 67, 1, 0, 0]), 'Exact physical job counts')
    need(inventory['all_collected_jobs_desktops_closed_private'] is True and inventory['all_inline_exact_physical_matches'] is True and inventory['registered_cancel_observed'] is True, 'Recorded physical closure/inline facts')
    need(same(host, inventory['process_observation']), 'Direct raw root observation')
    for observation in (host, release['second_identity_and_scope_observation']):
        need(observation['owned_runtime_matches'] == [] and observation['owned_runtime_command_matches_absent'] is True and observation['observer_retained_Popen_reaped'] is True and observation['root_observer_issued_no_termination'] is True, 'Recorded host no termination/empty scopes')
        for role, (pid, stamp) in BIRTHS.items():
            row = observation[role]
            need(row['pid'] == pid and row['expected_creation_utc'] == stamp and row['original_absent'] is True and row['pid_present'] is False and row['current_creation_utc'] is None, 'Recorded original process absence identity')
    need(len(inventory['rows']) == 68, 'Exact raw receipt row count')
    desktops, receipts, cancels = set(), [], 0
    for index, row in enumerate(inventory['rows']):
        payload = raw['receipts/%03d.json' % index]
        need(sha(payload) == row['source_sha256'], 'Physical raw receipt byte identity')
        receipt = parse(payload)
        need(same(receipt, row['receipt']), 'Typed physical/inline receipt join')
        need(PureWindowsPath(row['preserved_raw_copy']).parent == PureWindowsPath(state['run_folder']) / 'terminal-audit-attempt1', 'Physical preserved-copy owned run boundary')
        for key, value in {'format': 'studio_private_desktop_1', 'private_window_seen': True, 'child_desktop_confirmed': True, 'foreground_child_observed': False, 'desktop_switch_requested': False, 'job_closed': True, 'desktop_closed': True}.items():
            need(same(receipt.get(key), value), 'Strict physical placement/closure')
        need(type(receipt['desktop']) is str and receipt['desktop'] not in desktops and type(receipt['exit']) is int, 'Unique actual desktop/job')
        desktops.add(receipt['desktop'])
        if row['classification'] == 'registered_Krita_cancel_exit2':
            need(receipt['exit'] == 2 and receipt.get('cancelled') is True and 'source_registered_Krita_cancel' in row['references'], 'Registered Krita cancellation only')
            cancels += 1
        else:
            need(row['classification'] == 'normal_exit0' and receipt['exit'] == 0, 'Normal physical exit zero')
        receipts.append(receipt)
    need(cancels == 1, 'Exactly one registered cancellation')
    need(same(inventory['unique_job_classifications'], {r['receipt']['desktop']: r['classification'] for r in inventory['rows']}), 'Physical classification crossjoin')
    for inline in inventory['inline_receipts']:
        need(any(same(inline['receipt'], physical) for physical in receipts), 'Every recorded inline receipt has exact physical witness')
    log = raw['canonical.log'].decode('utf-8')
    stale = r'C:\Users\noble\.codex\worktrees\ec34\cloudflare\hybrid-animation-studio\output\sfm-face-integration\1793571300524663600\prepared-head\scene.glb'
    need('tests/verify_shape_catalog.py' in log and 'FileNotFoundError: [Errno 2]' in log and repr(stale) in log and 'path.read_bytes()' in log, 'Retain exact failing stale-bundle traceback')
    need(log.index('PASS animated shapes, native GPU, blocks, clipboard, helper capture, recovery and movie') < log.index('Traceback (most recent call last):'), 'Earlier stage passes precede failure in ordered canonical log')
    source = raw['original-verify_shape_catalog.py'].decode('utf-8')
    need("face=ROOT/'output/sfm-face-pilot.json'" in source and source.index('path.read_bytes()') < source.index("unit=execute("), 'Original wrapper bypass and pre-execute failure site')
    return {'format': 'has_neon_fe9_closed_failed_full_1', 'candidate': REVISION, 'full_suite_passed': False, 'main_merged': False, 'functional_sources_unchanged': 1029,
            'failure': 'Shape catalogue reads legacy local face descriptor; its referenced ec34 prepared-head scene.glb is missing before catalogue unit/GPU execute calls.',
            'failing_wrapper_source_sha256': SOURCE, 'physical_jobs': 68, 'normal_exit0': 67, 'registered_Krita_cancel_exit2': 1, 'failed_private_graphical_jobs': 0,
            'all_private_jobs_desktops_closed': True, 'recorded_inline_receipts_joined': len(inventory['inline_receipts']), 'canonical_PASS_lines_preserved': sum(line.startswith('PASS ') for line in log.splitlines()),
            'earlier_stage_evidence': 'Ordered canonical PASS lines and terminal inventory references preserved; no stale full report used or complete registry inferred.',
            'released_utc': release['released_utc'], 'root_no_termination_observations': 2, 'new_shape_catalogue_unit_or_GPU_result_claimed': False,
            'raw_face_descriptor_models_media_native_arrays_copied': False, 'fix_successor_or_native_fidelity_qualified': False}
