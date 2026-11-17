"""Source-only descriptor-root inventory. Does not import or run test wrappers."""
from pathlib import Path
import ast
import hashlib
import json

HERE = Path(__file__).resolve().parent
REVIEW = HERE.parents[1].parent / 'has-neon-review-20261116-c2d52ff'
TESTS = REVIEW / 'tests'
DESCRIPTORS = {'sfm-face-pilot.json', 'native-import-verification.json', 'physics-recording-result.json'}


def flatten(node):
    if isinstance(node, ast.Name) and node.id == 'ROOT': return ['ROOT']
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        left = flatten(node.left)
        if left and isinstance(node.right, ast.Constant) and type(node.right.value) is str: return left + [node.right.value]
    return None


def main():
    driver_raw = (TESTS / 'verify.py').read_bytes(); driver = ast.parse(driver_raw.decode('utf-8'))
    registered = {Path(node.value).name for node in ast.walk(driver) if isinstance(node, ast.Constant) and type(node.value) is str and node.value.endswith('.py')}
    records = []; failures = []; source_rows = []
    files = sorted(TESTS.rglob('*.py'))
    for path in files:
        raw = path.read_bytes(); source_rows.append({'path': path.relative_to(REVIEW).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest()})
        try: tree = ast.parse(raw.decode('utf-8'))
        except (SyntaxError, UnicodeError) as error: failures.append({'path': path.relative_to(REVIEW).as_posix(), 'error_type': type(error).__name__}); continue
        parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
        for node in ast.walk(tree):
            parts = flatten(node)
            if not parts: continue
            relative = '/'.join(parts[1:]).replace('\\', '/')
            if not relative.startswith('output/') or Path(relative).name not in DESCRIPTORS: continue
            # Record maximal expression once; an outer /suffix expression is a
            # distinct selection only when it adds to this descriptor path.
            ancestor = parents.get(node)
            if isinstance(ancestor, ast.BinOp) and isinstance(ancestor.op, ast.Div) and flatten(ancestor): continue
            parent = node
            while parent in parents and not isinstance(parent, (ast.Assign, ast.Call, ast.Expr)): parent = parents[parent]
            records.append({'path': path.relative_to(REVIEW).as_posix(), 'line': node.lineno, 'descriptor': relative,
                            'registered_in_default_driver_by_literal_filename': path.name in registered,
                            'context': ast.get_source_segment(raw.decode('utf-8'), parent)[:350]})
    classifications = {
        'tests/verify_shape_catalog.py': 'DEFAULT_INPUT_BYPASS_FIXED_BY_PRIMARY_PROPOSAL: face descriptor bypasses existing fixture_output import',
        'tests/verify_character_height.py': 'DEFAULT_INPUT_BYPASS_FIXED_BY_SEPARATE_PROPOSAL: raw VRM height subcase can disappear under stale descriptor',
        'tests/prepare_mima_fixture.py': 'MANUAL_GENERATOR_DEFAULT: explicit --pilot-report input/output argument; not registered in default verify.py',
        'tests/verify_native_import.py': 'MANUAL_NATIVE_IMPORT_GENERATOR_AND_EXPLICIT_RETAINED_INPUT_FALLBACK: not registered in default verify.py',
        'tests/verify_physics_recording.py': 'OUTPUT_WRITER: writes its own current physics result; descriptor read is already fixture_output in native_fixture_plans',
        'tests/verify_mmd_pose.py': 'LEGACY_STANDALONE_CONSUMER: no default driver reference; does not honor fixture override',
        'tests/verify_mmd_motion.py': 'LEGACY_STANDALONE_CONSUMER: no default driver reference; does not honor fixture override',
        'tests/verify_mmd_motion_progress.py': 'LEGACY_STANDALONE_CONSUMER: no default driver reference; does not honor fixture override',
        'tests/mmd_ik_reference.py': 'LEGACY_STANDALONE_REFERENCE: no default driver reference; does not honor fixture override',
    }
    for row in records: row['classification'] = classifications.get(row['path'], 'MANUAL_REVIEW_REQUIRED')
    applies = {}
    for name in ('verify_shape_catalog.py', 'verify_character_height.py'):
        proposed = HERE / name.replace('.py', '.proposed.py')
        applies[name] = {'current_sha256': hashlib.sha256((TESTS / name).read_bytes()).hexdigest(),
                         'proposed_sha256': hashlib.sha256(proposed.read_bytes()).hexdigest(),
                         'current_matches_proposal': (TESTS / name).read_bytes() == proposed.read_bytes(),
                         'original_snapshot': 'original-' + name}
    result = {'format': 'has_remaining_native_descriptor_root_source_audit_1', 'Python_files_scanned': len(files), 'parse_failures': failures,
              'default_driver_sha256': hashlib.sha256(driver_raw).hexdigest(), 'ROOT_output_descriptor_expressions': records,
              'source_files': source_rows, 'default_registered_consumers_requiring_lookup_fix': ['tests/verify_shape_catalog.py', 'tests/verify_character_height.py'],
              'default_native_import_generator_registered': 'verify_native_import.py' in registered,
              'current_selected_proposals': applies,
              'state_note': 'Root-owned selected applies may precede this current-source scan; retained original snapshots prove both prior bypasses. The agent did not apply them.',
              'important_distinction': 'ROOT/output/shape-catalog-verification.json in native_fixture_plans and its downstream wrappers is a fresh same-checkout result from the preceding registered catalogue stage; it must not be redirected to an old fixture-root result.',
              'scope_limits': ['Literal/AST source inventory only; no dynamic execution/call-graph proof.', 'Legacy standalone readers are disclosed but not modified or newly registered.',
                               'Native descriptors, bundles, raw models and active/full outputs are not read. Root owns all native identity and focused tests.'],
              'native_or_engine_CIM_Git_or_agent_review_source_mutation': False}
    (HERE / 'REMAINING_WRAPPERS_AUDIT.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'Python_files_scanned': len(files), 'parse_failures': len(failures), 'descriptor_ROOT_expressions': len(records),
                      'default_input_bypasses': [r['path'] for r in records if r['classification'].startswith('DEFAULT_INPUT_BYPASS')],
                      'unclassified': [r['path'] for r in records if r['classification'] == 'MANUAL_REVIEW_REQUIRED']}))


if __name__ == '__main__': main()
