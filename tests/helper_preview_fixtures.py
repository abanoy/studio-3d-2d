"""Caller-pinned, self-authored helper fixtures for CPU/app acceptance.

Install as tests/helper_preview_fixtures.py. The caller supplies a source root
and its SHA256 manifest; there is no search path or cached-result fallback.
This module invokes only the existing pure-Python helper protocol/builders.
"""
from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import math
import shutil
import stat
import sys

SOURCES = {
    'secondary_helpers': 'tools/secondary_helpers.py',
    'secondary_helpers_batch': 'tools/secondary_helpers_batch.py',
    'wind_helper_preview': 'tools/wind_helper_preview.py',
    'test_secondary_helpers': 'tests/test_secondary_helpers.py',
    'test_secondary_existing_joints': 'tests/test_secondary_existing_joints.py',
}
BACKHAIR_SHA = '4d62236d5c34468ea1f91c43089d6ce3c193be27b8460d53ea8d91d2238ab7b5'
BACKHAIR_BYTES = 7273728
PARAMETERS_SHA = 'f4e1850d9f4fa9359a72d43f3c945aaf61a1bd726538b025da31c4fa5f8071ba'
PARAMETERS_BYTES = 28797


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _path(path):
    value = Path(path)
    if not value.is_absolute() or '..' in value.parts:
        raise ValueError('An explicit absolute path without traversal is required')
    for part in (value, *value.parents):
        if part.exists():
            row = part.lstat()
            if stat.S_ISLNK(row.st_mode) or getattr(row, 'st_file_attributes', 0) & 0x400:
                raise ValueError('Fixture paths refuse links/reparse points')
    return value


def _stamp(path, limit=128 * 1024 * 1024):
    path = _path(path)
    info = path.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
        raise ValueError('Fixture input is not a bounded regular file')
    return {'path': str(path), 'sha256': _sha(path), 'bytes': info.st_size,
            'mtime_ns': info.st_mtime_ns}


def _same(records):
    try:
        return all(Path(row['path']).is_file() and _stamp(row['path']) == row for row in records)
    except (OSError, ValueError):
        return False


