"""Independent read-only audit. No archived builder is imported or executed."""
from pathlib import Path
import gzip
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
ROOTS = {'main': ROOT, 'neon': ROOT.parent / 'has-neon-review-20261116-c2d52ff'}
PINS = {
    'normal_setter_actual_packet_20261117': 'c47b56629c65159decb44bab975c52ea1f65b01754f44370cecab2e8b9b20df2',
    'neon_failed_381_actual_packet_20261117': '2bf3b9a947ede52cb7a8e64dab46580f16abb426ab345923b14631403e86c644',
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def privacy_screen(value, path=''):
    if isinstance(value, dict):
        forbidden = {'vertex_positions', 'corner_normals', 'setter_payload', 'initial_vertices',
                     'initial_corner_indices', 'source_raw_vertex_indices', 'source_lod0_vertex_indices',
                     'image_data', 'audio_data', 'base64'}
        for key, item in value.items():
            assert not (key in forbidden and item), (path, key)
            assert not (key in {'vertices', 'indices', 'triangles'} and isinstance(item, (list, dict))), (path, key)
            privacy_screen(item, path + '/' + str(key))
    elif isinstance(value, list):
        assert not (len(value) > 32 and all(isinstance(x, (float, int)) and not isinstance(x, bool) for x in value)), path
        for i, item in enumerate(value):
            privacy_screen(item, path + '/' + str(i))


def audit_packet(name, pin):
    folder = ROOT / 'experiments' / name
    index = folder / 'INDEX.json'
    raw = index.read_bytes()
    assert sha(raw) == pin
    document = json.loads(raw)
    listed = {row['path'] for row in document['files']}
    actual = {f.relative_to(folder).as_posix() for f in folder.rglob('*') if f.is_file() and f != index}
    assert len(listed) == len(document['files']) and listed == actual, (name, listed ^ actual)
    byte_count = json_count = gzip_count = 0
    for row in document['files']:
        relative = Path(row['path'])
        assert not relative.is_absolute() and '..' not in relative.parts
        source = folder / relative
        data = source.read_bytes()
        assert len(data) == row['bytes'] and sha(data) == row['sha256'], source
        assert source.suffix.lower() in {'.json', '.py', '.md', '.log', '.gz'}, source
        assert not source.name.startswith('PRIVATE'), source
        byte_count += len(data)
        if source.suffix == '.gz':
            data = gzip.decompress(data)
            gzip_count += 1
        text = data.decode('utf-8')
        assert not text.lstrip().startswith(('data:image', 'data:audio', 'data:video')), source
        if source.suffix == '.json' or source.name.endswith('.json.gz'):
            privacy_screen(json.loads(text))
            json_count += 1
    assert document.get('file_count', len(listed)) == len(listed) and document['bytes'] == byte_count
    bindings = json.loads((folder / 'EXACT_SOURCE_BINDINGS.json').read_bytes())['files']
    assert len({row['archive_path'] for row in bindings}) == len(bindings)
    compressed_count = original_bytes = 0
    for row in bindings:
        source = ROOTS[row['root']] / row['path']
        original = source.read_bytes()
        archived = (folder / row['archive_path']).read_bytes()
        assert not source.name.startswith('PRIVATE'), source
        assert len(original) == row['bytes'] and sha(original) == row['sha256'], source
        assert len(archived) == row['archive_bytes'] and sha(archived) == row['archive_sha256'], source
        body = gzip.decompress(archived) if row['gzip_exact_original'] else archived
        assert body == original, source
        compressed_count += bool(row['gzip_exact_original'])
        original_bytes += len(original)
    return {
        'packet': name, 'expected_index_sha256': pin, 'index_sha256_verified': True,
        'closed_payload_set': True, 'payload_files': len(listed), 'payload_bytes': byte_count,
        'gzip_payloads': gzip_count, 'JSON_payloads_structurally_screened': json_count,
        'exact_original_bindings': len(bindings), 'exact_gzip_original_bindings': compressed_count,
        'bound_original_bytes': original_bytes, 'all_original_and_compressed_SHA_bytes_and_body_equal': True,
        'no_media_or_PRIVATE_payload_paths': True,
        'no_forbidden_native_array_JSON_keys_or_large_numeric_arrays_found': True,
        'source_code_reference_to_private_paths_is_not_a_private_payload': True,
    }


def main():
    result = {
        'format': 'has_independent_actual_archive_audit_1', 'status': 'PASS_SOURCE_AND_CPU_ONLY',
        'reports': [audit_packet(name, pin) for name, pin in PINS.items()],
        'limitations': 'Public structured payloads and text formats screened; no original private native output or media read. Hash-only private references remain permitted. No engines, CIM, Git or functional-source mutation.',
    }
    target = HERE / 'INDEPENDENT_ACTUAL_ARCHIVE_AUDIT.json'
    target.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'audit_sha256': sha(target.read_bytes()), 'results': result['reports']}))


if __name__ == '__main__':
    main()
