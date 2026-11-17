"""Seal this bounded source packet and a non-executing integration plan."""
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RUNTIME = ROOT / 'experiments/native_normal_known_factory_resource_successor_20261117'
RUNTIME_SHA = '1eeca1e85d93c834c52c1208ed68d18aaa2b00bc1b62987cf0b89d5561ab6f90'
BINDER = ROOT / 'experiments/native_normal_known_factory_binding_git_tool_20261117'
BINDER_SHA = '3917792c091fe776cdd49b7f3e015b5655b104798c8a605e340967e870801235'
RUNTIME_NAMES = ('ADMISSION.template.json', 'CURRENT-CLOSED-LANE.template.json',
                 'baseline_predicate.py', 'current_context.py', 'diagnostic_host.py',
                 'diagnostic_support.py', 'handler_metadata.py', 'known_handler_policy.py',
                 'known_loaded_survey.py', 'root_runner.py')
PAYLOADS = ('derive_api_fix.py', 'test_api_fix.py', 'validate_cpu.py', 'seal_source.py',
            'survey_core.py', 'test_resources.py', 'export_provenance.py', 'loaded_survey.py',
            'probe_resources.py', 'stager.py', 'survey_admission.py', 'setter_support.py',
            'placement_sentinel.py', 'DERIVATION.json', 'CPU_VALIDATION.json', 'README.md',
            'RUNTIME_INTEGRATION.json', 'ROOT_ATTESTED_FAILURE_HISTORY.json')


def sha(raw): return hashlib.sha256(raw).hexdigest()


def packet_rows(folder, pin, names):
    index = (folder / 'INDEX.json').read_bytes(); assert sha(index) == pin
    indexed = {row['path']: row for row in json.loads(index)['files']}; out = {}
    for name in names:
        raw = (folder / name).read_bytes(); row = indexed[name]
        assert len(raw) == row['bytes'] and sha(raw) == row['sha256']
        out[name] = row
    return out


def save(name, value):
    with (HERE / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, allow_nan=False); stream.write('\n')


