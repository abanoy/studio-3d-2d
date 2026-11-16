"""Independent read-only content audit; writes one fresh compact receipt only."""
from pathlib import Path
import datetime
import gzip
import hashlib
import json
import stat

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / 'experiments/resume_archive_20261115'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read_inside(base, relative):
    path = base / relative
    assert not Path(relative).is_absolute() and '..' not in Path(relative).parts
    assert path.resolve().is_relative_to(base.resolve())
    for ancestor in (path, *path.parents):
        info = ancestor.lstat()
        assert not stat.S_ISLNK(info.st_mode)
        assert not getattr(info, 'st_file_attributes', 0) & 0x400
    before = path.stat()
    assert before.st_nlink == 1 and before.st_size < 20_000_000
    raw = path.read_bytes()
    after = path.stat()
    assert (before.st_size, before.st_mtime_ns, before.st_ino) == (
        after.st_size, after.st_mtime_ns, after.st_ino)
    return raw


def main():
    manifest = json.loads(read_inside(PACKET, 'FILES.json'))
    rows = manifest['files']
    assert len(rows) == len({row['path'] for row in rows})
    actual = {p.relative_to(PACKET).as_posix() for p in PACKET.rglob('*') if p.is_file()}
    assert actual == {row['path'] for row in rows} | {'FILES.json'}
    for row in rows:
        raw = read_inside(PACKET, row['path'])
        assert len(raw) == row['bytes'] and digest(raw) == row['sha256']
    index = json.loads(read_inside(PACKET, 'INDEX.json'))
    assert len(index['files']) == 16
    total_raw = total_stored = 0
    for row in index['files']:
        stored = read_inside(PACKET, row['path'])
        assert digest(stored) == row['stored_sha256'] and len(stored) == row['stored_bytes']
        assert row['encoding'] in ('gzip', 'identity')
        raw = gzip.decompress(stored) if row['encoding'] == 'gzip' else stored
        assert len(raw) == row['raw_bytes'] and digest(raw) == row['raw_sha256']
        assert raw == read_inside(ROOT, row['source'])
        total_raw += len(raw)
        total_stored += len(stored)
    assert total_raw == 4_122_249 and total_stored == 756_657
    proof = {'format': 'has_root_independent_archive_content_audit_1',
             'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'packet': PACKET.relative_to(ROOT).as_posix(),
             'manifest_sha256': digest(read_inside(PACKET, 'FILES.json')),
             'indexed_files_verified': len(rows), 'raw_payloads_verified': 16,
             'raw_bytes': total_raw, 'stored_bytes': total_stored,
             'original_metadata_bytes_equal': True, 'remote_verification': 'PENDING',
             'new_nonuse_probe': False, 'deletions': 0, 'reclaimed_bytes': 0}
    target = Path(__file__).with_name('archive-independent-content-audit.json')
    with target.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(proof, stream, indent=2)
        stream.write('\n')
    print(json.dumps(proof, indent=2))


if __name__ == '__main__':
    main()
