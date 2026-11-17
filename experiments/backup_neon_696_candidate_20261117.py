"""Public text-only reconstruction packet; no redesign merge or branch push."""
from pathlib import Path
import gzip
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
DEST = ROOT / 'experiments/neon_696_candidate_reconstruction_20261117'
COMMIT = '696ca7f1491a43b1a2267a53f8ca0f62b7c211a9'
PARENT = '00bf0f916a549f5e858cb39dd91a149071fd5181'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
git = lambda *args: subprocess.check_output(['git', *args], cwd=REVIEW)
assert git('rev-parse', 'HEAD').decode().strip() == COMMIT
names = git('diff-tree', '--no-commit-id', '--name-only', '-r', COMMIT).decode().splitlines()
assert set(names) == {'LLM.md', 'docs/REDESIGN-PORT.md', 'src/app.gd', 'tests/helper_preview_port_files.json', 'tests/wind_review_port_files.json'}
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
    if working == raw:
        recipe = {'kind': 'exact'}
    else:
        assert b'\r' not in raw and working.replace(b'\r\n', b'\n') == raw
        crlf = [j for j, line in enumerate(working.splitlines(keepends=True)) if line.endswith(b'\r\n')]
        selected = set(crlf)
        assert b''.join(line[:-1] + b'\r\n' if j in selected and line.endswith(b'\n') else line for j, line in enumerate(raw.splitlines(keepends=True))) == working
        recipe = {'kind': 'LF_blob_with_selected_CRLF_lines', 'zero_based_lines': crlf}
    filename = f'git-blobs/{i:02d}.txt.gz'
    packed = gzip.compress(raw, compresslevel=9, mtime=0)
    prepared.append((filename, packed))
    rows.append({'path': name, 'git_blob': blob, 'blob_bytes': len(raw), 'blob_sha256': sha(raw), 'payload': filename,
                 'working_sha256': sha(working), 'working_bytes': len(working), 'working_recipe': recipe})
patch = git('diff', '--binary', PARENT, COMMIT)
assert b'GIT binary patch' not in patch
patch.decode('utf-8', 'strict')
record = {'format': 'has_text_candidate_reconstruction_1', 'candidate': COMMIT, 'parent_reconstruction': {'commit': PARENT, 'packet': 'experiments/neon_00bf_candidate_reconstruction_20261117', 'main_checkpoint': 'a41a204bffb98614abfa80e0e6340078b1d719f1'},
    'tree': git('rev-parse', COMMIT + '^{tree}').decode().strip(), 'files': rows,
    'review_branch_push': 'NOT_ATTEMPTED_AFTER_PRIOR_BRANCH_REJECTION', 'main_application_merge': False,
    'scope': 'Only five changed public text files; reconstruct the explicitly published parent packet first, then and replace these committed blobs. Exact working-byte recipes preserve tested EOL identities.',
    'full_suite_pass_claimed': False, 'private_art_native_media_included': False}
metadata = (json.dumps(record, indent=2) + '\n').encode()
prepared += [('RECONSTRUCTION.json.gz', gzip.compress(metadata, compresslevel=9, mtime=0)), ('COMMIT.txt', commit), ('candidate.patch', patch)]
DEST.mkdir(exist_ok=False)
for name, raw in prepared:
    path = DEST / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
(DEST / 'README.md').write_text('This reconstructs local696ca7f from00bf0f9 using five exact public Git text blobs, patch, commit/tree identities and tested working-EOL recipes. Parent00bf is recoverable from its reconstruction packet on verified maina41a204 (and4ec). One existing camera-inspector refresh call and two exact app source-pin rows differ, plus two review notes. Original predicates remain unchanged; actual focused camera60/native5,Neon12504,controls48 pass with1029 source bytes preserved. A new complete full verifier remains required before merge. The review-branch upload was not retried; main source/evidence publication is not a product merge. Private native art/media/model arrays are excluded.\n', encoding='utf-8', newline='\n')
payloads = [{'path': p.relative_to(DEST).as_posix(), 'bytes': p.stat().st_size, 'sha256': sha(p.read_bytes())} for p in sorted(DEST.rglob('*')) if p.is_file()]
(DEST / 'INDEX.json').write_text(json.dumps({'format': 'has_source_experiment_index_1', 'files': payloads}, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({'candidate': COMMIT, 'changed_text_files': len(rows), 'packet_bytes': sum(row['bytes'] for row in payloads), 'index_sha256': sha((DEST / 'INDEX.json').read_bytes())}))
