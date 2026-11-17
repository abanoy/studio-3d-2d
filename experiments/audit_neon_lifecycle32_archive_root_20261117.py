"""Independently verify the standalone32 exact-text append, without native calls."""
from pathlib import Path
import gzip, hashlib, json

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
PACKET = ROOT / 'experiments/neon_world_lifecycle32_actual_packet_20261117'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
assert sha((PACKET / 'INDEX.json').read_bytes()) == 'db32fd9398c358a74b455d26e074482c717c456b812b17fd43a3d5233e41618e'
rows = json.loads((PACKET / 'INDEX.json').read_bytes())['files']
assert len(rows) == 36 and sum(row['bytes'] for row in rows) == 130015
names = {row['path'] for row in rows}
assert len(names) == 36 and {p.relative_to(PACKET).as_posix() for p in PACKET.rglob('*') if p.is_file()} == names | {'INDEX.json'}
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
assert set(roots.values()).issubset({ROOT, REVIEW})
bindings = json.loads((PACKET / 'EXACT_SOURCE_BINDINGS.json').read_bytes())['files']
assert len(bindings) == 33
for row in bindings:
    original = roots[row['root']] / row['path']
    assert original.resolve().is_relative_to(roots[row['root']]) and not original.is_symlink()
    packed = (PACKET / row['archive_path']).read_bytes()
    assert len(packed) == row['archive_bytes'] and sha(packed) == row['archive_sha256']
    raw = gzip.decompress(packed) if row['gzip_exact_original'] else packed
    assert len(raw) == row['bytes'] and sha(raw) == row['sha256'] and raw == original.read_bytes()
facts = json.loads((PACKET / 'ACTUAL_RESULT.json').read_bytes())
assert facts['report']['checks'] == 32 and facts['report']['failures'] == 0
assert facts['formal12504_changed'] is False and facts['full_Windows_PASS_claimed'] is False
assert facts['unique_physical_jobs'] == 1 and facts['native_arrays_art_media_or_projects_included'] is False
out = ROOT / 'experiments/neon_lifecycle32_root_audit_20261117'
out.mkdir(exist_ok=False)
record = {'format': 'has_root_neon_standalone32_archive_audit_1', 'passed': True, 'exact_payloads': 36,
          'exact_original_bindings': 33, 'checks': 32, 'failures': 0, 'closed_physical_jobs': 1,
          'formal12504_changed': False, 'full_pass_claimed': False, 'private_arrays_art_media_copied': False}
(out / 'ROOT_AUDIT.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record))
