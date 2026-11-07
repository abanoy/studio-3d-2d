"""Local save sync helpers; unsupported platforms are reported, never certified."""
from pathlib import Path
import errno
import os


def existing_boundary(directory):
    current = Path(directory).absolute()
    while not current.is_dir():
        parent = current.parent
        if parent == current:
            raise OSError('Cannot find an existing save parent')
        current = parent
    return current.resolve(strict=True)


def sync_directory(directory):
    if os.name != 'posix':
        return False
    handle = os.open(directory, os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0))
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


def parents(directories, boundary):
    boundary = Path(boundary).resolve(strict=True)
    result = set()
    for directory in directories:
        current = Path(directory).resolve(strict=True)
        while True:
            if not current.is_relative_to(boundary):
                raise ValueError('Save sync escaped its owned boundary')
            result.add(current)
            if current == boundary:
                break
            current = current.parent
    return sorted(result, key=lambda path: (-len(path.parts), str(path)))
