"""Synthetic prior-run gates only; no engine, process inventory or Git access."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from setter_support import validate_prior, sha


class PriorContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.paths = {name: root / (name + '.json') for name in (
            'saved_capture', 'prior_public', 'prior_comparison', 'prior_execution', 'prior_closure')}
        self.documents = {
            'saved_capture': {'synthetic': True},
            'prior_public': {},
            'prior_comparison': {
                'status': 'COHERENT_BOUNDARY_MEASUREMENT',
                'matched_exported_vertices': 9661,
                'unmatched_exported_vertices': 0,
                'original_raw_gate': {'historical_failure_reproduced': True}},
            'prior_execution': {'diagnostic_completed': True, 'private_job_desktop_closed': True,
                                'runtime_lease_released': True},
            'prior_closure': {'owned_count': 0},
        }
        self.flush()

    def flush(self):
        def write(name):
            self.paths[name].write_text(json.dumps(self.documents[name]), encoding='utf-8')
            return sha(self.paths[name].read_bytes())
        capture = write('saved_capture')
        self.documents['prior_public']['private_sha256'] = capture
        self.documents['prior_comparison']['private_capture_sha256'] = capture
        public = write('prior_public')
        comparison = write('prior_comparison')
        self.documents['prior_execution'].update(comparison_sha256=comparison, public_capture_sha256=public)
        write('prior_execution')
        write('prior_closure')

    def test_complete_coherent_closed_context(self):
        result = validate_prior(self.paths)
        self.assertEqual(set(result), {'private_capture_sha256', 'comparison_sha256', 'prior_closed'})
        self.assertIs(result['prior_closed'], True)

    def test_each_closure_boolean_must_be_literal_true(self):
        original = copy.deepcopy(self.documents)
        for key in ('diagnostic_completed', 'private_job_desktop_closed', 'runtime_lease_released'):
            for value in (False, 1, 'true', None):
                with self.subTest(key=key, value=value):
                    self.documents = copy.deepcopy(original)
                    self.documents['prior_execution'][key] = value
                    self.flush()
                    with self.assertRaises(ValueError): validate_prior(self.paths)

    def test_incomplete_match_or_wrong_status_refused(self):
        original = copy.deepcopy(self.documents)
        for key, value in (('status', 'synthetic'), ('matched_exported_vertices', 9660),
                           ('unmatched_exported_vertices', 1)):
            with self.subTest(key=key):
                self.documents = copy.deepcopy(original)
                self.documents['prior_comparison'][key] = value
                self.flush()
                with self.assertRaises(ValueError): validate_prior(self.paths)

    def test_historical_raw_failure_must_be_retained(self):
        self.documents['prior_comparison']['original_raw_gate']['historical_failure_reproduced'] = False
        self.flush()
        with self.assertRaises(ValueError): validate_prior(self.paths)

    def test_saved_capture_mutation_refused(self):
        self.paths['saved_capture'].write_text('{"synthetic":"changed"}', encoding='utf-8')
        with self.assertRaises(ValueError): validate_prior(self.paths)

    def test_comparison_mutation_after_execution_refused(self):
        self.paths['prior_comparison'].write_text(self.paths['prior_comparison'].read_text() + '\n', encoding='utf-8')
        with self.assertRaises(ValueError): validate_prior(self.paths)

    def test_public_capture_mutation_after_execution_refused(self):
        self.paths['prior_public'].write_text(self.paths['prior_public'].read_text() + '\n', encoding='utf-8')
        with self.assertRaises(ValueError): validate_prior(self.paths)

    def test_live_owned_process_refused(self):
        self.documents['prior_closure']['owned_count'] = 1
        self.flush()
        with self.assertRaises(ValueError): validate_prior(self.paths)

    def test_boolean_or_float_counts_refused(self):
        original = copy.deepcopy(self.documents)
        for name, key, value in (('prior_closure', 'owned_count', False),
                                 ('prior_closure', 'owned_count', 0.0),
                                 ('prior_comparison', 'matched_exported_vertices', 9661.0),
                                 ('prior_comparison', 'unmatched_exported_vertices', False)):
            with self.subTest(name=name, key=key, value=value):
                self.documents = copy.deepcopy(original)
                self.documents[name][key] = value
                self.flush()
                with self.assertRaises(ValueError): validate_prior(self.paths)


if __name__ == '__main__': unittest.main()
