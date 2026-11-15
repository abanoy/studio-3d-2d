"""Read-only exact raw-Git proof. Never writes/removes any source or Git data."""
from pathlib import Path, PurePosixPath
import argparse, gzip, hashlib, json, re, subprocess

REVISION = 'e9cc7cfb20266b4863bde134bcb30457547a343d'
PACKET_SHA = '847609fa241f70f89c711a93ed0035a8a1fe69cf34bd998b9d418630db1cb70a'
GZIP_SHA = 'c772ec391c36db95b8a016125e41bc1588cdbc14ae542d6a64e66d66136f55a4'
PLAN_SHA = 'e65b408acdf63eade874709b6dc37de43b6c244ff3f9fe5fc11cab222c43fa8a'
ROOT = Path(r'C:\a\Programming\cloudflare\has-acceptance-session-20261111')
PLAN = ROOT / 'output/sfm-v2-code-cleanup-plan-20261113'
EXECUTOR = ROOT / 'output/sfm-v2-code-cleanup-executor-20261113'

def require(ok, message):
    if not ok:
        raise ValueError(message)

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def git(*args, input=None):
    return subprocess.check_output(['git', *args], cwd=ROOT, input=input, stderr=subprocess.PIPE)

def ancestor(older, newer):
    result = subprocess.run(['git', 'merge-base', '--is-ancestor', older, newer], cwd=ROOT, capture_output=True)
    require(result.returncode == 0, 'Required commit ancestry unavailable: ' + older + ' -> ' + newer)

def prefix(value):
    parts = PurePosixPath(value).parts
    require(bool(parts) and not value.startswith('/') and '\\' not in value and ':' not in value
            and all(x not in ('', '.', '..') for x in value.split('/')), 'Unsafe published Git prefix')
    return value

def verify_local():
    packet = (PLAN/'PACKET.json').read_bytes()
    packed = (PLAN/'PLAN.json.gz').read_bytes()
    raw = (PLAN/'PLAN.json').read_bytes()
    require(digest(packet) == PACKET_SHA and digest(packed) == GZIP_SHA and digest(raw) == PLAN_SHA,
            'Frozen packet/gzip/raw plan changed')
    require(len(raw) == 7532146 and gzip.decompress(packed) == raw, 'Plan compression identity failed')
    p = json.loads(raw)
    require(p['format'] == 'has_four_v2_git_code_cleanup_plan_1' and p['historical_source_commit'] == REVISION,
            'Unexpected plan schema/revision')
    candidates = [x for project in p['projects'] for x in project['candidate_files']]
    retained = [x for project in p['projects'] for x in project['retained_files']]
    require((len(p['projects']), len(candidates), sum(x['bytes'] for x in candidates), len(retained), sum(x['bytes'] for x in retained))
            == (4, 4308, 33607832, 2613, 68376831), 'Frozen counts changed')
    tree = {}
    for record in git('ls-tree', '-rz', '--full-tree', REVISION).split(b'\0'):
        if record:
            meta, name = record.split(b'\t', 1)
            tree[name.decode('utf-8')] = tuple(x.decode('ascii') for x in meta.split())
    objects = sorted({x['git_oid'] for x in candidates})
    require(all(re.fullmatch('[a-f0-9]{40}', x) for x in objects), 'Invalid raw blob OID')
    batch = git('cat-file', '--batch', input=''.join(x+'\n' for x in objects).encode('ascii'))
    blobs, offset = {}, 0
    for oid in objects:
        end = batch.index(b'\n', offset)
        actual, kind, size = batch[offset:end].split()
        require(actual.decode() == oid and kind == b'blob', 'Raw Git batch response mismatch')
        size = int(size)
        start, finish = end+1, end+1+size
        data = batch[start:finish]
        require(len(data) == size and batch[finish:finish+1] == b'\n', 'Truncated raw blob')
        blobs[oid] = (size, digest(data))
        offset = finish+1
    require(offset == len(batch), 'Unexpected trailing raw blob data')
    for project in p['projects']:
        manifest = json.loads(Path(project['original_manifest']['path']).read_bytes())
        require(manifest['root_revision'] == REVISION and manifest['source_mode'] == 'exact_git_revision'
                and manifest['copied_source_is_exact_git_revision'] is True, 'Historical source context differs')
        source = manifest['projects'][project['mode']]
        require(source['path'].casefold() == project['source_root'].casefold(), 'Historical manifest root differs')
        for entry in project['candidate_files']:
            require(entry['git_commit'] == REVISION and entry['git_path'] == entry['relative_path'], 'Candidate revision/path mismatch')
            require(tree.get(entry['git_path']) == (entry['git_mode'], 'blob', entry['git_oid'])
                    and entry['git_mode'] in ('100644', '100755'), 'Raw Git path/mode/OID mismatch')
            require(blobs[entry['git_oid']] == (entry['bytes'], entry['sha256']), 'Raw Git blob bytes/hash mismatch')
            require(source['files'].get(entry['relative_path']) == entry['sha256'] == entry['original_manifest_sha256'],
                    'Original manifest hash mismatch')
    return {'format':'has_sfm_v2_readonly_git_proof_1', 'passed':True, 'raw_plan_sha256':PLAN_SHA,
            'packet_sha256':PACKET_SHA, 'gzip_sha256':GZIP_SHA, 'historical_revision':REVISION,
            'candidate_files':len(candidates), 'candidate_bytes':sum(x['bytes'] for x in candidates),
            'raw_git_objects':len(objects), 'eol_conversion_used':False,
            'publication_status':'UNRUN_LOCAL_PROOF_ONLY', 'git_or_source_mutation':False}

