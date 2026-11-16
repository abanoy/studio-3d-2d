"""Root-only frozen-chain experiments; prepared source, never auto-executed.

Run only after root reviews the current source and closes its existing lease:
  python -B experiments/native_source_live_port_20261115/run_chain_owned.py \
      --attempt 1 --acknowledge-historical-full

The retained full suite is f0dd57a, NOT a full-suite qualification of the current
dirty production port. Current state180 and new math/native probes have separate
scopes. This driver never changes source, installed apps or original model files.
"""
from pathlib import Path
import argparse
import ast
import datetime
import hashlib
import json
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
SELF = Path(__file__).resolve()
ENGINE = Path(r'C:\a\tools\Godot\Godot_v4.6-stable_win64.exe')
ENGINE_SHA = '63913d01be2c2d1f929b4a626f5347117126b34e9c64cbf350ea9f35a9657ebf'
PWSH = Path(r'C:\Users\noble\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe')
PWSH_SHA = '2a6769a3330dc1084d0154bfde7d164ab750ca7f700f313f9d417c1be78b2233'
FULL_HEAD = 'f0dd57a2e568089d396fecba819ab987da658bf0'
CURRENT_HEAD = '9de4e6cbdf8b0369cbdf118a40c13f85860eaac0'
PACKET = ROOT / 'experiments/source_0x31_chains_20261115'
PACKET_SHA = '5f204a52d82a61174da1dbb33da3c132f636b5d8bc5eba39f7679279599782c0'
COUNT_SHA = '846c05acdda220b6b189f8ce4d3174a69d708de5760fbd9bb38b56b326db98ae'
LEAF = ROOT / 'experiments/source_0x31_native_leaf_compat_20261115'
BUNDLE = ROOT / 'output/sfm-bone-bindings-native-launch-20261114T033026205/run/Studio/output/compatibility/source-1794627119-888-34370685'
STATE = ROOT / 'output/source-native-state-20261116T020227823185'
BAD = ('ERROR:', 'WARNING:', 'SCRIPT ERROR', 'SHADER ERROR', 'FAIL ',
       'ObjectDB instances leaked', 'unclaimed string names', 'resources still in use',
       'Pages in use exist at exit')
