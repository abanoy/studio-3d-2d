"""Verify every public checkpoint file from independent GitHub connector bytes."""
from pathlib import Path
import base64, hashlib, json, subprocess

ROOT = Path(__file__).resolve().parents[1]
COMMIT = '1ce433bd7484e2e1652fafa5a5d2d58b0f0c1329'
manifest = json.loads((ROOT / 'output/neon-completed-checkpoint-20261117-manifest-v2.json').read_bytes())
paths = [row['path'] for row in manifest['files']]
assert len(paths) == len(set(paths)) == 565
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
for start in range(0, 565, 20):
    source = ROOT / f'output/1ce-all-remote-batch-{start:03}.json'
    batch = json.loads(source.read_bytes())
    assert batch['commit'] == COMMIT and batch['start'] == start
    assert [row['path'] for row in batch['files']] == paths[start:start + 20]
    for row in batch['files']:
        name = row['path']
        assert name not in seen
        seen.add(name)
        response = row['response']
        assert response['encoding'] == 'base64'
        remote = base64.b64decode(response['content'])
        remote_method = 'contents_base64'
        if not remote and name == 'docs/progress_memo.md':
            fallback = json.loads((ROOT / 'output/1ce-progress-memo-remote-blob.json').read_bytes())
            assert fallback['path'] == name and fallback['encoding'] == 'utf-8'
            assert fallback['blob_sha'] == response['sha']
            remote = fallback['content'].encode('utf-8')
            remote_method = 'blob_sha_utf8_contents_api_oversize_fallback'
        blob = hashlib.sha1(b'blob ' + str(len(remote)).encode() + b'\0' + remote).hexdigest()
        wanted_blob, wanted_bytes = expected[name]
        assert blob == response['sha'] == wanted_blob and remote == wanted_bytes, (name, len(remote), len(wanted_bytes), blob, response['sha'], wanted_blob)
        working = (ROOT / name).read_bytes()
        if working == remote:
            recipe = {'kind': 'exact'}
        else:
            assert b'\r' not in remote
            # Preserve exact mixed working line endings if an append retained an old prefix.
            assert working.replace(b'\r\n', b'\n') == remote
            endings = [i for i, line in enumerate(working.splitlines(keepends=True)) if line.endswith(b'\r\n')]
            lines = remote.splitlines(keepends=True)
            rebuilt = b''.join(line[:-1] + b'\r\n' if i in set(endings) and line.endswith(b'\n') else line
                               for i, line in enumerate(lines))
            assert rebuilt == working
            recipe = {'kind': 'LF_blob_with_selected_CRLF_lines', 'zero_based_lines': endings}
        verified.append({'path': name, 'bytes': len(remote), 'sha256': hashlib.sha256(remote).hexdigest(),
                         'git_blob': blob, 'independent_remote_bytes_exact': True, 'remote_method': remote_method,
                         'working_sha256': hashlib.sha256(working).hexdigest(), 'working_recipe': recipe})
assert seen == set(paths)
target = ROOT / 'experiments/neon_completed_checkpoint_remote_20261117/COMPLETE_READBACK.json'
with target.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump({'format': 'has_complete_independent_remote_readback_1', 'commit': COMMIT,
               'files': verified, 'file_count': len(verified), 'bytes': sum(row['bytes'] for row in verified),
               'redesign_merge_claimed': False, 'cleanup_performed': False}, stream, indent=2)
    stream.write('\n')
print(json.dumps({'commit': COMMIT, 'exact_remote_files': len(verified),
                  'bytes': sum(row['bytes'] for row in verified),
                  'working_byte_recipes': sum(row['working_recipe']['kind'] != 'exact' for row in verified),
                  'redesign_merged': False, 'cleanup_performed': False}))
