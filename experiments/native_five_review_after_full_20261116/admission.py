"""Source-only prepared admission gates; no build, runtime or process queries."""
from pathlib import Path
import hashlib
import json
import stat

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
NATIVE=ROOT/'output/sfm-bone-bindings-native-launch-20261114T033026205/run'
REVISION='52f63c944ded7a651da871524d23a345b606424d'
FULL=ROOT/'output/windows-canonical-bone-binding-20261116T041518335'
FULL_SOURCE_SHA='4b1eb25e1da8e510106fe3dd01c4b5014c7cc719133f18e1bbccd386ec9deae7'
NATIVE_SHA='10ee4a984c9e54b1acf37d79d5013a10780abe98416b8350f3edf3ee37277c4b'
TEXT={'.py','.pyw','.gd','.gdshader','.tscn','.tres','.json','.godot','.cfg','.uid','.txt','.md','.svg'}
TEXT_PATHS={'tests/blank','tests/krita_fixture/has_fixture.desktop','tools/docker/sourceio_metadata.Dockerfile',
            'tools/docker/sourceio_worker.Dockerfile','tools/krita-runtime.Dockerfile'}

def need(value,message):
    if not value:raise RuntimeError(message)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_bytes())
def no_links(path):
    for p in (path,*path.parents):
        try:s=p.lstat()
        except FileNotFoundError:continue
        need(not stat.S_ISLNK(s.st_mode) and not getattr(s,'st_file_attributes',0)&0x400,'Link/reparse metadata refused')
def functional(name):
    return (name.split('/')[0] in ('src','tests','tools','data','examples') or name in ('project.godot','main.tscn','run.py','launch.pyw')) and '__pycache__' not in Path(name).parts and not name.endswith('.pyc')
def canonical(raw,name):return raw.replace(b'\r\n',b'\n') if Path(name).suffix in TEXT or name in TEXT_PATHS else raw

def require_full_release(identity):
    """Read actual current terminal artifacts only; never infer or write them."""
    state=load(FULL/'state.json')
    need(state.get('status')=='passed' and state.get('suite_exit')==0 and state.get('source_unchanged') is True and state.get('source_commit')==REVISION,'Current52f complete PASS required before any review write/launch')
    need(state.get('pid')==79488 and state.get('process_started')=='2026-11-16T04:15:18.3655401Z','Actual current coordinator identity differs')
    host_path=FULL/'authoritative-host-termination.json';raw_path=FULL/'authoritative-host-terminal.json'
    host=load(host_path);raw=load(raw_path);release_path=FULL/'graphics-lease-released.json';release=load(release_path)
    need(host.get('source_commit')==REVISION and host.get('canonical_run')==FULL.name and host.get('coordinator_pid')==79488 and host.get('python_pid')==91024 and host.get('raw_observation_sha256')==sha(raw_path),'Actual current authoritative host proof differs')
    need(host.get('expected_creation_utc')=='2026-11-16T04:15:18.3655401Z' and host.get('expected_python_creation_utc')=='2026-11-16T04:15:18.9615298Z' and host.get('functional_source_entries')==1019,'Actual current host source/birth scope differs')
    need(all(host.get(k) is True for k in ('coordinator_absent','python_absent','owned_runtime_command_matches_absent','source_before_after_and_current_exact','root_observer_issued_no_termination')) and host.get('coordinator_matches')==[] and host.get('owned_runtime_matches')==[],'Current root-owned host absence is not closed')
    need(raw.get('source_commit')==REVISION and raw.get('canonical_run')==str(FULL) and raw.get('state_status')=='passed' and raw.get('suite_exit')==0 and raw.get('root_birth_observation_sha256')=='ce9b8c1197b02b3d575083635419b7309160ea70ab08896d819f5d112c2da6df','Actual raw host/current birth binding differs')
    need(release.get('format')=='has_root_canonical_graphics_lease_release_1' and release.get('released') is True and release.get('source_commit')==REVISION and release.get('canonical_run')==FULL.name and release.get('coordinator_pid')==79488 and release.get('python_pid')==91024,'Actual current full graphics release required')
    need(all(release.get(k) is True for k in ('all_private_jobs_closed','owned_runtime_command_matches_absent','normalized_log_report_suffix_equal','root_observer_issued_no_termination')) and release.get('functional_source_entries')==1019,'Current release closure/source scope differs')
    need(release.get('canonical_state_sha256')==sha(FULL/'state.json') and release.get('host_proof_sha256')==sha(host_path) and release.get('full_report_sha256')==sha(ROOT/'output/verification.json'),'Current release report/state/host byte binding differs')
    need(type(release.get('private_jobs')) is int and release['private_jobs']>0 and release.get('normal_exit_0',-1)+release.get('expected_Krita_cancellation_exit_2',-1)==release['private_jobs'],'Actual release receipt totals differ; no historical total admitted')
    need(sha(FULL/'source-before.json')==sha(FULL/'source-after.json')==FULL_SOURCE_SHA,'Exact current1019 full source bytes differ')
    for path in (FULL/'launch.json',FULL/'root-birth-observation.json',host_path,raw_path,release_path):no_links(path)
    return {str(p):identity(p) for p in (FULL/'state.json',host_path,raw_path,FULL/'source-before.json',FULL/'source-after.json',FULL/'launch.json',FULL/'root-birth-observation.json',release_path,ROOT/'output/verification.json')}

