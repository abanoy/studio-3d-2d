"""Whitelist-copy metadata and source only; never copy private normal arrays/art."""
from pathlib import Path
import gzip, hashlib, json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
HEAD = '52f63c944ded7a651da871524d23a345b606424d'
FULL = ROOT / 'output/windows-canonical-bone-binding-20261116T041518335'
PACKETS = {
    'original': ('normal_boundary_probe_20261116', '49e7f5067be896b2faab57ae41f3afb2089a94a55b9988ea35150e4227f73856'),
    'sentinel': ('normal_boundary_probe_sentinel_20261116', 'a2475b28c03c6b87cc0d98d537433204b9553122a97f1197321455a491e2ef64'),
}
copies = []

def digest(raw): return hashlib.sha256(raw).hexdigest()
def load(path): return json.loads(path.read_bytes())
def write(name, raw):
    path = HERE / name
    assert path.resolve().is_relative_to(HERE) and not path.exists(), name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream: stream.write(raw)
def save(name, value): write(name, (json.dumps(value, indent=2, allow_nan=False) + '\n').encode())
def copy(source, name, compressed=False):
    assert source.is_file() and not source.is_symlink()
    assert source.name != 'PRIVATE_NORMALS.json'
    assert source.suffix.lower() not in {'.blend', '.glb', '.mdl', '.vvd', '.has', '.png', '.wav', '.mp4'}
    raw = source.read_bytes()
    assert len(raw) < 500_000, (source, len(raw))
    packed = gzip.compress(raw, mtime=0) if compressed else raw
    write(name, packed)
    copies.append({'original': str(source), 'payload': name, 'codec': 'gzip' if compressed else 'identity',
                   'raw_bytes': len(raw), 'raw_sha256': digest(raw),
                   'payload_bytes': len(packed), 'payload_sha256': digest(packed)})

