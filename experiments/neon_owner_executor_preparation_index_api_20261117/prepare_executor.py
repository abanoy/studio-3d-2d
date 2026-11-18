"""Root-only future assembly/render glue. Import does not load target helpers/data."""
from pathlib import Path
from types import SimpleNamespace
import argparse, hashlib, importlib.util, json, re, stat, sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
EXPERIMENTS = ROOT / 'experiments'
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
PACKETS = {
    'executor': ('neon_owner_executor_index_api_20261117', 'ced9e3943f24263b2399d14e77cc943e39371edacf7716e5fdbb9d336dcc447c'),
    'core': ('neon_owner_admission_shell_eol_index_compat_20261117', 'f8da4f783958b918a35b53116fa6182fcddc9cd3cf485959f8bb088ce8147ee5'),
    'renderer': ('neon_owner_activation_index_api_20261117', '36fe7f94d9e519050ffac503a5c69be831563ce5ca8da8ac2bfec2d5216e7e4b'),
    'ram': ('neon_696_postpass_copy_readiness_20261117', 'd90b594b3a3cb32c5b42167bda4ee9c77ba7151340a660b966897d122dbe8b7a'),
    'terminal': ('neon_3a_mmd_terminal_20261117', 'f223587f75cb56281b961679fecb399672025216c1b0f23f5cebee20cdc38d6b'),
}
CONTEXT_SHA = '5424628e28385ce331b55be404384039a3d54262033cbbc96a12445c8dfeb8ba'
RENDERER_SHA = '5acfa3635a8baf4a969bf3c6bb44151f08a1c46dd2a4936f41ca837541e75f1d'
ROLES = {'state': 'state.json', 'birth': 'root-birth-observation.json', 'launch': 'launch.json',
         'before': 'source-before.json', 'after': 'source-after.json',
         'full_report': 'terminal-audit-attempt1/full-verification.json', 'canonical_log': 'canonical.log',
         'inventory': 'terminal-audit-attempt1/receipt-inventory.json', 'release': 'graphics-lease-closed.json'}
PAYLOADS = {'owner_archive_catalogue': 'OWNER_ARCHIVE_CATALOGUE.json',
            'merged_working_recipe': 'MERGED_WORKING_RECIPE.json',
            'reviewed52_to_candidate_delta': 'REVIEWED52_TO_CANDIDATE_DELTA.json'}
SCOPE = ('src', 'tests', 'tools', 'data', 'examples', 'project.godot', 'main.tscn', 'run.py', 'launch.pyw')


def need(ok, message):
    if not ok: raise ValueError(message)


