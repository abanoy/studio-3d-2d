"""Audit completed backup/protection metadata only; never open old candidate roots."""
from pathlib import Path
import collections
import datetime
import gzip
import hashlib
import io
import json
import re

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
A = '4da35573655c799c521f5f7460af76b2bd8de533'
F = 'f0dd57a2e568089d396fecba819ab987da658bf0'
OLD = '8d4fde001258f501602bd94bd80d925683062f15'
INPUTS = {
    'increment': ROOT / 'output/remote-new-increment-20261115.json',
    'recovery': ROOT / 'output/remote-old-recovery-20261115.json',
    'protection': ROOT / 'output/old-native-protection-refresh-20261115/protected-inputs-fresh.json'}
PROOFS = []


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def oid(raw):
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def read(path):
    # All call sites are completed output JSON or public experiments metadata.
    # No path is taken from a native-root inventory for a filesystem read.
    assert not path.is_relative_to(ROOT / 'output/source-choices-native')
    raw = path.read_bytes()
    PROOFS.append({'path': str(path), 'bytes': len(raw), 'sha256': sha(raw)})
    return raw


def load(path):
    return json.loads(read(path))


def utc(value):
    return datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))


def save(name, value):
    with (HERE / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2); stream.write('\n')


def main():
    actual_raw = {name: read(path) for name, path in INPUTS.items()}
    reports = {name: json.loads(raw) for name, raw in actual_raw.items()}
    new, old, protected = (reports[name] for name in ('increment', 'recovery', 'protection'))
    assert new['format'] == 'has_exact_github_increment_readback_1'
    assert new['passed'] is True and new['base_commit'] == F and new['remote_main_commit'] == A
    assert new['files'] == len(new['remote_files']) == 1095 and new['raw_bytes'] == 15135622
    new_rows = {row['path']: row for row in new['remote_files']}
    assert len(new_rows) == 1095 and sum(row['bytes'] for row in new_rows.values()) == new['raw_bytes']
    for row in new_rows.values():
        assert row['remote_bytes_equal'] is True and 1 <= row['attempts'] <= 3
        assert re.fullmatch('[0-9a-f]{64}', row['sha256']) and re.fullmatch('[0-9a-f]{40}', row['git_blob'])
        assert 0 <= row['bytes'] <= 8 * 1024 * 1024
    catalogue_path = 'experiments/windows_bone_binding_full_actual_20261115/full/canonical/source-before.json.gz'
    catalogue_raw = gzip.decompress(read(ROOT / catalogue_path))
    assert sha(catalogue_raw) == '8d9e7d94c745081e0ca084bc64e7498bc7ccb218c44209e1354bcd53f3c50a2a'
    catalogue = json.loads(catalogue_raw)
    assert catalogue['commit'] == F and len(catalogue['source_sha256']) == 1008
    catalogue_pin = new['tested_source_catalogue']
    assert catalogue_pin['path'] == catalogue_path and catalogue_pin['raw_sha256'] == sha(catalogue_raw)
    assert catalogue_pin['git_blob_bytes'] == new_rows[catalogue_path]['bytes']
    assert catalogue_pin['git_blob_sha256'] == new_rows[catalogue_path]['sha256']
    lock_path = 'experiments/source_0x31_native_leaf_20261115/SOURCE_LOCK.json'
    lock_raw = read(ROOT / lock_path)
    lock = json.loads(lock_raw)
    assert lock['source_HEAD_context'] == F and len(lock['files']) == 200
    assert sha(lock_raw) == catalogue_pin['leaf_source_lock_sha256'] == new_rows[lock_path]['sha256']
    extras = {row['path']: row for row in lock['files']}
    extras.update({name: {'path': name, 'sha256': catalogue['source_sha256'][name]}
                   for name in ('data/bone_names.en.json', 'data/discovery_sources.json', 'data/shape_names.en.json')})
    assert len(extras) == new['unchanged_leaf_source_support_files'] == 203
    assert {name for name, row in new_rows.items() if 'reconstruction' in row} == set(extras)
    recipes = collections.Counter()
    for name, pin in extras.items():
        row = new_rows[name]
        assert row['tested_sha256'] == pin['sha256'] == catalogue['source_sha256'][name]
        assert row['remote_git_sha256'] == row['sha256'] and row['remote_git_bytes'] == row['bytes']
        assert row['remote_tested_source_reconstruction_equal'] is True
        assert row['reconstruction'] in ('exact', 'LF_to_CRLF')
        assert 'bytes' not in pin or row['tested_bytes'] == pin['bytes']
        if row['reconstruction'] == 'exact':
            assert row['tested_sha256'] == row['sha256'] and row['tested_bytes'] == row['bytes']
        else:
            assert row['tested_sha256'] != row['sha256'] and row['tested_bytes'] > row['bytes']
        recipes[row['reconstruction']] += 1
    assert recipes == new['tested_source_reconstruction_recipes'] == {'exact': 40, 'LF_to_CRLF': 163}
    checker_names = ['verify_remote_increment.py', 'verify_old_recovery_remote.py',
                     'audit_protected_inputs_before_cleanup.py']
    checker_hashes = {}
    for name in checker_names:
        relative = 'experiments/resume_root_20261115/' + name
        raw = read(ROOT / relative)
        assert new_rows[relative]['sha256'] == sha(raw)
        checker_hashes[name] = sha(raw)

    plan_path = 'experiments/resume_root_20261115/old_native_recovery_plan.json'
    plan_raw = read(ROOT / plan_path)
    assert sha(plan_raw) == '194ccde44c5d78f20832c7837b5d61ac4de8557524c69c9c3d87a2c24e9b29c5'
    plan = json.loads(plan_raw)
    packet = 'experiments/source_appearance/main_native_app_actual_20261113/'
    index_path = packet + 'INDEX.json'
    index = load(ROOT / index_path)
    assert len(index['files']) == 506
    inventories = {}
    for phase in ('core14', 'wider11'):
        relative = 'experiments/resume_archive_20261115/historical-cleanup-audit/' + phase + '-fresh-inventory.json.gz'
        parsed = json.loads(gzip.decompress(read(ROOT / relative)))
        inventories[phase] = {row['path']: row for row in parsed['files']}
    assert old['format'] == 'has_exact_old_native_recovery_remote_readback_1'
    assert old['passed'] is True and old['publication_commit'] == A and old['source_commit'] == OLD
    assert old['checker_sha256'] == checker_hashes['verify_old_recovery_remote.py']
    assert old['origin_main_exact_at_start'] is True and not old['errors']
    assert old['read_only_Git_operations'] is True and old['Git_mutation'] is False
    assert old['cleanup_authorized'] is False and old['payloads_saved_to_disk'] is False
    assert (old['maximum_workers'], old['socket_timeout_seconds'], old['attempts_per_file']) == (8, 20, 3)
    assert old['maximum_file_bytes'] == 8388608 and old['maximum_total_local_payload_bytes'] == 33554432
    assert len(old['prerequisites']) == 5
    for row in old['prerequisites']:
        raw = read(ROOT / row['path'])
        assert row['remote_bytes_equal'] is True and 1 <= row['attempts'] <= 3
        assert (len(raw), sha(raw), oid(raw)) == (row['bytes'], row['sha256'], row['git_blob_oid'])
    assert len(old['remote_files']) == 1487
    assert len({(row['commit'], row['path']) for row in old['remote_files']}) == 1487
    source_rows, packet_rows = {}, {}
    for row in old['remote_files']:
        assert row['passed'] is True and row['remote_bytes_equal'] is True
        assert row['git_blob_oid_recomputed_equal'] is True and 1 <= row['attempts'] <= 3
        assert 0 <= row['bytes'] <= 8388608
        assert re.fullmatch('[0-9a-f]{64}', row['sha256']) and re.fullmatch('[0-9a-f]{40}', row['git_blob_oid'])
        if row['kind'] == 'historical_source':
            assert row['commit'] == OLD
            source_rows[row['path']] = row
        else:
            assert row['kind'] == 'public_packet' and row['commit'] == A
            packet_rows[row['path']] = row
    assert len(source_rows) == old['historical_unique_source_files'] == 981
    assert len(packet_rows) == old['public_packet_payload_files'] == 506
    assert set(source_rows) == {row['git_path'] for row in plan['snapshot_recovery']['source_files']}
    old_recipes, fixtures = collections.Counter(), []
    for pin in plan['snapshot_recovery']['source_files']:
        row = source_rows[pin['git_path']]
        for name in ('git_blob_oid', 'reconstruction', 'restored_bytes', 'restored_sha256', 'public_builtin_fixture'):
            assert row[name] == pin[name]
        assert row.get('crlf_newline_ordinals') == pin.get('crlf_newline_ordinals')
        assert row['snapshot_restorations_verified'] == 2
        for phase in inventories:
            expected = inventories[phase][pin['restore_relative_path']]
            assert expected['bytes'] == row['restored_bytes'] and expected['sha256'] == row['restored_sha256']
        old_recipes[row['reconstruction']] += 1
        if row['public_builtin_fixture']:
            fixtures.append({'path': row['path'], 'restored_bytes': row['restored_bytes']})
    assert old_recipes == {'exact_git_blob': 196, 'git_blob_LF_to_CRLF': 783, 'git_blob_selected_LF_to_CRLF': 2}
    assert sum(row['snapshot_restorations_verified'] for row in source_rows.values()) == old['snapshot_files_reconstructable'] == 1962
    assert len(fixtures) == old['public_builtin_fixture_files'] == 6
    assert sum(row['restored_bytes'] for row in fixtures) == old['public_builtin_fixture_restored_bytes'] == 175666
    assert set(packet_rows) == {packet + row['path'] for row in index['files']}
    for pin in index['files']:
        row = packet_rows[packet + pin['path']]
        assert (row['bytes'], row['sha256']) == (pin['bytes'], pin['sha256'])
    expected_joins = {(row['phase'], row['restore_relative_path']): row for row in plan['metadata_recovery']['joins']}
    observed_joins = {}
    for row in packet_rows.values():
        for join in row['metadata_restorations']:
            key = (join['phase'], join['restore_relative_path'])
            assert key not in observed_joins and join['exact_inventory_match'] is True
            pin = expected_joins[key]
            assert row['path'] == pin['public_path_at_commitA']
            assert all(join[name] == pin[name] for name in ('reconstruction', 'restored_bytes', 'restored_sha256'))
            expected = inventories[join['phase']][join['restore_relative_path']]
            assert join['restored_bytes'] == expected['bytes'] and join['restored_sha256'] == expected['sha256']
            observed_joins[key] = join
    assert len(observed_joins) == len(expected_joins) == old['exact_metadata_joins'] == 44
    total = sum(row['bytes'] for row in old['remote_files'] + old['prerequisites'])
    assert total == old['expected_remote_payload_bytes'] == 14225344 and total <= 33554432

    assert protected['format'] == 'has_protected_inputs_fresh_readonly_proof_1' and protected['passed'] is True
    assert protected['source_commit'] == F
    assert protected['actual_metadata_source_code_sha256'] == checker_hashes['audit_protected_inputs_before_cleanup.py']
    assert (protected['originals']['families'], protected['originals']['files'], protected['originals']['bytes']) == (5, 561, 469130387)
    assert (protected['originals']['current_review_files'], protected['originals']['additional_Kanako_files']) == (495, 66)
    assert protected['originals']['all_historical_identity_fields_match'] and protected['originals']['regular_single_link']
    assert (protected['shared_runtime_executables'], protected['original_SourceIO_files'], protected['installed_exporter_noncache_sources'],
            protected['current_review']['shipped_files'], protected['functional_source_files']) == (6, 574, 120, 5844, 1008)
    assert Path(protected['current_review']['root']) == ROOT.parent / 'HAS-Review-20261115-SFM-Joints-f0dd57a-replay2'
    assert protected['current_review']['excluded_runtime_generated_subtrees'] == ['Studio/output', 'Studio/.godot']
    assert protected['current_review']['historical_size_mtime_SHA256_and_exact_membership_match']
    assert protected['all_sources_current_exact_SHA256'] and protected['no_reparse_ancestors_and_stable_regular_reads']
    assert protected['cleanup_authorized'] is False and protected['originals_or_tools_modified'] is False
    for pin in protected['frozen_maps'].values():
        raw = read(Path(pin['path']))
        assert len(raw) == pin['bytes'] and sha(raw) == pin['sha256']
        restored = gzip.decompress(raw) if pin['path'].endswith('.gz') else raw
        assert len(restored) == pin['raw_bytes'] and sha(restored) == pin['raw_sha256']
    assert utc(old['started_utc']) <= utc(old['finished_utc'])
    assert abs((utc(old['finished_utc']) - utc(old['started_utc'])).total_seconds() - old['seconds']) < 1
    assert max(utc(new['observed_utc']), utc(old['finished_utc'])) <= utc(protected['started_utc'])
    assert utc(protected['started_utc']) <= utc(protected['finished_utc']) <= datetime.datetime.now(datetime.timezone.utc)
    copies = []
    for name, raw in actual_raw.items():
        compressed = io.BytesIO()
        with gzip.GzipFile(filename='', mode='wb', fileobj=compressed, mtime=0, compresslevel=9) as stream:
            stream.write(raw)
        payload = compressed.getvalue()
        assert gzip.decompress(payload) == raw
        path = HERE / (name + '.json.gz')
        with path.open('xb') as stream:
            stream.write(payload)
        copies.append({'source': str(INPUTS[name]), 'source_bytes': len(raw), 'source_sha256': sha(raw),
                       'stored': path.name, 'stored_bytes': len(payload), 'stored_sha256': sha(payload),
                       'decompressed_bytes_exact': True})
    audit = {'format': 'has_completed_backup_protection_independent_metadata_audit_1', 'passed': True,
             'checked_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'publication_commit': A,
             'scope': 'Completed remote increment/recovery/protection report metadata only. Candidate old roots were never opened.',
             'increment': {'files': 1095, 'raw_bytes': 15135622, 'seconds': new['seconds'], 'extras': 203,
                           'source_reconstruction_recipes': dict(recipes), 'finished_utc': new['observed_utc']},
             'recovery': {'jobs': 1487, 'prerequisites': 5, 'public_packet_payload_files': 506,
                          'historical_unique_source_files': 981, 'snapshot_restorations': 1962, 'metadata_joins': 44,
                          'reconstruction_recipes': dict(old_recipes), 'public_builtin_fixture_files': 6,
                          'public_builtin_fixture_bytes': 175666, 'payload_bytes': 14225344,
                          'started_utc': old['started_utc'], 'finished_utc': old['finished_utc'], 'seconds': old['seconds']},
             'preservation': {'original_files': 561, 'original_bytes': 469130387, 'review_shipped_files': 5844,
                              'shared_runtime_executables': 6, 'SourceIO_files': 574, 'exporter_sources': 120,
                              'functional_source_files': 1008, 'started_utc': protected['started_utc'],
                              'finished_utc': protected['finished_utc'], 'started_after_both_remote_readbacks': True},
             'all_per_file_and_metadata_join_claims_match_pinned_plans_and_source_predicates': True,
             'checker_source_sha256': checker_hashes, 'copies': copies,
             'source_metadata_proofs': sorted({row['path']: row for row in PROOFS}.values(), key=lambda row: row['path']),
             'new_network_or_Git_or_process_queries_or_runtime_launched': False,
             'candidate_root_file_reads_or_hashes_or_opens': False,
             'cleanup_authorized': False, 'cleanup_or_current_probe_result_claimed': False,
             'limits': 'This checks completed reports and their exact source/map bindings. It does not repeat remote retrieval, asset hashing, candidate sharing, ownership observation or cleanup. Root decides after actual probe/BeforeRemoval ownership evidence.'}
    save('AUDIT.json', audit)
    note = ('# Actual backup and preservation metadata audit\n\n'
            'Passed for publication `' + A + '`. The completed increment report has1,095 exact remote files/15,135,622 bytes, including203 reconstructed source/support records (40exact,163LF→CRLF). The separate old recovery report has1,487 successful file jobs:506 public packet payloads and981 unique historical source files, proving1,962 snapshot restorations and44 exact metadata joins. Its six explicitly allowed public fixtures total175,666 bytes.\n\n'
            'The fresh preservation interval00:55:12.424730–00:55:41.558012 UTC begins after both remote readbacks completed. Counts match the reviewed guards:561 originals,5,844 shipped review files,6 runtime executables,574 SourceIO files,120 exporter sources and1,008 functional source files. All per-file claims, plans, source hashes, map pins and recorded time predicates matched.\n\n'
            'Only completed metadata was read. Both old candidate roots, the running sharing probe and current processes were untouched. This audit does not authorize or claim cleanup. Three deterministic gzip copies preserve the exact completed reports without media or model payloads.\n')
    with (HERE / 'README.md').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(note)
    files = []
    for path in sorted(HERE.iterdir()):
        if path.is_file() and path.name != 'INDEX.json':
            raw = path.read_bytes(); files.append({'path': path.name, 'bytes': len(raw), 'sha256': sha(raw)})
    save('INDEX.json', {'format': 'has_completed_backup_metadata_packet_index_1', 'files': files})
    print(json.dumps({'passed': True, 'index_sha256': sha((HERE / 'INDEX.json').read_bytes()),
                      'audit_sha256': sha((HERE / 'AUDIT.json').read_bytes()), 'indexed_payloads': len(files)}))


if __name__ == '__main__':
    main()
