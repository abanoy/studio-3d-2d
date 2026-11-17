"""Future after-copy admission. Current activation is deliberately absent.

Only source definitions are imported before the activation gate. The qualification
factory is reproduced in RAM with one reviewed lifecycle predicate: a new-copy
destination must now be the existing copied review. All other factory code stays
identical to the sealed executor. No product/controller/tool code is changed.
"""
from dataclasses import dataclass
from pathlib import Path
import ast
import copy
import hashlib
import importlib.util
import json
import re
import stat
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
EXPERIMENTS = ROOT / 'experiments'
APPROVED_VALIDATION_ACTIVATION_SHA256 = None
EXECUTOR_Q_SHA = '4ec96ec0aac53813600fa9807a7bfa065a542b2cd07e9413c031f0e7677f3a73'
EXECUTOR_C_SHA = '0d966a3c229fe21aed6a27c425ca1c6704cdb28d57e52a39c00098f88332bcf2'
CORE_SHA = 'c6ebc4b6e3999fbdecf13697a2ccb0ca9f0cafe3368beaf9767bd5f247247f76'
REFERENCE_C39_SHA = 'c39e3751621bc4428166d64b7c6f6120bd7ef39251ccf9bbbf8a46dca390ce21'
LEGACY_SHA = '0e5041bba2dd135c7580d32c46bbe3c02b3032fb072e0b64c9a3b918a6e11460'
_TOKEN = object()


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def parse(raw):
    def pairs(rows):
        value = {}
        for key, item in rows:
            need(key not in value, 'Duplicate metadata key'); value[key] = item
        return value
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite metadata')))


def equal(a, b):
    if type(a) is not type(b):
        return False
    if type(a) is dict:
        return a.keys() == b.keys() and all(equal(a[k], b[k]) for k in a)
    if type(a) is list:
        return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    return a == b


def no_links(path):
    for item in (path, *path.parents):
        try:
            info = item.lstat()
        except FileNotFoundError:
            continue
        need(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400,
             'Link/reparse path refused')


def identity(path):
    path = Path(path); no_links(path)
    before = path.stat(); need(path.is_file(), 'Regular proof/source file required')
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    after = path.stat()
    need((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns), 'Input changed while hashing')
    return {'bytes': after.st_size, 'mtime_ns': after.st_mtime_ns, 'sha256': digest}


def guarded(path, boundary):
    path = Path(path).absolute(); boundary = Path(boundary).absolute()
    no_links(path); no_links(boundary)
    need('..' not in path.parts and path.resolve().is_relative_to(boundary.resolve()), 'Exact owned proof boundary')
    return path


def require_activation():
    need(type(APPROVED_VALIDATION_ACTIVATION_SHA256) is str
         and re.fullmatch('[a-f0-9]{64}', APPROVED_VALIDATION_ACTIVATION_SHA256),
         'UNREADY: actual full/release/merge/copied-review validation activation is not sealed')


def read_bound(descriptor, boundary, protected, exact=None, maximum=16 * 1024 * 1024):
    need(type(descriptor) is dict and set(descriptor) == {'path', 'bytes', 'mtime_ns', 'sha256'}, 'Exact proof descriptor')
    need(type(descriptor['bytes']) is int and 0 <= descriptor['bytes'] <= maximum
         and type(descriptor['mtime_ns']) is int and type(descriptor['sha256']) is str
         and re.fullmatch('[a-f0-9]{64}', descriptor['sha256']), 'Bounded typed proof descriptor')
    path = guarded(descriptor['path'], boundary)
    need(exact is None or path == Path(exact).absolute(), 'Exact proof path differs')
    wanted = {k: descriptor[k] for k in ('bytes', 'mtime_ns', 'sha256')}
    need(identity(path) == wanted, 'Proof identity before read differs')
    raw = path.read_bytes()
    need(len(raw) == wanted['bytes'] and sha(raw) == wanted['sha256'] and identity(path) == wanted, 'Proof read identity differs')
    protected[str(path)] = wanted
    return raw


def packet(folder, expected_index, protected):
    folder = guarded(folder, EXPERIMENTS)
    need(folder.parent == EXPERIMENTS, 'Source packet must retain exact two-level ROOT layout')
    index_path = folder / 'INDEX.json'; before = identity(index_path)
    need(expected_index is None or before['sha256'] == expected_index, 'Exact source packet INDEX differs')
    raw = index_path.read_bytes(); need(identity(index_path) == before, 'Source INDEX changed')
    protected[str(index_path)] = before
    rows = parse(raw).get('files', parse(raw).get('payloads'))
    need(type(rows) is list and 0 < len(rows) <= 256, 'Bounded source packet membership')
    names = set(); total = 0
    for row in rows:
        name = row['path']
        need(type(name) is str and name and name not in names and '\\' not in name
             and not Path(name).is_absolute() and all(p not in ('', '.', '..') for p in name.split('/')), 'Source packet name')
        path = guarded(folder / name, folder); current = identity(path)
        need(type(row['bytes']) is int and current['bytes'] == row['bytes'] and current['sha256'] == row['sha256'] and current['bytes'] <= 16 * 1024 * 1024, 'Exact bounded source payload')
        names.add(name); total += current['bytes']; protected[str(path)] = current
    need(total <= 64 * 1024 * 1024 and {p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()} == names | {'INDEX.json'}, 'Closed bounded source packet')
    for path in folder.rglob('*'):
        no_links(path)
    return folder


