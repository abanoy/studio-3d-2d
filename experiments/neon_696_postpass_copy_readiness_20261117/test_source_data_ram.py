"""Synthetic RAM source metadata only; no Git, runtime, activation or copy."""
from pathlib import Path
import ast
import hashlib
import sys
import unittest

import source_data_ram as R

EXECUTOR = Path(__file__).resolve().parents[1] / 'neon_owner_review_executor_20261117'
sys.path.insert(0, str(EXECUTOR))
import admission_core as A
import qualified_inputs as Q
assert hashlib.sha256((EXECUTOR / 'admission_core.py').read_bytes()).hexdigest() == 'cdad5359f6fe6bf63d93bd95845680dec7f6eb2d041b265d05b05efe3ce1096f'
assert hashlib.sha256((EXECUTOR / 'qualified_inputs.py').read_bytes()).hexdigest() == '15fcdbe33334476957f0ed7bd88a3161a35363d673bf6eb9e520455ec232ec26'


def fixture():
    bodies = {'src/a.gd': b'authored source\n', 'docs/licenses.md': b'authored license\n'}
    listing = b''; check = b''; batch = b''
    for name, body in bodies.items():
        oid = hashlib.sha1(b'blob ' + str(len(body)).encode() + b'\0' + body).hexdigest().encode()
        listing += b'100644 blob ' + oid + b'\t' + name.encode() + b'\0'
        header = oid + b' blob ' + str(len(body)).encode() + b'\n'
        check += header; batch += header + body + b'\n'
    return bodies, listing, check, batch


class SourceDataTests(unittest.TestCase):
    def test_catalogue_is_consumed_by_original_readonly_guard(self):
        bodies, listing, check, batch = fixture()
        entries, request = R.archive_entries(Q, listing)
        sizes = R.archive_sizes(entries, check)
        catalogue, blobs = R.owner_catalogue(A, 'a' * 40, entries, sizes, batch)
        self.assertEqual(blobs, bodies); self.assertEqual(request.count(b'\n'), 2)
        class Git:
            responses = [listing, check, batch]
            def check_output(self, *args, **options): return self.responses.pop(0)
        actual, summary = Q.read_committed_archive(Git(), 'a' * 40, catalogue)
        self.assertEqual(actual, bodies); self.assertEqual(summary['files'], 2)

    def test_archive_policy_exclusions_and_windows_names(self):
        bodies, listing, check, batch = fixture()
        extra = b'100644 blob ' + b'0' * 40 + b'\toutput/private.bin\0'
        self.assertEqual(len(R.archive_entries(Q, listing + extra)[0]), 2)
        for name in ['../escape', 'docs/NUL.txt', 'src/a.gd/../other', 'docs/trailing.']:
            with self.assertRaises(ValueError): R.archive_entries(Q, b'100644 blob ' + b'0' * 40 + b'\t' + name.encode() + b'\0')
        with self.assertRaises(ValueError): R.archive_entries(Q, listing.replace(b'100644 blob', b'120000 blob', 1))
        with self.assertRaises(ValueError): R.archive_entries(Q, listing + listing[:listing.index(b'\0') + 1].replace(b'src/a.gd', b'SRC/a.gd'))

    def test_sizes_refuse_wrong_identity_and_existing_resource_overflow(self):
        bodies, listing, check, batch = fixture(); entries, _ = R.archive_entries(Q, listing)
        for changed in [check.replace(check[:40], b'0' * 40, 1), check.replace(b' blob ', b' tree ', 1), check.splitlines()[0] + b'\n']:
            with self.assertRaises(ValueError): R.archive_sizes(entries, changed)
        one = {'src/a.gd': ('100644', '1' * 40)}
        with self.assertRaises(ValueError): R.archive_sizes(one, b'1' * 40 + b' blob 134217729\n')

    def test_batch_framing_body_and_trailing_bytes_refuse(self):
        bodies, listing, check, batch = fixture(); entries, _ = R.archive_entries(Q, listing); sizes = R.archive_sizes(entries, check)
        for changed in [batch + b'extra', batch[:-1] + b'X', batch.replace(b'authored source', b'changed! source', 1)]:
            with self.assertRaises(ValueError): R.owner_catalogue(A, 'a' * 40, entries, sizes, changed)

    def source_maps(self):
        working = {'src/f%04d.gd' % index: b'authored\n' for index in range(1029)}
        committed = dict(working); working['src/f0000.gd'] = b'authored\r\n'
        return {name: A.digest(raw) for name, raw in working.items()}, working, committed

    def test_recipe_uses_original_guard_and_exact_four_field_schema(self):
        tested, working, committed = self.source_maps()
        recipe, proof = R.merged_recipe(A, 'a' * 40, tested, working, committed, True)
        self.assertEqual(proof['source_files'], 1029)
        self.assertEqual(recipe['src/f0000.gd']['source_mode'], 'candidate_tested_raw_with_explicit_Git_CRLF_LF_bridge')
        self.assertEqual(recipe['src/f0001.gd']['source_mode'], 'exact_Git_and_tested_working_bytes')
        self.assertEqual(set(recipe['src/f0000.gd']), {'tested_working_sha256', 'git_blob_sha256', 'canonical_content_sha256', 'source_mode'})

    def test_recipe_does_not_admit_unreviewed_EOL_content_or_raw_mismatch(self):
        tested, working, committed = self.source_maps()
        with self.assertRaises(ValueError): R.merged_recipe(A, 'a' * 40, tested, working, committed)
        changed = dict(committed); changed['src/f0000.gd'] = b'different\n'
        with self.assertRaises(ValueError): R.merged_recipe(A, 'a' * 40, tested, working, changed, True)
        changed = dict(tested); changed['src/f0001.gd'] = '0' * 64
        with self.assertRaises(ValueError): R.merged_recipe(A, 'a' * 40, changed, working, committed, True)
        for table in (tested, working, committed): table['data/a.png'] = table.pop('src/f0000.gd')
        with self.assertRaises(ValueError): R.merged_recipe(A, 'a' * 40, tested, working, committed, True)

    def test_no_IO_entry_or_activation_override(self):
        source = Path(R.__file__).read_text(encoding='utf-8'); tree = ast.parse(source)
        self.assertEqual({node.names[0].name for node in tree.body if isinstance(node, ast.Import)}, {'hashlib', 're'})
        self.assertFalse(any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {'open', 'exec', 'eval', 'compile', '__import__'} for node in ast.walk(tree)))
        self.assertNotIn('__main__', source)
        self.assertIsNone(Q.APPROVED_ACTIVATION_SHA256)
        with self.assertRaisesRegex(ValueError, 'UNREADY'): Q.require_activation_pin()


if __name__ == '__main__': unittest.main()
