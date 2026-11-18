"""Focused CPU admission, output/failure boundaries, and exact source inverses."""
import ast
import copy
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import current_context as C
import diagnostic_support as S
import derive_source as D
import known_handler_policy as H
import ownership_outputs as O
import qualified_context as Q
from survey_core import canonical, SurveyError

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / 'native_normal_known_factory_blender51_resource_20261117'
OWNERSHIP_PARENT = HERE.parent / 'native_B_resource_ownership_metadata_20261118'
S.packet(OWNERSHIP_PARENT, 'd3346044906201097f86548bcbc2b22ef3031980c80dc7b1dfadb9f3fa77d46a')
spec = importlib.util.spec_from_file_location('unchanged_ownership_cpu_fixtures', OWNERSHIP_PARENT / 'test_ownership.py')
F = importlib.util.module_from_spec(spec); spec.loader.exec_module(F)
OwnershipTests = F.OwnershipTests
NOW = datetime.datetime(2026, 11, 18, tzinfo=datetime.timezone.utc)


def admitted():
    value = json.loads((HERE / 'ADMISSION.template.json').read_bytes())
    value.update(root_native_lane_exclusive=True, cold187_disposition='NOT_STARTED_CURRENT_CONTEXT',
                 issued_utc=NOW.isoformat(), expires_utc=(NOW + datetime.timedelta(minutes=5)).isoformat())
    for row in value['proofs'].values(): row.update(path='SYNTHETIC', bytes=1, mtime_ns=1, sha256='a' * 64)
    record = json.loads((HERE / 'CURRENT-CLOSED-LANE.template.json').read_bytes())
    record.update(observed_utc=(NOW - datetime.timedelta(seconds=1)).isoformat(), root_native_lane_exclusive=True,
        ui_lane_closed=True, all_owned_jobs_desktops_closed=True, source_unchanged=True,
        current_full_run_active=False, current_targeted_run_active=False, cold187_launched=False,
        termination_issued=False, owned_count=0, main_count=0, neon_count=0,
        root_metadata_head=C.EXPECTED_METADATA_HEAD, root_functional_commit=Q.TESTED,
        root_functional_count=1029, review_commit=Q.TESTED, review_functional_count=1029,
        root_snapshot_sha256='a' * 64, review_snapshot_sha256='a' * 64,
        cold187_disposition=value['cold187_disposition'])
    return value, {'closed_lane_root_record': record}


