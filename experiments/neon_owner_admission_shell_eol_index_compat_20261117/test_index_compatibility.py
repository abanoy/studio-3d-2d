"""Actual legacy consumer expression with RAM metadata; no admission/native run."""
from pathlib import Path
from types import SimpleNamespace
import ast, hashlib, json, unittest

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / 'neon_owner_admission_shell_eol_20261117'
PARENT_INDEX = '8ab1c8eb9f576a9c8a315ebf4df433fc4e4b8b4767ac44cdf64a2403467a2d42'
Q = HERE.parent / 'neon_owner_executor_shell_eol_20261117/qualified_inputs.py'
Q_SHA = '4ec96ec0aac53813600fa9807a7bfa065a542b2cd07e9413c031f0e7677f3a73'


def parent():
    raw = (PARENT / 'INDEX.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == PARENT_INDEX
    return json.loads(raw)


def exact_consumer(document):
    raw = Q.read_bytes(); assert hashlib.sha256(raw).hexdigest() == Q_SHA
    unit = ast.parse(raw)
    factory = next(n for n in unit.body if isinstance(n, ast.FunctionDef) and n.name == 'require_qualified_inputs')
    node = next(n for n in ast.walk(factory) if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == 'core_rows' for t in n.targets))
    namespace = {'A': SimpleNamespace(parse=json.loads),
                 'core_index': SimpleNamespace(read_bytes=lambda: json.dumps(document).encode())}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), '<exact legacy core INDEX consumer>', 'exec'), namespace)
    return namespace['core_rows']


class CompatibilityTests(unittest.TestCase):
    def test_original_failure_is_reproduced_before_any_external_admission(self):
        with self.assertRaises(KeyError): exact_consumer(parent())

    def test_payloads_only_schema_satisfies_exact_original_consumer(self):
        document = parent(); rows = document.pop('files'); document['payloads'] = rows
        result = exact_consumer(document)
        self.assertEqual(result, {r['path']: r for r in rows})
        pins = (HERE / 'PREDECESSOR_SOURCE_PINS.json').read_bytes()
        self.assertEqual(result['PREDECESSOR_SOURCE_PINS.json']['sha256'], hashlib.sha256(pins).hexdigest())

    def test_generic_consumer_and_single_membership_field_remain_compatible(self):
        document = parent(); rows = document.pop('files'); document['payloads'] = rows
        self.assertEqual(document.get('files', document.get('payloads')), rows)
        self.assertEqual([k for k in ('files', 'payloads', 'artifacts') if k in document], ['payloads'])

    def test_all_thirteen_predecessor_payload_bytes_are_exact(self):
        rows = parent()['files']; self.assertEqual(len(rows), 13)
        for row in rows:
            self.assertEqual((HERE / row['path']).read_bytes(), (PARENT / row['path']).read_bytes())


if __name__ == '__main__': unittest.main(verbosity=2)
