"""Qualify frozen synthetic easing transactions; no app hooks or graphics."""
from pathlib import Path
import hashlib,json,os,stat,subprocess,time

ROOT=Path(__file__).resolve().parents[1]
PREP=ROOT/'output/source-keyframe-easing-editor-prep-20261121'
ENGINE=Path('C:/a/tools/Godot/Godot_v4.6-stable_win64.exe')
STAGE=ROOT.parent/('has-easing-headless-'+str(time.time_ns()))
def need(ok,msg):
    if not ok: raise RuntimeError(msg)
def pin(path):
    s=path.stat();raw=path.read_bytes();t=path.stat()
    identity=lambda v:(v.st_dev,v.st_ino,v.st_size,v.st_mtime_ns,v.st_nlink)
    need(identity(s)==identity(t),'Input changed while read')
    return {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'identity':list(identity(s))}
before_env=dict(os.environ)
manifest=json.loads((PREP/'SOURCE_PINS.json').read_bytes())
sources={}
for row in manifest['files']:
    source=PREP/row['path'];p=pin(source)
    need(p['bytes']==row['bytes'] and p['sha256']==row['sha256'],'Frozen packet changed: '+row['path'])
    sources[source]=p
need(pin(ENGINE)['sha256']=='63913d01be2c2d1f929b4a626f5347117126b34e9c64cbf350ea9f35a9657ebf','Engine differs')
timeline=ROOT/'src/timeline.gd';sources[timeline]=pin(timeline)
need(sources[timeline]['sha256']=='2cd69b4ae0b2fe546064bd318301fc1c7cd6ac8f7c9cadf91730a473ee36f835','Timeline baseline differs')
STAGE.mkdir(exist_ok=False)
runtime=STAGE/'Studio';runtime.mkdir()
runtime_sources={}
for source in [PREP/'payload/src/camera_easing_editor.gd',PREP/'payload/src/keyframe_easing.gd',
               PREP/'payload/tests/keyframe_easing_math_unit.gd',PREP/'payload/tests/keyframe_easing_unit.gd',timeline]:
    name=source.relative_to(PREP/'payload').as_posix() if source.is_relative_to(PREP/'payload') else 'src/timeline.gd'
    target=runtime/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes())
    runtime_sources[target]=pin(target)
(runtime/'project.godot').write_text('config_version=5\n[application]\nconfig/name="HAS CPU easing qualification"\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n',encoding='utf-8')
runtime_sources[runtime/'project.godot']=pin(runtime/'project.godot')
env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
for key,leaf in [('APPDATA','Roaming'),('LOCALAPPDATA','Local'),('TEMP','Temp'),('TMP','Temp')]:
    path=STAGE/'User'/leaf;path.mkdir(parents=True,exist_ok=True);env[key]=str(path)
cases=[];error=None
try:
    for name,script,marker,count in [
       ('math','keyframe_easing_math_unit.gd','KEYFRAME_EASING_MATH_UNIT ',24),
       ('editor','keyframe_easing_unit.gd','KEYFRAME_EASING_EDITOR_UNIT ',45)]:
        folder=STAGE/name;folder.mkdir()
        args=[str(ENGINE),'--headless','--path',str(runtime),'--audio-driver','Dummy',
              '--log-file',str(folder/'engine.log'),'--script','res://tests/'+script]
        started=time.time_ns()
        with (folder/'stdout.log').open('wb') as out,(folder/'stderr.log').open('wb') as err:
            process=subprocess.Popen(args,cwd=runtime,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
            try: process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                process.kill();process.wait();raise
        log=(folder/'stdout.log').read_text(encoding='utf-8',errors='replace')+(folder/'stderr.log').read_text(encoding='utf-8',errors='replace')+(folder/'engine.log').read_text(encoding='utf-8',errors='replace')
        row={'name':name,'pid':process.pid,'exit':process.returncode,'child_reaped':process.poll() is not None,'seconds':(time.time_ns()-started)/1e9}
        cases.append(row)
        need(process.returncode==0 and not any(x in log for x in ('ERROR:','SCRIPT ERROR','SHADER ERROR','FAIL ','ObjectDB instances leaked')),'CPU case failed: '+name)
        raw=(folder/'stdout.log').read_text(encoding='utf-8',errors='replace')
        lines=[line[len(marker):] for line in raw.splitlines() if line.startswith(marker)]
        need(len(lines)==1,'Missing/duplicate result marker')
        result=json.loads(lines[0]);row['result']=result
        need(type(result['checks']) is int and result['checks']==count and type(result['failures']) is int and result['failures']==0,'Unexpected check count/failure')
        need(sum(line.startswith('PASS ') for line in raw.splitlines())==count,'Actual PASS line count differs')
except BaseException as exc:
    error=repr(exc)
finally:
    preserved=all(pin(path)==value for path,value in {**sources,**runtime_sources}.items())
    result={'format':'has_easing_root_synthetic_headless_1','status':'PASS' if error is None and preserved and dict(os.environ)==before_env else 'FAIL',
      'cases':cases,'checks':sum(r.get('result',{}).get('checks',0) for r in cases),
      'error':error,'inputs_and_runtime_sources_preserved':preserved,'parent_environment_preserved':dict(os.environ)==before_env,
      'application_adopted':False,'actual_app_undo_qualified':False,'graphics_or_native_jobs_started':False,
      'full_source_modified':False,'source_manifest_sha256':hashlib.sha256((PREP/'SOURCE_PINS.json').read_bytes()).hexdigest(),
      'source_and_runtime_inputs':[{'path':str(p),**v} for p,v in {**sources,**runtime_sources}.items()]}
    (STAGE/'PUBLIC_RESULT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='source_and_runtime_inputs'},indent=2))
    print(str(STAGE),flush=True)
need(result['status']=='PASS','See retained failure evidence')
