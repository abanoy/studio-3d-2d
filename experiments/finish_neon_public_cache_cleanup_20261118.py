"""Remove two verified followup response caches and record the completed cleanup."""
from pathlib import Path
import base64
import hashlib
import json
import os
import stat

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output'
COMMIT = '05649446a1fc851623a92a82d8ac7d8b8e06834f'
PROOF = ROOT / 'experiments/neon_post_copy_source_checkpoint_remote_20261118/COMPLETE_READBACK.json'
PROOF_SHA = '20930aaca71ac115a7d43dee1b98e40a194504978045d9d9de40b7ff49f27e87'
NAMES = ['post-copy-0564944-remote-batch-000.json', 'post-copy-0564944-remote-batch-020.json']
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def plain(path):
    assert path.is_file() and path.resolve().is_relative_to(ROOT.resolve())
    cursor = path
    while cursor != ROOT:
        info = cursor.lstat()
        assert not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400
        cursor = cursor.parent
    assert path.stat().st_nlink == 1


def identity(path):
    plain(path)
    before = path.stat(); raw = path.read_bytes(); after = path.stat()
    assert (before.st_size, before.st_ino, before.st_mtime_ns) == (after.st_size, after.st_ino, after.st_mtime_ns)
    return raw, {'path': path.relative_to(ROOT).as_posix(), 'bytes': len(raw),
                 'sha256': sha(raw), 'mtime_ns': before.st_mtime_ns, 'inode': before.st_ino}


proof_raw, _ = identity(PROOF)
assert sha(proof_raw) == PROOF_SHA
proof = json.loads(proof_raw)
assert proof['commit'] == COMMIT and proof['file_count'] == proof['changed_file_count'] == 27
assert all(row['independent_remote_bytes_exact'] is True for row in proof['files'])
expected = {row['path']: row for row in proof['files']}
old_journal = OUT / 'neon-public-cache-cleanup-20261118-journal.jsonl'
old_raw, _ = identity(old_journal)
old_rows = [json.loads(line) for line in old_raw.splitlines()]
assert old_rows[-1] == {'stage': 'complete', 'deleted_files': 18, 'deleted_logical_bytes': 20347848}
old_deleted = [row for row in old_rows if row['stage'] == 'deleted']
assert len(old_deleted) == 18 and len({row['path'] for row in old_deleted}) == 18
plan_raw, _ = identity(ROOT / 'experiments/neon_public_cache_cleanup_20261118/PLAN.json')
assert sha(plan_raw) == 'd6e703b179d37c7543ac1bd35c78d5809a62fe13219a49f51d9feab88a326a6f'
plan = json.loads(plan_raw)
assert [(row['path'], row['bytes'], row['sha256']) for row in old_deleted] == [
    (row['path'], row['bytes'], row['sha256']) for row in plan['files']]
assert all((ROOT / row['path']).parent == OUT and not os.path.lexists(ROOT / row['path']) for row in old_deleted)
prepared = []
for start, name in zip((0, 20), NAMES):
    path = OUT / name
    assert path.parent == OUT and path.resolve().parent == OUT.resolve()
    raw, descriptor = identity(path)
    batch = json.loads(raw)
    assert batch['commit'] == COMMIT and batch['start'] == start
    assert [row['path'] for row in batch['files']] == [row['path'] for row in proof['files'][start:start + 20]]
    for row in batch['files']:
        response = row['response']; assert response['encoding'] == 'base64'
        remote = base64.b64decode(response['content'])
        if not remote and 'fallback_utf8' in row:
            remote = row['fallback_utf8'].encode()
        wanted = expected[row['path']]
        assert len(remote) == wanted['bytes'] and sha(remote) == wanted['sha256']
        assert hashlib.sha1(b'blob ' + str(len(remote)).encode() + b'\0' + remote).hexdigest() == response['sha'] == wanted['git_blob']
    prepared.append((path, descriptor))

journal = OUT / 'neon-post-readback-cache-pair-cleanup-20261118.jsonl'
assert not os.path.lexists(journal)
result = ROOT / 'experiments/neon_public_cache_cleanup_completion_20261118/RESULT.json'
assert not result.parent.exists()
with journal.open('x', encoding='utf-8', newline='\n') as stream:
    def record(row):
        stream.write(json.dumps(row, sort_keys=True) + '\n'); stream.flush(); os.fsync(stream.fileno())
    record({'stage': 'prepared', 'proof_commit': COMMIT, 'proof_sha256': PROOF_SHA,
            'files': [row for _, row in prepared]})
    for path, descriptor in prepared:
        _, current = identity(path); assert current == descriptor
        record({'stage': 'deleting', **descriptor})
        path.unlink(); assert not os.path.lexists(path)
        record({'stage': 'deleted', **descriptor})
    record({'stage': 'complete', 'files': 2, 'logical_bytes': sum(row['bytes'] for _, row in prepared)})
result.parent.mkdir()
pair_raw = journal.read_bytes()
value = {
    'format': 'has_verified_public_response_cache_cleanup_completion_1', 'status': 'PASSED',
    'published_proof_commit': COMMIT, 'independent_27_file_readback_sha256': PROOF_SHA,
    'reviewed_18_file_plan': 'experiments/neon_public_cache_cleanup_20261118/PLAN.json',
    'reviewed_18_file_plan_sha256': 'd6e703b179d37c7543ac1bd35c78d5809a62fe13219a49f51d9feab88a326a6f',
    'reviewed_cache_files_removed': 18, 'reviewed_logical_bytes_removed': 20347848,
    'reviewed_deletion_journal_sha256': sha(old_raw),
    'followup_verified_cache_pair': [row for _, row in prepared],
    'followup_deletion_journal_sha256': sha(pair_raw),
    'total_files_removed': 20, 'total_logical_bytes_removed': 20347848 + sum(row['bytes'] for _, row in prepared),
    'all_removed_files_are_verified_public_GitHub_response_caches': True,
    'recursive_operations': False, 'originals_reviews_private_native_outputs_or_runtimes_touched': False,
    'cold_attempts_overall': ['INCOMPLETE_NOT_PASS', 'INCOMPLETE_NOT_PASS'],
    'native_B_ownership_execution': 'UNRUN', 'human_acceptance': 'DEFERRED',
}
with result.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(value, stream, indent=2); stream.write('\n')
print(json.dumps({'removed_files': 20, 'removed_logical_bytes': value['total_logical_bytes_removed'],
                  'result_sha256': sha(result.read_bytes())}))