def _write(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def _source_records(root, expected_hashes):
    root = _path(root)
    if not (root / 'project.godot').is_file() or not isinstance(expected_hashes, dict):
        raise ValueError('Explicit main-layout source root and caller SHA manifest required')
    records = []
    for relative in SOURCES.values():
        expected = expected_hashes.get(relative)
        if not isinstance(expected, str) or len(expected) != 64 or any(c not in '0123456789abcdef' for c in expected):
            raise ValueError('Missing caller-pinned source: ' + relative)
        actual = _stamp(root / relative, 4 * 1024 * 1024)
        if actual['sha256'] != expected:
            raise ValueError('Caller-pinned source changed: ' + relative)
        records.append(actual)
    return records


def _modules(root, expected_hashes):
    """Import only exact approved files; never replace a foreign live module."""
    old_path = sys.path[:]
    old_cache = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        sys.path[:0] = [str(root / 'tests'), str(root / 'tools')]
        result = {}
        for name, relative in SOURCES.items():
            wanted = root / relative
            module = sys.modules.get(name)
            if module is not None:
                if Path(getattr(module, '__file__', '')).resolve() != wanted.resolve():
                    raise ValueError('A foreign module is already loaded: ' + name)
                if getattr(module, '__has_fixture_source_sha256', None) != expected_hashes[relative]:
                    raise ValueError('An untracked or stale module is already loaded: ' + name)
            else:
                spec = importlib.util.spec_from_file_location(name, wanted)
                module = importlib.util.module_from_spec(spec)
                sys.modules[name] = module
                spec.loader.exec_module(module)
                module.__has_fixture_source_sha256 = expected_hashes[relative]
            if Path(module.__file__).resolve() != wanted.resolve():
                raise ValueError('Imported module path changed: ' + name)
            result[name] = module
        return result
    finally:
        sys.path[:] = old_path
        sys.dont_write_bytecode = old_cache


def _native_records(native_input):
    if native_input is None:
        return []
    required = {'source', 'parameters', 'source_identity', 'parameters_identity'}
    if not isinstance(native_input, dict) or set(native_input) != required:
        raise ValueError('Optional native input needs complete explicit staged paths and identities')
    records = []
    for key, expected_sha, expected_bytes in (
            ('source', BACKHAIR_SHA, BACKHAIR_BYTES),
            ('parameters', PARAMETERS_SHA, PARAMETERS_BYTES)):
        identity = native_input[key + '_identity']
        if not isinstance(identity, dict) or set(identity) != {'sha256', 'bytes', 'mtime_ns'}:
            raise ValueError('Optional native input needs exact SHA/size/nsmtime identities')
        # Refuse unsupported declarations before opening their paths.
        if identity['sha256'] != expected_sha or identity['bytes'] != expected_bytes or type(identity['mtime_ns']) is not int:
            raise ValueError('Optional native input is not the retained supported Backhair pair')
        actual = _stamp(native_input[key])
        if {k: actual[k] for k in identity} != identity:
            raise ValueError('Explicit staged native input changed: ' + key)
        records.append(actual)
    return records


def expected_adapter_checks(cases):
    """Exact successful count for the unchanged adapter151 GDScript contract.

    Seven fixed predicates: three malformed-inventory controls plus source
    binding and result assertions for each late-edit/late-free control.
    Every successful case executes 23 predicates, an extra shape-index refusal
    when overrides is nonempty, and two observed-parent controls when present.
    This function describes expected coverage, not an executed test result.
    """
    return 7 + sum(23 + bool(row['shape'].get('overrides')) +
                   2 * ('ordinary_reparent' in row) for row in cases)


def _context(label, source_sha, shape):
    def digest(value):
        return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    return {'actor_id': 'self-authored-' + label, 'root_instance_id': '1',
            'revision': '0', 'frame': '5', 'authored_sha256': source_sha,
            'shape_sha256': digest(shape), 'bindings_sha256': digest({'fixture': label})}


def _candidate(modules, folder, label, source, options, shape, head=2):
    protocol = modules['wind_helper_preview']
    before = _stamp(source)
    context = _context(label, before['sha256'], shape)
    lease = protocol.DraftLease(folder / 'owned')
    token = lease.begin(source, [options], context, 'focused-single')
    prepared = protocol.build_candidate(token['job'], lease.owned_root)
    receipt = protocol.check_receipt(token['job'], lease.owned_root,
                                     token['request_sha256'], context,
                                     prepared['completion']['receipt_sha256'])
    if _stamp(source) != before:
        raise ValueError('Self-authored/original source changed during fixture preparation')
    candidate = token['job'] / receipt['candidate']['path']
    candidate_stamp = _stamp(candidate)
    if candidate_stamp['sha256'] != receipt['candidate']['identity']['sha256']:
        raise ValueError('Fixture candidate differs from the actual protocol completion')
    return {'label': label, 'head_node': head, 'source': str(source),
            'source_sha256': before['sha256'], 'candidate': str(candidate),
            'candidate_sha256': candidate_stamp['sha256'],
            'shape': copy.deepcopy(shape), 'operations': copy.deepcopy(receipt['operations'])}


def build(root: Path, destination: Path, expected_hashes: dict[str, str],
          native_input: dict | None = None) -> dict:
    """Publish fresh fixtures. Default is five synthetic adapter cases only.

    native_input, when supplied by the driver's validated native-input plan,
    contains absolute source/parameters paths and matching source_identity /
    parameters_identity dictionaries with sha256, bytes, mtime_ns. The retained
    source is copied before a new pure-Python existing-chain candidate is built;
    no historical derived GLB or user/default search path is consumed.
    """
    root = _path(root)
    destination = _path(destination)
    sources = _source_records(root, expected_hashes)
    protected_native = _native_records(native_input)
    if destination.exists():
        raise ValueError('Use a fresh fixture destination; no replacement or cleanup occurs')
    if destination.is_relative_to(root):
        relative = destination.relative_to(root)
        if not relative.parts or relative.parts[0] in {'.git', 'src', 'tests', 'tools', 'data'}:
            raise ValueError('Fixture output cannot target protected project source folders')
    destination.mkdir(parents=True, exist_ok=False)
    cases = []
    failure = None
    try:
        modules = _modules(root, expected_hashes)
        factory = modules['test_secondary_helpers']
        helper = modules['secondary_helpers']
        for label, weight, nonidentity, ordinary in (
                ('neutral', 0., False, False),
                ('morph-quarter', .25, False, False),
                ('morph-half-nonidentity', .5, True, False),
                ('ordinary-parent-identity', .25, False, True)):
            folder = destination / label
            folder.mkdir()
            source = folder / 'source.glb'
            glb = factory.two_panel_fixture(source, 'v1')
            if nonidentity:
                glb.doc['nodes'][1].update(rotation=[0., math.sin(.15), 0., math.cos(.15)],
                                           scale=[1.1, .9, 1.2])
            if ordinary:
                if len(glb.doc['nodes']) != 6:
                    raise ValueError('Authored parent-control fixture layout changed')
                glb.doc['nodes'][0]['children'] += [6, 7]
                glb.doc['nodes'] += [{'name': 'IdentityParentA', 'children': [8]},
                                     {'name': 'IdentityParentB'}, {'name': 'OrdinaryChild'}]
            factory.write_glb(source, glb.doc, bytes(glb.binary))
            options = factory.request(helper.GLB(source))
            options.update(source_morph_defaults=False, morph_weights={'3': [weight]})
            shape = {'format': 'studio_source_shape_2', 'enabled': False,
                     'overrides': {'3': {'0': weight}}}
            row = _candidate(modules, folder, label, source, options, shape)
            if ordinary:
                row['ordinary_reparent'] = {'node': 8, 'parent': 7}
            cases.append(row)

        folder = destination / 'existing'
        folder.mkdir()
        source = folder / 'source.glb'
        glb = modules['test_secondary_existing_joints'].existing_fixture(source)
        options = {'source_sha256': glb.sha, 'node': 3, 'primitive': 1,
                   'component': 0, 'anchor_node': 4, 'segments': 3,
                   'review_only': True, 'use_existing_joints': True, 'reviewed': True}
        cases.append(_candidate(modules, folder, 'existing-native-chain-synthetic',
                                source, options, {'format': 'studio_source_shape_2',
                                                  'enabled': False, 'overrides': {}}, 4))

        # Separate six-node host fixture contains a real, nonzero morph delta;
        # its evaluated .5 amount and recorded body/expression tracks belong to
        # the ordinary app harness, rather than this source-file constructor.
        host = destination / 'host'
        host.mkdir()
        host_source = host / 'two-panel-v1.glb'
        factory.two_panel_fixture(host_source, 'v1')

        if native_input is not None:
            folder = destination / 'native-backhair'
            folder.mkdir()
            source = folder / 'source.glb'
            parameters = folder / 'parameters.json'
            shutil.copy2(native_input['source'], source)
            shutil.copy2(native_input['parameters'], parameters)
            if _sha(source) != BACKHAIR_SHA or _sha(parameters) != PARAMETERS_SHA:
                raise ValueError('Explicit native staging copy differs')
            glb = helper.GLB(source)
            assessment = helper.inspect(source)
            matches = [row for row in assessment.get('regions', [])
                       if (row.get('node'), row.get('primitive'), row.get('component')) == (80, 1, 1)
                       and row.get('existing_chain', {}).get('center_node') == 16
                       and row.get('existing_chain', {}).get('joint_nodes') == [11, 10, 9]]
            if len(matches) != 1 or len(glb.doc['nodes']) != 103:
                raise ValueError('Explicit native Backhair source-node assessment changed')
            options = {'source_sha256': glb.sha, 'node': 80, 'primitive': 1,
                       'component': 1, 'anchor_node': 16, 'segments': 3,
                       'source_morph_defaults': False, 'use_existing_joints': True,
                       'reviewed': True}
            native = _candidate(modules, folder, 'actual-retained-backhair-fresh-candidate',
                                source, options, {'format': 'studio_source_shape_2',
                                                  'enabled': False, 'overrides': {}}, 11)
            operation = native['operations']
            if len(operation) != 1 or operation[0]['configured_source_nodes'] != [11, 10, 9] or operation[0]['candidate_helper_nodes'] != [103]:
                raise ValueError('Fresh native candidate changed the expected chain/endpoint')
            cases.append(native)

        plan = {'format': 'has_helper_preview_fixture_plan_1', 'cases': cases,
                'scope': 'self-authored synthetic defaults; optional explicit retained input only',
                'native_requested': native_input is not None,
                'expected_adapter_checks': expected_adapter_checks(cases),
                'expected_host_checks': 69,
                'host_source': str(host_source), 'source_hashes': {r: expected_hashes[r] for r in SOURCES.values()}}
        _write(destination / 'plan.json', plan)
    except Exception as error:
        failure = {'type': type(error).__name__, 'message': str(error)}
        raise
    finally:
        preservation = {'sources': _same(sources), 'native': _same(protected_native)}
        _write(destination / 'fixture-receipt.json', {
            'format': 'has_helper_preview_fixture_receipt_1', 'root': str(root),
            'source_records': sources, 'protected_native': protected_native,
            'preservation': preservation, 'failure': failure,
            'processes_launched': 0, 'gpu': False, 'conversion_runtime': False})
        if not all(preservation.values()):
            raise ValueError('Fixture preparation changed protected source/native inputs')
    return {'plan_path': str(destination / 'plan.json'), 'host_source': str(host_source),
            'expected_adapter_checks': expected_adapter_checks(cases),
            'expected_host_checks': 69, 'protected_native': protected_native}
