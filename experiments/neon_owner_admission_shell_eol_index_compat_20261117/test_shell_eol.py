"""Synthetic exact-three-path EOL bridges; no native/process/Git/copy operations."""
from pathlib import Path
import ast, copy, importlib.util, unittest
import admission_core as A
import derive_source as D

HERE = Path(__file__).resolve().parent


def shell_sources(names=D.SHELLS):
    work = {'src/synthetic_%04d.gd' % i: b'authored\n' for i in range(1029 - len(names))}
    work.update({name: b'#!/bin/sh\r\nprintf synthetic\r\n' for name in names})
    git = {name: raw.replace(b'\r\n', b'\n') for name, raw in work.items()}
    tested = {name: A.digest(raw) for name, raw in work.items()}
    recipe = {name: {'tested_working_sha256': tested[name], 'git_blob_sha256': A.digest(git[name]),
                     'canonical_content_sha256': A.digest(A.canonical(raw, name)),
                     'source_mode': 'exact_Git_and_tested_working_bytes' if raw == git[name]
                         else 'candidate_tested_raw_with_explicit_Git_CRLF_LF_bridge'} for name, raw in work.items()}
    return [tested, work, git, recipe, 'a' * 40, True]


class ShellEOLTests(unittest.TestCase):
    def test_exact_three_path_delta_entire_inverse_and_reference_bytes(self):
        parents = D.parent_sources(); raw = (HERE / 'admission_core.py').read_bytes()
        self.assertEqual(D.render(parents['admission_core.py']), raw)
        self.assertEqual(raw.replace(D.NEW, D.OLD, 1), parents['admission_core.py'])
        old_unit, new_unit = ast.parse(parents['admission_core.py']), ast.parse(raw)
        assignments = lambda u: {n.targets[0].id: ast.literal_eval(n.value) for n in u.body
            if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id in ('TEXT', 'TEXT_PATHS')}
        old, new = assignments(old_unit), assignments(new_unit)
        self.assertEqual(new['TEXT'], old['TEXT']); self.assertEqual(new['TEXT_PATHS'] - old['TEXT_PATHS'], set(D.SHELLS))
        self.assertEqual(old['TEXT_PATHS'] - new['TEXT_PATHS'], set())
        for name in D.COPIES: self.assertEqual((HERE / name).read_bytes(), parents[name])

    def test_all_three_CRLF_working_LF_Git_bridges_preserve_tested_bytes(self):
        args = shell_sources(); before = copy.deepcopy(args)
        result = A.check_merged_sources(*args)
        self.assertEqual(result['source_files'], 1029); self.assertEqual(args, before)
        for name in D.SHELLS:
            self.assertNotEqual(args[0][name], A.digest(args[2][name]))
            self.assertEqual(A.canonical(args[1][name], name), args[2][name])

    def test_old_core_refusal_reproduced_without_changing_its_source(self):
        spec = importlib.util.spec_from_file_location('original_shell_EOL_core_cpu_only', D.PARENT / 'admission_core.py')
        old = importlib.util.module_from_spec(spec); spec.loader.exec_module(old)
        with self.assertRaises(ValueError): old.check_merged_sources(*shell_sources())

    def test_explicit_checkout_EOL_permission_still_required(self):
        args = shell_sources(); args[-1] = False
        with self.assertRaises(ValueError): A.check_merged_sources(*args)

    def test_changed_shell_content_or_tested_raw_bytes_refuse(self):
        for name in D.SHELLS:
            args = shell_sources(); args[2][name] = b'#!/bin/sh\nprintf changed\n'
            args[3][name]['git_blob_sha256'] = A.digest(args[2][name])
            with self.assertRaises(ValueError): A.check_merged_sources(*args)
            args = shell_sources(); args[1][name] = args[2][name]
            with self.assertRaises(ValueError): A.check_merged_sources(*args)

    def test_undeclared_shell_case_alias_and_binary_EOL_stay_refused(self):
        for name in ('tools/linux/undeclared.sh', 'TOOLS/linux/run_test.sh', 'data/image.png'):
            args = shell_sources((name,))
            self.assertEqual(A.canonical(args[1][name], name), args[1][name])
            with self.assertRaises(ValueError): A.check_merged_sources(*args)

    def test_exact_LF_or_CRLF_Git_bytes_need_no_translation(self):
        for crlf in (False, True):
            args = shell_sources()
            for name in D.SHELLS:
                raw = args[1][name] if crlf else args[2][name]
                args[1][name] = args[2][name] = raw; args[0][name] = A.digest(raw)
                args[3][name] = {'tested_working_sha256': A.digest(raw), 'git_blob_sha256': A.digest(raw),
                                 'canonical_content_sha256': A.digest(A.canonical(raw, name)),
                                 'source_mode': 'exact_Git_and_tested_working_bytes'}
            args[-1] = False; A.check_merged_sources(*args)


if __name__ == '__main__': unittest.main(verbosity=2)
