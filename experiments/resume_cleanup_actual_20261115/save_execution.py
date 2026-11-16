"""Save whitelisted completed cleanup metadata; never access removed candidates."""
from pathlib import Path
import datetime
import gzip
import hashlib
import io
import json

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
FROZEN = {
    'AUDIT.json': '509f7b6edbfaf43443c7aef8d50783015e6b8f7332ba70100cabf9b0f3a71dff',
    'audit_completed_backup_metadata.py': 'e227092df4048fb6fb72d8c144b16615bb89ec2d62780e345f2b6a279feed151',
    'increment.json.gz': '012cc5ebf67a69d099c1d442e1487ae1b23daa6211af3a75499448ac8d2b4157',
    'INDEX.json': '858347c685d7ea3d53d9b8c850068da2e67e6d3e9d7e2fcda769d024bd2868c1',
    'protection.json.gz': 'd1a6cccf66b75455bb18b50232e240a76d596bb6d9133a712349a245d78bd811',
    'README.md': 'e72f4577b283340bef82d3c6512b4f047c555964c51770baec7127b2b917bd26',
    'recovery.json.gz': 'ac9ae6c1e3b47eb6e8ee3d8c2f9b44f2e468ff21bd05034537a5c65203953064',
}
SOURCES = [
    'output/old-native-root-release-20261115.json',
    *['output/old-native-exclusive-read-20261115_actual/' + name + '.json' for name in
      ['verification', 'inventory-before', 'inventory-after', 'exclusive-open-results', 'root-release']],
    'output/old-native-owner-BeforeProbe-20261115.json',
    'output/old-native-owner-BeforeRemoval-20261115.json',
    'output/old-native-cleanup-decision-20261115.json',
    'output/old-native-cleanup-actual-20261115.json',
    *['output/old-native-protection-refresh-20261115/' + name + '.json' for name in
      ['post-cleanup-attempt1-and-ffprobe-diagnostic',
       'post-cleanup-ffprobe-exact-stamp-diagnostic',
       'protected-inputs-post-cleanup-attempt2']],
]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write(path, raw):
    with path.open('xb') as stream:
        stream.write(raw)


def save(path, value):
    write(path, (json.dumps(value, indent=2, allow_nan=False) + '\n').encode())


def compressed(raw):
    buffer = io.BytesIO()
    with gzip.GzipFile(filename='', mode='wb', fileobj=buffer, compresslevel=9, mtime=0) as stream:
        stream.write(raw)
    return buffer.getvalue()


def metadata_only(value):
    # The actual reports contain file identities, hashes, aggregate flags and
    # diagnostics only. Reject coordinate-shaped numeric arrays or raw payloads.
    if isinstance(value, dict):
        for key, item in value.items():
            assert key not in {'raw_vertices', 'bone_rests', 'native_coordinates',
                               'image_base64', 'audio_base64', 'pcm_bytes', 'geometry_bytes'}
            metadata_only(item)
    elif isinstance(value, list):
        assert not (len(value) >= 3 and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in value))
        for item in value:
            metadata_only(item)


