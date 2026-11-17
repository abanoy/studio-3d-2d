"""Synthetic rejection cases; no Git or native calls."""
import copy
import hashlib
import unittest
import audit_reconstruction as audit


def row(blob=b'a\nb\n', selected=None):
    selected = [1] if selected is None else selected
    working = b'a\nb\r\n'
    return {'blob_bytes': len(blob), 'blob_sha256': audit.sha(blob), 'git_blob': audit.git_id('blob', blob),
            'working_bytes': len(working), 'working_sha256': audit.sha(working),
            'working_recipe': {'kind': 'LF_blob_with_selected_CRLF_lines', 'zero_based_lines': selected}}


PATCH = b'diff --git a/test.txt b/test.txt\nindex 123..456 100644\n--- a/test.txt\n+++ b/test.txt\n@@ -1,3 +1,3 @@\n a\n-b\n+B\n c\n'


class ReconstructionTests(unittest.TestCase):
    def test_exact_mixed_EOL_and_inverse(self):
        self.assertEqual(audit.reconstruct_working(b'a\nb\n', row()), b'a\nb\r\n')

    def test_recipe_rejects_boolean_duplicate_unsorted_out_of_range(self):
        for selected in [[True], [1, 1], [1, 0], [-1], [2]]:
            with self.assertRaises(ValueError): audit.reconstruct_working(b'a\nb\n', row(selected=selected))

    def test_recipe_rejects_tampered_blob_or_working_identity(self):
        for key, value in [('blob_bytes', True), ('blob_bytes', 9), ('blob_sha256', '0' * 64),
                           ('git_blob', '0' * 40), ('working_bytes', True), ('working_sha256', '0' * 64)]:
            candidate = row(); candidate[key] = value
            with self.assertRaises(ValueError): audit.reconstruct_working(b'a\nb\n', candidate)

    def test_patch_positive_and_context_count_binary_path_negatives(self):
        self.assertEqual(audit.apply_text_patch(PATCH, {'test.txt': b'a\nb\nc\n'}), {'test.txt': b'a\nB\nc\n'})
        for patch in [PATCH.replace(b'-b\n', b'-x\n'), PATCH.replace(b'-1,3', b'-1,4'),
                      PATCH + b'GIT binary patch\n', PATCH.replace(b'test.txt', b'other.txt')]:
            with self.assertRaises(ValueError): audit.apply_text_patch(patch, {'test.txt': b'a\nb\nc\n'})

    def test_tree_round_trip_and_duplicate_or_truncated_rejections(self):
        entries = [(b'100644', b'a.txt', '1' * 40), (b'40000', b'dir', '2' * 40)]
        raw = audit.tree_bytes(entries)
        self.assertEqual(audit.tree_entries(raw), entries)
        for bad in [raw[:-1], audit.tree_bytes([entries[0], entries[0]])]:
            with self.assertRaises(ValueError): audit.tree_entries(bad)


if __name__ == '__main__': unittest.main(verbosity=2)
