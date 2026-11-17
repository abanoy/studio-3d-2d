"""Preserve only public text/scalar/source-hash/physical receipts of the failed run."""
from pathlib import Path
import gzip, hashlib, json

ROOT = Path(__file__).resolve().parents[1]
NEON = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
RUN = NEON / 'output/windows-neon-f387d0e-20261117T012410'
TARGET = ROOT / 'experiments/neon_failed_f387_actual_packet_20261117'

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

release = json.loads((RUN / 'graphics-lease-closed.json').read_bytes())
assert release['release_kind'] == 'closed_failed_partial_run' and release['released'] is True
assert release['full_suite_passed'] is False and release['final_full_report_used'] is False
assert release['physical_jobs'] == release['physical_receipt_files'] == 36
assert release['receipt_inventory_sha256'] == 'c00553b7f303f7047e4b46beeceb439312e9139896532fe38583e65fd8c6cb03'
inventory_path = RUN / 'terminal-audit-attempt1/receipt-inventory.json'
assert sha(inventory_path.read_bytes()) == release['receipt_inventory_sha256']
inventory = json.loads(inventory_path.read_bytes())
assert inventory['normal_exit0'] == 35 and inventory['registered_cancel_exit2'] == 1
assert inventory['failed_partial_nonzero'] == 0
selections = [(RUN / name, 'actual/' + name) for name in (
    'state.json', 'source-before.json', 'source-after.json', 'launch.json',
    'root-birth-observation.json', 'canonical.log', 'graphics-lease-closed.json')]
selections += [(inventory_path, 'actual/receipt-inventory.json'),
               (RUN / 'terminal-audit-attempt1/host-observation.json', 'actual/host-observation.json'),
               (NEON / 'output/workspace-controls/1794879473739162800/result.json', 'actual/workspace-result.json'),
               (NEON / 'output/workspace-controls/1794879473739162800/app.log', 'actual/workspace-app.log')]
for i, row in enumerate(inventory['rows']):
    original = Path(row['preserved_raw_copy'])
    assert original.resolve().is_relative_to(RUN) and sha(original.read_bytes()) == row['source_sha256']
    selections.append((original, f'actual/receipts/{i:03d}-{original.name}'))
prepared = []
for original, name in selections:
    assert original.resolve().is_relative_to(NEON) and not original.is_symlink()
    raw = original.read_bytes()
    assert b'\0' not in raw
    raw.decode('utf-8-sig')
    zipped = len(raw) > 12000
    body = gzip.compress(raw, compresslevel=9, mtime=0) if zipped else raw
    prepared.append((original, name + ('.gz' if zipped else ''), raw, body, zipped))
assert not TARGET.exists()
TARGET.mkdir(exist_ok=False)
bindings = []
for original, name, raw, body, zipped in prepared:
    path = TARGET / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    bindings.append({'root': 'neon', 'path': original.relative_to(NEON).as_posix(), 'archive_path': name,
                     'bytes': len(raw), 'sha256': sha(raw), 'archive_bytes': len(body),
                     'archive_sha256': sha(body), 'gzip_exact_original': zipped})
facts = {'format': 'has_neon_f387_failed_actual_1', 'full_suite_passed': False,
         'candidate': release['source_commit'], 'main_redesign_merged': False,
         'functional_sources_unchanged': 1028, 'failure': 'workspace_controls wrapper refuses teardown font errors',
         'workspace_predicates': {'checks': 48, 'failures': 0},
         'font_error_after_app_free': 'Parameter fd is null; WorldSelection.set_rail -> WorkspaceLayout.refresh_world_mode',
         'core_groups_passed_before_workspace': 36, 'physical_jobs': 36,
         'normal_exit0': 35, 'registered_Krita_cancel_exit2': 1,
         'all_jobs_desktops_closed': True, 'release_utc': release['released_utc'],
         'stale_final_report_used': False, 'private_art_arrays_or_media_copied': False,
         'original_failure_retained': True, 'repair_qualified_by_this_archive': False}
(TARGET / 'ACTUAL_RESULT.json').write_text(json.dumps(facts, indent=2) + '\n', encoding='utf-8')
(TARGET / 'EXACT_SOURCE_BINDINGS.json').write_text(json.dumps({'files': bindings}, indent=2) + '\n', encoding='utf-8')
(TARGET / 'README.md').write_text('Closed failed f387 Windows run. All36 core groups and48 workspace assertions pass, but font errors during explicit app teardown make the strict wrapper/full suite fail. No assertion or error filter is relaxed. No full PASS, merge, native-normal repair or owner result is claimed. Exact public originals and all36 physical receipts are retained; images/native arrays stay private.\n', encoding='utf-8')
rows = [{'path': p.relative_to(TARGET).as_posix(), 'bytes': p.stat().st_size, 'sha256': sha(p.read_bytes())}
        for p in sorted(TARGET.rglob('*')) if p.is_file()]
(TARGET / 'INDEX.json').write_text(json.dumps({'format': 'has_source_experiment_index_1', 'files': rows,
                                             'file_count': len(rows), 'bytes': sum(row['bytes'] for row in rows)}, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'packet': str(TARGET), 'index_sha256': sha((TARGET / 'INDEX.json').read_bytes()),
                  'payloads': len(rows), 'exact_originals': len(bindings), 'full_pass': False}))
