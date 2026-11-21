"""Sync and atomically promote one bounded private metadata/preview file."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import sys

try:
    from .save_sync import sync_directory, parents
    from .has_project import HasError, safe, MAX_META
except ImportError:
    from save_sync import sync_directory, parents
    from has_project import HasError, safe, MAX_META


def owned(root, relative):
    safe(relative.as_posix())
    path = root
    for part in relative.parts:
        path /= part
        if path.is_symlink():
            raise HasError('Linked metadata destination refused; previous state preserved')
    if path.exists() and not path.is_file():
        raise HasError('Metadata destination is not a regular file; previous state preserved')
    return path


def commit(root, target, temporary, digest, boundary):
    lexical = Path(root).absolute()
    target_relative = Path(target).absolute().relative_to(lexical)
    temporary_relative = Path(temporary).absolute().relative_to(lexical)
    if temporary_relative.parent != target_relative.parent or not re.fullmatch(
            re.escape(target_relative.name) + r'\.[A-Za-z0-9_-]+\.tmp', temporary_relative.name):
        raise HasError('Invalid metadata temporary ownership; previous state preserved')
    if not re.fullmatch(r'[0-9a-f]{64}', digest):
        raise HasError('Invalid metadata fingerprint; previous state preserved')
    root = lexical.resolve(strict=True)
    target = owned(root, target_relative)
    temporary = owned(root, temporary_relative)
    owned(root, Path(str(target_relative) + '.tmp'))
    if not temporary.is_file() or temporary.stat().st_size > MAX_META or temporary.stat().st_nlink != 1:
        raise HasError('Invalid metadata temporary; previous state preserved')
    with temporary.open('r+b') as stream:
        data = stream.read(MAX_META + 1)
        if len(data) > MAX_META or hashlib.sha256(data).hexdigest() != digest:
            raise HasError('Metadata readback differs; previous state preserved')
        stream.flush()
        os.fsync(stream.fileno())
        stream.seek(0)
        if stream.read(MAX_META + 1) != data:
            raise HasError('Synced metadata readback differs; previous state preserved')
    directories = parents([target.parent, root], boundary)
    synced_count = sum(bool(sync_directory(directory)) for directory in directories)
    os.replace(temporary, target)
    try:
        final_synced = sync_directory(target.parent)
    except OSError as error:
        return dict(ok=False, committed=True, error='Saved file was written, but directory sync failed: ' + str(error))
    return dict(ok=True, committed=True, directory_synced=synced_count == len(directories) and final_synced,
                directories_synced=synced_count, manifest_directory_synced=final_synced)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['root', 'target', 'temporary', 'digest', 'boundary']:
        parser.add_argument(name)
    args = parser.parse_args()
    try:
        result = commit(args.root, args.target, args.temporary, args.digest, args.boundary)
    except (OSError, ValueError, RuntimeError) as error:
        result = dict(ok=False, committed=False, error=str(error))
    sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
