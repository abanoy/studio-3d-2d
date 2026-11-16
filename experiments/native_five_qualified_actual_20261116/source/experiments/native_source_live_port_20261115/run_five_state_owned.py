"""SOURCE-ONLY UNRUN successor. Root may stage under experiments/native_source_live_port_20261115 after full closure; supplied inputs stay read-only."""
from pathlib import Path
import datetime
import hashlib
import json
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
ENGINE = Path(r'C:\a\tools\Godot\Godot_v4.6-stable_win64.exe')
ENGINE_SHA = '63913d01be2c2d1f929b4a626f5347117126b34e9c64cbf350ea9f35a9657ebf'
PWSH = Path(r'C:\Users\noble\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe')
PWSH_SHA = '2a6769a3330dc1084d0154bfde7d164ab750ca7f700f313f9d417c1be78b2233'
INPUT = ROOT / 'output/sfm-bone-bindings-native-launch-20261114T033026205/run/Studio/output/compatibility/source-1794627119-888-34370685'
EXPECTED = {'scene.glb': '4e6ac7c2a7a84dea4b46b0bcb5724af68781243f57737e555b4cc82f2628b90d',
            'parameters.json': 'b807fc82ac1b1d1658b659b41250001e3bdecde99c3d32764122c2add6b51eed'}