def activated_Q_matches_reference(actual, reference, activation_raw):
    """Only the reviewed activation literal may differ in the future Q source."""
    need(sha(reference) == EXECUTOR_Q_SHA, 'Sealed inactive Q reference differs')
    tree = ast.parse(actual); normal = copy.deepcopy(tree)
    values = [n for n in normal.body if isinstance(n, ast.Assign)
              and any(isinstance(t, ast.Name) and t.id == 'APPROVED_ACTIVATION_SHA256' for t in n.targets)]
    need(len(values) == 1 and isinstance(values[0].value, ast.Constant)
         and type(values[0].value.value) is str and values[0].value.value == sha(activation_raw), 'Exact activated executor literal required')
    values[0].value = ast.Constant(None)
    need(ast.dump(normal, include_attributes=False) == ast.dump(ast.parse(reference), include_attributes=False),
         'Executor Q differs beyond approved activation literal')
    return tree


def existing_factory_ast(source):
    """Exact factory AST with the single reviewed post-copy lifecycle change."""
    tree = ast.parse(source)
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'require_qualified_inputs']
    need(len(functions) == 1, 'One original qualification factory')
    node = copy.deepcopy(functions[0]); changed = 0
    wanted = ast.dump(ast.parse('final.parent==WORKSPACE and not final.exists()', mode='eval').body, include_attributes=False)
    for item in ast.walk(node):
        if isinstance(item, ast.Call) and len(item.args) >= 2 and isinstance(item.args[1], ast.Constant) and item.args[1].value == 'exact fresh new review sibling required':
            need(ast.dump(item.args[0], include_attributes=False) == wanted, 'Original exact fresh-destination predicate changed')
            item.args[0] = ast.parse('final.parent==WORKSPACE and final.is_dir()', mode='eval').body
            item.args[1] = ast.Constant('exact existing copied review sibling required'); changed += 1
    need(changed == 1, 'Exactly one post-copy lifecycle predicate required')
    node.name = 'qualify_existing_review'
    return ast.fix_missing_locations(node)


def existing_review_factory(source, namespace):
    module = ast.fix_missing_locations(ast.Module(body=[existing_factory_ast(source)], type_ignores=[]))
    result = dict(namespace)
    exec(compile(module, '<reviewed after-copy qualification factory>', 'exec'), result)
    return result['qualify_existing_review']


def validate_copy_receipt(built, data):
    review = Path(data['final'])
    need(built.get('format') == 'has_neon_qualified_merge_owner_review_copy_1' and built.get('passed') is True
         and built.get('source_commit') == data['merged_revision'] and built.get('candidate_commit') == data['candidate_commit']
         and built.get('graphics_launched') is False and built.get('native_sources_included') is True,
         'Exact successful unlaunched concrete copy required')
    expected = {'functional_source_hashes': data['source_hashes'], 'support_source_hashes': data['support_source_hashes'],
                'source_hashes': {**data['source_hashes'], **data['support_source_hashes']},
                'source_delta_admission': data['source_delta_admission'], 'builder_preparation': data['preparation'],
                'full_run_gate': data['full_gate'], 'checkout_EOL_admission': data['eol_recipe']}
    need(all(equal(built.get(k), v) for k, v in expected.items()), 'Copy receipt does not join newly revalidated full/source/delta proofs')
    need(built.get('final') == str(review) and built.get('source_mode') == 'candidate_tested_raw_bytes_with_reviewed_Git_EOL_bridge'
         and built.get('support_source_mode') == 'exact_committed_nonfunctional_Git_blobs'
         and built.get('startup_or_final_replay') == 'UNRUN_root_private_187_validation_required', 'Fresh copy source/startup scope')
    need(type(built.get('native_source_files')) is int and built['native_source_files'] == 495
         and type(built.get('native_source_bytes')) is int and built['native_source_bytes'] == 451266730
         and type(built.get('sourceio_files')) is int and built['sourceio_files'] == 574
         and type(built.get('installed_exporter_sources_preserved')) is int and built['installed_exporter_sources_preserved'] == 120,
         'Original concrete copy input scopes differ')
    return True


def load_module(name, path):
    need(name not in sys.modules, 'Unexpected local qualification module already imported')
    spec = importlib.util.spec_from_file_location(name, path); value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    try:
        spec.loader.exec_module(value)
    except BaseException:
        sys.modules.pop(name, None); raise
    return value


@dataclass(frozen=True)
class ValidationInputs:
    data: dict
    _token: object
    _snapshot: str
    _Q: object
    _qualified: object


