"""Exact independent GitHub byte readback of the public174-file checkpoint."""
from pathlib import Path
import base64
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
COMMIT = '4fd0052f52a594e86ca77df0e50e12e8d026a874'
manifest = json.loads((ROOT / 'output/neon-camera-source-checkpoint-20261117-manifest.json').read_bytes())
paths = [row['path'] for row in manifest['files']] + ['experiments/neon_camera_source_checkpoint_catalogue_20261117/PUBLIC_MANIFEST.json']
assert len(paths) == len(set(paths)) == 174
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
seen = set()
verified = []
for start in range(0, 174, 20):
    batch = json.loads((ROOT / f'output/4fd0-all-remote-batch-{start:03}.json').read_bytes())
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
        working = (ROOT / name).read_bytes()
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
public = expected['experiments/neon_camera_source_checkpoint_catalogue_20261117/PUBLIC_MANIFEST.json'][1]
assert hashlib.sha256(public).hexdigest() == '1549568b8b838dd3b9304e56cf0bb0bc8995c9dc118aae60e841ba738881ced0'
target = ROOT / 'experiments/neon_camera_source_checkpoint_remote_20261117/COMPLETE_READBACK.json'
target.parent.mkdir(exist_ok=False)
with target.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump({'format': 'has_complete_independent_remote_readback_1', 'commit': COMMIT,
        'files': verified, 'file_count': len(verified), 'bytes': sum(row['bytes'] for row in verified),
        'redesign_merge_claimed': False, 'review_branch375_pushed': False, 'cleanup_performed': False}, stream, indent=2)
    stream.write('\n')
print(json.dumps({'commit': COMMIT, 'independent_exact_files': len(verified), 'bytes': sum(row['bytes'] for row in verified),
    'working_byte_recipes': sum(row['working_recipe']['kind'] != 'exact' for row in verified), 'redesign_merged': False, 'cleanup_performed': False}))
