"""One-shot closed-foundation text archive, no runtime execution or deletion."""
from pathlib import Path
import gzip
import hashlib
import json
from archive_checks import check, load, require, same

HERE = Path(__file__).resolve().parent
DEST = HERE.parent / 'neon_foundation_fe9_actual_packet_20261117'
INPUTS_SHA = 'd1f896070f114f78d72ede167d3056b3e22f0e81d8def63e80c07c2f1f27f2f6'


def sha(raw): return hashlib.sha256(raw).hexdigest()


def safe(path, root):
    require(path.is_absolute() and path.resolve().is_relative_to(root), 'Owned input boundary')
    for item in (path, *path.parents):
        if item == root.parent: break
        require(not item.is_symlink() and not getattr(item.lstat(), 'st_file_attributes', 0) & 0x400, 'Input reparse refused')
    require(path.is_file(), 'Regular input required')


def save(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream: json.dump(value, stream, indent=2, allow_nan=False); stream.write('\n')


def main():
    require(not DEST.exists(), 'Never overwrite an earlier archive')
    spec_raw = (HERE / 'INPUTS.json').read_bytes(); require(sha(spec_raw) == INPUTS_SHA, 'Frozen input list differs')
    spec = load(spec_raw); require(spec['format'] == 'has_foundation_fe9_closed_text_archive_recipe_1', 'Exact recipe format')
    raw = {}
    for row in spec['inputs']:
        require(row['root'] in ('MAIN', 'REVIEW') and row['path'] not in ('', '.') and not Path(row['path']).is_absolute() and '..' not in Path(row['path']).parts, 'Input alias/domain')
        root = Path(spec['roots'][row['root']]); path = root / row['path']; safe(path, root)
        require(path.suffix in ('.json', '.log', '.py'), 'Only admitted source/scalar/log files')
        before = path.stat(); data = path.read_bytes(); after = path.stat()
        require((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns) == (row['bytes'], row['mtime_ns']), 'Original metadata differs')
        require(len(data) <= 2 * 1024 * 1024 and b'\0' not in data and sha(data) == row['sha256'], 'Original exact bounded text differs')
        data.decode('utf-8-sig'); key = row['root'] + ':' + row['path']; require(key not in raw, 'Duplicate input'); raw[key] = data
    summary = check(raw, spec['roots']['REVIEW']); require(same(summary, spec['expected_summary']), 'Summary differs')
    unique = {sha(data): data for data in raw.values()}
    DEST.mkdir(); (DEST / 'objects').mkdir(); objects = []
    for digest, data in sorted(unique.items()):
        packed = gzip.compress(data, compresslevel=9, mtime=0); name = 'objects/' + digest + '.gz'
        with (DEST / name).open('xb') as stream: stream.write(packed)
        objects.append({'path': name, 'bytes': len(packed), 'sha256': sha(packed), 'decoded_bytes': len(data), 'decoded_sha256': digest})
    save(DEST / 'BINDINGS.json', {'format': 'has_foundation_fe9_original_text_bindings_1', 'roots': spec['roots'], 'bindings': spec['inputs']})
    save(DEST / 'ACTUAL_RESULT.json', summary)
    with (DEST / 'README.md').open('x', encoding='utf-8', newline='\n') as stream: stream.write((HERE / 'PACKET_README.md').read_text(encoding='utf-8'))
    plain = []
    for name in ('BINDINGS.json', 'ACTUAL_RESULT.json', 'README.md'):
        data = (DEST / name).read_bytes(); plain.append({'path': name, 'bytes': len(data), 'sha256': sha(data)})
    index = {'format': 'has_foundation_fe9_compact_exact_actual_packet_1', 'recipe_inputs_sha256': sha(spec_raw), 'original_bindings': len(raw), 'unique_decoded_objects': len(unique),
             'builder_sha256': sha(Path(__file__).read_bytes()), 'verifier_sha256': sha((HERE / 'verify_packet.py').read_bytes()), 'check_source_sha256': sha((HERE / 'archive_checks.py').read_bytes()),
             'objects': objects, 'files': plain, 'uncompressed_original_bytes': sum(len(data) for data in raw.values()), 'real_private_jobs': 1,
             'full_suite_pass_claimed': False, 'native_fidelity_claimed': False, 'upcoming_full_output_read': False, 'decoded_art_models_media_native_arrays_included': False}
    save(DEST / 'INDEX.json', index)
    print(json.dumps({'archive': str(DEST), 'INDEX_sha256': sha((DEST / 'INDEX.json').read_bytes()), 'original_bindings': len(raw), 'unique_objects': len(unique), 'compressed_object_bytes': sum(r['bytes'] for r in objects)}, indent=2))


if __name__ == '__main__': main()
