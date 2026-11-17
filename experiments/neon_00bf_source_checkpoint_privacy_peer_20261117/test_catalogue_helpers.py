"""Synthetic selection/inventory checks, no file/manifest/native/Git reads."""
import unittest
import audit_catalogue_source as audit


class CatalogueHelperTests(unittest.TestCase):
    def test_literal_lists_extracted_without_executing_preparer(self):
        source = "FOLDERS='one two'.split()\nFILES='a.py b.json'.split()\nraise RuntimeError('must never execute')\n"
        self.assertEqual(audit.static_lists(source), {'FOLDERS': ['one', 'two'], 'FILES': ['a.py', 'b.json']})

    def test_selection_rejects_dynamic_or_missing_roles(self):
        for source in ["FOLDERS=get_data().split()\nFILES='a'.split()", "FOLDERS='one'.split()"]:
            with self.assertRaises((ValueError, TypeError)): audit.static_lists(source)

    def test_packet_roles_and_duplicate_payload_rejections(self):
        self.assertEqual(audit.packet_rows({'files': {'a.py': {'bytes': 1, 'sha256': 'x'}}}), [{'path': 'a.py', 'bytes': 1, 'sha256': 'x'}])
        for value in [{'files': [], 'payloads': []}, {'files': [{'path': 'a'}], 'objects': [{'path': 'a'}]}, {'files': True}]:
            with self.assertRaises(ValueError): audit.packet_rows(value)

    def test_array_scan_reports_location_count_without_publishing_values(self):
        value = {'files': [{'working_recipe': {'zero_based_lines': list(range(24))}}]}
        self.assertEqual(audit.suspicious_arrays(value), [{'field': '$.files[0].working_recipe.zero_based_lines', 'numeric_items': 24}])
        self.assertEqual(audit.suspicious_arrays({'hashes': ['a' * 64] * 50}), [])
        self.assertEqual(audit.suspicious_arrays({'small_UI_rect': [1, 2, 3, 4]}), [])

    def test_compact_numeric_array_scan_covers_small_arrays_without_values(self):
        self.assertEqual(audit.numeric_arrays({'assessment': {'axis': [0.2, 0.3, 0.4]}, 'pose': [1, 2]}), [{'field': '$.assessment.axis', 'numeric_items': 3}, {'field': '$.pose', 'numeric_items': 2}])
        self.assertEqual(audit.numeric_arrays({'hashes': ['abc'] * 40}), [])


if __name__ == '__main__': unittest.main(verbosity=2)
