"""Pin known public source only. Never reads any native or run output path."""
import ast
import hashlib
import io
import json
from pathlib import Path
import re
import unittest

import test_projection

HERE = Path(__file__).resolve().parent
MAIN = HERE.parents[1]
REVIEW = MAIN.parent / 'has-neon-review-20261116-c2d52ff'
PATHS = {
    'MAIN': [
        'experiments/neon_00bf_terminal_20261117/close_terminal.py',
        'experiments/neon_00bf_terminal_20261117/legacy_result_gates.py',
        'experiments/neon_00bf_terminal_20261117/RESULT_REGISTRY.json',
        'experiments/neon_00bf_terminal_20261117/INDEX.json',
        'experiments/native_five_full_actual_20261116/packaging-attempt1/build_packet.py',
        'experiments/native_five_full_actual_20261116/RESULT_EXTRACT.json',
        'experiments/native_five_full_actual_20261116/verify_packet.py',
    ],
    'REVIEW': [
        'tests/verify.py', 'tests/verify_neon_workspace.py',
        'tests/neon_inset_scene_regression.gd', 'tests/neon_behavior_regression.gd',
        'tests/neon_compact_timeline_reveal_smoke.gd', 'tests/neon_rail_placement_smoke.gd',
        'tests/neon_world_rail_lifecycle.gd', 'tools/private_desktop.py',
    ],
}


def sha(raw): return hashlib.sha256(raw).hexdigest()


def save(name, value):
    with (HERE / name).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, indent=2, allow_nan=False); f.write('\n')


def sources():
    result = {}
    for alias, names in PATHS.items():
        root = MAIN if alias == 'MAIN' else REVIEW
        for name in names:
            path = root / name
            for item in (path, *path.parents):
                assert not item.is_symlink() and not getattr(item.lstat(), 'st_file_attributes', 0) & 0x400
            assert path.is_file() and path.stat().st_size <= 2 * 1024 * 1024
            before = path.stat(); raw = path.read_bytes(); after = path.stat()
            assert (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns)
            result[alias + ':' + name] = (raw, {'bytes': len(raw), 'sha256': sha(raw)})
    return result


def main():
    assert not (HERE / 'INDEX.json').exists(), 'Sealed preparation is immutable'
    before = sources()
    registry = json.loads(before['MAIN:experiments/neon_00bf_terminal_20261117/RESULT_REGISTRY.json'][0])
    verifier = before['REVIEW:tests/verify.py'][0]
    assert sha(verifier) == registry['verifier_sha256']
    assert [len(registry[k]) for k in ('expected_result_keys', 'expected_core_process_keys', 'expected_movie_keys')] == [158, 36, 21]
    wrapper = before['REVIEW:tests/verify_neon_workspace.py'][0].decode('utf-8-sig')
    assignments = [n for n in ast.parse(wrapper).body if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == 'CASES' for t in n.targets)]
    assert len(assignments) == 1
    cases = ast.literal_eval(assignments[0].value)
    assert {r[0]: r[3] for r in cases} == test_projection.P.COUNTS
    assert sum(r[3] for r in cases) == 12504
    behavior = before['REVIEW:tests/neon_behavior_regression.gd'][0].decode('utf-8-sig')
    behavior_names = re.findall(r'check\("([^"\n]+)"', behavior)
    assert len(behavior_names) == len(set(behavior_names)) == 32
    text = verifier.decode('utf-8-sig')
    assert '(output / "verification.json").write_text(json.dumps(results, indent=2)' in text
    assert 'print(json.dumps(results, indent=2))' in text
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromModule(test_projection))
    save('CPU_RECEIPT.json', {'format': 'has_successful_full_projection_synthetic_cpu_1',
        'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
        'passed': result.wasSuccessful(), 'stdout': stream.getvalue(),
        'actual_full_reports_or_native_inputs_read': False})
    assert result.wasSuccessful() and result.testsRun == 14
    after = sources()
    assert before == after
    save('SOURCE_PROFILE.json', {'format': 'has_successful_full_projection_source_profile_1',
        'qualification': 'PUBLIC_SOURCE_ONLY_NO_ACTUAL_RUN_OUTPUTS_READ',
        'sources': {name: value[1] for name, value in before.items()},
        'functional_code_modified': False,
        'registry_counts': {'groups': 158, 'core': 36, 'movies': 21},
        'neon_counts': {r[0]: r[3] for r in cases},
        'behavior_names': sorted(behavior_names),
        'source_unchanged_across_CPU_tests': True,
        'future_archive_activation_available': False,
        'private_full_validator_and_closed_inventory_required': True,
        'actual_run_report_log_native_output_CIM_engine_remote_Git_access': False,
        'known_published_52_full_scalar_extract_read_as_public_reference': True})
    files = []
    for path in sorted(HERE.iterdir(), key=lambda p: p.name.lower()):
        assert path.is_file()
        raw = path.read_bytes(); files.append({'path': path.name, 'bytes': len(raw), 'sha256': sha(raw)})
    save('INDEX.json', {'format': 'has_source_experiment_index_1', 'packet': HERE.name,
        'status': 'SEALED_SOURCE_ONLY_EXPLICIT_PROJECTION_ACTUAL_ARCHIVE_UNAVAILABLE', 'files': files})
    print(json.dumps({'passed': True, 'source_files': len(before), 'CPU_methods': result.testsRun,
                     'INDEX_sha256': sha((HERE / 'INDEX.json').read_bytes())}))


if __name__ == '__main__': main()
