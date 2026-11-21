"""Only declared managed files participate in directory save syncing."""
from pathlib import Path
import hashlib
import os
import re

try:
    from .has_project import HasError, safe
    from .save_sync import parents
except ImportError:
    from has_project import HasError, safe
    from save_sync import parents


def mapping(value):
    if not isinstance(value, dict):
        raise HasError('Invalid managed payload metadata; previous save preserved')
    return value


def rows(value):
    if not isinstance(value, list):
        raise HasError('Invalid managed payload list; previous save preserved')
    return value


def declared(manifest, result=None, depth=0):
    if depth > 8:
        raise HasError('Excessive scene nesting in save sync; previous save preserved')
    if result is None:
        result = {}

    def add(row, path_key='path', hash_key='sha256'):
        if not isinstance(row, dict) or not row.get(path_key):
            return
        path = row[path_key]
        if not isinstance(path, str):
            raise HasError('Invalid declared save path; previous save preserved')
        safe(path)
        if not path.startswith(('assets/', 'cels/', 'references/')):
            raise HasError('Save payload is outside managed folders; previous save preserved')
        digest = row.get(hash_key) if hash_key else None
        if hash_key and (not isinstance(digest, str) or not re.fullmatch(r'[0-9a-f]{64}', digest)):
            raise HasError('Invalid declared asset digest; previous save preserved')
        if result.get(path) is not None and digest is not None and result[path] != digest:
            raise HasError('Conflicting declared asset digest; previous save preserved')
        result[path] = digest or result.get(path)

    for key in ('scene', 'model', 'reference_sheet'):
        add(manifest.get(key))
    for layer in rows(manifest.get('layers', [])):
        for cel in rows(mapping(layer).get('cels', [])):
            # Cel pixel_sha256 hashes decoded pixels, not the encoded PNG file.
            # The Godot writer already verifies those pixels before staging.
            add(cel, hash_key=None)
    audio = mapping(manifest.get('audio', {}))
    add(audio)
    for clip in rows(audio.get('clips', [])):
        add(clip)
    world = mapping(manifest.get('world', {}))
    for row in rows(world.get('objects', [])):
        add(row)
    for row in rows(world.get('effects', [])):
        add(row)
        add(row, 'texture_path', 'texture_sha256')
    for asset in rows(mapping(manifest.get('sequence_graph', {})).get('assets', [])):
        declared(mapping(mapping(asset).get('scene')), result, depth + 1)
    return result


def sync_files(folder, manifest):
    names = declared(manifest)
    directories = {folder}
    synced = os.name == 'posix'
    verified_assets = 0
    for name, expected in sorted(names.items()):
        path = folder
        for part in Path(name).parts:
            path /= part
            if path.is_symlink():
                raise HasError('Linked managed payload refused; previous save preserved')
        if not path.is_file():
            raise HasError('Missing declared payload: ' + name + '; previous save preserved')
        with path.open('rb') as stream:
            if expected is not None:
                digest = hashlib.sha256()
                for block in iter(lambda: stream.read(1024 * 1024), b''):
                    digest.update(block)
                if digest.hexdigest() != expected:
                    raise HasError('Declared payload checksum differs: ' + name + '; previous save preserved')
                verified_assets += 1
            if os.name == 'posix':
                os.fsync(stream.fileno())
        directories.add(path.parent)
    return dict(files=len(names), assets_verified=verified_assets, payload_synced=synced), directories


def parent_directories(directories, folder, boundary):
    boundary = Path(boundary).resolve(strict=True)
    if not folder.is_relative_to(boundary):
        raise HasError('Invalid directory sync boundary; previous save preserved')
    return parents(directories, boundary)
