"""Static compile/API checks only; do not import the glue or target helpers."""
from pathlib import Path
import ast, hashlib, json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main():
    raw = (HERE / 'prepare_executor.py').read_bytes(); tree = ast.parse(raw); compile(raw, 'prepare_executor.py', 'exec')
    top_imports = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    names = {a.name.split('.')[0] for n in top_imports if isinstance(n, ast.Import) for a in n.names}
    names |= {n.module.split('.')[0] for n in top_imports if isinstance(n, ast.ImportFrom)}
    assert names <= {'pathlib', 'types', 'argparse', 'hashlib', 'importlib', 'json', 're', 'stat', 'sys'}
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
    forbidden = {'build', 'main_copy', 'require_qualified_inputs', 'require_validated_inputs', '_admitted', 'Admitted', 'Popen', 'run', 'system', 'unlink', 'rmdir', 'replace', 'rename'}
    assert not any(isinstance(n.func, ast.Attribute) and n.func.attr in forbidden for n in calls)
    functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    collect = ast.get_source_segment(raw.decode(), functions['collect'])
    for api in ('check_candidate_bundle', 'ApprovedGit', "H['subprocess'] = Git", 'archive_sizes', 'owner_catalogue',
                'read_committed_archive', 'merged_recipe', '_historical52_proof', 'reconstruct_historical52',
                'check_historical_predecessors', 'revalidate_native_predecessor', 'check_reviewed_delta', 'assemble_copy_proposal'):
        assert api in collect
    assert collect.index("H['subprocess'] = Git") < collect.index('H.git_blobs(')
    assert collect.index('RAM.archive_sizes(') < collect.index('RAM.owner_catalogue(')
    assemble = ast.get_source_segment(raw.decode(), functions['assemble'])
    assert assemble.index('collect(api,') < assemble.index('target.mkdir(')
    assert assemble.index('target.mkdir(') < assemble.index('plan[field] = descriptor(')
    materialize = ast.get_source_segment(raw.decode(), functions['materialize'])
    assert 'root_approved_activation_sha256' in materialize and "api.R.render('executor', api.files['executor'], raw," in materialize
    assert "n not in extras] + ['INDEX.json']" in materialize
    assert "descriptor(api, target / name) == plan[field]" in materialize
    modules = {
        'neon_owner_executor_index_api_20261117/qualified_inputs.py': ('read_bound', 'read_committed_archive', '_historical52_proof', 'reconstruct_historical52', 'revalidate_native_predecessor', '_verify_packet_files'),
        'neon_owner_admission_shell_eol_index_compat_20261117/admission_core.py': ('check_candidate_bundle', 'check_historical_predecessors', 'check_reviewed_delta', 'assemble_copy_proposal'),
        'neon_696_postpass_copy_readiness_20261117/source_data_ram.py': ('archive_entries', 'archive_sizes', 'owner_catalogue', 'merged_recipe'),
        'neon_owner_activation_index_api_20261117/render_successor.py': ('encoded', 'sha', 'render'),
        'neon_owner_executor_index_api_20261117/copy_executor.py': ('helpers', '_write_blob'),
    }
    for relative, required in modules.items():
        source = ast.parse((ROOT / 'experiments' / relative).read_bytes())
        available = {n.name for n in source.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
        assert set(required) <= available
    print(json.dumps({'source_check': 'PASS', 'glue_sha256': hashlib.sha256(raw).hexdigest(),
                      'target_API_modules_parsed_only': len(modules), 'target_helpers_imported_or_executed': False,
                      'actual_data_Git_private_native_or_full_access': False}))


if __name__ == '__main__': main()
