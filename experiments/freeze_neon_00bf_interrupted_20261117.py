"""Source-only bounded freeze of an interrupted run; no terminal or engine API calls."""
from pathlib import Path
from datetime import datetime, timezone
import gzip
import hashlib
import importlib.util
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
OUTPUT = REVIEW / 'output'
RUN = OUTPUT / 'windows-neon-00bf0f9-20261117T044200'
HELPER = ROOT / 'experiments/neon_00bf_terminal_20261117'
CUTOFF = '2026-11-17T15:46:49.6912177Z'
HELPER_SHA = 'c39e3751621bc4428166d64b7c6f6120bd7ef39251ccf9bbbf8a46dca390ce21'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def classify(receipt, cancel, helper):
    try:
        return helper.classify_receipt(receipt, cancel, False)
    except (ValueError, KeyError, TypeError):
        return 'unknown_incomplete_or_unvalidated_receipt'


def main():
    assert digest((HELPER / 'close_terminal.py').read_bytes()) == HELPER_SHA
    sys.path.insert(0, str(HELPER))
    spec = importlib.util.spec_from_file_location('sealed_interrupted_metadata_helper', HELPER / 'close_terminal.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    safe, load, ns = helper.safe, helper.load, helper.ns
    context = load(HELPER / 'CONTEXT.json')
    assert context['commit'] == '00bf0f916a549f5e858cb39dd91a149071fd5181'
    for name, expected in context['immutable_run_inputs'].items():
        assert helper.sha(safe(RUN / name)) == expected
    state = load(RUN / 'state.json')
    assert state['status'] == 'running' and state['source_commit'] == context['commit']
    assert not (safe(RUN) / 'source-after.json').exists()
    start, end = ns(state['started_utc']), ns(CUTOFF)
    assert start < end
    output = safe(OUTPUT)
    selected, gaps, queue, seen, inline = {}, [], [], set(), []

    def admit(path, origin, required=False):
        try:
            path = safe(path)
            assert path.is_relative_to(output) and path.suffix.lower() in ('.json', '.log')
            assert path.is_file()
            stamp = path.stat()
            assert stamp.st_size <= 64 * 1024 * 1024
            assert (origin == 'exact_original_run_metadata' or start <= stamp.st_mtime_ns) and stamp.st_mtime_ns <= end
            selected.setdefault(path, {'mtime_ns': stamp.st_mtime_ns, 'bytes': stamp.st_size, 'origins': set()})['origins'].add(origin)
            assert len(selected) <= 8192
            return path
        except (OSError, ValueError, AssertionError) as error:
            if required:
                gaps.append({'path': str(path), 'origin': origin, 'reason': str(error) or type(error).__name__})
            return None

    def known_folder(folder, origin):
        try:
            folder = safe(folder)
            assert folder.is_relative_to(output) and folder.is_dir()
            verify = admit(folder / 'verification.json', origin + '.folder_verification')
            if verify is not None:
                queue.append(verify)
            # Direct sibling logs only: never recurse through generated fixture directories.
            for path in folder.glob('*.log'):
                admit(path, origin + '.known_folder_log')
        except (OSError, ValueError, AssertionError) as error:
            gaps.append({'path': str(folder), 'origin': origin, 'reason': str(error) or type(error).__name__})

    def walk(value, origin):
        if type(value) is dict:
            if value.get('format') == 'studio_private_desktop_1':
                inline.append({'origin': origin, 'receipt': value})
            if value.get('format') == 'has_helper_preview_main_verification_1' and value.get('mode') == 'graphical':
                for row in value.get('results', []):
                    if 'private_receipt' in row:
                        admit(Path(value['actual_res_root']) / 'output/helper-preview-qa' / row['label'] / 'private-receipt.json', origin + '.derived_helper_' + row['label'], True)
            for key, item in value.items():
                if type(item) is str and re.match(r'^[A-Za-z]:[\\/]', item):
                    path = Path(item)
                    if path.suffix.lower() == '.json' and ('receipt' in key.lower() or 'private-desktop' in item.lower() or 'private-receipt' in item.lower()):
                        admit(path, origin + '.' + key, True)
                    elif path.suffix.lower() == '.log':
                        admit(path, origin + '.' + key, True)
                    if key == 'folder':
                        known_folder(path, origin + '.' + key)
                walk(item, origin + '.' + key)
        elif type(value) is list:
            for index, item in enumerate(value):
                loc = origin + '[' + str(index) + ']'
                if type(item) is str and re.match(r'^[A-Za-z]:[\\/]', item) and Path(item).suffix.lower() == '.json' and ('receipt' in origin.lower() or 'private-desktop' in item.lower() or 'private-receipt' in item.lower()):
                    admit(item, loc, True)
                walk(item, loc)

    desktop = safe(OUTPUT / 'private-desktop')
    for path in desktop.glob('*.json'):
        admit(path, 'fresh_root_actual_interval')
    for pattern in ('*-verification.json', '*-result.json'):
        for path in output.glob(pattern):
            accepted = admit(path, 'fresh_top_phase_actual_interval')
            if accepted is not None:
                queue.append(accepted)
    for name in ('state.json', 'source-before.json', 'launch.json', 'root-birth-observation.json', 'root-birth-api-detail.json', 'canonical.log', 'coordinator.stderr.log', 'coordinator.stdout.log'):
        assert admit(RUN / name, 'exact_original_run_metadata', True) is not None
    while queue:
        assert len(seen) < 1024 and len(inline) < 10000
        path = queue.pop(0)
        if path in seen:
            continue
        seen.add(path)
        walk(load(path), str(path))

    # Registered cancellation is established only from the actual fresh phase and pinned test source.
    cancel = None
    phase = OUTPUT / 'krita-import-verification.json'
    if phase in selected:
        cancelled = Path(load(phase)['cancelled_receipt'])
        source = safe(REVIEW / 'tests/verify_krita_import.py')
        before = load(RUN / 'source-before.json')
        assert helper.sha(source) == before['source_sha256']['tests/verify_krita_import.py']
        assert "assert r['exit']==2 and r['cancelled'] and r['child_desktop_confirmed']" in source.read_text(encoding='utf-8')
        cancelled = admit(cancelled, 'source_registered_Krita_cancel', True)
        if cancelled is not None:
            cancel = load(cancelled)

    assert selected and sum(row['bytes'] for row in selected.values()) <= 512 * 1024 * 1024
    target = ROOT / 'output' / ('PRIVATE-neon-00bf-interrupted-bounded-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S'))
    target.mkdir(exist_ok=False)
    (target / 'objects').mkdir()
    bindings, receipts, physical = [], [], {}
    for path, meta in sorted(selected.items(), key=lambda pair: str(pair[0])):
        path = safe(path)
        before_stamp = path.stat()
        assert (before_stamp.st_size, before_stamp.st_mtime_ns) == (meta['bytes'], meta['mtime_ns'])
        raw = path.read_bytes()
        after_stamp = path.stat()
        assert (after_stamp.st_size, after_stamp.st_mtime_ns) == (meta['bytes'], meta['mtime_ns'])
        pin = digest(raw)
        obj = target / 'objects' / (pin + '.gz')
        packed = gzip.compress(raw, compresslevel=6, mtime=0)
        if not obj.exists():
            with obj.open('xb') as stream:
                stream.write(packed)
        assert gzip.decompress(obj.read_bytes()) == raw
        bindings.append({'path': path.relative_to(output).as_posix(), **{key: meta[key] for key in ('bytes', 'mtime_ns')}, 'sha256': pin, 'object': 'objects/' + obj.name, 'origins': sorted(meta['origins'])})
        if path.suffix.lower() == '.json':
            value = json.loads(raw)
            if type(value) is dict and value.get('format') == 'studio_private_desktop_1':
                classification = classify(value, helper.typed_same(value, cancel), helper)
                row = {'source_path': str(path), 'sha256': pin, 'classification': classification, 'receipt': value}
                receipts.append(row)
                identity = value.get('desktop')
                if identity in physical and not helper.typed_same(physical[identity], value):
                    gaps.append({'origin': str(path), 'reason': 'conflicting receipt values for desktop'})
                else:
                    physical[identity] = value
    for item in inline:
        if not helper.typed_same(physical.get(item['receipt'].get('desktop')), item['receipt']):
            gaps.append({'origin': item['origin'], 'reason': 'inline receipt lacks exact physical match'})
    counts = {}
    for row in receipts:
        counts[row['classification']] = counts.get(row['classification'], 0) + 1
    report = {
        'format': 'has_interrupted_bounded_private_metadata_freeze_1',
        'source_commit': context['commit'], 'functional_sources_pinned': context['functional_sources'],
        'run': str(RUN), 'started_utc': state['started_utc'], 'actual_interval_cutoff_utc': CUTOFF,
        'cutoff_basis': 'root supplied current host scope observation; freeze itself performs no process query',
        'result': 'INTERRUPTED_NO_TERMINAL_RESULT', 'suite_exit': None, 'original_state_status': state['status'],
        'full_suite_passed': False, 'final_full_report_used': False,
        'all_old_jobs_gracefully_closed': 'unknown', 'interrupted_or_unwritten_receipts': 'unknown',
        'graphics_lease_released': False, 'native_lane_availability_decided_by_root_host_observation': True,
        'bounded_discovery_complete': True, 'private_snapshot_not_publication_authority': True,
        'metadata_bindings': bindings, 'metadata_files': len(bindings), 'metadata_bytes': sum(row['bytes'] for row in bindings),
        'phase_documents': len(seen), 'physical_receipt_files': len(receipts), 'unique_desktop_receipts': len(physical),
        'receipt_file_classifications': counts, 'receipts': receipts, 'inline_receipt_bindings': len(inline), 'unresolved_gaps': gaps,
        'no_CIM_engines_Git_network_or_REVIEW_writes': True,
        'script_sha256': digest(Path(__file__).read_bytes()), 'sealed_helper_sha256': HELPER_SHA,
    }
    manifest = target / 'INTERRUPTED-INVENTORY.json'
    with manifest.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')
    summary = {key: report[key] for key in ('result', 'metadata_files', 'metadata_bytes', 'phase_documents', 'physical_receipt_files', 'unique_desktop_receipts', 'receipt_file_classifications', 'inline_receipt_bindings')}
    summary.update({'private_snapshot': str(target), 'inventory_sha256': digest(manifest.read_bytes()), 'unresolved_gaps': len(gaps), 'metadata_frozen_safe_for_root_new_run': True})
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
