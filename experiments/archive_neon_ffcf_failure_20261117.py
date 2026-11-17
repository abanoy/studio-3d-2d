"""Compact public metadata for the closed failed ffcf full; no media/native data."""
from pathlib import Path
import gzip, hashlib, json

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
RUN = REVIEW / 'output/windows-neon-ffcf4c5-20261117T021833'
TARGET = ROOT / 'experiments/neon_failed_ffcf_actual_packet_20261117'
SCENE = REVIEW / 'output/scene-view/1794882871269454800'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
release = json.loads((RUN / 'graphics-lease-closed.json').read_bytes())
assert release['release_kind'] == 'closed_failed_partial_run' and release['released'] is True
assert release['physical_jobs'] == release['physical_receipt_files'] == 48
assert release['final_full_report_used'] is False
inventory_path = RUN / 'terminal-audit-attempt1/receipt-inventory.json'
assert sha(inventory_path.read_bytes()) == release['receipt_inventory_sha256'] == '2c334aab837768ee17b2c13be0ad6ac26fa203a9e8815cd991b24a2de3386704'
inventory = json.loads(inventory_path.read_bytes())
assert (inventory['normal_exit0'], inventory['registered_cancel_exit2'], inventory['failed_partial_nonzero']) == (46, 1, 1)
selections = [(RUN / name, 'actual/' + name) for name in (
    'state.json', 'source-before.json', 'source-after.json', 'launch.json', 'root-birth-observation.json',
    'root-birth-api-detail.json', 'canonical.log', 'graphics-lease-closed.json')]
selections += [(inventory_path, 'actual/receipt-inventory.json'),
               (RUN / 'terminal-audit-attempt1/host-observation.json', 'actual/host-observation.json')]
selections += [(SCENE / name, 'scene/' + name) for name in (
    'result.json', 'unit.json', 'source-sha256.json', 'scene_view_unit.log', 'scene_view_smoke.log',
    'scene_view_smoke-engine.log', 'scene_view_unit-command.json', 'scene_view_smoke-command.json')]
for i, row in enumerate(inventory['rows']):
    original = Path(row['preserved_raw_copy'])
    assert original.resolve().is_relative_to(RUN) and sha(original.read_bytes()) == row['source_sha256']
    selections.append((original, f'actual/receipts/{i:03d}-{original.name}'))
prepared = []
for original, name in selections:
    assert original.resolve().is_relative_to(REVIEW) and not original.is_symlink()
    raw = original.read_bytes()
    assert b'\0' not in raw
    raw.decode('utf-8-sig')
    zipped = len(raw) > 12000
    packed = gzip.compress(raw, compresslevel=9, mtime=0) if zipped else raw
    prepared.append((original, name + ('.gz' if zipped else ''), raw, packed, zipped))
TARGET.mkdir(exist_ok=False)
bindings = []
for original, name, raw, packed, zipped in prepared:
    path = TARGET / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(packed)
    bindings.append({'root': 'neon', 'path': original.relative_to(REVIEW).as_posix(), 'archive_path': name,
                     'bytes': len(raw), 'sha256': sha(raw), 'archive_bytes': len(packed),
                     'archive_sha256': sha(packed), 'gzip_exact_original': zipped})
facts = {'format': 'has_neon_ffcf_closed_failed_full_1', 'candidate': release['source_commit'],
         'full_suite_passed': False, 'main_merged': False, 'functional_sources_unchanged': 1029,
         'core_groups_passed': 36, 'integrated_neon_checks_passed': 12504,
         'failure': 'scene_view_smoke four off-frame displayed-color predicates',
         'scene_view_actual': json.loads((SCENE / 'result.json').read_bytes()),
         'source_style_observation': 'Neon CanvasView draws 62 percent dim bands outside camera frame',
         'analytical_fixture_successor': 'UNRUN_NOT_QUALIFIED_BY_THIS_ARCHIVE',
         'physical_jobs': 48, 'normal_exit0': 46, 'Krita_cancel_exit2': 1, 'scene_assertion_exit1': 1,
         'all_jobs_desktops_closed': True, 'released_utc': release['released_utc'],
         'stale_final_report_used': False, 'private_arrays_original_art_or_media_copied': False}
(TARGET / 'ACTUAL_RESULT.json').write_text(json.dumps(facts, indent=2) + '\n', encoding='utf-8')
(TARGET / 'EXACT_SOURCE_BINDINGS.json').write_text(json.dumps({'files': bindings}, indent=2) + '\n', encoding='utf-8')
(TARGET / 'README.md').write_text('Closed failed full ffcf run: source1029 unchanged, all36 core and12504 Neon checks pass, then scene-view102/4 stops the strict verifier. Original mask-sensitive failures and all48 physical receipts are retained. No full PASS, merge, analytical-fixture qualification or native model fidelity is claimed. Images/GLB/native arrays remain private.\n', encoding='utf-8')
rows = [{'path': path.relative_to(TARGET).as_posix(), 'bytes': path.stat().st_size, 'sha256': sha(path.read_bytes())}
        for path in sorted(TARGET.rglob('*')) if path.is_file()]
(TARGET / 'INDEX.json').write_text(json.dumps({'format': 'has_source_experiment_index_1', 'files': rows,
                                             'file_count': len(rows), 'bytes': sum(row['bytes'] for row in rows)}, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'payloads': len(rows), 'exact_originals': len(bindings), 'index_sha256': sha((TARGET / 'INDEX.json').read_bytes())}))
