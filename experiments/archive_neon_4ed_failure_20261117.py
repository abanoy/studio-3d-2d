"""Exact compact public evidence of the closed4ed helper source-manifest refusal."""
from pathlib import Path
import gzip
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
RUN = REVIEW / 'output/windows-neon-4ed3a63-20261117T030209'
TARGET = ROOT / 'experiments/neon_failed_4ed_actual_packet_20261117'
HELPER = REVIEW / 'output/helper-preview/cpu-1794885569749222100-140852bb'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
load = lambda path: json.loads(path.read_bytes())
release = load(RUN / 'graphics-lease-closed.json')
assert release['release_kind'] == 'closed_failed_partial_run' and release['released'] is True
assert release['source_commit'] == '4ed3a63b716f696daa1699a76443d6f1abb9b096'
assert release['physical_jobs'] == release['physical_receipt_files'] == 49
assert release['final_full_report_used'] is False
inventory_path = RUN / 'terminal-audit-attempt1/receipt-inventory.json'
assert sha(inventory_path.read_bytes()) == release['receipt_inventory_sha256'] == '6b8c57667a3c553152396711a6b755faf7f923714ad6724eddba06bf123ad87d'
inventory = load(inventory_path)
assert (inventory['normal_exit0'], inventory['registered_cancel_exit2'], inventory['failed_partial_nonzero']) == (48, 1, 0)
helper = load(HELPER / 'verification.json')
assert helper['checks'] == 0 and helper['graphical_process_attempted'] is False
assert helper['error'] == 'RuntimeError: Unreviewed helper main bytes: src/app.gd'
scene_report = REVIEW / 'output/scene-view-verification.json'
scene = load(scene_report)
assert scene['scene_view_smoke']['checks'] == 106 and scene['scene_view_smoke']['failures'] == 0
assert scene['scene_view_unit']['checks'] == 12830 and scene['scene_view_unit']['failures'] == 0
scene_folder = Path(scene['folder'])
assert scene_folder.resolve().is_relative_to(REVIEW / 'output')
selections = [(RUN / name, 'actual/' + name) for name in (
    'state.json', 'source-before.json', 'source-after.json', 'launch.json', 'root-birth-observation.json',
    'root-birth-api-detail.json', 'canonical.log', 'graphics-lease-closed.json')]
selections += [(inventory_path, 'actual/receipt-inventory.json'),
    (RUN / 'terminal-audit-attempt1/host-observation.json', 'actual/host-observation.json'),
    (HELPER / 'verification.json', 'helper/verification.json'),
    (HELPER / 'main-source-after.json', 'helper/main-source-after.json'),
    (REVIEW / 'tests/helper_preview_port_files.json', 'helper/helper_preview_port_files.original.json'),
    (scene_report, 'scene/verification.json')]
selections += [(scene_folder / name, 'scene/' + name) for name in (
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
        'bytes': len(raw), 'sha256': sha(raw), 'archive_bytes': len(packed), 'archive_sha256': sha(packed), 'gzip_exact_original': zipped})
facts = {'format': 'has_neon_4ed_closed_failed_full_1', 'candidate': release['source_commit'],
    'full_suite_passed': False, 'main_merged': False, 'functional_sources_unchanged': 1029,
    'core_groups_passed': 36, 'integrated_neon_checks_passed': 12504, 'scene_view_smoke_checks_passed': 106,
    'scene_view_unit_checks_passed': 12830, 'failure': helper['error'], 'helper_checks_run': 0,
    'helper_graphical_process_attempted': False, 'helper_source_manifest_successor': 'UNRUN_NOT_QUALIFIED_BY_THIS_ARCHIVE',
    'physical_jobs': 49, 'normal_exit0': 48, 'Krita_cancel_exit2': 1, 'failed_physical_jobs': 0,
    'all_jobs_desktops_closed': True, 'released_utc': release['released_utc'],
    'stale_final_report_used': False, 'private_arrays_original_art_or_media_copied': False}
(TARGET / 'ACTUAL_RESULT.json').write_text(json.dumps(facts, indent=2) + '\n', encoding='utf-8', newline='\n')
(TARGET / 'EXACT_SOURCE_BINDINGS.json').write_text(json.dumps({'files': bindings}, indent=2) + '\n', encoding='utf-8', newline='\n')
(TARGET / 'README.md').write_text('Closed failed4ed complete Windows attempt: source1029 unchanged; all36core,12504Neon, scene106 and12830 mapping checks pass. Later helper-preview CPU entry refuses unreviewed app.gd against its stale manifest before running checks or launching a process. All49physical jobs are closed. No full PASS, merge, helper successor result or native fidelity is claimed. Originals/media/native arrays remain private.\n', encoding='utf-8', newline='\n')
rows = [{'path': path.relative_to(TARGET).as_posix(), 'bytes': path.stat().st_size, 'sha256': sha(path.read_bytes())}
    for path in sorted(TARGET.rglob('*')) if path.is_file()]
(TARGET / 'INDEX.json').write_text(json.dumps({'format': 'has_source_experiment_index_1', 'files': rows,
    'file_count': len(rows), 'bytes': sum(row['bytes'] for row in rows)}, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({'payloads': len(rows), 'exact_originals': len(bindings), 'index_sha256': sha((TARGET / 'INDEX.json').read_bytes())}))
