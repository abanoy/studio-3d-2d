"""Create only the pinned public metadata archive after root review; never run native tools."""
from pathlib import Path
import argparse
import gzip
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SAFE_SUFFIXES = {'.json', '.log', '.cfg', '.py', '.gd', '.original', '.md', '.patch'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def safe_relative(value):
    path = Path(value)
    assert not path.is_absolute() and '..' not in path.parts and path.parts, value
    # Public physical receipts live in private-desktop; PRIVATE_* native payloads do not.
    assert not any(part.startswith('PRIVATE_') for part in path.parts), value
    return path


def privacy_screen(value):
    if isinstance(value, dict):
        for key, item in value.items():
            assert not (key in {'vertex_positions', 'corner_normals', 'setter_payload', 'initial_vertices',
                                'initial_corner_indices', 'source_raw_vertex_indices', 'source_lod0_vertex_indices',
                                'image_data', 'audio_data', 'base64'} and item), key
            assert not (key in {'vertices', 'indices', 'triangles', 'normals', 'positions', 'tangents',
                                'bone_matrices', 'normal_words'} and isinstance(item, (list, dict))), key
            privacy_screen(item)
    elif isinstance(value, list):
        assert not (len(value) > 32 and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in value))
        for item in value:
            privacy_screen(item)


def transport(row, data):
    # Validate type and body before compression or any target-directory creation.
    source_path = safe_relative(row['path'])
    safe_relative(row['archive_path'])
    assert source_path.suffix.lower() in SAFE_SUFFIXES, source_path
    assert type(row['bytes']) is int and len(data) == row['bytes'] and sha(data) == row['sha256']
    text = data.decode('utf-8')
    assert not text.lstrip().startswith(('data:image', 'data:audio', 'data:video'))
    if source_path.suffix == '.json':
        privacy_screen(json.loads(text))
    assert type(row['gzip_exact_original']) is bool
    body = gzip.compress(data, compresslevel=9, mtime=0) if row['gzip_exact_original'] else data
    assert (gzip.decompress(body) if row['gzip_exact_original'] else body) == data
    return body


def verify_recipe(expected):
    index_path = HERE / 'INDEX.json'
    assert sha(index_path.read_bytes()) == expected
    index = json.loads(index_path.read_bytes())
    actual = {p.relative_to(HERE).as_posix() for p in HERE.rglob('*') if p.is_file() and p != index_path}
    assert actual == {row['path'] for row in index['files']}
    for row in index['files']:
        body = (HERE / safe_relative(row['path'])).read_bytes()
        assert len(body) == row['bytes'] and sha(body) == row['sha256']
    return index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-recipe-index', required=True)
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    verify_recipe(options.expected_recipe_index)
    target = options.output.resolve()
    assert target.parent == (ROOT / 'experiments').resolve() and not target.exists(), target
    assert target.name == 'neon_focused_followup_actual_packet_20261117', target
    plan = json.loads((HERE / 'INPUTS.json').read_bytes())
    prepared = []
    for row in plan['files']:
        source = Path(plan['roots'][row['root']]) / safe_relative(row['path'])
        raw = source.read_bytes()
        prepared.append((row, raw, transport(row, raw)))
    assert len(prepared) == len({row['archive_path'] for row, _, _ in prepared})
    # All input/source/privacy gates above finish before the first mutation.
    target.mkdir(exist_ok=False)
    bindings = []
    for row, raw, body in prepared:
        destination = target / safe_relative(row['archive_path'])
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(body)
        bindings.append(dict(row, archive_sha256=sha(body), archive_bytes=len(body)))
    for source in HERE.iterdir():
        if source.is_file():
            destination = target / 'recipe' / source.name
            destination.parent.mkdir(exist_ok=True)
            destination.write_bytes(source.read_bytes())
    (target / 'EXACT_SOURCE_BINDINGS.json').write_text(json.dumps({'format': 'has_public_archive_exact_sources_1', 'files': bindings}, indent=2) + '\n', encoding='utf-8')
    (target / 'ACTUAL_RESULT.json').write_bytes((HERE / 'ACTUAL_FACTS.json').read_bytes())
    (target / 'README.md').write_text('Public scalar/source/receipt follow-up evidence only. Earlier failures, script watchdog and successful successors remain distinct; no full-suite PASS is claimed. Media, native arrays and original art are excluded. See ACTUAL_RESULT.json and recipe/README.md.\n', encoding='utf-8')
    files = [{'path': p.relative_to(target).as_posix(), 'bytes': p.stat().st_size, 'sha256': sha(p.read_bytes())}
             for p in sorted(target.rglob('*')) if p.is_file()]
    index = {'format': 'has_source_experiment_index_1', 'packet': target.name, 'files': files,
             'file_count': len(files), 'bytes': sum(row['bytes'] for row in files), 'excludes': ['INDEX.json']}
    (target / 'INDEX.json').write_text(json.dumps(index, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'packet': str(target), 'index_sha256': sha((target / 'INDEX.json').read_bytes()),
                      'files': len(files), 'bytes': index['bytes'], 'native_processes_started': False}))


if __name__ == '__main__':
    main()
