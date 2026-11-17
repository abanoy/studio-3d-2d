"""Authored RAM metadata/source checks only; never run the preparer's main()."""
import ast
import copy
import datetime
from pathlib import Path
import unittest
import prepare_root as P

NOW = datetime.datetime(2026, 11, 17, 20, 0, tzinfo=datetime.timezone.utc)
PYTHON = r'C:\Program Files\Python313\python.exe'


def fixture(exits=(0,) * 44, reported=None):
    cases = tuple(('case' + str(i), 'verify_synthetic_' + str(i) + '.py', (), 'synthetic.json', 180) for i in range(44))
    witness = {'format': 'has_root_targeted_tool_terminal_observation_1', 'candidate_commit': P.REVIEW_COMMIT,
        'driver_path': str(P.DRIVER), 'driver_sha256': P.DRIVER_SHA, 'tool_session_id': 20079,
        'observed_utc': (NOW - datetime.timedelta(minutes=1)).isoformat(),
        'tool_result': {'exit_code': 0 if len(exits) == 44 and all(v == 0 for v in exits) else 1,
                        'output': 'SYNTHETIC', 'chunk_id': 'synthetic', 'wall_time_seconds': 1.0}}
    receipts = {}; rows = []; count = len(exits) if reported is None else reported
    scope = {'format': 'has_root_workspace_scope_observation_1', 'owned_count': 0,
             'termination_issued': False, 'observed_utc': (NOW - datetime.timedelta(minutes=2)).isoformat()}
    for index, code in enumerate(exits):
        label = cases[index][0]
        process = {'label': label, 'pid': 100 + index, 'exit': code, 'retained_Popen_reaped': True,
                   'seconds': 1.0, 'timed_out': False}
        receipts[label] = {'process': process, 'start': {'pid': process['pid'], 'retained_Popen': True,
            'started_utc': (NOW - datetime.timedelta(minutes=3)).isoformat()},
            'command': [PYTHON, '-B', '-u', str(P.REVIEW / 'tests' / cases[index][1])], 'closure': copy.deepcopy(scope)}
        if index < count: rows.append({**process, 'report': {'synthetic_only': True}})
    complete = witness['tool_result']['exit_code'] == 0
    verification = {'format': 'has_root_workspace_followup_1', 'rows': rows,
        'all_functional_source_unchanged': True, 'functional_source_files': 1029,
        'host_scopes_closed': True, 'full_suite_pass_claimed': False,
        'passed': bool(rows) and all(row['exit'] == 0 for row in rows)}
    marker = {'format': 'has_targeted_neon_late_stage_completion_1', 'candidate_commit': P.REVIEW_COMMIT,
        'expected_wrappers': 44, 'all44_completed_and_canonical_reports_passed': complete,
        'host_return': 0 if complete else (1 if count == len(exits) else None), 'full_PASS_or_merge_claimed': False}
    before = {'synthetic/' + str(i): 'a' * 64 for i in range(1029)}
    return [witness, verification, marker, before, copy.deepcopy(before), receipts, cases,
            str(P.DRIVER), PYTHON, 20079, NOW, lambda label, report: None]


class BindingTests(unittest.TestCase):
    def test_actual_tool_terminal_semantics_and_successful_synthetic_prefix(self):
        result = P.validate_terminal(*fixture())
        self.assertEqual(result['executed_wrappers'], 44)
        self.assertIs(result['targeted_completed'], True)
        self.assertIs(result['outer_Popen_or_birth_claimed'], False)
        for key, value in (('session_id', 20079), ('exit_code', False)):
            values = fixture(); values[0]['tool_result'][key] = value
            with self.assertRaises(ValueError): P.validate_terminal(*values)
        values = fixture(); values[0]['retained_Popen_reaped'] = True
        with self.assertRaises(ValueError): P.validate_terminal(*values)

    def test_closed_failed_targeted_does_not_need_PASS_or_all44(self):
        result = P.validate_terminal(*fixture((0, 1)))
        self.assertIs(result['targeted_completed'], False)
        self.assertEqual(result['outer_tool_exit'], 1)
        # An outer report assertion can omit the final already-reaped receipt
        # from host rows; final scope and actual receipt still prove closure.
        result = P.validate_terminal(*fixture((0, 0), reported=1))
        self.assertEqual(result['reported_rows'], 1)

    def test_unreaped_mismatched_or_postfailure_receipts_refuse(self):
        for key, replacement in (('retained_Popen_reaped', False), ('timed_out', True), ('pid', False)):
            values = fixture(); values[5]['case0']['process'][key] = replacement
            with self.assertRaises(ValueError): P.validate_terminal(*values)
        values = fixture((1, 0))
        with self.assertRaises(ValueError): P.validate_terminal(*values)
        values = fixture((0, 1)); values[5]['case0']['command'].append('--weakened')
        with self.assertRaises(ValueError): P.validate_terminal(*values)

    def test_changed_source_active_scope_and_false_completion_refuse(self):
        values = fixture(); values[4]['synthetic/0'] = 'b' * 64
        with self.assertRaises(ValueError): P.validate_terminal(*values)
        values = fixture(); values[5]['case0']['closure']['owned_count'] = 1
        with self.assertRaises(ValueError): P.validate_terminal(*values)
        values = fixture((0, 1)); values[2]['all44_completed_and_canonical_reports_passed'] = True
        with self.assertRaises(ValueError): P.validate_terminal(*values)

    def test_source_has_no_runner_launch_and_uses_sealed_existing_gates(self):
        raw = Path(P.__file__).read_bytes(); tree = ast.parse(raw)
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
        for node in calls:
            if isinstance(node.func, ast.Attribute):
                self.assertNotIn(node.func.attr, ('Popen', 'run', 'check_call', 'invoke'))
        self.assertEqual(sum(isinstance(node.func, ast.Attribute) and node.func.attr == 'check_output' for node in calls), 1)
        for text in (b'S.check_inputs(', b'S.check_snapshot(ROOT,', b'S.check_snapshot(REVIEW,',
                     b"R.closure(folder, 'fresh-before-binding')", b"R.closure(folder, 'fresh-after-binding')",
                     b"'runner_launched': False", b"return 0  # No invocation"):
            self.assertIn(text, raw)
        self.assertEqual(P.SUCCESSOR_SHA, '82727caa443cc58d623463e195fc6220d08c2d878cb93461eb481c722098b6e0')


if __name__ == '__main__': unittest.main(verbosity=2)
