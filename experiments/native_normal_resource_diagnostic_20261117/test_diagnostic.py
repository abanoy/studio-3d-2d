"""Pure source/schema/physical-receipt tests; no actual root or native inputs."""
import ast
import copy
import datetime
import re
from pathlib import Path
import unittest
import diagnostic_support as S
import root_runner as R

NOW = datetime.datetime(2026, 11, 17, 18, tzinfo=datetime.timezone.utc)


def admission():
    return {'format': 'has_session_B_resource_diagnostic_admission_1', 'profile': S.PROFILE,
            'root_native_lane_exclusive': True, 'loader_readonly_dependency_resolution_authorized': True,
            'claims': {key: False for key in S.QUALIFICATIONS},
            'expected_metadata_head': '1' * 40, 'functional_commit': '2' * 40, 'candidate_commit': S.CANDIDATE,
            'functional_count': 1029, 'issued_utc': (NOW - datetime.timedelta(seconds=10)).isoformat(),
            'expires_utc': (NOW + datetime.timedelta(seconds=290)).isoformat(),
            'proofs': {key: {} for key in S.PROOFS}, 'protected_originals': {key: {} for key in ('blend', 'glb', 'parameters')}}


def receipt():
    return {'format': 'studio_private_desktop_1', 'exit': 0, 'private_window_seen': True,
            'child_desktop_confirmed': True, 'foreground_child_observed': False, 'desktop_switch_requested': False,
            'job_closed': True, 'desktop_closed': True, 'job_memory_limit_bytes': 4096 * 1024 * 1024}


class DiagnosticTests(unittest.TestCase):
    def test_separate_authorized_profile_with_all_qualification_claims_false(self):
        value = admission(); self.assertIs(S.validate_admission(value, NOW), value)
        for key in ('root_native_lane_exclusive', 'loader_readonly_dependency_resolution_authorized'):
            changed = copy.deepcopy(value); changed[key] = 1
            with self.assertRaises(ValueError): S.validate_admission(changed, NOW)

    def test_never_promotes_legacy_confinement_generation_or_normal_claims(self):
        for key in S.QUALIFICATIONS:
            for bad in (True, 0, None):
                changed = admission(); changed['claims'][key] = bad
                with self.assertRaises(ValueError): S.validate_admission(changed, NOW)

    def test_current_exact_context_and_all_closure_roles_required(self):
        for key in S.PROOFS:
            changed = admission(); del changed['proofs'][key]
            with self.assertRaises(ValueError): S.validate_admission(changed, NOW)
        for key, bad in (('candidate_commit', '3' * 40), ('functional_count', True), ('profile', 'LEGACY_STRICT')):
            changed = admission(); changed[key] = bad
            with self.assertRaises(ValueError): S.validate_admission(changed, NOW)

    def test_expired_future_naive_and_widened_lease_refused(self):
        for start, end in ((-400, -1), (1, 100), (-1, 601)):
            changed = admission(); changed['issued_utc'] = (NOW + datetime.timedelta(seconds=start)).isoformat()
            changed['expires_utc'] = (NOW + datetime.timedelta(seconds=end)).isoformat()
            with self.assertRaises(ValueError): S.validate_admission(changed, NOW)
        changed = admission(); changed['issued_utc'] = '2026-11-17T17:59:50'
        with self.assertRaises(ValueError): S.validate_admission(changed, NOW)

    def test_physical_receipt_needs_real_window_and_all_closure_flags(self):
        self.assertTrue(R.receipt_ok(receipt()))
        for key in ('private_window_seen', 'child_desktop_confirmed', 'job_closed', 'desktop_closed'):
            for bad in (False, 1, None):
                changed = receipt(); changed[key] = bad; self.assertFalse(R.receipt_ok(changed))

    def test_physical_error_foreground_timeout_and_wrong_memory_refused(self):
        for key in ('error', 'monitor_error', 'desktop_enumeration_error', 'timed_out', 'cancelled', 'foreground_child_observed', 'desktop_switch_requested'):
            changed = receipt(); changed[key] = True; self.assertFalse(R.receipt_ok(changed))
        changed = receipt(); changed['job_memory_limit_bytes'] = 8192 * 1024 * 1024
        self.assertFalse(R.receipt_ok(changed))

    def test_typed_json_joins_reject_integer_booleans(self):
        self.assertTrue(R.typed_equal({'closed': True, 'size': [0, 0]}, {'closed': True, 'size': [0, 0]}))
        self.assertFalse(R.typed_equal({'closed': 1}, {'closed': True}))

    def test_identity_records_reject_float_timestamps_and_boolean_sizes(self):
        value = {'path': r'C:\synthetic\proof.json', 'bytes': 24, 'mtime_ns': 1234, 'sha256': 'a' * 64}
        self.assertIs(S.validate_identity(value), value)
        for key, bad in (('bytes', True), ('mtime_ns', 1234.0), ('sha256', 'A' * 64)):
            changed = dict(value); changed[key] = bad
            with self.assertRaises(ValueError): S.validate_identity(changed)

    def test_scope_coordinator_matcher_handles_both_path_separators(self):
        for text in (r'C:\owned\tests\verify.py', 'C:/owned/tests/verify.py',
                     'run_canonical_owned.ps1', 'start_canonical_new.ps1', 'replay_runtime.py'):
            self.assertIsNotNone(re.search(R.CANONICAL_PATTERN, text, re.IGNORECASE))
        self.assertIsNone(re.search(R.CANONICAL_PATTERN, 'root_runner.py'))

    def test_host_source_uses_owned_open_with_scripts_and_UI_disabled_and_no_save_export(self):
        source = (Path(__file__).parent / 'diagnostic_host.py').read_text(encoding='utf-8')
        unit = ast.parse(source)
        calls = [node for node in ast.walk(unit) if isinstance(node, ast.Call)]
        opens = [node for node in calls if isinstance(node.func, ast.Attribute) and node.func.attr == 'open_mainfile']
        self.assertEqual(len(opens), 1)
        values = {key.arg: key.value for key in opens[0].keywords}
        self.assertEqual(ast.literal_eval(values['load_ui']), False)
        self.assertEqual(ast.literal_eval(values['use_scripts']), False)
        self.assertTrue(all(not isinstance(node.func, ast.Attribute) or node.func.attr not in
                            {'save_as_mainfile', 'save_mainfile', 'reload', 'unpack', 'foreach_get', 'gltf'} for node in calls))


if __name__ == '__main__': unittest.main(verbosity=2)
