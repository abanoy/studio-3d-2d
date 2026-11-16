"""Independent read-only alias/source audit; writes a fresh compact receipt."""
from pathlib import Path
import gzip
import hashlib
import json
import stat

HERE = Path(__file__).resolve().parent


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    for ancestor in (path, *path.parents):
        info = ancestor.lstat()
        assert not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400
    before = path.stat()
    raw = path.read_bytes()
    after = path.stat()
    assert before.st_nlink == 1 and (before.st_size, before.st_mtime_ns, before.st_ino) == (
        after.st_size, after.st_mtime_ns, after.st_ino)
    return raw


def main():
    raw_index = read(HERE / 'PAYLOAD_INDEX.json')
    index = json.loads(raw_index)
    assert index['source_commit'] == 'f0dd57a2e568089d396fecba819ab987da658bf0'
    assert len(index['files']) == 61
    blobs = set()
    for row in index['files']:
        relative = Path(row['path'])
        assert not relative.is_absolute() and '..' not in relative.parts
        stored = read(HERE / relative)
        assert len(stored) == row['stored_bytes'] and sha(stored) == row['stored_sha256']
        assert row['encoding'] in ('gzip', 'identity')
        raw = gzip.decompress(stored) if row['encoding'] == 'gzip' else stored
        assert len(raw) == row['raw_bytes'] and sha(raw) == row['raw_sha256']
        assert raw == read(Path(row['source']))
        blobs.add(row['path'])
    assert len(blobs) == index['stored_payloads'] == 52
    benchmark = json.loads(read(HERE / 'BENCHMARK.json'))
    assert benchmark['packet_payload_index_sha256'] == sha(raw_index)
    assert benchmark['passed'] and benchmark['checks'] == 180 and benchmark['check_split'] == [44, 46, 49, 41]
    assert benchmark['private_jobs'] == 4 and benchmark['all_closed'] and len(benchmark['preservation']) == 9
    assert all(benchmark['preservation'].values())
    assert len(benchmark['exact_names']) == len(set(benchmark['exact_names'])) == 180
    assert benchmark['audio_cache_phase_proofs'] == benchmark['strict_state_comparisons'] == 12
    assert benchmark['generated_retained'] == {'output': 10, '.godot': 0}
    assert benchmark['first_validation_status'].startswith('FAILED_') and benchmark['first_failed_review_retained']
    assert benchmark['native_Source_solver'] == 'not_implemented' and not benchmark['artist_or_human_device_acceptance']
    proof = {'format': 'has_independent_actual_review_metadata_audit_1', 'passed': True,
             'source_aliases_verified': 61, 'stored_payloads_verified': 52,
             'all_raw_stored_original_hashes_equal': True, 'checks': 180, 'private_jobs': 4,
             'preservation_gates': 9, 'payload_index_sha256': sha(raw_index),
             'benchmark_sha256': sha(read(HERE / 'BENCHMARK.json')),
             'new_app_or_parser_runs': False, 'deletions': 0, 'remote_retrieval': 'PENDING_ROOT_PUBLICATION'}
    with (HERE / 'INDEPENDENT_AUDIT.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(proof, stream, indent=2)
        stream.write('\n')
    print(json.dumps(proof, indent=2))


if __name__ == '__main__':
    main()
