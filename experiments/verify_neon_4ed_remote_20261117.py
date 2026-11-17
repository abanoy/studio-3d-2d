"""Independently verify the four backed-up candidate files, not a merge claim."""
from pathlib import Path
import base64
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
COMMIT = '4ed3a63b716f696daa1699a76443d6f1abb9b096'
paths = ['tests/scene_view_smoke.gd', 'tests/verify_scene_view.py', 'LLM.md', 'docs/REDESIGN-PORT.md']
changed = subprocess.check_output(['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', COMMIT], cwd=REVIEW, text=True).splitlines()
assert set(changed) == set(paths)
rows = []
for index, name in enumerate(paths):
    response = json.loads((ROOT / f'output/4ed-remote-{index}.json').read_bytes())
    assert response['path'] == name and response['result']['isError'] is False
    remote = response['result']['structuredContent']
    assert remote['encoding'] == 'base64'
    raw = base64.b64decode(remote['content'], validate=False)
    wanted = subprocess.check_output(['git', 'show', f'{COMMIT}:{name}'], cwd=REVIEW)
    blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
    local_blob = subprocess.check_output(['git', 'rev-parse', f'{COMMIT}:{name}'], cwd=REVIEW, text=True).strip()
    assert raw == wanted and blob == remote['sha'] == local_blob, name
    working = (REVIEW / name).read_bytes()
    if working == raw:
        recipe = {'kind': 'exact'}
    else:
        assert b'\r' not in raw and working.replace(b'\r\n', b'\n') == raw
        endings = [i for i, line in enumerate(working.splitlines(keepends=True)) if line.endswith(b'\r\n')]
        ending_set = set(endings)
        rebuilt = b''.join(line[:-1] + b'\r\n' if i in ending_set and line.endswith(b'\n') else line for i, line in enumerate(raw.splitlines(keepends=True)))
        assert rebuilt == working
        recipe = {'kind': 'LF_blob_with_selected_CRLF_lines', 'zero_based_lines': endings}
    rows.append({'path': name, 'bytes': len(raw), 'git_blob': blob, 'sha256': hashlib.sha256(raw).hexdigest(),
                 'independent_remote_bytes_exact': True, 'working_sha256': hashlib.sha256(working).hexdigest(), 'working_recipe': recipe})
target = ROOT / 'experiments/neon_4ed_candidate_remote_20261117'
target.mkdir(exist_ok=False)
(target / 'REMOTE_READBACK.json').write_text(json.dumps({'format': 'has_neon_candidate_independent_remote_readback_1', 'commit': COMMIT,
    'files': rows, 'file_count': len(rows), 'main_merged': False, 'full_pass_claimed': False, 'cleanup_performed': False}, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({'commit': COMMIT, 'independent_exact_files': len(rows), 'bytes': sum(row['bytes'] for row in rows)}))
