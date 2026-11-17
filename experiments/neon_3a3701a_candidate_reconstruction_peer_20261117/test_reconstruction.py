"""Five synthetic rejection groups; no Git, working source or native reads."""
import copy
import unittest
import audit_reconstruction as A


def row(blob, recipe, working):
    return {'blob_bytes': len(blob), 'blob_sha256': A.sha(blob), 'git_blob': A.git_id('blob', blob),
            'working_bytes': len(working), 'working_sha256': A.sha(working), 'working_recipe': recipe}


def patch_file(name, before, after):
    old = before.splitlines(keepends=True); new = after.splitlines(keepends=True)
    return (f'diff --git a/{name} b/{name}\nindex {A.git_id("blob", before)[:7]}..{A.git_id("blob", after)[:7]} 100644\n'
            f'--- a/{name}\n+++ b/{name}\n@@ -1,3 +1,3 @@\n').encode() + b' ' + old[0] + b'-' + old[1] + b'+' + new[1] + b' ' + old[2]


class ReconstructionTests(unittest.TestCase):
    def test_exact_CRLF_and_mixed_EOL_profiles_with_no_silent_normalization(self):
        blob = b'a\r\nb\r\n'; exact = row(blob, {'kind': 'exact'}, blob)
        self.assertEqual(A.reconstruct_working(blob, exact), blob)
        lf = b'a\nb\n'; mixed = row(lf, {'kind': 'LF_blob_with_selected_CRLF_lines', 'zero_based_lines': [1]}, b'a\nb\r\n')
        self.assertEqual(A.reconstruct_working(lf, mixed), b'a\nb\r\n')
        changed = row(lf, {'kind': 'exact'}, blob)
        with self.assertRaises(ValueError): A.reconstruct_working(lf, changed)
        changed = copy.deepcopy(exact); changed['working_recipe']['zero_based_lines'] = []
        with self.assertRaises(ValueError): A.reconstruct_working(blob, changed)

    def test_LF_recipe_boolean_duplicate_unsorted_out_of_range_and_CR_blob_refusals(self):
        for selected in ([True], [1, 1], [1, 0], [-1], [2]):
            candidate = row(b'a\nb\n', {'kind': 'LF_blob_with_selected_CRLF_lines', 'zero_based_lines': selected}, b'a\nb\r\n')
            with self.assertRaises(ValueError): A.reconstruct_working(b'a\nb\n', candidate)
        blob = b'a\r\nb\r\n'
        with self.assertRaises(ValueError): A.reconstruct_working(blob, row(blob, {'kind': 'LF_blob_with_selected_CRLF_lines', 'zero_based_lines': []}, blob))

    def test_blob_Git_and_working_identity_type_or_digest_mutations_refuse(self):
        blob = b'a\r\nb\r\n'; valid = row(blob, {'kind': 'exact'}, blob)
        for key, bad in (('blob_bytes', True), ('blob_bytes', 99), ('blob_sha256', '0' * 64), ('git_blob', '0' * 40),
                         ('working_bytes', True), ('working_bytes', 99), ('working_sha256', '0' * 64)):
            changed = copy.deepcopy(valid); changed[key] = bad
            with self.assertRaises(ValueError): A.reconstruct_working(blob, changed)

    def test_patch_both_EOL_domains_and_context_count_path_binary_index_negatives(self):
        old = {'lf.txt': b'a\nb\nc\n', 'crlf.txt': b'a\r\nb\r\nc\r\n'}
        new = {'lf.txt': b'a\nB\nc\n', 'crlf.txt': b'a\r\nB\r\nc\r\n'}
        patch = b''.join(patch_file(name, old[name], new[name]) for name in old)
        self.assertEqual(A.apply_text_patch(patch, old), new)
        bad_index = patch.replace(A.git_id('blob', old['lf.txt'])[:7].encode(), b'0000000', 1)
        for changed in (patch.replace(b'-b\n', b'-wrong\n'), patch.replace(b'-1,3', b'-1,4', 1),
                        patch.replace(b'\r\n', b'\n'), patch + b'GIT binary patch\n',
                        patch.replace(b'lf.txt', b'other.txt'), bad_index):
            with self.assertRaises(ValueError): A.apply_text_patch(changed, old)

    def test_tree_duplicate_truncated_and_commit_identity_shape_refusals(self):
        entries = [(b'100644', b'a.txt', '1' * 40), (b'40000', b'dir', '2' * 40)]
        raw = A.tree_bytes(entries); self.assertEqual(A.tree_entries(raw), entries)
        for changed in (raw[:-1], A.tree_bytes([entries[0], entries[0]])):
            with self.assertRaises(ValueError): A.tree_entries(changed)
        valid = b'tree ' + b'1' * 40 + b'\nparent ' + b'2' * 40 + b'\n\nmessage\n'
        self.assertEqual(A.commit_headers(valid), ('1' * 40, ['2' * 40]))
        for changed in (valid.replace(b'\n\n', b'\n'), valid.replace(b'1' * 40, b'x' * 40), b'tree ' + b'1' * 40 + b'\n' + valid):
            with self.assertRaises(ValueError): A.commit_headers(changed)


if __name__ == '__main__': unittest.main(verbosity=2)