class SuccessorTests(unittest.TestCase):
    def test_context_admits_only_fixed_tested1029_dcb_and_fresh_closed_lane(self):
        value, data = admitted(); C.validate_admission(value, NOW); C.validate_current_closed_lane(value, data)
        for key, replacement in [('functional_commit', '52f63c944ded7a651da871524d23a345b606424d'),
                                 ('functional_count', 1019), ('expected_metadata_head', 'a' * 40),
                                 ('candidate_functional_count', True)]:
            bad = copy.deepcopy(value); bad[key] = replacement
            with self.assertRaises(ValueError): C.validate_admission(bad, NOW)
        bad = copy.deepcopy(value); bad['claims']['native_fidelity'] = True
        with self.assertRaises(ValueError): C.validate_admission(bad, NOW)
        for key, replacement in [('owned_count', 1), ('root_functional_count', 1019),
                                 ('cold187_launched', True), ('full_suite_pass_claimed', True),
                                 ('observed_utc', (NOW - datetime.timedelta(seconds=121)).isoformat())]:
            bad = copy.deepcopy(data); bad['closed_lane_root_record'][key] = replacement
            with self.assertRaises(ValueError): C.validate_current_closed_lane(value, bad)

    def test_public_qualification_is_sealed_and_current_Main_equals_immutable_map(self):
        snapshot = Q.check_qualified_context()
        S.check_snapshot(S.ROOT, snapshot, Q.TESTED, 1029)
        values = [snapshot, S.read_json(Q.FULL / 'RESULT.json'), S.read_json(Q.FULL / 'RELEASE.json'),
                  S.read_json(Q.FULL / 'STATE.json'), S.read_json(Q.FULL / 'PROTECTED_INPUTS_AFTER.json'),
                  S.read_json(Q.REVIEWED)]
        for index, key, replacement in [(1, 'physical_jobs', 195), (1, 'movie_groups', 20),
                                        (1, 'strict_terminal_INDEX_sha256', 'a' * 64),
                                        (2, 'released', False), (5, 'rows', [])]:
            bad = copy.deepcopy(values); bad[index][key] = replacement
            with self.assertRaises(ValueError): Q.validate_qualification(*bad)

    def test_six_refusals_and_output_hashes_survive_addon_failure_and_success(self):
        for fail in (False, True):
            bpy, _ = F.fixture(); private, survey = F.baseline(bpy)
            parent_private = canonical(private)
            parent_public = canonical({'survey': survey, 'export_branch': 'UNKNOWN'})
            with tempfile.TemporaryDirectory() as folder:
                stage = Path(folder)
                (stage / 'PRIVATE_RESOURCES.json').write_bytes(parent_private)
                (stage / 'PUBLIC_RESOURCES.json').write_bytes(parent_public)
                replacement = (lambda *a: (_ for _ in ()).throw(RuntimeError('PRIVATE_OWNER_PATH'))) if fail else O.collect_ownership_metadata
                with patch.object(O, 'collect_ownership_metadata', replacement):
                    public, binding = O.write_outputs(stage, bpy, private, survey, C.QUALIFICATIONS,
                                                       C.PROFILE, 'a' * 64, S.save)
                self.assertEqual((stage / 'PRIVATE_RESOURCES.json').read_bytes(), parent_private)
                self.assertEqual((stage / 'PUBLIC_RESOURCES.json').read_bytes(), parent_public)
                self.assertEqual(survey['status'], 'RESOURCE_PROFILE_REFUSED')
                self.assertEqual(survey['profile_issues'], 6)
                self.assertEqual(private['issues'], json.loads(parent_private)['issues'])
                self.assertIs(public['ownership_metadata_collected'], not fail)
                self.assertEqual(public['source_resource_public_sha256'], hashlib.sha256(parent_public).hexdigest())
                own_raw = (stage / 'PRIVATE_OWNERSHIP_METADATA.json').read_bytes()
                self.assertEqual(binding['private_bytes'], len(own_raw))
                self.assertEqual(binding['private_sha256'], hashlib.sha256(own_raw).hexdigest())
                self.assertEqual(binding['public_sha256'], hashlib.sha256((stage / 'PUBLIC_OWNERSHIP_METADATA.json').read_bytes()).hexdigest())
                if fail: self.assertNotIn('PRIVATE_OWNER_PATH', canonical(public).decode())

    def test_malformed_summary_and_public_binding_cannot_change_baseline_decision(self):
        bpy, _ = F.fixture(); private, survey = F.baseline(bpy)
        _, summary = O.collect_separate(bpy, private, survey)
        public = {'format': 'has_session_B_resource_ownership_diagnostic_summary_1', 'profile': C.PROFILE,
                  'ownership_metadata_collected': True, 'source_resource_private_sha256': 'a' * 64,
                  'source_resource_public_sha256': 'b' * 64, 'summary': summary,
                  'claims': {key: False for key in C.QUALIFICATIONS}}
        O.validate_public(public, 'a' * 64, 'b' * 64, C.QUALIFICATIONS, C.PROFILE, survey)
        for mutation in ('hash', 'status', 'issues', 'baseline', 'qualification'):
            bad = copy.deepcopy(public)
            if mutation == 'hash': bad['source_resource_public_sha256'] = 'c' * 64
            if mutation == 'status': bad['summary']['status'] = 'METADATA_SURVEY_ONLY'
            if mutation == 'issues': bad['summary']['profile_issues'] = False
            if mutation == 'baseline': bad['summary']['original_resource_summary']['export_invoked'] = True
            if mutation == 'qualification': bad['summary']['strict31_native_qualified'] = True
            with self.assertRaises((ValueError, SurveyError)):
                O.validate_public(bad, 'a' * 64, 'b' * 64, C.QUALIFICATIONS, C.PROFILE, survey)

    def test_host_preserves_parent_before_addon_and_uses_only_existing_handler_phases(self):
        source = (HERE / 'diagnostic_host.py').read_text(); tree = ast.parse(source)
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
        phases = [node.args[2].value for node in calls if isinstance(node.func, ast.Attribute)
                  and node.func.attr == 'check_live' and len(node.args) == 3]
        self.assertTrue(phases); self.assertTrue(set(phases) <= set(H.PHASES))
        parent_marker = source.index("print('HAS_B_RESOURCE_PLACEMENT '")
        self.assertLess(parent_marker, source.index('ownership, ownership_binding = write_outputs('))
        parent_source = (PARENT / 'diagnostic_host.py').read_text()
        self.assertEqual(source[:source.index('    # Parent files and markers above')],
                         parent_source[:parent_source.index('\n\n\nif __name__')].rstrip() + '\n\n')
        prepare = ast.parse((HERE / 'prepare_root.py').read_text())
        attributes = [node.func.attr for node in ast.walk(prepare) if isinstance(node, ast.Call)
                      and isinstance(node.func, ast.Attribute)]
        self.assertFalse(set(attributes) & {'Popen', 'run', 'check_call', 'invoke', 'main'})

    def test_exact_parent_derivations_inverses_and_byte_exact_safety_companions(self):
        delta = S.read_json(HERE / 'SOURCE_DELTA.json')
        self.assertEqual(S.digest((PARENT / 'INDEX.json').read_bytes()),
                         '82727caa443cc58d623463e195fc6220d08c2d878cb93461eb481c722098b6e0')
        for row in delta['changed']:
            before = (S.ROOT / row['parent_path']).read_bytes(); after = (HERE / row['path']).read_bytes()
            self.assertEqual(D.render(before, row), after)
            self.assertEqual(D.render(after, row, inverse=True), before)
            with self.assertRaises(ValueError): D.render(before + b'\n', row)
        for row in delta['byte_exact']:
            self.assertEqual((S.ROOT / row['parent_path']).read_bytes(), (HERE / row['path']).read_bytes())
        for path in HERE.glob('*.py'): compile(path.read_bytes(), str(path), 'exec')


if __name__ == '__main__': unittest.main(verbosity=2)
