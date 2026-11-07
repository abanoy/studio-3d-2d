"""Guarded promotion of an already validated directory-project manifest."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import sys
import tempfile

try:
    from .has_project import HasError, MAX_META, save_lock, sha
    from .directory_payloads import sync_files, parent_directories
    from .save_sync import sync_directory
except ImportError:
    from has_project import HasError, MAX_META, save_lock, sha
    from directory_payloads import sync_files, parent_directories
    from save_sync import sync_directory


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


def commit(folder, candidate_name, expected, candidate_sha, previous_valid, boundary=None):
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
        payload, directories = sync_files(folder, json.loads(data))
        directories = parent_directories(directories, folder, folder if boundary is None else boundary)
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
        synced_count = 0
        for directory in directories:
            if sync_directory(directory):synced_count += 1
        synced = synced_count == len(directories)
        os.replace(candidate, target)
        try:
            final_synced = sync_directory(folder)
        except OSError as error:
            return dict(ok=False, committed=True, error='Project was written, but directory sync failed: ' + str(error))
        return dict(ok=True, committed=True, directory_synced=synced and final_synced, directories_synced=synced_count, manifest_directory_synced=final_synced, **payload)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder')
    parser.add_argument('candidate')
    parser.add_argument('expected')
    parser.add_argument('candidate_sha')
    parser.add_argument('previous_valid', choices=['yes', 'no'])
    parser.add_argument('--sync-boundary')
    args = parser.parse_args()
    try:
        result = commit(args.folder, args.candidate, '' if args.expected == 'missing' else args.expected, args.candidate_sha, args.previous_valid == 'yes', args.sync_boundary)
    except (OSError, ValueError, RuntimeError) as error:
        result = dict(ok=False, committed=False, error=str(error))
    sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
