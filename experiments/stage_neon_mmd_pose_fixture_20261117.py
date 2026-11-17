"""Root-only exact private copy of the prepared owner MMD pose fixture."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import stat

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
RUN = REVIEW / 'output/windows-neon-3a3701a-20261117T185401541257'
REV = '3a3701ab6edfa81dc883759403c170b8555aab07'


def safe(path):
    path = Path(path).absolute()
    assert '..' not in path.parts
    for part in (path, *path.parents):
        if part.exists():
            value = part.lstat()
            assert not stat.S_ISLNK(value.st_mode) and not getattr(value, 'st_file_attributes', 0) & 0x400
    return path


def identity(path):
    value = safe(path).stat()
    assert stat.S_ISREG(value.st_mode) and value.st_nlink == 1 and value.st_size <= 64 * 1024 * 1024
    return {name: getattr(value, name) for name in (
        'st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_nlink', 'st_file_attributes')}


def observed(path):
    before = identity(path)
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    assert identity(path) == before
    return {'identity': before, 'sha256': digest}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root-lane-closed', action='store_true', required=True)
    parser.add_argument('--closure', type=Path, required=True)
    parser.add_argument('--closure-sha256', required=True)
    args = parser.parse_args()
    closure = safe(args.closure)
    assert closure.parent.resolve() == RUN.resolve()
    authority = observed(closure)
    assert authority['sha256'] == args.closure_sha256
    released = json.loads(closure.read_bytes())
    assert released['released'] is True and released['full_suite_passed'] is False
    assert released['source_commit'] == REV and released['canonical_run'] == RUN.name
    assert released['all_collected_jobs_desktops_closed_private'] is True
    assert released['all_inline_exact_physical_matches'] is True
    assert released['root_observer_issued_no_termination'] is True
    source = safe(ROOT / 'output/compatibility/miku-tested')
    target = safe(REVIEW / 'output/compatibility/miku-tested')
    assert source.is_dir() and not target.exists()
    files = sorted(path for path in source.rglob('*') if path.is_file())
    assert len(files) == 18
    assert {path.relative_to(source).as_posix() for path in files} == {
        'conversion-request.json', 'conversion.log', 'editable.blend', 'parameters.json',
        'scene.glb', 'worker.json', 'native/eye2.bmp', 'native/Miku_Hatsune.pmd',
        *(f'toon{number:02}.bmp' for number in range(1, 11))}
    before = {path.relative_to(source).as_posix(): observed(path) for path in files}
    assert sum(row['identity']['st_size'] for row in before.values()) < 4 * 1024 * 1024
    private = safe(ROOT / 'output/PRIVATE-neon-mmd-pose-fixture-stage-20261117')
    private.mkdir(exist_ok=False)
    target.mkdir(parents=True, exist_ok=False)
    rows = []
    with (private / 'JOURNAL.jsonl').open('x', encoding='utf-8', newline='\n') as journal:
        for relative, original in zip(before, files):
            assert observed(original) == before[relative]
            copy = safe(target / relative)
            assert copy.is_relative_to(target) and not copy.exists()
            copy.parent.mkdir(parents=True, exist_ok=True)
            with original.open('rb') as reader, copy.open('xb') as writer:
                shutil.copyfileobj(reader, writer)
            shutil.copystat(original, copy, follow_symlinks=False)
            final = observed(copy)
            assert observed(original) == before[relative]
            assert final['sha256'] == before[relative]['sha256']
            assert final['identity']['st_size'] == before[relative]['identity']['st_size']
            assert final['identity']['st_mtime_ns'] == before[relative]['identity']['st_mtime_ns']
            row = {'relative': relative, 'source': before[relative], 'copy': final}
            rows.append(row)
            journal.write(json.dumps(row, allow_nan=False) + '\n')
            journal.flush()
            os.fsync(journal.fileno())
    assert {path.relative_to(source).as_posix(): observed(path) for path in files} == before
    assert observed(closure) == authority
    record = {'format': 'has_private_neon_mmd_pose_fixture_stage_1', 'closure': str(closure),
              'closure_sha256': args.closure_sha256, 'source': str(source), 'target': str(target),
              'files': len(rows), 'bytes': sum(row['identity']['st_size'] for row in before.values()),
              'all_originals_preserved': True, 'all_copies_equal': True, 'rows': rows,
              'native_pose_tested': False, 'full_suite_passed': False, 'private_art_publication': False}
    with (private / 'PROVENANCE.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(record, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({key: record[key] for key in ('files', 'bytes', 'all_originals_preserved',
                     'all_copies_equal', 'native_pose_tested', 'full_suite_passed')}))


if __name__ == '__main__':
    main()
