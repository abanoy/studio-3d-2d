"""Read back every changed public file from the exact GitHub commit before cleanup."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import argparse
import datetime
import gzip
import hashlib
import io
import json
import subprocess
import time
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
ART = {'.png', '.jpg', '.jpeg', '.wav', '.mp3', '.mp4', '.has', '.blend', '.vrm',
       '.glb', '.gma', '.rar', '.zip', '.bin', '.mdl', '.vvd', '.vtx', '.vtf', '.kra'}


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def tested_source_projection(payload, tested_sha256, tested_bytes=None, reconstruction=None):
    """Admit exact bytes or one explicit UTF8 LF->CRLF reconstruction only."""
    if reconstruction is None:
        reconstruction = 'exact' if hashlib.sha256(payload).hexdigest() == tested_sha256 else 'LF_to_CRLF'
    assert reconstruction in ('exact', 'LF_to_CRLF')
    reconstructed = payload
    if reconstruction == 'LF_to_CRLF':
        assert b'\x00' not in payload and b'\r' not in payload
        payload.decode('utf-8', errors='strict')
        reconstructed = payload.replace(b'\n', b'\r\n')
    assert hashlib.sha256(reconstructed).hexdigest() == tested_sha256
    if tested_bytes is not None:
        assert len(reconstructed) == tested_bytes
    return {'reconstruction': reconstruction, 'tested_sha256': tested_sha256,
            'tested_bytes': len(reconstructed)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--commit', required=True)
    parser.add_argument('--base', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--include-leaf-source', action='store_true', help='Also retrieve the unchanged203source/support files backing disposable leaf copies')
    args = parser.parse_args()
    commit = git('rev-parse', args.commit).decode().strip()
    base = git('rev-parse', args.base).decode().strip()
    assert len(commit) == len(base) == 40
    remote = git('ls-remote', 'origin', 'refs/heads/main').decode().split()[0]
    assert remote == commit
    output = args.output.resolve()
    assert output.is_relative_to(ROOT / 'output') and not output.exists()
    names = git('diff', '--name-only', '--diff-filter=AM', '-z', base, commit).decode('utf-8').split('\0')
    names = sorted(p for p in names if p)
    extra = {}
    source_catalogue = None
    if args.include_leaf_source:
        lock_path = 'experiments/source_0x31_native_leaf_20261115/SOURCE_LOCK.json'
        catalogue_path = 'experiments/windows_bone_binding_full_actual_20261115/full/canonical/source-before.json.gz'
        lock_raw = git('show', commit + ':' + lock_path)
        catalogue_gzip = git('show', commit + ':' + catalogue_path)
        assert len(lock_raw) <= 8 * 1024 * 1024 and len(catalogue_gzip) <= 8 * 1024 * 1024
        lock = json.loads(lock_raw)
        with gzip.GzipFile(fileobj=io.BytesIO(catalogue_gzip), mode='rb') as stream:
            catalogue_raw = stream.read(8 * 1024 * 1024 + 1)
        assert len(catalogue_raw) <= 8 * 1024 * 1024
        assert hashlib.sha256(catalogue_raw).hexdigest() == '8d9e7d94c745081e0ca084bc64e7498bc7ccb218c44209e1354bcd53f3c50a2a'
        catalogue = json.loads(catalogue_raw)
        assert catalogue['commit'] == lock['source_HEAD_context'] == 'f0dd57a2e568089d396fecba819ab987da658bf0'
        assert len(catalogue['source_sha256']) == 1008
        assert len(lock['files']) == 200 and len({row['path'] for row in lock['files']}) == 200
        assert all(catalogue['source_sha256'][row['path']] == row['sha256'] for row in lock['files'])
        extra = {row['path']: {'tested_sha256': row['sha256'], 'tested_bytes': row['bytes']} for row in lock['files']}
        for name in ('data/bone_names.en.json', 'data/discovery_sources.json', 'data/shape_names.en.json'):
            assert name not in extra
            extra[name] = {'tested_sha256': catalogue['source_sha256'][name], 'tested_bytes': None}
        assert len(extra) == 203
        source_catalogue = {'path': catalogue_path, 'git_blob_bytes': len(catalogue_gzip),
                            'git_blob_sha256': hashlib.sha256(catalogue_gzip).hexdigest(),
                            'raw_bytes': len(catalogue_raw), 'raw_sha256': hashlib.sha256(catalogue_raw).hexdigest(),
                            'tested_source_commit': catalogue['commit'], 'source_files': 1008,
                            'leaf_source_lock': lock_path, 'leaf_source_lock_sha256': hashlib.sha256(lock_raw).hexdigest()}
        names = sorted(set(names) | set(extra) | {lock_path, catalogue_path})
    assert 0 < len(names) <= 3000 and len(names) == len(set(names))
    expected = {}
    reader = subprocess.Popen(['git', 'cat-file', '--batch'], cwd=ROOT,
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        for name in names:
            relative = Path(name)
            assert '\n' not in name and '\r' not in name and not relative.is_absolute() and '..' not in relative.parts
            assert relative.suffix.lower() not in ART and (name.startswith('experiments/') or name.startswith('docs/') or name == 'LLM.md' or name in extra)
            reader.stdin.write((commit + ':' + name + '\n').encode('utf-8'))
            reader.stdin.flush()
            header = reader.stdout.readline().decode('ascii').strip().split()
            assert len(header) == 3 and header[1] == 'blob'
            size = int(header[2])
            assert 0 <= size <= 8 * 1024 * 1024
            payload = reader.stdout.read(size)
            assert len(payload) == size and reader.stdout.read(1) == b'\n'
            expected[name] = {'bytes': size, 'sha256': hashlib.sha256(payload).hexdigest(), 'git_blob': header[0]}
            if name in extra:
                expected[name].update(tested_source_projection(
                    payload, extra[name]['tested_sha256'], extra[name]['tested_bytes']))
                expected[name].update(remote_git_sha256=expected[name]['sha256'], remote_git_bytes=size)
    finally:
        reader.stdin.close()
        code = reader.wait(timeout=10)
        assert code == 0
    started = time.monotonic()

    def fetch(name):
        pin = expected[name]
        url = 'https://raw.githubusercontent.com/abanoy/studio-3d-2d/' + commit + '/' + urllib.parse.quote(name, safe='/')
        failures = []
        for attempt in range(3):
            try:
                request = urllib.request.Request(url, headers={'User-Agent': 'HAS-Exact-Backup-Verification'})
                with urllib.request.urlopen(request, timeout=20) as response:
                    assert response.status == 200
                    payload = response.read(pin['bytes'] + 1)
                assert len(payload) == pin['bytes'] and hashlib.sha256(payload).hexdigest() == pin['sha256']
                reconstructed = {}
                if name in extra:
                    admission = {key: pin[key] for key in ('reconstruction', 'tested_sha256', 'tested_bytes')}
                    observed = tested_source_projection(payload, admission['tested_sha256'],
                                                        admission['tested_bytes'], admission['reconstruction'])
                    assert observed == admission
                    reconstructed['remote_tested_source_reconstruction_equal'] = True
                return {'path': name, **pin, **reconstructed, 'remote_bytes_equal': True, 'attempts': attempt + 1}
            except Exception as exc:
                failures.append(type(exc).__name__ + ': ' + str(exc))
                if attempt < 2:
                    time.sleep(1)
        return {'path': name, **pin, 'remote_bytes_equal': False, 'errors': failures}

    rows = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(fetch, name): name for name in names}
        for future in as_completed(futures):
            rows.append(future.result())
            if len(rows) % 100 == 0:
                print(json.dumps({'verified': len(rows), 'total': len(names)}), flush=True)
    rows.sort(key=lambda row: row['path'])
    passed = all(row['remote_bytes_equal'] and
                 (row['path'] not in extra or row.get('remote_tested_source_reconstruction_equal') is True)
                 for row in rows)
    recipes = {name: sum(row.get('reconstruction') == name for row in rows)
               for name in ('exact', 'LF_to_CRLF')}
    value = {'format': 'has_exact_github_increment_readback_1', 'passed': passed,
             'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'base_commit': base, 'remote_main_commit': commit, 'files': len(rows),
             'unchanged_leaf_source_support_files': len(extra),
             'tested_source_catalogue': source_catalogue, 'tested_source_reconstruction_recipes': recipes,
             'raw_bytes': sum(row['bytes'] for row in rows), 'seconds': time.monotonic() - started,
             'native_art_media_downloaded': False, 'remote_files': rows}
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
    print(json.dumps({k: value[k] for k in ['passed', 'files', 'raw_bytes', 'seconds']}), flush=True)
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
