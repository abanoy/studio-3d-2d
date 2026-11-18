"""Verify, or later delete, eighteen exact session-owned public response caches.

Default is read-only. Deletion additionally requires the published proof's exact
Git bytes and Root's independently pinned complete remote readback reference.
No recursive operation, process control, native data or private output is used.
"""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import os
import re
import stat
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / 'output'
PLAN_SHA256 = 'd6e703b179d37c7543ac1bd35c78d5809a62fe13219a49f51d9feab88a326a6f'
PROOF_PATH = 'experiments/neon_owner_copy_source_checkpoint_remote_20261117/COMPLETE_READBACK.json'
PROOF_SHA256 = '7d3a345fb459b9396173906b00955cda5fe433d7447c1af9884e73636b4d3581'
NEW_COMMIT = 'ddc24d786228c8a66a38a21d4db61e939ca6dee8'
NAMES = ([f'9730-all-remote-batch-{start:03}.json' for start in range(0, 180, 20)]
         + [f'owner-copy-ddc24d7-complete-remote-batch-{start:03}.json' for start in range(0, 160, 20)]
         + ['owner-copy-ddc24d7-remote-batch-000.json'])
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def plain_file(path):
    path = Path(path).absolute()
    assert path.resolve().is_relative_to(ROOT) and path.is_file(), str(path)
    cursor = path
    while cursor != ROOT:
        info = cursor.lstat()
        assert not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400, str(cursor)
        cursor = cursor.parent
    info = path.stat()
    assert stat.S_ISREG(info.st_mode) and info.st_nlink == 1
    return path, info


def identity(path):
    path, before = plain_file(path)
    raw = path.read_bytes()
    after = path.stat()
    assert (before.st_size, before.st_mtime_ns, before.st_ino) == (after.st_size, after.st_mtime_ns, after.st_ino)
    return {'bytes': len(raw), 'mtime_ns': before.st_mtime_ns, 'inode': before.st_ino, 'sha256': sha(raw)}, raw


def cache_path(row):
    relative = PurePosixPath(row['path'])
    assert row['path'] == 'output/' + relative.name and relative.name in NAMES
    path = ROOT / row['path']
    assert path.parent == OUT and path.resolve().parent == OUT.resolve()
    return path


def preflight():
    _, raw = identity(HERE / 'PLAN.json')
    assert sha(raw) == PLAN_SHA256
    plan = json.loads(raw)
    assert plan['format'] == 'has_exact_public_cache_cleanup_plan_1'
    assert plan['file_count'] == len(plan['files']) == len(NAMES) == 18
    assert [row['path'] for row in plan['files']] == ['output/' + name for name in NAMES]
    assert plan['logical_bytes'] == sum(row['bytes'] for row in plan['files']) == 20347848
    assert plan['required_published_proof_path'] == PROOF_PATH and plan['required_published_proof_sha256'] == PROOF_SHA256
    for row in plan['files']:
        found, raw = identity(cache_path(row))
        assert all(found[key] == row[key] for key in found), row['path']
        doc = json.loads(raw)
        paths = [item['path'] for item in doc['files']]
        assert doc['commit'] == row['header_commit'] and type(doc['start']) is int and doc['start'] == row['header_start']
        assert len(paths) == row['header_path_count'] and sha(json.dumps(paths, ensure_ascii=True, separators=(',', ':')).encode()) == row['header_paths_sha256']
    return plan


def publication(args):
    assert args.published_commit and re.fullmatch('[0-9a-f]{40}', args.published_commit)
    assert args.root_publication_reference is not None and args.root_publication_reference_sha256
    assert re.fullmatch('[0-9a-f]{64}', args.root_publication_reference_sha256)
    reference_path, _ = plain_file(args.root_publication_reference)
    assert reference_path.stat().st_size <= 16 * 1024 * 1024
    reference_raw = reference_path.read_bytes()
    assert sha(reference_raw) == args.root_publication_reference_sha256
    reference = json.loads(reference_raw)
    assert reference['format'] == 'has_complete_independent_remote_readback_1' and reference['commit'] == args.published_commit
    rows = reference['files']
    assert reference['file_count'] == len(rows) and len(rows) == len({row['path'] for row in rows})
    assert all(row['independent_remote_bytes_exact'] is True for row in rows)
    proof_rows = [row for row in rows if row['path'] == PROOF_PATH]
    assert len(proof_rows) == 1 and proof_rows[0]['sha256'] == PROOF_SHA256
    committed = subprocess.check_output(['git', 'cat-file', 'blob', args.published_commit + ':' + PROOF_PATH], cwd=ROOT)
    assert sha(committed) == PROOF_SHA256
    assert hashlib.sha1(b'blob ' + str(len(committed)).encode() + b'\0' + committed).hexdigest() == proof_rows[0]['git_blob']
    proof = json.loads(committed)
    assert proof['commit'] == NEW_COMMIT and proof['file_count'] == 151
    return {'published_commit': args.published_commit, 'proof_sha256': PROOF_SHA256,
            'Root_reference': reference_path.relative_to(ROOT).as_posix(),
            'Root_reference_sha256': args.root_publication_reference_sha256}


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--delete', action='store_true')
parser.add_argument('--published-commit')
parser.add_argument('--root-publication-reference', type=Path)
parser.add_argument('--root-publication-reference-sha256')
args = parser.parse_args()
plan = preflight()
if not args.delete:
    print(json.dumps({'mode': 'VERIFY_ONLY', 'files': 18, 'logical_bytes': plan['logical_bytes'], 'deleted': False}))
    raise SystemExit(0)
published = publication(args)
journal = OUT / 'neon-public-cache-cleanup-20261118-journal.jsonl'
assert journal.parent.resolve() == OUT.resolve() and not os.path.lexists(journal)
deleted = 0
deleted_bytes = 0
with journal.open('x', encoding='utf-8', newline='\n') as stream:
    def record(value):
        stream.write(json.dumps(value, sort_keys=True) + '\n')
        stream.flush()
        os.fsync(stream.fileno())
    record({'stage': 'started', 'plan_sha256': PLAN_SHA256, 'file_count': 18, 'publication': published})
    for row in plan['files']:
        try:
            path = cache_path(row)
            found, _ = identity(path)
            assert all(found[key] == row[key] for key in found), row['path']
            record({'stage': 'deleting', 'path': row['path'], 'bytes': row['bytes'], 'sha256': row['sha256']})
            path.unlink()
            assert not os.path.lexists(path)
            deleted += 1
            deleted_bytes += row['bytes']
            record({'stage': 'deleted', 'path': row['path'], 'bytes': row['bytes'], 'sha256': row['sha256']})
        except BaseException as error:
            record({'stage': 'failure', 'path': row['path'], 'error_type': type(error).__name__,
                    'error': str(error), 'deleted_files_before_failure': deleted,
                    'deleted_bytes_before_failure': deleted_bytes, 'other_files_left_untouched': True})
            raise
    assert deleted == 18 and deleted_bytes == plan['logical_bytes']
    record({'stage': 'complete', 'deleted_files': deleted, 'deleted_logical_bytes': deleted_bytes})
print(json.dumps({'mode': 'DELETED', 'files': deleted, 'logical_bytes': deleted_bytes, 'journal': str(journal)}))
