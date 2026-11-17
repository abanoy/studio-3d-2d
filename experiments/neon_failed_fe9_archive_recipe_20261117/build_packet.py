"""Copy-only exact text archive for one already-closed failed run."""
from pathlib import Path
import gzip
import json
from archive_checks import check, need, parse, same, sha

HERE = Path(__file__).resolve().parent
DEST = HERE.parent / 'neon_failed_fe9_actual_packet_20261117'
INPUTS_SHA = 'a0b2ecdcd8db87363384188a927eb1f58f071250ca6bba34e952e8a40d07f230'


def safe(path, root):
    need(path.is_absolute() and path.resolve().is_relative_to(root.resolve()), 'Owned input boundary')
    for part in (path, *path.parents):
        if part == root.parent:
            break
        need(not part.is_symlink() and not getattr(part.lstat(), 'st_file_attributes', 0) & 0x400, 'Input reparse refused')
    need(path.is_file(), 'Regular input required')


def save(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, allow_nan=False); stream.write('\n')


def main():
    need(not DEST.exists(), 'Never overwrite an archive')
    spec_raw = (HERE / 'INPUTS.json').read_bytes()
    need(sha(spec_raw) == INPUTS_SHA, 'Frozen input list changed')
    spec = parse(spec_raw)
    need(spec['format'] == 'has_fe9_closed_failure_archive_inputs_1' and len(spec['inputs']) == 85, 'Exact frozen closed input scope')
    raw, total = {}, 0
    for row in spec['inputs']:
        need(row['root'] in ('MAIN', 'REVIEW') and not Path(row['path']).is_absolute() and '..' not in Path(row['path']).parts and row['alias'] not in raw, 'Input domain/duplicates')
        root = Path(spec['roots'][row['root']]); path = root / row['path']; safe(path, root)
        a = path.stat(); data = path.read_bytes(); b = path.stat()
        need((a.st_size, a.st_mtime_ns) == (b.st_size, b.st_mtime_ns) == (row['bytes'], row['mtime_ns']), 'Original metadata changed')
        need(len(data) <= 2 * 1024 * 1024 and b'\0' not in data and sha(data) == row['sha256'], 'Original exact bounded text changed')
        data.decode('utf-8-sig'); total += len(data); need(total <= 16 * 1024 * 1024, 'Global retained text cap')
        raw[row['alias']] = data
    result = check(raw); need(same(result, spec['expected_summary']), 'Scoped result changed')
    unique = {sha(data): data for data in raw.values()}
    DEST.mkdir(); (DEST / 'objects').mkdir()
    objects = []
    for digest, data in sorted(unique.items()):
        packed = gzip.compress(data, compresslevel=9, mtime=0); name = 'objects/' + digest + '.gz'
        with (DEST / name).open('xb') as stream:
            stream.write(packed)
        objects.append({'path': name, 'bytes': len(packed), 'sha256': sha(packed), 'decoded_bytes': len(data), 'decoded_sha256': digest})
    save(DEST / 'BINDINGS.json', {'format': 'has_fe9_closed_failure_bindings_1', 'roots': spec['roots'], 'inputs': spec['inputs']})
    save(DEST / 'ACTUAL_RESULT.json', result)
    with (DEST / 'README.md').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write((HERE / 'PACKET_README.md').read_text(encoding='utf-8'))
    files = []
    for name in ('BINDINGS.json', 'ACTUAL_RESULT.json', 'README.md'):
        data = (DEST / name).read_bytes(); files.append({'path': name, 'bytes': len(data), 'sha256': sha(data)})
    save(DEST / 'INDEX.json', {'format': 'has_fe9_closed_failure_exact_archive_1', 'recipe_inputs_sha256': INPUTS_SHA,
        'builder_sha256': sha(Path(__file__).read_bytes()), 'checker_sha256': sha((HERE / 'archive_checks.py').read_bytes()),
        'verifier_sha256': sha((HERE / 'verify_packet.py').read_bytes()), 'original_bindings': len(raw), 'unique_objects': len(unique),
        'decoded_total_bytes_including_aliases': total, 'objects': objects, 'files': files, 'full_suite_passed': False, 'native_art_arrays_copied': False})
    print(json.dumps({'INDEX_sha256': sha((DEST / 'INDEX.json').read_bytes()), 'original_bindings': len(raw), 'unique_objects': len(unique), 'compressed_bytes': sum(row['bytes'] for row in objects)}, indent=2))


if __name__ == '__main__':
    main()
