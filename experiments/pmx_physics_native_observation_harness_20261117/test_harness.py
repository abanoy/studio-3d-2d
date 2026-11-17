"""Authored files only; never open the fixed actual-input context."""
from pathlib import Path
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as S
import run_observation as R
import worker as W


FIXTURE_SHA = '323129acee5355b6cc6d99b3068e07253e17d87cd01cbcbc572f3a25eed45b59'


def fixture_tree():
    owner = S.HERE / 'synthetic_runs'; owner.mkdir(exist_ok=True)
    base = Path(tempfile.mkdtemp(prefix='authored-', dir=owner))
    for leaf in ('originals', 'copies', 'outputs'): (base / leaf).mkdir()
    fixture = S.read_json(S.ROOT / 'experiments/pmx_physics_native_reader_prototype_20261117/MANUAL_FIXTURE_EXPECTATIONS.json', 16384, FIXTURE_SHA)
    raw = bytes.fromhex(fixture['complete_hex']); rows = []
    for i in range(4):
        original = base / 'originals' / ('SECRET_ARTIST_CANARY_' + str(i) + '.pmx')
        copied = base / 'copies' / ('input-' + str(i) + '.pmx')
        original.write_bytes(raw); copied.write_bytes(raw)
        rows.append({'source': str(original), 'source_identity': S.stamp(original.lstat()), 'sha256': S.sha(raw),
                     'copy': str(copied), 'copy_identity': S.stamp(copied.lstat()), 'copy_bytes_equal_source': True})
    provenance = {'format': 'has_private_owned_pmx_source_copies_1', 'discovery_sha256': 'a' * 64,
                  'producer_sha256': 'b' * 64, 'rows': rows, 'source_read_only_and_unchanged': True,
                  'native_body_or_joint_tables_parsed': False, 'native_qualification': False,
                  'private_original_copies_do_not_upload': True}
    payload = S.canonical(provenance); (base / 'copies/PROVENANCE.json').write_bytes(payload)
    return base, S.context(base, S.sha(payload)), provenance


class HarnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base, cls.ctx, cls.provenance = fixture_tree()
        cls.oracle_dir = cls.base / 'outputs/PRIVATE-pmx-observation-oracle'
        cls.oracle, cls.oracle_public = R.run_batch('oracle', cls.ctx, cls.oracle_dir)
        cls.oracle_path = cls.oracle_dir / 'PRIVATE_ORACLE_PHASE.json'
        cls.oracle_sha = S.sha(cls.oracle_path.read_bytes())
        cls.compare_dir = cls.base / 'outputs/PRIVATE-pmx-observation-compare'
        cls.compared, cls.compare_public = R.run_batch('compare', cls.ctx, cls.compare_dir,
            oracle_manifest=cls.oracle_path, oracle_sha=cls.oracle_sha, root_frozen=True)

    @classmethod
    def tearDownClass(cls):
        # Only this exact verified owned synthetic subtree is removed.
        if cls.base.parent == S.HERE / 'synthetic_runs': shutil.rmtree(cls.base)

    def private_fixture(self):
        base, ctx, provenance = fixture_tree()
        self.addCleanup(lambda: shutil.rmtree(base) if base.parent == S.HERE / 'synthetic_runs' else None)
        return base, ctx, provenance

    def test_01_two_separate_phases_four_retained_children_each(self):
        self.assertTrue(self.oracle['all_cases_completed_and_preserved'])
        self.assertTrue(self.compared['all_cases_completed_and_preserved'])
        for manifest in (self.oracle, self.compared):
            self.assertFalse(manifest['native_protocol_qualified'])
            for row in manifest['cases']:
                self.assertTrue(row['process']['retained_Popen_reaped'])
                self.assertEqual(row['process']['exit'], 0)
                self.assertFalse(row['process']['timed_out'])
                self.assertTrue(row['preserved'])
        self.assertTrue(all(r['declaration_correspondence_observed'] and r['archive_exact_roundtrip_observed'] for r in self.compared['cases']))
        self.assertEqual(self.compared['oracle_manifest_sha256_frozen_by_Root'], self.oracle_sha)

    def test_02_oracle_has_no_candidate_artifacts_or_imports(self):
        for i in range(4):
            case = self.oracle_dir / ('case-' + str(i))
            receipt = S.read_json(case / 'PRIVATE_RECEIPT.json', 131072)
            self.assertIs(receipt['detail']['candidate_or_archive_imported'], False)
            self.assertFalse((case / 'PRIVATE_CANDIDATE.json').exists())
            self.assertFalse((case / 'PRIVATE_ARCHIVE.glb').exists())
        base, ctx, provenance = self.private_fixture(); case = base / 'oracle-direct'; case.mkdir()
        with mock.patch.object(S, 'module', wraps=S.module) as observed:
            W.perform({'phase': 'oracle'}, ctx, provenance['rows'][0], case)
        self.assertEqual([Path(call.args[1]).name for call in observed.call_args_list], ['oracle.py'])

    def test_03_root_freeze_is_required_before_output_or_candidate(self):
        target = self.base / 'outputs/PRIVATE-pmx-observation-without-freeze'
        with mock.patch.object(R, 'run_child', side_effect=AssertionError('no child allowed')):
            with self.assertRaises(S.Refusal):
                R.run_batch('compare', self.ctx, target, oracle_manifest=self.oracle_path, oracle_sha=self.oracle_sha)
        self.assertFalse(target.exists())

    def test_04_manifest_sha_tamper_refuses_before_output(self):
        target = self.base / 'outputs/PRIVATE-pmx-observation-wrong-sha'
        with self.assertRaises(S.Refusal):
            R.run_batch('compare', self.ctx, target, oracle_manifest=self.oracle_path, oracle_sha='0' * 64, root_frozen=True)
        self.assertFalse(target.exists())

    def test_05_frozen_witness_tamper_precedes_candidate_import(self):
        batch = self.base / 'outputs/PRIVATE-pmx-observation-tamper'; batch.mkdir()
        (batch / 'case-0').mkdir()
        witness = (self.oracle_dir / 'case-0/PRIVATE_ORACLE.json').read_bytes()
        (batch / 'case-0/PRIVATE_ORACLE.json').write_bytes(witness + b' ')
        manifest_path = batch / 'PRIVATE_ORACLE_PHASE.json'; manifest_path.write_bytes(self.oracle_path.read_bytes())
        case = self.base / 'tamper-case'; case.mkdir()
        request = {'phase': 'compare', 'root_witness_frozen': True, 'case_index': 0,
                   'oracle_manifest': str(manifest_path), 'oracle_manifest_sha256': S.sha(manifest_path.read_bytes()),
                   'harness_index_sha256': None, 'code_binding': S.code_binding()}
        with mock.patch.object(S, 'module', side_effect=AssertionError('candidate must not import')):
            with self.assertRaises(S.Refusal): W.perform(request, self.ctx, self.provenance['rows'][0], case)
        self.assertFalse((case / 'PRIVATE_CANDIDATE.json').exists())

    def test_06_boolean_case_index_is_not_integer(self):
        value = copy.deepcopy(self.oracle); value['cases'][0]['case_index'] = False
        batch = self.base / 'outputs/PRIVATE-pmx-observation-bool'; batch.mkdir()
        path = batch / 'PRIVATE_ORACLE_PHASE.json'; S.save(path, value)
        with self.assertRaises(S.Refusal): S.frozen_manifest(self.ctx, path, S.sha(path.read_bytes()), None, S.code_binding())

    def test_07_provenance_claims_do_not_replace_actual_hash_checks(self):
        _base, ctx, value = self.private_fixture(); row = value['rows'][0]
        self.assertTrue(S.load_provenance(ctx)['source_read_only_and_unchanged'])
        copied = Path(row['copy']); changed = bytearray(copied.read_bytes()); changed[-1] ^= 1; copied.write_bytes(changed)
        with self.assertRaises(S.Refusal): S.read_pair(row)

    def test_08_same_length_wrong_hash_and_resource_caps_refuse(self):
        _base, _ctx, value = self.private_fixture(); row = value['rows'][0]
        with self.assertRaises(S.Refusal): S.read_stable(row['source'], S.SOURCE_CAP, expected_sha='0' * 64)
        with self.assertRaises(S.Refusal): S.read_stable(row['source'], 10)
        bad = dict(row['source_identity']); bad['st_size'] = S.SOURCE_CAP + 1
        with self.assertRaises(S.Refusal): S.validate_stamp(bad)

    def test_09_exact_schema_rows_and_strict_stamps(self):
        base, ctx, value = self.private_fixture()
        for mutate in (lambda v: v.update(extra=True), lambda v: v['rows'].pop(),
                       lambda v: v['rows'][0]['source_identity'].update(st_nlink=True),
                       lambda v: v['rows'][0]['copy_identity'].update(st_size=339.0),
                       lambda v: v['rows'][1].update(copy=v['rows'][0]['copy'])):
            bad = copy.deepcopy(value); mutate(bad); raw = S.canonical(bad)
            (base / 'copies/PROVENANCE.json').write_bytes(raw)
            with self.assertRaises(S.Refusal): S.load_provenance(S.context(base, S.sha(raw)))

    def test_10_synthetic_context_cannot_select_real_roots(self):
        with self.assertRaises(S.Refusal): S.context(S.ROOT / 'output', '0' * 64)
        with self.assertRaises(S.Refusal): S.output_path(self.ctx, self.base / 'PRIVATE-pmx-observation-escape')
        with self.assertRaises(S.Refusal): S.output_path(self.ctx, self.base / 'outputs/PUBLIC-anything')
        with mock.patch.object(S, 'safe', side_effect=AssertionError('must not inspect actual roots')):
            ctx = S.context()
        self.assertFalse(ctx['synthetic']); self.assertEqual(ctx['provenance_sha'], S.PROVENANCE_SHA)

    def test_11_exact_current_source_binding_is_checked(self):
        request = {'synthetic_root': str(self.base), 'code_binding': S.code_binding()}
        S.verify_code(request); request['code_binding']['worker.py'] = '0' * 64
        with self.assertRaises(S.Refusal): S.verify_code(request)

    def test_12_timeout_terminates_only_retained_child_and_reaps(self):
        base, _ctx, _value = self.private_fixture(); case = base / 'timeout'; case.mkdir()
        child = mock.Mock(); child.returncode = -9
        child.wait.side_effect = [subprocess.TimeoutExpired(['owned'], 60), subprocess.TimeoutExpired(['owned'], 5), -9]
        child.poll.return_value = -9
        with mock.patch.object(R.subprocess, 'Popen', return_value=child) as popen:
            result = R.run_child(['owned'], case)
        popen.assert_called_once(); child.terminate.assert_called_once_with(); child.kill.assert_called_once_with()
        self.assertEqual(child.wait.call_count, 3)
        self.assertTrue(result['timed_out']); self.assertTrue(result['retained_Popen_reaped'])

    def test_13_public_projection_has_no_artist_or_payload_data(self):
        for public in (self.oracle_public, self.compare_public):
            raw = json.dumps(public)
            for secret in ('SECRET_ARTIST_CANARY', str(self.base), self.provenance['rows'][0]['sha256'], self.oracle_sha):
                self.assertNotIn(secret, raw)
            self.assertEqual(public['cases'], 4); self.assertEqual(public['python_allocation_measured_cases'], 4)
            self.assertIs(public['synthetic_inputs'], True)
            self.assertGreater(public['max_observed_python_allocation_peak_bytes'], 0)
            for key in ('Windows_peak_RSS_measured', 'hard_memory_enforcement', 'IO_confinement_claimed',
                        'actual_model_conversion_or_HAS_retention', 'native_protocol_qualified', 'simulation_or_production_adoption'):
                self.assertIs(public[key], False)

    def test_14_unmeasured_metrics_remain_null(self):
        public = R.project('oracle', [{'completed': False, 'preserved': False, 'process': {}, 'python_tracemalloc_peak_bytes': None}], True)
        self.assertIsNone(public['max_parent_wall_seconds'])
        self.assertIsNone(public['max_observed_python_allocation_peak_bytes'])
        self.assertEqual(public['python_allocation_measured_cases'], 0)

    def test_15_malformed_measured_receipt_refuses(self):
        receipt = S.read_json(self.oracle_dir / 'case-0/PRIVATE_RECEIPT.json', 131072)
        for key, bad in (('python_tracemalloc_peak_bytes', True), ('child_wall_seconds', 'SECRET_ARTIST_CANARY'),
                         ('case_index', False), ('native_protocol_qualified', True)):
            value = copy.deepcopy(receipt); value[key] = bad
            with self.assertRaises(S.Refusal): R.checked_receipt(value, 'oracle', 0)

    def test_16_bounded_strict_json_and_exclusive_private_writes(self):
        with self.assertRaises(S.Refusal): S.parse(b'{"x":1,"x":2}')
        with self.assertRaises(S.Refusal): S.parse(b'{"x":NaN}')
        base, _ctx, _value = self.private_fixture(); path = base / 'PRIVATE_once.json'
        S.save(path, {'ok': True})
        with self.assertRaises(FileExistsError): S.save(path, {'ok': False})
        with self.assertRaises(S.Refusal): S.save(base / 'PUBLIC_payload.json', {})
        with self.assertRaises(S.Refusal): W.write_bytes(base / 'PRIVATE_oversize', b'xx', 1)

    def test_17_unsupported_input_is_private_failure_with_preservation(self):
        base, _ctx, value = self.private_fixture(); row = value['rows'][0]
        raw = b'not an authored PMX'
        for role in ('source', 'copy'):
            path = Path(row[role]); path.write_bytes(raw); row[role + '_identity'] = S.stamp(path.lstat())
        row['sha256'] = S.sha(raw)
        provenance = S.canonical(value); (base / 'copies/PROVENANCE.json').write_bytes(provenance)
        ctx = S.context(base, S.sha(provenance)); target = base / 'outputs/PRIVATE-pmx-observation-refusal'
        manifest, public = R.run_batch('oracle', ctx, target)
        self.assertFalse(manifest['all_cases_completed_and_preserved'])
        self.assertFalse(manifest['cases'][0]['completed']); self.assertTrue(manifest['cases'][0]['preserved'])
        self.assertEqual(public['completed_cases'], 3); self.assertEqual(public['preserved_cases'], 4)
        self.assertNotIn('SECRET_ARTIST_CANARY', json.dumps(public))
        self.assertTrue((target / 'case-0/PRIVATE_FAILURE.log').is_file())
        self.assertFalse((target / 'case-0/PRIVATE_ORACLE.json').exists())

    def test_18_candidate_disagreement_cannot_create_archive(self):
        case = self.base / 'disagree-case'; case.mkdir()
        request = {'phase': 'compare', 'root_witness_frozen': True, 'case_index': 0,
                   'oracle_manifest': str(self.oracle_path), 'oracle_manifest_sha256': self.oracle_sha,
                   'harness_index_sha256': None, 'code_binding': S.code_binding()}
        capsule = S.read_json(self.compare_dir / 'case-0/PRIVATE_CANDIDATE.json', 2 * 1024 * 1024)
        capsule['source_sha256'] = '0' * 64
        real_module = S.module
        def loaded(name, path):
            if Path(path).name == 'pmx_native_physics.py':
                return mock.Mock(read_pmx20_physics=mock.Mock(return_value=capsule))
            return real_module(name, path)
        with mock.patch.object(S, 'module', side_effect=loaded) as observed:
            with self.assertRaises(ValueError): W.perform(request, self.ctx, self.provenance['rows'][0], case)
        self.assertNotIn('pmx_archive.py', [Path(call.args[1]).name for call in observed.call_args_list])
        self.assertFalse((case / 'PRIVATE_ARCHIVE.glb').exists())

    def test_19_actual_hardlink_alias_is_refused(self):
        base, _ctx, value = self.private_fixture(); original = Path(value['rows'][0]['source'])
        alias = base / 'originals/authored-alias.pmx'
        try: os.link(original, alias)
        except OSError as error: self.skipTest('host does not support authored test hardlink: ' + type(error).__name__)
        self.assertGreater(original.lstat().st_nlink, 1)
        with self.assertRaises(S.Refusal): S.read_stable(original, S.SOURCE_CAP)

    def unresolved_mock(self):
        old = R.RETAINED_UNCONFIRMED[:]
        self.addCleanup(lambda: R.RETAINED_UNCONFIRMED.__setitem__(slice(None), old))
        child = mock.Mock(pid=12345, returncode=None)
        child.poll.return_value = None
        child.wait.side_effect = subprocess.TimeoutExpired(['owned-authored-mock'], 5)
        return child

    def test_20_unreaped_child_retained_with_private_ownership_failure(self):
        base, ctx, _value = self.private_fixture(); case = base / 'unreaped'; case.mkdir()
        child = self.unresolved_mock()
        with mock.patch.object(R.subprocess, 'Popen', return_value=child):
            with self.assertRaises(R.UnconfirmedClosure) as observed: R.run_child(['owned-authored-mock'], case)
        self.assertIs(observed.exception.process, child)
        self.assertIn(observed.exception, R.RETAINED_UNCONFIRMED)
        record = S.read_json(case / 'PRIVATE_OWNERSHIP_FAILURE.json', 131072)
        self.assertIs(record['process']['retained_Popen_reaped'], False)
        self.assertIs(record['lane_closed'], False); self.assertIs(record['arbitrary_PID_kill_authorized'], False)
        self.assertIs(record['Root_ownership_intervention_required'], True)
        with mock.patch.object(R, 'run_child', side_effect=AssertionError('no later launch')) as launched:
            with self.assertRaises(S.Refusal): R.run_batch('oracle', ctx, base / 'outputs/PRIVATE-pmx-observation-forbidden')
        launched.assert_not_called()

    def test_21_batch_stops_and_remaining_cases_stay_unstarted(self):
        base, ctx, _value = self.private_fixture(); child = self.unresolved_mock()
        target = base / 'outputs/PRIVATE-pmx-observation-unconfirmed'
        failure = R.UnconfirmedClosure(child, target / 'case-0', {'exit': None, 'timed_out': True, 'retained_Popen_reaped': False})
        with mock.patch.object(R, 'run_child', side_effect=failure) as launched:
            manifest, public = R.run_batch('oracle', ctx, target)
        self.assertEqual(launched.call_count, 1)
        self.assertFalse(manifest['all_cases_completed_and_preserved'])
        self.assertEqual(public['unstarted_cases'], 3); self.assertEqual(public['unconfirmed_child_closure_cases'], 1)
        self.assertTrue(public['Root_ownership_intervention_required'])
        self.assertTrue(all(not row['completed'] and not row['preserved'] for row in manifest['cases']))
        self.assertFalse((target / 'case-1').exists())
        record = S.read_json(target / 'PRIVATE_BATCH_STOPPED.json', 131072)
        self.assertEqual(record['unstarted_case_indices'], [1, 2, 3]); self.assertFalse(record['lane_closed'])

    def test_22_failed_ownership_record_write_still_retains_and_stops(self):
        base, _ctx, _value = self.private_fixture(); case = base / 'unreaped-write-refusal'; case.mkdir()
        child = self.unresolved_mock()
        with mock.patch.object(R.subprocess, 'Popen', return_value=child), mock.patch.object(S, 'save', side_effect=OSError('authored disk refusal')):
            with self.assertRaises(R.UnconfirmedClosure) as observed: R.run_child(['owned-authored-mock'], case)
        self.assertIs(observed.exception.process, child)
        self.assertIs(observed.exception.record['retained_Popen_reaped'], False)
        self.assertEqual(observed.exception.record['ownership_record_write_failure_type'], 'OSError')
        self.assertIn(observed.exception, R.RETAINED_UNCONFIRMED)

    def test_23_poll_failure_cannot_be_treated_as_closure(self):
        base, _ctx, _value = self.private_fixture(); case = base / 'unknown-handle'; case.mkdir()
        child = self.unresolved_mock(); child.poll.side_effect = OSError('authored unknown retained handle')
        with mock.patch.object(R.subprocess, 'Popen', return_value=child):
            with self.assertRaises(R.UnconfirmedClosure) as observed: R.run_child(['owned-authored-mock'], case)
        self.assertFalse(observed.exception.record['retained_Popen_reaped'])
        self.assertFalse(R.reaped(child))

    def test_24_log_stat_failure_cannot_bypass_unreaped_ownership(self):
        base, _ctx, _value = self.private_fixture(); case = base / 'unreaped-stat'; case.mkdir()
        child = self.unresolved_mock()
        with mock.patch.object(R.subprocess, 'Popen', return_value=child), mock.patch.object(Path, 'stat', side_effect=OSError('authored log stat refusal')) as observed_stat:
            with self.assertRaises(R.UnconfirmedClosure) as observed: R.run_child(['owned-authored-mock'], case)
        observed_stat.assert_not_called()
        self.assertIs(observed.exception.process, child)
        self.assertFalse(observed.exception.record['retained_Popen_reaped'])
        self.assertFalse(observed.exception.record['stream_size_observation_completed'])
        self.assertFalse(observed.exception.record['stream_acceptance_cap_passed'])


if __name__ == '__main__': unittest.main(verbosity=2)