def admit_source_delta(native,final_root,final_members):
    """Old native result is DATA; current runtime admits only an explicit delta."""
    need(sha(NATIVE/'verification.json')==NATIVE_SHA and native.get('passed') is True,'Pinned earlier four-case DATA result required')
    delta=load(HERE/'source-delta.json');source=load(FULL/'source-before.json')
    need(sha(FULL/'source-before.json')==FULL_SOURCE_SHA and source.get('commit')==REVISION and len(source['source_sha256'])==1019,'Current source delta target differs')
    new=source['source_sha256'];old={n:r for n,r in native['source_before']['files'].items() if functional(n)}
    need(len(old)==1008 and set(new)==set(n for n in final_members if functional(n)),'Explicit old/current functional inventories differ')
    rows={r['path']:r for r in delta['changed_or_added']};observed=set();unchanged=[]
    for name,expected in new.items():
        current=ROOT/name;final=final_root/name;no_links(current);no_links(final)
        b=current.read_bytes();need(hashlib.sha256(b).hexdigest()==expected,'Current admitted source changed: '+name)
        need(canonical(final.read_bytes(),name)==canonical(b,name),'Final exact source content differs: '+name)
        a=None
        if name in old:
            original=NATIVE/'Studio'/name;no_links(original);a=original.read_bytes()
            need(hashlib.sha256(a).hexdigest()==old[name]['sha256'],'Retained original native source changed: '+name)
        if a is not None and canonical(a,name)==canonical(b,name):
            need(name not in rows,'Delta falsely declares an unchanged file');unchanged.append(name);continue
        observed.add(name);need(name in rows,'Unreviewed native/current source delta: '+name)
        row=rows[name]
        need(row['new_working_sha256']==expected and row['new_content_sha256']==hashlib.sha256(canonical(b,name)).hexdigest(),'Explicit current delta bytes differ: '+name)
        need(row['old_native_sha256']==(old[name]['sha256'] if name in old else None) and row['old_content_sha256']==(hashlib.sha256(canonical(a,name)).hexdigest() if a is not None else None),'Explicit old delta bytes differ: '+name)
    need(set(old)<=set(new) and observed==set(rows) and len(observed)==20,'Unexpected removal/addition/change outside exact20-file delta')
    for name in delta['unchanged_core']:
        need(name in unchanged and old[name]['sha256']==new[name],'Model/Bindings/SceneIO core is not exact unchanged')
    # Earlier actual266/102 stage is evidence of runtime code, not new execution.
    qualified=ROOT/'experiments/native_five_qualified_actual_20261116'
    need(sha(qualified/'INDEX.json')=='429ea76d462a385cfa2d292ed9c2c12dd9fbf9e52193f63bfb0e7776324dd655','Isolated native5 qualification packet changed')
    qrows={r['path']:r for r in load(qualified/'INDEX.json')['files']}
    for name in ('BENCHMARK.json','source/src/source_secondary.gd','source/src/secondary_live.gd','source/src/source_chain_math.gd'):
        p=qualified/name;no_links(p);need(sha(p)==qrows[name]['sha256'] and p.stat().st_size==qrows[name]['bytes'],'Qualified native5 metadata/source alias changed')
    q=load(qualified/'BENCHMARK.json');need(q['state']['passed'] is True and q['state']['checks']==266 and q['state']['failures']==0 and q['GUI']['passed'] is True and q['GUI']['checks']==102 and q['GUI']['failures']==0 and q['runtime_lease_released'] is True,'Exact earlier isolated native5 result scope differs')
    def code(p):return '\n'.join(s for s in p.read_text(encoding='utf-8').splitlines() if s.strip() and not s.lstrip().startswith('#'))
    for name in ('src/source_secondary.gd','src/secondary_live.gd','src/source_chain_math.gd'):
        need(code(ROOT/name)==code(qualified/'source'/name),'Current native5 runtime differs beyond qualified source headers')
    return {'format':'has_explicit_native_DATA_current_runtime_delta_1','old_native_functional_files':1008,'current_functional_files':1019,'unchanged_content_files':len(unchanged),'explicit_changed_or_added_files':sorted(observed),'unchanged_core':delta['unchanged_core'],'source_delta_sha256':sha(HERE/'source-delta.json'),'native_verification_sha256':NATIVE_SHA,'current_full_source_sha256':FULL_SOURCE_SHA,'native5_prior_state_GUI_checks':[266,102],'native_conversion_performed':False,'final_current_four_example_replay':'REQUIRED_SEPARATE_EXECUTION'}
