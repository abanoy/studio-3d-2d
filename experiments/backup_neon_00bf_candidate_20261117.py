"""Public text-only reconstruction packet; no redesign merge or branch push."""
from pathlib import Path
import gzip
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
DEST = ROOT / 'experiments/neon_00bf_candidate_reconstruction_20261117'
COMMIT = '00bf0f916a549f5e858cb39dd91a149071fd5181'
PARENT = 'fe9aace86f7a349c90a951ff26d76f746d1e4701'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
git = lambda *args: subprocess.check_output(['git', *args], cwd=REVIEW)
assert git('rev-parse', 'HEAD').decode().strip() == COMMIT
names = git('diff-tree', '--no-commit-id', '--name-only', '-r', COMMIT).decode().splitlines()
assert set(names) == {'LLM.md', 'docs/REDESIGN-PORT.md', 'tests/verify_shape_catalog.py', 'tests/verify_character_height.py'}
commit = git('cat-file', 'commit', COMMIT)
assert hashlib.sha1(b'commit ' + str(len(commit)).encode() + b'\0' + commit).hexdigest() == COMMIT
assert b'parent ' + PARENT.encode() + b'\n' in commit
prepared = []
rows = []
for i, name in enumerate(names):
    raw = git('show', COMMIT + ':' + name)
    assert b'\0' not in raw
    raw.decode('utf-8', 'strict')
    blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
    assert git('rev-parse', COMMIT + ':' + name).decode().strip() == blob
    working = (REVIEW / name).read_bytes()
    assert working.replace(b'\r\n', b'\n') == raw
    crlf = [j for j, line in enumerate(working.splitlines(keepends=True)) if line.endswith(b'\r\n')]
    selected = set(crlf)
    assert b''.join(line[:-1] + b'\r\n' if j in selected and line.endswith(b'\n') else line for j, line in enumerate(raw.splitlines(keepends=True))) == working
    filename = f'git-blobs/{i:02d}.txt.gz'
    packed = gzip.compress(raw, compresslevel=9, mtime=0)
    prepared.append((filename, packed))
    rows.append({'path': name, 'git_blob': blob, 'blob_bytes': len(raw), 'blob_sha256': sha(raw), 'payload': filename,
                 'working_sha256': sha(working), 'working_bytes': len(working), 'working_recipe': {'kind': 'LF_blob_with_selected_CRLF_lines', 'zero_based_lines': crlf}})
patch = git('diff', '--binary', PARENT, COMMIT)
assert b'GIT binary patch' not in patch
patch.decode('utf-8', 'strict')
record = {'format': 'has_text_candidate_reconstruction_1', 'candidate': COMMIT, 'parent_reconstruction': {'commit': PARENT, 'packet': 'experiments/neon_fe9_candidate_reconstruction_20261117', 'main_publication': 'PENDING_WITH_THIS_INCREMENT'},
    'tree': git('rev-parse', COMMIT + '^{tree}').decode().strip(), 'files': rows,
    'review_branch_push': 'NOT_ATTEMPTED_AFTER_PRIOR_BRANCH_REJECTION', 'main_application_merge': False,
    'scope': 'Only three changed public text files; start from known remote parent and replace these committed blobs. Exact working-byte recipes preserve tested EOL identities.',
    'full_suite_pass_claimed': False, 'private_art_native_media_included': False}
metadata = (json.dumps(record, indent=2) + '\n').encode()
prepared += [('RECONSTRUCTION.json.gz', gzip.compress(metadata, compresslevel=9, mtime=0)), ('COMMIT.txt', commit), ('candidate.patch', patch)]
DEST.mkdir(exist_ok=False)
for name, raw in prepared:
    path = DEST / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
(DEST / 'README.md').write_text('This reconstructs local00bf0f9 fromfe9aace using four exact public Git text blobs, patch, commit/tree identities and tested working-EOL recipes. Parentfe9 is reconstructed from experiments/neon_fe9_candidate_reconstruction_20261117; parent375 is backed by mainE8 and its parent4ed is on the remote review branch. The review-branch upload was not attempted after the prior branch rejection. Main evidence publication does not merge or activate the redesign. Only two test fixture selectors and two review notes differ fromfe9; focused catalogue130/unit34,comparison94,height105/rawVRM9 pass, complete Windows qualification remains unfinished. Private native models/art/media/arrays are excluded.\n', encoding='utf-8', newline='\n')
payloads = [{'path': p.relative_to(DEST).as_posix(), 'bytes': p.stat().st_size, 'sha256': sha(p.read_bytes())} for p in sorted(DEST.rglob('*')) if p.is_file()]
(DEST / 'INDEX.json').write_text(json.dumps({'format': 'has_source_experiment_index_1', 'files': payloads}, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({'candidate': COMMIT, 'changed_text_files': len(rows), 'packet_bytes': sum(row['bytes'] for row in payloads), 'index_sha256': sha((DEST / 'INDEX.json').read_bytes())}))
