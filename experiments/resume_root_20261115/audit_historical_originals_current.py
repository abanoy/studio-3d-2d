"""Fresh read-only hashes of exactly561 historically pinned native source inputs."""
from pathlib import Path, PurePosixPath
import datetime
import gzip
import hashlib
import json
import os
import stat

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
FROZEN = ROOT / 'experiments/resume_archive_20261115/historical-cleanup-audit/retained-originals-fresh-proof.json.gz'
EXPECTED_SHA = '80de0389dc4c2220b2ac6a3751f525bf001259810d27a2e799d169cd759e7f1c'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def clear(path):
    for item in (path, *path.parents):
        info = item.lstat()
        assert not stat.S_ISLNK(info.st_mode)
        assert not getattr(info, 'st_file_attributes', 0) & 0x400


def stamp(info):
    return (info.st_size, info.st_mtime_ns, info.st_dev, info.st_ino, info.st_nlink,
            getattr(info, 'st_file_attributes', 0))


def main():
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    archive = FROZEN.read_bytes()
    raw = gzip.decompress(archive)
    assert sha(raw) == EXPECTED_SHA
    frozen = json.loads(raw)
    review_path = ROOT / 'experiments/replay_audio_fix_20261115/builder/input-lock.json'
    review_raw = review_path.read_bytes()
    review = json.loads(review_raw)['native_families']
    assert len(frozen) == 5 and sum(map(len, frozen.values())) == 561
    assert len(review) == 4 and sum(map(len, review.values())) == 495
    assert all(family in frozen and frozen[family] == rows for family, rows in review.items())
    old_parent = ROOT / 'output/source-choices-native'
    families = []
    for name, rows in sorted(frozen.items()):
        family = Path(name)
        assert family.is_absolute() and family.is_relative_to(ROOT / 'output')
        assert not family.is_relative_to(old_parent)
        clear(family)
        assert family.resolve(strict=True) == family
        observed = {}
        for relative, expected in sorted(rows.items()):
            logical = PurePosixPath(relative)
            assert logical.as_posix() == relative and not logical.is_absolute()
            assert not set(logical.parts) & {'', '.', '..'}
            assert '\\' not in relative and ':' not in relative
            path = family / relative
            clear(path)
            before = path.lstat()
            assert stat.S_ISREG(before.st_mode) and before.st_nlink == 1
            assert before.st_size == expected['bytes']
            with path.open('rb') as stream:
                opened = os.fstat(stream.fileno())
                digest = hashlib.file_digest(stream, 'sha256').hexdigest()
                after = os.fstat(stream.fileno())
            final = path.lstat()
            assert all(stamp(value) == stamp(before) for value in (opened, after, final))
            assert digest == expected['sha256']
            observed[relative] = {
                'bytes': final.st_size, 'sha256': digest, 'mtime_ns': final.st_mtime_ns,
                'historical_mtime_ns': expected['mtime_ns'],
                'historical_size_and_SHA256_match': True,
                'historical_mtime_match': final.st_mtime_ns == expected['mtime_ns'],
                'stat_device': final.st_dev, 'stat_inode': final.st_ino,
                'hardlinks': final.st_nlink, 'no_reparse_ancestors': True,
                'unchanged_during_open_hash_close': True}
        families.append({'root': name, 'files': len(observed),
                         'bytes': sum(row['bytes'] for row in observed.values()),
                         'included_in_current_review495': name in review,
                         'outside_both_old_native_roots': True, 'source_map': observed})
    assert sum(row['files'] for row in families) == 561
    assert sum(row['bytes'] for row in families) == 469130387
    value = {
        'format': 'has_historical561_original_inputs_fresh_readonly_proof_1',
        'passed': True, 'started_utc': started,
        'finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'frozen_map': {'path': str(FROZEN), 'bytes': len(archive), 'sha256': sha(archive),
                       'raw_bytes': len(raw), 'raw_sha256': sha(raw)},
        'current_review_map': {'path': str(review_path), 'bytes': len(review_raw),
                               'sha256': sha(review_raw), 'families': 4, 'files': 495,
                               'exact_historical_submaps': True},
        'families': 5, 'files': 561, 'bytes': 469130387,
        'current_review_files': 495, 'additional_Kanako_files': 66,
        'all_historical_size_and_SHA256_matches': True,
        'all_historical_mtime_matches': all(v['historical_mtime_match'] for row in families for v in row['source_map'].values()),
        'regular_single_link_no_reparse_stable_reads': True,
        'source_families': families,
        'actual_metadata_source_code_sha256': sha(Path(__file__).read_bytes()),
        'native_content_copied_or_printed': False,
        'originals_modified': False, 'apps_or_parsers_launched': False,
        'process_or_CIM_queries': False, 'Git_or_network_operations': False,
        'cleanup_authorized': False,
        'limits': 'Point-in-time original-byte preservation only. This does not establish old-root current nonuse, remote backup, later preservation, or authorize cleanup.'}
    output = OUT / 'audit_historical_originals_current.json'
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2); stream.write('\n')
    print(json.dumps({'passed': value['passed'], 'families': 5, 'files': 561,
                      'bytes': 469130387, 'all_historical_mtime_matches': value['all_historical_mtime_matches'],
                      'proof_sha256': sha(output.read_bytes()), 'cleanup_authorized': False}))


if __name__ == '__main__':
    main()
