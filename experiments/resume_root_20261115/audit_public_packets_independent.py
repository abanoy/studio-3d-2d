"""Read-only public packet/privacy/cross-link audit; no Git, app or process use."""
from pathlib import Path
import datetime
import gzip
import hashlib
import json
import stat

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
TARGETS = {
    'source_0x31_candidate_20261115': 'INDEX.json',
    'source_0x31_godot_candidate_20261115': 'INDEX.json',
    'resume_archive_20261115': 'FILES.json',
    'sfm_review_actual_20261115': 'INDEX.json',
    'windows_bone_binding_full_actual_20261115': 'OUTER_INDEX.json',
    'native_runtime_readiness_actual_20261115': 'OUTER_INDEX.json',
}
FORBIDDEN = {'pcm', 'vertex_positions', 'vertex_buffer', 'index_buffer', 'image_data',
             'audio_data', 'base64', 'native_rest_words_uint32', 'native_rest_matrices',
             'Blender_matrix_local_row_major', 'expected_world_bones', 'expected_native_Z_tips'}
MEDIA_SUFFIXES = {'.glb', '.gltf', '.has', '.wav', '.mp3', '.ogg', '.png', '.jpg', '.jpeg',
                  '.vrm', '.mdl', '.vvd', '.vtx', '.vtf', '.blend', '.kra', '.mp4', '.exe', '.dll', '.bin'}
json_docs = gzip_streams = source_aliases = 0


def need(value, message):
    if not value:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    for ancestor in (path, *path.parents):
        info = ancestor.lstat()
        need(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400,
             'Reparse/symlink: ' + str(path))
    before = path.stat()
    need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= 32*1024*1024,
         'Regular bounded single-link file: ' + str(path))
    raw = path.read_bytes()
    after = path.stat()
    need((before.st_size, before.st_mtime_ns, before.st_ino) == (after.st_size, after.st_mtime_ns, after.st_ino),
         'File changed: ' + str(path))
    return raw