PROOFS = {
    'full_receipt': ('output/windows-canonical-bone-binding-20261115T225514304/state.json', '952613d8c02c7e41a98631cd563c640e750eafc5c6d535fce2bf1f27bd8bbecb'),
    'full_catalogue': ('output/windows-canonical-bone-binding-20261115T225514304/source-before.json', '8d9e7d94c745081e0ca084bc64e7498bc7ccb218c44209e1354bcd53f3c50a2a'),
    'full_closure': ('output/windows-canonical-bone-binding-20261115T225514304/authoritative-host-termination.json', 'c2a0f1b9027baeb45d0648708da2e6c87a77c2a91841a84a0241b70830674dba'),
    'FK_receipt': ('output/native-jiggle-headless-transport-prep-20261115/runtime-post-full-f0dd57a/verification.json', '57122759af2ad3c66687afab4c27b49ec09fba99bf4c5397e33e49125f650e64'),
    'FK_closure': ('output/native-jiggle-headless-transport-prep-20261115/runtime-post-full-f0dd57a/authoritative-closure.json', '10215a0b33c048cd74493af310ca9a4b1adfc1ab2c1577e748f72be937779513'),
    'math_receipt': ('output/source-0x31-godot-math-20261115-attempt1/verification.json', 'aed2991883ed196eb1f6f52cba0bc8c1609ea6a2e842e03f8f0d562490da996a'),
    'math_closure': ('output/source-0x31-godot-math-20261115-attempt1/authoritative-closure.json', 'e92e57e1f42a8c2834cca28618a9798910cda872b855bb70cb3ebc861bde3ff0'),
    'leaf_receipt': ('output/source-0x31-native-leaf-20261115-attempt3/verification.json', 'dcda15bbd1938b60cc7ce3bd8f8745a75bbedef2a28d90533bc5478f259e2261'),
    'leaf_closure': ('output/source-0x31-native-leaf-20261115-attempt3/authoritative-closure.json', '6822755f42de414a14a8c9bedca04f1c83e3436c7165ed00f8b2edfe938fc000'),
    'state_receipt': ('output/source-native-state-20261116T020227823185/verification.json', '31e08e4c15915f543b9df9ad8b01b4bfe472b7d47fde4558090cacc834d3097f'),
    'state_closure': ('output/source-native-state-20261116T020227823185/after-runtime-closure.json', '9d1f091c21750928489c6764a61bca50b82083bbc3c8e1d2ea7031471d921f95'),
    'state_source': ('output/source-native-state-20261116T020227823185/SOURCE.json', 'ac029880c8084961115e3e1233775585004c77dabd0fb867f55bd3238d642ce3'),
    'state_result': ('output/source-native-state-20261116T020227823185/result.json', 'a42cc5de39e6cbaadc5adbdf3811739ef979bc0f37c56c72e369e1f159d3d1e6'),
}
ALIASES = {
    'candidate': (ROOT / 'experiments/source_0x31_godot_candidate_20261115/candidate.gd', 'leaf_candidate.gd', '14053abf4b00c50909468d41372ce77c826bf0ec0b895bec19418a5961b4fae3'),
    'adapter': (LEAF / 'leaf_adapter.gd', 'leaf_adapter.gd', '6945153a65741f65f15505a1b840ddbf530c483790824d8a98e90a4d53e539e8'),
    'capture': (LEAF / 'weighted_capture.gd', 'weighted_capture.gd', '1ffecc00666a7e9e6957b7354fd0b862eac07b0f16b79200345370348e91aacb'),
    'harness': (LEAF / 'leaf_harness.gd', 'leaf_harness.gd', '2abbb08831586323878cabb504e5400406144ad34e4b890791539b68633f722c'),
    'chain_solver': (PACKET / 'chain_solver.gd', 'chain_solver.gd', '01635f84e05abe0ecc998b71117eed9c7afc6f5b15d04e8743cdf1c22efa362f'),
    'model_adapter': (PACKET / 'model_adapter.gd', 'model_adapter.gd', '38a226db7af1843c1f0df04318aaccc726dc88f7c61b9389f8aa029d52a4fe8c'),
    'chain_capture': (PACKET / 'chain_capture.gd', 'chain_capture.gd', 'b1dc120815f9e56b79ca4406dd3a04ddd5b0978510c6e5ca8234b11ae88ff58b'),
    'chain_harness': (PACKET / 'chain_harness.gd', 'chain_harness.gd', 'd25e37499f8a4b076a65e61a1a97c7ad7fb0d27828f1bd7a2bc76e9f6b0a8b5f'),
    'math_checks': (PACKET / 'math_checks.gd', 'math_checks.gd', '062b182c7b876658ec7b54132ec4d0125170b7506ad7bc469f92e2eb4cf61e32'),
}
INPUTS = {
    'glb': (BUNDLE / 'scene.glb', '4e6ac7c2a7a84dea4b46b0bcb5724af68781243f57737e555b4cc82f2628b90d'),
    'parameters': (BUNDLE / 'parameters.json', 'b807fc82ac1b1d1658b659b41250001e3bdecde99c3d32764122c2add6b51eed'),
    'mdl': (BUNDLE / 'native/junko hair.mdl', '8da09c905227ddc8eef73a3f83594a4eb1c3a6d5304ee41ba5471bef834bc716'),
    'vvd': (BUNDLE / 'native/junko hair.vvd', '2bfa2a363eea586d06d4fd0e28c7751c10276da5cc0c46c310ffa9dedbb159e0'),
}

