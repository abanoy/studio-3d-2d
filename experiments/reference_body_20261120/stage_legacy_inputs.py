"""Stage only declared private fixture payloads for the existing Windows suite."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import stat
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.has_project import members


def identity(path):
    value = path.stat()
    return dict(bytes=value.st_size, mtime_ns=value.st_mtime_ns,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def regular(path, boundary):
    path, boundary = Path(path).absolute(), Path(boundary).resolve(strict=True)
    assert path.resolve(strict=True).is_relative_to(boundary)
    for part in (path, *path.parents):
        info = part.lstat()
        assert not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400
        if part == boundary:break
    assert path.is_file()
    return path


def destination(path, boundary):
    path, boundary = Path(path).absolute(), Path(boundary).resolve(strict=True)
    assert path.resolve().is_relative_to(boundary) and path != boundary
    for part in (path, *path.parents):
        try:info = part.lstat()
        except FileNotFoundError:
            if part == boundary:raise
            continue
        assert not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400
        if stat.S_ISREG(info.st_mode):assert info.st_nlink == 1
        if part == boundary:break
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture-root', type=Path, required=True)
    options = parser.parse_args()
    source_root = options.fixture_root.resolve(strict=True)
    output = ROOT / 'output'
    output.mkdir(exist_ok=True)
    records = []

    def copy(relative, expected=None):
        original = regular(source_root / relative, source_root)
        target = destination(output / relative, output)
        before = identity(original)
        if expected is not None:assert before['sha256'] == expected
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            regular(target, output)
            if identity(target) != before:
                assert relative == 'native-import-verification.json'
                backup = destination(target.with_name('native-import-verification-before-body-staging.json'), output)
                assert not backup.exists()
                shutil.copy2(target, backup)
        shutil.copy2(original, target)
        regular(target, output)
        assert identity(original) == identity(target) == before
        records.append(dict(source=str(original), copy=str(target), **before))

    for relative in ('pose-smoke/miku-project', 'source-smoke/source-project', 'sfm-smoke/project'):
        manifest_path = regular(source_root / relative / 'project.json', source_root)
        assets, cels = members(json.loads(manifest_path.read_bytes()))
        for name in ['project.json', *sorted(set(assets) | set(cels))]:
            copy(relative + '/' + name, assets[name]['sha256'] if name in assets else None)
    copy('native-import-verification.json')
    # Existing optional PMD pose coverage reads this exact preparation location.
    copy('compatibility/miku-tested/scene.glb', 'b0a78fd482908e72099ad970649849bc0cd392e6e50585efade1175f45dece9a')
    copy('compatibility/miku-tested/parameters.json', 'cfe628f5a8c5134df94448b72597146975707dbec938ada7efe3d04305514fc8')
    assert all(identity(Path(row['source'])) == {key:row[key] for key in ('bytes','mtime_ns','sha256')} for row in records)
    result = dict(format='has_body_legacy_input_staging_1', source_root=str(source_root),
                  files=records, count=len(records), bytes=sum(row['bytes'] for row in records), originals_unchanged=True)
    destination(output / 'reference-body-legacy-staging.json', output).write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({key:value for key,value in result.items() if key != 'files'}))


if __name__ == '__main__':main()
