"""Archive only public-cache cleanup journals; no cache contents/native artifacts."""
from pathlib import Path
import gzip
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'experiments/public_cache_cleanup_actual_20261117'
load = lambda p: json.loads(p.read_bytes())
sha = lambda raw: hashlib.sha256(raw).hexdigest()
output = ROOT / 'output'
first = output / 'remote-cache-cleanup-1ce-09fb-20261117-attempt1'
probe = output / 'remote-cache-readonly-git-probe-v2-20261117-attempt1'
second = output / 'remote-cache-cleanup-1ce-09fb-20261117-attempt2'
old = load(first / 'RESULT.json')
assert old['confirmed_deleted_and_absent_files'] == old['remove_calls_returned_successfully'] == 0 and old['uncertain_last_attempt_effect'] is False
actual_probe = load(probe / 'stdout.json')
assert actual_probe['passed'] is True and actual_probe['deletion_invoked'] is False and actual_probe['cleanup_entry_invoked'] is False
assert len(actual_probe['checks']) == 3 and all(row['actual_type'] == 'System.Byte[]' for row in actual_probe['checks'])
result = load(second / 'RESULT.json')
assert result['status'] == 'COMPLETE_EXACT71' and result['confirmed_deleted_and_absent_files'] == 71 and result['confirmed_deleted_logical_bytes'] == 14151060
assert result['uncertain_last_attempt_effect'] is False and result['recursive_delete'] is False
assert sha((second / 'RESULT.json').read_bytes()) == 'd3ea618c2438c66554d176a7b164cc84d59999d71625b18d7e8a4ecfbe18cd6d'
plan = load(ROOT / 'experiments/remote_download_cache_cleanup_preparation_20261117/PLAN.json')
for i, row in enumerate(plan['targets']):
    assert not (ROOT / row['path']).exists()
    a = load(second / f'predelete-{i:03d}.json')
    b = load(second / f'deleted-{i:03d}.json')
    assert a['path'] == b['path'] == row['path'] and a['sha256'] == b['sha256'] == row['sha256']
    assert b['status'] == 'DELETED_AND_ABSENCE_OBSERVED'
assert len(list(output.glob('e8cf-all-remote-batch-*.json'))) == 27
assert (ROOT / plan['retained_auxiliary_fallback']['path']).is_file()
prepared = []
for folder, prefix in ((first, 'attempt1'), (probe, 'readonly-probe'), (second, 'attempt2')):
    for path in sorted(folder.iterdir()):
        assert path.is_file() and not path.is_symlink() and path.suffix in ('.json', '.log')
        raw = path.read_bytes()
        assert b'\0' not in raw and len(raw) <= 2 * 1024 * 1024
        raw.decode('utf-8-sig', 'strict')
        zipped = len(raw) > 12000
        packed = gzip.compress(raw, compresslevel=9, mtime=0) if zipped else raw
        name = prefix + '/' + path.name + ('.gz' if zipped else '')
        prepared.append((path, name, raw, packed, zipped))
DEST.mkdir(exist_ok=False)
bindings = []
for source, name, raw, packed, zipped in prepared:
    target = DEST / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(packed)
    bindings.append({'source_path': source.relative_to(ROOT).as_posix(), 'archive_path': name, 'bytes': len(raw), 'sha256': sha(raw),
        'archive_bytes': len(packed), 'archive_sha256': sha(packed), 'gzip_exact_original': zipped})
facts = {'format': 'has_root_public_download_cache_cleanup_actual_1', 'first_attempt': 'PREFLIGHT_REFUSAL_ZERO_REMOVE_CALLS',
    'readonly_v2_Git_probe': 'PASS_3_EXACT_BYTE_ARRAY_CASES', 'second_attempt': 'COMPLETE_EXACT71',
    'confirmed_deleted_and_currently_absent_files': 71, 'confirmed_deleted_logical_bytes': 14151060,
    'disk_free_space_gain_measured': False, 'source_plan_sha256': result['plan_sha256'], 'executed_source_sha256': result['script_sha256'],
    'proof_records_rechecked_before_delete': 1402, 'new_e8_public_download_caches_retained': 27, 'auxiliary_fallback_retained': True,
    'private_native_original_review_tool_media_or_source_deletions_authorized': False, 'recursive_deletion': False,
    'scope_limit': 'Exact71 immediate public cache paths only. This is not an independent fresh inventory of every protected file on the PC.',
    'finished_utc': result['finished_utc'], 'models_or_arrays_in_archive': False}
(DEST / 'ACTUAL_RESULT.json').write_text(json.dumps(facts, indent=2) + '\n', encoding='utf-8', newline='\n')
(DEST / 'EXACT_SOURCE_BINDINGS.json').write_text(json.dumps({'files': bindings}, indent=2) + '\n', encoding='utf-8', newline='\n')
(DEST / 'README.md').write_text('Exact public-download cache cleanup after verified source/evidence publication. First attempt stopped before any remove call; actual readonlyGit probe passed after one return-value suppression. Second attempt removed and independently observed absence of exactly71old1ce/09fb public cache files totaling14,151,060logicalbytes, with predelete/deleted journals. This is not a measured free-space claim.27currente8 caches and external1ce fallback remain; no recursive/private/native/model/review/tool/source cleanup was authorized. Raw public journals, not cache payloads, are preserved.\n', encoding='utf-8', newline='\n')
rows = [{'path': p.relative_to(DEST).as_posix(), 'bytes': p.stat().st_size, 'sha256': sha(p.read_bytes())} for p in sorted(DEST.rglob('*')) if p.is_file()]
(DEST / 'INDEX.json').write_text(json.dumps({'format': 'has_source_experiment_index_1', 'files': rows}, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({'payloads': len(rows), 'exact_original_journals': len(bindings), 'index_sha256': sha((DEST / 'INDEX.json').read_bytes()), 'removed_files': 71, 'logical_bytes': 14151060}))