# This wrapper is generated only in the fresh owned output project. The check
# object is RefCounted, so --script must target a SceneTree entry instead.
MATH_ENTRY = '''extends SceneTree
const Checks = preload("res://math_checks.gd")
func _initialize() -> void: call_deferred("run")
func run() -> void:
\tvar args := OS.get_cmdline_user_args()
\tif args.size() != 1: push_error("Fresh root chain math lease required"); quit(2); return
\tvar value = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
\tif not value is Dictionary or value.get("phase") != "ROOT_APPROVED_CHAIN_SYNTHETIC_MATH" or value.get("root_closed_all") != true or float(value.get("expires_unix",0)) <= Time.get_unix_time_from_system(): push_error("Invalid chain math authority"); quit(2); return
\tif DisplayServer.get_name() != "headless" or FileAccess.get_sha256(OS.get_executable_path()) != str(value.get("engine_sha256","")): push_error("Exact headless engine required"); quit(2); return
\tfor pin in value.files.values():
\t\tif not str(pin.path).is_absolute_path() or FileAccess.get_sha256(str(pin.path)) != str(pin.sha256): push_error("Changed chain math source/proof"); quit(2); return
\tvar path: String = value.public_result
\tif not path.is_absolute_path() or FileAccess.file_exists(path): push_error("Fresh math result required"); quit(2); return
\tvar checks = Checks.new()
\tvar result: Dictionary = checks.run()
\tresult["root_lease_sha256"] = FileAccess.get_sha256(args[0])
\tvar passed: bool = result.get("status") == "PASSED_SYNTHETIC_CHAIN_MATH_ONLY" and result.get("checks") == 4012 and result.get("failures") is Array and result.failures.is_empty()
\tvar file := FileAccess.open(path,FileAccess.WRITE)
\tif file == null: push_error("Cannot write chain math result"); quit(2); return
\tfile.store_string(JSON.stringify(result,"",true,true)); file.close()
\tprint("CHAIN_MATH "+JSON.stringify({"checks":result.get("checks",0),"passed":passed}))
\tquit(0 if passed else 1)
'''


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def save(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def pin(path):
    return {'path': str(path), 'sha256': sha(path)}


def functional_snapshot():
    paths = []
    for name in ('src', 'tests', 'tools', 'data', 'examples'):
        paths += [p for p in (ROOT / name).rglob('*') if p.is_file() and p.suffix != '.pyc' and '__pycache__' not in p.parts]
    paths += [ROOT / p for p in ('launch.pyw', 'main.tscn', 'project.godot', 'run.py')]
    require(all(not p.is_symlink() for p in paths), 'Functional source must not contain symlinks')
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(paths)}


def verify_packet():
    require(sha(PACKET / 'INDEX.json') == PACKET_SHA, 'Frozen chain index changed')
    for row in json.loads((PACKET / 'INDEX.json').read_bytes())['files']:
        relative = Path(row['path'])
        require(not relative.is_absolute() and '..' not in relative.parts, 'Invalid packet path')
        path = PACKET / relative
        require(not path.is_symlink() and path.stat().st_size == row['bytes'] and sha(path) == row['sha256'], 'Frozen packet source changed')
    require(sha(PACKET / 'COUNT_AUDIT_20261115.json') == COUNT_SHA, 'Preregistered count audit changed')
    counts = json.loads((PACKET / 'COUNT_AUDIT_20261115.json').read_bytes())
    require(counts['math']['expected_checks'] == 4012 and counts['native']['expected_checks'] == 21087, 'Wrong preregistered counts')
    for source, _alias, expected in ALIASES.values():
        require(not source.is_symlink() and sha(source) == expected, 'Qualified or candidate alias changed')


