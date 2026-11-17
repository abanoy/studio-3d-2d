"""Root independently checks compact public archives against their originals."""
from pathlib import Path
import gzip, hashlib, json

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
PACKETS = (
    ('normal_setter_actual_packet_20261117', 'c47b56629c65159decb44bab975c52ea1f65b01754f44370cecab2e8b9b20df2', 35, 25),
    ('neon_failed_381_actual_packet_20261117', '2bf3b9a947ede52cb7a8e64dab46580f16abb426ab345923b14631403e86c644', 52, 42),
)

def sha(data):
    return hashlib.sha256(data).hexdigest()

results = []
for name, pin, payload_count, binding_count in PACKETS:
    packet = ROOT / 'experiments' / name
    assert sha((packet / 'INDEX.json').read_bytes()) == pin
    entries = json.loads((packet / 'INDEX.json').read_bytes())['files']
    assert len(entries) == payload_count
    names = {row['path'] for row in entries}
    assert len(names) == payload_count
    actual = {p.relative_to(packet).as_posix() for p in packet.rglob('*') if p.is_file()}
    assert actual == names | {'INDEX.json'}
    allowed = {'.json', '.md', '.py', '.ps1', '.gd', '.log', '.txt', '.gz'}
    for row in entries:
        path = packet / row['path']
        assert path.resolve().is_relative_to(packet) and not path.is_symlink()
        assert path.suffix.lower() in allowed
        data = path.read_bytes()
        assert len(data) == row['bytes'] and sha(data) == row['sha256']
        decoded = gzip.decompress(data) if path.suffix == '.gz' else data
        decoded.decode('utf-8-sig')
        assert b'\0' not in decoded
        assert 'PRIVATE_SETTER' not in path.name
    bindings = json.loads((packet / 'EXACT_SOURCE_BINDINGS.json').read_bytes())['files']
    assert len(bindings) == binding_count
    for row in bindings:
        base = {'main': ROOT, 'neon': REVIEW}[row['root']]
        original = base / row['path']
        assert original.resolve().is_relative_to(base) and not original.is_symlink()
        packed = (packet / row['archive_path']).read_bytes()
        assert len(packed) == row['archive_bytes'] and sha(packed) == row['archive_sha256']
        raw = gzip.decompress(packed) if row['gzip_exact_original'] else packed
        assert len(raw) == row['bytes'] and sha(raw) == row['sha256']
        assert raw == original.read_bytes()
    results.append({'packet': name, 'index_sha256': pin,
                    'exact_payloads': payload_count, 'exact_original_files': binding_count,
                    'all_text_or_compressed_text': True,
                    'private_arrays_media_or_projects_copied': False})

target = ROOT / 'experiments' / 'setter_failed381_root_archive_audit_20261117'
target.mkdir(exist_ok=False)
record = {'format': 'has_independent_public_archive_root_audit_1',
          'passed': True, 'archives': results, 'product_test_checks_claimed': 0}
(target / 'ROOT_AUDIT.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record))
