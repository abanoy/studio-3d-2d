"""Authored RAM metadata and mocked publication only; no actual terminal access."""
import ast
import contextlib
import copy
import io
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import close_terminal as C
import full_pass_reference as F
import test_terminal_reference as T
from unqualified_result import validate_unqualified_result, UNQUALIFIED_SUMMARY


def fixture():
    value, registry = T.result()
    value.pop('posed_model_video_1')
    value['actual_mmd_tested'] = False
    value['pose_checks'] = 37
    return value, registry


class UnqualifiedTests(unittest.TestCase):
    def test_exact_refusal_signature_admits_closure_without_changing_input_or_registry(self):
        value, registry = fixture(); before = copy.deepcopy((value, registry))
        result = validate_unqualified_result(value, C.CONTEXT, registry)
        self.assertEqual((value, registry), before)
        self.assertEqual(result, UNQUALIFIED_SUMMARY)
        self.assertFalse(result['native_mmd_owner_acceptance'])
        self.assertFalse(result['merge_copy_or_cold187_authorized'])
        self.assertEqual(len(registry['expected_result_keys']), 158)

    def test_original_complete_full_gate_still_accepts_original_fixture_and_refuses_partial(self):
        value, registry = T.result()
        F.validate_result(value, F.CONTEXT, registry)
        partial, registry = fixture()
        with self.assertRaises(ValueError):
            F.validate_result(partial, F.CONTEXT, registry)
        with self.assertRaises(ValueError):
            C.validate_result(partial, C.CONTEXT, registry)

    def test_missing_extra_native_bool_count_core_movie_and_neon_changes_refuse(self):
        base, registry = fixture()
        mutations = [lambda v: v.update(actual_mmd_tested=0), lambda v: v.update(actual_mmd_tested=True),
            lambda v: v.update(pose_checks=37.0), lambda v: v.update(pose_checks=38),
            lambda v: v.pop('posed_model_video_0'), lambda v: v.update(posed_model_video_1={}),
            lambda v: v.update(unexpected={}), lambda v: v['unit'].update(exit=True),
            lambda v: v['unit'].update(exit=1), lambda v: v['unit'].update(seconds=float('inf')),
            lambda v: v['posed_model_video_0'].update(frames=47),
            lambda v: v['posed_model_video_0'].update(duration='99'),
            lambda v: v['neon_workspace'].update(checks=12503),
            lambda v: v['neon_workspace'].update(failures=False),
            lambda v: v['neon_workspace'].update(all_private_jobs_and_desktops_closed=False)]
        for mutate in mutations:
            value = copy.deepcopy(base); mutate(value)
            with self.assertRaises(ValueError): validate_unqualified_result(value, C.CONTEXT, registry)

    def test_original_registry_cannot_be_reduced_or_repurposed(self):
        value, base = fixture()
        for key in ('expected_result_keys', 'expected_core_process_keys', 'expected_movie_keys'):
            registry = copy.deepcopy(base); registry[key].pop()
            with self.assertRaises(ValueError): validate_unqualified_result(value, C.CONTEXT, registry)
        registry = copy.deepcopy(base); registry['source_commit'] = '0' * 40
        with self.assertRaises(ValueError): validate_unqualified_result(value, C.CONTEXT, registry)

    def test_source_lifecycle_and_full_validator_ASTs_are_original(self):
        before = ast.parse((C.HERE / 'full_pass_reference.py').read_bytes())
        after = ast.parse((C.HERE / 'close_terminal.py').read_bytes())
        for name in ('validate_terminal', 'validate_result', 'validate_current_sources', 'observe',
                     'classify_receipt', 'validate_ownership', 'inventory'):
            left = next(n for n in before.body if isinstance(n, ast.FunctionDef) and n.name == name)
            right = next(n for n in after.body if isinstance(n, ast.FunctionDef) and n.name == name)
            self.assertEqual(ast.dump(left, include_attributes=False), ast.dump(right, include_attributes=False))

    def test_partial_native_does_not_allow_failed_physical_jobs_in_software_completed_inventory(self):
        receipt = T.receipt(); receipt['exit'] = 1
        with self.assertRaises(ValueError): C.classify_receipt(receipt, False, True)

    def test_terminal_keeps_exact_log_suffix_and_uses_closure_signature(self):
        value, registry = fixture(); state, birth, launch, before, after, context = T.metadata()
        context['immutable_run_inputs'] = {}
        mapping = {'state.json': state, 'source-before.json': before, 'source-after.json': after,
                   'root-birth-observation.json': birth, 'launch.json': launch,
                   'RESULT_REGISTRY.json': registry, 'verification.json': value}
        text = json.dumps(value)
        source_calls = []
        def fake_load(path):
            self.assertIn(Path(path).name, mapping)
            return copy.deepcopy(mapping[Path(path).name])
        def digest(path):
            return {'legacy_result_gates.py': context['legacy_result_gates_sha256'],
                    'RESULT_REGISTRY.json': context['registry_sha256']}.get(Path(path).name, context['runner_sha256'])
        def read_text(path, **_kwargs):
            return 'PASS authored completed software\n' + text if Path(path).name == 'canonical.log' else text
        with patch.object(C, 'CONTEXT', context), patch.object(C, 'load', side_effect=fake_load), \
             patch.object(C, 'sha', side_effect=digest), \
             patch.object(C, 'validate_current_sources', side_effect=lambda data: source_calls.append(data)), \
             patch.object(Path, 'stat', return_value=SimpleNamespace(st_mtime_ns=C.ns(state['started_utc']))), \
             patch.object(Path, 'read_text', read_text):
            returned = C.terminal()
        self.assertEqual(returned, (state, before, value)); self.assertEqual(source_calls, [before])
        bad = copy.deepcopy(value); bad['actual_mmd_tested'] = True
        with self.assertRaises(ValueError): validate_unqualified_result(bad, context, registry)

    def test_profile_rejects_failed_software_state_before_reading_full_report(self):
        state, birth, launch, before, after, context = T.metadata('failed')
        context['immutable_run_inputs'] = {}
        mapping = {'state.json': state, 'source-before.json': before, 'source-after.json': after,
                   'root-birth-observation.json': birth, 'launch.json': launch}
        with patch.object(C, 'CONTEXT', context), \
             patch.object(C, 'load', side_effect=lambda path: copy.deepcopy(mapping[Path(path).name])):
            with self.assertRaises(ValueError): C.terminal()

    def test_mocked_publication_and_release_always_unqualified_with_distinct_private_paths(self):
        value, _registry = fixture(); state, _birth, _launch, before, _after, _context = T.metadata()
        observed = {'observed_utc': '2026-11-17T03:00:00Z'}
        found = {'rows': [], 'unique_physical_jobs': 0, 'unique_job_classifications': {},
                 'inline_receipts': [], 'phase_documents': {}, 'ignored_named_non_receipts': [],
                 'registered_cancel_observed': True}
        saved = []; copies = []
        with patch('sys.argv', ['authored', '--root-terminal-confirmed', '--release-closed']), \
             patch.object(C, 'load', return_value={'files': []}), \
             patch.object(C, 'terminal', return_value=(state, before, value)), \
             patch.object(C, 'observe', return_value=observed), \
             patch.object(C, 'inventory', return_value=found), \
             patch.object(C, 'sha', return_value='a' * 64), \
             patch.object(C, 'save', side_effect=lambda path, data: saved.append((Path(path).as_posix(), copy.deepcopy(data)))), \
             patch.object(Path, 'exists', return_value=False), patch.object(Path, 'mkdir'), \
             patch.object(Path, 'read_bytes', return_value=b'authored private bytes'), \
             patch.object(Path, 'write_bytes', lambda path, data: copies.append(Path(path).as_posix())), \
             contextlib.redirect_stdout(io.StringIO()) as output:
            C.main()
        inventory = next(data for name, data in saved if name.endswith('/receipt-inventory.json'))
        release_name, release = next((name, data) for name, data in saved if name.endswith('graphics-lease-unqualified-closed.json'))
        self.assertFalse(inventory['full_suite_passed']); self.assertFalse(release['full_suite_passed'])
        self.assertTrue(inventory['final_full_report_used']); self.assertTrue(release['final_full_report_used'])
        self.assertEqual(inventory['suite_status'], 'passed'); self.assertEqual(inventory['suite_exit'], 0)
        self.assertEqual((inventory['result_groups'], inventory['core_groups'], inventory['movie_groups']), (157, 36, 20))
        self.assertTrue(release['released']); self.assertEqual(release['release_kind'], 'closed_unqualified_MMD_fixture_missing_run')
        self.assertEqual(release['qualification'], 'UNQUALIFIED_MMD_POSED_FIXTURE_MISSING')
        self.assertFalse(release['merge_copy_or_cold187_authorized'])
        self.assertTrue(any('terminal-audit-unqualified-mmd-attempt1' in name and name.endswith('full-verification.json') for name in copies))
        self.assertNotIn('"full_suite_passed": true', output.getvalue())


if __name__ == '__main__':
    unittest.main(verbosity=2)
