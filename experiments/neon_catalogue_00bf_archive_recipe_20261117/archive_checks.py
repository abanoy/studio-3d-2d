"""Pure exact joins for closed catalogue/comparison/height observations."""
from pathlib import PureWindowsPath
import hashlib
import json

ROOT_RUN = 'output/neon-catalogue-00bf0f9-20261117-attempt1/'
REVISION = '00bf0f916a549f5e858cb39dd91a149071fd5181'
LABELS = ['MMD', 'GMod', 'SFM', 'VRM1.0', 'VRM0.x', 'Supplied Mima']
EXPECTED = [('catalogue', 130, 37.6931239, 'output/shape-catalog/', 2),
            ('comparison', 94, 43.6109725, 'output/shape-comparison-tests/', 3),
            ('height', 105, 48.1988992, 'output/character-height/', 3)]


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
        for key, item in rows: require(key not in value, 'Duplicate JSON key'); value[key] = item
        return value
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def relative(value, review): return PureWindowsPath(value).relative_to(PureWindowsPath(review)).as_posix()


def marker(raw, prefix):
    lines = [line[len(prefix):] for line in raw.splitlines() if line.startswith(prefix)]
    require(len(lines) == 1, 'One original scalar log marker required'); return load(lines[0])


def check(raw, review):
    def body(name): return raw['REVIEW:' + name]
    def obj(name): return load(body(name))
    root = obj(ROOT_RUN + 'verification.json'); before = obj(ROOT_RUN + 'source-before.json')
    require(root['format'] == 'has_root_workspace_followup_1' and root['passed'] is True and root['full_suite_pass_claimed'] is False
            and root['all_functional_source_unchanged'] is True and root['host_scopes_closed'] is True and root['functional_source_files'] == 1029, 'Root scoped result')
    require(len(before) == 1029 and same(before, obj(ROOT_RUN + 'source-after.json')), 'Exact1029 source preservation')
    for name, digest in [('tests/verify_shape_catalog.py', '54431c2c486bce9828ec47ebe046da9f413b3854e8c0290829c24183fe72e057'),
                         ('tests/verify_character_height.py', 'cccfb7d472b5d552cbd3cfc07dc9058c1789b9c1947f6a1a548c924dd38a3f79')]:
        require(before[name] == digest, 'Exact fixture selector source')
    require([r['label'] for r in root['rows']] == [r[0] for r in EXPECTED], 'Three original ordered modes')
    for label in ('before', 'catalogue-after', 'comparison-after', 'height-after', 'after'):
        scope = obj(ROOT_RUN + label + '-closure.json')
        require(scope['format'] == 'has_root_workspace_scope_observation_1' and type(scope['owned_count']) is int and scope['owned_count'] == 0 and scope['owned_matches'] == []
                and scope['termination_issued'] is False and scope['matcher_positive_cases'] == 4 and scope['matcher_negative_cases'] == 3, 'Recorded main/review zero scope')
    reports = {}; folders = {}; physical = []; receipt_paths = []
    for row, (label, count, seconds, prefix, jobs) in zip(root['rows'], EXPECTED, strict=True):
        require(type(row['exit']) is int and row['exit'] == 0 and row['retained_Popen_reaped'] is True and row['timed_out'] is False and row['seconds'] == seconds, 'Exact root process gates')
        require(same({k: v for k, v in row.items() if k != 'report'}, obj(ROOT_RUN + label + '-process.json')), 'Direct root process metadata')
        start = obj(ROOT_RUN + label + '-start.json'); require(start['pid'] == row['pid'] and start['retained_Popen'] is True, 'Retained root launch identity')
        report = obj(ROOT_RUN + label + '-report.json'); require(same(report, row['report']), 'Root saved report/inline copy')
        require(type(report['checks']) is int and report['checks'] == count and type(report['failures']) is int and report['failures'] == 0, 'Original case checks/failures')
        child = relative(report['folder'], review) + '/'; require(child.startswith(prefix), 'Saved child output domain')
        reports[label] = report; folders[label] = child
        raw_result = obj(child + 'result.json')
        require(all(key in report and same(value, report[key]) for key, value in raw_result.items()), 'Original raw result subset')
        require(len(report['private_receipts']) == jobs, 'Exact physical receipt membership')
        for path in report['private_receipts']:
            relative_path = relative(path, review); require(relative_path.startswith('output/private-desktop/'), 'Private receipt path boundary')
            receipt = obj(relative_path)
            for key, value in {'format': 'studio_private_desktop_1', 'exit': 0, 'private_window_seen': True, 'child_desktop_confirmed': True,
                               'foreground_child_observed': False, 'desktop_switch_requested': False, 'job_closed': True, 'desktop_closed': True}.items():
                require(same(receipt.get(key), value), 'Strict physical receipt placement/closure')
            receipt_paths.append(relative_path); physical.append((receipt['desktop'], receipt['child_pid']))
    require(len(receipt_paths) == len(set(receipt_paths)) == len(set(physical)) == 8, 'Eight distinct physical jobs, no headless fabrication')
    catalogue = reports['catalogue']; C = folders['catalogue']
    require(same(catalogue['plans'], ['Authored fixture'] + LABELS) and type(catalogue['unit_checks']) is int and catalogue['unit_checks'] == 34, 'All seven catalogue inputs and unit34')
    unit = marker(body(C + 'shape_catalog_unit.log'), b'SHAPE_CATALOG_UNIT ')
    require(same(unit, {'checks': 34, 'failures': 0}), 'Actual headless unit marker')
    require(same(catalogue['reader'], obj(C + 'reader-result.json')) and same(catalogue['reader'], {'checks': 5, 'failures': 0}), 'Cold catalogue reader5')
    comparison = reports['comparison']; C = folders['comparison']
    require([m['label'] for m in comparison['models']] == ['Authored fixture'] + LABELS and comparison['native_models_tested'] == 6, 'All six comparison native cases')
    require(same(comparison['teardown'], obj(C + 'teardown-result.json')) and same(comparison['teardown'], {'actual_readback_pending': True, 'checks': 2, 'failures': 0, 'released_after_app_free': True}), 'Actual pending teardown2')
    require(same(comparison['draft_recovery'], obj(C + 'draft-reader.json')) and same(comparison['draft_recovery'], {'checks': 4, 'failures': 0}), 'Supplied Mima draft recovery4 retained')
    height = reports['height']; C = folders['height']
    require(height['native_models'] == 6 and [m['label'] for m in height['models']] == ['Authored figure'] + LABELS + ['Short legs', 'Long legs', 'Head with full rig'], 'Six native height inputs and three diagnostic cases')
    require(same(height['reader'], {'checks': 4, 'failures': 0}) and same(height['native_import'], {'checks': 9, 'failures': 0}), 'Cold height4 and actual raw VRM9, no omission')
    require(same(height['reader'], marker(body(C + 'reader.log'), b'CHARACTER_HEIGHT_READER '))
            and same(height['native_import'], marker(body(C + 'native.log'), b'HEIGHT_IMPORT_NATIVE ')), 'Original height scalar log markers')
    for command_name, receipt_path in zip(('command.json', 'reader-command.json', 'native-command.json'), height['private_receipts'], strict=True):
        saved = obj(C + command_name); require(type(saved['exit']) is int and saved['exit'] == 0, 'Original saved height process exit')
        args = saved['args']; require(args.count('--receipt') == 1 and PureWindowsPath(args[args.index('--receipt') + 1]) == PureWindowsPath(receipt_path), 'Saved height command→physical receipt join')
    prepared = load(raw['MAIN:experiments/neon_shape_catalog_fixture_actual_inputs_20261117/PREPARATION.json'])
    require(prepared['descriptor_sha256'] == '05bd6d4ba63e481cf3488f9bf0082d662812d3bf8bb861796860f42fcb3e2310'
            and prepared['scene']['bytes'] == 7830992 and prepared['scene']['sha256'] == 'e9b21ab5f1171b21d0a7d3e3f83e5341f6b297516d09582e49c0283dfe10d8da'
            and prepared['prior_plan_exact_current_bundle_path'] is True and prepared['historical_b577_glb_substituted_or_recovered'] is False
            and prepared['raw_descriptor_native_arrays_model_or_media_included'] is False, 'Retained current Mima input scalar provenance')
    for key, data in raw.items():
        if key.startswith('REVIEW:') and key[7:] in before: require(hashlib.sha256(data).hexdigest() == before[key[7:]], 'Selected source body matches tested source map')
    return {'format': 'has_catalogue_00bf_compact_actual_summary_1', 'qualification': 'CLOSED_FOCUSED_NATIVE_BEHAVIOR_SCALAR_EVIDENCE_NOT_COMPLETE_FULL_OR_FIDELITY',
            'revision': REVISION, 'catalogue': {'checks': 130, 'unit': 34, 'reader': 5, 'input_labels': ['Authored fixture'] + LABELS},
            'comparison': {'checks': 94, 'native_models': 6, 'teardown': 2, 'draft_recovery': 4},
            'height': {'checks': 105, 'native_models': 6, 'reader': 4, 'raw_VRM_import': 9},
            'root_seconds': {r[0]: r[2] for r in EXPECTED}, 'functional_sources_preserved': 1029, 'physical_private_jobs': 8,
            'physical_receipt_paths': receipt_paths, 'saved_direct_physical_command_joins': {'catalogue': 0, 'comparison': 0, 'height': 3},
            'command_evidence_limit': 'Catalogue/comparison wrappers did not persist private argv; recorded path→physical receipt joins are retained, no command files invented. Unit34 is headless with log marker and no private receipt.',
            'public_measurement_scope': 'Comparison focus-bound strings and small height assessment axis/coverage vectors are derived result measurements; original positions/poses/weights/parameters are excluded.',
            'full_suite_pass_claimed': False, 'native_roundtrip_fidelity_or_main_merge_claimed': False,
            'model_media_original_native_arrays_or_generated_fixture_payloads_included': False, 'upcoming_full_outputs_read': False}
