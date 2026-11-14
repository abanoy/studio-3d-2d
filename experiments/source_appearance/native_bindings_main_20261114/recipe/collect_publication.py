"""Output-only compact packet collector. Default validates terminal inputs only."""
from pathlib import Path
import argparse
import gzip
import hashlib
import json
import shutil
import stat

ROOT = Path(__file__).resolve().parents[2]
LAUNCH = ROOT / 'output/sfm-bone-bindings-native-launch-20261114T033026205'
RUN = LAUNCH / 'run'
FOUNDATION = ROOT / 'output/sfm-bone-bindings-foundation-20261114-attempt1'
NATIVE_SHA = '10ee4a984c9e54b1acf37d79d5013a10780abe98416b8350f3edf3ee37277c4b'
FOUNDATION_SHA = 'fd95889efd55d62d1dfd8af9ba06a8c7a68b9f3d1b7df0e8efc1ff76d01192bf'
MANIFEST_SHA = 'f41595de1db83c90aca99fea3c74661bfa97b2eefc6cddf2520155bc49fe9c3f'
SOURCE_FILES = ['src/source_bone_bindings.gd', 'src/secondary_helper_editor.gd',
                'tools/source_bone_metadata.py', 'tools/source_bone_export.py',
                'tools/source_jiggle_crosswalk.py', 'tools/source_jiggle_metadata.py',
                'tools/source_jiggle_values.py', 'tools/source_mdl_snapshot.py',
                'tools/blender_source_bridge.py', 'tools/prepare_source.py',
                'tests/verify_source_bone_bindings.py', 'tests/verify_source_bone_crosswalk_cpu.py',
                'tests/verify_source_choice_foundation.py', 'tests/verify_source_choices_native.py',
                'tests/source_choices_native_smoke.gd', 'tests/native_source_binding_ui.gd']
FORBIDDEN_KEYS = {'Blender_matrix_local_row_major', 'native_rest_words_uint32', 'portable_world',
                  'authored_body', 'bone_poses', 'pose_keys', 'rest_matrices', 'vertices',
                  'vertex_positions', 'vertex_weights', 'pixels', 'raster_bytes', 'bone_catalogue'}


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def safe(path):
    path = path.absolute()
    for part in [path, *path.parents]:
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        require(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400,
                'Reparse source/target refused')
    return path


def raw(path):
    safe(path)
    before = path.stat()
    require(path.is_file() and before.st_size <= 16 * 1024 * 1024, 'Bounded regular metadata only')
    value = path.read_bytes()
    after = path.stat()
    require((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns), 'Input changed while read')
    return value


def no_coordinates(value):
    if isinstance(value, dict):
        for key, child in value.items():
            require(not (key in FORBIDDEN_KEYS and isinstance(child, (dict, list))),
                    'Full coordinate/rig/fixture payload refused: ' + key)
            no_coordinates(child)
    elif isinstance(value, list):
        for child in value:
            no_coordinates(child)


def metadata(path):
    value = raw(path)
    if path.suffix == '.json':
        no_coordinates(json.loads(value))
    elif path.suffix == '.log':
        for token in (b'Blender_matrix_local_row_major', b'native_rest_words_uint32', b'"portable_world":'):
            require(token not in value, 'Raw log contains private coordinate payload')
    return value


def load(path):
    return json.loads(raw(path))


