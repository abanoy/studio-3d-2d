"""Independent root checks for the exact focused Windows evidence archive."""
from pathlib import Path
import gzip, hashlib, json

ROOT = Path(__file__).resolve().parents[1]
NEON = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
PACKET = ROOT / 'experiments/neon_focused_followup_actual_packet_20261117'

def sha(body):
    return hashlib.sha256(body).hexdigest()

assert sha((PACKET / 'INDEX.json').read_bytes()) == '7720129209746ac294b3a752c7296b688d957bd8fcbba57419a544b5351ab2a5'
entries = json.loads((PACKET / 'INDEX.json').read_bytes())['files']
assert len(entries) == 156 and sum(row['bytes'] for row in entries) == 361380
names = {row['path'] for row in entries}
assert len(names) == 156
assert {p.relative_to(PACKET).as_posix() for p in PACKET.rglob('*') if p.is_file()} == names | {'INDEX.json'}
allowed = {'.json', '.log', '.gz', '.gd', '.py', '.md', '.original', '.cfg'}
for row in entries:
    path = PACKET / row['path']
    assert path.resolve().is_relative_to(PACKET) and not path.is_symlink() and path.suffix in allowed
    raw = path.read_bytes()
    assert len(raw) == row['bytes'] and sha(raw) == row['sha256']
    text = gzip.decompress(raw) if path.suffix == '.gz' else raw
    assert b'\0' not in text
    text.decode('utf-8')
    assert not path.name.startswith('PRIVATE_')
bindings = json.loads((PACKET / 'EXACT_SOURCE_BINDINGS.json').read_bytes())['files']
assert len(bindings) == 143
for row in bindings:
    base = {'main': ROOT, 'neon': NEON}[row['root']]
    original = base / row['path']
    assert original.resolve().is_relative_to(base) and not original.is_symlink()
    archived = (PACKET / row['archive_path']).read_bytes()
    assert len(archived) == row['archive_bytes'] and sha(archived) == row['archive_sha256']
    decoded = gzip.decompress(archived) if row['gzip_exact_original'] else archived
    assert len(decoded) == row['bytes'] and sha(decoded) == row['sha256']
    assert decoded == original.read_bytes()
facts = json.loads((PACKET / 'ACTUAL_RESULT.json').read_bytes())
assert facts['full_suite_passed'] is False and facts['old_failures_replaced'] is False
assert facts['media_native_arrays_or_original_art_included'] is False
assert facts['physical_receipt_files_selected'] == 13
assert facts['explicit_command_or_result_receipt_bindings'] == 11
assert facts['temporal_stem_only_receipt_associations'] == 2
target = ROOT / 'experiments/neon_focused_root_archive_audit_20261117'
target.mkdir(exist_ok=False)
record = {'format': 'has_root_focused_archive_audit_1', 'passed': True,
          'index_sha256': sha((PACKET / 'INDEX.json').read_bytes()),
          'exact_payloads': 156, 'exact_original_bindings': 143, 'physical_receipts': 13,
          'weaker_historical_associations_stay_labeled': 2, 'full_suite_pass_claimed': False,
          'media_native_arrays_or_original_art_copied': False}
(target / 'ROOT_AUDIT.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record))