def main():
    for label, (folder, expected) in PACKETS.items():
        source = ROOT / 'experiments' / folder
        assert digest((source / 'INDEX.json').read_bytes()) == expected
        index = load(source / 'INDEX.json')
        rows = index['files']
        entries = rows.items() if isinstance(rows, dict) else ((row['path'], row) for row in rows)
        copy(source / 'INDEX.json', 'source/' + label + '/INDEX.json')
        for name, row in entries:
            path = source / name
            assert path.resolve().is_relative_to(source.resolve())
            assert len(path.read_bytes()) == row['bytes'] and digest(path.read_bytes()) == row['sha256']
            copy(path, 'source/' + label + '/' + name)
    coordinator = ROOT / 'experiments/normal_boundary_probe_actual_20261116'
    for name in ('run_owned.py', 'run_sentinel_owned.py', 'prepare_sentinel_runner.py', 'stage_with_trace.py'):
        copy(coordinator / name, 'source/root-coordinator/' + name)
    for source in ('tools/private_desktop.py',
                   'experiments/resume_root_20261115/audit_protected_inputs_before_cleanup.py',
                   'experiments/source_appearance/native_coordinates_20261114/prove_coordinates_stdlib.py'):
        copy(ROOT / source, 'source/locked/' + Path(source).name)
    copy(ROOT / 'experiments/replay_audio_fix_20261115/builder/input-lock.json', 'context/input-lock.json.gz', True)
    for name in ('state.json', 'launch.json', 'root-birth-observation.json', 'source-before.json',
                 'source-after.json', 'authoritative-host-termination.json',
                 'authoritative-host-terminal.json', 'graphics-lease-released.json'):
        copy(FULL / name, 'context/full/' + name + ('.gz' if name.startswith('source-') else ''), name.startswith('source-'))
    private_metadata = []
    for number in (1, 2):
        stage = ROOT / ('output/normal-boundary-20261116-attempt' + str(number))
        prefix = 'attempt' + str(number) + '/'
        for name in ('lease.json', 'ROOT_COMMANDS.json', 'STAGED.json', 'private-receipt.json', 'capture/PUBLIC_CAPTURE.json'):
            copy(stage / name, prefix + name)
        names = ['before-closure.json', 'after-closure.json', 'verification.json']
        names += [phase + '-' + suffix for phase in ('before', 'after') for suffix in ('inventory-stdout.log', 'inventory-stderr.log')]
        names += ['capture-' + suffix for suffix in ('command.json', 'process.json', 'start.json', 'stdout.log', 'stderr.log')]
        if number == 2:
            names += ['comparison-' + suffix for suffix in ('command.json', 'process.json', 'start.json', 'stdout.log', 'stderr.log')]
            copy(stage / 'BLENDER_BOUNDARY_COMPARISON.json', prefix + 'BLENDER_BOUNDARY_COMPARISON.json')
        for name in names: copy(stage / 'root-execution' / name, prefix + 'root-execution/' + name)
        private = stage / 'capture/PRIVATE_NORMALS.json'
        # Hash in place, then discard bytes; this file never enters the packet.
        with private.open('rb') as stream: private_sha = hashlib.file_digest(stream, 'sha256').hexdigest()
        public = load(stage / 'capture/PUBLIC_CAPTURE.json')
        assert private_sha == public['private_sha256'] and private.stat().st_size == public['private_bytes']
        private_metadata.append({'attempt': number, 'private_local_path': str(private),
                                 'bytes': private.stat().st_size, 'sha256': private_sha, 'copied': False})
    for name in ('normal-preflight-runtime-stamps-20261116.json',
                 'normal-runtime-stage-trace-1794872690018354700.json',
                 'normal-runtime-stage-trace-1794872697847387300.json'):
        copy(ROOT / 'output' / name, 'preflight/' + name)
    save('PRIVATE_DATA_RETENTION.json', {'format': 'has_private_normal_retention_metadata_1',
         'files': private_metadata, 'exact_private_capture_bytes_equal': private_metadata[0]['sha256'] == private_metadata[1]['sha256'],
         'private_arrays_published': False, 'art_or_raw_full_report_copied': False})
    save('PREPARATION_OBSERVATIONS.json', {
        'format': 'has_normal_preparation_observation_1',
        'artifact_observations': [
            {'artifact': 'preflight/normal-preflight-runtime-stamps-20261116.json',
             'meaning': 'Initial ffmpeg strict file-stamp refusal; no stage created. Three subsequent four-stamp observations all agree with the approved hash. Cause remains UNDETERMINED.'},
            {'artifact': 'preflight/normal-runtime-stage-trace-1794872690018354700.json',
             'meaning': 'All six unchanged strict identities passed. Instrumented runpy setup then refused missing probe_support before staging.'},
            {'artifact': 'preflight/normal-runtime-stage-trace-1794872697847387300.json',
             'meaning': 'After adding the packet script directory to sys.path, all six unchanged strict identities and the unchanged stager passed.'}],
        'root_reported_tool_trace_only_observations': [
            'An initial attempt2 stager refused a pythonw file-stamp mismatch before writes; initial failing stamps were not retained, so cause remains UNDETERMINED.',
            'A nested-quote temporary Python runner generator had SyntaxError, followed by a missing-runner launch; no native process started.',
            'The first attempt2 coordinator preparation assumed dict INDEX rows but received a list, refusing before an output directory or native process. The retained coordinator handles either exact schema.'],
        'reported_observation_provenance': 'Root task handoff and tool trace; no separate raw log is asserted for these three observations.',
        'strict_identity_gate_changed': False, 'invented_logs_or_stamps': False,
        'historical_preparation_statuses_preserved': True})
    comparison = load(ROOT / 'output/normal-boundary-20261116-attempt2/BLENDER_BOUNDARY_COMPARISON.json')
    one = load(ROOT / 'output/normal-boundary-20261116-attempt1/root-execution/verification.json')
    two = load(ROOT / 'output/normal-boundary-20261116-attempt2/root-execution/verification.json')
    save('BENCHMARK.json', {
        'format': 'has_normal_boundary_actual_benchmark_1', 'source_commit': HEAD,
        'diagnostic_status': 'COHERENT_BOUNDARY_MEASUREMENT', 'normal_fidelity': 'FAILED_UNQUALIFIED',
        'original_threshold': 2e-5, 'original_failures': comparison['original_raw_gate']['raw_metrics']['diagnostic_above_2e_5'],
        'original_count': comparison['exported_vertices'], 'original_max_distance': comparison['original_raw_gate']['raw_metrics']['max'],
        'original_mean_distance': comparison['original_raw_gate']['raw_metrics']['mean'],
        'captured_meshes': comparison['captured_meshes'], 'captured_corners': comparison['captured_corners'],
        'matched_exported_vertices': comparison['matched_exported_vertices'], 'unmatched_exported_vertices': comparison['unmatched_exported_vertices'],
        'exporter_prediction_max_error': comparison['exporter_prediction_error']['max'],
        'native_to_saved_blender_best_above_threshold': comparison['metrics']['native_raw_to_blender_transported_raw']['raw_distance']['diagnostic_above_2e_5'],
        'saved_blender_to_glb_above_threshold': comparison['metrics']['blender_transported_raw_to_glb_raw']['raw_distance']['diagnostic_above_2e_5'],
        'attempt1': {'capture': one['capture'], 'comparison': 'UNRUN', 'diagnostic_completed': False,
                     'physical_job_and_desktop_closed': True, 'window_seen': False, 'desktop_confirmed': False,
                     'root_closure_owned_count': 0, 'placement_qualification': 'FAILED'},
        'attempt2': {'capture': two['capture'], 'comparison': two['comparison'], 'diagnostic_completed': True,
                     'physical_job_and_desktop_closed': True, 'window_seen': True, 'desktop_confirmed': True,
                     'root_closure_owned_count': 0, 'strict_sentinel_policy_satisfied': True},
        'identical_private_capture_sha256': private_metadata[0]['sha256'],
        'interpretation': 'The saved corner-normal/exporter boundary is measured coherently; original native fidelity still fails. Normalization does not repair it. Corner ambiguity prevents unique setter/encoder causal attribution.',
        'hidden_window_scope': 'Background process desktop placement only; no Blender GUI or rendering assertion.',
        'product_source_changed_by_probe': False, 'installed_sources_modified': False,
        'private_arrays_published': False, 'new_acceptance_checks_claimed': 0, 'human_review': 'DEFERRED_NO_RESULT'})
    save('SOURCE_MANIFEST.json', {'format': 'has_normal_boundary_actual_source_manifest_1',
         'copies': copies, 'exact_copy_count': len(copies),
         'source_packet_indexes': {k: value[1] for k, value in PACKETS.items()},
         'coordinator_alias_scope': 'Exact current post-run source snapshots. Process records prove the invoked command; no extra prelaunch coordinator digest record is invented.',
         'raw_full_report_copied': False, 'private_normals_copied': False})
    rows = []
    for path in sorted(HERE.rglob('*')):
        if path.is_file() and path != HERE / 'INDEX.json' and '__pycache__' not in path.parts:
            raw = path.read_bytes(); rows.append({'path': path.relative_to(HERE).as_posix(), 'bytes': len(raw), 'sha256': digest(raw)})
    save('INDEX.json', {'format': 'has_normal_boundary_actual_index_1', 'payload_files': len(rows),
         'payload_bytes': sum(row['bytes'] for row in rows), 'files': rows})
    print(json.dumps({'packet': str(HERE), 'files': len(rows), 'bytes': sum(row['bytes'] for row in rows),
                      'exact_copies': len(copies), 'index_sha256': digest((HERE / 'INDEX.json').read_bytes())}))

if __name__ == '__main__': main()
