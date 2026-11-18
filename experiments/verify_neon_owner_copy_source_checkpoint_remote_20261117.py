"""Independent byte readback for one metadata-only owner-copy checkpoint.

The commit and manifest pin are supplied after the actual commit. Every selected
path is checked against independent remote response bytes, immutable Git blobs
and a reversible working-tree EOL recipe. Native/runtime reports stay private.
"""
from pathlib import Path, PurePosixPath
import argparse
import base64
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PARENT = '973039e40622ac20600e6d297d712de419877eda'
PUBLIC_MANIFEST = 'experiments/neon_owner_copy_source_checkpoint_catalogue_20261117/PUBLIC_MANIFEST.json'


def safe_relative(name):
    assert type(name) is str and name and '\\' not in name and ':' not in name
    relative = PurePosixPath(name)
    assert not relative.is_absolute() and all(part not in ('', '.', '..') for part in relative.parts), name
    parts = [part.casefold() for part in relative.parts]
    assert parts[0] in ('experiments', 'docs') or name == 'LLM.md', name
    assert not any(part in ('output', '.git', '.godot', '__pycache__', 'receipt-logs', 'terminal-audit')
                   or part.startswith('private') or 'remote-batch' in part for part in parts), name
    assert relative.suffix in ('.json', '.md', '.py', '.gd', '.ps1', '.patch', '.proposed', '.original', '.log', '.txt', '.gz', '.cfg'), name
    return relative


def checked_path(path):
    path = Path(path).absolute()
    assert path.resolve().is_relative_to(ROOT.resolve()) and path.is_file(), str(path)
    cursor = path
    while cursor != ROOT:
        assert not cursor.is_symlink() and not getattr(cursor.lstat(), 'st_file_attributes', 0) & 0x400, str(cursor)
        cursor = cursor.parent
    return path


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--commit', required=True)
parser.add_argument('--manifest', type=Path, required=True)
parser.add_argument('--manifest-sha256', required=True)
parser.add_argument('--cache-prefix', required=True)
args = parser.parse_args()
COMMIT = args.commit
assert re.fullmatch(r'[0-9a-f]{40}', COMMIT) and re.fullmatch(r'[0-9a-f]{64}', args.manifest_sha256)
assert re.fullmatch(r'[A-Za-z0-9_-]+', args.cache_prefix)
manifest_path = checked_path(args.manifest)
assert manifest_path.parent == ROOT / 'output'
manifest_raw = manifest_path.read_bytes()
assert hashlib.sha256(manifest_raw).hexdigest() == args.manifest_sha256
manifest = json.loads(manifest_raw)
assert manifest['format'] == 'has_public_neon_owner_copy_source_checkpoint_catalogue_1'
assert manifest['metadata_parent_HEAD_at_preparation_Root_reported'] == PARENT
assert manifest['main_functional_matches_qualified_candidate'] == 1029
rows = manifest['files']
assert type(rows) is list and rows
paths = [row['path'] for row in rows] + [PUBLIC_MANIFEST]
assert len(paths) == len(set(paths))
for row in rows:
    assert type(row['bytes']) is int and row['bytes'] > 0 and re.fullmatch(r'[0-9a-f]{64}', row['sha256'])
for name in paths:
    safe_relative(name)
checkpoint_header = subprocess.check_output(['git', 'cat-file', 'commit', COMMIT], cwd=ROOT).split(b'\n\n', 1)[0]
assert [line.split()[1].decode() for line in checkpoint_header.splitlines() if line.startswith(b'parent ')] == [PARENT]
diff_raw = subprocess.check_output(['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', '-z', PARENT, COMMIT], cwd=ROOT)
assert diff_raw and diff_raw.endswith(b'\0')
changed = [name.decode('utf-8') for name in diff_raw[:-1].split(b'\0')]
assert len(changed) == len(set(changed)) and set(changed) <= set(paths), 'Unexpected checkpoint change outside exact metadata selection'
for name in changed:
    safe_relative(name)

