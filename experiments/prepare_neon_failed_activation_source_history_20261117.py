"""Preserve the failed activation's exact source without duplicate catalogues.

Reads only the three explicit source packets below. Each failed payload either
has a byte-identical recoverable source reference or a small public text copy.
No runtime/native result, private file, application, Git or process is opened.
"""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / 'experiments/neon_owner_executor_active_973039e_20261117'
BASE = ROOT / 'experiments/neon_owner_executor_shell_eol_20261117'
FINAL = ROOT / 'experiments/neon_owner_executor_active_973039e_index_20261117'
TARGET = ROOT / 'experiments/neon_owner_failed_activation_source_history_20261117'
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def safe(folder, name):
    assert type(name) is str and name and '/' not in name and '\\' not in name and ':' not in name
    path = folder / name
    assert path.resolve().parent == folder.resolve() and path.is_file() and not path.is_symlink()
    assert not getattr(path.lstat(), 'st_file_attributes', 0) & 0x400
    return path


def packet(folder, pin):
    raw = safe(folder, 'INDEX.json').read_bytes()
    assert sha(raw) == pin
    doc = json.loads(raw)
    rows = doc['files']
    assert type(rows) is list and len(rows) == len({row['path'] for row in rows})
    assert {item.name for item in folder.iterdir()} == {'INDEX.json', *(row['path'] for row in rows)}
    for row in rows:
        body = safe(folder, row['path']).read_bytes()
        assert (len(body), sha(body)) == (row['bytes'], row['sha256'])
    return raw, rows


old_index, old_rows = packet(OLD, 'a906a2dd491d73a41b5e473bc6f3c121c510b1a9bd3fabcec3cbe29c6b66cdc3')
base_index, base_rows = packet(BASE, '3ea125a3c043688c2bf5f2dbe5ce4c41501ea41b7f831575eefbe5bdfffbdcf4')
final_index, final_rows = packet(FINAL, '61978b62ac92f6471d5b1dcbcc8cb485caccb3d2b7adb5d7edaa643e2252a066')
references = [(BASE, {row['path']: row for row in base_rows}), (FINAL, {row['path']: row for row in final_rows})]
copies = {'FAILED_ACTIVE_INDEX.json': old_index}
mapping = []
for row in old_rows:
    body = safe(OLD, row['path']).read_bytes()
    source = None
    for folder, entries in references:
        other = entries.get(row['path'])
        if other is not None and (other['bytes'], other['sha256']) == (row['bytes'], row['sha256']):
            assert safe(folder, row['path']).read_bytes() == body
            source = (folder / row['path']).relative_to(ROOT).as_posix()
            break
    if source is None:
        assert len(body) <= 64 * 1024 and b'\0' not in body
        body.decode('utf-8-sig')
        assert Path(row['path']).suffix in ('.json', '.py', '.md')
        name = 'FAILED_' + row['path']
        copies[name] = body
        source = (TARGET / name).relative_to(ROOT).as_posix()
    mapping.append({**row, 'recoverable_source': source, 'source_bytes_exact': True})
assert len(mapping) == 23
assert not TARGET.exists()
TARGET.mkdir()
for name, body in copies.items():
    (TARGET / name).write_bytes(body)
summary = {
    'format': 'has_failed_activation_exact_source_reconstruction_1',
    'failed_active_INDEX_sha256': sha(old_index),
    'committed_predecessor_INDEX_sha256': sha(base_index),
    'final_compatible_active_INDEX_sha256': sha(final_index),
    'payloads': mapping,
    'all_23_failed_payloads_recoverable_exact': True,
    'failed_activation_execution_outcome': 'FACTORY_KEYERROR_BEFORE_COPY_NO_NATIVE_LAUNCH',
    'large_identical_catalogue_recipe_and_delta_copied': False,
    'raw_runtime_reports_or_native_data_included': False,
}
(TARGET / 'SOURCE_MAP.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8', newline='\n')
rows = [{'path': path.name, 'bytes': path.stat().st_size, 'sha256': sha(path.read_bytes())}
        for path in sorted(TARGET.iterdir())]
(TARGET / 'INDEX.json').write_text(json.dumps({
    'format': 'has_failed_activation_source_history_packet_1', 'files': rows,
    'source_only_no_activation': True}, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({'files': len(rows), 'copied_unique_source_bytes': sum(row['bytes'] for row in rows),
                  'INDEX_sha256': sha((TARGET / 'INDEX.json').read_bytes())}))
