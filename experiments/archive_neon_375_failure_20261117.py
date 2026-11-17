"""Compact exact closed-run evidence; authored fixture source is public, no native art."""
from pathlib import Path
import gzip
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
RUN = REVIEW / 'output/windows-neon-375ec05-20261117T033037'
PHASE = REVIEW / 'output/canonical-spikes/1794886264394629400/source-choices/bindings-headless'
DEST = ROOT / 'experiments/neon_failed_375_actual_packet_20261117'
load = lambda p: json.loads(p.read_bytes())
sha = lambda raw: hashlib.sha256(raw).hexdigest()
release = load(RUN / 'graphics-lease-closed.json')
assert release['released'] is True and release['release_kind'] == 'closed_failed_partial_run'
assert release['source_commit'] == '375ec05e925159850ff3b0abf2e8f98f9d2ce129'
assert release['physical_jobs'] == release['physical_receipt_files'] == 51 and release['final_full_report_used'] is False
inventory_path = RUN / 'terminal-audit-attempt1/receipt-inventory.json'
assert sha(inventory_path.read_bytes()) == release['receipt_inventory_sha256'] == '0bd04488ed3f67cb8cdfdac4952736c3c5008e3defe15bbbd531412f67b7f1bd'
inventory = load(inventory_path)
assert (inventory['normal_exit0'], inventory['registered_cancel_exit2'], inventory['failed_partial_nonzero']) == (50, 1, 0)
headless = load(PHASE / 'bindings/run-process.json')
assert headless['exit'] == 1 and headless['headless'] is True and headless['timed_out'] is False and headless['graphics'] is False
phase_report = load(PHASE / 'verification.json')
assert phase_report['passed'] is False and phase_report['checks'] == 0 and phase_report['source_unchanged'] is True and phase_report['runtime_unchanged'] is True
selections = [(RUN / name, 'actual/' + name) for name in ('state.json', 'source-before.json', 'source-after.json', 'launch.json',
    'root-birth-observation.json', 'root-birth-api-detail.json', 'canonical.log', 'graphics-lease-closed.json')]
selections += [(inventory_path, 'actual/receipt-inventory.json'), (RUN / 'terminal-audit-attempt1/host-observation.json', 'actual/host-observation.json')]
selections += [(PHASE / name, 'headless/' + name) for name in ('verification.json', 'source-before.json', 'source-after.json')]
selections += [(PHASE / 'bindings' / name, 'headless/bindings/' + name) for name in ('parse-command.json', 'parse-process.json',
    'parse-console.log', 'parse-engine.log', 'run-command.json', 'run-process.json', 'run-console.log', 'run-engine.log', 'fixture/result.json')]
selections += [(PHASE.parent / 'bindings-headless.log', 'headless/wrapper.log')]
selections += [(REVIEW / name, 'source/' + name) for name in ('tests/source_bone_bindings_unit.gd', 'tests/source_native_helper_choice_unit.gd',
    'tests/verify_source_bone_bindings.py', 'tests/verify_source_choice_foundation.py')]
for i, row in enumerate(inventory['rows']):
    path = Path(row['preserved_raw_copy'])
    assert path.resolve().is_relative_to(RUN) and sha(path.read_bytes()) == row['source_sha256']
    selections.append((path, f'actual/receipts/{i:03d}-{path.name}'))
prepared = []
for original, name in selections:
    assert original.resolve().is_relative_to(REVIEW) and not original.is_symlink()
    raw = original.read_bytes()
    assert len(raw) <= 2 * 1024 * 1024 and b'\0' not in raw
    raw.decode('utf-8-sig', 'strict')
    compressed = len(raw) > 12000
    packed = gzip.compress(raw, compresslevel=9, mtime=0) if compressed else raw
    prepared.append((original, name + ('.gz' if compressed else ''), raw, packed, compressed))
DEST.mkdir(exist_ok=False)
bindings = []
for original, name, raw, packed, compressed in prepared:
    target = DEST / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(packed)
    bindings.append({'root': 'neon', 'path': original.relative_to(REVIEW).as_posix(), 'archive_path': name,
        'bytes': len(raw), 'sha256': sha(raw), 'archive_bytes': len(packed), 'archive_sha256': sha(packed), 'gzip_exact_original': compressed})
facts = {'format': 'has_neon_375_closed_failed_full_1', 'candidate': release['source_commit'], 'full_suite_passed': False,
    'main_merged': False, 'functional_sources_unchanged': 1029, 'core_groups_passed': 36, 'integrated_neon_checks_passed': 12504,
    'scene_smoke_checks_passed': 106, 'scene_unit_checks_passed': 12830, 'helper_cpu_checks_passed': 208, 'helper_graphical_checks_passed': 266,
    'source_choice_foundation_whole_pass': False, 'failure': 'Authored source bone fixture golden base64 decode fails with CR left after LF-only stripping',
    'failing_headless_process': headless, 'failing_fixture_actual': load(PHASE / 'bindings/fixture/result.json'),
    'expected_binding_checks': 79, 'subsequent_helper17': 'UNRUN_IN_THIS_FAILED_WRAPPER', 'fixture_successor': 'UNRUN_NOT_QUALIFIED_BY_ARCHIVE',
    'physical_jobs': 51, 'normal_exit0': 50, 'Krita_cancel_exit2': 1, 'failed_private_graphical_jobs': 0,
    'headless_failure_not_invented_as_private_job': True, 'all_private_jobs_desktops_closed': True, 'released_utc': release['released_utc'],
    'stale_final_report_used': False, 'private_art_models_media_or_native_arrays_copied': False}
(DEST / 'ACTUAL_RESULT.json').write_text(json.dumps(facts, indent=2) + '\n', encoding='utf-8', newline='\n')
(DEST / 'EXACT_SOURCE_BINDINGS.json').write_text(json.dumps({'files': bindings}, indent=2) + '\n', encoding='utf-8', newline='\n')
(DEST / 'README.md').write_text('Closed375 failed full attempt: Source1029 unchanged; core36,Neon12504,scene106/unit12830 and helper208/266 pass. Later authored bone fixture fails base64 decoding at40/40; raw ordered logs/source/commands and its owned headless exit1 are retained. All51private jobs(50exit0+Krita cancel2) closed; no private failure or extra headless desktop is invented. No full PASS, merge, fixture successor result or native fidelity follows. Public self-authored fixture source is retained; original models/art/media/native arrays remain private.\n', encoding='utf-8', newline='\n')
rows = [{'path': p.relative_to(DEST).as_posix(), 'bytes': p.stat().st_size, 'sha256': sha(p.read_bytes())} for p in sorted(DEST.rglob('*')) if p.is_file()]
(DEST / 'INDEX.json').write_text(json.dumps({'format': 'has_source_experiment_index_1', 'files': rows}, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({'payloads': len(rows), 'exact_originals': len(bindings), 'index_sha256': sha((DEST / 'INDEX.json').read_bytes())}))
