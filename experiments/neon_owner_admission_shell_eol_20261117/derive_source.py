"""Exact three-path text admission; no functional source or actual proof writes."""
from pathlib import Path
import ast, hashlib, json

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / 'neon_owner_review_after_qualified_merge_20261117'
PARENT_INDEX = '5479aeea2485e6221589e874053e37197d66bc3dc8dd4acb86c8d53ec144715d'
PARENT_CORE_SHA = 'cdad5359f6fe6bf63d93bd95845680dec7f6eb2d041b265d05b05efe3ce1096f'
SHELLS = ('tools/linux/liveness_shim.sh', 'tools/linux/run_test.sh', 'tools/linux/shoot.sh')
OLD = b"TEXT_PATHS={'tests/blank','tests/krita_fixture/has_fixture.desktop','tools/docker/sourceio_metadata.Dockerfile','tools/docker/sourceio_worker.Dockerfile','tools/krita-runtime.Dockerfile'}"
NEW = OLD[:-1] + b",'tools/linux/liveness_shim.sh','tools/linux/run_test.sh','tools/linux/shoot.sh'}"
COPIES = ('legacy_result_gates.py', 'reference_close_terminal.py', 'reference_registry.json',
          'reference_test_terminal.py', 'test_admission_core.py', 'PREDECESSOR_SOURCE_PINS.json')


def sha(raw): return hashlib.sha256(raw).hexdigest()


def parent_sources():
    index = (PARENT / 'INDEX.json').read_bytes(); assert sha(index) == PARENT_INDEX
    rows = {r['path']: r for r in json.loads(index)['payloads']}; result = {}
    for name in ('admission_core.py', *COPIES):
        raw = (PARENT / name).read_bytes(); row = rows[name]
        assert (len(raw), sha(raw)) == (row['bytes'], row['sha256'])
        result[name] = raw
    return result


def render(raw):
    assert sha(raw) == PARENT_CORE_SHA and raw.count(OLD) == 1 and NEW not in raw
    changed = raw.replace(OLD, NEW, 1)
    assert changed.replace(NEW, OLD, 1) == raw
    a, b = ast.parse(raw), ast.parse(changed)
    functions = lambda unit: {n.name: ast.dump(n, include_attributes=False) for n in unit.body if isinstance(n, ast.FunctionDef)}
    assert functions(a) == functions(b)
    return changed


def main():
    rows = {}
    for name, raw in parent_sources().items():
        changed = render(raw) if name == 'admission_core.py' else raw
        with (HERE / name).open('xb') as stream: stream.write(changed)
        rows[name] = {'parent_sha256': sha(raw), 'derived_sha256': sha(changed),
                      'bytes': len(changed), 'literal_changes': 1 if name == 'admission_core.py' else 0}
    with (HERE / 'DERIVATION.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump({'format': 'has_exact_three_shell_text_path_admission_derivation_1',
                   'parent_INDEX_sha256': PARENT_INDEX, 'sources': rows, 'added_TEXT_PATHS': SHELLS,
                   'TEXT_suffixes_unchanged': True, 'whole_core_byte_inverse_exact': True,
                   'all_core_function_ASTs_exact': True, 'original27_tests_entire_source_exact': True,
                   'strict_reference_legacy_registry_and_native_receipt_gates_unchanged': True,
                   'functional_working_or_Git_bytes_changed': False}, stream, indent=2); stream.write('\n')
    print(json.dumps({'core_sha256': rows['admission_core.py']['derived_sha256'],
                      'exact_added_paths': 3, 'whole_inverse': True}))


if __name__ == '__main__': main()