def snapshot(data):
    def plain(value):
        if isinstance(value, Path): return str(value)
        if type(value) is dict: return {k: plain(v) for k, v in value.items()}
        if type(value) in (list, tuple): return [plain(v) for v in value]
        need(type(value) in (str, int, float, bool, type(None)), 'Unserializable validation input')
        return value
    return sha(json.dumps(plain(data), sort_keys=True, separators=(',', ':'), allow_nan=False).encode())


def assert_validated(value):
    require_activation()  # No external path access while inactive, including direct runtime calls.
    need(type(value) is ValidationInputs and value._token is _TOKEN and snapshot(value.data) == value._snapshot,
         'Sealed validation token/data changed')
    value._Q.assert_admitted(value._qualified)
    need(all(identity(Path(path)) == row for path, row in value.data['protected_gate'].items()), 'Validation source/proof/main bytes changed')
    return value.data


def recheck(value):
    assert_validated(value)
    return True


def require_validated_inputs():
    require_activation()  # Before any review/native/functional/Git/qualification read.
    protected = {}
    activation_path = guarded(HERE / 'ACTIVATION.json', HERE)
    activation_before = identity(activation_path)
    need(activation_before['bytes'] <= 8 * 1024 * 1024, 'Bounded activation source')
    raw = activation_path.read_bytes()
    need(len(raw) <= 8 * 1024 * 1024 and sha(raw) == APPROVED_VALIDATION_ACTIVATION_SHA256, 'Validation activation exact identity')
    need(identity(activation_path) == activation_before, 'Activation changed while read')
    protected[str(activation_path)] = activation_before
    plan = parse(raw)
    need(plan.get('format') == 'has_root_after_copy_owner_validation_activation_1'
         and plan.get('status') == 'ROOT_REVIEWED_ACTUAL_FULL_RELEASE_MERGE_AND_FRESH_COPY', 'Actual after-copy root activation required')
    packet(HERE, None, protected)
    executor = packet(plan['executor_packet']['folder'], plan['executor_packet']['INDEX_sha256'], protected)
    source = (executor / 'qualified_inputs.py').read_bytes()
    activated_Q_matches_reference(source, (HERE / 'reference_qualified_inputs.py').read_bytes(), (executor / 'ACTIVATION.json').read_bytes())
    for name, digest in [('copy_executor.py', EXECUTOR_C_SHA), ('admission_core.py', CORE_SHA),
                         ('reference_close_terminal.py', REFERENCE_C39_SHA), ('legacy_result_gates.py', LEGACY_SHA)]:
        need(identity(executor / name)['sha256'] == digest, 'Exact activated executor dependency source differs')
    load_module('admission_core', executor / 'admission_core.py')
    load_module('copy_executor', executor / 'copy_executor.py')
    Q = load_module('qualified_inputs', executor / 'qualified_inputs.py')
    qualified = existing_review_factory(source, Q.__dict__)()
    data = Q.assert_admitted(qualified)
    review = Path(data['final']); built_path = review / 'BUILD-VERIFICATION.json'
    built = parse(read_bound(plan['build_verification'], review, protected, exact=built_path))
    validate_copy_receipt(built, data)
    executor_plan = parse((executor / 'ACTIVATION.json').read_bytes())
    context = parse(Path(executor_plan['candidate_context']['path']).read_bytes())
    canonical = Path(context['checkout']) / 'output' / context['run_name']
    need(context['commit'] == data['candidate_commit'] and context['functional_sources'] == 1029, 'Distinct actual tested candidate context')
    old_delta = parse((ROOT / 'experiments/native_five_review_after_full_20261116/source-delta.json').read_bytes())
    native52 = sorted(row['path'] for row in old_delta['changed_or_added'])
    need(len(native52) == 20, 'Exact original twenty source delta names')
    changed = sorted(set(native52) | set(data['source_delta_admission']['second']['changed_or_added_files']))
    protected.update(data['full_gate'])
    protected.update(data['preparation'])
    protected.update({str(ROOT / name): row for name, row in data['source_identities'].items()})
    value = {'root': ROOT, 'workspace': ROOT.parent, 'review': review, 'built': built, 'lock': data['lock'],
             'merged_revision': data['merged_revision'], 'source_commit': data['merged_revision'],
             'candidate_commit': data['candidate_commit'], 'canonical_run': canonical,
             'full_gate': data['full_gate'], 'preparation': data['preparation'], 'protected_gate': protected,
             'source_delta_admission': data['source_delta_admission'], 'legacy_admitted_changes': changed,
             'native52_admitted_changes': native52,
             'validated_source_context': {'candidate_commit': data['candidate_commit'], 'merged_revision': data['merged_revision'],
                                          'canonical_run': str(canonical), 'factory_lifecycle_delta': 'exact sibling absent to exact existing directory only'}}
    result = ValidationInputs(value, _TOKEN, snapshot(value), Q, qualified)
    assert_validated(result)
    return result