def main():
    for name, expected in FROZEN.items():
        assert sha((HERE / name).read_bytes()) == expected
    assert not (HERE / 'execution').exists()
    raw = {name: (ROOT / name).read_bytes() for name in SOURCES}
    values = {name: json.loads(content) for name, content in raw.items()}
    for value in values.values():
        metadata_only(value)
    prefix = 'output/old-native-exclusive-read-20261115_actual/'
    before = values[prefix + 'inventory-before.json']
    after = values[prefix + 'inventory-after.json']
    assert before == after
    assert sum(len(row['files']) for row in after.values()) == 9307
    assert sum(len(row['directories_including_root']) - 1 for row in after.values()) == 1537
    assert sum(v['bytes'] for row in after.values() for v in row['files'].values()) == 1442187088
    opened = values[prefix + 'exclusive-open-results.json']
    assert len(opened) == 9307 and len({(row['phase'], row['path']) for row in opened}) == 9307
    for row in opened:
        expected = after[row['phase']]['files'][row['path']]
        assert row['opened'] and row['closed'] and row['identity_equal'] and row['regular_no_reparse']
        assert row['identity']['bytes'] == expected['bytes']
        assert row['identity']['mtime_ns'] == expected['mtime_ns']
        assert row['identity']['hardlinks'] == expected['hardlinks'] == 1
        assert row['identity']['file_index'] == expected['stat_inode']
    verification = values[prefix + 'verification.json']
    assert verification['passed'] and verification['files_exclusively_opened_closed_verified'] == 9307
    assert verification['inventories_before_after_identical'] and verification['errors'] == []
    assert verification['cleanup_authorized'] is False
    release_name = 'output/old-native-root-release-20261115.json'
    assert raw[release_name] == raw[prefix + 'root-release.json']
    assert verification['root_release_sha256'] == sha(raw[release_name])
    decision = values['output/old-native-cleanup-decision-20261115.json']
    actual = values['output/old-native-cleanup-actual-20261115.json']
    assert actual['passed'] and actual['removed_roots'] == 2 and actual['fully_removed_files'] == 9307
    assert actual['reclaimed_bytes'] == 1442187088 and actual['failure'] is None
    assert actual['partial_removal_unmeasured'] is False and actual['no_process_killed'] is True
    assert actual['decision_sha256'] == sha(raw['output/old-native-cleanup-decision-20261115.json'])
    assert actual['verified_backup_commit'] == decision['verified_backup_commit'] == '4da35573655c799c521f5f7460af76b2bd8de533'
    for key, pin in decision['evidence'].items():
        path = Path(pin['path'])
        assert sha(path.read_bytes()) == pin['sha256'], key
    for phase in ['BeforeProbe', 'BeforeRemoval']:
        owner = values['output/old-native-owner-' + phase + '-20261115.json']
        assert owner['phase'] == phase and owner['owned_runtime_commands_absent']
        assert owner['exact_old_coordinators_absent'] and owner['no_process_killed']
        assert owner['engine_processes_any_path'] == owner['old_root_argument_processes'] == 0
        assert owner['all_global_nonuse_proven'] is False
    protection_prefix = 'output/old-native-protection-refresh-20261115/'
    failed = values[protection_prefix + 'post-cleanup-attempt1-and-ffprobe-diagnostic.json']
    exact = values[protection_prefix + 'post-cleanup-ffprobe-exact-stamp-diagnostic.json']
    post = values[protection_prefix + 'protected-inputs-post-cleanup-attempt2.json']
    assert failed['prior_post_cleanup_attempt_failed'] and failed['prior_exit'] == 1
    assert exact['passed'] and exact['original_diagnostic_sha256'] == sha(raw[protection_prefix + 'post-cleanup-attempt1-and-ffprobe-diagnostic.json'])
    assert len(exact['rows']) == 3 and all(row['actual_helper_stamp_equal'] and row['sha256_equal'] for row in exact['rows'])
    assert sha(raw[protection_prefix + 'protected-inputs-post-cleanup-attempt2.json']) == 'd2acca7b9f820a8ca6733446162506aedfe747b6e1db1afa8826b22760507a75'
    assert post['passed'] and post['originals']['files'] == 561
    assert post['current_review']['shipped_files'] == 5844 and post['shared_runtime_executables'] == 6
    assert post['original_SourceIO_files'] == 574 and post['installed_exporter_noncache_sources'] == 120
    assert post['functional_source_files'] == 1008 and post['all_sources_current_exact_SHA256']
    assert post['no_reparse_ancestors_and_stable_regular_reads']
    assert post['actual_metadata_source_code_sha256'] == '5be1d34aa6aced8fc112bee3ecadd489be9b7f38ab710553385bfd77ca500d83'
    assert datetime.datetime.fromisoformat(post['started_utc']) > datetime.datetime.fromisoformat(actual['checked_utc'])
    destination = HERE / 'execution'
    destination.mkdir()
    copies = []
    for name, content in raw.items():
        relative = Path(name).relative_to('output').as_posix()
        store = destination / (relative + ('.gz' if len(content) > 65536 else ''))
        store.parent.mkdir(parents=True, exist_ok=True)
        data = compressed(content) if len(content) > 65536 else content
        assert (gzip.decompress(data) if store.suffix == '.gz' else data) == content
        write(store, data)
        copies.append({'source': str(ROOT / name), 'source_bytes': len(content), 'source_sha256': sha(content),
                       'stored': store.relative_to(HERE).as_posix(), 'stored_bytes': len(data),
                       'stored_sha256': sha(data), 'raw_roundtrip_exact': True})
    proof = {'format': 'has_cleanup_execution_exact_source_proof_1', 'passed': True,
             'checked_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'original_frozen_files_sha256': FROZEN, 'copies': copies,
             'inventory_before_after_exact': True, 'exclusive_open_records_joined_to_inventory': 9307,
             'root_release_exact_copies_and_probe_join': True, 'decision_evidence_hashes_verified': len(decision['evidence']),
             'strict_post_attempt2_passed': True, 'first_post_attempt_failed_cause': 'UNDETERMINED',
             'metadata_only': True, 'native_geometry_media_or_payload_bytes_copied': False,
             'removed_candidate_roots_read': False, 'apps_processes_CIM_Git_network_or_deletion_by_exporter': False}
    save(HERE / 'SOURCE_PROOF.json', proof)
    benchmark = {'format': 'has_actual_old_native_cleanup_benchmark_1',
                 'verified_backup_commit': actual['verified_backup_commit'], 'passed': True,
                 'cleanup_checked_utc': actual['checked_utc'], 'removed_roots': 2, 'removed_files': 9307,
                 'removed_directory_descendants': 1537, 'logical_removed_bytes': 1442187088,
                 'physical_allocated_disk_reclamation_measured': False,
                 'exclusive_open_closed_identity_verified_files': 9307,
                 'inventories_before_after_identical': True, 'no_process_killed': True,
                 'originals_tools_newer_reviews_recovery_removed': False,
                 'preservation_before_and_strict_post_attempt2': {'original_files': 561, 'original_bytes': 469130387,
                     'review2_shipped_files': 5844, 'shared_runtime_executables': 6,
                     'original_SourceIO_files': 574, 'installed_exporter_noncache_sources': 120,
                     'functional_source_files': 1008},
                 'post_attempt1': {'status': 'FAILED', 'exit': 1, 'reason': failed['prior_failure'], 'cause': 'UNDETERMINED'},
                 'subsequent_ffprobe_diagnostic': {'exact_helper_domain_stamp_and_approved_hash_checks': 3, 'all_passed': True,
                     'raw_st_mode_difference_explains_first_refusal': 'NOT_ESTABLISHED', 'waiver_or_helper_change': False},
                 'strict_post_attempt2': {'status': 'PASSED', 'started_utc': post['started_utc'], 'finished_utc': post['finished_utc'],
                     'report_sha256': 'd2acca7b9f820a8ca6733446162506aedfe747b6e1db1afa8826b22760507a75'},
                 'discarded_generated_binary_bytes_exactly_backed_up': False,
                 'exact_regeneration_promised': False,
                 'limits': 'Generated test GLB/HAS/frames/audio/movie/import-cache bytes were intentionally not archived as recoverable binaries. Original inputs, source/tool identities, public metadata and newer useful runs remain. Logical removed bytes include copied original inputs and source, not only generated binaries. Read-only ownership/sharing evidence is bounded and does not prove universal nonuse.'}
    save(HERE / 'BENCHMARK.json', benchmark)
    for name, expected in FROZEN.items():
        assert sha((HERE / name).read_bytes()) == expected
    files = []
    for path in sorted(HERE.rglob('*')):
        if path.is_file() and path.name != 'OUTER_INDEX.json':
            content = path.read_bytes()
            files.append({'path': path.relative_to(HERE).as_posix(), 'bytes': len(content), 'sha256': sha(content)})
    save(HERE / 'OUTER_INDEX.json', {'format': 'has_cleanup_actual_outer_index_1', 'files': files,
                                    'preserved_original_index_sha256': FROZEN['INDEX.json']})
    print(json.dumps({'passed': True, 'exact_execution_copies': len(copies), 'outer_payloads': len(files),
                      'outer_bytes': sum(row['bytes'] for row in files),
                      'outer_index_sha256': sha((HERE / 'OUTER_INDEX.json').read_bytes())}))


if __name__ == '__main__':
    main()