def main():
    runtime = packet_rows(RUNTIME, RUNTIME_SHA, RUNTIME_NAMES)
    binder = packet_rows(BINDER, BINDER_SHA, ('prepare_root.py',))
    support = (RUNTIME / 'diagnostic_support.py').read_bytes()
    old_path = "SURVEY = ROOT / 'experiments/native_normal_resource_survey_20261117'"
    new_path = "SURVEY = ROOT / 'experiments/native_normal_blender51_resource_api_fix_20261117'"
    old_pin = "SURVEY_SHA = 'b6069eb8c87d7599d10165de987ab2d9924fb377890e12a4cb2f0bdaf9ab735c'"
    assert support.count(old_path.encode()) == support.count(old_pin.encode()) == 1
    preparer = (BINDER / 'prepare_root.py').read_bytes()
    assert preparer.count(b"SUCCESSOR = ROOT / 'experiments/native_normal_known_factory_resource_successor_20261117'") == 1
    assert preparer.count(("SUCCESSOR_SHA = '" + RUNTIME_SHA + "'").encode()) == 1
    save('RUNTIME_INTEGRATION.json', {
        'format': 'has_B_resource_Blender51_API_runtime_integration_plan_1',
        'status': 'SOURCE_PLAN_ONLY_NO_RUNTIME_BINDER_OR_ADMISSION_CREATED',
        'collector_packet': HERE.relative_to(ROOT).as_posix(),
        'collector_INDEX_pin': 'Use this final sealed INDEX SHA256 supplied and reviewed by Root; no self-hash is embedded',
        'runtime_parent': {'path': RUNTIME.relative_to(ROOT).as_posix(), 'INDEX_sha256': RUNTIME_SHA, 'files': runtime},
        'future_runtime_packet': 'experiments/native_normal_known_factory_blender51_resource_20261117',
        'runtime_exact_derivation': {
            'copy_byte_exact': [name for name in RUNTIME_NAMES if name != 'diagnostic_support.py'],
            'diagnostic_support.py': [
                {'before': old_path, 'after': new_path, 'occurrences': 1},
                {'before': old_pin, 'after': "SURVEY_SHA = '<EXACT_FINAL_CORRECTED_COLLECTOR_INDEX_SHA256>'", 'occurrences': 1}],
            'require_whole_source_inverse': True,
            'new_INDEX_must_include_all_runtime_members_and_new_derivation_evidence': True,
            'old_source_successor_and_test_harness_must_not_be_relabelled_as_deriving_the_new_support': True},
        'binder_parent': {'path': BINDER.relative_to(ROOT).as_posix(), 'INDEX_sha256': BINDER_SHA, 'files': binder},
        'future_binder_packet': 'experiments/native_normal_known_factory_blender51_binding_20261117',
        'binder_exact_derivation': {
            'prepare_root.py_literal_changes': [
                {'before': "SUCCESSOR = ROOT / 'experiments/native_normal_known_factory_resource_successor_20261117'",
                 'after': "SUCCESSOR = ROOT / 'experiments/native_normal_known_factory_blender51_resource_20261117'", 'occurrences': 1},
                {'before': "SUCCESSOR_SHA = '" + RUNTIME_SHA + "'",
                 'after': "SUCCESSOR_SHA = '<EXACT_FINAL_NEW_RUNTIME_INDEX_SHA256>'", 'occurrences': 1}],
            'require_whole_source_inverse': True,
            'keep_initial_and_final_installed_Git_single_link_false': True,
            'keep_original_source_model_and_generic_single_link_guards': True},
        'source_CPU_before_Root_execution': [
            'Verify this packet INDEX and all payload identities',
            'Render each runtime/binder clone from the pinned parent and require complete byte inverse',
            'Compile all cloned source without calling any runtime entry',
            'Check corrected namespace imports resolve from the selected corrected survey folder',
            'Run pure synthetic known-handler/current-context/binder guards with explicitly rebound source pins'],
        'Root_execution_preconditions': [
            'Actual current full and every native/targeted lane closed and released; never infer closure from this plan',
            'Fresh actual scope observations plus separate current ROOT1019/qualified52 and Review1029/3a maps',
            'Exact original six tools, SourceIO574 original and copy, exporter120, known B three identities preserved',
            'Fresh expiring Root admission and newly owned private output; keep factory baseline/source bindings',
            'Run preparation as a completed separate command, then invoke the direct owned driver; no waiting Python parent'],
        'unchanged_claim_boundaries': ['No preload IO confinement', 'No handler behavior or globals proof',
            'No historical generation or export-equivalence proof', 'No old strict31 native PASS',
            'No normal repair, fidelity, carrier enablement, or adoption'],
        'runtime_or_binder_written': False, 'native_private_or_current_full_read': False,
        'native_execution_authorized_by_this_plan': False})
    save('ROOT_ATTESTED_FAILURE_HISTORY.json', {
        'format': 'has_B_resource_Blender51_API_failure_history_1',
        'evidence_role': 'Root-supplied scalar facts; not independently reobserved by packet author',
        'corrected_Git_binder_INDEX_sha256': BINDER_SHA,
        'preparation_passed': True, 'owned_B_loaded': True,
        'after_load_factory_handler_metadata_gate_passed': True,
        'resource_collection_completed': False,
        'failure_type': 'AttributeError', 'failure_cause': 'module bpy has no attribute blend_paths',
        'wrapper_exit_code': 1, 'wrapper_reaped': True, 'private_child_exit_code': 1,
        'job_and_desktop_closed': True, 'fresh_scopes_closed': True,
        'sources_inputs_tools_preserved': True,
        'resource_inventory_qualified': False, 'normal_fidelity_qualified': False,
        'private_output_or_native_input_read_by_packet_author': False,
        'prior_sealed_diagnostics_changed': False})
    files = []
    for name in sorted(PAYLOADS):
        raw = (HERE / name).read_bytes()
        if name.endswith('.py'): compile(raw, name, 'exec')
        files.append({'path': name, 'bytes': len(raw), 'sha256': sha(raw)})
    assert {p.name for p in HERE.iterdir()} == set(PAYLOADS), 'Unlisted local member before sealing'
    save('INDEX.json', {'format': 'has_source_experiment_index_1', 'packet': HERE.name,
         'status': 'SEALED_SOURCE_CPU_API_CORRECTION_NATIVE_UNRUN_RUNTIME_WIRING_PLAN_ONLY',
         'files': files, 'payload_files': len(files), 'payload_bytes': sum(r['bytes'] for r in files),
         'original_tests': 31, 'additional_API_tests': 7, 'failures': 0, 'errors': 0,
         'original_strict31_packet_changed': False, 'runtime_binder_or_admission_created': False,
         'native_private_or_current_full_read_or_native_executed': False})
    print(json.dumps({'INDEX_sha256': sha((HERE / 'INDEX.json').read_bytes()),
                      'payload_files': len(files), 'payload_bytes': sum(r['bytes'] for r in files),
                      'collector_sha256': sha((HERE / 'survey_core.py').read_bytes()),
                      'test_mock_sha256': sha((HERE / 'test_resources.py').read_bytes())}))


if __name__ == '__main__': main()
