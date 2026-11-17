"""Read-only evidence/cache audit and narrow cleanup plan preparation; no deletion."""
from pathlib import Path
import base64
import datetime
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
COMMITS = ('1ce433bd7484e2e1652fafa5a5d2d58b0f0c1329', '09fb70ed86b5a704caba34e60be6b24e12aa68a6', 'e8cf93ce25811cbc967b1024a6d2c87ffd9cfb9a')
PROOFS = (
    ('experiments/neon_completed_checkpoint_remote_20261117/COMPLETE_READBACK.json', 'e6c89005e71a05ab7713902b60fb6f24c76049ba5ec2c3f76d4279d0d27998f2', 614454, 565, 4982585),
    ('experiments/neon_followup_checkpoint_remote_20261117/COMPLETE_READBACK.json', '5a46fd420b208954375a217ec93f40fa2e0ac3b11a3dc3ffdbff210c92478dda', 781680, 837, 6516391),
    ('experiments/neon_375_checkpoint_remote_20261117/COMPLETE_READBACK.json', 'efb5fb94aee5e143deb0cb4dff17141ba1d35c29079694fdc830f92ac5a6157c', 603000, 534, 5857844),
)
AUX = ('output/1ce-progress-memo-remote-blob.json', 'd18d50cb75f9177224630de524ed57b84cb8cad53f2631c2429e172554fb5424', 1367390)


def require(ok, message):
    if not ok: raise ValueError(message)


def sha(raw): return hashlib.sha256(raw).hexdigest()


def blob_id(raw): return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def parse(raw):
    def pairs(rows):
        result = {}
        for key, value in rows:
            require(key not in result, 'Duplicate JSON key'); result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs)


def regular(path):
    require(path.is_absolute() and path.resolve().is_relative_to(ROOT), 'ROOT path boundary')
    for item in (path, *path.parents):
        if item == ROOT.parent: break
        require(not item.is_symlink() and not getattr(item.lstat(), 'st_file_attributes', 0) & 0x400, 'Reparse refused')
    require(path.is_file(), 'Regular file required')


def read(path):
    regular(path); before = path.stat(); raw = path.read_bytes(); after = path.stat()
    require((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns), 'File changed during read')
    return raw, {'bytes': len(raw), 'sha256': sha(raw), 'mtime_ns': before.st_mtime_ns}


def git(*args):
    return subprocess.check_output(['git', '--no-optional-locks', *args], cwd=ROOT, creationflags=subprocess.CREATE_NO_WINDOW)


def decode_record(row, expected, auxiliary):
    require(row['path'] == expected['path'], 'Batch/proof ordered path')
    response = row['response']
    require(response['encoding'] == 'base64', 'Actual contents response profile')
    remote = base64.b64decode(response['content'], validate=False); method = 'contents_base64'
    if not remote and 'fallback_utf8' in row:
        require(type(row['fallback_utf8']) is str, 'Inline fallback text'); remote = row['fallback_utf8'].encode('utf-8', 'strict')
        method = 'blob_sha_utf8_contents_api_oversize_fallback'
    elif not remote and row['path'] == 'docs/progress_memo.md':
        require(auxiliary['path'] == row['path'] and auxiliary['encoding'] == 'utf-8' and auxiliary['blob_sha'] == response['sha'], 'Original auxiliary fallback identity')
        remote = auxiliary['content'].encode('utf-8', 'strict'); method = 'blob_sha_utf8_contents_api_oversize_fallback'
    require(type(expected['bytes']) is int and len(remote) == expected['bytes'] and sha(remote) == expected['sha256'], 'Decoded remote byte identity')
    require(blob_id(remote) == response['sha'] == expected['git_blob'], 'Decoded Git blob identity')
    require(expected['independent_remote_bytes_exact'] is True and expected['remote_method'] == method, 'Published remote method')
    return {'path': row['path'], 'bytes': len(remote), 'sha256': sha(remote), 'git_blob': blob_id(remote), 'remote_method': method}