query = ''.join(COMMIT + ':' + name + '\n' for name in paths).encode()
raw_git = subprocess.check_output(['git', 'cat-file', '--batch'], input=query, cwd=ROOT)
expected = {}
offset = 0
for name in paths:
    end = raw_git.index(b'\n', offset)
    blob, kind, size = raw_git[offset:end].decode().split(' ')
    assert kind == 'blob'
    size = int(size)
    body = raw_git[end + 1:end + 1 + size]
    assert len(body) == size and raw_git[end + 1 + size:end + 2 + size] == b'\n'
    expected[name] = (blob, body)
    offset = end + size + 2
assert offset == len(raw_git)
assert expected[PUBLIC_MANIFEST][1] == manifest_raw
seen = set()
verified = []
for start in range(0, len(paths), 20):
    batch_path = checked_path(ROOT / 'output' / f'{args.cache_prefix}{start:03}.json')
    batch = json.loads(batch_path.read_bytes())
    assert batch['commit'] == COMMIT and batch['start'] == start
    assert [row['path'] for row in batch['files']] == paths[start:start + 20]
    for row in batch['files']:
        name = row['path']
        assert name not in seen
        seen.add(name)
        response = row['response']
        assert response['encoding'] == 'base64'
        remote = base64.b64decode(response['content'])
        method = 'contents_base64'
        if not remote and 'fallback_utf8' in row:
            remote = row['fallback_utf8'].encode('utf-8')
            method = 'blob_sha_utf8_contents_api_oversize_fallback'
        blob = hashlib.sha1(b'blob ' + str(len(remote)).encode() + b'\0' + remote).hexdigest()
        wanted_blob, wanted_bytes = expected[name]
        assert blob == response['sha'] == wanted_blob and remote == wanted_bytes, name
        working = checked_path(ROOT / name).read_bytes()
        if working == remote:
            recipe = {'kind': 'exact'}
        else:
            assert b'\r' not in remote and working.replace(b'\r\n', b'\n') == remote
            endings = [i for i, line in enumerate(working.splitlines(keepends=True)) if line.endswith(b'\r\n')]
            selected = set(endings)
            rebuilt = b''.join(line[:-1] + b'\r\n' if i in selected and line.endswith(b'\n') else line for i, line in enumerate(remote.splitlines(keepends=True)))
            assert rebuilt == working
            recipe = {'kind': 'LF_blob_with_selected_CRLF_lines', 'zero_based_lines': endings}
        verified.append({'path': name, 'bytes': len(remote), 'sha256': hashlib.sha256(remote).hexdigest(),
            'git_blob': blob, 'independent_remote_bytes_exact': True, 'remote_method': method,
            'working_sha256': hashlib.sha256(working).hexdigest(), 'working_recipe': recipe})
assert seen == set(paths)
for row in rows:
    working = checked_path(ROOT / row['path']).read_bytes()
    assert len(working) == row['bytes'] and hashlib.sha256(working).hexdigest() == row['sha256'], row['path']
public = expected[PUBLIC_MANIFEST][1]
assert hashlib.sha256(public).hexdigest() == args.manifest_sha256

target = ROOT / 'experiments/neon_owner_copy_source_checkpoint_remote_20261117/COMPLETE_READBACK.json'
target.parent.mkdir(exist_ok=False)
with target.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump({'format': 'has_complete_independent_remote_readback_1', 'commit': COMMIT,
        'single_parent': PARENT, 'metadata_only_changed_paths': changed,
        'checkpoint_catalogue_files': len(paths), 'changed_file_count': len(changed),
        'public_manifest_sha256': args.manifest_sha256,
        'files': verified, 'file_count': len(verified), 'bytes': sum(row['bytes'] for row in verified),
        'owner_copy_passed': manifest['actual_owner_copy_passed'],
        'cold_attempts_overall': manifest['cold_attempts_overall'],
        'raw_native_runtime_reports_included': False, 'cleanup_performed': False}, stream, indent=2)
    stream.write('\n')
print(json.dumps({'commit': COMMIT, 'independent_exact_files': len(verified), 'changed_file_count': len(changed),
    'bytes': sum(row['bytes'] for row in verified),
    'working_byte_recipes': sum(row['working_recipe']['kind'] != 'exact' for row in verified), 'cleanup_performed': False}))