def admission():
    require(digest(raw(RUN / 'verification.json')) == NATIVE_SHA, 'Native verification bytes differ')
    native = load(RUN / 'verification.json')
    host = load(LAUNCH / 'authoritative-host-terminal.json')
    launch = load(LAUNCH / 'launch.json')
    manifest = Path(launch['arguments'][launch['arguments'].index('--inputs-manifest') + 1])
    require(launch['manifest_sha256'] == digest(raw(manifest)) == MANIFEST_SHA
            and load(manifest) == load(RUN / 'input-manifest.json'), 'Original manifest identity differs')
    require(host.get('format') == 'has_root_sfm_bone_bindings_native_terminal_1'
            and host.get('pid') == 27676 and host.get('creation_utc') == '2026-11-14T03:30:26.2220993Z'
            and host.get('exact_coordinator_identity_absent') is True
            and host.get('graphics_lease_released') is True and host.get('suite_passed') is True
            and host.get('matching_owned_runtime_commands') == [] and host.get('processes_killed') == []
            and host.get('verification_sha256') == NATIVE_SHA
            and host.get('launch_sha256') == digest(raw(LAUNCH / 'launch.json')), 'Exact released terminal proof required')
    require(native['passed'] is True and not native['errors'] and len(native['preservation']) == 8
            and all(value is True for value in native['preservation'].values()), 'All native preservation gates required')
    require(load(RUN / 'source-before.json') == load(RUN / 'source-after.json'), 'Frozen run source maps differ')
    runtime = load(RUN / 'runtimes-before.json')
    require(len(runtime['executables']) == 6 and len(runtime['sourceio_files']) == 574
            and len(runtime['blender_exporter_noncache_sources']) == 120, 'Runtime/exporter source catalogue differs')
    require(len(native['readers']) == 4 and native['writer']['result']['checks'] == 117
            and sum(row['result']['checks'] for row in native['readers']) == 124, 'Four actual writer/readers differ')
    named = [native['writer']['result']['named_checks'], *[row['result']['named_checks'] for row in native['readers']]]
    require(len(named[0]) == 194 and sum(map(len, named[1:])) == 100
            and all(value is True for group in named for value in group.values()), 'Named native checks differ')
    require(len(native['receipts']) == 5, 'Exactly five original private receipts required')
    for row in native['receipts']:
        receipt = row['receipt']
        require(receipt.get('exit') == 0 and all(receipt.get(key) is True for key in
                ['private_window_seen', 'child_desktop_confirmed', 'job_closed', 'desktop_closed'])
                and receipt.get('foreground_child_observed') is False and receipt.get('desktop_switch_requested') is False,
                'Private graphical receipt failed')
    require(digest(raw(FOUNDATION / 'verification.json')) == FOUNDATION_SHA, 'Foundation bytes differ')
    foundation = load(FOUNDATION / 'verification.json')
    require(foundation['passed'] is True and foundation['source_unchanged'] is True and foundation['checks'] == 167
            and foundation['reports']['crosswalk_cpu']['checks'] == 77
            and foundation['reports']['bone_bindings_headless']['checks'] == 96
            and foundation['reports']['bone_bindings_headless']['source_unchanged'] is True,
            'Separate foundation167/Python77/headless96 required')
    return native, foundation


