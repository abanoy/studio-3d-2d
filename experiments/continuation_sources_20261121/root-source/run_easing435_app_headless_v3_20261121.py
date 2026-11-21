"""Actual app transaction controls on a frozen proposed port; headless only."""
from pathlib import Path
import hashlib,importlib.util,json,os,subprocess,time

ROOT=Path(__file__).resolve().parents[1]
PREP=ROOT/'output/source-keyframe-easing435-undo-fix-prep-20261121'
STAGE=ROOT.parent/('has-easing435-app-cpu-'+str(time.time_ns()))
REV='435dc02426a7cdd313e43fe674c9008520845428'
ENGINE=Path('C:/a/tools/Godot/Godot_v4.6-stable_win64.exe')
def need(ok,msg):
    if not ok:raise RuntimeError(msg)
def pin(path):
    a=path.stat();raw=path.read_bytes();b=path.stat()
    stamp=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_nlink)
    need(stamp(a)==stamp(b),'Changing source')
    return {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'identity':list(stamp(a))}
original_env=dict(os.environ);sources={}
pins=json.loads((PREP/'SOURCE_PINS.json').read_bytes())
for row in pins['files']:
    path=PREP/row['path'];value=pin(path)
    need(value['bytes']==row['bytes'] and value['sha256']==row['sha256'],'Frozen port differs')
    sources[path]=value
fixture=ROOT/'output/easing435_app_headless_v2.gd';sources[fixture]=pin(fixture)
need(pin(ENGINE)['sha256']=='63913d01be2c2d1f929b4a626f5347117126b34e9c64cbf350ea9f35a9657ebf','Wrong engine')
spec=importlib.util.spec_from_file_location('easing_cpu_snapshot',ROOT/'tools/build_owner_review_snapshot.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
STAGE.mkdir(exist_ok=False);runtime=STAGE/'Studio'
revision,base_hashes=builder.freeze_source(ROOT,runtime,REV,runtime_scope=True)
need(revision==REV,'Wrong revision')
for path in (PREP/'payload').rglob('*'):
    if path.is_file():
        target=runtime/path.relative_to(PREP/'payload');target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(path.read_bytes())
(runtime/'tests/easing435_app_headless.gd').write_bytes(fixture.read_bytes())
(runtime/'override.cfg').write_text('[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name="HAS easing CPU '+str(time.time_ns())+'"\n',encoding='utf-8')
runtime_sources={path:pin(path) for path in runtime.rglob('*') if path.is_file()}
cases=[];error=None
try:
    for theme in ('classic','neon'):
        for workspace in ('simple','advanced'):
            case=STAGE/(theme+'-'+workspace);case.mkdir()
            env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
            for key,leaf in [('APPDATA','Roaming'),('LOCALAPPDATA','Local'),('TEMP','Temp'),('TMP','Temp')]:
                path=case/'User'/leaf;path.mkdir(parents=True,exist_ok=True);env[key]=str(path)
            args=[str(ENGINE),'--headless','--path',str(runtime),'--audio-driver','Dummy','--log-file',str(case/'engine.log'),
                  '--script','res://tests/easing435_app_headless.gd','--',str(case)]
            if theme=='classic':args.append('--classic')
            if workspace=='advanced':args.append('--advanced')
            started=time.time_ns()
            with (case/'stdout.log').open('wb') as out,(case/'stderr.log').open('wb') as err:
                process=subprocess.Popen(args,cwd=runtime,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
                try:process.wait(timeout=45)
                except subprocess.TimeoutExpired:process.kill();process.wait();raise
            row={'name':case.name,'pid':process.pid,'exit':process.returncode,'child_reaped':process.poll() is not None,'seconds':(time.time_ns()-started)/1e9};cases.append(row)
            raw=(case/'stdout.log').read_text(encoding='utf-8',errors='replace')
            log=raw+(case/'stderr.log').read_text(encoding='utf-8',errors='replace')+(case/'engine.log').read_text(encoding='utf-8',errors='replace')
            need(process.returncode==0 and not any(x in log for x in ('ERROR:','SCRIPT ERROR','FAIL ','ObjectDB instances leaked')),'Actual headless app case failed: '+case.name)
            marker='EASING435_APP_HEADLESS '
            lines=[line[len(marker):] for line in raw.splitlines() if line.startswith(marker)]
            need(len(lines)==1,'Missing result marker')
            result=json.loads(lines[0]);row['result']=result
            need(type(result['checks']) is int and result['checks']==24 and type(result['failures']) is int and result['failures']==0,'Wrong assertion count/failures')
            need(sum(line.startswith('PASS ') for line in raw.splitlines())==24,'Wrong PASS line count')
except BaseException as exc:error=repr(exc)
finally:
    preserved=all(pin(p)==v for p,v in {**sources,**runtime_sources}.items())
    result={'format':'has_easing435_actual_app_headless_1','status':'PASS' if error is None and preserved and original_env==dict(os.environ) else 'FAIL',
      'cases':cases,'error':error,'checks':sum(r.get('result',{}).get('checks',0) for r in cases),
      'source_revision':REV,'sources_preserved':preserved,'parent_environment_preserved':original_env==dict(os.environ),
      'graphics_or_native_jobs_started':False,'application_adopted':False,'pixels_export_cold_save_qualified':False,
      'source_port_pins_sha256':hashlib.sha256((PREP/'SOURCE_PINS.json').read_bytes()).hexdigest(),
      'fixture_sha256':sources[fixture]['sha256'],'source_file_count':len(runtime_sources)}
    (STAGE/'PUBLIC_RESULT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    (STAGE/'SOURCE_INPUTS.json').write_text(json.dumps([{'path':str(p),**v} for p,v in {**sources,**runtime_sources}.items()],indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2));print(str(STAGE),flush=True)
need(result['status']=='PASS','Retained actual app failure; port not adopted')
