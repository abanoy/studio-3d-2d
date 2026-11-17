"""Authored RAM fixtures only; no actual successful run or certificate is supplied."""
import copy
import json
import unittest

import certificate_projection as C
import projection_core as P
import source_registry as S
import test_projection as Old

AUTHORED_COMMITMENT = 'a' * 64


def fixture():
    authored, old_registry = Old.fixture()
    fixed = {
        'expected_result_keys': list(S.EXPECTED_RESULT_KEYS),
        'expected_core_process_keys': list(S.EXPECTED_CORE_PROCESS_KEYS),
        'expected_movie_keys': list(S.EXPECTED_MOVIE_KEYS),
    }
    core, movies = set(fixed['expected_core_process_keys']), set(fixed['expected_movie_keys'])
    report = {name: {'private_omitted_canary': Old.CANARY} for name in fixed['expected_result_keys']}
    for name in core:
        report[name] = {'exit': 0, 'seconds': .25}
    for name in movies:
        report[name] = {'frames': 48, 'fps': '24/1', 'duration': '2.000000'}
    report['neon_workspace'] = copy.deepcopy(authored['neon_workspace'])
    report['neon_workspace']['reports']['behavior']['result']['named_checks'] = {name: True for name in S.BEHAVIOR_NAMES}
    return report


class CertificateProjection(unittest.TestCase):
    def test_authored_hash_is_only_a_commitment_and_source_domains_remain_exact(self):
        out = C.project(fixture(), root_private_validation_certificate_sha256=AUTHORED_COMMITMENT)
        self.assertEqual((len(out['result_keys']), len(out['core_process_groups']), len(out['movie_groups'])), (158, 36, 21))
        self.assertEqual(out['result_keys'], sorted(S.EXPECTED_RESULT_KEYS))
        self.assertEqual(out['neon_workspace']['checks'], 12504)
        certificate = out['root_private_validation_certificate']
        self.assertEqual(certificate['sha256'], AUTHORED_COMMITMENT)
        self.assertTrue(certificate['commitment_only'])
        self.assertFalse(certificate['certificate_contents_or_authority_validated_by_projection'])
        self.assertFalse(certificate['omitted_private_data_independently_validated_by_public_extract'])
        self.assertFalse(out['independent_validation_of_all_158_groups_claimed'])
        self.assertNotIn(Old.CANARY, json.dumps(out, allow_nan=False))

    def test_missing_or_malformed_commitment_cannot_project(self):
        for value in (None, '', True, 7, 'a' * 63, 'a' * 65, 'A' * 64, Old.CANARY, {'sha256': 'a' * 64}):
            with self.subTest(kind=type(value).__name__):
                with self.assertRaises(P.Refusal):
                    C.project(fixture(), root_private_validation_certificate_sha256=value)
        with self.assertRaises(TypeError):
            C.project(fixture())

    def test_supplied_counterfeit_registry_cannot_replace_frozen_names(self):
        report = fixture()
        name = next(name for name in report if name not in set(S.EXPECTED_CORE_PROCESS_KEYS) | set(S.EXPECTED_MOVIE_KEYS) | {'neon_workspace'})
        report['authored_replacement_name'] = report.pop(name)
        with self.assertRaises(P.Refusal):
            C.project(report, root_private_validation_certificate_sha256=AUTHORED_COMMITMENT)

    def test_omitted_private_failure_remains_unvalidated_and_archive_always_refuses(self):
        report = fixture()
        name = next(name for name in report if name not in set(S.EXPECTED_CORE_PROCESS_KEYS) | set(S.EXPECTED_MOVIE_KEYS) | {'neon_workspace'})
        report[name] = {'passed': False, 'private': Old.CANARY}
        out = C.project(report, root_private_validation_certificate_sha256=AUTHORED_COMMITMENT)
        self.assertFalse(out['independent_validation_of_all_158_groups_claimed'])
        self.assertNotIn(Old.CANARY, json.dumps(out))
        with self.assertRaises(P.Refusal):
            C.activate_archive(report=report, root_terminal=True, closed_inventory=True, certificate_sha256=AUTHORED_COMMITMENT)


if __name__ == '__main__':
    unittest.main()
