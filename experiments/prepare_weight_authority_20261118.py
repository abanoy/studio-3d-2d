"""Root-only read-only lane check and fresh synthetic-test authority; no Blender.

Invoke this as a file. Embedding its filter in the caller's shell command makes
that shell match the very coordinator-pattern being observed. No scope filter
or count is weakened here. Only a genuine zero count can issue the authority.
"""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
import stat
import subprocess
import uuid

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SHA = 'e17561614cd2ec4fe5b9210b0d1062371d8c34649184752c088ecfb4ce8a70ab'
PROBE_SHA = '31f4a7275e11883a9936b033148d3bae5638d2017fa5147b305ea6a945289adb'
HEAD = '795a0af905bfbe49b99ab7335594cd6666ef91e5'
POINTER = ROOT / 'output/weight_authority_current_20261118.json'


def read(path, maximum):
    path = Path(path)
    for item in (path, *path.parents):
        assert not item.is_symlink()
        assert not (os.path.lexists(item) and getattr(item.lstat(), 'st_file_attributes', 0) & 0x400)
    before = path.lstat()
    assert stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and 0 < before.st_size <= maximum
    body = path.read_bytes()
    after = path.lstat()
    fields = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_nlink)
    assert fields(before) == fields(after) and len(body) == before.st_size
    return body


def digest(body):
    return hashlib.sha256(body).hexdigest()


def packet(name, pin):
    folder = ROOT / 'experiments' / name
    raw = read(folder / 'INDEX.json', 1024 * 1024)
    assert digest(raw) == pin
    rows = json.loads(raw)['files']
    rows = [dict(path=k, **v) for k, v in rows.items()] if type(rows) is dict else rows
    assert type(rows) is list and 1 <= len(rows) <= 20
    names = [x['path'] for x in rows]
    assert len(names) == len(set(names))
    assert {p.name for p in folder.iterdir()} == {'INDEX.json', *names}
    for row in rows:
        name = row['path']
        assert type(name) is str and name not in ('', '.', '..', 'INDEX.json')
        assert not any(c in name for c in ('/', '\\', ':'))
        body = read(folder / name, 2 * 1024 * 1024)
        assert type(row['bytes']) is int and len(body) == row['bytes'] and digest(body) == row['sha256']


def output_identity():
    directory = ROOT / 'output'
    for item in (directory, *directory.parents):
        info = item.lstat()
        assert stat.S_ISDIR(info.st_mode) and not item.is_symlink()
        assert not getattr(info, 'st_file_attributes', 0) & 0x400
    assert directory.resolve() == directory
    info = directory.lstat()
    return info.st_dev, info.st_ino, getattr(info, 'st_file_attributes', 0)


def save(path, value, expected_directory):
    assert path.parent == ROOT / 'output' and output_identity() == expected_directory
    body = (json.dumps(value, indent=2, allow_nan=False) + '\n').encode()
    with path.open('xb') as stream:
        stream.write(body)
        stream.flush()
        os.fsync(stream.fileno())
    assert output_identity() == expected_directory
    return digest(body)


def main():
    assert os.name == 'nt' and not os.path.lexists(POINTER)
    output_directory = output_identity()
    packet('blender_weight_storage_probe_runtime_20261118', RUNTIME_SHA)
    packet('blender_weight_storage_probe_20261118', PROBE_SHA)
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True, timeout=15).strip() == HEAD
    pins = json.loads(read(ROOT / 'experiments/blender_weight_storage_probe_runtime_20261118/RUNTIME_PINS.json', 65536))
    shell = Path(pins['executables']['pwsh']['path'])
    assert digest(read(shell, 32 * 1024 * 1024)) == pins['executables']['pwsh']['sha256']
    pattern = r'(run_canonical_owned\.ps1|start_canonical_[^ ]*\.ps1|tests[\\/]verify\.py|replay_runtime\.py|neon_owner_cold187|weight-storage-probe)'
    code = (
        "$ErrorActionPreference='Stop'; $items=@(Get-CimInstance Win32_Process | Where-Object {"
        "$_.ProcessId -notin @($PID," + str(os.getpid()) + ") -and "
        r"(($_.Name -match '^(Godot.*|blender|ffmpeg|ffprobe|pythonw?)\.exe$') -or "
        r"($_.Name -match '^(pwsh|powershell)\.exe$' -and $_.CommandLine -match '" + pattern + "')) -and "
        "($_.CommandLine -like '*has-acceptance-session-20261111*' -or $_.CommandLine -like '*has-neon-review-20261116-c2d52ff*')}); "
        "@{owned_count=$items.Count; main_count=@($items | Where-Object {$_.CommandLine -like '*has-acceptance-session-20261111*'}).Count; "
        "review_count=@($items | Where-Object {$_.CommandLine -like '*has-neon-review-20261116-c2d52ff*'}).Count; "
        "observed_utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json -Compress"
    )
    result = subprocess.run([str(shell), '-NoLogo', '-NoProfile', '-NonInteractive', '-Command', code],
                            capture_output=True, timeout=40, creationflags=subprocess.CREATE_NO_WINDOW)
    assert result.returncode == 0 and not result.stderr.strip() and len(result.stdout) <= 65536
    lane = json.loads(result.stdout)
    assert all(type(lane[k]) is int and lane[k] == 0 for k in ('owned_count', 'main_count', 'review_count'))
    lane.update(format='has_root_synthetic_weight_storage_closed_lane_1', termination_issued=False)
    run_id = uuid.uuid4().hex
    now = datetime.now(timezone.utc)
    authority = {
        'format': 'has_root_synthetic_weight_storage_execution_authority_1',
        'phase': 'ROOT_APPROVED_FRESH_SYNTHETIC_ONLY', 'metadata_head': HEAD,
        'run_id': run_id, 'issued_utc': now.isoformat(),
        'expires_utc': (now + timedelta(minutes=15)).isoformat(),
        'output_root': str(ROOT / 'output' / ('weight-storage-probe-20261118-' + run_id)),
        'runtime_packet_sha256': RUNTIME_SHA, 'probe_packet_sha256': PROBE_SHA,
        'root_execution_authorized': True, 'root_lane': lane,
    }
    path = ROOT / 'output' / ('weight-storage-probe-authority-' + run_id + '.json')
    pin = save(path, authority, output_directory)
    pointer = {'authority': str(path), 'authority_sha256': pin, 'runtime_packet_sha256': RUNTIME_SHA,
               'run_id': run_id, 'stage': authority['output_root']}
    save(POINTER, pointer, output_directory)
    print(json.dumps(pointer))


if __name__ == '__main__':
    main()
