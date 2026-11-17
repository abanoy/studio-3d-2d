"""Record CPU/artifact results and recheck only the 69 frozen closed inputs.

This does not build an archive, observe processes, invoke Git or read a live run.
The recipe index is written last and existing records are never overwritten.
"""
import hashlib
import io
import json
from pathlib import Path
import unittest

import test_admission
import test_artifact
import verify_packet

HERE = Path(__file__).resolve().parent
EXPECTED_ARTIFACT_INDEX = '5f8ea1352707c02a914c51dd15c984a86c69e16e3199798ae0a988ecd61b34d7'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(name, value):
    with (HERE / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def main():
    assert not (HERE / 'INDEX.json').exists(), 'Sealed recipe is immutable'
    suite = unittest.TestSuite([
        unittest.defaultTestLoader.loadTestsFromModule(test_admission),
        unittest.defaultTestLoader.loadTestsFromModule(test_artifact),
    ])
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    save('CPU_FINAL.json', {
        'format': 'has_catalogue_00bf_archive_final_cpu_1',
        'tests': result.testsRun, 'failures': len(result.failures),
        'errors': len(result.errors), 'passed': result.wasSuccessful(),
        'admission_methods': 15, 'artifact_only_methods': 17,
        'stdout': stream.getvalue(),
        'source_sha256': {name: sha((HERE / name).read_bytes()) for name in (
            'archive_checks.py', 'build_packet.py', 'capture_inputs.py',
            'verify_packet.py', 'test_admission.py', 'test_artifact.py')},
        'engine_CIM_Git_or_upcoming_full_reads': False,
    })
    assert result.wasSuccessful() and result.testsRun == 32

    report = verify_packet.verify()
    assert report['passed'] is True and report['INDEX_sha256'] == EXPECTED_ARTIFACT_INDEX
    assert (report['original_bindings'], report['unique_objects'], report['private_jobs']) == (69, 61, 8)
    save('ARTIFACT_VERIFICATION.json', report)

    spec = json.loads((HERE / 'INPUTS.json').read_bytes())
    assert sha((HERE / 'INPUTS.json').read_bytes()) == verify_packet.INPUTS_SHA
    rows = []
    for row in spec['inputs']:
        path = Path(spec['roots'][row['root']]) / row['path']
        verify_packet.regular(path)
        before = path.stat()
        assert path.is_file() and before.st_size == row['bytes'] <= 2 * 1024 * 1024
        data = path.read_bytes()
        after = path.stat()
        assert (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns) == (row['bytes'], row['mtime_ns'])
        assert sha(data) == row['sha256']
        rows.append({'root': row['root'], 'path': row['path'], 'bytes': len(data), 'sha256': sha(data), 'mtime_ns': after.st_mtime_ns})
    assert len(rows) == 69
    save('ORIGINALS_RECHECK.json', {
        'format': 'has_catalogue_00bf_frozen_closed_originals_recheck_1',
        'passed': True, 'originals': rows,
        'identity_size_and_mtime_exact': True,
        'engine_CIM_Git_or_upcoming_full_reads': False,
        'native_models_media_or_original_native_arrays_read': False,
    })
    save('PEER_OBSERVATION.json', {
        'format': 'has_catalogue_00bf_peer_observation_transcription_1',
        'evidence_kind': 'Legible transcription of sibling messages; not separately captured raw stdout',
        'peer': '/root/review_build_audit',
        'peer_packet': 'experiments/neon_catalogue_00bf_archive_peer_20261117',
        'peer_INDEX_sha256': '8ddd004a55bf1b53daf57d4dde3f0958c9e6fd3bb746d202cfa129c6100cea1c',
        'peer_REPORT_sha256': '9512dac9b0ff9970b07004e305709ee55db5e918d2e06732c478f054032c5f01',
        'source_review_scoped_go': True, 'independent_admission_methods_pass': 15,
        'independent_artifact_methods_pass': 17,
        'actual_artifact_only_verifier_pass': True,
        'actual_tool_chunk': '9c4356',
        'actual_archive_INDEX_sha256': EXPECTED_ARTIFACT_INDEX,
        'observed_original_bindings': 69, 'observed_unique_objects': 61,
        'observed_physical_private_jobs': 8,
        'peer_original_native_active_full_CIM_or_Git_reads': False,
    })
    rows = []
    for path in sorted(HERE.iterdir(), key=lambda p: p.name.lower()):
        assert path.is_file() and path.name != 'INDEX.json', 'Only flat recipe payload files'
        verify_packet.regular(path)
        data = path.read_bytes()
        rows.append({'path': path.name, 'bytes': len(data), 'sha256': sha(data)})
    save('INDEX.json', {
        'format': 'has_source_experiment_index_1',
        'packet': HERE.name,
        'status': 'SEALED_CLOSED_CATALOGUE_ARCHIVE_RECIPE_AND_INDEPENDENT_VERIFIER',
        'files': rows,
        'actual_archive_INDEX_sha256': EXPECTED_ARTIFACT_INDEX,
        'full_suite_pass_claimed': False,
        'native_fidelity_or_main_merge_claimed': False,
    })
    print(json.dumps({'passed': True, 'recipe_INDEX_sha256': sha((HERE / 'INDEX.json').read_bytes()), 'recipe_payload_files': len(rows), 'recipe_payload_bytes': sum(r['bytes'] for r in rows), 'archive_INDEX_sha256': EXPECTED_ARTIFACT_INDEX, 'CPU_methods': result.testsRun, 'originals_rechecked': 69}))


if __name__ == '__main__':
    main()
