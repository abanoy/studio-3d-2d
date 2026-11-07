"""Guarded promotion of an already validated directory-project manifest."""
from pathlib import Path
import argparse
import errno
import hashlib
import json
import os
import re
import sys
import tempfile

try:
    from .has_project import HasError, MAX_META, save_lock, sha
except ImportError:
    from has_project import HasError, MAX_META, save_lock, sha


def check_path(folder, name):
    path = folder / name
    if path.is_symlink() or path.is_dir():
        raise HasError('Directory save destination is linked or blocked; previous save preserved')
    return path


def read_manifest(path, expected=None):
    if not path.is_file() or path.stat().st_size > MAX_META:
        raise HasError('Missing or oversized manifest; previous save preserved')
    data = path.read_bytes()
    if expected is not None and hashlib.sha256(data).hexdigest() != expected:
        raise HasError('Prepared manifest changed; previous save preserved')
    value = json.loads(data, parse_constant=lambda value: (_ for _ in ()).throw(HasError("Nonfinite manifest value; previous save preserved")))
    if not isinstance(value, dict) or type(value.get('schema_version')) not in (int, float) or value['schema_version'] not in range(1, 9):
        raise HasError('Invalid prepared manifest; previous save preserved')
    return data


def sync_directory(folder):
    # Python does not expose a portable Windows directory-flush handle. Keep its
    # established save behavior; native directory/power-loss validation is open.
    if os.name != 'posix':
        return False
    handle = os.open(folder, os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0))
    try:
        try:
            os.fsync(handle)
        except OSError as error:
            if error.errno in (errno.EINVAL, errno.ENOTSUP, errno.ENOSYS):
                return False
            raise
    finally:
        os.close(handle)
    return True


def commit(folder, candidate_name, expected, candidate_sha, previous_valid):
    folder = Path(folder).resolve(strict=True)
    if not re.fullmatch(r'project\.json\.[A-Za-z0-9_-]+\.tmp', candidate_name):
        raise HasError('Invalid prepared manifest filename; previous save preserved')
    if not re.fullmatch(r'[0-9a-f]{64}', candidate_sha) or expected and not re.fullmatch(r'[0-9a-f]{64}', expected):
        raise HasError('Invalid manifest fingerprint; previous save preserved')
    target = check_path(folder, 'project.json')
    backup = check_path(folder, 'project.backup.json')
    candidate = check_path(folder, candidate_name)
    for name in ('project.json.tmp', 'project.backup.json.tmp'):
        check_path(folder, name)
    with save_lock(target, label="project"):
        # Unique prepared asset/PNG names can coexist. Only the writer whose
        # starting manifest still matches may rotate the committed generation.
        current = sha(target) if target.exists() else ''
        if current != expected:
            raise HasError('Another save changed this project. Current saved generation preserved; save again to retry.')
        data = read_manifest(candidate, candidate_sha)
        if candidate.stat().st_nlink != 1:
            raise HasError('Prepared manifest has another file owner; previous save preserved')
        with candidate.open('r+b') as stream:
            stream.flush()
            os.fsync(stream.fileno())
        # Read after sync too, before either committed directory entry changes.
        if read_manifest(candidate, candidate_sha) != data:
            raise HasError('Manifest readback differs; previous save preserved')
        if current and previous_valid:
            old = read_manifest(target, current)
            handle, name = tempfile.mkstemp(prefix='project.backup.json.', suffix='.tmp', dir=folder)
            temporary = Path(name)
            with os.fdopen(handle, 'wb') as stream:
                stream.write(old)
                stream.flush()
                os.fsync(stream.fileno())
            if temporary.read_bytes() != old:
                raise HasError('Backup readback differs; previous save preserved')
            os.replace(temporary, backup)
        synced = sync_directory(folder)
        os.replace(candidate, target)
        try:
            sync_directory(folder)
        except OSError as error:
            return dict(ok=False, committed=True, error='Project was written, but directory sync failed: ' + str(error))
        return dict(ok=True, committed=True, directory_synced=synced)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder')
    parser.add_argument('candidate')
    parser.add_argument('expected')
    parser.add_argument('candidate_sha')
    parser.add_argument('previous_valid', choices=['yes', 'no'])
    args = parser.parse_args()
    try:
        result = commit(args.folder, args.candidate, '' if args.expected == 'missing' else args.expected, args.candidate_sha, args.previous_valid == 'yes')
    except (OSError, ValueError, RuntimeError) as error:
        result = dict(ok=False, committed=False, error=str(error))
    sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
