"""CPU-only verification of the frozen interrupted metadata and closure refusal cases."""
from pathlib import Path
import gzip
import hashlib
import importlib.util
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / 'output/PRIVATE-neon-00bf-interrupted-bounded-20261117T154921'
HELPER = ROOT / 'experiments/neon_00bf_terminal_20261117'
sys.path.insert(0, str(HELPER))


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def main():
    source = ROOT / 'experiments/freeze_neon_00bf_interrupted_20261117.py'
    frozen = module('bounded_interrupted_freeze', source)
    helper = module('sealed_receipt_guards', HELPER / 'close_terminal.py')
    manifest = FREEZE / 'INTERRUPTED-INVENTORY.json'
    raw = manifest.read_bytes()
    report = json.loads(raw)
    assert hashlib.sha256(raw).hexdigest() == '6ea95acc9b13af6bec50781eb705a414e8640282c4b3aa09f67db28cc385fefa'
    assert report['script_sha256'] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert report['result'] == 'INTERRUPTED_NO_TERMINAL_RESULT' and report['suite_exit'] is None
    assert report['original_state_status'] == 'running' and report['full_suite_passed'] is False
    assert report['all_old_jobs_gracefully_closed'] == report['interrupted_or_unwritten_receipts'] == 'unknown'
    assert report['final_full_report_used'] is False and report['graphics_lease_released'] is False
    paths = set()
    for binding in report['metadata_bindings']:
        assert binding['path'] not in paths
        paths.add(binding['path'])
        relative = Path(binding['object'])
        assert not relative.is_absolute() and '..' not in relative.parts
        payload = gzip.decompress(helper.safe(FREEZE / relative).read_bytes())
        assert len(payload) == binding['bytes'] and hashlib.sha256(payload).hexdigest() == binding['sha256']
    assert len(paths) == report['metadata_files'] == 215
    assert 'verification.json' not in paths
    desktops = set()
    for row in report['receipts']:
        value = row['receipt']
        assert isinstance(value['desktop'], str) and value['desktop']
        assert type(value['child_pid']) is int and value['child_pid'] > 0
        assert value['desktop'] not in desktops
        desktops.add(value['desktop'])
        is_cancel = row['classification'] == 'registered_Krita_cancel_exit2'
        assert helper.classify_receipt(value, is_cancel, False) == row['classification']
    assert len(desktops) == 80 and report['unresolved_gaps'] == []
    valid = next(row['receipt'] for row in report['receipts'] if row['classification'] == 'normal_exit0')
    negative_cases = 0
    for key, replacement in (
        ('job_closed', False), ('desktop_closed', False), ('private_window_seen', False),
        ('child_desktop_confirmed', False), ('desktop_switch_requested', True),
        ('foreground_child_observed', True), ('exit', None), ('monitor_error', 'synthetic error'),
        ('desktop_enumeration_error', 'synthetic error'), ('cancelled', True),
    ):
        changed = dict(valid, **{key: replacement})
        assert frozen.classify(changed, False, helper) == 'unknown_incomplete_or_unvalidated_receipt'
        negative_cases += 1
    cancelled = next(row['receipt'] for row in report['receipts'] if row['classification'] == 'registered_Krita_cancel_exit2')
    assert frozen.classify(cancelled, False, helper) == 'unknown_incomplete_or_unvalidated_receipt'
    assert frozen.classify(dict(cancelled, exit=0), True, helper) == 'unknown_incomplete_or_unvalidated_receipt'
    assert frozen.classify(dict(valid, exit=1), False, helper) == 'failed_partial_run_nonzero_exit'
    negative_cases += 2
    print(json.dumps({'passed': True, 'verified_compressed_bindings': len(paths), 'verified_individual_receipts': len(desktops), 'negative_closure_or_cancellation_cases': negative_cases, 'terminal_or_exit_invention': False, 'engine_or_process_queries': False}))


if __name__ == '__main__':
    main()
