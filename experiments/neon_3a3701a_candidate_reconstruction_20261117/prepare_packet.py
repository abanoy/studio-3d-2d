"""Read-only committed public text recovery; no product merge or branch upload."""
from pathlib import Path
import gzip
import hashlib
import json
import re
import subprocess

SOURCE = Path(__file__).resolve()
ROOT = SOURCE.parents[2] if SOURCE.parent.name == 'neon_3a3701a_candidate_reconstruction_20261117' else SOURCE.parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
DEST = ROOT / 'experiments/neon_3a3701a_candidate_reconstruction_20261117'
COMMIT = '3a3701ab6edfa81dc883759403c170b8555aab07'
PARENT = '696ca7f1491a43b1a2267a53f8ca0f62b7c211a9'
MAIN = '4fd0052f52a594e86ca77df0e50e12e8d026a874'
PARENT_PACKET = 'experiments/neon_696_candidate_reconstruction_20261117'
PARENT_INDEX = '94a74d55d78f411d3da89a31e838bdbce863b4a682697be988de9d8556bf314d'
PATHS = ('LLM.md', 'docs/REDESIGN-PORT.md', 'tests/color_sampler_smoke.gd')
TEST_WORKING_SHA = '102ec02e262644a641f6ecc43020940c33834a59b695cfdc0d2d889cc8cae781'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
oid = lambda kind, raw: hashlib.sha1(kind.encode() + b' ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def git(repo, *args):
    return subprocess.check_output(['git', '--no-optional-locks', '-c', 'core.fsmonitor=false', *args],
                                   cwd=repo, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))


cache = {}
def obj(kind, name, repo=REVIEW):
    assert kind in ('commit', 'tree', 'blob') and re.fullmatch('[0-9a-f]{40}', name)
    key = (str(repo), kind, name)
    if key not in cache:
        raw = git(repo, 'cat-file', kind, name)
        assert oid(kind, raw) == name
        cache[key] = raw
    return cache[key]


def headers(raw):
    lines = raw.split(b'\n\n', 1)[0].split(b'\n')
    tree = [line[5:].decode() for line in lines if line.startswith(b'tree ')]
    parents = [line[7:].decode() for line in lines if line.startswith(b'parent ')]
    assert len(tree) == 1 and all(re.fullmatch('[0-9a-f]{40}', value) for value in tree + parents)
    return tree[0], parents


def entries(raw):
    rows = {}; offset = 0
    while offset < len(raw):
        space = raw.index(b' ', offset); nul = raw.index(b'\0', space)
        mode = raw[offset:space]; name = raw[space + 1:nul]
        assert mode in (b'100644', b'100755', b'40000', b'120000', b'160000')
        assert name and b'/' not in name and name not in rows and nul + 21 <= len(raw)
        rows[name] = (mode, raw[nul + 1:nul + 21].hex()); offset = nul + 21
    assert offset == len(raw)
    return rows


changed = {}; new_trees = {}
def difference(old, new, prefix=''):
    if old == new:
        return
    before = entries(obj('tree', old)); after_raw = obj('tree', new); after = entries(after_raw)
    assert before.keys() == after.keys(), 'Only existing public files may change'
    new_trees[prefix] = (new, after_raw)
    for name in before:
        old_mode, old_id = before[name]; mode, new_id = after[name]
        assert mode == old_mode
        path = prefix + name.decode('utf-8', 'strict')
        if mode == b'40000':
            difference(old_id, new_id, path + '/')
        elif old_id != new_id:
            assert mode == b'100644' and path in PATHS
            changed[path] = (old_id, new_id)


# Retain the exact already-published parent packet without running its preparer.
parent_folder = ROOT / PARENT_PACKET
parent_index_raw = (parent_folder / 'INDEX.json').read_bytes()
assert sha(parent_index_raw) == PARENT_INDEX
parent_index = json.loads(parent_index_raw)
for row in [{'path': 'INDEX.json', 'bytes': len(parent_index_raw), 'sha256': PARENT_INDEX}] + parent_index['files']:
    raw = (parent_folder / row['path']).read_bytes()
    assert len(raw) == row['bytes'] and sha(raw) == row['sha256']
    assert git(ROOT, 'cat-file', 'blob', MAIN + ':' + PARENT_PACKET + '/' + row['path']) == raw
parent_record = json.loads(gzip.decompress((parent_folder / 'RECONSTRUCTION.json.gz').read_bytes()))
assert parent_record['candidate'] == PARENT
commit = obj('commit', COMMIT); tree, parents = headers(commit)
assert parents == [PARENT]
parent_commit = obj('commit', PARENT); parent_tree, unused = headers(parent_commit)
assert (parent_folder / 'COMMIT.txt').read_bytes() == parent_commit and parent_record['tree'] == parent_tree
difference(parent_tree, tree)
assert set(changed) == set(PATHS) and set(new_trees) == {'', 'docs/', 'tests/'}

