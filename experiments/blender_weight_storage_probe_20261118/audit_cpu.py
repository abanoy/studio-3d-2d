"""Exclusive source-only audit and CPU fakes. Does not import or run Blender."""
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PINS = {
    'output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647/blender_bindings/models/mdl49/import_mdl.py':
        '173a34ecae50e0b7a9d467908f238c02d5d7e19df3c7f52387534914d703233b',
    'output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647/blender_bindings/models/common.py':
        '2522f2a451f082edcfcf66c3b445782716e24feb45f8b43d5d6e459f6408f750',
    'output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647/blender_bindings/utils/fast_mesh.py':
        'ece5c47ac13eb5885bdc7c5b415784a6c7ea3ecc76d13c620bb561ca9c30058a',
    'tools/private_desktop.py': '9788e7fde42de7bce022589c86146eaa93deb142ef368aa37a05259ec3047628',
    'experiments/replay_audio_fix_20261115/builder/input-lock.json':
        '3bb7c2ce75f55dcb53143aab0df5ab8b39c68180617092664a579126fb09cfb6',
    'experiments/native_point_expectation_bone_state_fix_20261118/INDEX.json':
        '4afdadb1fbbbf44216b9c3c0d7736efc293c7717eb8908e7eb219b7af094c7c8',
    'experiments/native_point_expectation_bone_state_fix_20261118/native_point_expectation.py':
        'cbb4eca98a6cf5045211dc10bd8e060b79492ec306d61a4d29679fc0d5cc184d',
    'experiments/native_point_expectation_bone_state_actual_20261118/RESULT.json':
        '36dac1dbc6a9218c0cf291cb38c05342d49f01e46c606961d0218544b63e9612',
}


def identity(path):
    before = path.stat(); raw = path.read_bytes(); after = path.stat()
    assert (before.st_size, before.st_mtime_ns, before.st_ino) == (after.st_size, after.st_mtime_ns, after.st_ino)
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def check_pins():
    result = {}
    for name, expected in PINS.items():
        row = identity(ROOT / name); assert row['sha256'] == expected, name
        result[name] = row
    return result


def write_new(name, value):
    with (HERE / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, allow_nan=False); stream.write('\n')


def main():
    expected = {'weight_storage_contract.py', 'blender_weight_storage_probe.py', 'test_weight_storage_probe.py',
                'audit_cpu.py', 'README.md', 'SOURCE_DERIVATION.json', 'PEER_REVIEW.md'}
    assert {path.name for path in HERE.iterdir()} == expected, 'Fresh source-only packet required'
    before = check_pins()
    source_before = {name: identity(HERE / name) for name in sorted(expected)}
    captured = io.StringIO()
    with redirect_stdout(captured), redirect_stderr(captured):
        suite = unittest.defaultTestLoader.discover(str(HERE), pattern='test_weight_storage_probe.py')
        result = unittest.TextTestRunner(stream=captured, verbosity=2).run(suite)
    assert result.wasSuccessful() and result.testsRun == 11, captured.getvalue()
    assert 'bpy' not in sys.modules, 'Native module unexpectedly imported by CPU audit'
    assert check_pins() == before
    assert {name: identity(HERE / name) for name in sorted(expected)} == source_before
    from weight_storage_contract import cases, case_digest
    report = {'format': 'has_synthetic_weight_storage_probe_source_CPU_audit_1',
              'utc': datetime.now(timezone.utc).isoformat(), 'status': 'CPU_FAKE_PASS_NATIVE_UNRUN',
              'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
              'source_pins_before_after': before, 'packet_sources_before_after': source_before,
              'finite_cases': 21952, 'positive_add_calls': 47040, 'group_count': 69,
              'case_catalogue_sha256': case_digest(cases()), 'test_output': captured.getvalue(),
              'original_native_arrays_models_or_art_read': False, 'native_Blender_SourceIO_or_export_run': False,
              'Git_network_installs_or_process_queries_used': False, 'window_or_desktop_API_called': False,
              'all_runtime6_SourceIO574_exporter120_or_1029_source_rechecked': False,
              'Root_native_launcher_or_fresh_request_created': False, 'expired_admission_reused': False,
              'native_storage_or_universal_F32_policy_qualified': False,
              'native_fidelity_export_repair_adoption_qualified': False}
    write_new('CPU_VALIDATION.json', report)
    write_new('INDEX.json', {'format': 'has_synthetic_weight_storage_probe_source_packet_index_1',
                            'status': 'SOURCE_CPU_READY_ROOT_NATIVE_UNRUN',
                            'files': {path.name: identity(path) for path in sorted(HERE.iterdir()) if path.is_file()}})
    print(json.dumps({'tests': result.testsRun, 'failures': 0, 'errors': 0,
                      'source_pins': len(PINS), 'index': identity(HERE / 'INDEX.json'), 'native_run': False}))


if __name__ == '__main__':
    main()
