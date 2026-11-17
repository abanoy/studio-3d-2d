"""Authored RAM context and exact public-source inverses; no native/root IO."""
from pathlib import Path
import copy
import datetime
import hashlib
import unittest
import diagnostic_support as S
import source_successor as D
from test_diagnostic import NOW, admission

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'native_normal_resource_diagnostic_20261117'


def lane():
    value = admission()
    value['proofs'] = {key: {'sha256': str(i) * 64} for i, key in enumerate(sorted(S.PROOFS), 1)}
    full = {'format': 'has_root_neon_ffcf_graphics_lease_release_1', 'released': True,
            'all_collected_jobs_desktops_closed_private': True, 'canonical_run': S.FULL_RUN,
            'source_commit': S.CANDIDATE, 'functional_sources': 1029, 'full_suite_passed': False,
            'final_full_report_used': False, 'suite_exit': 1, 'release_kind': 'closed_failed_partial_run',
            'released_utc': (NOW - datetime.timedelta(seconds=30)).isoformat()}
    unstarted = {'format': 'has_root_cold187_not_started_after_failed_full_1',
                 'disposition': 'NOT_STARTED_AFTER_FAILED_FULL', 'cold187_launched': False,
                 'root_native_lane_exclusive': True, 'candidate_commit': S.CANDIDATE,
                 'canonical_run': S.FULL_RUN, 'root_metadata_head': value['expected_metadata_head'],
                 'root_functional_commit': S.ROOT_FUNCTIONAL_COMMIT,
                 'root_functional_count': 1019, 'review_functional_count': 1029,
                 'full_release_sha256': value['proofs']['full_release']['sha256'],
                 'root_snapshot_sha256': value['proofs']['functional_snapshot']['sha256'],
                 'review_snapshot_sha256': value['proofs']['review_functional_snapshot']['sha256'],
                 'observed_utc': (NOW - datetime.timedelta(seconds=20)).isoformat()}
    return value, {'full_release': full, 'cold187_not_started_root_record': unstarted}


class FailedFullSuccessorTests(unittest.TestCase):
    def test_failed_full_and_explicit_unstarted_admission_needs_no_cold_result(self):
        value, data = lane(); S.validate_admission(value, NOW); S.validate_failed_full_lane(value, data)
        self.assertNotIn('cold187_verification', value['proofs'])
        self.assertNotIn('cold187_closure', value['proofs'])

    def test_never_relabels_root_as_candidate_or_merged1029(self):
        for field, bad in (('functional_commit', S.CANDIDATE), ('functional_count', 1029),
                           ('candidate_functional_count', 1019), ('cold187_disposition', 'PASSED')):
            value, _ = lane(); value[field] = bad
            with self.assertRaises(ValueError): S.validate_admission(value, NOW)

    def test_closed_failed_full_cannot_be_replaced_by_pass_unknown_or_wrong_context(self):
        for field, bad in (('full_suite_passed', True), ('final_full_report_used', True), ('suite_exit', 0),
                           ('suite_exit', False), ('released', False), ('functional_sources', 1019),
                           ('canonical_run', 'old-attempt'), ('source_commit', S.ROOT_FUNCTIONAL_COMMIT)):
            value, data = lane(); data['full_release'][field] = bad
            with self.assertRaises(ValueError): S.validate_failed_full_lane(value, data)

    def test_unstarted_record_is_explicit_and_has_separate_exact_roles(self):
        for field, bad in (('cold187_launched', True), ('cold187_launched', 0), ('root_native_lane_exclusive', False),
                           ('root_functional_count', 1029), ('review_functional_count', 1019),
                           ('root_metadata_head', 'a' * 40), ('root_functional_commit', S.CANDIDATE)):
            value, data = lane(); data['cold187_not_started_root_record'][field] = bad
            with self.assertRaises(ValueError): S.validate_failed_full_lane(value, data)

    def test_root_disposition_joins_release_and_both_source_maps(self):
        for field in ('full_release_sha256', 'root_snapshot_sha256', 'review_snapshot_sha256'):
            value, data = lane(); data['cold187_not_started_root_record'][field] = 'f' * 64
            with self.assertRaises(ValueError): S.validate_failed_full_lane(value, data)

    def test_root_not_started_observation_must_follow_release_and_be_fresh(self):
        for offset in (-150, -40, 1):
            value, data = lane(); data['cold187_not_started_root_record']['observed_utc'] = (NOW + datetime.timedelta(seconds=offset)).isoformat()
            with self.assertRaises(ValueError): S.validate_failed_full_lane(value, data)

    def test_exact_source_derivation_inverse_and_tamper_refusals(self):
        for name in D.SPEC:
            old = (OLD / name).read_text(encoding='utf-8'); current = (HERE / name).read_text(encoding='utf-8')
            self.assertEqual(D.derive(name, old), current); self.assertEqual(D.restore(name, current), old)
            with self.assertRaises(ValueError): D.derive(name, old + '\n')
            with self.assertRaises(ValueError): D.restore(name, current.replace('NOT_STARTED_AFTER_FAILED_FULL', 'PRETEND_READY', 1))

    def test_host_and_driver_are_byte_identical_to_sealed_predecessor(self):
        for name in ('diagnostic_host.py', 'root_runner.py'):
            self.assertEqual((HERE / name).read_bytes(), (OLD / name).read_bytes())


if __name__ == '__main__': unittest.main(verbosity=2)
