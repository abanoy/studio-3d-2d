"""Independent artifact-only verifier; no builders, original outputs or engines."""
from pathlib import Path,PureWindowsPath
import gzip
import hashlib
import io
import json
import re

HERE=Path(__file__).resolve().parent
PACKET=HERE.parent/'neon_helper375_actual_packet_20261117'
INPUTS_SHA='f793f505db95097a27e2f9dac845e5bec6d012b7a4ae4610140ad4f64e927af1'
def need(ok,message):
    if not ok:raise ValueError(message)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def parse(raw):
    def pairs(rows):
        out={}
        for k,v in rows:
            need(k not in out,'Duplicate JSON key');out[k]=v
        return out
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('Nonfinite JSON')))
def equal(a,b):
    if type(a) is not type(b):return False
    if type(a) is dict:return a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
    if type(a) is list:return len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
    return a==b
def verify(folder=PACKET):
    need(not folder.is_symlink() and not getattr(folder.lstat(),'st_file_attributes',0)&0x400,'Archive reparse refused')
    spec_raw=(HERE/'INPUTS.json').read_bytes();need(digest(spec_raw)==INPUTS_SHA,'Frozen input recipe changed');spec=parse(spec_raw)
    idx=parse((folder/'INDEX.json').read_bytes())
    need(idx['format']=='has_helper375_compact_exact_actual_packet_1' and idx['recipe_inputs_sha256']==digest(spec_raw),'Recipe/archive binding differs')
    for key,name in (('builder_sha256','build_packet.py'),('verifier_sha256','verify_packet.py'),('check_source_sha256','archive_checks.py')):
        need(idx[key]==digest((HERE/name).read_bytes()),'Recipe source pin differs')
    expected_inputs={(r['root'],r['path']):r for r in spec['inputs']}
    need(len(expected_inputs)==len(spec['inputs']) and len(expected_inputs)==idx['original_bindings'],'Original membership differs')
    decoded={};expected_files={'INDEX.json'}
    for row in idx['objects']:
        name=row['path'];need(re.fullmatch(r'objects/[a-f0-9]{64}\.gz',name) and name not in expected_files,'Unsafe/duplicate object')
        need(type(row['decoded_bytes']) is int and 0<=row['decoded_bytes']<=2*1024*1024,'Decoded bound differs')
        path=folder/name;need(not path.is_symlink() and not getattr(path.lstat(),'st_file_attributes',0)&0x400,'Object reparse refused')
        packed=path.read_bytes();need(len(packed)==row['bytes'] and digest(packed)==row['sha256'],'Compressed bytes differ')
        with gzip.GzipFile(fileobj=io.BytesIO(packed)) as stream:data=stream.read(row['decoded_bytes']+1)
        need(len(data)==row['decoded_bytes'] and digest(data)==row['decoded_sha256'] and name=='objects/'+digest(data)+'.gz','Decoded bytes differ')
        data.decode('utf-8-sig',errors='strict');need(digest(data) not in decoded,'Duplicate object digest');decoded[digest(data)]=data;expected_files.add(name)
    need(len(decoded)==idx['unique_decoded_objects'],'Object count differs')
    for row in idx['files']:
        name=row['path'];need(name in ('BINDINGS.json','ACTUAL_RESULT.json','README.md') and name not in expected_files,'Plain member differs')
        data=(folder/name).read_bytes();need(len(data)==row['bytes'] and digest(data)==row['sha256'],'Plain bytes differ');expected_files.add(name)
    actual={p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}
    need(actual==expected_files and not any(p.is_symlink() or getattr(p.lstat(),'st_file_attributes',0)&0x400 for p in folder.rglob('*')),'Unexpected/unsafe archive member')
    bindings=parse((folder/'BINDINGS.json').read_bytes());need(equal(bindings['roots'],spec['roots']) and equal(bindings['bindings'],spec['inputs']),'Original bindings differ')
    raw={}
    for row in bindings['bindings']:
        need(row['root'] in ('MAIN','REVIEW') and '..' not in Path(row['path']).parts and not Path(row['path']).is_absolute(),'Unsafe original alias')
        need(row['sha256'] in decoded and len(decoded[row['sha256']])==row['bytes'],'Original/raw object join differs')
        raw[row['root']+':'+row['path']]=decoded[row['sha256']]
    need(set(decoded)=={r['sha256'] for r in bindings['bindings']},'Unbound payload')
    R='output/neon-helper-375ec05-20261117-attempt1/'
    rev='375ec05e925159850ff3b0abf2e8f98f9d2ce129'
    def obj(name):return parse(raw['REVIEW:'+name])
    root=obj(R+'verification.json');before=obj(R+'source-before.json')
    need(root['format']=='has_root_neon_helper_followup_1' and root['revision']==rev and root['passed'] is True and root['full_suite_pass_claimed'] is False and root['host_scopes_closed'] is True and root['all_functional_source_unchanged'] is True,'Root scoped result differs')
    need(root['functional_source_files']==1029 and len(before)==1029 and equal(before,obj(R+'source-after.json')),'Root1029 source identity differs')
    for label in ('before','cpu-after','graphical-after','after'):
        for suffix,fmt,negative in (('-closure.json','has_root_workspace_scope_observation_1',3),('-worker-closure.json','has_root_neon_helper_worker_scope_1',2)):
            scope=obj(R+label+suffix)
            need(scope['format']==fmt and type(scope['owned_count']) is int and scope['owned_count']==0 and scope['owned_matches']==[] and scope['termination_issued'] is False and scope['matcher_positive_cases']==4 and scope['matcher_negative_cases']==negative,'Recorded scope differs')
    need([row['mode'] for row in root['rows']]==['cpu','graphical'],'Mode order differs')
    private=[];launch_rows=[];outcome_rows=[];missing=[]
    for row,ledger,total,seconds in zip(root['rows'],[[('transport',11),('adapter',128),('host',69)],[('focused',221),('peers',45)]],[208,266],[41.7605826,102.8179396]):
        mode=row['mode'];report=obj(R+mode+'-report.json');child=PureWindowsPath(row['report_path']).parent.relative_to(PureWindowsPath(spec['roots']['REVIEW'])).as_posix()+'/'
        need(row['exit']==0 and row['retained_Popen_reaped'] is True and row['timed_out'] is False and row['root_exact_suite_assertions_passed'] is True and row['seconds']==seconds,'Exact root mode admission differs')
        need(equal(report,row['report']) and equal(report,obj(child+'verification.json')),'Exact child/report copy differs')
        need(report['passed'] is True and report['error'] is None and report['mode']==mode and report['source_context']=='main_source_snapshot' and report['source_state']['revision']==rev and report['source_state']['working_status']==[] and report['overlay_files']==0 and report['native_requested'] is False and report['native_inputs_checked'] is False and report['native_fidelity'] is False and report['graphical_process_attempted'] is (mode=='graphical') and report['gpu_used'] is (mode=='graphical'),'Committed/no-overlay/native boundary differs')
        need(type(report['checks']) is int and report['checks']==total and [(c['label'],c['checks']) for c in report['results']]==ledger,'Original208/266 case ledger differs')
        need(set(report['preservation'])=={'main_sources','runtimes','head','native_originals','staged_native_inputs','published_requests','snapshot_sources','snapshot_extras','fixtures'} and all(x is True for x in report['preservation'].values()),'Original preservation gates differ')
        source=obj(child+'main-source-before.json');need(len(source)==1030 and equal(source,obj(child+'main-source-after.json')) and equal(source,obj(child+'snapshot-source-before.json')),'1030 snapshot identities differ')
        need(set(source)==set(before)|{'dependencies.json'} and all(source[name]['sha256']==value for name,value in before.items()),'1029 to1030 exact membership/projection differs')
        need(digest(raw['REVIEW:dependencies.json'])==source['dependencies.json']['sha256'],'Dependency source body/snapshot identity differs')
        source_digest=digest((json.dumps(source,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode())
        for case,(_,count) in zip(report['results'],ledger):
            label=case['label'];case_path=child+'Studio/output/helper-preview-qa/'+label+'/'
            need(case['passed'] is True and case['exit']==0 and case['timed_out'] is False and case['retained_Popen_reaped'] is True and case['error_markers']==[] and case['result_source_context_bound'] is True,'Case process/source controls differ')
            actual=obj(case_path+'result.json');got=len(actual['checks']) if type(actual['checks']) is list else actual['checks'];metrics=actual.get('metrics',actual)
            need(type(got) is int and got==count and actual['failures'] in ([],0) and metrics['main_revision']==rev and metrics['source_context']=='main_source_snapshot' and metrics['source_manifest_sha256']==source_digest,'Raw case count/context differs')
            command=obj(case_path+'command.json')
            if mode=='graphical':
                receipt=obj(case_path+'private-receipt.json');need(equal(receipt,case['private_receipt']) and case['clean_private_receipt'] is True,'Typed inline receipt differs')
                need(command.count('--receipt')==1 and PureWindowsPath(command[command.index('--receipt')+1])==PureWindowsPath(spec['roots']['REVIEW'])/PureWindowsPath(case_path)/'private-receipt.json','Direct receipt command path differs')
                for key,value in {'format':'studio_private_desktop_1','exit':0,'private_window_seen':True,'child_desktop_confirmed':True,'foreground_child_observed':False,'desktop_switch_requested':False,'job_closed':True,'desktop_closed':True}.items():need(equal(receipt.get(key),value),'Strict private desktop closure differs')
                private.append((receipt['desktop'],receipt['child_pid']))
            else:need('--receipt' not in command and (label=='transport' or '--headless' in command),'Headless CPU domain differs')
        prefix='REVIEW:'+child+'Studio/output/helper-preview-qa/'
        for key,data in raw.items():
            if key.startswith(prefix) and key.endswith('/owned-launch.json'):
                launch=parse(data);launch_rows.append(key)
                need(launch['job_assigned'] is True and launch['kill_on_close'] is True and launch['no_window'] is True and launch['active_process_limit']==1,'Owned worker launch differs')
                outkey=key.removesuffix('owned-launch.json')+'owned-outcome.json'
                if outkey in raw:
                    outcome=parse(raw[outkey]);need(equal(outcome['owner'],launch['owner']) and equal(outcome['python'],launch['python']) and equal(outcome['source_sha256'],launch['source_sha256']) and outcome['state']=='prepared_hidden' and outcome['exit']==0 and outcome['error']=='' and outcome['job_closed'] is True and outcome['process_handle_closed'] is True,'Worker completed outcome differs');outcome_rows.append(outkey)
                else:missing.append(key)
    need(len(private)==len(set(private))==2 and len(launch_rows)==21 and len(outcome_rows)==17 and len(missing)==4,'Private/worker metadata totals differ')
    need(all(any('/focused/worker-'+tag+'-helper-work/' in key for key in missing) for tag in ('seek','save','off','close')),'Launch-only cancellation scenario membership differs')
    for key,data in raw.items():
        if key.startswith('REVIEW:') and key[7:] in before:need(digest(data)==before[key[7:]],'Selected source bytes do not match tested root source map')
    summary=parse((folder/'ACTUAL_RESULT.json').read_bytes());need(equal(summary,spec['expected_summary']) and summary['full_suite_pass_claimed'] is False and summary['native_fidelity_claimed'] is False,'Public scoped summary differs')
    return {'passed':True,'original_bindings':len(raw),'unique_objects':len(decoded),'private_desktop_jobs':2,'CPU208_graphical266_original_ledger':True,'source1029_and_snapshot1030_join':True,'worker_launches':21,'completed_worker_outcomes':17,'four_launch_only_scenarios_disclosed':True,'zero_base_worker_scope_pairs':4,'originals_or_active_full_read':False,'INDEX_sha256':digest((folder/'INDEX.json').read_bytes())}
if __name__=='__main__':print(json.dumps(verify(),indent=2))
