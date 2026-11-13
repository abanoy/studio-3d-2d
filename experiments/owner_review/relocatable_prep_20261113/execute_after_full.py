"""Prepared only: exact new external review, gated on a passed/released full run.

No main verifier guard is changed. The external replay has two exact boundaries:
the newly reserved final review and its fresh checkout/output validation folder.
It uses the unchanged committed GDScript and metadata comparison contract.
"""
from pathlib import Path, PurePosixPath
import argparse, ctypes as C, hashlib, importlib.util, json, os, re, shutil
import stat, subprocess, sys, time, zipfile
from ctypes import wintypes as W

BASE=Path(__file__).resolve().parent
ROOT=next(p for p in BASE.parents if (p/'project.godot').is_file())
WORKSPACE=ROOT.parent
PYTHON=Path(r'C:\Program Files\Python313\python.exe')
PYTHONW=PYTHON.with_name('pythonw.exe')
GODOT=Path(r'C:\a\tools\Godot\Godot_v4.6-stable_win64.exe')
FFMPEG=Path(r'C:\Program Files\ffmpeg\bin\ffmpeg.exe')
SOURCEIO=ROOT/'output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647'
PINS={PYTHON:'03573716a7fcbd8b7fed8fe0163bbfbd3a852546920d6a666123f307c8dac7d9',PYTHONW:'2bea4fc941b7d9436afa1be8cb46551c0694deed23b3fec87b969054238be099',GODOT:'63913d01be2c2d1f929b4a626f5347117126b34e9c64cbf350ea9f35a9657ebf'}
BAD=['ERROR:','WARNING:','SCRIPT ERROR','SHADER ERROR','FAIL ','ObjectDB instances leaked','unclaimed string names','Pages in use exist at exit','_set_transient_exclusive_child']

def need(ok,message):
    if not ok:raise RuntimeError(message)
def sha(path):
    with Path(path).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def guarded(path,boundary):
    path=Path(path).absolute();boundary=Path(boundary).absolute()
    need('..'not in path.parts and path!=boundary and path.resolve().is_relative_to(boundary.resolve()),'Outside exact boundary: '+str(path))
    for part in(path,*path.parents):
        if part.exists():
            s=part.lstat();need(not stat.S_ISLNK(s.st_mode)and not getattr(s,'st_file_attributes',0)&0x400,'Link/reparse path refused: '+str(part))
        if part==boundary:break
    return path
def stamp(path):
    p=Path(path);a=p.stat();need(p.is_file(),'Expected regular file: '+str(p));digest=sha(p);b=p.stat()
    need((a.st_size,a.st_mtime_ns)==(b.st_size,b.st_mtime_ns),'File changed during hashing: '+str(p))
    return dict(bytes=b.st_size,mtime_ns=b.st_mtime_ns,sha256=digest)
def load(path):return json.loads(Path(path).read_bytes())
def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def source_map(folder):
    result={}
    for base,dirs,files in os.walk(folder,followlinks=False):
        base=Path(base)
        for name in dirs:guarded(base/name,folder)
        dirs[:]=sorted(name for name in dirs if name not in('output','.godot','__pycache__'))
        for name in sorted(files):
            p=base/name
            if p.suffix not in('.pyc','.pyo'):result[p.relative_to(folder).as_posix()]=stamp(guarded(p,folder))
    return result
def runtime_map():
    result={str(p):stamp(p)for p in PINS}
    need(all(result[str(p)]['sha256']==h for p,h in PINS.items()),'Approved executable fingerprint differs')
    need(FFMPEG.is_file(),'Existing FFmpeg is absent');result[str(FFMPEG)]=stamp(FFMPEG);return result

