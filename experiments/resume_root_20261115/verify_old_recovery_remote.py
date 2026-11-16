"""Exact bounded readback of the old public packet and two source snapshots.

Only root may execute after publication A. No cleanup, restore, installation or
Git mutation occurs. Payloads remain in memory; the output contains hashes only.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path, PurePosixPath
import argparse
import collections
import datetime
import gzip
import hashlib
import io
import json
import re
import stat
import subprocess
import time
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
RAW = 'https://raw.githubusercontent.com/abanoy/studio-3d-2d/'
OLD_COMMIT = '8d4fde001258f501602bd94bd80d925683062f15'
PLAN_PATH = 'experiments/resume_root_20261115/old_native_recovery_plan.json'
PLAN_SHA = '194ccde44c5d78f20832c7837b5d61ac4de8557524c69c9c3d87a2c24e9b29c5'
PACKET = 'experiments/source_appearance/main_native_app_actual_20261113/'
INDEX_PATH = PACKET + 'INDEX.json'
INDEX_SHA = '4be9c24cbd516bd18c161b6450034244f02fddbccdcb31e516132118e452444b'
AUDIT = 'experiments/resume_archive_20261115/historical-cleanup-audit/'
RECOVERY_PATH = AUDIT + 'GIT_RECOVERY_BATCH_PROOF.json.gz'
RECOVERY_RAW_SHA = '0bce42ead2142ea1c49ce6655e0c9e0dcca5e3fc02133b6aadd538c93cf456bc'
INVENTORIES = {
    'core14': (AUDIT + 'core14-fresh-inventory.json.gz',
               '846d0015644af0b8fca2eebed64c247dc6cee3a95c03240133ccd0c70fd9f20c',
               '1794615194930984000-ae0e0967', 4707, 1699274),
    'wider11': (AUDIT + 'wider11-fresh-inventory.json.gz',
                '0d5fbd84a774958d53ac6d7f8f1065e319b0d6c8e1ab413a73febf31b73dee29',
                '1794615438168999800-42f0686d', 4600, 1659153)}
PUBLIC_FIXTURES = frozenset({
    'examples/room.glb', 'examples/tutorials/Practice cue.wav',
    'examples/tutorials/Practice figure.glb', 'examples/tutorials/Practice room.glb',
    'examples/tutorials/first-movie.has', 'examples/tutorials/practice.has'})
SOURCE_SUFFIXES = {'.gd', '.py', '.json', '.gdshader', '.Dockerfile', '.tscn',
                   '.godot', '.patch', '.desktop'}
PACKET_SUFFIXES = {'.json', '.log', '.py', '.gz', '.gd', '.md', '.godot'}
MAX_FILE = 8 * 1024 * 1024
MAX_TOTAL = 32 * 1024 * 1024


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def blob_oid(raw):
    return hashlib.sha1(b'blob ' + str(len(raw)).encode('ascii') + b'\0' + raw).hexdigest()


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def safe_path(name):
    assert isinstance(name, str) and name and not any(c in name for c in '\\\r\n\0:')
    path = PurePosixPath(name)
    assert not path.is_absolute() and path.as_posix() == name
    assert all(part not in ('', '.', '..') and part == part.rstrip(' .') for part in path.parts)
    assert not any(ord(c) < 32 for c in name)
    return path


def source_path(name):
    path = safe_path(name)
    assert name in ('main.tscn', 'project.godot', 'run.py') or path.parts[0] in ('data', 'examples', 'src', 'tests', 'tools')
    if name not in PUBLIC_FIXTURES:
        assert path.suffix in SOURCE_SUFFIXES or name == 'tests/blank'
    return path


def packet_path(name):
    path = safe_path(name)
    assert name.startswith(PACKET) and len(path.parts) > len(PurePosixPath(PACKET).parts)
    assert path.suffix in PACKET_SUFFIXES
    return path


def ungzip(raw, maximum=MAX_FILE):
    assert len(raw) <= MAX_FILE
    with gzip.GzipFile(fileobj=io.BytesIO(raw), mode='rb') as stream:
        result = stream.read(maximum + 1)
    assert len(result) <= maximum
    return result


def restore_source(raw, row):
    """Return only the exact source bytes admitted by the frozen recovery map."""
    source_path(row['git_path'])
    assert len(raw) <= MAX_FILE and blob_oid(raw) == row['git_blob_oid']
    recipe = row['reconstruction']
    if recipe == 'exact_git_blob':
        restored = raw
        assert 'crlf_newline_ordinals' not in row
    else:
        assert b'\x00' not in raw and b'\r' not in raw
        raw.decode('utf-8', errors='strict')
        if recipe == 'git_blob_LF_to_CRLF':
            assert 'crlf_newline_ordinals' not in row
            restored = raw.replace(b'\n', b'\r\n')
        else:
            assert recipe == 'git_blob_selected_LF_to_CRLF'
            ordinals = row['crlf_newline_ordinals']
            assert isinstance(ordinals, list) and ordinals == sorted(set(ordinals))
            chunks = raw.split(b'\n')
            assert all(type(i) is int and 0 <= i < len(chunks) - 1 for i in ordinals)
            chosen = set(ordinals)
            restored = b''.join(chunk + (b'\r\n' if i in chosen else b'\n')
                                for i, chunk in enumerate(chunks[:-1])) + chunks[-1]
    assert len(restored) == row['restored_bytes'] and sha(restored) == row['restored_sha256']
    return restored


def verify_metadata(raw, row, inventories):
    assert len(raw) == row['public_bytes'] and sha(raw) == row['public_sha256']
    assert row['reconstruction'] in ('exact', 'gzip_decompress')
    restored = ungzip(raw) if row['reconstruction'] == 'gzip_decompress' else raw
    assert len(restored) == row['restored_bytes'] and sha(restored) == row['restored_sha256']
    target = inventories[row['phase']][row['restore_relative_path']]
    assert target['bytes'] == len(restored) and target['sha256'] == sha(restored)
    return {'phase': row['phase'], 'restore_relative_path': row['restore_relative_path'],
            'reconstruction': row['reconstruction'], 'restored_bytes': len(restored),
            'restored_sha256': sha(restored), 'exact_inventory_match': True}


def validate_plan(plan, proof, inventories, index):
    assert plan['public506_packet']['index_path'] == INDEX_PATH
    assert plan['public506_packet']['index_sha256'] == INDEX_SHA
    assert len(index['files']) == 506 and len({row['path'] for row in index['files']}) == 506
    assert sum(row['bytes'] for row in index['files']) == plan['public506_packet']['payload_bytes'] == 5819299
    public = {}
    for row in index['files']:
        safe_path(row['path'])
        name = PACKET + row['path']
        packet_path(name)
        assert 0 <= row['bytes'] <= MAX_FILE and re.fullmatch('[0-9a-f]{64}', row['sha256'])
        public[name] = row
    assert proof['all_checks_passed'] and proof['snapshot_code_files_checked'] == 1962
    joins = proof['candidate_joins']
    assert len(joins) == 2 and {row['phase'] for row in joins} == set(INVENTORIES)
    code_maps = [row['code_recovery'] for row in joins]
    assert code_maps[0] == code_maps[1] and len(code_maps[0]) == 981
    source = plan['snapshot_recovery']['source_files']
    assert len(source) == 981 and len({row['git_path'] for row in source}) == 981
    source_by_name = {row['git_path']: row for row in source}
    fixture_names = set()
    for original in code_maps[0]:
        assert original['path'].startswith('Studio/')
        name = original['path'][7:]
        source_path(name)
        row = source_by_name[name]
        assert row['historical_commit'] == OLD_COMMIT
        assert row['restore_relative_path'] == original['path']
        assert row['git_blob_oid'] == original['git_blob_oid']
        assert row['restored_sha256'] == original['original_sha256']
        assert row['reconstruction'] == original['recovery']
        assert row.get('crlf_newline_ordinals') == original.get('crlf_newline_ordinals')
        assert row['public_builtin_fixture'] is (name in PUBLIC_FIXTURES)
        assert 0 <= row['restored_bytes'] <= MAX_FILE
        for phase in INVENTORIES:
            pin = inventories[phase][row['restore_relative_path']]
            assert pin['bytes'] == row['restored_bytes'] and pin['sha256'] == row['restored_sha256']
        if name in PUBLIC_FIXTURES:
            assert row['reconstruction'] == 'exact_git_blob'
            fixture_names.add(name)
    assert fixture_names == PUBLIC_FIXTURES
    assert sum(row['restored_bytes'] for row in source if row['git_path'] in PUBLIC_FIXTURES) == 175666
    assert sum(row['restored_bytes'] for row in source) == 7117526
    assert collections.Counter(row['reconstruction'] for row in source) == {
        'exact_git_blob': 196, 'git_blob_LF_to_CRLF': 783, 'git_blob_selected_LF_to_CRLF': 2}
    metadata = plan['metadata_recovery']['joins']
    assert len(metadata) == 44
    actual_joins = {(join['phase'], item['candidate']): item
                    for join in joins for item in join['metadata_joins']}
    assert len(actual_joins) == 44
    for row in metadata:
        previous = actual_joins[(row['phase'], row['restore_relative_path'])]
        assert row['public_path_at_commitA'] == previous['git_path']
        assert row['restored_sha256'] == previous['sha256'] and previous['equal']
        assert row['historical_git_blob_oid'] == previous['git_blob_oid']
        assert row['reconstruction'] == ('gzip_decompress' if previous['gzip_recovered'] else 'exact')
        indexed = public[row['public_path_at_commitA']]
        assert row['public_bytes'] == indexed['bytes'] and row['public_sha256'] == indexed['sha256']
    return public, source, metadata


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, timeout=60,
                                   creationflags=subprocess.CREATE_NO_WINDOW)


def tree(commit, prefixes):
    raw = git('ls-tree', '-rlz', '--full-tree', commit, '--', *prefixes)
    assert len(raw) <= MAX_FILE
    result = {}
    for item in raw.split(b'\0'):
        if not item:
            continue
        header, name_raw = item.split(b'\t', 1)
        mode, kind, oid, size = header.split()
        name = name_raw.decode('utf-8')
        safe_path(name)
        assert mode in (b'100644', b'100755') and kind == b'blob'
        assert re.fullmatch(b'[0-9a-f]{40}', oid)
        number = int(size)
        assert 0 <= number <= MAX_FILE and name not in result
        result[name] = {'git_blob_oid': oid.decode('ascii'), 'bytes': number}
    return result


class GitBatch:
    def __init__(self):
        self.process = subprocess.Popen(['git', 'cat-file', '--batch'], cwd=ROOT,
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        creationflags=subprocess.CREATE_NO_WINDOW)

    def read(self, pin):
        oid = pin['git_blob_oid']
        assert re.fullmatch('[0-9a-f]{40}', oid) and 0 <= pin['bytes'] <= MAX_FILE
        self.process.stdin.write((oid + '\n').encode('ascii'))
        self.process.stdin.flush()
        header = self.process.stdout.readline(200).decode('ascii').strip().split()
        assert header == [oid, 'blob', str(pin['bytes'])]
        raw = self.process.stdout.read(pin['bytes'])
        assert len(raw) == pin['bytes'] and self.process.stdout.read(1) == b'\n'
        assert blob_oid(raw) == oid
        return raw

    def close(self):
        self.process.stdin.close()
        code = self.process.wait(timeout=10)
        assert code == 0 and not self.process.stderr.read(MAX_FILE + 1)


def fetch_raw(commit, name, pin):
    safe_path(name)
    assert re.fullmatch('[0-9a-f]{40}', commit)
    url = RAW + commit + '/' + urllib.parse.quote(name, safe='/')
    errors = []
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'HAS-Exact-Old-Recovery-Verification'})
            with urllib.request.urlopen(request, timeout=20) as response:
                assert response.status == 200
                raw = response.read(pin['bytes'] + 1)
            assert len(raw) == pin['bytes'] and sha(raw) == pin['sha256']
            assert blob_oid(raw) == pin['git_blob_oid']
            return raw, attempt + 1
        except Exception as exc:
            errors.append(type(exc).__name__ + ': ' + str(exc))
            if attempt < 2:
                time.sleep(1)
    raise RuntimeError('; '.join(errors))


def guarded_output(path):
    output = path.absolute()
    assert output.parent == ROOT / 'output' and output.suffix == '.json' and not output.exists()
    for current in (output.parent, *output.parent.parents):
        info = current.lstat()
        assert not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400
    assert output.resolve() == output
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publication-commit', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    output = guarded_output(args.output)
    assert re.fullmatch('[0-9a-f]{40}', args.publication_commit)
    publication = args.publication_commit
    started = time.monotonic()
    value = {'format': 'has_exact_old_native_recovery_remote_readback_1', 'passed': False,
             'started_utc': utc(), 'publication_commit': publication, 'source_commit': OLD_COMMIT,
             'checker_sha256': sha(Path(__file__).read_bytes()),
             'read_only_Git_operations': True, 'Git_mutation': False, 'cleanup_authorized': False,
             'art_policy': 'Only six literal public built-in fixtures; no owner/native source-art retrieval.',
             'maximum_workers': 8, 'socket_timeout_seconds': 20, 'attempts_per_file': 3,
             'maximum_file_bytes': MAX_FILE, 'maximum_total_local_payload_bytes': MAX_TOTAL,
             'prerequisites': [], 'remote_files': [], 'errors': []}
    batch = None
    try:
        remote = git('ls-remote', 'origin', 'refs/heads/main').decode('ascii').split()
        assert remote == [publication, 'refs/heads/main']
        value['origin_main_exact_at_start'] = True
        prerequisite_paths = [PLAN_PATH, INDEX_PATH, RECOVERY_PATH] + [row[0] for row in INVENTORIES.values()]
        pub_tree = tree(publication, [PLAN_PATH, PACKET, RECOVERY_PATH] + [row[0] for row in INVENTORIES.values()])
        assert all(name in pub_tree for name in prerequisite_paths)
        batch = GitBatch()
        prerequisite_raw = {}
        for name in prerequisite_paths:
            local = batch.read(pub_tree[name])
            pin = {**pub_tree[name], 'sha256': sha(local)}
            remote_raw, attempts = fetch_raw(publication, name, pin)
            assert remote_raw == local
            prerequisite_raw[name] = remote_raw
            value['prerequisites'].append({'path': name, **pin, 'attempts': attempts, 'remote_bytes_equal': True})
        assert sha(prerequisite_raw[PLAN_PATH]) == PLAN_SHA
        assert sha(prerequisite_raw[INDEX_PATH]) == INDEX_SHA
        plan = json.loads(prerequisite_raw[PLAN_PATH])
        index = json.loads(prerequisite_raw[INDEX_PATH])
        proof_raw = ungzip(prerequisite_raw[RECOVERY_PATH])
        assert sha(proof_raw) == RECOVERY_RAW_SHA
        proof = json.loads(proof_raw)
        inventories = {}
        for phase, (name, expected_sha, basename, count, raw_size) in INVENTORIES.items():
            raw = ungzip(prerequisite_raw[name])
            assert sha(raw) == expected_sha and len(raw) == raw_size
            parsed = json.loads(raw)
            expected_root = ROOT / 'output/source-choices-native' / basename
            assert Path(parsed['absolute_root']) == expected_root and len(parsed['files']) == count
            inventories[phase] = {row['path']: row for row in parsed['files']}
            assert len(inventories[phase]) == count
        public, sources, metadata = validate_plan(plan, proof, inventories, index)
        assert {name for name in pub_tree if name.startswith(PACKET)} == set(public) | {INDEX_PATH}
        old_tree = tree(OLD_COMMIT, ['data', 'examples', 'main.tscn', 'project.godot', 'run.py', 'src', 'tests', 'tools'])
        metadata_by_path = collections.defaultdict(list)
        for row in metadata:
            metadata_by_path[row['public_path_at_commitA']].append(row)
        jobs = []
        for name, row in sorted(public.items()):
            pin = pub_tree[name]
            assert pin['bytes'] == row['bytes']
            local = batch.read(pin)
            assert sha(local) == row['sha256']
            for join in metadata_by_path[name]:
                verify_metadata(local, join, inventories)
            jobs.append({'kind': 'public_packet', 'commit': publication, 'path': name,
                         'pin': {**pin, 'sha256': row['sha256']}})
        for row in sources:
            name = row['git_path']
            assert name in old_tree and old_tree[name]['git_blob_oid'] == row['git_blob_oid']
            pin = old_tree[name]
            assert pin['bytes'] <= row['restored_bytes']
            local = batch.read(pin)
            restored = restore_source(local, row)
            assert all(inventories[phase][row['restore_relative_path']]['sha256'] == sha(restored)
                       for phase in INVENTORIES)
            jobs.append({'kind': 'historical_source', 'commit': OLD_COMMIT, 'path': name,
                         'pin': {**pin, 'sha256': sha(local)}, 'restore': row})
        assert len(jobs) == 1487 and len({(row['commit'], row['path']) for row in jobs}) == 1487
        total = sum(job['pin']['bytes'] for job in jobs) + sum(row['bytes'] for row in value['prerequisites'])
        assert total <= MAX_TOTAL
        value['expected_remote_payload_bytes'] = total
        batch.close()
        batch = None

        def execute(job):
            pin = job['pin']
            row = {'kind': job['kind'], 'commit': job['commit'], 'path': job['path'], **pin,
                   'remote_bytes_equal': False}
            try:
                raw, attempts = fetch_raw(job['commit'], job['path'], pin)
                row.update(attempts=attempts, remote_bytes_equal=True, git_blob_oid_recomputed_equal=True)
                if job['kind'] == 'historical_source':
                    source = job['restore']
                    restored = restore_source(raw, source)
                    assert all(inventories[phase][source['restore_relative_path']]['bytes'] == len(restored) and
                               inventories[phase][source['restore_relative_path']]['sha256'] == sha(restored)
                               for phase in INVENTORIES)
                    row.update(reconstruction=source['reconstruction'], restored_bytes=len(restored),
                               restored_sha256=sha(restored), snapshot_restorations_verified=2,
                               public_builtin_fixture=source['public_builtin_fixture'])
                    if 'crlf_newline_ordinals' in source:
                        row['crlf_newline_ordinals'] = source['crlf_newline_ordinals']
                else:
                    row['metadata_restorations'] = [verify_metadata(raw, item, inventories)
                                                    for item in metadata_by_path[job['path']]]
                row['passed'] = True
            except Exception as exc:
                row['passed'] = False
                row['error'] = type(exc).__name__ + ': ' + str(exc)
            return row

        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = [pool.submit(execute, job) for job in jobs]
            for future in as_completed(futures):
                value['remote_files'].append(future.result())
                if len(value['remote_files']) % 100 == 0:
                    print(json.dumps({'completed': len(value['remote_files']), 'total': len(jobs)}), flush=True)
        value['remote_files'].sort(key=lambda row: (row['kind'], row['path']))
        rows = value['remote_files']
        value['public_packet_payload_files'] = sum(row['kind'] == 'public_packet' and row['passed'] for row in rows)
        value['historical_unique_source_files'] = sum(row['kind'] == 'historical_source' and row['passed'] for row in rows)
        value['snapshot_files_reconstructable'] = sum(row.get('snapshot_restorations_verified', 0) for row in rows)
        value['exact_metadata_joins'] = sum(len(row.get('metadata_restorations', [])) for row in rows if row['passed'])
        value['public_builtin_fixture_files'] = sum(row.get('public_builtin_fixture', False) for row in rows if row['passed'])
        value['public_builtin_fixture_restored_bytes'] = sum(row.get('restored_bytes', 0) for row in rows if row['passed'] and row.get('public_builtin_fixture'))
        value['passed'] = (len(rows) == 1487 and all(row['passed'] for row in rows) and
                           value['public_packet_payload_files'] == 506 and value['historical_unique_source_files'] == 981 and
                           value['snapshot_files_reconstructable'] == 1962 and value['exact_metadata_joins'] == 44 and
                           value['public_builtin_fixture_files'] == 6 and value['public_builtin_fixture_restored_bytes'] == 175666)
    except Exception as exc:
        value['errors'].append(type(exc).__name__ + ': ' + str(exc))
        value['passed'] = False
    finally:
        if batch is not None:
            try:
                batch.close()
            except Exception as exc:
                value['errors'].append('Git read-helper close: ' + type(exc).__name__ + ': ' + str(exc))
                value['passed'] = False
        value['finished_utc'] = utc()
        value['seconds'] = time.monotonic() - started
        value['payloads_saved_to_disk'] = False
        with output.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(value, stream, indent=2); stream.write('\n')
    print(json.dumps({'passed': value['passed'], 'files': len(value['remote_files']),
                      'errors': value['errors'], 'output': str(output)}), flush=True)
    return 0 if value['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
