"""Compile/API/order checks only; no target import or actual after-copy IO."""
from pathlib import Path
import ast, hashlib, json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main():
    raw = (HERE / 'prepare_validator.py').read_bytes(); tree = ast.parse(raw); compile(raw, 'prepare_validator.py', 'exec')
    imports = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    modules = {a.name.split('.')[0] for n in imports if isinstance(n, ast.Import) for a in n.names}
    modules |= {n.module.split('.')[0] for n in imports if isinstance(n, ast.ImportFrom)}
    assert modules <= {'pathlib', 'types', 'argparse', 'hashlib', 'importlib', 'json', 're', 'stat', 'sys'}
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
    forbidden = {'build', 'run', 'Popen', 'invoke', 'require_validated_inputs', 'require_qualified_inputs', 'ValidationInputs', '_admitted'}
    assert not any((isinstance(n.func, ast.Attribute) and n.func.attr in forbidden)
                   or (isinstance(n.func, ast.Name) and n.func.id in forbidden) for n in calls)
    functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    qualify = ast.get_source_segment(raw.decode(), functions['qualify_copy'])
    assert qualify.index('activated_Q_matches_reference') < qualify.index("V.load_module('admission_core'")
    assert qualify.index('for name, pin in') < qualify.index("V.load_module('admission_core'")
    for name in ('existing_review_factory', 'assert_admitted', 'validate_copy_receipt', 'fresh_copy', "built['source_hashes']", "data['source_identities']"):
        assert name in qualify
    assert "studio / 'output'" in qualify and "studio / '.godot'" in qualify
    assembly = ast.get_source_segment(raw.decode(), functions['assemble'])
    assert assembly.index('qualify_copy(') < assembly.index('write_new(')
    materialize = ast.get_source_segment(raw.decode(), functions['materialize'])
    assert materialize.index('root_approved_activation_sha256') < materialize.index('qualify_copy(')
    assert "api.R.render('validator', api.parent_files, raw," in materialize
    assert materialize.index('qualify_copy(') < materialize.index('target.mkdir(')
    assert "+ ['INDEX.json']" in materialize and 'api.V.packet(target,' in materialize
    old = ast.parse((ROOT / 'experiments/neon_owner_cold187_index_api_20261117/validation_admission.py').read_bytes())
    available = {n.name for n in old.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    assert {'packet', 'activated_Q_matches_reference', 'load_module', 'existing_review_factory', 'validate_copy_receipt', 'read_bound'} <= available
    constants = {n.targets[0].id: ast.literal_eval(n.value) for n in tree.body
                 if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and isinstance(n.value, ast.Constant)}
    for folder, index_key, source, source_key in (
        ('neon_owner_cold187_index_api_20261117', 'COLD_INDEX', 'validation_admission.py', 'V_SHA'),
        ('neon_owner_activation_index_api_20261117', 'RENDERER_INDEX', 'render_successor.py', 'RENDERER_SHA')):
        packet = ROOT / 'experiments' / folder
        assert hashlib.sha256((packet / 'INDEX.json').read_bytes()).hexdigest() == constants[index_key]
        assert hashlib.sha256((packet / source).read_bytes()).hexdigest() == constants[source_key]
    guide = (HERE / 'ROOT_LAUNCH.md').read_text(encoding='utf-8')
    future_host = guide.split('```python\n', 1)[1].split('```', 1)[0]
    compile(ast.parse(future_host), 'ROOT_LAUNCH.md:future-host', 'exec')
    print(json.dumps({'source_check': 'PASS', 'glue_sha256': hashlib.sha256(raw).hexdigest(),
                      'target_adapter_parsed_only': True, 'four_source_pins_checked': True,
                      'future_launch_guide_compiled_not_executed': True, 'target_helpers_imported_or_executed': False,
                      'actual_copy_private_native_current_full_or_Git_access': False}))


if __name__ == '__main__': main()