def release_gate(canonical,release,revision):
    state=load(canonical/'state.json');released=load(release)
    need(state.get('status')=='passed'and state.get('suite_exit')==0 and state.get('source_unchanged')is True and state.get('source_commit')==revision,'Full suite is not a passed exact-revision terminal run')
    need(released.get('format')=='has_canonical_graphics_lease_released_1'and released.get('released')is True and released.get('canonical_run')==canonical.name and released.get('source_commit')==revision and released.get('coordinator_pid')==state['pid']and released.get('canonical_state_sha256')==sha(canonical/'state.json'),'Released lease does not bind the passed canonical state')
    need(released.get('fresh_root_receipts_all_exit0_closed_no_foreground_no_switch')is True and any('absent_authoritative_host_query'in key and value is True for key,value in released.items()),'Authoritative coordinator/child absence and clean desktop release proof required')
    kernel=C.WinDLL('kernel32',use_last_error=True);kernel.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];kernel.OpenProcess.restype=W.HANDLE
    kernel.WaitForSingleObject.argtypes=[W.HANDLE,W.DWORD];kernel.WaitForSingleObject.restype=W.DWORD;kernel.CloseHandle.argtypes=[W.HANDLE];kernel.CloseHandle.restype=W.BOOL
    handle=kernel.OpenProcess(0x100000,False,state['pid'])
    if handle:
        try:need(kernel.WaitForSingleObject(handle,0)==0,'Canonical coordinator PID is live or reused; no graphics admitted')
        finally:kernel.CloseHandle(handle)
    else:need(C.get_last_error()==87,'Cannot prove canonical coordinator absent in this execution context')
    return dict(state=stamp(canonical/'state.json'),release=stamp(release),source_commit=revision)

