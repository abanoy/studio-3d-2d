"""CPU-only entry/preservation tests; own public source refs and RAM objects only."""
import ast
import copy
import hashlib
import inspect
import io
from contextlib import redirect_stderr
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import patch
import replay_runtime as M


def layout():
    delta = {'historical_native52': 'authored', 'reviewed52_candidate': 'authored'}
    gate = {'synthetic/proof': {'sha256': '0' * 64}}
    revision = 'a' * 40
    return {'root': M.ROOT, 'workspace': M.WORKSPACE, 'review': M.WORKSPACE / 'HAS-Review-Neon-aaaaaaa-native', 'merged_revision': revision,
            'source_delta_admission': delta, 'full_gate': gate,
            'built': {'passed': True, 'source_commit': revision, 'native_sources_included': True, 'graphics_launched': False, 'source_delta_admission': copy.deepcopy(delta), 'full_run_gate': copy.deepcopy(gate)}}


class ReplayRuntime(unittest.TestCase):
    def test_CLI_requires_both_explicit_runtime_flags_before_admission(self):
        fake = SimpleNamespace(require_validated_inputs=lambda: (_ for _ in ()).throw(AssertionError('Admission reached')))
        for flags in ([], ['--run-gpu'], ['--lease-confirmed']):
            with self.subTest(flags=flags), patch.dict(sys.modules, {'validation_admission': fake}), patch.object(sys, 'argv', ['replay_runtime.py', '--output', str(M.ROOT / 'output/authored-unrun'), *flags]), redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as stopped: M.main()
                self.assertEqual(stopped.exception.code, 2)
    def test_token_refusal_is_before_layout_source_native_or_engine_access(self):
        fake = SimpleNamespace(assert_validated=lambda value: (_ for _ in ()).throw(ValueError('Unqualified token')))
        with patch.dict(sys.modules, {'validation_admission': fake}):
            with patch.object(M, 'lexical_layout', side_effect=AssertionError('layout called')), patch.object(M, 'identity', side_effect=AssertionError('file read')), patch.object(M, 'load', side_effect=AssertionError('JSON read')), patch.object(M, 'module', side_effect=AssertionError('controller loaded')), patch.object(M.subprocess, 'Popen', side_effect=AssertionError('process launched')):
                with self.assertRaisesRegex(ValueError, 'Unqualified token'): M.run(object(), M.ROOT / 'output/authored-unrun')
    def test_lexical_boundary_admits_only_the_new_exact_review_name(self):
        d = layout(); got = M.lexical_layout(d, M.ROOT / 'output/authored-unrun'); self.assertEqual(got[-1], 'a' * 40)
        for review in (M.WORKSPACE / 'HAS-Review-Neon-bbbbbbb-native', M.WORKSPACE / 'HAS-Review-20261115-Native-Hair-aaaaaaa', M.WORKSPACE / 'foreign/HAS-Review-Neon-aaaaaaa-native'):
            d = layout(); d['review'] = review
            with self.assertRaises(RuntimeError): M.lexical_layout(d, M.ROOT / 'output/authored-unrun')
    def test_lexical_output_refuses_relative_parent_root_or_escape(self):
        for output in (Path('relative'), M.ROOT / 'output', M.ROOT / 'output/../foreign', M.WORKSPACE / 'other/output'):
            with self.subTest(output=output):
                with self.assertRaises(RuntimeError): M.lexical_layout(layout(), output)
    def test_copy_receipt_cannot_claim_prior_graphics_or_wrong_revision(self):
        for key, value in [('passed', False), ('graphics_launched', True), ('native_sources_included', False), ('source_commit', 'b' * 40)]:
            d = layout(); d['built'][key] = value
            with self.assertRaises(RuntimeError): M.lexical_layout(d, M.ROOT / 'output/authored-unrun')
    def test_both_copy_gate_and_two_stage_delta_must_join(self):
        for key in ('source_delta_admission', 'full_run_gate'):
            d = layout(); d['built'][key] = {'unqualified': True}
            with self.assertRaises(RuntimeError): M.lexical_layout(d, M.ROOT / 'output/authored-unrun')
    def test_revision_and_root_cannot_be_redirected(self):
        for key, value in [('merged_revision', 'A' * 40), ('merged_revision', 'a' * 39), ('root', M.WORKSPACE / 'foreign'), ('workspace', M.WORKSPACE / 'foreign')]:
            d = layout(); d[key] = value
            with self.assertRaises(RuntimeError): M.lexical_layout(d, M.ROOT / 'output/authored-unrun')
    def test_native_helper_ledger_retains_real_on_tick_off_and_no_autoactivation(self):
        names = M.extra_names({'native_helper_preview': {'authored': True}, 'shape_ui': {'controls': ['a', 'b']}})
        self.assertEqual(len(names), len(set(names)))
        self.assertTrue({'native5.capability', 'native5.five_anchors', 'native5.no_autoactivation', 'native5.relocated_on', 'native5.relocated_fixed_tick', 'native5.relocated_off_exact', 'native5.relocated_protected_state'} <= set(names))
        self.assertEqual(len([n for n in names if n.startswith('native_helper.')]), 8)
        self.assertTrue({'shapes.binding_0', 'shapes.binding_1'} <= set(names))
    def test_optional_shape_controls_add_exactly_their_existing_binding_checks(self):
        plain = M.extra_names({}); shaped = M.extra_names({'shape_ui': {'controls': ['a', 'b', 'c']}})
        self.assertEqual(len(shaped) - len(plain), 5); self.assertEqual(shaped[-3:], ['shapes.binding_0', 'shapes.binding_1', 'shapes.binding_2'])
    def test_all_eleven_inherited_helpers_have_exact_original_AST(self):
        original = ast.parse((M.HERE / 'reference_validator.py').read_bytes())
        functions = {n.name: n for n in original.body if isinstance(n, ast.FunctionDef)}
        self.assertEqual(len(M.HELPERS), 11)
        for name in M.HELPERS:
            actual = ast.parse(inspect.getsource(getattr(M, name))).body[0]
            self.assertEqual(ast.dump(actual, include_attributes=False), ast.dump(functions[name], include_attributes=False), name)
    def test_all_five_public_reference_files_retain_exact_original_bytes(self):
        for name, digest in M.REFERENCE_PINS.items(): self.assertEqual(hashlib.sha256((M.HERE / name).read_bytes()).hexdigest(), digest, name)
    def test_original_four_case_tail_and_nine_finally_gates_raw_inverse(self):
        original = (M.HERE / 'reference_validator.py').read_text(encoding='utf8')
        old = original[original.index('    results = []; errors = []; attempts = 0\n'):original.index('\n\nif __name__ == "__main__":')]
        current = (M.HERE / 'replay_runtime.py').read_text(encoding='utf8')
        tail = current[current.index('    results = []; errors = []; attempts = 0\n'):current.index('\n\ndef main():')].rstrip('\n')
        tail = tail.replace('        capture("validation-recheck", lambda: V.recheck(value))\n', '')
        begin = tail.index('        software_checks = sum('); end = tail.index('        save(output/"verification.json", result)', begin)
        tail = tail[:begin] + tail[end:]
        tail = tail.replace('    return result', '    print(json.dumps({"passed": True, "verification": str(output/"verification.json"), "automatic_cleanup": False}))')
        self.assertEqual(tail, old.rstrip('\n'))
    def test_functional_context_excludes_only_original_nonfunctional_scopes(self):
        self.assertTrue(M.functional('src/app.gd')); self.assertTrue(M.functional('project.godot'))
        self.assertFalse(M.functional('docs/manual.md')); self.assertFalse(M.functional('tools/__pycache__/worker.pyc'))


if __name__ == '__main__': unittest.main(verbosity=2)
