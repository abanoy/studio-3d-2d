"""Public source/metadata CPU audit only; never starts a native process."""
from pathlib import Path
from dataclasses import asdict
import ast
import datetime
import hashlib
import io
import json
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PUBLIC_BINDINGS = {
    'carrier_recipe_index': ('experiments/native_normal_carrier_probe_20261117/INDEX.json', 'a800398fa46c506c339aa81b4bc3db098bc6dc1c0d03b30274899debac61e8e6'),
    'carrier_recipe': ('experiments/native_normal_carrier_probe_20261117/NEXT_NATIVE_RECIPE.md', 'f565fdd73c8868863d2d29dd56f1bae598dde426544b0425be39b4a6df2c9aac'),
    'original_B_public_hashmetadata': ('experiments/source_normal_followup_plan_20261115/INPUT_METADATA.json', '080cfbcea375c18fa21f29b51d9afbd30bfc4862524974b8900cfd67541d4914'),
    'original_setter_support': ('experiments/normal_setter_boundary_sentinel_20261117/setter_support.py', 'fda14a49be8fb57908524aad7869a851ea234036a7c30892ef3e01777ba73bb9'),
    'original_placement_source': ('experiments/native_normal_carrier_probe_20261117/placement_sentinel.py', 'e42fa44efa599851396c517fa0b4bc90a692efb1f911517fa3d748879d1462c2'),
    'approved_sentinel_fake_tests': ('experiments/normal_setter_boundary_sentinel_20261117/test_sentinel.py', 'c070508aea3face5986b491f25bd06ba5b7bd0627853bedbdda34c01d98d6ae2'),
    'approved_input_lock_metadata': ('experiments/replay_audio_fix_20261115/builder/input-lock.json', '3bb7c2ce75f55dcb53143aab0df5ab8b39c68180617092664a579126fb09cfb6'),
    'approved_identity_reader_source': ('experiments/resume_root_20261115/audit_protected_inputs_before_cleanup.py', '5be1d34aa6aced8fc112bee3ecadd489be9b7f38ab710553385bfd77ca500d83'),
    'retained_normal_context_support': ('experiments/normal_boundary_probe_20261116/probe_support.py', '71fc6b8ddd270fc40a42212dad3e1a7fd64d24b8e7c401ee32d1744c8b00adf0'),
    'non_NORMAL_semantic_packet_index': ('experiments/carrier_semantic_preservation_20261117/INDEX.json', 'edab37a065d3c29a316b7a1c1cab3a4263f5d4e716f97fa4192f541b391ea4fd'),
    'semantic_qualification_addendum_index': ('experiments/carrier_semantic_qualification_boundary_20261117/INDEX.json', '2bf04bdbad8623e7b2004ab001ed582276b6a3bde608fa60a94c84067d2e00cc'),
}


def sha(raw): return hashlib.sha256(raw).hexdigest()


def bind_public_sources():
    rows = {}
    for role, (relative, digest) in PUBLIC_BINDINGS.items():
        source = ROOT / relative
        raw = source.read_bytes()
        if sha(raw) != digest: raise ValueError('Pinned public source/metadata differs: ' + role)
        rows[role] = {'path': relative, 'bytes': len(raw), 'sha256': digest}
    return rows


def main():
    import survey_core
    import export_provenance
    import test_resources
    before = bind_public_sources()
    local_before = {p.name: {'bytes': p.stat().st_size, 'sha256': sha(p.read_bytes())}
                    for p in HERE.glob('*.py')}
    # Collector/helper source must have no filesystem, network, native-process
    # or bpy imports. Fake RNA property traps provide complementary dynamic tests.
    for name in ('survey_core.py', 'loaded_survey.py', 'export_provenance.py'):
        unit = ast.parse((HERE / name).read_text(encoding='utf-8'))
        for node in ast.walk(unit):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in {'open', 'eval', 'exec', '__import__'}: raise ValueError('Unexpected collector capability')
            if isinstance(node, ast.Import):
                if any(alias.name.split('.')[0] in {'bpy', 'os', 'sys', 'pathlib', 'subprocess', 'socket', 'ctypes', 'requests', 'urllib'} for alias in node.names):
                    raise ValueError('Unexpected collector import')
    metadata = json.loads((ROOT / PUBLIC_BINDINGS['original_B_public_hashmetadata'][0]).read_bytes())
    provenance = export_provenance.classify_public_reference(metadata)
    lock = json.loads((ROOT / PUBLIC_BINDINGS['approved_input_lock_metadata'][0]).read_bytes())
    catalogue_counts = {'runtime_executable_references': len(lock['runtime_executables']),
                        'sourceio_file_references': len(lock['sourceio_files']),
                        'exporter_source_references': len(lock['exporter_noncache_sources'])}
    if catalogue_counts != {'runtime_executable_references': 6, 'sourceio_file_references': 574, 'exporter_source_references': 120}:
        raise ValueError('Retained catalogue role counts differ')
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(test_resources.ResourceTests)
    methods = unittest.defaultTestLoader.getTestCaseNames(test_resources.ResourceTests)
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    after = bind_public_sources()
    local_after = {p.name: {'bytes': p.stat().st_size, 'sha256': sha(p.read_bytes())}
                   for p in HERE.glob('*.py')}
    if before != after or local_before != local_after: raise ValueError('Public/source files changed during CPU audit')
    report = {'format': 'has_B_resource_survey_preparation_cpu_audit_1',
              'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
              'status': 'SOURCE_CPU_PASS_NATIVE_UNSTAGEABLE' if result.wasSuccessful() else 'SOURCE_CPU_FAILED',
              'test_methods': methods, 'synthetic_stdout': stream.getvalue(),
              'local_python_sources': local_before, 'public_source_bindings': before,
              'public_sources_unchanged': True, 'limits': asdict(survey_core.Limits()),
              'locked_reference_catalogue_counts': catalogue_counts,
              'runtime_or_694_source_identities_observed_current': False,
              'public_hashmetadata_provenance': provenance,
              'native_assets_or_private_arrays_or_media_read': False,
              'native_stage_or_engine_or_CIM_or_Git_invoked': False,
              'native_stage_ready': False, 'actual_resource_inventory_observed': False,
              'native_input_validity_ID_semantics_NORMAL_or_fidelity_qualified': False}
    (HERE / 'CPU_VALIDATION.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({key: report[key] for key in ('status', 'tests', 'failures', 'errors', 'native_stage_ready')}))
    if not result.wasSuccessful(): raise SystemExit(1)


if __name__ == '__main__': main()
