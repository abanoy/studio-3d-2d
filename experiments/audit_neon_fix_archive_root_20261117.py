"""Independent root verification of compact completed workspace evidence."""
from pathlib import Path
import gzip, hashlib, json

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
PACKET = ROOT / 'experiments/neon_workspace_fix_sequence_actual_packet_20261117'

def sha(body):
    return hashlib.sha256(body).hexdigest()

index_raw = (PACKET / 'INDEX.json').read_bytes()
assert sha(index_raw) == 'e8a7f25ed780eaac2b6d0611fcbc7c7d388945fd82e7f23df6979cf0147060c9'
index = json.loads(index_raw)
rows = index['files']
assert len(rows) == 305 and index['exact_original_bindings'] == 417
names = {row['path'] for row in rows}
assert len(names) == 305
assert {p.relative_to(PACKET).as_posix() for p in PACKET.rglob('*') if p.is_file()} == names | {'INDEX.json'}
for row in rows:
    path = PACKET / row['path']
    assert path.resolve().is_relative_to(PACKET) and not path.is_symlink()
    assert path.suffix in {'.json', '.log', '.py', '.gd', '.md', '.patch', '.gz'}
    raw = path.read_bytes()
    assert len(raw) == row['bytes'] and sha(raw) == row['sha256']
    text = gzip.decompress(raw) if path.suffix == '.gz' else raw
    assert b'\0' not in text
    text.decode('utf-8')
roots = {key: Path(value).resolve() for key, value in json.loads((PACKET / 'recipe/INPUTS.json').read_bytes())['roots'].items()}
assert set(roots.values()) == {ROOT, REVIEW}
bindings = json.loads((PACKET / 'EXACT_SOURCE_BINDINGS.json').read_bytes())['files']
assert len(bindings) == 417
for row in bindings:
    original = roots[row['root']] / row['path']
    assert original.resolve().is_relative_to(roots[row['root']]) and not original.is_symlink()
    assert Path(row['source_absolute_path']) == original
    body = (PACKET / row['archive_path']).read_bytes()
    assert len(body) == row['archive_bytes'] and sha(body) == row['archive_sha256']
    raw = gzip.decompress(body) if row['gzip_exact_original'] else body
    assert len(raw) == row['bytes'] and sha(raw) == row['sha256'] and raw == original.read_bytes()
facts = json.loads((PACKET / 'ACTUAL_SEQUENCE.json').read_bytes())
assert facts['unique_physical_jobs'] == 23 and facts['physical_receipt_files'] == 25
assert facts['normal_exit0_jobs'] == 21 and facts['assertion_exit1_jobs'] == 2
assert facts['transaction_standard12504'] == 'PASS_ALL5_CASES'
assert facts['full_Windows_PASS_or_merge_claimed'] is False
assert facts['after_free_attribution'] == 'RETRACTED'
assert facts['native_art_arrays_media_or_projects_included'] is False
out = ROOT / 'experiments/neon_fix_sequence_root_audit_20261117'
out.mkdir(exist_ok=False)
record = {'format': 'has_root_neon_completed_sequence_archive_audit_1', 'passed': True,
          'index_sha256': sha(index_raw), 'exact_payloads': 305, 'exact_original_bindings': 417,
          'closed_jobs': 23, 'closed_receipt_files': 25, 'full_pass_or_merge_claimed': False,
          'both_interpretation_corrections_preserved': True, 'native_arrays_art_media_copied': False}
(out / 'ROOT_AUDIT.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record))
