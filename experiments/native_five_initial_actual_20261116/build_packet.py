"""Freeze explicit safe scalar metadata; no native asset, engine or Git access."""
from pathlib import Path
import datetime
import gzip
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BASE = ROOT / 'output/native-five-stage-attempt1'
STRICT = ROOT / 'output/native-five-stage-attempt2'
STATE1 = BASE / 'Studio/output/source-native-five-state-20261116T032753090430'
GUI = BASE / 'Studio/output/native-five-gui-attempt1'
STATE2 = STRICT / 'Studio/output/source-native-five-state-20261116T034910930092'
DIAG = STRICT / 'Studio/output/opposite-diagnostic-attempt1'
ALIASES = []

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def load(path):
    return json.loads(path.read_bytes())

def write(name, value):
    with (HERE/name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2); stream.write('\n')

def privacy(value, path=''):
    if isinstance(value, dict):
        for key, child in value.items():
            privacy(child, path+'/'+key)
    elif isinstance(value, list):
        if any(isinstance(x, (int, float)) and not isinstance(x, bool) for x in value):
            permitted = {'/scope/native_rule_indices_selected':[8,17,18,26,27],
                         '/UI_driver_binding/proposed_writer_packed_linked_checks':[82,11,8]}
            assert path in permitted and value == permitted[path], path
        for child in value:
            privacy(child, path+'/*')

def copy(source, stored, compressed=False):
    assert source.is_file() and source.suffix in ('.json', '.log')
    raw = source.read_bytes()
    if source.suffix == '.json':
        privacy(json.loads(raw))
    target = HERE/stored
    assert target.is_relative_to(HERE) and '..' not in Path(stored).parts
    target.parent.mkdir(parents=True, exist_ok=True)
    content = gzip.compress(raw, mtime=0) if compressed else raw
    if target.exists():
        assert target.read_bytes() == content, 'Existing partial copy differs: '+stored
    else:
        with target.open('xb') as stream:
            stream.write(content)
    ALIASES.append({'source': source.relative_to(ROOT).as_posix(), 'stored': stored,
                    'raw_bytes': len(raw), 'raw_sha256': sha(raw),
                    'encoding': 'gzip_mtime0' if compressed else 'identity'})

def state(folder, label):
    v, r = load(folder/'verification.json'), load(folder/'result.json')
    assert v['passed'] and v['actual_result_valid'] and v['runtime_lease_released']
    assert v['checks_observed'] == r['checks'] == len(r['named_checks']) == 266
    assert v['failures_observed'] == r['failures'] == 0 and all(r['named_checks'].values())
    assert r['complete_assertion_set'] and r['metrics']['completed_native_steps'] == 886
    assert r['job_sha256'] == sha((folder/'job.json').read_bytes())
    assert r['source_manifest_sha256'] == sha((folder/'SOURCE.json').read_bytes())
    assert v['test_result_sha256'] == sha((folder/'result.json').read_bytes())
    assert all(v['preservation'].values())
    for phase in v['phases']:
        assert phase['exit'] == 0 and phase['retained_Popen_reaped']
        assert not phase['timed_out'] and not phase['owned_child_terminated']
        assert not phase['owned_child_forced_kill'] and not phase['error_markers']
    for when in ('before', 'after'):
        assert load(folder/(when+'-runtime-closure.json'))['owned_count'] == 0
    for p in sorted(folder.iterdir()):
        if p.is_file() and p.suffix in ('.json', '.log'):
            copy(p, label+'/'+p.name+('.gz' if p.name == 'SOURCE.json' else ''), p.name == 'SOURCE.json')
    return {'checks': 266, 'failures': 0, 'passed': True, 'completed_native_steps': 886,
            'result_sha256': sha((folder/'result.json').read_bytes()),
            'private_GPU_UI': False, 'runtime_lease_released': True}

