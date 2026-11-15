"""CPU-only syntax/path/fixture-resolution checks, never execute the proposed driver."""
from pathlib import Path
import ast
import copy
import hashlib
import json
import os
import stat

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
TESTS = OUT / 'proposed/tests'
CHECKS = OUT / 'validation'
CHECKS.mkdir(exist_ok=True)

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

for path in (OUT / 'build_proposal.py', TESTS / 'verify_wind_review.py', TESTS / 'native_fixture_plans.wind_review.append.py'):
    ast.parse(path.read_text(encoding='utf-8'))
driver = (TESTS / 'verify_wind_review.py').read_text(encoding='utf-8')
for old_assumption in ('BASE.parents[2]', "BASE/'Studio'", 'runtime-review-reviewfixed.json', 'active-root-raw-sha256.json', 'output/compatibility/source-'):
    assert old_assumption not in driver

roles = {'vrm0': 'compatibility/source-1794448093-218-23395070',
         'vrm1': 'compatibility/source-1794448091-467-21644406',
         'backhair': 'back-hair-composition/1794516017604605200/input'}
manifest = {'format': 'has_wind_review_inputs_1', 'inputs': {
    role: {'source': relative + '/scene.glb', 'parameters': relative + '/parameters.json'}
    for role, relative in roles.items()}}
manifest_path = CHECKS / 'observed-manifest.json'
manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')

# Execute only the proposed pure resolver with explicitly supplied fixture roots.
# No run.py import, Godot invocation, native helper build or source preparation.
os.environ['HYBRID_NATIVE_FIXTURES'] = str(ROOT / 'output')
namespace = {'Path': Path, 'hashlib': hashlib, 'json': json, 'ROOT': ROOT,
             'fixture_output': lambda: ROOT / 'output'}
exec(compile((TESTS / 'native_fixture_plans.wind_review.append.py').read_text(encoding='utf-8'), '<proposed-pure-resolver>', 'exec'), namespace)
resolved = namespace['wind_review_native_plans'](manifest_path)
assert set(resolved['inputs']) == set(roles)
observed = {'scope': 'Read-only observation of approved current prepared bundles; these paths are not future driver defaults.',
            'future_relative_layout': json.loads((OUT / 'wind-review-inputs.example.json').read_bytes()),
            **resolved}
(OUT / 'observed-input-identities.json').write_text(json.dumps(observed, indent=2) + '\n', encoding='utf-8')

refusals = {}
bad = copy.deepcopy(manifest); del bad['inputs']['backhair']; refusals['missing-role'] = bad
bad = copy.deepcopy(manifest); bad['inputs']['vrm0']['source'] = '../outside.glb'; refusals['traversal'] = bad
bad = copy.deepcopy(manifest); bad['inputs']['vrm0']['source'] = 'C:/absolute.glb'; refusals['absolute'] = bad
bad = copy.deepcopy(manifest); bad['inputs']['vrm0']['parameters'] = manifest['inputs']['vrm1']['parameters']; refusals['wrong-pinned-report'] = bad
for label, document in refusals.items():
    path = CHECKS / (label + '.json'); path.write_text(json.dumps(document), encoding='utf-8')
    try: namespace['wind_review_native_plans'](path)
    except (ValueError, FileNotFoundError): pass
    else: raise AssertionError('Resolver accepted ' + label)
after = namespace['wind_review_native_plans'](manifest_path)
assert resolved == after

tree = ast.parse(driver)
definitions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in ('require', 'guard')]
guard_namespace = {'Path': Path, 'stat': stat}
exec(compile(ast.Module(body=definitions, type_ignores=[]), '<proposed-path-guards>', 'exec'), guard_namespace)
guard = guard_namespace['guard']
assert guard(CHECKS / 'fresh-file.json', CHECKS) == CHECKS / 'fresh-file.json'
for invalid in (CHECKS, CHECKS / '..' / 'escape.json', ROOT / 'output/owner-review/anything.json'):
    try: guard(invalid, CHECKS)
    except RuntimeError: pass
    else: raise AssertionError('Output guard accepted ' + str(invalid))

packet = ROOT / 'experiments/local_wind_review/production_port_candidate_20261112'
retained = ROOT / 'output/wind-review-production-port-20261112'
packet_files = [p for p in packet.rglob('*') if p.is_file()]
packet_mismatches = [str(p.relative_to(packet)) for p in packet_files if not (retained / p.relative_to(packet)).is_file() or sha(p) != sha(retained / p.relative_to(packet))]
assert not packet_mismatches
port = json.loads((TESTS / 'wind_review_port_files.json').read_bytes())
assert len(port['files']) == 16 and len({row['path'] for row in port['files']}) == 16
for row in port['files']:
    path = TESTS / 'wind_review_gpu_common.gd' if row['path'] == 'tests/wind_review_gpu_common.gd' else packet / 'overlay' / row['path']
    assert sha(path) == row['sha256']
request = json.loads((OUT / 'ribbon-request.json').read_bytes())
assert hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest().startswith('26e82282b205')

report = {'format': 'has_wind_main_driver_proposal_validation_1', 'python_ast_passed': True,
          'pure_native_resolver_exact_current_inputs_passed': True,
          'refused_cases': list(refusals), 'output_boundary_cases_passed': 4,
          'prepared_input_hash_size_mtime_preserved': True,
          'published_and_retained_packet_files_identical': len(packet_files),
          'packet_mismatches': packet_mismatches,
          'reviewed_port_file_bindings_checked': len(port['files']),
          'exact_ribbon_request_identity_confirmed': True,
          'godot_started': False, 'gpu_used': False, 'native_worker_started': False,
          'gdscript_parser_run': False, 'main_driver_executed': False,
          'main_or_prototype_source_mutations': False}
(OUT / 'validation.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, indent=2))
