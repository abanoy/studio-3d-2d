"""Root-only after-copy activation preparation; import loads no target helper/data."""
from pathlib import Path
from types import SimpleNamespace
import argparse, hashlib, importlib.util, json, re, stat, sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
EXPERIMENTS = ROOT / 'experiments'
COLD = EXPERIMENTS / 'neon_owner_cold187_index_api_20261117'
COLD_INDEX = '1d622b70d155441f4f07edf38be962d4ffc7ed0ecaf61ab6af13cf575ac1baac'
V_SHA = '87995d9226077ac012fbd41bce12e7ed168e6ee78a31159a916bddd7dffb6649'
RENDERER = EXPERIMENTS / 'neon_owner_activation_index_api_20261117'
RENDERER_INDEX = '36fe7f94d9e519050ffac503a5c69be831563ce5ca8da8ac2bfec2d5216e7e4b'
RENDERER_SHA = '5acfa3635a8baf4a969bf3c6bb44151f08a1c46dd2a4936f41ca837541e75f1d'


def need(ok, message):
    if not ok: raise ValueError(message)


def pinned_source(path, digest):
    for item in (path, *path.parents):
        info = item.lstat(); need(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400, 'source reparse path refused')
    raw = path.read_bytes(); need(hashlib.sha256(raw).hexdigest() == digest, 'pinned source differs'); return raw


def load_api():
    sys.dont_write_bytecode = True
    need(all(name not in sys.modules for name in ('admission_core', 'copy_executor', 'qualified_inputs')), 'fresh preparation process required')
    pinned_source(COLD / 'INDEX.json', COLD_INDEX); pinned_source(COLD / 'validation_admission.py', V_SHA)
    pinned_source(RENDERER / 'INDEX.json', RENDERER_INDEX); pinned_source(RENDERER / 'render_successor.py', RENDERER_SHA)
    def module(name, path):
        spec = importlib.util.spec_from_file_location(name, path); value = importlib.util.module_from_spec(spec)
        sys.modules[name] = value; spec.loader.exec_module(value); return value
    V = module('_root_sealed_after_copy_adapter', COLD / 'validation_admission.py')
    protected = {}; V.packet(COLD, COLD_INDEX, protected); V.packet(RENDERER, RENDERER_INDEX, protected)
    R = module('_root_sealed_validator_renderer', RENDERER / 'render_successor.py')
    index = V.parse((COLD / 'INDEX.json').read_bytes())
    parent_files = {name: (COLD / name).read_bytes() for name in ['INDEX.json', *[row['path'] for row in index['files']]]}
    return SimpleNamespace(V=V, R=R, protected=protected, parent_files=parent_files)


def descriptor(api, path):
    path = Path(path).absolute(); return {'path': str(path), **api.V.identity(path)}


def successor_path(api, value):
    path = api.V.guarded(Path(value).absolute(), EXPERIMENTS)
    need(path.parent == EXPERIMENTS and not path.exists(), 'fresh direct experiments validator required')
    return path


def qualify_copy(api, executor_folder, executor_sha, build_descriptor=None):
    """Use V's unchanged after-copy factory; never create V tokens or run replay."""
    V = api.V; protected = dict(api.protected)
    executor = V.packet(executor_folder, executor_sha, protected)
    source = (executor / 'qualified_inputs.py').read_bytes()
    activation = (executor / 'ACTIVATION.json').read_bytes()
    V.activated_Q_matches_reference(source, (COLD / 'reference_qualified_inputs.py').read_bytes(), activation)
    for name, pin in [('copy_executor.py', V.EXECUTOR_C_SHA), ('admission_core.py', V.CORE_SHA),
                      ('reference_close_terminal.py', V.REFERENCE_C39_SHA), ('legacy_result_gates.py', V.LEGACY_SHA)]:
        need(V.identity(executor / name)['sha256'] == pin, 'exact activated executor dependency required')
    V.load_module('admission_core', executor / 'admission_core.py')
    C = V.load_module('copy_executor', executor / 'copy_executor.py')
    Q = V.load_module('qualified_inputs', executor / 'qualified_inputs.py')
    qualified = V.existing_review_factory(source, Q.__dict__)()
    data = Q.assert_admitted(qualified)
    review = Path(data['final']); built_path = review / 'BUILD-VERIFICATION.json'
    build_descriptor = descriptor(api, built_path) if build_descriptor is None else build_descriptor
    built = V.parse(V.read_bound(build_descriptor, review, protected, exact=built_path))
    V.validate_copy_receipt(built, data)
    protected.update(data['full_gate']); protected.update(data['preparation'])
    protected.update({str(ROOT / name): row for name, row in data['source_identities'].items()})
    H = C.helpers(ROOT); studio = review / 'Studio'
    def fresh_copy():
        need(not H.tree(studio / 'output') and not H.tree(studio / '.godot'), 'copied Studio is no longer unlaunched')
    fresh_copy()
    for name, expected in built['source_hashes'].items():
        path = V.guarded(studio / name, studio); actual = V.identity(path)
        need(actual['sha256'] == expected, 'copied source/support bytes differ'); protected[str(path)] = actual
    def recheck():
        Q.assert_admitted(qualified); fresh_copy()
        need(all(V.identity(Path(path)) == row for path, row in protected.items()), 'after-copy proof/source/receipt changed')
    recheck()
    return SimpleNamespace(C=C, H=H, data=data, descriptor=build_descriptor, recheck=recheck)