def verify_publication(options, proof):
    require(re.fullmatch('[a-f0-9]{40}', options.checkpoint or ''), 'Exact published checkpoint required')
    require(re.fullmatch('[a-f0-9]{64}', options.executor_sha or '') and re.fullmatch('[a-f0-9]{64}', options.helper_sha or ''),
            'Exact independently reviewed executor/helper SHA gates required')
    plan_prefix, executor_prefix = prefix(options.plan_prefix), prefix(options.executor_prefix)
    require(git('rev-parse', options.checkpoint+'^{commit}').decode().strip() == options.checkpoint, 'Checkpoint missing locally')
    ancestor(REVISION, options.checkpoint)
    remote = git('ls-remote', '--exit-code', 'origin', 'refs/heads/main').decode('ascii').strip().split()
    require(len(remote) == 2 and re.fullmatch('[a-f0-9]{40}', remote[0]) and remote[1] == 'refs/heads/main', 'Remote main could not be verified')
    # A later remote tip must already be present locally. This helper never fetches.
    ancestor(options.checkpoint, remote[0])
    for local, git_path, expected in [
        (PLAN/'PACKET.json', plan_prefix+'/PACKET.json', PACKET_SHA),
        (PLAN/'PLAN.json.gz', plan_prefix+'/PLAN.json.gz', GZIP_SHA),
        (EXECUTOR/'execute-sfm-v2-cleanup.ps1', executor_prefix+'/execute-sfm-v2-cleanup.ps1', options.executor_sha),
        (EXECUTOR/'verify-git.py', executor_prefix+'/verify-git.py', options.helper_sha),
    ]:
        data = git('cat-file', 'blob', options.checkpoint+':'+git_path)
        require(digest(data) == expected and data == local.read_bytes(), 'Published artifact differs: '+git_path)
    proof.update(publication_status='REMOTE_MAIN_REACHABLE_EXACT_ARTIFACTS_VERIFIED',
                 checkpoint=options.checkpoint, remote_main_at_check=remote[0],
                 plan_git_prefix=plan_prefix, executor_git_prefix=executor_prefix,
                 executor_sha256=options.executor_sha, helper_sha256=options.helper_sha)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint')
    parser.add_argument('--plan-prefix')
    parser.add_argument('--executor-prefix')
    parser.add_argument('--executor-sha')
    parser.add_argument('--helper-sha')
    options = parser.parse_args()
    proof = verify_local()
    if any(vars(options).values()):
        verify_publication(options, proof)
    print(json.dumps(proof, indent=2))

if __name__ == '__main__':
    main()