def predecessor_proofs():
    values = {}
    for name, (relative, expected) in PROOFS.items():
        path = ROOT / relative
        require(sha(path) == expected, 'Predecessor proof changed: ' + name)
        values[name] = json.loads(path.read_bytes())
    full = values['full_receipt']
    require(full['source_commit'] == FULL_HEAD and full['status'] == 'passed' and full['suite_exit'] == 0 and full['source_unchanged'], 'Historical full suite not passed')
    full_dir = (ROOT / PROOFS['full_receipt'][0]).parent
    require((full_dir / 'source-before.json').read_bytes() == (full_dir / 'source-after.json').read_bytes(), 'Historical full catalogue changed')
    require(values['full_closure']['owned_runtime_command_matches_absent'] and values['full_closure']['no_process_killed'] and values['full_closure']['python_absent'] and values['full_closure']['coordinator_absent'], 'Historical full closure missing')
    for name, expected_checks in (('FK_receipt',41588),('math_receipt',8994),('leaf_receipt',7289)):
        item = values[name]
        require(item['passed'] and item['result']['checks'] == expected_checks and item['result']['failures'] == 0, 'Bounded predecessor failed: ' + name)
        require(all(p['retained_Popen_reaped'] and not p['timed_out'] and not p['error_markers'] for p in item['phases']), 'Predecessor child not cleanly reaped')
    for name in ('FK_closure','math_closure','leaf_closure'):
        require(values[name]['runtime_lease_released'] and values[name]['owned_runtime_commands_absent'] and values[name]['no_process_killed'], 'Bounded predecessor closure missing')
    state = values['state_receipt']
    require(state['passed'] and state['actual_result_valid'] and state['checks_observed'] == 180 and state['failures_observed'] == 0 and state['runtime_lease_released'], 'Current state180 proof failed')
    require(all(state['preservation'].values()) and all(p['retained_Popen_reaped'] and not p['timed_out'] and p['passed'] for p in state['phases']), 'Current state preservation/closure failed')
    require(values['state_closure']['owned_count'] == 0 and state['test_result_sha256'] == PROOFS['state_result'][1], 'Current state closure/result mismatch')
    result = values['state_result']
    require(result['checks'] == 180 and result['failures'] == 0 and result['complete_assertion_set'] and all(result['named_checks'].values()), 'Current actual state result failed')
    require(values['state_source']['source_HEAD'] == CURRENT_HEAD and result['source_manifest_sha256'] == PROOFS['state_source'][1], 'Current state source identity mismatch')
    for row in values['state_source']['files']:
        require(sha(ROOT / row['path']) == row['sha256'], 'Current source differs from actual state180 source: ' + row['path'])
    return values


def inventory(folder, label):
    # Read-only approved PowerShell/CIM. Do not terminate any discovered app.
    code = "$ErrorActionPreference='Stop'; $items=@(Get-CimInstance Win32_Process | Where-Object {$_.Name -match '^(Godot.*|blender|ffmpeg|ffprobe)\\.exe$' -and $_.CommandLine -like '*has-acceptance-session-20261111*'}); @{owned_count=$items.Count;observed_utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json -Compress"
    command = [str(PWSH), '-NoLogo', '-NoProfile', '-NonInteractive', '-Command', code]
    child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
    terminated = False
    killed = False
    try:
        out, err = child.communicate(timeout=30)
    except subprocess.TimeoutExpired:
        terminated = True
        child.terminate()
        try:
            out, err = child.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            killed = True
            child.kill()
            out, err = child.communicate(timeout=5)
    (folder / (label + '-inventory-stdout.log')).write_bytes(out)
    (folder / (label + '-inventory-stderr.log')).write_bytes(err)
    process = {'pid':child.pid,'exit':child.returncode,'retained_Popen_reaped':child.poll() is not None,'owned_inventory_terminated':terminated,'owned_inventory_killed':killed}
    save(folder / (label + '-inventory-process.json'), process)
    require(child.returncode == 0 and not terminated and not err.strip(), 'Fresh read-only inventory failed')
    value = json.loads(out)
    save(folder / (label + '-runtime-closure.json'), value)
    require(value['owned_count'] == 0, 'An owned runtime is still active; no app was closed')
    return value


