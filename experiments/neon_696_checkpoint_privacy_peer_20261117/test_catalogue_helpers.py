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

    def test_exact_literal_exception_maps_without_selector_execution(self):
        source = "UNSEALED={'obs':('a.json',)}\nFLAT_SEALS={'seal':('experiments/a.py','experiments/b.py')}\nraise RuntimeError('must not execute')\n"
        actual = audit.literal_maps(source)
        self.assertEqual(actual['UNSEALED'], {'obs': ('a.json',)})
        for bad in ["UNSEALED=load()\nFLAT_SEALS={}", "UNSEALED={}\nUNSEALED={}\nFLAT_SEALS={}",
                    "UNSEALED={'same':('a.json',)}\nFLAT_SEALS={'same':('b.py',)}",
                    "UNSEALED={'obs':('a.json','a.json')}\nFLAT_SEALS={}",
                    "UNSEALED={'obs':('../a.json',)}\nFLAT_SEALS={}"]:
            with self.assertRaises((ValueError, TypeError)): audit.literal_maps(bad)

    def test_flat_seal_refuses_duplicate_missing_or_arbitrary_source_roles(self):
        allowed = ('experiments/a.py', 'experiments/b.py')
        valid = {'format':'has_neon696_full_preflight_source_seal_1', 'source_files':[
            {'ROOT_relative_path':'experiments/a.py'}, {'ROOT_relative_path':'experiments/b.py'}]}
        self.assertEqual(audit.flat_rows(valid, allowed), valid['source_files'])
        for bad in [{'format':'other','source_files':valid['source_files']},
                    {'format':valid['format'],'source_files':[valid['source_files'][0]]},
                    {'format':valid['format'],'source_files':[valid['source_files'][0],valid['source_files'][0]]},
                    {'format':valid['format'],'source_files':[valid['source_files'][0],{'ROOT_relative_path':'private/model.json'}]}]:
            with self.assertRaises(ValueError): audit.flat_rows(bad, allowed)


if __name__ == '__main__': unittest.main(verbosity=2)