def load(path):
    return json.loads(read(path), parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def scan(value):
    if isinstance(value, dict):
        for key, child in value.items():
            need(not (key in FORBIDDEN and child), 'Private payload field: ' + key)
            need(not (key in {'vertices', 'indices', 'triangles'} and isinstance(child, (list, dict))), 'Mesh array')
            scan(child)
    elif isinstance(value, list):
        for child in value:
            scan(child)
    elif isinstance(value, str):
        need(len(value) < 16384, 'Unreviewed long JSON string')


def member(base, relative):
    rel = Path(relative)
    need(not rel.is_absolute() and '..' not in rel.parts, 'Unsafe packet member')
    path = base / rel
    need(path.resolve().is_relative_to(base.resolve()), 'Packet escape')
    return path


def manifest(base, name, exact=True):
    raw = read(base / name)
    index = json.loads(raw)
    rows = index['files']
    need(len(rows) == len({row['path'] for row in rows}), 'Duplicate physical member')
    for row in rows:
        data = read(member(base, row['path']))
        need(len(data) == row['bytes'] and sha(data) == row['sha256'], 'Manifest mismatch: ' + row['path'])
    if exact:
        actual = {p.relative_to(base).as_posix() for p in base.rglob('*') if p.is_file()}
        need(actual == {row['path'] for row in rows} | {name}, 'Unindexed/missing physical member: ' + str(base))
    return {'index': name, 'index_sha256': sha(raw), 'files': len(rows), 'bytes': sum(row['bytes'] for row in rows)}


def aliases(base, index_name, original_source_key):
    global source_aliases
    index = load(base / index_name)
    rows = index['files']
    for row in rows:
        stored = read(member(base, row['path']))
        need(len(stored) == row['stored_bytes'] and sha(stored) == row['stored_sha256'], 'Stored alias mismatch')
        need(row['encoding'] in ('gzip', 'identity'), 'Unknown encoding')
        raw = gzip.decompress(stored) if row['encoding'] == 'gzip' else stored
        need(len(raw) == row['raw_bytes'] and sha(raw) == row['raw_sha256'], 'Raw alias mismatch')
        need(raw == read(Path(row[original_source_key])), 'Original source mismatch')
    source_aliases += len(rows)
    return len(rows)


def main():
    global json_docs, gzip_streams
    packets = {}
    for name, index in TARGETS.items():
        base = ROOT / 'experiments' / name
        packets[name] = manifest(base, index)
        for path in sorted(p for p in base.rglob('*') if p.is_file()):
            need(path.suffix.lower() not in MEDIA_SUFFIXES, 'Private/media artifact suffix')
            need('PRIVATE_ORACLE' not in path.name and 'INPUT_LOCK' not in path.name, 'Private native fixture/lock copied')
            raw = read(path)
            if path.suffix == '.gz':
                raw = gzip.decompress(raw); gzip_streams += 1
                if path.name.endswith('.json.gz'):
                    scan(json.loads(raw)); json_docs += 1
            elif path.suffix == '.json':
                scan(json.loads(raw)); json_docs += 1
        need(sha(read(base / index)) == packets[name]['index_sha256'], 'Index changed mid-audit')

    py = ROOT / 'experiments/source_0x31_candidate_20261115'
    gd = ROOT / 'experiments/source_0x31_godot_candidate_20261115'
    # The original immutable INDEX predates its separately outer-indexed
    # FREEZE marker. Verify original payloads and admit exactly that marker.
    manifest(py / 'attempt1-original', 'INDEX.json', exact=False)
    original_index = load(py / 'attempt1-original/INDEX.json')
    original_members = {row['path'] for row in original_index['files']} | {'INDEX.json', 'FREEZE.json'}
    need({path.relative_to(py / 'attempt1-original').as_posix() for path in
          (py / 'attempt1-original').rglob('*') if path.is_file()} == original_members,
         'Unexpected frozen-original member')
    original_failure = load(py / 'root-zero-cone-failure.json')
    need(original_failure['cases'] == 1000 and original_failure['failures'] == 104, 'Original zero-cone failure not retained')
    need(sha(read(py / 'candidate.py')) == 'dd472f2b4de64adebc83a03c2e812ac2e14805c752b220c26c53dd58bf99519c', 'Current corrected math source changed')
    need(sha(read(gd / 'candidate.gd')) == '14053abf4b00c50909468d41372ce77c826bf0ec0b895bec19418a5961b4fae3', 'GDScript source changed')
    need(sha(read(gd / 'harness.gd')) == '284944cd8ba0b876e09bbab0f86bd359d9446c6ff0ec2969fc8ec0747b1011fa', 'Harness source changed')
    need(sha(read(gd / 'PUBLIC_SYNTHETIC_ORACLE.json')) == 'd131028f688711c7bc669eeeac04255a87a763e55fcda7e76b3337763bf976df', 'Synthetic oracle changed')

    archive = ROOT / 'experiments/resume_archive_20261115'
    archived_aliases = aliases(archive, 'INDEX.json', 'source')
    need(archived_aliases == 16, 'Old metadata count drift')
    review = ROOT / 'experiments/sfm_review_actual_20261115'
    review_aliases = aliases(review, 'PAYLOAD_INDEX.json', 'source')
    need(review_aliases == 61, 'Actual review metadata count drift')
    review_benchmark = load(review / 'BENCHMARK.json')
    need(review_benchmark['passed'] and review_benchmark['checks'] == 180 and review_benchmark['check_split'] == [44, 46, 49, 41], 'Review benchmark drift')
    need(review_benchmark['private_jobs'] == 4 and all(review_benchmark['preservation'].values()) and
         review_benchmark['first_validation_status'].startswith('FAILED_'), 'Actual review/failed history lost')

    full = ROOT / 'experiments/windows_bone_binding_full_actual_20261115'
    full_benchmark = load(full / 'BENCHMARK.json')
    full_proof = load(full / 'SOURCE_PROOF.json')
    full_index = manifest(full / 'full', 'INDEX.json')
    need(full_index['files'] == full_benchmark['original_payload_files'] == 468 and full_index['index_sha256'] ==
         full_benchmark['original_INDEX_sha256'] == full_proof['original_INDEX_sha256'], 'Full original packet cross-link')
    need(full_benchmark['passed'] and full_benchmark['functional_source_files'] == 1008 and
         full_benchmark['named_result_groups'] == 157 and full_benchmark['core_process_groups'] == 36 and
         full_benchmark['root_movie_metadata_groups'] == 21 and full_benchmark['private_jobs'] == 192 and
         full_benchmark['normal_exit0'] == 191 and full_benchmark['registered_Krita_cancellation_exit2'] == 1,
         'Full result scope mismatch')

    ready = ROOT / 'experiments/native_runtime_readiness_actual_20261115'
    proof = load(ready / 'SOURCE_PROOF.json')
    bench = load(ready / 'BENCHMARK.json')
    for row in proof['actual_metadata_sources']:
        source = read(ROOT / row['source'])
        copied = read(member(ready, row['stored']))
        need(source == copied and len(source) == row['bytes'] and sha(source) == row['sha256'], 'Readiness metadata source/copy mismatch')
    for row in proof['source_and_case_references_only']:
        raw = read(ROOT / row['source'])
        need(len(raw) == row['bytes'] and sha(raw) == row['sha256'], 'Readiness source-code cross-link')
    need(proof['math_source_packet_INDEX_sha256'] == sha(read(gd / 'INDEX.json')), 'GDScript packet index cross-link')
    need(bench['FK']['passed'] and bench['FK']['checks'] == 41588 and bench['FK']['configurations'] == 220 and
         bench['standalone_math']['passed'] and bench['standalone_math']['checks'] == 8994 and
         bench['standalone_math']['candidate_sha256'] == sha(read(gd / 'candidate.gd')) and
         bench['standalone_math']['harness_sha256'] == sha(read(gd / 'harness.gd')) and
         bench['standalone_math']['public_synthetic_oracle_sha256'] == sha(read(gd / 'PUBLIC_SYNTHETIC_ORACLE.json')) and
         bench['application_solver_integrated'] is False, 'Runtime readiness scope drift')

    candidates = load(archive / 'DUPLICATE_PUBLIC_PREPARATION_CANDIDATES.json')
    need(len(candidates['files']) == candidates['count'] == 46 and candidates['bytes'] == 558431 and
         candidates['cleanup_authorized'] is False and candidates['recursive_removal_allowed'] is False, 'Candidate-scope drift')
    rows = []
    for row in candidates['files']:
        source = Path(row['literal_path'])
        backup = ROOT / row['backing_path']
        need(source.resolve().is_relative_to(ROOT / 'output') and backup.resolve().is_relative_to(ROOT / 'experiments'), 'Candidate outside owned/public boundaries')
        raw = read(source); backed = read(backup)
        need(raw == backed and len(raw) == row['bytes'] and sha(raw) == row['sha256'], 'Duplicate current bytes changed')
        info = source.stat()
        current = [info.st_size, info.st_mtime_ns, info.st_dev, info.st_ino, info.st_nlink, getattr(info, 'st_file_attributes', 0)]
        need(current == row['stat_size_mtime_dev_ino_nlink_attrs'], 'Duplicate file identity/stamp changed')
        rows.append({'literal_path': str(source), 'backup': row['backing_path'], 'bytes': len(raw),
                     'sha256': sha(raw), 'local_bytes_and_recorded_stamp_equal': True})

    result = {'format': 'has_independent_prepublication_packet_audit_1', 'passed': True,
        'checked_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'packets': packets,
        'packet_count': len(packets), 'JSON_documents_privacy_scanned': json_docs,
        'gzip_streams_decompressed': gzip_streams, 'source_aliases_roundtripped': source_aliases,
        'cross_links': {'original_zero_cone_failure_preserved': True, 'corrected_Python_source': sha(read(py / 'candidate.py')),
                       'full_157_36_21_192_scope': True, 'review_180_4_9_scope': True,
                       'FK_41588_220_and_math8994_separate': True, 'native_solver_product_integrated': False,
                       'preparation_UNRUN_labels_are_historical_not_current_runtime_claims': True},
        'public_duplicate_candidates': {'count': 46, 'bytes': sum(row['bytes'] for row in rows),
            'local_backing_bytes_and_stamps_verified': True, 'candidate_files': rows,
            'recorded_backing_revision': 'f0dd57a2e568089d396fecba819ab987da658bf0',
            'Git_or_remote_verification_performed': False, 'current_dependency_or_nonuse_established': False,
            'cleanup_authorized': False, 'recursive_removal_authorized': False,
            'verdict': 'RETAIN_PENDING_ROOT_REMOTE_RETRIEVAL_DEPENDENCY_NONUSE_AND_LITERAL_FILE_DECISION'},
        'publication_blockers': [], 'cleanup_remaining_gates': ['Remote retrieval verification',
            'Fresh active dependency/nonuse evidence', 'Separate root-reviewed exact literal-file decision'],
        'private_payloads_found': False, 'apps_tests_parsers_processes_Git_network_or_deletion': False,
        'native_roots_1442187088bytes_outside_duplicate_scope': True, 'reclaimed_bytes': 0,
        'auditor_source_sha256': sha(read(Path(__file__)))}
    path = OUT / 'audit_public_packets_independent.json'
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'passed': True, 'packets': len(packets), 'physical_files': sum(row['files'] for row in packets.values()),
                      'JSON_documents': json_docs, 'gzip_streams': gzip_streams, 'aliases': source_aliases,
                      'duplicate_candidate_files': 46, 'duplicate_bytes': 558431,
                      'publication_blockers': [], 'cleanup_authorized': False, 'receipt_sha256': sha(read(path))}))


if __name__ == '__main__':
    main()