def main():
    proof_rows = []; proofs = []; raw_proofs = []
    for commit, (relative, digest, size, count, total) in zip(COMMITS, PROOFS):
        raw, identity = read(ROOT / relative); require(identity['sha256'] == digest and identity['bytes'] == size, 'Proof pin')
        value = parse(raw); require(value['format'] == 'has_complete_independent_remote_readback_1' and value['commit'] == commit, 'Proof format/commit')
        require(type(value['file_count']) is int and value['file_count'] == len(value['files']) == count and value['bytes'] == sum(r['bytes'] for r in value['files']) == total, 'Exact proof totals')
        require(len({r['path'] for r in value['files']}) == count and all(r['independent_remote_bytes_exact'] is True for r in value['files']), 'Unique remote-exact proof files')
        proof_rows.append({'path': relative, **identity, 'commit': commit, 'file_count': count, 'remote_bytes': total})
        proofs.append(value); raw_proofs.append(raw)
    require(git('rev-parse', '--verify', 'HEAD').decode().strip() == COMMITS[2], 'Current main HEAD differs')
    chain = []
    for child in (1, 2):
        parent = child - 1; record = next(r for r in proofs[child]['files'] if r['path'] == PROOFS[parent][0])
        require(record['sha256'] == sha(raw_proofs[parent]) and record['bytes'] == len(raw_proofs[parent]) and record['git_blob'] == blob_id(raw_proofs[parent]), 'Published proof body chain')
        committed = git('cat-file', 'blob', COMMITS[child] + ':' + PROOFS[parent][0]); require(committed == raw_proofs[parent], 'Committed published proof bytes')
        commit_raw = git('cat-file', 'commit', COMMITS[child]); parents = [line[7:].decode() for line in commit_raw.split(b'\n\n', 1)[0].splitlines() if line.startswith(b'parent ')]
        require(parents == [COMMITS[parent]], 'Exact main commit ancestry')
        chain.append({'commit': COMMITS[child], 'sole_parent': COMMITS[parent], 'published_proof_path': PROOFS[parent][0], 'proof_blob': record['git_blob'], 'proof_sha256': record['sha256']})
    auxiliary_raw, auxiliary_identity = read(ROOT / AUX[0]); require(auxiliary_identity['sha256'] == AUX[1] and auxiliary_identity['bytes'] == AUX[2], 'Auxiliary pin')
    auxiliary = parse(auxiliary_raw)
    targets = []
    for prefix, maximum, proof, commit in [('1ce', 560, proofs[0], COMMITS[0]), ('09fb', 820, proofs[1], COMMITS[1])]:
        seen = set()
        for start in range(0, maximum + 1, 20):
            relative = f'output/{prefix}-all-remote-batch-{start:03d}.json'; raw, identity = read(ROOT / relative); batch = parse(raw)
            require(batch['format'] == 'has_independent_remote_fetch_batch_1' and batch['commit'] == commit and type(batch['start']) is int and batch['start'] == start, 'Exact batch profile')
            expected = proof['files'][start:start + 20]; require(len(batch['files']) == len(expected), 'Exact batch membership')
            records = []
            for row, expected_row in zip(batch['files'], expected, strict=True):
                require(row['path'] not in seen, 'Duplicate cached member'); seen.add(row['path'])
                records.append(decode_record(row, expected_row, auxiliary))
            targets.append({'path': relative, **identity, 'prefix': prefix, 'start': start, 'commit': commit, 'response_files': len(records), 'decoded_source_bytes': sum(r['bytes'] for r in records), 'records': records})
        require(seen == {r['path'] for r in proof['files']}, 'Complete proof coverage')
    require(len(targets) == 71 and len({r['path'] for r in targets}) == 71, 'Exact71 scope')
    tracked = git('--literal-pathspecs', 'ls-files', '-z', '--', *[r['path'] for r in targets]); require(tracked == b'', 'A target is tracked')
    for row in targets:
        unused_raw, identity = read(ROOT / row['path']); require(all(identity[k] == row[k] for k in identity), 'Cache changed during preparation')
    require(git('rev-parse', '--verify', 'HEAD').decode().strip() == COMMITS[2], 'HEAD changed during preparation')
    plan = {'format': 'has_exact_public_download_cache_cleanup_plan_1', 'preparation_only': True,
            'workspace_root': str(ROOT), 'expected_main_head': COMMITS[2], 'proofs': proof_rows, 'published_chain': chain,
            'retained_auxiliary_fallback': {'path': AUX[0], **auxiliary_identity, 'deletion_authorized': False},
            'targets': targets, 'target_files': 71, 'target_bytes': sum(r['bytes'] for r in targets),
            'target_group_counts': {'1ce': 29, '09fb': 42}, 'decoded_response_files': 1402,
            'not_in_scope': ['auxiliary fallback', 'all e8 caches', 'private/native/model/media inputs', 'review checkouts', 'installed tools', 'tracked sources', 'any other output or directory'],
            'cleanup_executed': False}
    (HERE / 'PLAN.json').write_text(json.dumps(plan, indent=2) + '\n', encoding='utf-8')
    report = {'format': 'has_cache_cleanup_read_only_preparation_observation_1', 'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'status': 'EXACT71_UNTRACKED_PUBLIC_CACHES_RECONCILED_NO_DELETION', 'targets': 71, 'bytes': plan['target_bytes'],
              'decoded_records': 1402, 'proof_chain_verified_against_local_committed_bytes': True, 'all_targets_untracked': True,
              'auxiliary_fallback_retained': AUX[0], 'fallback_scope': 'One external1ce fallback; twelve inline09fb fallbacks, including empty files',
              'Git_operations': 'Local read-only rev-parse/cat-file/ls-files only', 'cleanup_script_invoked': False,
              'delete_move_native_engine_CIM_or_active_full_reads': False, 'PLAN_sha256': sha((HERE / 'PLAN.json').read_bytes())}
    (HERE / 'PREPARATION_OBSERVATION.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
