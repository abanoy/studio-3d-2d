"""Synthetic RAM outputs only; no activation/proof reads or successor writes."""
from pathlib import Path
import ast
import copy
import json
import unittest

import render_successor as R

EXPERIMENTS = Path(__file__).resolve().parent.parent
FOLDERS = {'executor': 'neon_owner_executor_index_api_20261117',
           'validator': 'neon_owner_cold187_index_api_20261117'}
SYNTHETIC = b'{"synthetic_RAM_only":true,"not_an_activation":true}\n'


def source_fixture(kind):
    folder = EXPERIMENTS / FOLDERS[kind]
    index = (folder / 'INDEX.json').read_bytes()
    assert R.sha(index) == R.PARENTS[kind][0]
    names = [row['path'] for row in json.loads(index)['files']]
    return {'INDEX.json': index, **{name: (folder / name).read_bytes() for name in names}}


def extras(kind):
    return {name: b'{"synthetic_RAM_only":true}\n' for name in R.EXECUTOR_EXTRAS} if kind == 'executor' else {}


class RendererTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parents = {kind: source_fixture(kind) for kind in R.PARENTS}

    def rendered(self, kind):
        return R.render(kind, self.parents[kind], SYNTHETIC, R.sha(SYNTHETIC), extras(kind))

    def test_executor_literal_inverse_and_all_other_payloads_exact(self):
        result = self.rendered('executor'); parent = self.parents['executor']
        for name, raw in parent.items():
            if name not in ('INDEX.json', 'qualified_inputs.py'):
                self.assertEqual(result[name], raw)
        self.assertEqual(result['qualified_inputs.py'].replace(repr(R.sha(SYNTHETIC)).encode(), b'None', 1), parent['qualified_inputs.py'])

    def test_validator_literal_inverse_and_all_other_payloads_exact(self):
        result = self.rendered('validator'); parent = self.parents['validator']
        for name, raw in parent.items():
            if name not in ('INDEX.json', 'validation_admission.py'):
                self.assertEqual(result[name], raw)
        self.assertEqual(result['validation_admission.py'].replace(repr(R.sha(SYNTHETIC)).encode(), b'None', 1), parent['validation_admission.py'])

    def test_new_indexes_bind_closed_outputs_and_exact_extents(self):
        for kind in R.PARENTS:
            result = self.rendered(kind); index = json.loads(result['INDEX.json'])
            self.assertEqual(set(result), {row['path'] for row in index['files']} | {'INDEX.json'})
            self.assertEqual(index['payload_files'], len(result) - 1)
            self.assertEqual(index['payload_bytes'], sum(len(raw) for name, raw in result.items() if name != 'INDEX.json'))
            for row in index['files']:
                self.assertEqual((len(result[row['path']]), R.sha(result[row['path']])), (row['bytes'], row['sha256']))

    def test_renderer_does_not_mutate_caller_maps(self):
        for kind in R.PARENTS:
            parent = self.parents[kind]; before = copy.deepcopy(parent); supplied = extras(kind); extra_before = dict(supplied)
            result = R.render(kind, parent, SYNTHETIC, R.sha(SYNTHETIC), supplied)
            self.assertEqual(parent, before); self.assertEqual(supplied, extra_before)
            result.clear(); self.assertEqual(parent, before)

    def test_wrong_kind_or_parent_index_refuses(self):
        with self.assertRaises(ValueError): R.render('other', {}, SYNTHETIC, R.sha(SYNTHETIC))
        for kind in R.PARENTS:
            changed = dict(self.parents[kind]); changed['INDEX.json'] += b' '
            with self.assertRaises(ValueError): R.render(kind, changed, SYNTHETIC, R.sha(SYNTHETIC), extras(kind))

    def test_parent_changed_missing_or_added_payload_refuses(self):
        for kind in R.PARENTS:
            code = R.PARENTS[kind][1]
            for change in ('tamper', 'missing', 'extra'):
                parent = dict(self.parents[kind])
                if change == 'tamper': parent[code] += b'\n# changed\n'
                elif change == 'missing': del parent[code]
                else: parent['unreviewed.py'] = b'pass\n'
                with self.assertRaises(ValueError): R.render(kind, parent, SYNTHETIC, R.sha(SYNTHETIC), extras(kind))

    def test_unapproved_or_empty_activation_bytes_refuse(self):
        for raw, pin in [(SYNTHETIC, None), (SYNTHETIC, '0' * 64), (b'', R.sha(b'')), ('text', R.sha(SYNTHETIC))]:
            with self.assertRaises(ValueError): R.render('validator', self.parents['validator'], raw, pin)

    def test_exact_extra_metadata_roles_no_overwrite_or_traversal(self):
        parent = self.parents['executor']
        for supplied in ({}, {'../outside.json': b'{}'}, {'ACTIVATION.json': b'{}'}, {**extras('executor'), 'extra.json': b'{}'}):
            with self.assertRaises(ValueError): R.render('executor', parent, SYNTHETIC, R.sha(SYNTHETIC), supplied)
        with self.assertRaises(ValueError): R.render('validator', self.parents['validator'], SYNTHETIC, R.sha(SYNTHETIC), extras('executor'))

    def test_metadata_must_remain_bounded_byte_payloads(self):
        supplied = extras('executor'); supplied['OWNER_ARCHIVE_CATALOGUE.json'] = 'not bytes'
        with self.assertRaises(ValueError): R.render('executor', self.parents['executor'], SYNTHETIC, R.sha(SYNTHETIC), supplied)
        with self.assertRaises(ValueError): R.render('validator', self.parents['validator'], b'x' * (8 * 1024 * 1024 + 1), '0' * 64)

    def test_literal_transform_preserves_CRLF_and_refuses_noninactive_or_duplicate_gate(self):
        raw = b'GATE = None\r\nOTHER = 7\r\n'
        changed = R.activation_literal(raw, 'GATE', R.sha(SYNTHETIC))
        self.assertEqual(changed.replace(repr(R.sha(SYNTHETIC)).encode(), b'None'), raw)
        for source in (b'GATE = 1\n', b'GATE = None\nGATE = None\n', b'OTHER = None\n', b'GATE = OTHER = None\n'):
            with self.assertRaises(ValueError): R.activation_literal(source, 'GATE', R.sha(SYNTHETIC))

    def test_derivation_labels_parent_CPU_as_historical_and_qualification_unexecuted(self):
        for kind in R.PARENTS:
            value = json.loads(self.rendered(kind)['ACTIVATION_DERIVATION.json'])
            self.assertTrue(value['raw_byte_and_whole_AST_inverse'])
            self.assertTrue(value['parent_CPU_and_readiness_documents_are_historical'])
            self.assertFalse(value['semantic_qualification_or_actual_activation_or_copy_or187_executed'])

    def test_renderer_has_no_filesystem_process_or_execution_entry(self):
        source = Path(R.__file__).read_text(encoding='utf-8'); tree = ast.parse(source)
        imports = {node.names[0].name for node in tree.body if isinstance(node, ast.Import)}
        self.assertEqual(imports, {'ast', 'hashlib', 'json', 're'})
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotIn(node.func.id, {'open', 'exec', 'eval', 'compile', '__import__'})
        self.assertNotIn("__name__ == '__main__'", source)


if __name__ == '__main__': unittest.main()