def main():
    first = state(STATE1, 'initial-state')
    second = state(STATE2, 'strict-state')
    gv, gr, gc = load(GUI/'verification.json'), load(GUI/'writer/result.json'), load(GUI/'authoritative-closure.json')
    assert gv['passed'] is False and gr['checks'] == len(gr['named_checks']) == 82
    assert gr['failures'] == 1 and [k for k,v in gr['named_checks'].items() if not v] == ['fan.opposite_tip_directions']
    assert gv['checks_expected'] == 101 and gv['checks_observed'] == 82 and len(gv['results']) == 1
    assert gc['runtime_lease_released'] and gc['private_job_closed'] and gc['private_desktop_closed']
    assert gc['writer_exit'] == 1 and gc['retained_Popen_reaped'] and gc['owned_runtime_commands_absent']
    assert all(gv['preservation'].values()) and not (GUI/'reader-packed').exists() and not (GUI/'reader-linked').exists()
    receipt = load(GUI/'writer/private-receipt.json')
    assert receipt['exit'] == 1 and receipt['job_closed'] and receipt['desktop_closed']
    assert receipt['child_desktop_confirmed'] and not receipt['foreground_child_observed']
    for name in ('verification.json', 'authoritative-closure.json', 'source-before.json', 'source-after.json',
                 'writer/result.json', 'writer/job.json', 'writer/private-receipt.json',
                 'writer/process-verification.json', 'writer/command.json', 'writer/stdout.log',
                 'writer/stderr.log', 'writer/engine.log'):
        compressed = name.startswith('source-')
        copy(GUI/name, 'failed-GUI/'+name+('.gz' if compressed else ''), compressed)
    dv, dr, ds = load(DIAG/'verification.json'), load(DIAG/'result.json'), load(DIAG/'opposite-diagnostic.json')
    assert dv['diagnostic_completed'] and not dv['qualification_pass_claimed'] and not dv['main_promoted']
    assert dr['checks'] == len(dr['named_checks']) == dv['checks'] == 57
    assert dv['retained_gate_failures'] == dr['failures'] == 2
    failed = [k for k,v in dr['named_checks'].items() if not v]
    assert failed == ['fan.opposite_tip_directions', 'fan.original_native8_opposite_tip_directions']
    assert dv['process']['exit'] == 1 and dv['process']['retained_Popen_reaped'] and not dv['process']['timed_out']
    assert dv['private_job_desktop_closed'] and dv['source_preserved'] and dv['runtime_lease_released']
    assert dv['result_sha256'] == sha((DIAG/'result.json').read_bytes())
    assert dv['scalar_report_sha256'] == sha((DIAG/'opposite-diagnostic.json').read_bytes())
    assert dr['job_sha256'] == sha((DIAG/'job.json').read_bytes())
    assert dr['source_manifest_sha256'] == sha((DIAG/'SOURCE.json').read_bytes())
    assert ds['native']['8']['original_native8_gate'] is False
    assert ds['native']['8']['world_delta_dot'] > 0
    assert all(ds['native'][str(i)]['world_delta_dot'] < 0 for i in (17,18,26,27))
    for p in sorted(DIAG.iterdir()):
        if p.is_file() and p.suffix in ('.json', '.log'):
            copy(p, 'strict-diagnostic/'+p.name+('.gz' if p.name == 'SOURCE.json' else ''), p.name == 'SOURCE.json')
    for source, target in [(BASE/'STAGE-MANIFEST.json','stage-initial.json'),
                            (BASE/'ROOT-PRESERVATION-initial-runs.json','root-preservation-initial.json'),
                            (STRICT/'STAGE-MANIFEST.json','stage-strict-base.json'),
                            (STRICT/'STRICT-OVERLAY.json','strict-overlay.json')]:
        copy(source, 'provenance/'+target+'.gz', True)
    upstream = {}
    for rel, pin in {
        'experiments/runtime_snapshot_repair_actual_20261115/INDEX.json':'bb96fd44d526409bd9ed06e535ae94f5f8b76c106be43e543b0837b8bad06cf4',
        'experiments/source_native_five_port_candidate_v2_20261115/INDEX.json':'460b7719c1bab426aebcc1d04d97bf0d6932b0a6bcadb75db9000147fef6c657',
        'experiments/native_five_performance_candidate_20261115/INDEX.json':'80203837bd647fbad157d9ea7b1ee8e0c82014bbaa1329b0c5f2fac7e95bb441',
        'experiments/source_native_five_opposite_diagnostic_20261116/INDEX.json':'50df7f894b04633568679ab9252727597e7f76d5abff83d52d646602e63bd3f5',
    }.items():
        assert sha((ROOT/rel).read_bytes()) == pin
        upstream[rel] = pin
    for name in ('native_five_initial_2026-11-15.json', 'world_selection_runtime_snapshot_2026-11-15.json',
                 'windows_native_leaf_full_timeout_2026-11-15.json'):
        copy(ROOT/'docs/benchmarks'/name, 'prior-benchmarks/'+name)
    write('BENCHMARK.json', {'format':'has_native_five_initial_actual_1',
        'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'production_backend':'NATIVE8_ONLY_NOT_PROMOTED', 'manual_hair_check':'OWNER_BUSY_DEFERRED_NO_RESULT',
        'complete_default':'DBF0BC1_FAILED_180S_TEARDOWN_TIMEOUT_FRESH_COMPLETE_REQUIRED',
        'snapshot_repair':{'CPU':27,'actual_UI':28,'failures':0,'scope':'SCOPED_ONLY_NOT_FULL'},
        'initial_state':first, 'initial_GUI':{'passed':False,'checks':82,'failures':1,
           'failed_names':['fan.opposite_tip_directions'],'readers':'UNRUN_AFTER_WRITER_FAILURE',
           'runtime_lease_released':True},
        'strict_state':second, 'strict_diagnostic':{'completed':True,'qualification_pass':False,
           'checks':57,'failures':2,'failed_names':failed,'only_native8_world_delta_dot_positive':True,
           'runtime_lease_released':True},
        'performance':{'scope':'Successful Native.step only; no120Hz or displayed FPS pass',
           'strict_diagnostic_mean_ms_by_profile':{k:v['native_step_processing']['mean_usec']/1000 for k,v in dr['metrics'].items() if isinstance(v,dict) and 'native_step_processing' in v},
           'fixed_clock_budget_ms':1000/120},
        'upstream_packet_indices':upstream, 'private_arrays_serialized':False,
        'formal_acceptance':'55/62_UNCHANGED','implementation':'52/54_UNCHANGED',
        'next':'Independently correct controlled fan fixture/invariant; retain failures; actual GUI cold/export qualification and fresh complete default before product promotion claims.'})
    write('SOURCE_MANIFEST.json', {'format':'has_native_five_initial_actual_sources_1','copies':ALIASES})
    entries=[]
    for p in sorted(HERE.rglob('*')):
        if p.is_file() and p.name != 'INDEX.json':
            raw=p.read_bytes();entries.append({'path':p.relative_to(HERE).as_posix(),'bytes':len(raw),'sha256':sha(raw)})
    write('INDEX.json', {'format':'has_native_five_initial_actual_index_1','files':entries,
                        'file_count':len(entries),'total_bytes':sum(x['bytes'] for x in entries)})
    print(json.dumps({'files':len(entries),'bytes':sum(x['bytes'] for x in entries),'index_sha256':sha((HERE/'INDEX.json').read_bytes())}))

if __name__ == '__main__':
    main()
