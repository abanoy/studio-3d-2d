"""SOURCE-ONLY UNRUN proposed native5 editor/fan/Record and packed+linked cold-reader phase.

Consumes one original GLB/report from a passed normal native conversion run.
It does not reconvert MDL or claim a new converter test. Root owns the GPU lease.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
GLB_SHA = 'b8436dea1d13a7cb4632c37c50b4cab123616ec574720fe4e764b844c5293e71'  # Bind only after actual live Root success.
LIVE_ROOT_RESULT_SHA = 'db271160d54d5c2fa62089f928360015b80d8e08f8348a3ad3aeebd8c574bae7'
LIVE_CROSSWALK_PROOF_SHA = 'fb677e1a5e196f964c3634abba009ff792e7af0ff6dda260abc2e3ee12dacc37'
PARAM_SHA = 'dbff99d5e84042812dc75edc3135727efc40eee62fa554b23746e0cb4ea6d69d'
GODOT_SHA = '63913d01be2c2d1f929b4a626f5347117126b34e9c64cbf350ea9f35a9657ebf'
CAPTURE_SHA = 'b1dc120815f9e56b79ca4406dd3a04ddd5b0978510c6e5ca8234b11ae88ff58b'
BAD = ('ERROR:', 'WARNING:', 'SCRIPT ERROR', 'SHADER ERROR', 'FAIL ',
       'ObjectDB instances leaked', 'unclaimed string names', 'Pages in use exist at exit')
sys.dont_write_bytecode = True


def names(mode, export_frames=False):
    if mode != 'writer':
        result = ['cold.no_autoactivation', 'cold.bound_profile', 'cold.report_49_unchanged',
                  'cold.fk_0', 'cold.frame_0', 'cold.fk_24', 'cold.frame_24', 'cold.arbitrary_seek']
        if export_frames:
            result += ['cold.export', 'cold.export_frame_0', 'cold.export_frame_24']
        return result
    result = ['import.normal_add_model', 'import.exact_69_49_no_generic', 'import.native8_identity',
              'import.nonrest_keys_valid', 'import.fresh_native5_on', 'import.fresh_native5_identity_fallback',
              'import.fresh_native5_off_exact', 'import.partial_native5_on_off',
              'import.keyed_root_rotation_constant_scale', 'fan.add_control', 'fan.actual_add',
              'fan.native_target_and_aim', 'fan.actual_field_reaches_joint', 'fan.controlled_transverse_fixture']
    result += [profile + '.' + suffix
               for profile in ('disabled', 'zero', 'miss', 'speed3', 'speed12', 'speed50', 'opposite')
               for suffix in ('on', 'fixed_ticks', 'weighted_profile', 'authored_and_64_bones', 'off_restores_authored')]
    result += ['fan.zero_equals_disabled', 'fan.miss_equals_disabled']
    result += ['fan.' + profile + '_weighted_response' for profile in ('speed3', 'speed12', 'speed50', 'opposite')]
    result += ['fan.strong_response_and_wiggle', 'fan.opposite_tip_directions',
               'off.all_profiles_keep_authored', 'off.keyed12_weighted_exact',
               'body.refuse_allocation_while_native', 'off.keyed24_weighted_exact',
               'seek.restores_without_draft', 'save.restores_without_draft',
               'body.partial_rig_refuses_ragdoll', 'body.partial_refusal_preserves_model',
               'body.independent_primary_started', 'body.NativeHairOn_keepssameindependent_primary',
               'body.NativeHairOff_keepssameindependent_primary', 'body.test_authored_restore',
               'record.cancel_connected_local', 'record.escape_preserves_authored',
               'record.stop_connected_local', 'record.stop_ordinary_fk_take',
               'record.same_actor_and_immutable_report', 'record.undo_exact', 'record.redo_exact',
               'record.frame_0', 'record.frame_24', 'record.arbitrary_seek',
               'record.save_packed', 'record.save_linked', 'generic.existing_backend', 'generic.off']
    return result


def no_links(path):
    for item in (path, *path.parents):
        info = item.lstat()
        assert not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400


def identity(path):
    no_links(path)
    before = path.stat()
    assert path.is_file()
    with path.open('rb') as stream:
        value = hashlib.file_digest(stream, 'sha256').hexdigest()
    after = path.stat()
    assert (before.st_size, before.st_mtime_ns, before.st_ino) == (after.st_size, after.st_mtime_ns, after.st_ino)
    return {'bytes': after.st_size, 'mtime_ns': after.st_mtime_ns, 'sha256': value}


def save(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2); stream.write('\n')


def load(path):
    assert path.stat().st_size <= 16 * 1024 * 1024
    return json.loads(path.read_bytes())


def functional():
    files = [path for name in ('src', 'tests', 'tools', 'data', 'examples')
             for path in (ROOT / name).rglob('*')
             if path.is_file() and path.suffix != '.pyc' and '__pycache__' not in path.parts]
    files += [ROOT / name for name in ('main.tscn', 'project.godot', 'run.py', 'launch.pyw')]
    return {path.relative_to(ROOT).as_posix(): identity(path) for path in sorted(files)}


def execute(module, studio, folder, request, environment):
    folder.mkdir(exist_ok=False)
    request.update(format='has_source_native_five_transverse_live_job_3', folder=folder.as_posix(),
                   expected_glb_sha256=GLB_SHA, expected_parameters_sha256=PARAM_SHA,
                   qualified_live_root_sha256=LIVE_ROOT_RESULT_SHA)
    request['expected_names'] = names(request['mode'], request.get('export_frames', False))
    job = folder / 'job.json'
    save(job, request)
    previous = os.environ.get('HYBRID_GODOT')
    try:
        os.environ['HYBRID_GODOT'] = environment['HYBRID_GODOT']
        args = module.command('tests/source_native_five_corrected_live_ui.gd', extra=[
            '--audio-driver', 'Dummy', '--log-file', str(folder / 'engine.log'), '--', str(job)])
    finally:
        if previous is None:
            os.environ.pop('HYBRID_GODOT', None)
        else:
            os.environ['HYBRID_GODOT'] = previous
    assert '--receipt' in args and Path(args[args.index('--path') + 1]).resolve() == studio
    assert Path(args[1]).resolve() == studio / 'tools/private_desktop.py'
    assert Path(args[0]).resolve() == Path(sys.executable).with_name('pythonw.exe').resolve()
    receipt = folder / 'private-receipt.json'
    args[args.index('--receipt') + 1] = str(receipt)
    save(folder / 'command.json', args)
    process = subprocess.Popen(args, cwd=studio, env=environment,
                               stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    started = time.monotonic()
    execution_error = None
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=285)
    except BaseException as exc:
        timed_out = isinstance(exc, subprocess.TimeoutExpired)
        execution_error = {'type': type(exc).__name__, 'message': str(exc)}
        if process.poll() is None:
            process.kill()  # This exact retained private launcher, never arbitrary processes.
        stdout, stderr = process.communicate(timeout=20)
    (folder / 'stdout.log').write_bytes(stdout)
    (folder / 'stderr.log').write_bytes(stderr)
    engine = (folder / 'engine.log').read_text(encoding='utf-8', errors='replace') if (folder / 'engine.log').is_file() else ''
    texts = (stdout.decode('utf-8', 'replace'), stderr.decode('utf-8', 'replace'), engine)
    errors = [line for text in texts for line in text.splitlines() if any(token in line for token in BAD)]
    metadata_errors = []
    try:
        result = load(folder / 'result.json') if (folder / 'result.json').is_file() else {}
    except (ValueError, OSError) as exc:
        result = {}
        metadata_errors.append('result: ' + type(exc).__name__ + ': ' + str(exc))
    if not isinstance(result, dict):
        result = {}
        metadata_errors.append('result: dictionary required')
    try:
        private = load(receipt) if receipt.is_file() else {}
    except (ValueError, OSError) as exc:
        private = {}
        metadata_errors.append('private receipt: ' + type(exc).__name__ + ': ' + str(exc))
    if not isinstance(private, dict):
        private = {}
        metadata_errors.append('private receipt: dictionary required')
    result_ok = (result.get('format') == 'has_source_native_five_transverse_live_result_3' and result.get('mode') == request['mode']
                 and result.get('storage', '') == request.get('storage', '')
                 and result.get('checks') == len(request['expected_names'])
                 and result.get('complete_assertion_set') is True
                 and set(result.get('named_checks', {})) == set(request['expected_names'])
                 and all(type(value) is bool for value in result.get('named_checks', {}).values())
                 and type(result.get('failures')) is int
                 and result['failures'] == sum(value is False for value in result['named_checks'].values())
                 and result.get('job_sha256') == identity(job)['sha256']
                 and Path(result.get('job_path', '')).resolve() == job
                 and Path(result.get('project_root', '')).resolve() == studio
                 and result.get('source_manifest_sha256') == request['source_manifest_sha256']
                 and result.get('actual_editor') is True and result.get('native_rules_solved') == 5
                 and result.get('retained_rules') == 49 and result.get('private_native_arrays_serialized') is False)
    domain_ok = (result_ok and result.get('failures') == 0 and
                 all(value is True for value in result.get('named_checks', {}).values()))
    receipt_ok = (private.get('format') == 'studio_private_desktop_1' and private.get('exit') == 0
                  and all(private.get(key) is True for key in ('private_window_seen', 'child_desktop_confirmed', 'job_closed', 'desktop_closed'))
                  and all(private.get(key) is False for key in ('desktop_switch_requested', 'foreground_child_observed')))
    passed = (execution_error is None and not timed_out and process.poll() is not None and process.returncode == 0
              and not errors and not metadata_errors and result_ok and domain_ok and receipt_ok and 'SOURCE_NATIVE_LIVE ' in texts[0])
    proof = {'passed': passed, 'exit': process.returncode, 'timed_out': timed_out,
             'retained_Popen_reaped': process.poll() is not None, 'seconds': time.monotonic() - started,
             'execution_error': execution_error, 'error_markers': errors, 'metadata_errors': metadata_errors,
             'result_binding': result_ok, 'domain_checks_passed': domain_ok,
             'domain_failure_count': result.get('failures'),
             'private_receipt_passed': receipt_ok, 'private_receipt': str(receipt),
             'checks': result['checks'] if type(result.get('checks')) is int and 0 <= result['checks'] <= 10000 else 0,
             'result_sha256': identity(folder / 'result.json')['sha256'] if result else None}
    save(folder / 'process-verification.json', proof)
    return proof


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--glb', type=Path, required=True)
    parser.add_argument('--parameters', type=Path, required=True)
    parser.add_argument('--baseline-verification', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--run-gpu', action='store_true')
    parser.add_argument('--lease-confirmed', action='store_true')
    args = parser.parse_args()
    assert os.name == 'nt' and args.run_gpu and args.lease_confirmed
    folder = args.output.absolute()
    assert folder.is_relative_to(ROOT / 'output') and folder != ROOT / 'output' and not folder.exists()
    no_links(folder.parent)
    assert folder.resolve() == folder
    glb, parameters, baseline_path = (path.resolve(strict=True) for path in (args.glb, args.parameters, args.baseline_verification))
    originals = {str(path): identity(path) for path in (glb, parameters, baseline_path)}
    assert originals[str(glb)]['sha256'] == GLB_SHA and originals[str(parameters)]['sha256'] == PARAM_SHA
    assert all(type(value) is str and len(value) == 64 and all(ch in '0123456789abcdef' for ch in value)
               for value in (GLB_SHA, PARAM_SHA, LIVE_ROOT_RESULT_SHA, LIVE_CROSSWALK_PROOF_SHA)), 'Live profile is not yet qualified'
    assert originals[str(baseline_path)]['sha256'] == LIVE_ROOT_RESULT_SHA
    baseline = load(baseline_path)
    assert baseline.get('format') == 'has_source_live_native_normal_root_result_1'
    assert baseline.get('status') == 'LIVE_VMT_NORMALS_BONES_AND_PARAMETERS_MATCHED'
    assert all(baseline.get(key) == value for key, value in dict(models=2, points=9661, bones=69, jiggle_rules=49).items())
    assert baseline.get('final_normal_max_euclidean_error') == 0.0 and baseline.get('source_normal_threshold') == 2e-5
    assert baseline.get('final_parameters_crosswalk_bound') is True
    assert baseline.get('all_source_runtime_native_and_mount_preservation_checks_passed') is True
    assert baseline.get('private_job_closed') is True and baseline.get('retained_launcher_reaped') is True
    assert type(baseline.get('physical_owned_processes')) is int and baseline['physical_owned_processes'] == 0
    assert baseline.get('foreground_activation') is False and baseline.get('owned_lock_removed') is True
    assert baseline['artifacts']['scene_glb']['sha256'] == GLB_SHA and baseline['artifacts']['parameters_json']['sha256'] == PARAM_SHA
    assert Path(baseline['artifacts']['scene_glb']['path']).resolve() == glb and Path(baseline['artifacts']['parameters_json']['path']).resolve() == parameters
    # The exact Root receipt pin above binds its complete original/runtime/closure result.
    report = load(parameters)
    crosswalk = report['native_parameters']['source_export_crosswalk']
    assert crosswalk['glb_sha256'] == GLB_SHA and crosswalk['proof_sha256'] == LIVE_CROSSWALK_PROOF_SHA
    engine = Path(os.environ.get('HYBRID_GODOT', r'C:\a\tools\Godot\Godot_v4.6-stable_win64.exe')).resolve(strict=True)
    runtime_before = identity(engine)
    assert runtime_before['sha256'] == GODOT_SHA
    assert identity(ROOT / 'tests/source_native_five_capture.gd')['sha256'] == CAPTURE_SHA
    source_before = functional()
    folder.mkdir(exist_ok=False)
    studio = folder / 'Studio'
    studio.mkdir()
    for relative, expected in source_before.items():
        target = studio / relative
        assert target.is_relative_to(studio) and not target.exists()
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
        assert identity(target) == expected
    candidate_sources = {
        'src/source_secondary.gd': ROOT / 'src/source_secondary.gd',
        'tests/source_native_five_corrected_live_ui.gd': HERE / 'source_native_five_corrected_live_ui.gd',
    }
    candidate_pins = {str(path): identity(path) for path in candidate_sources.values()}
    frozen_source = dict(source_before)
    for relative, candidate_path in candidate_sources.items():
        target = studio / relative
        assert target.is_relative_to(studio) and target.is_file()
        shutil.copy2(candidate_path, target)
        frozen_source[relative] = identity(target)
        assert frozen_source[relative] == candidate_pins[str(candidate_path)]
    save(folder / 'source-before.json', source_before)
    save(folder / 'candidate-source.json', frozen_source)
    source_manifest_sha = identity(folder / 'candidate-source.json')['sha256']
    (studio / 'override.cfg').write_text('[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name=' +
                                       json.dumps('HAS native5 live ' + str(time.time_ns())) + '\n', encoding='utf-8')
    inputs = folder / 'owned-input'
    inputs.mkdir()
    for source, name in ((glb, 'scene.glb'), (parameters, 'parameters.json')):
        shutil.copy2(source, inputs / name)
        assert identity(inputs / name) == originals[str(source)]
    spec = importlib.util.spec_from_file_location('source_native_live_frozen_run', studio / 'run.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    environment = os.environ.copy()
    environment.update(PYTHONDONTWRITEBYTECODE='1', HYBRID_PYTHON=str(Path(sys.executable).resolve()), HYBRID_GODOT=str(engine))
    results = []
    error = None
    try:
        writer = folder / 'writer'
        results.append(execute(module, studio, writer, {'mode': 'writer', 'glb': (inputs / 'scene.glb').as_posix(),
                                                      'source_manifest_sha256': source_manifest_sha}, environment))
        assert results[-1]['passed'], 'Native editor writer failed; retain ' + str(writer)
        # Only the two disposable input copies move. Both literal endpoints are
        # verified inside this newly created run; original inputs stay untouched.
        transition = [inputs, writer / 'has-cache', studio / 'output/templates', studio / 'output/imports']
        offline_plan = []
        for path in transition:
            if not path.exists():
                continue
            offline = path.with_name(path.name + '.offline')
            assert not offline.exists() and path.resolve().is_relative_to(folder) and offline.resolve().is_relative_to(folder)
            no_links(path)
            offline_plan.append({'source': str(path), 'offline': str(offline)})
        save(folder / 'offline-plan.json', offline_plan)
        for row in offline_plan:
            Path(row['source']).rename(Path(row['offline']))
        for mode in ('packed', 'linked'):
            results.append(execute(module, studio, folder / ('reader-' + mode),
                                   {'mode': 'reader', 'storage': mode, 'expected': (writer / 'expected.json').as_posix(),
                                    'export_frames': mode == 'packed', 'source_manifest_sha256': source_manifest_sha}, environment))
            assert results[-1]['passed'], 'Native editor reader failed; retain ' + mode
    except BaseException as exc:
        error = {'type': type(exc).__name__, 'message': str(exc)}
    source_after = functional()
    save(folder / 'source-after.json', source_after)
    preservation = {'current_functional_source': source_before == source_after,
                    'original_native_GLB_report_and_baseline': all(identity(Path(path)) == pin for path, pin in originals.items()),
                    'approved_Godot': identity(engine) == runtime_before,
                    'frozen_functional_source': all(identity(studio / path) == pin for path, pin in frozen_source.items()),
                    'candidate_sources_unchanged': all(identity(Path(path)) == pin for path, pin in candidate_pins.items())}
    value = {'format': 'has_source_native_corrected_five_live_actual_verification_1',
             'passed': error is None and len(results) == 3 and all(row['passed'] for row in results) and all(preservation.values()),
             'checks_expected': len(names('writer')) + len(names('reader', True)) + len(names('reader', False)),
             'checks_observed': sum(row['checks'] for row in results),
             'phase_expected': {'writer': len(names('writer')), 'reader-packed': len(names('reader', True)),
                                'reader-linked': len(names('reader', False))},
             'results': results, 'error': error, 'preservation': preservation,
             'baseline_conversion': {'path': str(baseline_path), **originals[str(baseline_path)]},
             'native_conversion_performed_by_this_driver': False, 'native5_editor_backend_tested': True,
             'same_actor_reverse_body_qualification': 'UNQUALIFIED_PARTIAL_SOURCE_RIG',
             'private_arrays_in_public_result': False, 'output': str(folder)}
    save(folder / 'verification.json', value)
    print(json.dumps({key: value[key] for key in ('passed', 'checks_expected', 'checks_observed', 'phase_expected', 'error')}))
    return 0 if value['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
