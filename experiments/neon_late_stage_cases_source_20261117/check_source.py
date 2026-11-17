"""CPU/source check only: never import a verifier/host or invoke subprocesses."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import late_cases as spec


def must_refuse(call):
    try:
        call()
    except (AssertionError, KeyError):
        return
    raise AssertionError('negative source/report case was accepted')


def main():
    root = Path(__file__).resolve().parents[2]
    review = root.parent / 'has-neon-review-20261116-c2d52ff'
    raw_verify = (review / 'tests/verify.py').read_bytes()
    raw_host = (root / 'experiments/run_neon_scene_followup_20261117.py').read_bytes()
    rows = spec.check_source(raw_verify, raw_host)
    pins = json.loads(Path(__file__).with_name('STATIC_SOURCE_PINS.json').read_text(encoding='utf-8'))
    assert pins['canonical_verify_raw_sha256'] == spec.VERIFY_RAW_SHA256
    assert pins['root_host_sha256'] == spec.ROOT_HOST_SHA256
    assert set(pins['wrappers']) == {row[1] for row in rows}
    for name, descriptor in pins['wrappers'].items():
        raw = (review / 'tests' / name).read_bytes()
        assert len(raw) == descriptor['bytes'] and hashlib.sha256(raw).hexdigest() == descriptor['sha256']

    must_refuse(lambda: spec.check_source(raw_verify + b'\n', raw_host))
    must_refuse(lambda: spec.check_source(raw_verify, raw_host + b'\n'))
    changes = [rows[:-1], (rows[1], rows[0], *rows[2:])]
    for index, field, replacement in ((5, 2, ()), (15, 3, 'wrong.json'), (17, 4, 999)):
        edited = list(rows)
        changed = list(edited[index]); changed[field] = replacement
        edited[index] = tuple(changed)
        changes.append(tuple(edited))
    for edited in changes:
        must_refuse(lambda edited=edited: spec.check_source(raw_verify, raw_host, edited))

    # Synthetic dictionaries test report criteria only; they are no actual run.
    good = {'failures': 0, 'writer': {'failures': 0}, 'reader': {'failures': 0},
            'readers': {'a': {'failures': 0}, 'b': {'failures': 0}}, 'fresh_readers': [0, 1, 2, 3]}
    for label, *_ in rows:
        spec.assert_canonical_report(label, good)
    bad = []
    for label, path in (
        ('contact_animation', ('failures',)),
        ('contact_persistence', ('writer', 'failures')),
        ('contact_persistence', ('readers', 'b', 'failures')),
        ('contact_viewport', ('reader', 'failures')),
        ('component_contact_clipboard', ('failures',)),
        ('motion_assist', ('failures',)),
        ('motion_editor', ('reader', 'failures')),
    ):
        report = deepcopy(good); target = report
        for key in path[:-1]: target = target[key]
        target[path[-1]] = 1
        bad.append((label, report))
    report = deepcopy(good); report['fresh_readers'].pop()
    bad.append(('project_duration', report))
    for label, report in bad:
        must_refuse(lambda label=label, report=report: spec.assert_canonical_report(label, report))
    print(json.dumps({'format': 'has_neon_late_stage_cpu_source_check_1',
        'passed': True, 'source_only': True, 'canonical_cases': len(rows),
        'pinned_unchanged_wrappers': len(pins['wrappers']),
        'source_and_case_negative_checks': 2 + len(changes),
        'synthetic_report_positive_labels': len(rows), 'synthetic_report_negative_checks': len(bad),
        'native_execution': False, 'actual_targeted_pass_claimed': False, 'full_suite_pass_claimed': False}, indent=2))


if __name__ == '__main__':
    main()