SCRIPT = 'tests/source_native_five_state_unit.gd'
SCRIPT_SHA = 'ab40f406e7b2ececc719761f0f0246ecb347bf853d711c3901671c8b8d6d7174'
EXPECTED_NAMES = ['baseline.direct_nonzero_null_atomic', 'baseline.direct_nonzero_null_pose_exact', 'baseline.direct_nonzero_null_refused', 'cleanup.authored3_restored', 'cleanup.owned_sources_restored', 'cleanup.passed_inputs_read_only', 'cleanup.report_files_untouched', 'file.header.create_refused', 'file.header.isolated_observation', 'file.header.keys_report_unchanged', 'file.header.refused', 'file.header.restored', 'file.header.state_atomic', 'file.length.create_refused', 'file.length.isolated_observation', 'file.length.keys_report_unchanged', 'file.length.refused', 'file.length.restored', 'file.length.state_atomic', 'file.mtime.isolated_observation', 'file.mtime.keys_report_unchanged', 'file.mtime.refused', 'file.mtime.restored', 'file.mtime.state_atomic', 'instances.A120_preserves_BC', 'instances.B120_equals_A_C_unused', 'instances.create3', 'instances.dispose3_inactive', 'instances.equal_seed_different_instances', 'instances.keys_complete_pose_raw_reports_unchanged', 'instances.reenable_exact_seed', 'load.a.actual_Model_SceneIO', 'load.a.complete_nonrest_baseline', 'load.a.copied', 'load.a.fresh_partial_dictionary', 'load.a.fresh_rest_null', 'load.a.qualified69_49', 'load.a.raw_report_file_exact', 'load.b.actual_Model_SceneIO', 'load.b.complete_nonrest_baseline', 'load.b.copied', 'load.b.fresh_partial_dictionary', 'load.b.fresh_rest_null', 'load.b.qualified69_49', 'load.b.raw_report_file_exact', 'load.c.actual_Model_SceneIO', 'load.c.complete_nonrest_baseline', 'load.c.copied', 'load.c.fresh_partial_dictionary', 'load.c.fresh_rest_null', 'load.c.qualified69_49', 'load.c.raw_report_file_exact', 'negative.actor_base.keys_report_unchanged', 'negative.actor_base.refused', 'negative.actor_base.restored', 'negative.actor_base.seeded', 'negative.actor_base.state_atomic', 'negative.actor_index.create_refused', 'negative.actor_index.keys_report_unchanged', 'negative.actor_index.refused', 'negative.actor_index.restored', 'negative.actor_index.seeded', 'negative.actor_index.state_atomic', 'negative.actor_order.keys_report_unchanged', 'negative.actor_order.refused', 'negative.actor_order.restored', 'negative.actor_order.seeded', 'negative.actor_order.state_atomic', 'negative.ancestor_parent.create_refused', 'negative.ancestor_parent.keys_report_unchanged', 'negative.ancestor_parent.refused', 'negative.ancestor_parent.restored', 'negative.ancestor_parent.seeded', 'negative.ancestor_parent.state_atomic', 'negative.cached_index.keys_report_unchanged', 'negative.cached_index.refused', 'negative.cached_index.restored', 'negative.cached_index.seeded', 'negative.cached_index.state_atomic', 'negative.cached_parent.keys_report_unchanged', 'negative.cached_parent.refused', 'negative.cached_parent.restored', 'negative.cached_parent.seeded', 'negative.cached_parent.state_atomic', 'negative.chain_binding_kind.keys_report_unchanged', 'negative.chain_binding_kind.refused', 'negative.chain_binding_kind.restored', 'negative.chain_binding_kind.seeded', 'negative.chain_binding_kind.state_atomic', 'negative.chain_duplicate.keys_report_unchanged', 'negative.chain_duplicate.refused', 'negative.chain_duplicate.restored', 'negative.chain_duplicate.seeded', 'negative.chain_duplicate.state_atomic', 'negative.chain_id.keys_report_unchanged', 'negative.chain_id.refused', 'negative.chain_id.restored', 'negative.chain_id.seeded', 'negative.chain_id.state_atomic', 'negative.chain_reorder.keys_report_unchanged', 'negative.chain_reorder.refused', 'negative.chain_reorder.restored', 'negative.chain_reorder.seeded', 'negative.chain_reorder.state_atomic', 'negative.chain_source_binding.keys_report_unchanged', 'negative.chain_source_binding.refused', 'negative.chain_source_binding.restored', 'negative.chain_source_binding.seeded', 'negative.chain_source_binding.state_atomic', 'negative.data_sha.create_refused', 'negative.data_sha.keys_report_unchanged', 'negative.data_sha.refused', 'negative.data_sha.restored', 'negative.data_sha.seeded', 'negative.data_sha.state_atomic', 'negative.disabled_bone.create_refused', 'negative.disabled_bone.keys_report_unchanged', 'negative.disabled_bone.refused', 'negative.disabled_bone.restored', 'negative.disabled_bone.seeded', 'negative.disabled_bone.state_atomic', 'negative.dt_double.keys_report_unchanged', 'negative.dt_double.refused', 'negative.dt_double.restored', 'negative.dt_double.seeded', 'negative.dt_double.state_atomic', 'negative.dt_nan.keys_report_unchanged', 'negative.dt_nan.refused', 'negative.dt_nan.restored', 'negative.dt_nan.seeded', 'negative.dt_nan.state_atomic', 'negative.dt_negative.keys_report_unchanged', 'negative.dt_negative.refused', 'negative.dt_negative.restored', 'negative.dt_negative.seeded', 'negative.dt_negative.state_atomic', 'negative.dt_zero.keys_report_unchanged', 'negative.dt_zero.refused', 'negative.dt_zero.restored', 'negative.dt_zero.seeded', 'negative.dt_zero.state_atomic', 'negative.force_large.keys_report_unchanged', 'negative.force_large.refused', 'negative.force_large.restored', 'negative.force_large.seeded', 'negative.force_large.state_atomic', 'negative.force_multiple.keys_report_unchanged', 'negative.force_multiple.refused', 'negative.force_multiple.restored', 'negative.force_multiple.seeded', 'negative.force_multiple.state_atomic', 'negative.force_nan.keys_report_unchanged', 'negative.force_nan.refused', 'negative.force_nan.restored', 'negative.force_nan.seeded', 'negative.force_nan.state_atomic', 'negative.force_slot_0.keys_report_unchanged', 'negative.force_slot_0.refused', 'negative.force_slot_0.restored', 'negative.force_slot_0.seeded', 'negative.force_slot_0.state_atomic', 'negative.force_slot_1.keys_report_unchanged', 'negative.force_slot_1.refused', 'negative.force_slot_1.restored', 'negative.force_slot_1.seeded', 'negative.force_slot_1.state_atomic', 'negative.force_slot_2.keys_report_unchanged', 'negative.force_slot_2.refused', 'negative.force_slot_2.restored', 'negative.force_slot_2.seeded', 'negative.force_slot_2.state_atomic', 'negative.force_slot_3.keys_report_unchanged', 'negative.force_slot_3.refused', 'negative.force_slot_3.restored', 'negative.force_slot_3.seeded', 'negative.force_slot_3.state_atomic', 'negative.force_slot_4.keys_report_unchanged', 'negative.force_slot_4.refused', 'negative.force_slot_4.restored', 'negative.force_slot_4.seeded', 'negative.force_slot_4.state_atomic', 'negative.foreign_modifier.create_refused', 'negative.foreign_modifier.keys_report_unchanged', 'negative.foreign_modifier.refused', 'negative.foreign_modifier.restored', 'negative.foreign_modifier.seeded', 'negative.foreign_modifier.state_atomic', 'negative.import_map.create_refused', 'negative.import_map.keys_report_unchanged', 'negative.import_map.refused', 'negative.import_map.restored', 'negative.import_map.seeded', 'negative.import_map.state_atomic', 'negative.native_report.create_refused', 'negative.native_report.keys_report_unchanged', 'negative.native_report.refused', 'negative.native_report.restored', 'negative.native_report.seeded', 'negative.native_report.state_atomic', 'negative.physical_body.actual_simulating', 'negative.physical_body.create_refused', 'negative.physical_body.keys_report_unchanged', 'negative.physical_body.refused', 'negative.physical_body.restored', 'negative.physical_body.seeded', 'negative.physical_body.state_atomic', 'negative.show_rest_only.create_refused', 'negative.show_rest_only.keys_report_unchanged', 'negative.show_rest_only.refused', 'negative.show_rest_only.restored', 'negative.show_rest_only.seeded', 'negative.show_rest_only.state_atomic', 'negative.skeleton_rest.keys_report_unchanged', 'negative.skeleton_rest.refused', 'negative.skeleton_rest.restored', 'negative.skeleton_rest.seeded', 'negative.skeleton_rest.state_atomic', 'negative.source_path.keys_report_unchanged', 'negative.source_path.refused', 'negative.source_path.restored', 'negative.source_path.seeded', 'negative.source_path.state_atomic', 'rotation.half.Off_exact', 'rotation.half.authored_preserved', 'rotation.half.fixed_ticks', 'rotation.half.sizes_exact', 'rotation.one.Off_exact', 'rotation.one.authored_preserved', 'rotation.one.fixed_ticks', 'rotation.one.sizes_exact', 'rotation.two.Off_exact', 'rotation.two.authored_preserved', 'rotation.two.fixed_ticks', 'rotation.two.sizes_exact', 'wrapper.64_unselected_world_bones_exact', 'wrapper.A120_preserves_BC', 'wrapper.complete_authored_pose_preserved', 'wrapper.create3_native', 'wrapper.invalid_dt_no_state_commit', 'wrapper.keys_raw_reports_immutable', 'wrapper.off_dispose_restore3_exact', 'wrapper.record_skip_no_state_commit', 'wrapper.reenable_exact_seed', 'wrapper.reenable_replay_exact', 'wrapper.reverse_no_state_commit', 'wrapper.seek_no_state_commit', 'wrapper_inventory.binding_shape.atomic', 'wrapper_inventory.binding_shape.refused', 'wrapper_inventory.binding_shape.restored', 'wrapper_inventory.binding_shape.visual_exact', 'wrapper_inventory.count.atomic', 'wrapper_inventory.count.refused', 'wrapper_inventory.count.restored', 'wrapper_inventory.count.visual_exact', 'wrapper_inventory.joints_empty.atomic', 'wrapper_inventory.joints_empty.refused', 'wrapper_inventory.joints_empty.restored', 'wrapper_inventory.joints_empty.visual_exact', 'wrapper_inventory.order.atomic', 'wrapper_inventory.order.refused', 'wrapper_inventory.order.restored', 'wrapper_inventory.order.visual_exact', 'wrapper_inventory.source_missing.atomic', 'wrapper_inventory.source_missing.refused', 'wrapper_inventory.source_missing.restored', 'wrapper_inventory.source_missing.visual_exact']
BAD = ['ERROR:', 'WARNING:', 'SCRIPT ERROR', 'ObjectDB instances leaked',
       'resources still in use', 'Pages in use exist at exit', 'FAIL source_native_state.']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def closed(folder, name):
    # Read-only process inventory. The separately launched owner review is not
    # under this checkout and is never closed, hidden, or otherwise controlled.
    code = "$ErrorActionPreference='Stop'; $items=@(Get-CimInstance Win32_Process | Where-Object {$_.Name -match '^(Godot.*|blender|ffmpeg|ffprobe)\\.exe$' -and $_.CommandLine -like '*has-acceptance-session-20261111*'}); @{owned_count=$items.Count;observed_utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json -Compress"
    child = subprocess.Popen([str(PWSH), '-NoLogo', '-NoProfile', '-NonInteractive', '-Command', code], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
    out, err = child.communicate(timeout=30)
    (folder / (name + '-inventory-stdout.log')).write_bytes(out)
    (folder / (name + '-inventory-stderr.log')).write_bytes(err)
    save(folder / (name + '-inventory-process.json'), {'pid':child.pid,'exit':child.returncode,'retained_Popen_reaped':child.poll() is not None})
    assert child.returncode == 0 and not err.strip(), 'Read-only process inventory failed'
    value = json.loads(out)
    save(folder / (name + '-runtime-closure.json'), value)
    assert value['owned_count'] == 0, 'An owned runtime is still active'
    return value


def main():
    assert sha(ENGINE) == ENGINE_SHA and sha(PWSH) == PWSH_SHA
    assert sha(ROOT / SCRIPT) == SCRIPT_SHA
    assert all(sha(INPUT / name) == expected for name, expected in EXPECTED.items())
    tag = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    folder = ROOT / 'output' / ('source-native-five-state-' + tag)
    folder.mkdir()
    closed(folder, 'before')
    project = folder / 'Studio'
    project.mkdir()
    paths = sorted(p for p in (ROOT / 'src').rglob('*') if p.is_file() and p.suffix != '.pyc' and '__pycache__' not in p.parts)
    paths += sorted((ROOT / 'data').glob('*.json')) + [ROOT / 'project.godot', ROOT / SCRIPT]
    pins = []
    for source in paths:
        relative = source.relative_to(ROOT)
        assert not source.is_symlink()
        target = project / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        pins.append({'path': relative.as_posix(), 'bytes': source.stat().st_size, 'sha256': sha(source)})
    save(folder / 'SOURCE.json', {'source_HEAD': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(), 'files': pins})
    inputs = folder / 'read-only-inputs'
    inputs.mkdir()
    for name, expected in EXPECTED.items():
        (inputs / name).write_bytes((INPUT / name).read_bytes())
        assert sha(inputs / name) == expected
    job = {'format': 'has_source_native_five_state_job_2', 'phase': 'ROOT_APPROVED_HEADLESS_FIVE_STATE_TEST',
           'folder': str(folder), 'glb': str(inputs / 'scene.glb'), 'report': str(inputs / 'parameters.json'),
           'engine_sha256': ENGINE_SHA, 'expected_script_sha256': SCRIPT_SHA,
           'source_manifest_sha256': sha(folder / 'SOURCE.json'), 'root_closed_all': True,
           'expires_unix': time.time() + 600}
    save(folder / 'job.json', job)
    phases = []
    for phase, options in [('parse', ['--check-only']), ('state', [])]:
        log = folder / (phase + '-engine.log')
        command = [str(ENGINE), '--headless', '--path', str(project), '--audio-driver', 'Dummy', '--log-file', str(log), '--script', 'res://' + SCRIPT, *options, '--', str(folder / 'job.json')]
        save(folder / (phase + '-command.json'), command)
        started = time.monotonic()
        child = subprocess.Popen(command, cwd=project, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
        timed_out = False
        forced_kill = False
        try:
            out, err = child.communicate(timeout=30 if phase == 'parse' else 200)
        except subprocess.TimeoutExpired:
            timed_out = True
            child.terminate()
            try:
                out, err = child.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                forced_kill = True
                child.kill()
                out, err = child.communicate(timeout=5)
        (folder / (phase + '-stdout.log')).write_bytes(out)
        (folder / (phase + '-stderr.log')).write_bytes(err)
        combined = out.decode('utf-8', errors='replace') + err.decode('utf-8', errors='replace') + (log.read_text(encoding='utf-8', errors='replace') if log.exists() else '')
        markers = [line for line in combined.splitlines() if any(value in line for value in BAD)]
        passed = child.returncode == 0 and not timed_out and not markers
        row = {'phase': phase, 'pid': child.pid, 'exit': child.returncode, 'retained_Popen_reaped': child.poll() is not None, 'timed_out': timed_out, 'owned_child_terminated': timed_out, 'owned_child_forced_kill': forced_kill, 'seconds': time.monotonic()-started, 'error_markers': markers, 'passed': passed}
        save(folder / (phase + '-process.json'), row)
        phases.append(row)
        if not passed:
            break
    result_path = folder / 'result.json'
    actual = json.loads(result_path.read_text(encoding='utf-8')) if result_path.exists() else None
    result_valid = (isinstance(actual, dict) and actual.get('checks') == 266 and actual.get('failures') == 0
                    and actual.get('format') == 'has_source_native_five_state_result_2'
                    and actual.get('scope', {}).get('native_rule_indices_selected') == [8,17,18,26,27]
                    and actual.get('scope', {}).get('native_rules_solved') == 5
                    and set(actual.get('named_checks', {})) == set(EXPECTED_NAMES)
                    and all(type(value) is bool for value in actual.get('named_checks', {}).values())
                    and actual.get('complete_assertion_set') is True
                    and actual.get('job_sha256') == sha(folder / 'job.json')
                    and actual.get('test_script_sha256') == SCRIPT_SHA
                    and actual.get('source_manifest_sha256') == sha(folder / 'SOURCE.json')
                    and actual.get('metrics', {}).get('actors_loaded') == 3
                    and actual.get('cleanup', {}).get('owned_copy_hashes_restored') is True
                    and actual.get('cleanup', {}).get('passed_input_hashes_preserved') is True
                    and len(actual.get('named_checks', {})) == 266 and all(actual.get('named_checks', {}).values()))
    source_preserved = all(sha(ROOT / p['path']) == sha(project / p['path']) == p['sha256'] for p in pins)
    inputs_preserved = all(sha(INPUT / name) == sha(inputs / name) == expected for name, expected in EXPECTED.items())
    runtimes_preserved = sha(ENGINE) == ENGINE_SHA and sha(PWSH) == PWSH_SHA
    after = closed(folder, 'after')
    result = {'format': 'has_source_native_five_state_verification_2', 'passed': len(phases)==2 and all(p['passed'] for p in phases) and bool(result_valid) and source_preserved and inputs_preserved and runtimes_preserved,
              'phases': phases, 'actual_result_valid': bool(result_valid), 'checks_observed': actual.get('checks',0) if actual else 0,
              'failures_observed': actual.get('failures') if actual else None,
              'preservation': {'source':source_preserved,'read_only_inputs':inputs_preserved,'runtimes':runtimes_preserved},
              'runtime_lease_released':after['owned_count']==0,
              'test_result_sha256':sha(result_path) if result_path.exists() else None,
              'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    save(folder / 'verification.json', result)
    print(json.dumps({'folder':str(folder),**result}))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
