"""Future owner-copy filesystem/proof adapter. Actual activation is absent.

Import reads only this packet's pinned source references. No functional, native,
Git, runtime or qualification file is read before the exact activation hash gate.
"""
from dataclasses import dataclass
from pathlib import Path,PureWindowsPath
import hashlib,json,os,re,stat,subprocess
import admission_core as A
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
WORKSPACE=ROOT.parent
APPROVED_ACTIVATION_SHA256='3ef0251629fcc3310eb2fa73edc53d699609e475f3c9ee2664ee708f69c1781b'
CORE_SHA='c6ebc4b6e3999fbdecf13697a2ccb0ca9f0cafe3368beaf9767bd5f247247f76'
CORE_PACKET_SHA='8ab1c8eb9f576a9c8a315ebf4df433fc4e4b8b4767ac44cdf64a2403467a2d42'
OLD=ROOT/'experiments/native_five_review_after_full_20261116'
SOURCEIO_PIN='fe24260b97ac03b899d9b5d4f0fd7b34772f3647'
SOURCE52='52f63c944ded7a651da871524d23a345b606424d'
_TOKEN=object()

@dataclass(frozen=True)
class Admitted:
    data:dict
    _token:object
    _snapshot_sha256:str

def _plain(value):
    if isinstance(value,Path):return str(value)
    if type(value) is bytes:return {'_blob_bytes':len(value),'_blob_sha256':A.digest(value)}
    if type(value) is dict:return {k:_plain(v) for k,v in value.items()}
    if type(value) is list:return [_plain(v) for v in value]
    if type(value) is tuple:return [_plain(v) for v in value]
    A.need(type(value) in (str,int,bool,float,type(None)),'unserializable admitted data');return value

def assert_admitted(value):
    A.need(type(value) is Admitted and value._token is _TOKEN and value._snapshot_sha256==A.digest(A.encoded(_plain(value.data))),'actual sealed input admission/token changed')
    require_activation_pin()
    import copy_executor as C
    data=value.data;H=C.helpers(data['root']);Git=ApprovedGit(H,data['git_executable'],data['git_identity'])
    A.need(Git.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==data['merged_revision'],'merged main HEAD changed after qualification')
    scope=['src','tests','tools','data','examples','project.godot','main.tscn','run.py','launch.pyw']
    changes=Git.check_output(['git','diff','HEAD','--name-only','--',*scope],cwd=ROOT,text=True).splitlines()+Git.check_output(['git','ls-files','--others','--exclude-standard','--',*scope],cwd=ROOT,text=True).splitlines()
    A.need(not [n for n in changes if '__pycache__' not in Path(n).parts and not n.endswith('.pyc')],'merged functional clean scope changed after qualification')
    A.need(not (ROOT/'override.cfg').exists() and not (ROOT/'project.binary').exists(),'main override changed after qualification')
    return data

def _admitted(data):
    require_activation_pin()
    return Admitted(data,_TOKEN,A.digest(A.encoded(_plain(data))))

def require_activation_pin():
    A.need(type(APPROVED_ACTIVATION_SHA256) is str and re.fullmatch('[a-f0-9]{64}',APPROVED_ACTIVATION_SHA256),'UNREADY: actual fullPASS/root release/mergedmain activation is not sealed')

def read_bound(H,descriptor,boundary,protected,exact=None,maximum=64*1024*1024):
    A.need(type(descriptor) is dict and set(descriptor)=={'path','bytes','mtime_ns','sha256'},'exact artifact descriptor required')
    A.need(type(descriptor['bytes']) is int and 0<=descriptor['bytes']<=maximum and type(descriptor['mtime_ns']) is int and type(descriptor['sha256']) is str and re.fullmatch('[a-f0-9]{64}',descriptor['sha256']),'invalid artifact identity')
    path=H['guarded'](Path(descriptor['path']),boundary)
    if exact is not None:A.need(path==Path(exact).absolute(),'exact proof artifact path differs')
    wanted={k:descriptor[k] for k in ('bytes','mtime_ns','sha256')}
    A.need(H['identity'](path)==wanted,'artifact before identity differs')
    raw=path.read_bytes();A.need(len(raw)==wanted['bytes'] and A.digest(raw)==wanted['sha256'] and H['identity'](path)==wanted,'artifact changed while read')
    protected[str(path)]=wanted;return raw