def run_phase(folder, project, label, entry, options, arguments, timeout):
    log = folder / (label + '-engine.log')
    command = [str(ENGINE),'--headless','--path',str(project),'--audio-driver','Dummy','--log-file',str(log),'--script','res://'+entry,*options,'--',*map(str,arguments)]
    save(folder / (label + '-command.json'), command)
    child = subprocess.Popen(command,cwd=project,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
    save(folder / (label + '-owned-start.json'), {'pid':child.pid,'command':command,'retained_Popen':True,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    started = time.monotonic()
    timed_out = False
    interrupted = False
    killed = False
    try:
        out,err = child.communicate(timeout=timeout)
    except (subprocess.TimeoutExpired, KeyboardInterrupt) as error:
        timed_out = isinstance(error,subprocess.TimeoutExpired)
        interrupted = isinstance(error,KeyboardInterrupt)
        child.terminate()  # Only the child whose retained Popen was created here.
        try:
            out,err = child.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            killed = True
            child.kill()
            out,err = child.communicate(timeout=5)
    (folder / (label + '-stdout.log')).write_bytes(out)
    (folder / (label + '-stderr.log')).write_bytes(err)
    texts = [out.decode('utf-8',errors='replace'),err.decode('utf-8',errors='replace'),log.read_text(encoding='utf-8',errors='replace') if log.exists() else '']
    markers = [line for text in texts for line in text.splitlines() if any(marker in line for marker in BAD)]
    row = {'phase':label,'pid':child.pid,'exit':child.returncode,'retained_Popen_reaped':child.poll() is not None,'timed_out':timed_out,'interrupted':interrupted,
           'owned_child_terminated':timed_out or interrupted,'owned_child_forced_kill':killed,'seconds':time.monotonic()-started,'error_markers':markers,
           'passed':child.returncode == 0 and not timed_out and not interrupted and not markers}
    save(folder / (label + '-process.json'),row)
    return row


def math_valid(result, lease_path):
    return (isinstance(result,dict) and result.get('status') == 'PASSED_SYNTHETIC_CHAIN_MATH_ONLY' and result.get('checks') == 4012
            and result.get('failures') == [] and result.get('root_lease_sha256') == sha(lease_path)
            and result.get('SDK_executed') is False and result.get('actual_native_chains_exercised') is False and result.get('float32_Model_boundary_exercised') is False)


def native_valid(result):
    if not (isinstance(result,dict) and result.get('status') == 'PASSED_NATIVE_TWO_PAIR_READINESS_ONLY' and result.get('checks') == 21087 and result.get('failures') == 0
            and result.get('failure_labels') == [] and result.get('dynamic_ticks') == 1440 and result.get('rule_evaluations') == 5760 and len(result.get('cases',[])) == 12):
        return False
    rows = result['cases']
    names = sorted(['control','positive3','negative3','positive12','positive50','repeat12']*2)
    return (sorted(row['profile'] for row in rows) == names
            and all(row['ticks'] == 120 and row['vertices'] == 9661 and row['weighted_to_selected'] == 542 and row['shared_with_other_bones'] == 340 and row['unaffected_vertices'] == 9119
                    and row['unaffected_exact'] and row['Off_all_weighted_points_exact'] and row['basis_error_max'] <= 2e-5
                    and row['origin_error_max'] <= 2e-5*row['root_size'] and row['tip_error_max'] <= 2e-5*row['root_size'] for row in rows))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempt',type=int,required=True,choices=range(1,6))
    parser.add_argument('--acknowledge-historical-full',action='store_true')
    args = parser.parse_args()
    require(args.acknowledge_historical_full, 'Explicit historical-full scope acknowledgment required')
    require(sha(ENGINE) == ENGINE_SHA and sha(PWSH) == PWSH_SHA, 'Approved runtime bytes changed')
    ast.parse(SELF.read_text(encoding='utf-8-sig'))
    verify_packet()
    evidence = predecessor_proofs()
    current_head = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    require(current_head == CURRENT_HEAD, 'Current checkout HEAD differs from state180 context')
    for source,expected in INPUTS.values(): require(not source.is_symlink() and sha(source) == expected, 'Protected input changed')
    frozen_source = functional_snapshot()
    driver_sha = sha(SELF)
    folder = ROOT / ('output/source-0x31-native-chains-20261115-attempt'+str(args.attempt))
    require(not folder.exists(), 'Preserve prior attempt; use a new attempt number')
    folder.mkdir()
    if args.attempt > 1:
        previous = ROOT / ('output/source-0x31-native-chains-20261115-attempt'+str(args.attempt-1)) / 'authoritative-closure.json'
        prior = json.loads(previous.read_bytes())
        require(prior['runtime_lease_released'] and prior['owned_runtime_commands_absent'] and prior['all_retained_children_reaped'], 'Previous attempt is not closed')
    phases = []
    error_message = None
    math_result = None
    native_result = None
    math_passed = False
    native_passed = False
    preservation = {}
    after = None
    lease = None
    math_lease = None
    project = folder / 'Studio'
    aliases = {}
    staged_rows = []
    try:
        before = inventory(folder,'before')
        project.mkdir()
        app_paths = sorted(p for p in (ROOT/'src').rglob('*') if p.is_file() and p.suffix != '.pyc' and '__pycache__' not in p.parts)
        app_paths += sorted(p for p in (ROOT/'data').rglob('*') if p.is_file() and p.suffix != '.pyc' and '__pycache__' not in p.parts)
        app_paths += [ROOT/'project.godot',ROOT/'main.tscn']
        for source in app_paths:
            relative = source.relative_to(ROOT)
            require(not source.is_symlink(), 'Application symlink refused')
            target = project/relative
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(source.read_bytes())
            staged_rows.append({'path':relative.as_posix(),'bytes':source.stat().st_size,'sha256':sha(source)})
        source_lock = folder/'CURRENT-SOURCE-LOCK.json'
        save(source_lock,{'format':'has_current_native_chain_source_lock_1','HEAD_context':current_head,'files':staged_rows})
        save(folder/'FROZEN-FUNCTIONAL-SOURCE.json',{'HEAD_context':current_head,'source_sha256':frozen_source})
        historical = evidence['full_catalogue']['source_sha256']
        changed = [{'path':p,'historical_full_sha256':historical[p],'current_sha256':frozen_source[p]} for p in sorted(historical.keys()&frozen_source.keys()) if historical[p] != frozen_source[p]]
        drift = {'format':'has_historical_full_scope_acknowledgment_1','root_acknowledged':True,'historical_full_revision':FULL_HEAD,'historical_full_receipt_sha256':PROOFS['full_receipt'][1],
                 'current_HEAD_context':current_head,'current_snapshot_is_historical_full_snapshot':frozen_source == historical,'current_full_product_suite_claimed':False,
                 'current_state180_receipt_sha256':PROOFS['state_receipt'][1],'current_state_source_sha256':PROOFS['state_source'][1],
                 'scope':'Historical full/FK/single-rule math/native8 leaf are predecessors only. Current source is separately frozen and state180-qualified. New chain probes are experimental, not current full-product acceptance.',
                 'changed':changed,'added':sorted(frozen_source.keys()-historical.keys()),'removed':sorted(historical.keys()-frozen_source.keys()),
                 'old_packet_source_lock_preserved':pin(PACKET/'SOURCE_LOCK.json')}
        save(folder/'PROVENANCE-DRIFT-ACKNOWLEDGMENT.json',drift)
        for name,(source,alias,expected) in ALIASES.items():
            target = project/alias
            target.write_bytes(source.read_bytes())
            require(sha(target) == expected, 'Staged alias differs')
            aliases[name] = {'source':str(source),'path':str(target),'sha256':expected}
        entry = project/'chain_math_entry.gd'
        entry.write_text(MATH_ENTRY,encoding='utf-8',newline='\n')
        aliases['math_entry'] = {'path':str(entry),'sha256':sha(entry),'generated_by_driver_sha256':driver_sha}
        inputs = folder/'read-only-inputs'; inputs.mkdir()
        for name in ('glb','parameters'):
            source,expected = INPUTS[name]
            target = inputs/source.name
            target.write_bytes(source.read_bytes())
            require(sha(target) == expected,'Staged private input differs')
        common = {name:pin(ROOT/relative) for name,(relative,_expected) in PROOFS.items()}
        common.update({'source_lock':pin(source_lock),'driver':pin(SELF),'frozen_functional_source':pin(folder/'FROZEN-FUNCTIONAL-SOURCE.json'),
                       'scope_acknowledgment':pin(folder/'PROVENANCE-DRIFT-ACKNOWLEDGMENT.json'),'packet_index':pin(PACKET/'INDEX.json'),'count_audit':pin(PACKET/'COUNT_AUDIT_20261115.json')})
        for name,row in aliases.items(): common[name] = {'path':row['path'],'sha256':row['sha256']}
        for name,(source,expected) in INPUTS.items(): common[name] = {'path':str(inputs/source.name) if name in ('glb','parameters') else str(source),'sha256':expected}
        save(folder/'COPY-PROVENANCE.json',{'driver':pin(SELF),'packet_index_sha256':PACKET_SHA,'application_files':len(staged_rows),'aliases':aliases,'read_only_original_inputs':{k:pin(p) for k,(p,_h) in INPUTS.items()},'original_source_lock_unchanged':pin(PACKET/'SOURCE_LOCK.json')})

        def preserved():
            return {'functional_source':functional_snapshot() == frozen_source,
                    'staged_application':all(sha(project/row['path']) == sha(ROOT/row['path']) == row['sha256'] for row in staged_rows),
                    'original_inputs':all(sha(p) == h for p,h in INPUTS.values()),
                    'staged_inputs':all(sha(inputs/INPUTS[name][0].name) == INPUTS[name][1] for name in ('glb','parameters')),
                    'aliases':all(sha(Path(row['path'])) == row['sha256'] and ('source' not in row or sha(Path(row['source'])) == row['sha256']) for row in aliases.values()),
                    'proofs_and_locks':all(sha(Path(row['path'])) == row['sha256'] for row in common.values()),
                    'runtimes':sha(ENGINE) == ENGINE_SHA and sha(PWSH) == PWSH_SHA,'driver':sha(SELF) == driver_sha,'frozen_packet_index':sha(PACKET/'INDEX.json') == PACKET_SHA}

        math_target = folder/'math-result.json'
        math_lease = {'format':'has_root_chain_math_lease_1','phase':'ROOT_APPROVED_CHAIN_SYNTHETIC_MATH','root_closed_all':before['owned_count'] == 0,'expires_unix':time.time()+600,
                      'engine_sha256':ENGINE_SHA,'files':common,'public_result':str(math_target),'preregistered_checks':4012}
        math_lease_path = folder/'ROOT-MATH-LEASE.json'; save(math_lease_path,math_lease)
        for label,options,timeout in [('math-parse',['--check-only'],30),('math-run',[],90)]:
            require(all(preserved().values()),'Preservation failed before math phase')
            inventory(folder,label+'-before')
            phase = run_phase(folder,project,label,'chain_math_entry.gd',options,[math_lease_path],timeout)
            phases.append(phase)
            inventory(folder,label+'-after')
            if not phase['passed']: break
        math_result = json.loads(math_target.read_bytes()) if math_target.exists() else None
        math_passed = len(phases) == 2 and all(p['passed'] for p in phases) and math_valid(math_result,math_lease_path) and all(preserved().values())
        math_verification = {'format':'has_chain_synthetic_math_execution_1','passed':bool(math_passed),'checks_expected':4012,'checks_observed':math_result.get('checks',0) if math_result else 0,
                             'phases':phases.copy(),'result':math_result,'preservation':preserved(),'actual_native_geometry_loaded':False,'source_HEAD_context':current_head}
        save(folder/'math-verification.json',math_verification)
        # Never construct or launch a native phase until actual math PASS and
        # both retained children have been independently observed absent.
        if math_passed:
            closed_math = inventory(folder,'post-math')
            lease = json.loads((PACKET/'ROOT_LEASE_READY_TEMPLATE.json').read_bytes())
            lease['files'] = dict(common)
            lease['files'].update({'chain_math_receipt':pin(folder/'math-verification.json'),'chain_math_closure':pin(folder/'post-math-runtime-closure.json'),
                                  'root_closure':pin(ROOT/PROOFS['state_closure'][0])})
            lease.update(phase='ROOT_APPROVED_AFTER_FULL_FK_MATH_LEAF_AND_CLOSURE',full_status='PASS',FK_status='PASS',math_status='PASS',leaf_status='PASS',chain_math_status='PASS',state_status='PASS',
                         root_closed_all=closed_math['owned_count'] == 0,expires_unix=time.time()+600,engine_sha256=ENGINE_SHA,public_result=str(folder/'result.json'))
            lease_path = folder/'ROOT-NATIVE-LEASE.json'; save(lease_path,lease)
            for label,options,timeout in [('native-parse',['--check-only'],30),('native-run',[],120)]:
                require(all(preserved().values()) and all(sha(Path(p['path'])) == p['sha256'] for p in lease['files'].values()),'Preservation failed before native phase')
                inventory(folder,label+'-before')
                phase = run_phase(folder,project,label,'chain_harness.gd',options,[lease_path,folder/'result.json'],timeout)
                phases.append(phase)
                inventory(folder,label+'-after')
                if not phase['passed']: break
            native_result = json.loads((folder/'result.json').read_bytes()) if (folder/'result.json').exists() else None
            native_passed = len(phases) == 4 and all(p['passed'] for p in phases) and native_valid(native_result)
        preservation = preserved()
    except Exception as error:
        error_message = str(error)
        save(folder/'driver-failure.json',{'error_type':type(error).__name__,'error':error_message,'engine_phases_completed':len(phases)})
    finally:
        try:
            after = inventory(folder,'after')
        except Exception as error:
            if error_message is None: error_message = str(error)
        no_kill = all(not p['owned_child_terminated'] and not p['owned_child_forced_kill'] for p in phases)
        all_reaped = all(p['retained_Popen_reaped'] for p in phases)
        released = after is not None and after['owned_count'] == 0 and all_reaped
        passed = bool(math_passed and native_passed and len(phases) == 4 and all(preservation.values()) and preservation and error_message is None and released and no_kill)
        verification = {'format':'has_root_two_chain_execution_1','passed':passed,'historical_full_revision':FULL_HEAD,'current_source_HEAD_context':current_head,'current_full_product_qualified':False,
                        'driver_sha256':driver_sha,'packet_index_sha256':PACKET_SHA,'phases':phases,'math_passed':bool(math_passed),'native_passed':bool(native_passed),
                        'math_result':math_result,'result':native_result,'preservation':preservation,'error':error_message,'runtime_lease_released':released,
                        'preregistered_expected':{'math_checks':4012,'native_checks':21087,'native_rows':12,'native_ticks':1440,'native_rule_evaluations':5760},
                        'scope':'Experimental chain orchestration only; no full49-rule/SDK-client/artist/GPU/body/fan/Record/HAS qualification',
                        'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
        save(folder/'verification.json',verification)
        closure = {'format':'has_root_two_chain_closure_1','validation_passed':passed,'all_retained_children_reaped':all_reaped,'owned_runtime_commands_absent':bool(after is not None and after['owned_count'] == 0),
                   'runtime_lease_released':released,'no_process_killed':no_kill,'verification_sha256':sha(folder/'verification.json'),'source_preservation_established':bool(preservation and all(preservation.values())),
                   'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
        save(folder/'authoritative-closure.json',closure)
    print(json.dumps({'folder':str(folder),'passed':passed,'math_checks':math_result.get('checks',0) if math_result else 0,'native_checks':native_result.get('checks',0) if native_result else 0,'error':error_message,'closed':released}))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