def write_new(api, bound, path, boundary, raw):
    bound.C._write_blob(bound.H, path, boundary, raw, api.R.sha(raw))


def assemble(api, args):
    need(args.root_actual_copy_and_closed_lane_reviewed is True, 'actual unlaunched copy and closed lane required')
    target = successor_path(api, args.successor)
    draft = api.V.guarded(args.draft.absolute(), ROOT / 'output')
    need(draft.parent.is_dir() and not draft.exists(), 'fresh external activation draft required')
    bound = qualify_copy(api, args.executor.absolute(), args.executor_index_sha256)
    plan = api.V.parse((RENDERER / 'VALIDATOR_ACTIVATION.template.json').read_bytes())
    plan.update(status='ROOT_REVIEWED_ACTUAL_FULL_RELEASE_MERGE_AND_FRESH_COPY',
                executor_packet={'folder': str(args.executor.absolute()), 'INDEX_sha256': args.executor_index_sha256},
                build_verification=bound.descriptor, not_an_activation=False, actual_startup_or187_result_supplied=False)
    raw = api.R.encoded(plan); need(len(raw) <= 8 * 1024 * 1024, 'activation capacity exceeded')
    bound.recheck(); write_new(api, bound, draft, ROOT / 'output', raw); bound.recheck()
    return {'phase': 'VALIDATOR_DRAFT_FOR_ROOT_REVIEW', 'draft': str(draft), 'activation_sha256': api.R.sha(raw),
            'successor': str(target), 'validator_or_copy_executed': False}


def materialize(api, args):
    target = successor_path(api, args.successor)
    draft = descriptor(api, api.V.guarded(args.draft.absolute(), ROOT / 'output'))
    need(draft['sha256'] == args.root_approved_activation_sha256, 'exact Root-approved activation SHA required')
    raw = api.V.read_bound(draft, ROOT / 'output', {}, maximum=8 * 1024 * 1024); plan = api.V.parse(raw)
    need(plan.get('format') == 'has_root_after_copy_owner_validation_activation_1'
         and plan.get('status') == 'ROOT_REVIEWED_ACTUAL_FULL_RELEASE_MERGE_AND_FRESH_COPY', 'actual validator activation schema required')
    bound = qualify_copy(api, plan['executor_packet']['folder'], plan['executor_packet']['INDEX_sha256'], plan['build_verification'])
    packet = api.R.render('validator', api.parent_files, raw, args.root_approved_activation_sha256)
    bound.recheck(); need(descriptor(api, Path(draft['path'])) == draft, 'approved activation draft changed')
    target.mkdir(exist_ok=False)
    for name in [name for name in packet if name != 'INDEX.json'] + ['INDEX.json']:
        write_new(api, bound, target / name, target, packet[name])
    api.V.packet(target, api.R.sha(packet['INDEX.json']), {})
    bound.recheck()
    return {'phase': 'VALIDATOR_RENDERED_SOURCE_ONLY', 'successor': str(target),
            'INDEX_sha256': api.R.sha(packet['INDEX.json']), 'validator_or_copy_executed': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__); modes = parser.add_subparsers(dest='phase', required=True)
    first = modes.add_parser('assemble'); first.add_argument('--root-actual-copy-and-closed-lane-reviewed', action='store_true', required=True)
    first.add_argument('--executor', type=Path, required=True); first.add_argument('--executor-index-sha256', required=True)
    second = modes.add_parser('materialize'); second.add_argument('--root-approved-activation-sha256', required=True)
    for mode in (first, second): mode.add_argument('--successor', type=Path, required=True); mode.add_argument('--draft', type=Path, required=True)
    args = parser.parse_args(); api = load_api()
    print(json.dumps(assemble(api, args) if args.phase == 'assemble' else materialize(api, args), sort_keys=True))


if __name__ == '__main__': main()