def source_packet(folder, expected):
    """Read only pinned public source before loading its definitions."""
    for path in (folder, *folder.parents):
        info = path.lstat(); need(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400, 'source reparse path refused')
    raw = (folder / 'INDEX.json').read_bytes(); need(hashlib.sha256(raw).hexdigest() == expected, 'sealed source INDEX differs')
    index = json.loads(raw); rows = index.get('files', index.get('payloads')); result = {'INDEX.json': raw}
    for row in rows:
        name = row['path']; path = folder / name
        need(type(name) is str and name and not Path(name).is_absolute() and '..' not in Path(name).parts, 'unsafe source member')
        for item in (path, *path.parents):
            info = item.lstat(); need(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400, 'source member reparse path refused')
        info = path.lstat(); need(stat.S_ISREG(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400, 'regular source member required')
        body = path.read_bytes(); need(len(body) == row['bytes'] and hashlib.sha256(body).hexdigest() == row['sha256'], 'sealed source member differs')
        need(name not in result, 'duplicate source member'); result[name] = body
    need({p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()} == set(result), 'closed source packet required')
    return result


def load_api():
    sys.dont_write_bytecode = True
    need(all(name not in sys.modules for name in ('admission_core', 'copy_executor', 'qualified_inputs')), 'fresh preparation process required')
    files = {role: source_packet(EXPERIMENTS / folder, pin) for role, (folder, pin) in PACKETS.items()}
    need(hashlib.sha256(files['renderer']['render_successor.py']).hexdigest() == RENDERER_SHA, 'exact950a renderer required')
    sys.path.insert(0, str(EXPERIMENTS / PACKETS['executor'][0]))
    import admission_core as A
    import copy_executor as C
    import qualified_inputs as Q
    def module(name, path):
        spec = importlib.util.spec_from_file_location(name, path); value = importlib.util.module_from_spec(spec)
        sys.modules[name] = value; spec.loader.exec_module(value); return value
    R = module('_root_owner_activation_renderer', EXPERIMENTS / PACKETS['renderer'][0] / 'render_successor.py')
    RAM = module('_root_owner_source_ram', EXPERIMENTS / PACKETS['ram'][0] / 'source_data_ram.py')
    return SimpleNamespace(A=A, C=C, Q=Q, R=R, RAM=RAM, H=C.helpers(ROOT), files=files)


def descriptor(api, path):
    path = Path(path).absolute(); return {'path': str(path), **api.H.identity(path)}


def successor_path(api, value):
    path = api.H.guarded(Path(value).absolute(), EXPERIMENTS)
    need(path.parent == EXPERIMENTS and path.name not in {row[0] for row in PACKETS.values()}, 'fresh direct experiments successor required')
    return path


def collect(api, plan, delta_descriptor, delta_boundary):
    """Original admission consumers, without minting an activation/admission token."""
    A, Q, H, R, RAM = api.A, api.Q, api.H, api.R, api.RAM
    protected = {}
    def bound(row, boundary, exact=None): return Q.read_bound(H, row, boundary, protected, exact=exact)
    for role, (name, pin) in PACKETS.items():
        folder = EXPERIMENTS / name
        need(H.identity(folder / 'INDEX.json')['sha256'] == pin, 'source INDEX changed')
        protected[str(folder / 'INDEX.json')] = H.identity(folder / 'INDEX.json')
        Q._verify_packet_files(H, folder, A.parse(api.files[role]['INDEX.json']), protected)
    source_pins = A.parse(api.files['core']['PREDECESSOR_SOURCE_PINS.json'])['pins']
    for name, row in source_pins.items():
        path = H.guarded(Q.OLD / name, Q.OLD); actual = H.identity(path)
        need(actual['bytes'] == row['bytes'] and actual['sha256'] == row['sha256'], 'immutable old builder/replay source changed')
        protected[str(path)] = actual
    terminal = EXPERIMENTS / PACKETS['terminal'][0]
    need(plan['candidate_terminal_packet_index_sha256'] == PACKETS['terminal'][1]
         and plan['candidate_context']['sha256'] == CONTEXT_SHA, 'exact fresh strictf223 context required')
    context = A.parse(bound(plan['candidate_context'], EXPERIMENTS, terminal / 'CONTEXT.json'))
    need(Path(context['checkout']) == REVIEW and context['functional_sources'] == 1029, 'exact candidate checkout scope required')
    run = H.guarded(REVIEW / 'output' / context['run_name'], REVIEW / 'output')
    need(set(plan['candidate_artifacts']) == set(ROLES), 'exact nine candidate roles required')
    artifacts = {key: bound(plan['candidate_artifacts'][key], REVIEW / 'output', run / name) for key, name in ROLES.items()}
    for name, pin in context['immutable_run_inputs'].items():
        row = descriptor(api, run / name); need(row['sha256'] == pin, 'immutable full input changed'); bound(row, run)
    registry_raw = api.files['terminal']['RESULT_REGISTRY.json']; need(A.digest(registry_raw) == context['registry_sha256'], 'registry pin differs')
    inventory = A.parse(artifacts['inventory']); report_meta = inventory['phase_documents'][str(REVIEW / 'output/verification.json')]
    need(report_meta['sha256'] == A.digest(artifacts['full_report']), 'preserved actual full report differs')
    candidate = A.check_candidate_bundle(artifacts, context, A.parse(registry_raw),
        {key: row['sha256'] for key, row in plan['candidate_artifacts'].items()}, report_meta['mtime_ns'])
    for key in ('runner', 'powershell'):
        row = descriptor(api, Path(context[key])); need(row['sha256'] == context[key + '_sha256'], 'qualified tool source changed'); protected[row['path']] = {k: row[k] for k in ('bytes', 'mtime_ns', 'sha256')}
    git = plan['git_executable']; git_path = Path(git['path']); git_id = {k: git[k] for k in ('bytes', 'mtime_ns', 'sha256')}
    need(H.identity(git_path) == git_id, 'approved Git tool differs'); protected[str(git_path)] = git_id
    Git = Q.ApprovedGit(H, git_path, git_id); H['subprocess'] = Git
    def main_now():
        need(Git.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == plan['merged_revision'], 'actual merged HEAD differs')
        dirty = Git.check_output(['git', 'diff', 'HEAD', '--name-only', '--', *SCOPE], cwd=ROOT, text=True).splitlines()
        dirty += Git.check_output(['git', 'ls-files', '--others', '--exclude-standard', '--', *SCOPE], cwd=ROOT, text=True).splitlines()
        need(not [n for n in dirty if '__pycache__' not in Path(n).parts and not n.endswith('.pyc')], 'merged functional dirt/overlay refused')
        need(not (ROOT / 'override.cfg').exists() and not (ROOT / 'project.binary').exists(), 'startup override refused')
    main_now(); tested = candidate['functional_source_sha256']; need(H.source_map() == tested, 'merged raw1029 differs from qualified full')
    stamps = {n: H.identity(ROOT / n) for n in tested}; working = {n: (ROOT / n).read_bytes() for n in tested}
    need(all(H.identity(ROOT / n) == stamps[n] and A.digest(working[n]) == tested[n] for n in tested), 'merged source changed during read')
    entries, request = RAM.archive_entries(Q, Git.check_output(['git', 'ls-tree', '-rz', plan['merged_revision']], cwd=ROOT))
    sizes = RAM.archive_sizes(entries, Git.check_output(['git', 'cat-file', '--batch-check=%(objectname) %(objecttype) %(objectsize)'], input=request, cwd=ROOT))
    catalogue, committed = RAM.owner_catalogue(A, plan['merged_revision'], entries, sizes, Git.check_output(['git', 'cat-file', '--batch'], input=request, cwd=ROOT))
    Q.read_committed_archive(Git, plan['merged_revision'], catalogue)
    need({n for n in committed if Q.functional(n)} == set(tested), 'committed functional membership differs')
    recipe, merged = RAM.merged_recipe(A, plan['merged_revision'], tested, working, committed, allow_checkout_eol=plan['allow_checkout_eol'])
    source52_raw, source52 = Q._historical52_proof(H, plan['historical52_full_proof'], protected)
    old_recipe = A.parse(bound(plan['historical52_working_recipe'], EXPERIMENTS))
    old_working = Q.reconstruct_historical52(H.git_blobs(Q.SOURCE52, list(source52['source_sha256'])), source52, old_recipe)
    lock_path = Q.OLD / 'builder/input-lock.json'; delta_path = Q.OLD / 'source-delta.json'
    lock_raw = bound(descriptor(api, lock_path), Q.OLD); old_delta_raw = bound(descriptor(api, delta_path), Q.OLD)
    historical = A.check_historical_predecessors(lock_raw, old_delta_raw, source52_raw, old_working)
    Q.revalidate_native_predecessor(H, A.parse(lock_raw), old_working, working, A.parse(old_delta_raw), protected)
    reviewed_raw = bound(delta_descriptor, delta_boundary); reviewed = A.parse(reviewed_raw)
    need(reviewed.get('format') == 'has_reviewed52_to_qualified_Neon_delta_1' and reviewed.get('review_status') == 'ROOT_REVIEWED_EXPLICIT_SOURCE_DELTA', 'actual reviewed delta required')
    maps = lambda table: {n: {'raw_sha256': A.digest(b), 'content_sha256': A.digest(A.canonical(b, n))} for n, b in table.items()}
    delta = A.check_reviewed_delta(maps(old_working), maps(working), reviewed['rows'])
    need(len(delta['changed_or_added_files']) == 39 and set(reviewed['reasons']) == set(delta['changed_or_added_files'])
         and all(type(v) is str and 0 < len(v) <= 2048 for v in reviewed['reasons'].values()), 'exact reviewed39 reasons required')
    A.assemble_copy_proposal(candidate, merged, historical, delta)
    final = ROOT.parent / ('HAS-Review-Neon-' + plan['merged_revision'][:7] + '-native')
    H.guarded(final, ROOT.parent); need(not final.exists(), 'new owner review sibling must remain absent')
    need((ROOT.parent / 'HAS-Review-20261115-SFM-Joints-f0dd57a-replay2').is_dir(), 'protected owner review missing')
    def recheck():
        main_now(); need(H.source_map() == tested and all(H.identity(ROOT / n) == row for n, row in stamps.items()), 'merged working source changed')
        need(all(H.identity(Path(path)) == row for path, row in protected.items()), 'protected proof/source/tool identity changed')
        need(not final.exists(), 'owner destination no longer fresh')
    recheck()
    return {PAYLOADS['owner_archive_catalogue']: R.encoded(catalogue), PAYLOADS['merged_working_recipe']: R.encoded(recipe),
            PAYLOADS['reviewed52_to_candidate_delta']: reviewed_raw}, recheck


def assemble(api, args):
    need(args.root_actual_strict_full_and_merge_reviewed is True and re.fullmatch('[a-f0-9]{40}', args.merged_revision), 'actual qualified full and merged revision required')
    target = successor_path(api, args.successor); need(not target.exists(), 'fresh source successor required')
    draft = api.H.guarded(args.draft.absolute(), ROOT / 'output'); need(draft.parent.is_dir() and not draft.exists(), 'fresh draft outside successor required')
    plan = api.A.parse(api.files['renderer']['EXECUTOR_ACTIVATION.template.json']); plan.pop('preparation_notes', None)
    historical = api.A.parse(api.files['ram']['HISTORICAL52_PATHS.json'])
    terminal = EXPERIMENTS / PACKETS['terminal'][0]; context = api.A.parse(api.files['terminal']['CONTEXT.json'])
    plan.update(status='ROOT_REVIEWED_ACTUAL_FULL_AND_MERGED_MAIN', candidate_context=descriptor(api, terminal / 'CONTEXT.json'),
                candidate_terminal_packet_index_sha256=PACKETS['terminal'][1], merged_revision=args.merged_revision,
                allow_checkout_eol=args.allow_checkout_eol, historical52_full_proof=historical['historical52_full_proof'],
                historical52_working_recipe=historical['historical52_working_recipe'])
    run = REVIEW / 'output' / context['run_name']; plan['candidate_artifacts'] = {role: descriptor(api, run / name) for role, name in ROLES.items()}
    delta = descriptor(api, api.H.guarded(args.reviewed_delta.absolute(), EXPERIMENTS)); need(delta['sha256'] == args.reviewed_delta_sha256, 'reviewed delta SHA differs')
    extras, recheck = collect(api, plan, delta, EXPERIMENTS)
    need(all(len(raw) <= 16 * 1024 * 1024 for raw in extras.values()), 'renderer payload ceiling exceeded')
    recheck(); target.mkdir(exist_ok=False)
    for name, raw in extras.items(): api.C._write_blob(api.H, target / name, target, raw, api.A.digest(raw))
    for field, name in PAYLOADS.items(): plan[field] = descriptor(api, target / name)
    raw = api.R.encoded(plan); need(len(raw) <= 8 * 1024 * 1024, 'activation ceiling exceeded')
    recheck()
    need(all(descriptor(api, target / name) == plan[field] for field, name in PAYLOADS.items()), 'new payload identity changed')
    api.C._write_blob(api.H, draft, ROOT / 'output', raw, api.A.digest(raw))
    need(all(descriptor(api, target / name) == plan[field] for field, name in PAYLOADS.items()), 'payload identity changed while writing draft')
    return {'phase': 'ASSEMBLED_FOR_ROOT_REVIEW', 'draft': str(draft), 'activation_sha256': api.A.digest(raw), 'successor': str(target), 'activated_packet_written': False}


def materialize(api, args):
    target = successor_path(api, args.successor)
    need({p.name for p in target.iterdir()} == set(PAYLOADS.values()), 'successor must contain only three staged payloads')
    draft = descriptor(api, api.H.guarded(args.draft.absolute(), ROOT / 'output'))
    need(draft['sha256'] == args.root_approved_activation_sha256, 'exact Root-approved activation bytes required')
    raw = api.Q.read_bound(api.H, draft, ROOT / 'output', {}, maximum=8 * 1024 * 1024); plan = api.A.parse(raw)
    need(plan.get('format') == 'has_neon_owner_review_actual_activation_1' and plan.get('status') == 'ROOT_REVIEWED_ACTUAL_FULL_AND_MERGED_MAIN'
         and type(plan.get('allow_checkout_eol')) is bool and re.fullmatch('[a-f0-9]{40}', plan.get('merged_revision', '')), 'actual activation schema required')
    extras = {name: api.Q.read_bound(api.H, plan[field], target, {}, exact=target / name, maximum=16 * 1024 * 1024) for field, name in PAYLOADS.items()}
    expected, recheck = collect(api, plan, plan['reviewed52_to_candidate_delta'], target)
    need(extras == expected, 'reviewed staged payload bytes differ from actual inputs')
    packet = api.R.render('executor', api.files['executor'], raw, args.root_approved_activation_sha256, extras)
    recheck(); need(descriptor(api, Path(draft['path'])) == draft, 'approved draft changed')
    for field, name in PAYLOADS.items():
        need(descriptor(api, target / name) == plan[field] and (target / name).read_bytes() == packet[name], 'staged payload identity changed')
    for name in [n for n in packet if n != 'INDEX.json' and n not in extras] + ['INDEX.json']:
        api.C._write_blob(api.H, target / name, target, packet[name], api.A.digest(packet[name]))
    api.Q._verify_packet_files(api.H, target, api.A.parse(packet['INDEX.json']), {})
    recheck()
    for field, name in PAYLOADS.items():
        need(descriptor(api, target / name) == plan[field] and (target / name).read_bytes() == packet[name], 'final staged payload identity changed')
    return {'phase': 'RENDERED_SOURCE_ONLY', 'successor': str(target), 'INDEX_sha256': api.A.digest(packet['INDEX.json']), 'copier_or_validator_executed': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__); modes = parser.add_subparsers(dest='phase', required=True)
    first = modes.add_parser('assemble'); first.add_argument('--root-actual-strict-full-and-merge-reviewed', action='store_true', required=True)
    first.add_argument('--merged-revision', required=True); first.add_argument('--allow-checkout-eol', action='store_true')
    first.add_argument('--reviewed-delta', type=Path, required=True); first.add_argument('--reviewed-delta-sha256', required=True)
    second = modes.add_parser('materialize'); second.add_argument('--root-approved-activation-sha256', required=True)
    for mode in (first, second): mode.add_argument('--successor', type=Path, required=True); mode.add_argument('--draft', type=Path, required=True)
    args = parser.parse_args(); api = load_api()
    print(json.dumps(assemble(api, args) if args.phase == 'assemble' else materialize(api, args), sort_keys=True))


if __name__ == '__main__': main()