prepared = []; rows = []
for i, name in enumerate(PATHS):
    previous, blob = changed[name]; raw = obj('blob', blob)
    assert b'\0' not in raw and b'\r' not in raw.replace(b'\r\n', b'')
    raw.decode('utf-8', 'strict')
    working = (REVIEW / name).read_bytes()
    if name == 'tests/color_sampler_smoke.gd':
        assert sha(working) == TEST_WORKING_SHA
    if working == raw:
        recipe = {'kind': 'exact'}
    else:
        assert b'\r' not in raw and working.replace(b'\r\n', b'\n') == raw
        crlf = [j for j, line in enumerate(working.splitlines(keepends=True)) if line.endswith(b'\r\n')]
        selected = set(crlf)
        assert b''.join(line[:-1] + b'\r\n' if j in selected and line.endswith(b'\n') else line
                        for j, line in enumerate(raw.splitlines(keepends=True))) == working
        recipe = {'kind': 'LF_blob_with_selected_CRLF_lines', 'zero_based_lines': crlf}
    payload = f'git-blobs/{i:02d}.txt.gz'
    prepared.append((payload, gzip.compress(raw, compresslevel=9, mtime=0)))
    rows.append({'path': name, 'parent_git_blob': previous, 'git_blob': blob,
                 'blob_bytes': len(raw), 'blob_sha256': sha(raw), 'payload': payload,
                 'working_bytes': len(working), 'working_sha256': sha(working), 'working_recipe': recipe})
tree_rows = []
for i, (prefix, (tree_id, raw)) in enumerate(sorted(new_trees.items())):
    payload = f'tree-objects/{i:02d}.hex'
    prepared.append((payload, (raw.hex() + '\n').encode('ascii')))
    tree_rows.append({'path': prefix or '/', 'git_tree': tree_id, 'raw_bytes': len(raw),
                      'raw_sha256': sha(raw), 'encoding': 'lowercase_hex_with_final_LF', 'payload': payload})
patch = git(REVIEW, 'diff', '--no-ext-diff', '--no-textconv', '--binary', '--no-renames', PARENT, COMMIT, '--', *PATHS)
assert b'GIT binary patch' not in patch and b'\0' not in patch
patch.decode('utf-8', 'strict')
record = {'format': 'has_text_candidate_reconstruction_1', 'candidate': COMMIT, 'tree': tree,
    'parent_reconstruction': {'commit': PARENT, 'packet': PARENT_PACKET,
        'INDEX_sha256': PARENT_INDEX, 'main_checkpoint': MAIN},
    'files': rows, 'exact_raw_changed_tree_objects': tree_rows,
    'review_branch_push': 'NOT_ATTEMPTED_AFTER_PRIOR_BRANCH_REJECTION',
    'main_application_merge': False, 'full_suite_pass_claimed': False,
    'focused_result_read_or_claimed_here': False, 'private_art_native_media_included': False,
    'scope': 'Exactly three changed public text files; parent696 is already recoverable on main4fd. The unchanged parent plus these blobs gives the candidate tree. Working EOL identities are separate from committed blob identities.'}
prepared += [('RECONSTRUCTION.json.gz', gzip.compress((json.dumps(record, indent=2) + '\n').encode(), compresslevel=9, mtime=0)),
             ('COMMIT.txt', commit), ('candidate.patch', patch),
             ('prepare_packet.py', Path(__file__).read_bytes()),
             ('README.md', b'This recovers candidate3a3701a from published parent696 using exactly three public text blobs: the pixel-center test adjustment and two review notes. Exact commit bytes, changed raw Git tree objects (hex), Git patch and working EOL recipes are retained. Parent packet bytes are verified against main4fd. App/helper/wind and every other committed path remain unchanged. This is text recovery only: no focused/full result, native fidelity, product merge, copy or cold187 is claimed. No review-branch upload was attempted.\n')]
assert len({name for name, raw in prepared}) == len(prepared)
DEST.mkdir(exist_ok=False)
for name, raw in prepared:
    path = DEST / name; path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(raw)
payloads = [{'path': name, 'bytes': len(raw), 'sha256': sha(raw)} for name, raw in sorted(prepared)]
with (DEST / 'INDEX.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump({'format': 'has_source_experiment_index_1', 'files': payloads}, stream, indent=2); stream.write('\n')
print(json.dumps({'candidate': COMMIT, 'tree': tree, 'changed_text_files': len(rows),
    'changed_raw_tree_objects': len(tree_rows), 'payloads': len(payloads),
    'packet_bytes': sum(row['bytes'] for row in payloads),
    'index_sha256': sha((DEST / 'INDEX.json').read_bytes())}))