def reconstruct_historical52(blobs,manifest,recipe):
    A.need(type(blobs) is dict and len(blobs)==1019 and set(blobs)==set(manifest['source_sha256'])==set(recipe),'historical52 Git/source/recipe membership differs')
    result={}
    for name,blob in blobs.items():
        row=recipe[name];A.need(type(blob) is bytes and type(row) is dict and set(row)=={'mode','git_blob_sha256','tested_working_sha256','canonical_content_sha256'},'historical52 EOL recipe fields differ')
        A.need(A.digest(blob)==row['git_blob_sha256'] and row['tested_working_sha256']==manifest['source_sha256'][name],'historical52 Git/target identity differs')
        mode=row['mode']
        if mode=='exact_Git_blob':raw=blob
        else:
            A.need(Path(name).suffix in A.TEXT or name in A.TEXT_PATHS,'historical nontext EOL transform refused')
            if mode=='explicit_CRLF_to_LF':raw=blob.replace(b'\r\n',b'\n')
            elif mode=='explicit_canonical_LF_to_CRLF':raw=blob.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')
            elif mode.startswith('explicit_per_newline_CRLF_mask:'):
                parts=mode.split(':');A.need(len(parts)==3 and parts[1].isdigit() and re.fullmatch('[0-9a-f]*',parts[2]) and len(parts[2])%2==0,'invalid explicit EOL bitmask')
                canonical=blob.replace(b'\r\n',b'\n');count=int(parts[1]);mask=bytes.fromhex(parts[2]);lines=canonical.split(b'\n')
                A.need(count==len(lines)-1 and len(mask)==(count+7)//8 and (not count%8 or mask[-1]>>(count%8)==0),'explicit EOL bitmask extent/padding differs')
                raw=b''.join(lines[i]+(b'\r\n' if mask[i//8]&(1<<(i%8)) else b'\n') for i in range(count))+lines[-1]
            else:raise ValueError('unknown historical52 EOL reconstruction')
        A.need(A.digest(raw)==row['tested_working_sha256'] and A.digest(A.canonical(raw,name))==row['canonical_content_sha256'],'historical52 reconstructed exact raw/content witness differs')
        result[name]=raw
    return result

def _historical52_proof(H,items,protected):
    """New data-only validation of retained old proof; never import/run old admission."""
    roles={'state','host','host_raw','release','launch','birth','before','after','full_report'}
    A.need(type(items) is dict and set(items)==roles,'exact retained historical52 full artifacts required')
    raw={k:read_bound(H,v,ROOT,protected) for k,v in items.items()};doc={k:A.parse(v) for k,v in raw.items()}
    state=doc['state'];host=doc['host'];obs=doc['host_raw'];release=doc['release'];before=doc['before'];after=doc['after']
    A.need(state.get('status')=='passed' and type(state.get('suite_exit')) is int and state['suite_exit']==0 and state.get('source_unchanged') is True and state.get('source_commit')==SOURCE52,'historical52 actual fullPASS required')
    A.need(type(state.get('pid')) is int and state['pid']==79488 and state.get('process_started')=='2026-11-16T04:15:18.3655401Z','historical52 coordinator differs')
    A.need(host.get('format')=='has_canonical_authoritative_host_termination_1' and host.get('source_commit')==SOURCE52 and host.get('canonical_run')=='windows-canonical-bone-binding-20261116T041518335' and host.get('coordinator_pid')==79488 and host.get('python_pid')==91024 and host.get('raw_observation_sha256')==A.digest(raw['host_raw']),'historical52 host/raw proof differs')
    A.need(host.get('expected_creation_utc')=='2026-11-16T04:15:18.3655401Z' and host.get('expected_python_creation_utc')=='2026-11-16T04:15:18.9615298Z' and host.get('functional_source_entries')==1019,'historical52 birth/source differs')
    A.need(all(host.get(k) is True for k in ['coordinator_absent','python_absent','owned_runtime_command_matches_absent','source_before_after_and_current_exact','root_observer_issued_no_termination','no_process_killed']) and host.get('coordinator_matches')==[] and host.get('owned_runtime_matches')==[],'historical52 host closure differs')
    A.need(obs.get('source_commit')==SOURCE52 and obs.get('canonical_run')==str(ROOT/'output/windows-canonical-bone-binding-20261116T041518335') and obs.get('state_status')=='passed' and type(obs.get('suite_exit')) is int and obs['suite_exit']==0 and obs.get('root_birth_observation_sha256')=='ce9b8c1197b02b3d575083635419b7309160ea70ab08896d819f5d112c2da6df','historical52 raw/source birth differs')
    A.need(release.get('format')=='has_root_canonical_graphics_lease_release_1' and release.get('released') is True and release.get('source_commit')==SOURCE52 and release.get('canonical_run')==host['canonical_run'] and release.get('coordinator_pid')==79488 and release.get('python_pid')==91024,'historical52 release scope differs')
    A.need(all(release.get(k) is True for k in ['all_private_jobs_closed','owned_runtime_command_matches_absent','normalized_log_report_suffix_equal','root_observer_issued_no_termination']) and release.get('functional_source_entries')==1019,'historical52 release closure/source differs')
    A.need(release.get('canonical_state_sha256')==A.digest(raw['state']) and release.get('host_proof_sha256')==A.digest(raw['host']) and release.get('full_report_sha256')==A.digest(raw['full_report']),'historical52 release raw-byte binding differs')
    A.need(type(release.get('private_jobs')) is int and release['private_jobs']>0 and type(release.get('normal_exit_0')) is int and type(release.get('expected_Krita_cancellation_exit_2')) is int and release['normal_exit_0']+release['expected_Krita_cancellation_exit_2']==release['private_jobs'],'historical52 actual receipt totals differ')
    A.need(A.digest(raw['birth'])=='ce9b8c1197b02b3d575083635419b7309160ea70ab08896d819f5d112c2da6df','historical52 actual birth bytes differ')
    A.need(raw['before']==raw['after'] and A.digest(raw['before'])==A.SOURCE52_SHA and A.REF['typed_same'](before,after) and before['commit']==SOURCE52 and len(before['source_sha256'])==1019,'exact historical52 tested source bytes differ')
    return raw['before'],before

def _verify_packet_files(H,folder,index,protected):
    rows=index.get('files',index.get('payloads'));A.need(type(rows) is list and rows,'source packet membership missing')
    declared=set()
    for row in rows:
        name=row['path'];A.need(type(name) is str and name not in declared and not Path(name).is_absolute() and '..' not in Path(name).parts,'unsafe source packet row');declared.add(name)
        path=H['guarded'](folder/name,folder);actual=H['identity'](path)
        A.need(actual['bytes']==row['bytes'] and actual['sha256']==row['sha256'],'source packet payload differs')
        protected[str(path)]=actual
    for path in folder.rglob('*'):H['no_links'](path)
    actual={f.relative_to(folder).as_posix() for f in folder.rglob('*') if f.is_file()}
    A.need(actual==declared|{'INDEX.json'},'source packet extra/missing payload')



def validate_git_name(name):
    A.need(type(name) is str and name,'committed source name type')
    windows=PureWindowsPath(name);parts=name.split('/')
    reserved={'CON','PRN','AUX','NUL'}|{p+n for p in ['COM','LPT'] for n in '123456789¹²³'}
    A.need(type(name) is str and name and not windows.anchor and not windows.drive and not windows.root,'unsafe committed source name')
    A.need(all(part and part not in ('.','..') and part==part.rstrip(' .') and not any(ord(c)<32 or c in '\\:<>"|?*' for c in part) and part.split('.')[0].upper() not in reserved for part in parts),'unsafe committed Windows source name')
    return parts

def archive_included(name):
    parts=Path(name).parts
    return bool(parts) and parts[0] not in ('output','.git','.godot','__pycache__') and '__pycache__' not in parts and not name.endswith('.pyc')

def functional(name):
    return (name.split('/')[0] in ('src','tests','tools','data','examples') or name in ('project.godot','main.tscn','run.py','launch.pyw')) and '__pycache__' not in Path(name).parts and not name.endswith('.pyc')

def infer_historical_eol_mode(blob,raw,name):
    A.need(type(blob) is bytes and type(raw) is bytes,'source byte witness required')
    if raw==blob:return 'exact_Git_blob'
    A.need(Path(name).suffix in A.TEXT or name in A.TEXT_PATHS,'nontext witness EOL mismatch')
    canonical=blob.replace(b'\r\n',b'\n')
    A.need(raw.replace(b'\r\n',b'\n')==canonical,'historical source content differs from Git52')
    if raw==canonical:return 'explicit_CRLF_to_LF'
    if raw==canonical.replace(b'\n',b'\r\n'):return 'explicit_canonical_LF_to_CRLF'
    endings=[i for i,b in enumerate(raw) if b==10];mask=bytearray((len(endings)+7)//8)
    for n,i in enumerate(endings):
        if i>0 and raw[i-1]==13:mask[n//8]|=1<<(n%8)
    return 'explicit_per_newline_CRLF_mask:'+str(len(endings))+':'+bytes(mask).hex()

class ApprovedGit:
    """Use one exact identity for inherited read-only Git helper calls."""
    def __init__(self,H,path,identity):self.H=H;self.path=path;self.identity=identity
    def check_output(self,args,**options):
        A.need(type(args) is list and args and args[0]=='git' and len(args)>1 and args[1] in ('rev-parse','diff','ls-files','ls-tree','cat-file'),'only inherited read-only Git commands allowed')
        A.need(Path(options.get('cwd',ROOT)).absolute()==ROOT.absolute() and not options.get('shell'),'Git scope differs')
        A.need(self.H['identity'](self.path)==self.identity,'approved Git executable changed')
        options['timeout']=120
        environment=os.environ.copy();environment['GIT_OPTIONAL_LOCKS']='0';options['env']=environment
        command=[str(self.path),'--no-optional-locks','-c','core.fsmonitor=false',*args[1:]]
        if args[1]=='diff':command.insert(command.index('diff')+1,'--no-ext-diff')
        result=subprocess.check_output(command,**options)
        A.need(self.H['identity'](self.path)==self.identity,'approved Git executable changed during read')
        return result

def read_committed_archive(Git,revision,declared):
    A.need(declared.get('format')=='has_neon_owner_committed_archive_catalogue_1' and declared.get('revision')==revision and type(declared.get('files')) is dict,'exact reviewed committed owner catalogue required')
    listing=Git.check_output(['git','ls-tree','-rz',revision],cwd=ROOT)
    entries={}
    for row in listing.split(b'\0'):
        if not row:continue
        meta,path=row.split(b'\t',1);mode,kind,oid=meta.split();name=path.decode('utf-8')
        if not archive_included(name):continue
        validate_git_name(name);A.need(mode in (b'100644',b'100755') and kind==b'blob' and name not in entries,'unsupported committed owner entry')
        entries[name]=(mode.decode(),oid)
    A.need(0<len(entries)<=50000 and len({n.casefold() for n in entries})==len(entries) and set(entries)==set(declared['files']),'owner archive exact membership/casefold bounds differ')
    checks=Git.check_output(['git','cat-file','--batch-check=%(objectname) %(objecttype) %(objectsize)'],input=b''.join(oid+b'\n' for _,oid in entries.values()),cwd=ROOT).splitlines()
    A.need(len(checks)==len(entries),'Git owner size catalogue differs');total=0
    for (name,(mode,oid)),line in zip(entries.items(),checks):
        actual,kind,size=line.split();size=int(size);row=declared['files'][name]
        A.need(type(row) is dict and set(row)=={'mode','git_oid','bytes','sha256'} and type(row['bytes']) is int and row['mode']==mode and row['git_oid']==oid.decode() and type(row['sha256']) is str and re.fullmatch('[a-f0-9]{64}',row['sha256']),'reviewed owner file identity differs')
        A.need(actual==oid and kind==b'blob' and 0<=size<=128*1024*1024 and size==row['bytes'],'Git owner file size differs');total+=size
    A.need(total<=512*1024*1024,'committed owner source catalogue exceeds bounded512MiB ceiling')
    batch=Git.check_output(['git','cat-file','--batch'],input=b''.join(oid+b'\n' for _,oid in entries.values()),cwd=ROOT)
    blobs={};offset=0
    for name,(_,oid) in entries.items():
        line_end=batch.index(b'\n',offset);actual,kind,size=batch[offset:line_end].split();start=line_end+1;end=start+int(size)
        A.need(actual==oid and kind==b'blob' and end<len(batch) and batch[end:end+1]==b'\n','Git owner blob framing differs');body=batch[start:end]
        A.need(len(body)==declared['files'][name]['bytes'] and A.digest(body)==declared['files'][name]['sha256'],'Git owner blobSHA/size differs');blobs[name]=body;offset=end+1
    A.need(offset==len(batch),'trailing Git owner batch bytes')
    return blobs,{'files':len(blobs),'bytes':total,'catalogue_sha256':A.digest(A.encoded(declared))}

def validate_native52_byte_bridge(native,original_bytes,source52,delta):
    old={n:r for n,r in native['source_before']['files'].items() if functional(n)}
    A.need(native.get('passed') is True and all(v is True for v in native['preservation'].values()) and len(old)==1008 and len(source52)==1019 and set(original_bytes)==set(old) and set(old)<=set(source52),'exact historical native/52 source inventories differ')
    rows={r['path']:r for r in delta['changed_or_added']};A.need(len(rows)==20 and len(rows)==len(delta['changed_or_added']),'exact historical20 delta rows required')
    unchanged=[];observed=set()
    for name,b in source52.items():
        a=original_bytes.get(name)
        if a is not None:A.need(A.digest(a)==old[name]['sha256'],'retained original native source bytes differ')
        if a is not None and A.canonical(a,name)==A.canonical(b,name):
            A.need(name not in rows,'historical unchanged source falsely relaxed');unchanged.append(name);continue
        observed.add(name);A.need(name in rows,'unreviewed original native→52 delta')
        row=rows[name]
        A.need(row['new_working_sha256']==A.digest(b) and row['new_content_sha256']==A.digest(A.canonical(b,name)) and row['old_native_sha256']==(old[name]['sha256'] if a is not None else None) and row['old_content_sha256']==(A.digest(A.canonical(a,name)) if a is not None else None),'historical20 delta source byte identities differ')
    A.need(observed==set(rows),'historical native→52 delta membership differs')
    for name in delta['unchanged_core']:A.need(name in unchanged and A.digest(original_bytes[name])==A.digest(source52[name]),'old Model/Bindings/SceneIO exact core differs')
    return {'old_native_files':1008,'source52_files':1019,'explicit_changed_added':20,'unchanged_content_files':len(unchanged),'unchanged_core':delta['unchanged_core']}

def revalidate_native_predecessor(H,lock,source52,current,delta,protected):
    path=H['NATIVE_RUN']/'verification.json';descriptor={'path':str(path),**lock['native_verification']}
    native=A.parse(read_bound(H,descriptor,ROOT/'output',protected,exact=path))
    old={n:r for n,r in native['source_before']['files'].items() if functional(n)};original={};total=0
    A.need(len(old)==1008,'original native functional1008 proof differs')
    for name,row in old.items():
        validate_git_name(name);p=H['guarded'](H['NATIVE_RUN']/'Studio'/name,H['NATIVE_RUN']/'Studio');before=H['identity'](p)
        A.need(before['sha256']==row['sha256'] and before['bytes']<=128*1024*1024,'old native source identity differs');total+=before['bytes'];A.need(total<=512*1024*1024,'old native source witness budget')
        body=p.read_bytes();A.need(A.digest(body)==row['sha256'] and H['identity'](p)==before,'old native source changed during read');original[name]=body;protected[str(p)]=before
    joined=validate_native52_byte_bridge(native,original,source52,delta)
    qualified=ROOT/'experiments/native_five_qualified_actual_20261116';index_path=H['guarded'](qualified/'INDEX.json',qualified);identity=H['identity'](index_path)
    A.need(identity['sha256']=='429ea76d462a385cfa2d292ed9c2c12dd9fbf9e52193f63bfb0e7776324dd655','prior isolated native5 qualification packet changed');index=A.parse(index_path.read_bytes());A.need(H['identity'](index_path)==identity,'prior native5 index changed');protected[str(index_path)]=identity
    rows={r['path']:r for r in index['files']};bodies={}
    for name in ['BENCHMARK.json','source/src/source_secondary.gd','source/src/secondary_live.gd','source/src/source_chain_math.gd']:
        p=H['guarded'](qualified/name,qualified);before=H['identity'](p);A.need(before['sha256']==rows[name]['sha256'] and before['bytes']==rows[name]['bytes'],'prior native5 source/metadata alias differs')
        body=p.read_bytes();A.need(A.digest(body)==before['sha256'] and H['identity'](p)==before,'prior native5 evidence changed');bodies[name]=body;protected[str(p)]=before
    result=A.parse(bodies['BENCHMARK.json'])
    A.need(result['state']['passed'] is True and type(result['state']['checks']) is int and result['state']['checks']==266 and result['state']['failures']==0 and result['GUI']['passed'] is True and type(result['GUI']['checks']) is int and result['GUI']['checks']==102 and result['GUI']['failures']==0 and result['runtime_lease_released'] is True,'exact prior266/102 native5 scope differs')
    def code(raw):return '\n'.join(line for line in raw.decode('utf-8').splitlines() if line.strip() and not line.lstrip().startswith('#'))
    for name in ['src/source_secondary.gd','src/secondary_live.gd','src/source_chain_math.gd']:
        A.need(name in current and code(current[name])==code(bodies['source/'+name]),'candidate native5 runtime differs beyond qualified source headers')
    joined.update(prior_native5_packet_sha256=identity['sha256'],prior_native5_checks=[266,102],new_conversion_performed=False)
    return joined

def require_qualified_inputs():
    require_activation_pin()  # Before any functional/native/Git/qualification path read.
    import copy_executor as C
    H=C.helpers(ROOT);protected={}
    activation_path=H['guarded'](HERE/'ACTIVATION.json',HERE)
    raw=activation_path.read_bytes();A.need(len(raw)<=8*1024*1024 and A.digest(raw)==APPROVED_ACTIVATION_SHA256,'actual activation raw identity differs')
    protected[str(activation_path)]=H['identity'](activation_path);plan=A.parse(raw)
    A.need(plan.get('format')=='has_neon_owner_review_actual_activation_1' and plan.get('status')=='ROOT_REVIEWED_ACTUAL_FULL_AND_MERGED_MAIN','actual root review activation required')
    A.need(type(plan.get('allow_checkout_eol')) is bool and type(plan.get('merged_revision')) is str and re.fullmatch('[a-f0-9]{40}',plan['merged_revision']),'merged revision/EOL admission differs')
    # This executor packet and sealed admission predecessor are code-only inputs.
    own_index_path=H['guarded'](HERE/'INDEX.json',HERE);own_index=A.parse(own_index_path.read_bytes());protected[str(own_index_path)]=H['identity'](own_index_path)
    _verify_packet_files(H,HERE,own_index,protected)
    core_packet=ROOT/'experiments/neon_owner_admission_shell_eol_20261117';core_index=H['guarded'](core_packet/'INDEX.json',ROOT/'experiments')
    A.need(A.digest((HERE/'admission_core.py').read_bytes())==CORE_SHA and H['identity'](core_index)['sha256']==CORE_PACKET_SHA,'sealed admission source predecessor differs');protected[str(core_index)]=H['identity'](core_index)
    predecessor_path=H['guarded'](core_packet/'PREDECESSOR_SOURCE_PINS.json',core_packet);source_pins=A.parse(predecessor_path.read_bytes());protected[str(predecessor_path)]=H['identity'](predecessor_path)
    core_rows={row['path']:row for row in A.parse(core_index.read_bytes())['payloads']}
    A.need(A.digest(predecessor_path.read_bytes())==core_rows['PREDECESSOR_SOURCE_PINS.json']['sha256'],'immutable predecessor reference list differs')
    for name,row in source_pins['pins'].items():
        path=H['guarded'](OLD/name,OLD);actual=H['identity'](path);A.need(actual['sha256']==row['sha256'] and actual['bytes']==row['bytes'],'immutable old builder/replay source changed');protected[str(path)]=actual
    git_desc=plan['git_executable'];A.need(type(git_desc) is dict and set(git_desc)=={'path','bytes','mtime_ns','sha256'},'approved exact Git executable identity required')
    git_path=Path(git_desc['path']).absolute();H['no_links'](git_path);git_identity={k:git_desc[k] for k in ('bytes','mtime_ns','sha256')}
    A.need(H['identity'](git_path)==git_identity,'approved read-only Git tool differs');protected[str(git_path)]=git_identity;Git=ApprovedGit(H,git_path,git_identity);H['subprocess']=Git
    context_raw=read_bound(H,plan['candidate_context'],ROOT/'experiments',protected);context=A.parse(context_raw)
    A.need(context['functional_sources']==1029 and type(context['functional_sources']) is int,'candidate functional scope differs')
    candidate=H['guarded'](Path(context['checkout']),WORKSPACE);A.need(candidate.name=='has-neon-review-20261116-c2d52ff','qualified candidate checkout scope differs')
    run=H['guarded'](candidate/'output'/context['run_name'],candidate/'output')
    context_folder=Path(plan['candidate_context']['path']).parent
    index_path=H['guarded'](context_folder/'INDEX.json',ROOT/'experiments');index_raw=index_path.read_bytes()
    A.need(A.digest(index_raw)==plan['candidate_terminal_packet_index_sha256'],'qualified root terminal source packet differs');protected[str(index_path)]=H['identity'](index_path);_verify_packet_files(H,context_folder,A.parse(index_raw),protected)
    A.need(A.digest((context_folder/'close_terminal.py').read_bytes())==A.REFERENCE_SHA and A.digest((context_folder/'legacy_result_gates.py').read_bytes())==A.LEGACY_SHA,'root observer/legacy code differs')
    registry_path=context_folder/'RESULT_REGISTRY.json';registry_raw=registry_path.read_bytes();A.need(A.digest(registry_raw)==context['registry_sha256'],'qualified registry raw pin differs');registry=A.parse(registry_raw)
    exact={'state':run/'state.json','birth':run/'root-birth-observation.json','launch':run/'launch.json','before':run/'source-before.json','after':run/'source-after.json','full_report':run/'terminal-audit-attempt1/full-verification.json','canonical_log':run/'canonical.log','inventory':run/'terminal-audit-attempt1/receipt-inventory.json','release':run/'graphics-lease-closed.json'}
    A.need(set(plan['candidate_artifacts'])==set(exact),'exact actual candidate proof roles required')
    artifacts={k:read_bound(H,plan['candidate_artifacts'][k],candidate/'output',protected,exact=v) for k,v in exact.items()}
    for name,digest in context['immutable_run_inputs'].items():
        path=H['guarded'](run/name,run);A.need(H['identity'](path)['sha256']==digest,'immutable launch/source/birth context changed');protected[str(path)]=H['identity'](path)
    inventory=A.parse(artifacts['inventory']);report_meta=inventory['phase_documents'][str(candidate/'output/verification.json')]
    A.need(report_meta['sha256']==A.digest(artifacts['full_report']),'preserved fresh full report differs from root-consulted phase')
    candidate_result=A.check_candidate_bundle(artifacts,context,registry,{k:v['sha256'] for k,v in plan['candidate_artifacts'].items()},report_meta['mtime_ns'])
    for path,digest in [(Path(context['runner']),context['runner_sha256']),(Path(context['powershell']),context['powershell_sha256'])]:
        A.need(H['identity'](path)['sha256']==digest,'qualified runner/observer tool source changed');protected[str(path)]=H['identity'](path)
    revision=Git.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();A.need(revision==plan['merged_revision'],'actual merged main HEAD differs')
    scope=['src','tests','tools','data','examples','project.godot','main.tscn','run.py','launch.pyw']
    changed=Git.check_output(['git','diff','HEAD','--name-only','--',*scope],cwd=ROOT,text=True).splitlines();untracked=Git.check_output(['git','ls-files','--others','--exclude-standard','--',*scope],cwd=ROOT,text=True).splitlines()
    A.need(not [n for n in changed+untracked if '__pycache__' not in Path(n).parts and not n.endswith('.pyc')],'merged functional source is dirty or overlaid')
    A.need(not (ROOT/'override.cfg').exists() and not (ROOT/'project.binary').exists(),'main override/binary source not admitted')
    hashes=H['source_map']();A.need(hashes==candidate_result['functional_source_sha256'],'merged actual functional working bytes differ from tested candidate')
    catalogue=A.parse(read_bound(H,plan['owner_archive_catalogue'],HERE,protected));committed,archive_identity=read_committed_archive(Git,revision,catalogue)
    A.need({n for n in committed if functional(n)}==set(hashes),'owner committed functional membership differs from qualified1029')
    identities={n:H['identity'](ROOT/n) for n in hashes};working={n:(ROOT/n).read_bytes() for n in hashes};git={n:committed[n] for n in hashes}
    A.need(all(H['identity'](ROOT/n)==identities[n] and A.digest(working[n])==hashes[n] for n in hashes),'merged working source changed while copied to memory')
    recipe_raw=read_bound(H,plan['merged_working_recipe'],HERE,protected);recipe=A.parse(recipe_raw)
    merged=A.check_merged_sources(hashes,working,git,recipe,revision,plan['allow_checkout_eol'])
    source52_raw,source52=_historical52_proof(H,plan['historical52_full_proof'],protected)
    old_recipe=A.parse(read_bound(H,plan['historical52_working_recipe'],ROOT/'experiments',protected));old_blobs=H['git_blobs'](SOURCE52,list(source52['source_sha256']))
    old_working=reconstruct_historical52(old_blobs,source52,old_recipe)
    lock_path=H['guarded'](OLD/'builder/input-lock.json',OLD);delta_path=H['guarded'](OLD/'source-delta.json',OLD);lock_before=H['identity'](lock_path);delta_before=H['identity'](delta_path);lock_raw=lock_path.read_bytes();old_delta_raw=delta_path.read_bytes();A.need(H['identity'](lock_path)==lock_before and H['identity'](delta_path)==delta_before,'historical lock/delta changed during read');protected[str(lock_path)]=lock_before;protected[str(delta_path)]=delta_before
    historical=A.check_historical_predecessors(lock_raw,old_delta_raw,source52_raw,old_working)
    native52=revalidate_native_predecessor(H,A.parse(lock_raw),old_working,working,A.parse(old_delta_raw),protected)
    second=A.parse(read_bound(H,plan['reviewed52_to_candidate_delta'],HERE,protected));A.need(second.get('format')=='has_reviewed52_to_qualified_Neon_delta_1' and second.get('review_status')=='ROOT_REVIEWED_EXPLICIT_SOURCE_DELTA','explicit second source delta review required')
    old_map={n:{'raw_sha256':A.digest(v),'content_sha256':A.digest(A.canonical(v,n))} for n,v in old_working.items()};new_map={n:{'raw_sha256':A.digest(v),'content_sha256':A.digest(A.canonical(v,n))} for n,v in working.items()}
    delta=A.check_reviewed_delta(old_map,new_map,second['rows']);A.need(set(second['reasons'])==set(delta['changed_or_added_files']) and all(type(v) is str and 0<len(v)<=2048 for v in second['reasons'].values()),'every source delta needs its exact reviewed reason')
    proposal=A.assemble_copy_proposal(candidate_result,merged,historical,delta)
    final=H['guarded'](WORKSPACE/('HAS-Review-Neon-'+revision[:7]+'-native'),WORKSPACE);A.need(final.parent==WORKSPACE and not final.exists(),'exact fresh new review sibling required')
    old_review=WORKSPACE/'HAS-Review-20261115-SFM-Joints-f0dd57a-replay2';A.need(old_review.is_dir() and final!=old_review,'existing owner review must remain')
    A.need(all(H['identity'](Path(path))==row for path,row in protected.items()),'qualification/preparation artifact changed before admission')
    data={'root':ROOT,'workspace':WORKSPACE,'final':final,'merged_revision':revision,'candidate_commit':context['commit'],'lock':A.parse(lock_raw),'source_identities':identities,'source_hashes':hashes,'eol_recipe':recipe,'source_delta_admission':{'historical':historical,'original_native52_revalidation':native52,'second':delta,'copy_source_proposal':proposal},'full_gate':protected,'preparation':{str(HERE/row['path']):H['identity'](HERE/row['path']) for row in own_index.get('files',own_index.get('payloads'))},'old_review':old_review,'support_source_blobs':{n:v for n,v in committed.items() if n not in hashes},'support_source_hashes':{n:A.digest(v) for n,v in committed.items() if n not in hashes},'support_catalogue_identity':archive_identity,'git_executable':git_path,'git_identity':git_identity}
    return _admitted(data)
