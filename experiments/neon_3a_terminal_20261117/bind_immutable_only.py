"""Prepare context using only four approved immutable documents and pure gates.

The copied binder main retains its full runtime/tool checks for Root. This
preparation entry never calls that main or reads current source/tool binaries.
"""
from pathlib import Path
import hashlib
import importlib.util
import json

HERE = Path(__file__).resolve().parent
BINDER_SHA = 'f795528e29b522473bc5542a5dc686ddef39ab666d26e7101977228f8d7cf865'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    assert not (HERE / 'INDEX.json').exists() and not (HERE / 'CONTEXT.json').exists()
    binder = HERE / 'bind_context.py'
    assert sha(binder) == BINDER_SHA
    spec = importlib.util.spec_from_file_location('source_only_3a_metadata_binder', binder)
    B = importlib.util.module_from_spec(spec); spec.loader.exec_module(B)  # No binder main call.
    registry = json.loads((HERE / 'RESULT_REGISTRY.json').read_bytes())
    assert registry['source_commit'] == B.COMMIT
    assert (len(registry['expected_result_keys']), len(registry['expected_core_process_keys']),
            len(registry['expected_movie_keys'])) == (158, 36, 21)
    values = {}; pins = {}
    for name in B.INPUTS:
        values[name], pins[name] = B.read_input(name)
    api_identity = B.adapt_actual_api_detail(values['root-birth-api-detail.json'])
    B.validate(values['source-before.json'], values['launch.json'], values['root-birth-observation.json'],
               api_identity, registry['verifier_sha256'])
    assert values['root-birth-api-detail.json']['python_CIM_birth'] == '2026-11-17T18:59:02.3970710Z'
    context = {'format': 'has_neon_3a_terminal_source_context_1', 'checkout': str(B.REVIEW),
        'run_name': B.RUN_NAME, 'commit': B.COMMIT, 'functional_sources': 1029,
        'coordinator_pid': B.COORDINATOR['pid'], 'coordinator_birth': B.COORDINATOR['creation_utc'],
        'python_pid': B.PYTHON['pid'], 'python_birth': B.PYTHON['creation_utc'],
        'python_executable': r'C:\Program Files\Python313\python.exe', 'python_command': B.PYTHON['command_line'],
        'runner': str(B.RUNNER), 'runner_sha256': B.RUNNER_SHA, 'powershell': str(B.PWSH),
        'powershell_sha256': B.PWSH_SHA, 'registry_sha256': sha(HERE / 'RESULT_REGISTRY.json'),
        'legacy_result_gates_sha256': sha(HERE / 'legacy_result_gates.py'),
        'immutable_run_inputs': pins, 'result_groups': 158, 'core_groups': 36, 'movie_groups': 21,
        'private_job_count': 'DERIVE_ACTUAL_NO_ASSUMPTION', 'birth_identity_api': 'Get-Process.StartTime',
        'terminal_state_or_full_report_read_by_preparation': False, 'engines_CIM_Git_executed': False}
    # Re-read only the same four allowed metadata files before committing context.
    for name, digest in pins.items():
        unused, current = B.read_input(name)
        assert current == digest
    B.save('CONTEXT.json', context)
    B.save('BINDING_RECEIPT.json', {'status': 'ACTUAL_FOUR_IMMUTABLE_DOCUMENT_BINDING_ONLY_TERMINAL_UNREAD',
        'context_sha256': sha(HERE / 'CONTEXT.json'), 'immutable_run_inputs': pins,
        'root_approved_exact_birth_coordinates': True, 'same_GetProcess_birth_API_as_terminal_observer': True,
        'strict_actual_sevenfield_API_detail_validated': True,
        'raw_CIM_precision_detail_pinned_without_using_CIM_as_identity': True,
        'only_four_current_run_documents_read': list(B.INPUTS), 'binder_main_executed': False,
        'current_verifier_runner_Pwsh_or_native_inputs_read': False,
        'run_state_source_after_logs_or_full_report_read': False,
        'process_query_or_engine_or_Git_run': False,
        'tool_source_identities_in_context_are_retained_source_pins_not_fresh_rehashes': True})
    print(json.dumps({'context_sha256': sha(HERE / 'CONTEXT.json'),
                      'immutable_inputs': len(pins), 'terminal_unread': True, 'binder_main_executed': False}))


if __name__ == '__main__':
    main()