def plan(native):
    values = []
    def add(path, logical):
        require(path.name != 'expected.json' and path.suffix in {'.json', '.log', '.py', '.gd'}, 'Metadata allowlist refused')
        require(not any(part in {'fixture', 'fixtures', 'inputs', 'native'} or part.endswith('.assets') for part in path.relative_to(ROOT).parts),
                'Private fixture/native input path refused')
        metadata(path)
        values.append((path, logical))
    for path in sorted(LAUNCH.iterdir()):
        if path.is_file() and path.suffix in {'.json', '.log'}: add(path, 'coordinator/' + path.name)
    launch = load(LAUNCH / 'launch.json')
    add(Path(launch['arguments'][launch['arguments'].index('--inputs-manifest') + 1]), 'input-manifest-original.json')
    for path in sorted(RUN.iterdir()):
        if path.is_file() and path.suffix in {'.json', '.log'}: add(path, 'native/' + path.name)
    for directory in [RUN / 'writer', *sorted((RUN / 'readers').iterdir())]:
        for path in sorted(directory.iterdir()):
            if path.is_file() and path.suffix in {'.json', '.log'}: add(path, 'native/' + path.relative_to(RUN).as_posix())
    for directory in sorted((RUN / 'cases').iterdir()):
        for name in ['writer-result.json']:
            if (directory / name).is_file(): add(directory / name, 'native/' + (directory / name).relative_to(RUN).as_posix())
        for path in sorted((directory / 'conversion-metadata').iterdir()):
            if path.suffix in {'.json', '.log'} and path.name != 'parameters.json':
                add(path, 'native/' + path.relative_to(RUN).as_posix())
    for row in native['receipts']:
        path = Path(row['path']); require(digest(raw(path)) == row['sha256'], 'Original receipt bytes differ')
        add(path, 'private-receipts/' + path.name)
    for path in sorted(FOUNDATION.glob('*.log')): add(path, 'foundation/' + path.name)
    add(FOUNDATION / 'verification.json', 'foundation/verification.json')
    for sub in ['jiggle-cpu', 'crosswalk-cpu', 'bindings-headless']:
        directory = FOUNDATION / sub
        add(directory / 'verification.json', 'foundation/' + sub + '/verification.json')
        for path in sorted(directory.rglob('*')):
            if not path.is_file() or 'fixture' in path.relative_to(directory).parts: continue
            if path.suffix == '.log' or path.name in {'source-before.json', 'source-after.json', 'verified.json'} or path.name.endswith(('-command.json', '-process.json')):
                add(path, 'foundation/' + sub + '/' + path.relative_to(directory).as_posix())
    for attempt in [1, 2, 3]:
        directory = ROOT / ('output/source-bone-bindings-headless-attempt' + str(attempt))
        for path in sorted(directory.rglob('*')):
            if path.is_file() and 'fixture' not in path.relative_to(directory).parts and (path.suffix == '.log' or path.name.endswith('command.json')):
                add(path, 'failed-headless/attempt' + str(attempt) + '/' + path.relative_to(directory).as_posix())
    for path in sorted((ROOT / 'output').glob('signed-zero-*.log')): add(path, 'signed-zero-probes/' + path.name)
    benchmark = ROOT / 'docs/benchmarks/sfm_source_bone_binding_main_2026-11-13.json'
    if benchmark.is_file(): add(benchmark, 'post-run/source-bone-binding-benchmark.json')
    for name in SOURCE_FILES:
        path = ROOT / name
        require(name in native['source_before']['files'] and digest(raw(path)) == native['source_before']['files'][name]['sha256'],
                'Recipe source is not exact passed working matrix: ' + name)
        add(path, 'source/' + name)
    add(Path(__file__).resolve(), 'recipe/collect_publication.py')
    require(len({logical for _, logical in values}) == len(values), 'Duplicate logical packet paths')
    return values


def compact_cases(native):
    result = []
    for row in native['writer']['result']['cases']:
        path = Path(row['parameters']); data = load(path); fields = data.get('native_parameters', {})
        crosswalk = fields.get('source_export_crosswalk'); jiggle = fields.get('source_jiggle')
        no_coordinates(crosswalk)
        result.append({'name': row['name'], 'parameters_sha256': digest(raw(path)), 'parameters_bytes': path.stat().st_size,
                       'original_source_sha256': data.get('source_sha256'), 'GLB_sha256': digest(raw(Path(row['bundle']) / 'scene.glb')),
                       'native_bone_count': len(fields.get('bones', [])),
                       'jiggle_status': jiggle.get('status') if isinstance(jiggle, dict) else 'none',
                       'jiggle_rules': len(jiggle.get('rules', [])) if isinstance(jiggle, dict) else 0,
                       'source_export_crosswalk': crosswalk})
    return result