def package_readback(path):
    # Data-only streaming CRC/SHA check; no member is extracted or executed.
    with zipfile.ZipFile(path)as archive:
        entries=archive.infolist();names=[e.filename for e in entries]
        need(len(names)==len(set(names))and len(names)<2000 and sum(e.file_size for e in entries)<=512*1024*1024,'Invalid/oversized package inventory')
        need(archive.getinfo('has.json').file_size<=1024*1024 and archive.getinfo('project.json').file_size<=1024*1024,'Oversized package metadata')
        header=json.loads(archive.read('has.json'));project=json.loads(archive.read('project.json'))
        need(header.get('storage')=='packed'and project.get('schema_version')==4,'Expected packed schema4 review')
        payload=header['payload'];need(set(names)=={'has.json'}|{r['path']for r in payload},'Unexpected package members')
        for row in payload:
            name=row['path'];parts=PurePosixPath(name)
            need(not parts.is_absolute()and '..'not in parts.parts and '\\'not in name and ':'not in name,'Unsafe data-only member path')
            entry=archive.getinfo(name);need(not entry.flag_bits&1 and entry.compress_type in(0,8)and entry.file_size==row['bytes'],'Invalid payload declaration')
            h=hashlib.sha256();count=0
            with archive.open(entry)as stream:
                for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk);count+=len(chunk)
            need(count==row['bytes']and h.hexdigest()==row['sha256'],'Payload SHA/CRC mismatch')
        return dict(storage='packed',all_payload_sha256_and_crc_readback=True,asset_count=len(header['assets']),cel_count=sum(len(l.get('cels',[]))for l in project['layers']),video=project['video'],objects=[o.get('name')for o in project['world']['objects']])

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision',default='1236796865e677b150a2d7e2add20f2aac5325fe')
    parser.add_argument('--canonical-run',type=Path,default=ROOT/'output/canonical-owned-20261113T200642700')
    parser.add_argument('--lease-release',type=Path)
    parser.add_argument('--final',type=Path)
    parser.add_argument('--execute-after-full',action='store_true')
    parser.add_argument('--exclusive-graphics-lease',action='store_true')
    parser.add_argument('--allow-checkout-eol',action='store_true')
    opt=parser.parse_args();need(re.fullmatch('[0-9a-f]{40}',opt.revision),'Exact full commit required')
    final=Path(opt.final or WORKSPACE/('HAS-Review-20261113-'+opt.revision[:7])).absolute()
    need(final.parent.resolve()==WORKSPACE.resolve()and re.fullmatch('HAS-Review-20261113-'+opt.revision[:7]+'(?:-[a-z0-9]+)?',final.name),'Final review must be the explicit fresh named workspace sibling')
    guarded(final,WORKSPACE)
    if not opt.execute_after_full:
        print(json.dumps(dict(prepared_only=True,final=str(final),revision=opt.revision,explicit_checkout_eol=opt.allow_checkout_eol,build_or_replay_performed=False,required='Passed canonical terminal state, authoritative graphics-release receipt, and explicit exclusive lease'),indent=2));return
    need(opt.exclusive_graphics_lease and os.name=='nt'and Path(sys.executable).resolve()==PYTHON.resolve(),'Approved Windows Python and explicit exclusive graphics lease required')
    need(not final.exists(),'Final delivery directory must be fresh')
    canonical=guarded(opt.canonical_run,ROOT/'output');release=guarded(opt.lease_release or canonical/'graphics-lease-released.json',canonical)
    lease=release_gate(canonical,release,opt.revision)
    preparation=load(BASE/'preparation.json');old=Path(preparation['protected_review']);need(old==ROOT/'output/owner-review-current-20261113','Protected review identity differs')
    for name,expected in preparation['protected_files'].items():need(stamp(guarded(old/name,old))==expected,'Protected old review changed before staging: '+name)
    protected_before={name:stamp(old/name)for name in preparation['protected_files']}
    old_source_before=load(BASE/'old-studio-source-before.json')
    need(source_map(old/'Studio')==old_source_before,'Protected old Studio source changed since preparation')
    runtimes=runtime_map();sourceio_before=load(BASE/'sourceio-source-before.json')
    need(source_map(SOURCEIO)==sourceio_before and(SOURCEIO/'LICENSE').is_file(),'Approved SourceIO source set differs from the recorded exact runtime')
    core=['tools/build_owner_review_snapshot.py','tools/verify_owner_review.py','tests/owner_review_replay.gd','tests/current_candidate_startup.gd','tests/current_candidate_startup.tscn']
    core_admission=[]
    for name in core:
        blob=subprocess.check_output(['git','show',opt.revision+':'+name],cwd=ROOT)
        actual=(ROOT/name).read_bytes();exact=actual==blob
        eol_only=opt.allow_checkout_eol and actual.replace(b'\r\n',b'\n')==blob.replace(b'\r\n',b'\n')
        need(exact or eol_only,'Current builder/harness differs from requested Git bytes; only explicit CRLF-to-LF admission is supported: '+name)
        core_admission.append(dict(path=name,working_sha256=hashlib.sha256(actual).hexdigest(),git_sha256=hashlib.sha256(blob).hexdigest(),admission='exact bytes'if exact else'explicit --allow-checkout-eol; CRLF-to-LF only; no file is normalized'))
    harness_paths=[ROOT/name for name in core]+[Path(__file__),BASE/'preparation.json',BASE/'README.template.md',BASE/'sourceio-source-before.json',BASE/'old-studio-source-before.json']
    harness_before={str(path):stamp(path)for path in harness_paths}
    nonce=str(time.time_ns());stage=guarded(ROOT/'output'/('owner-review-stage-'+opt.revision[:7]+'-'+nonce),ROOT/'output')
    evidence=guarded(ROOT/'output'/('owner-review-final-validation-'+opt.revision[:7]+'-'+nonce),ROOT/'output');need(not stage.exists()and not evidence.exists(),'Fresh staging/evidence required')
    stage.mkdir();evidence.mkdir();state=dict(format='has_relocatable_owner_review_run_1',source_commit=opt.revision,stage=str(stage),final=str(final),evidence=str(evidence),status='starting',passed=False,lease=lease)
    write(evidence/'harness-before.json',harness_before)
    write(evidence/'core-code-admission.json',dict(explicit_checkout_eol=opt.allow_checkout_eol,files=core_admission,final_source='Exact committed Git blobs, not normalized working files'))
    def save():write(evidence/'state.json',state)
    save();env=os.environ.copy();env.update(HYBRID_GODOT=str(GODOT),HYBRID_PYTHON=str(PYTHON),HYBRID_FFMPEG=str(FFMPEG),HYBRID_SOURCEIO=str(SOURCEIO),PYTHONDONTWRITEBYTECODE='1')
    def invoke(label,args,cwd,timeout):
        write(evidence/(label+'-command.json'),args);state['status']=label;save()
        child=subprocess.Popen(args,cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',errors='replace',creationflags=subprocess.CREATE_NO_WINDOW)
        timed_out=False
        try:out,err=child.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:timed_out=True;child.kill();out,err=child.communicate()
        text=out+err;(evidence/(label+'-process.log')).write_text(text,encoding='utf-8')
        need(not timed_out and child.returncode==0,'Owned subprocess failed or timed out: '+label);return text
    pure=module(ROOT/'tools/verify_owner_review.py','owner_review_pure_contract')
    snapshot=module(ROOT/'tools/build_owner_review_snapshot.py','owner_review_snapshot_contract')
    studio=None;studio_before=None;dependencies=None;results=[];error=None;final_package_before={}
    try:
        rows=load(old/'project-copies.json');preflight=[]
        need(len(rows)==6 and {r['name']for r in rows}=={r['name']for r in preparation['packages']} and all(Path(r['name']).name==r['name']and r['name'].endswith('.has')for r in rows),'Exact six protected package names required')
        for row in rows:
            source=guarded(old/row['name'],old);dest=guarded(stage/row['name'],stage);baseline=stamp(source);need(baseline['sha256']==row['sha256'].lower(),'Old protected package changed')
            shutil.copy2(source,dest);need(stamp(dest)==baseline and stamp(source)==baseline,'Exact initial package copy failed')
            preflight.append(dict(name=row['name'],**baseline,**package_readback(dest),source_unchanged=True,new_copy_and_original_hash_size_ns_mtime_preserved=True))
        write(stage/'project-copies.json',rows);write(stage/'project-package-verification.json',dict(format='has_private_review_package_checks_1',fresh_crc_sha_readback=True,projects=preflight))
        invoke('stage-build',[str(PYTHON),'-B',str(ROOT/'tools/build_owner_review_snapshot.py'),'--output',str(stage),'--revision',opt.revision],ROOT,900)
        built=load(stage/'source-snapshot-verification.json');need(built['source_mode']=='git_revision'and built['source_commit']==opt.revision,'Builder source revision differs')
        final.mkdir();studio=final/'Studio';studio.mkdir();dependencies=final/'Dependencies'/SOURCEIO.name;dependencies.mkdir(parents=True)
        for name,digest in built['source_hashes'].items():
            source=guarded(stage/'Studio'/name,stage/'Studio');dest=snapshot.safe_destination(studio,name);need(sha(source)==digest,'Staged Git blob changed')
            dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest);need(sha(dest)==digest,'Final Git blob copy differs')
        shutil.copy2(stage/'Studio/override.cfg',studio/'override.cfg')
        for name,expected in sourceio_before.items():
            source=guarded(SOURCEIO/name,SOURCEIO);dest=guarded(dependencies/name,dependencies);need(stamp(source)==expected,'Shared SourceIO file changed')
            dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest);need(stamp(dest)==expected,'Final SourceIO copy differs')
        final_preflight=[]
        for row in rows:
            source=guarded(stage/row['name'],stage);dest=guarded(final/row['name'],final);expected=stamp(source);shutil.copy2(source,dest);need(stamp(dest)==expected,'Final package copy differs')
            final_preflight.append(dict(name=row['name'],**expected,**package_readback(dest),source_unchanged=True,new_copy_and_original_hash_size_ns_mtime_preserved=True))
        write(final/'project-copies.json',rows);write(final/'project-package-verification.json',dict(format='has_private_review_package_checks_1',fresh_crc_sha_readback=True,projects=final_preflight))
        final_package_before={row['name']:stamp(final/row['name'])for row in rows}
        write(evidence/'final-package-before.json',final_package_before)
        write(final/'source-snapshot-verification-stage.json',built);write(final/'Dependencies/sourceio-file-index.json',dict(version='fe24260b97ac03b899d9b5d4f0fd7b34772f3647',files=sourceio_before,license_retained=True,existing_approved_runtime_copy=True,no_install_or_download=True))
        env['HYBRID_SOURCEIO']=str(dependencies)
        runner=module(studio/'run.py','final_owner_review_runner');need(runner.ROOT.resolve()==studio.resolve(),'Final runner root differs')
        studio_before=source_map(studio);write(evidence/'source-before.json',studio_before)
        def private(label,scene,request,case,timeout=220):
            case.mkdir(parents=True,exist_ok=True)
            previous=os.environ.get('HYBRID_GODOT')
            try:
                os.environ['HYBRID_GODOT']=str(GODOT)
                args=runner.command(extra=[str(scene),'--audio-driver','Dummy','--log-file',str(case/'engine.log'),'--',str(request)])
            finally:
                if previous is None:os.environ.pop('HYBRID_GODOT',None)
                else:os.environ['HYBRID_GODOT']=previous
            need(args.count('--receipt')==1 and Path(args[0]).resolve()==PYTHONW.resolve()and Path(args[1]).resolve()==(studio/'tools/private_desktop.py').resolve(),'No approved final private launcher')
            need(Path(args[args.index('--')+1]).resolve()==GODOT.resolve()and args.count('--path')==1 and Path(args[args.index('--path')+1]).resolve()==studio.resolve()and '--script'not in args,'Final engine/root/ordinary scene startup differs')
            args[args.index('--receipt')+1]=str(case/'private-receipt.json');text=invoke(label,args,studio,timeout)
            text+='\n'+(case/'engine.log').read_text(encoding='utf-8',errors='replace');need(not any(m in text for m in BAD),'Final replay log has error/warning markers: '+label)
            need(('CURRENT_REVIEW_STARTUP 'if label=='final-home'else'OWNER_REVIEW_REPLAY ')in text,'Final startup/replay completion marker is absent')
            r=load(case/'private-receipt.json');need(r.get('exit')==0 and all(r.get(k)is True for k in('private_window_seen','child_desktop_confirmed','job_closed','desktop_closed'))and all(r.get(k)is False for k in('foreground_child_observed','desktop_switch_requested')),'Final private receipt is not clean')
            return r
        home=evidence/'home';home.mkdir();home_result=home/'source-snapshot-startup.json'
        home_receipt=private('final-home','res://tests/current_candidate_startup.tscn',home_result,home)
        startup=load(home_result);need(startup['home_visible']and startup['simple']and startup['empty']and built['profile']in startup['profile']and not startup['recovery']['restored']and not startup['recovery']['cancelled'],'Final normal Home/Simple startup differs')
        copied=dict(built,target=str(studio),normal_startup=startup,private_receipt=home_receipt,source_mode_detail='Exact verified relocation of the committed Git-blob snapshot; final-path startup is fresh',relocated_from=str(stage))
        write(final/'source-snapshot-verification.json',copied)
        for index,row in enumerate(rows):
            case=evidence/('%02d-%s'%(index+1,Path(row['name']).stem.replace(' ','-').lower()));case.mkdir()
            package=final/row['name'];before_package=stamp(package);expected=pure.metadata(package);write(case/'expected.json',expected)
            request=case/'request.json';write(request,dict(format='has_owner_review_replay_request_1',package=str(package).replace('\\','/'),folder=str(case).replace('\\','/'),result=str(case/'result.json').replace('\\','/')))
            scene=case/'replay.tscn';scene.write_text('[gd_scene load_steps=2 format=3]\n[ext_resource type="Script" path='+json.dumps(str(studio/'tests/owner_review_replay.gd').replace('\\','/'))+' id="1"]\n[node name="OwnerReviewReplay" type="Node"]\nscript=ExtResource("1")\n',encoding='utf-8')
            receipt=private('final-'+str(index+1),scene,request,case);observed=load(case/'result.json')
            need(observed['failures']==0 and Path(observed['project_root']).resolve()==studio.resolve()and built['profile']in observed['profile'],'Final replay/source/profile differs')
            normal=observed['normal_startup'];need(normal['signal_seen']and normal['home_visible']and normal['empty']and normal['simple']and not normal['result']['restored']and not normal['result']['cancelled'],'Final replay did not take ordinary fresh Home startup')
            actual_cache=guarded(Path(observed['project_folder']),case/'has-cache');need(actual_cache.is_dir(),'Final replay cache is absent')
            differences={phase:pure.compare(expected,load(case/('observed-'+phase+'.json')))for phase in('before','after')};write(case/'state-comparison.json',dict(contract='Unchanged schema4 compare: exact IDs/keys/order/bools; finite numeric1e-12absolute only; explicit portable/raster normalization',differences=differences))
            need(not any(differences.values())and stamp(package)==before_package,'Final saved state/package changed')
            item=dict(name=row['name'],checks=len(observed['checks']),failures=0,passed=True,case=str(case),private_receipt=receipt);results.append(item);write(case/'verification.json',item)
        need(len(results)==6 and sum(r['checks']for r in results)==129,'Expected all six unchanged129 replay predicates')
        for row in rows:
            lines=['@echo off','setlocal','set "HYBRID_PYTHON='+str(PYTHON)+'"','set "HYBRID_GODOT='+str(GODOT)+'"','set "HYBRID_FFMPEG='+str(FFMPEG)+'"','set "HYBRID_SOURCEIO=%~dp0Dependencies\\'+SOURCEIO.name+'"','start "" "'+str(PYTHONW)+'" "%~dp0Studio\\launch.pyw" "%~dp0'+row['name']+'"']
            (final/('Open '+Path(row['name']).stem+'.bat')).write_bytes(('\r\n'.join(lines)+'\r\n').encode('utf-8'))
        lines=lines[:-1]+['start "" "'+str(PYTHONW)+'" "%~dp0Studio\\launch.pyw"'];(final/'Start review.bat').write_bytes(('\r\n'.join(lines)+'\r\n').encode('utf-8'))
        guide=(BASE/'README.template.md').read_text().replace('{{REVISION}}',opt.revision).replace('{{CHECKS}}','129');(final/'README.md').write_text(guide,encoding='utf-8')
        state['status']='passed';state['passed']=True
    except Exception as exc:error=type(exc).__name__+': '+str(exc);state['status']='failed';state['passed']=False
    finally:
        state['error']=error;state['results']=results
        probe_errors={}
        def probe(name,check):
            try:state[name]=bool(check())
            except Exception as exc:state[name]=False;probe_errors[name]=type(exc).__name__+': '+str(exc)
        probe('protected_old_review_unchanged',lambda:all(stamp(old/name)==value for name,value in protected_before.items()))
        probe('protected_old_studio_source_unchanged',lambda:source_map(old/'Studio')==old_source_before)
        probe('all_final_packages_unchanged',lambda:len(final_package_before)==6 and all(stamp(final/name)==value for name,value in final_package_before.items()))
        probe('harness_unchanged',lambda:all(stamp(path)==value for path,value in harness_before.items()))
        probe('original_sourceio_unchanged',lambda:source_map(SOURCEIO)==sourceio_before)
        probe('approved_runtimes_unchanged',lambda:runtime_map()==runtimes)
        probe('final_source_unchanged',lambda:studio_before is not None and source_map(studio)==studio_before)
        probe('final_sourceio_exact',lambda:dependencies is not None and source_map(dependencies)==sourceio_before)
        state['passed']=state['passed']and all(state[k]for k in('protected_old_review_unchanged','protected_old_studio_source_unchanged','all_final_packages_unchanged','harness_unchanged','original_sourceio_unchanged','approved_runtimes_unchanged','final_source_unchanged','final_sourceio_exact'))
        if not state['passed']:state['status']='failed'
        state['preservation_probe_errors']=probe_errors
        state['installation_replaced']=False;state['private_art_uploaded']=False;state['artist_device_install_acceptance']=False
        if studio_before is not None:
            try:write(evidence/'source-after.json',source_map(studio))
            except Exception as exc:write(evidence/'source-after-error.json',dict(error=type(exc).__name__+': '+str(exc)))
        if final_package_before:
            try:write(evidence/'final-package-after.json',{name:stamp(final/name)for name in final_package_before})
            except Exception as exc:write(evidence/'final-package-after-error.json',dict(error=type(exc).__name__+': '+str(exc)))
        try:write(evidence/'harness-after.json',{str(path):stamp(path)for path in harness_paths})
        except Exception as exc:write(evidence/'harness-after-error.json',dict(error=type(exc).__name__+': '+str(exc)))
        write(evidence/'verification.json',state);save()
    print(json.dumps(dict(passed=state['passed'],final=str(final),verification=str(evidence/'verification.json')),indent=2))
    raise SystemExit(0 if state['passed']else 1)

if __name__=='__main__':main()
