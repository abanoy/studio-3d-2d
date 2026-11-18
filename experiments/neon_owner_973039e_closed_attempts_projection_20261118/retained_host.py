"""Root-owned cold coordinator: existing retained invocation and scope observer."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import sys
import traceback

ROOT = Path(r'C:\a\Programming\cloudflare\has-acceptance-session-20261111')
RUNTIME = ROOT / 'experiments/native_normal_known_factory_blender51_resource_20261117'
PYTHON = r'C:\Program Files\Python313\python.exe'
sys.dont_write_bytecode = True


def load(name, path, pin):
    assert hashlib.sha256(path.read_bytes()).hexdigest() == pin
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validator', type=Path, required=True)
    parser.add_argument('--validator-index-sha256', required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(RUNTIME))
    observer = load('_owner973_scope_observer', RUNTIME / 'root_runner.py',
                    '012bef27696dd2752362426b162bfbd7afe9205febe76c489cd5ccab527648f6')
    owned = load('_owner973_retained_invocation',
                 ROOT / 'experiments/normal_boundary_probe_actual_20261116/run_owned.py',
                 'd6fc7ab7dba85c69658ce01e463f81c95912abbfeb16375e62a34be6db23096b')
    observer.S.packet(RUNTIME, '82727caa443cc58d623463e195fc6220d08c2d878cb93461eb481c722098b6e0')
    validator = observer.S.safe(args.validator.absolute())
    observer.S.packet(validator, args.validator_index_sha256)
    evidence = observer.S.safe(args.evidence.absolute())
    output = observer.S.safe(args.output.absolute())
    assert evidence.parent == output.parent == ROOT / 'output'
    assert evidence != output and not evidence.exists() and not output.exists()
    evidence.mkdir(exist_ok=False)
    observer.S.save(evidence / 'HOST-SOURCE.json', {
        'host_source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'validator_INDEX_sha256': args.validator_index_sha256,
        'retained_invocation_timeout_seconds': 2000,
        'actual_Main_HEAD_required_by_original_Q': '973039e40622ac20600e6d297d712de419877eda'})
    command = [PYTHON, '-B', '-X', 'utf8', str(validator / 'replay_runtime.py'),
               '--output', str(output), '--run-gpu', '--lease-confirmed']
    process = None
    try:
        try:
            observer.closure(evidence, 'before-cold187')
            process, _private_stdout = owned.invoke(evidence, 'cold187', command, 2000)
        finally:
            after = observer.closure(evidence, 'after-cold187')
        assert process is not None and process['exit'] == 0
        assert process['retained_Popen_reaped'] is True and process['timed_out'] is False
        assert all(after[key] == 0 for key in ('owned_count', 'main_count', 'neon_count'))
        print(json.dumps({'coordinator_exit': process['exit'],
                          'retained_Popen_reaped': process['retained_Popen_reaped'],
                          'timed_out': process['timed_out'],
                          'independent_zero_scope_closure': True,
                          'four_case_physical_audit_still_required': True}))
    except BaseException:
        observer.S.save(evidence / 'HOST-FAILURE.json',
                        {'ownership_released': False, 'traceback': traceback.format_exc()})
        raise


if __name__ == '__main__':
    main()