def main():
    global ROOT, LAUNCH, RUN, FOUNDATION
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--build', action='store_true', help='Explicit root-reviewed output packet creation')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    ROOT = safe(args.root.absolute()).resolve(strict=True)
    LAUNCH = ROOT / 'output/sfm-bone-bindings-native-launch-20261114T033026205'
    RUN = LAUNCH / 'run'
    FOUNDATION = ROOT / 'output/sfm-bone-bindings-foundation-20261114-attempt1'
    native, foundation = admission()
    values = plan(native); cases = compact_cases(native)
    summary = {'format': 'has_source_bone_bindings_packet_preflight_1', 'passed': True, 'native_verification_sha256': NATIVE_SHA,
               'foundation_sha256': FOUNDATION_SHA, 'manifest_source_sha256': MANIFEST_SHA,
               'planned_source_aliases': len(values), 'planned_uncompressed_bytes': sum(path.stat().st_size for path, _ in values),
               'writer_static': 117, 'readers_static': 124, 'writer_named': 194, 'reader_named': 100,
               'foundation': 167, 'Python_crosswalk': 77, 'headless': 96,
               'packet_created': False, 'native_simulation': False}
    if not args.build:
        print(json.dumps(summary)); return
    target = safe((args.output or ROOT / 'output/sfm-bone-bindings-publication-20261114').absolute()).resolve()
    require(target.is_relative_to((ROOT / 'output').resolve()) and target != ROOT / 'output' and not target.exists(), 'Use a fresh owned output target')
    target.mkdir(parents=True); aliases = []; stored = {}
    for source, logical in values:
        value = metadata(source); original_sha = digest(value)
        if original_sha in stored:
            relative = stored[original_sha]
        else:
            relative = logical + ('.gz' if len(value) > 65536 else '')
            encoded = gzip.compress(value, mtime=0) if relative.endswith('.gz') else value
            require(not relative.endswith('.gz') or gzip.decompress(encoded) == value, 'Lossless gzip failed')
            destination = target / relative; destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(encoded); stored[original_sha] = relative
        aliases.append({'source': str(source.relative_to(ROOT)), 'logical': logical, 'stored': relative,
                        'raw_bytes': len(value), 'raw_sha256': original_sha})
    def save(name, value):
        (target / name).write_text(json.dumps(value, indent=2, ensure_ascii=True) + '\n', encoding='utf-8')
    save('ALIASES.json', {'format': 'has_lossless_metadata_aliases_1', 'files': aliases})
    save('COMPACT_CASE_REPORTS.json', cases)
    save('HEADLESS_FAILURE_HISTORY.json', {'attempt1': 'wire Variant inference parse failure; dependent errors/owned headless timeout; remains FAILED',
         'attempt2': '77/1: negative-zero control targeted yaw_damping(field3), not actual signed-zero pitch_damping(field5); snapshot also dereferenced intentionally invalid index69; remains FAILED',
         'attempt3': '77/1 from the same wrong fixture field; snapshot errors fixed; remains FAILED',
         'corrected_evidence': 'Root corrected pitch_damping. Direct probe proves parsing -0.0 preserves0x80000000; JSON writing, including full_precision, normalizes+0. Zero-only compatibility preserves the original provenance word/prefix/wire SHA. Final79binding+17helper pass recorded independently in foundation.'})
    summary['packet_created'] = True; save('SUMMARY.json', summary)
    save('BOUNDARIES.json', {'scope': 'Actual four-case conversion/UI/history/HAS/cold opens and derived output; compact inactive binding and explicit helper review/cancel. No Source solver/artist fidelity/full canonical pass claim.',
         'excluded': 'No GLB/HAS/media/native binaries, authored fixture files, expected.json full rigs, full coordinates/private observed proof or full parameters report copied. Source matrix and raw logs/receipts retained losslessly; compact crosswalk has identities only.',
         'source_context': 'Exact passed working-source matrix at HEAD7477; not represented as a clean already-pushed implementation checkpoint.'})
    rows = [{'path': path.relative_to(target).as_posix(), 'bytes': path.stat().st_size, 'sha256': digest(path.read_bytes())}
            for path in sorted(target.rglob('*')) if path.is_file()]
    save('INDEX.json', {'format': 'has_metadata_source_packet_index_1', 'files': rows})
    print(json.dumps({'packet': str(target), 'files': len(rows), 'bytes': sum(row['bytes'] for row in rows),
                      'INDEX_sha256': digest((target / 'INDEX.json').read_bytes()), 'lossless_aliases': len(aliases)}))


if __name__ == '__main__':
    main()
