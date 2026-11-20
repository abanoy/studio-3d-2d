"""Synthetic byte-provenance cases; no native, graphical or filesystem inputs."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

try:
    from .receipt_provenance import classify
except ImportError:
    from receipt_provenance import classify


def receipt(path, desktop, exit_code=0, **extra):
    value = {'format': 'studio_private_desktop_1', 'desktop': desktop, 'exit': exit_code,
             'job_closed': True, 'desktop_closed': True, 'child_desktop_confirmed': True,
             'foreground_child_observed': False, 'desktop_switch_requested': False}
    value.update(extra)
    raw = json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
    return {'path': path, 'sha256': hashlib.sha256(raw).hexdigest(), 'value': value}


def copied(row, path):
    value = copy.deepcopy(row)
    value['path'] = path
    return value


class ReceiptProvenanceTests(unittest.TestCase):
    def test_failed_old_archives_are_proved_copies_and_new_normal_cancel_stay_current(self):
        old = receipt('experiments/old/private.json', 'old-failure', 2, error='Historical export failed')
        prior_output = receipt('output/earlier/private.json', 'prior-output')
        clone = copied(old, 'output/frozen/shipped-source/experiments/old/private.json')
        normal = receipt('output/new/normal.json', 'new-normal')
        cancel = receipt('output/new/cancel.json', 'new-cancel', 2, cancelled=True, error='Owned converter cancelled')
        result = classify([old, prior_output], [old, prior_output, clone, normal, cancel])
        self.assertEqual([row['path'] for row in result['current']], [normal['path'], cancel['path']])
        self.assertEqual(result['archived_copies'], [{'path': clone['path'], 'sha256': old['sha256'], 'desktop': 'old-failure',
                         'prior_originals': [{'path': old['path'], 'sha256': old['sha256']}],
                         'source_archive_paths': [old['path']], 'previous_path_sha256': None}])
        self.assertFalse(result['conflicts'])
        self.assertFalse(result['changed_original_archives'])

    def test_same_old_desktop_with_changed_bytes_is_not_silently_excluded(self):
        old = receipt('experiments/old/private.json', 'old', 1)
        tampered = receipt('output/new/copied.json', 'old', 0)
        result = classify([old], [old, tampered])
        self.assertFalse(result['current'])
        self.assertFalse(result['archived_copies'])
        self.assertEqual(result['conflicts'][0]['kind'], 'prior_desktop_unknown_bytes')
        self.assertEqual(result['conflicts'][0]['known_prior_sha256'], [old['sha256']])

    def test_original_archive_mutation_is_visible_even_with_unchanged_saved_copy(self):
        old = receipt('experiments/old/private.json', 'old', 1)
        changed = receipt(old['path'], 'old', 0)
        clone = copied(old, 'output/copy/private.json')
        result = classify([old], [changed, clone])
        self.assertEqual(result['changed_original_archives'], [{'kind': 'changed', 'path': old['path'],
                         'before_sha256': old['sha256'], 'after_sha256': changed['sha256']}])
        self.assertFalse(result['current'])
        self.assertEqual(len(result['archived_copies']), 1)

    def test_original_archive_missing_is_visible_even_with_matching_copy(self):
        old = receipt('experiments/old/private.json', 'old')
        result = classify([old], [copied(old, 'output/copy/private.json')])
        self.assertEqual(result['changed_original_archives'], [{'kind': 'missing', 'path': old['path'],
                         'before_sha256': old['sha256'], 'after_sha256': None}])
        self.assertEqual(len(result['archived_copies']), 1)

    def test_two_new_copy_paths_keep_individual_prior_original_proof(self):
        old = receipt('experiments/old/private.json', 'old')
        a, b = copied(old, 'output/a/private.json'), copied(old, 'output/b/private.json')
        result = classify([old], [old, a, b])
        self.assertEqual([row['path'] for row in result['archived_copies']], [a['path'], b['path']])
        self.assertTrue(all(row['prior_originals'] == [{'path': old['path'], 'sha256': old['sha256']}]
                            for row in result['archived_copies']))
        self.assertFalse(result['current'])

    def test_new_desktop_duplicates_remain_for_physical_field_deduplication(self):
        first = receipt('output/a/private.json', 'new')
        second = copied(first, 'output/b/private.json')
        third = receipt('output/c/private.json', 'new', error='Physical mismatch must be checked by caller')
        result = classify([], [first, second, third])
        self.assertEqual(result['current'], [first, second, third])
        self.assertFalse(result['archived_copies'])
        self.assertFalse(result['conflicts'])

    def test_duplicate_inventory_path_is_idempotent_and_payload_conflict_is_reported(self):
        first = receipt('output/a/private.json', 'new')
        result = classify([], [first, copy.deepcopy(first)])
        self.assertEqual(result['current'], [first])
        changed = receipt(first['path'], 'other')
        result = classify([], [first, changed])
        self.assertEqual(result['conflicts'][0]['kind'], 'conflicting_inventory_path')
        self.assertEqual(result['conflicts'][0]['inventory'], 'after')

    def test_changed_output_path_can_hold_a_genuinely_new_job(self):
        old = receipt('output/fixed/private.json', 'old')
        new = receipt(old['path'], 'new')
        result = classify([old], [new])
        self.assertEqual(result['current'], [new])
        self.assertFalse(result['conflicts'])
        self.assertFalse(result['changed_original_archives'])

    def test_missing_output_baseline_does_not_claim_original_archive_mutation(self):
        result = classify([receipt('output/temporary/private.json', 'old')], [])
        self.assertFalse(result['current'])
        self.assertFalse(result['changed_original_archives'])

    def test_added_source_archive_receipt_is_bank_drift_not_an_actual_job(self):
        new = receipt('experiments/new/private.json', 'new')
        result = classify([], [new])
        self.assertFalse(result['current'])
        self.assertEqual(result['changed_original_archives'][0]['kind'], 'added')

    def test_partial_genuine_current_receipts_are_not_dropped(self):
        value = {'format': 'studio_private_desktop_1', 'desktop': 'partial'}
        raw = json.dumps(value).encode()
        partial = {'path': 'output/partial.json', 'sha256': hashlib.sha256(raw).hexdigest(), 'value': value}
        result = classify([], [partial])
        self.assertEqual(result['current'], [partial])

    def test_sha_claim_cannot_hide_inconsistent_decoded_payload(self):
        old = receipt('experiments/old/private.json', 'old')
        forged = copied(old, 'output/copy/private.json')
        forged['value']['exit'] = 2
        result = classify([old], [old, forged])
        self.assertEqual(result['conflicts'][0]['kind'], 'same_sha_payload_differs')
        self.assertFalse(result['archived_copies'])

    def test_multiple_known_historical_serializations_require_one_exact_known_sha(self):
        a = receipt('experiments/a/private.json', 'old')
        b = receipt('experiments/b/private.json', 'old', seconds=1.0)
        clone = copied(b, 'output/new/copy.json')
        result = classify([a, b], [a, b, clone])
        self.assertFalse(result['conflicts'])
        self.assertEqual(result['archived_copies'][0]['prior_originals'], [{'path': b['path'], 'sha256': b['sha256']}])

    def test_inputs_and_returned_current_rows_are_independent(self):
        prior = [receipt('experiments/old/private.json', 'old')]
        after = [prior[0], receipt('output/new/private.json', 'new')]
        retained = copy.deepcopy((prior, after))
        result = classify(prior, after)
        self.assertEqual((prior, after), retained)
        result['current'][0]['value']['exit'] = 9
        self.assertEqual((prior, after), retained)

    def test_bad_path_sha_or_format_is_refused(self):
        for field, value in [('path', '../outside.json'), ('path', 'output/../experiments/x.json'),
                             ('path', 'output//x.json'), ('path', 'C:/outside.json'),
                             ('sha256', 'not-a-digest')]:
            row = receipt('output/new/private.json', 'new')
            row[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):classify([], [row])
        row = receipt('output/new/private.json', 'new');row['value']['format'] = 'mock'
        with self.assertRaises(ValueError):classify([], [row])

    def test_claimed_receipts_with_invalid_desktop_are_refused(self):
        for desktop in (None, '', False, True, 0, [], 'x' * 257):
            row = receipt('output/new/private.json', desktop)
            with self.subTest(desktop=desktop), self.assertRaises(ValueError):
                classify([], [row])

    def test_collector_parses_and_hashes_one_buffer_and_keeps_malformed_claim(self):
        try:
            from . import run_full as coordinator
        except ImportError:
            import run_full as coordinator
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'output').mkdir()
            (root / 'experiments').mkdir()
            valid = root / 'output/valid.json'
            malformed = root / 'output/malformed.json'
            valid.write_text(json.dumps({'format': 'studio_private_desktop_1', 'desktop': 'new'}))
            malformed.write_text(json.dumps({'format': 'studio_private_desktop_1', 'desktop': ''}))
            original_read = Path.read_bytes
            reads = {}
            def read_once(path):
                reads[path] = reads.get(path, 0) + 1
                return original_read(path)
            with mock.patch.object(coordinator, 'ROOT', root), mock.patch.object(Path, 'read_bytes', read_once):
                rows = coordinator.receipts()
            self.assertEqual(reads, {valid: 1, malformed: 1})
            self.assertEqual(len(rows), 2)
            for row in rows:
                raw = original_read(root / row['path'])
                self.assertEqual(row['value'], json.loads(raw))
                self.assertEqual(row['sha256'], hashlib.sha256(raw).hexdigest())
            with self.assertRaises(ValueError):
                classify([], rows)


if __name__ == '__main__':
    unittest.main()
