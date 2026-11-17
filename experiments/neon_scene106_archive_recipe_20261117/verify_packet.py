"""Independent artifact-only verifier; no builders, original outputs or engines."""
from pathlib import Path
import gzip
import hashlib
import io
import json
import re

HERE=Path(__file__).resolve().parent
PACKET=HERE.parent/'neon_scene106_actual_packet_20261117'
INPUTS_SHA='cc72b17a8e164da8de85e50095ca8d689ce85fb0a6d0bcf09b08503960735579'
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
    need(idx['format']=='has_scene106_compact_exact_actual_packet_1' and idx['recipe_inputs_sha256']==digest(spec_raw),'Recipe/archive binding differs')
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
    D='REVIEW:output/neon-scene-mask-diagnostic-20261117-attempt1/'
    P='REVIEW:output/neon-scene-view106-20261117-attempt1/'
    C='REVIEW:output/scene-view/1794884325741516800/'
    def obj(key):return parse(raw[key])
    diagnostic=obj(D+'verification.json');result=obj(P+'verification.json');report=obj(P+'scene-report.json')
    need(diagnostic['process_exit']==1 and diagnostic['reaped'] is True and diagnostic['report']['checks']==102 and diagnostic['report']['failures']==4 and diagnostic['full_pass_claimed'] is False,'Failed102/4 diagnostic lost')
    need(equal(diagnostic['report'],obj(D+'case/result.json')),'Raw failed report differs')
    need(result['passed'] is True and result['full_suite_pass_claimed'] is False and result['functional_source_files']==1029 and result['host_scopes_closed'] is True,'Scoped PASS differs')
    need(equal(result['rows'][0]['report'],report) and equal(obj(P+'scene-stdout.log'),report),'Exact raw/inline PASS report differs')
    smoke=report['scene_view_smoke'];unit=report['scene_view_unit']
    need(type(smoke['checks']) is int and smoke['checks']==106 and type(smoke['failures']) is int and smoke['failures']==0 and len(smoke['cases'])==4 and all(c['display_composition']['supported'] is True and c['display_composition']['composite_ok'] is True for c in smoke['cases']),'Actual106 checks differ')
    need(unit['checks']==12830 and unit['cases']==144 and unit['failures']==0 and equal(unit,obj(C+'unit.json')),'Unit result differs')
    need(equal({k:v for k,v in smoke.items() if k not in ('private_receipt','private_receipt_path')},obj(C+'result.json')),'Raw smoke report differs')
    before=obj(P+'source-before.json');need(len(before)==1029 and equal(before,obj(P+'source-after.json')),'1029 source preservation differs')
    need(equal(report['source_sha256'],obj(C+'source-sha256.json')) and len(report['source_sha256'])==203,'203 wrapper source preservation differs')
    for path,sha in report['source_sha256'].items():need(before[path.replace('\\','/')]==sha,'Source map cross-join differs')
    jobs=[]
    for command_key,receipt_key,exit_code in ((D+'command.json','REVIEW:output/private-desktop/scene_view_diagnostic_0ed86dca87e24d778e9be683015de1ad.json',1),(C+'scene_view_smoke-command.json','REVIEW:output/private-desktop/scene_view_smoke_d2e3009fb20f4ffa816db464d6a477e1.json',0)):
        command=obj(command_key);receipt=obj(receipt_key);path=spec['roots']['REVIEW']+'\\'+receipt_key.split(':',1)[1].replace('/','\\')
        need(command.count('--receipt')==1 and command[command.index('--receipt')+1]==path,'Direct owned receipt join differs')
        for key,val in {'format':'studio_private_desktop_1','exit':exit_code,'desktop_switch_requested':False,'private_window_seen':True,'child_desktop_confirmed':True,'foreground_child_observed':False,'job_closed':True,'desktop_closed':True}.items():need(equal(receipt.get(key),val),'Strict desktop closure differs')
        jobs.append((receipt['desktop'],receipt['child_pid']))
    need(len(set(jobs))==2 and equal(obj(D+'private-receipt.json'),obj('REVIEW:output/private-desktop/scene_view_diagnostic_0ed86dca87e24d778e9be683015de1ad.json')),'Two-job typed receipt dedup differs')
    need(raw['REVIEW:output/private-desktop/scene_view_diagnostic_0ed86dca87e24d778e9be683015de1ad.json'].replace(b'\r\n',b'\n')+b'\n'==raw[D+'private-receipt.json'],'Exact receipt serialization relation differs')
    need(equal(smoke['private_receipt'],obj('REVIEW:output/private-desktop/scene_view_smoke_d2e3009fb20f4ffa816db464d6a477e1.json')),'Inline physical receipt differs')
    ucmd=obj(C+'scene_view_unit-command.json');need('--headless' in ucmd and '--receipt' not in ucmd,'Unit domain differs')
    for key in (D+'before-closure.json',D+'after-closure.json',P+'before-closure.json',P+'after-closure.json',P+'scene-after-closure.json'):
        s=obj(key);need(type(s['owned_count']) is int and s['owned_count']==0 and s['owned_matches']==[] and s['termination_issued'] is False and s['matcher_positive_cases']==4 and s['matcher_negative_cases']==3,'Recorded host scope differs')
    diag_lines=raw[D+'ordered-engine.log'].decode('utf-8-sig').splitlines();pass_lines=raw[C+'scene_view_smoke-engine.log'].decode('utf-8-sig').splitlines()
    diag_checks=[line[5:] for line in diag_lines if line.startswith(('PASS ','FAIL '))]
    pass_checks=[line[5:] for line in pass_lines if line.startswith('PASS ')]
    need(len(diag_checks)==102 and sum(line.startswith('FAIL ') for line in diag_lines)==4 and len(pass_checks)==106 and not any(line.startswith('FAIL ') for line in pass_lines),'Ordered check ledger differs')
    retained=[s for s in pass_checks if not s.startswith('independent raw scene texel matches the source-pinned display composition: ')]
    need(retained==diag_checks,'Original102 ordered semantic messages changed')
    actual_summary=parse((folder/'ACTUAL_RESULT.json').read_bytes());need(equal(actual_summary,spec['expected_summary']) and actual_summary['unique_physical_jobs']==2 and actual_summary['full_suite_pass_claimed'] is False,'Public summary differs')
    return {'passed':True,'original_bindings':len(raw),'unique_objects':len(decoded),'unique_physical_jobs':2,'diagnostic':'102/4 exit1 retained','scene106':'106/0 plus unit12830/0','legacy102_ordered_messages_exact':True,'source1029_unchanged':True,'originals_or_active_full_read':False,'INDEX_sha256':digest((folder/'INDEX.json').read_bytes())}
if __name__=='__main__':print(json.dumps(verify(),indent=2))
