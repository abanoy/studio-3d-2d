"""Retain remaining lesson and scenario D private Windows regressions."""
from pathlib import Path
import hashlib,importlib.util,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('off_followup_full_helpers',ROOT/'experiments/reference_body_20261120/run_full.py')
full=importlib.util.module_from_spec(spec);spec.loader.exec_module(full)
def need(ok,msg):
    if not ok:raise RuntimeError(msg)
def git(*args):return subprocess.check_output(['git','-c','core.autocrlf=false',*args],cwd=ROOT).decode().strip()
def receipts():
    return {path.name:hashlib.sha256(path.read_bytes()).hexdigest() for path in (ROOT/'output/private-desktop').glob('*.json')}
need(os.name=='nt' and sys.flags.optimize==0,'Non-optimized Windows Python required')
head=git('rev-parse','HEAD');need(head=='435dc02426a7cdd313e43fe674c9008520845428','Unexpected source epoch')
folder=ROOT/'output'/('import-off-followup-scoped-'+str(time.time_ns()));folder.mkdir()
before=full.snapshot();need(len(before)==1103,'Unexpected functional source membership')
(folder/'source-before.json').write_text(json.dumps(before,indent=2)+'\n',encoding='utf-8')
prior=receipts();parent_env=dict(os.environ)
result={'format':'has_import_off_scenario_d_scoped_1','status':'FAIL','source_context':'main_working_source_snapshot',
 'base_head':head,'functional_sources':1103,'cases':[],'whole_full_claimed':False,'owner_device_or_human_claimed':False}
error=None;began=time.time_ns()
try:
    for name,script,report,extra in [
      ('scenario-d','tests/verify_scenario_d.py',folder/'scenario-d-artifacts/verification.json',['--output',str(folder/'scenario-d-artifacts')])]:
        case=folder/name;case.mkdir(exist_ok=True)
        env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',HYBRID_PYTHON=sys.executable,
          HYBRID_GODOT='C:/a/tools/Godot/Godot_v4.6-stable_win64.exe',
          HYBRID_NATIVE_FIXTURES='C:/a/Programming/cloudflare/has-acceptance-session-20261111/output',
          HYBRID_HECATIA_KRA='C:/a/Programming/HAS/hecatia.kra',
          HYBRID_SOURCEIO='C:/a/Programming/cloudflare/has-neon-review-20261116-c2d52ff/output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647',
          HYBRID_NATIVE_INPUTS='C:/a/dump',HYBRID_FFMPEG='C:/Program Files/ffmpeg/bin/ffmpeg.exe')
        for key,leaf in [('APPDATA','Roaming'),('LOCALAPPDATA','Local'),('TEMP','Temp'),('TMP','Temp')]:
            path=case/'User'/leaf;path.mkdir(parents=True,exist_ok=True);env[key]=str(path)
        argv=[sys.executable,'-B','-u',script,*extra];started=time.time_ns()
        with (case/'stdout.log').open('wb') as out,(case/'stderr.log').open('wb') as err:
            proc=subprocess.Popen(argv,cwd=ROOT,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
            print(json.dumps({'case':name,'pid':proc.pid,'folder':str(folder)}),flush=True)
            try:proc.wait(timeout=1000)
            except subprocess.TimeoutExpired:
                proc.kill();proc.wait();raise
        row={'name':name,'pid':proc.pid,'exit':proc.returncode,'child_reaped':proc.poll() is not None,'seconds':(time.time_ns()-started)/1e9};result['cases'].append(row)
        need(proc.returncode==0,'Scoped wrapper failed: '+name)
        need(report.is_file() and report.stat().st_mtime_ns>=started,'Fresh scoped report missing: '+name)
        raw=report.read_bytes();value=json.loads(raw);(case/'verification.json').write_bytes(raw)
        row['report_sha256']=hashlib.sha256(raw).hexdigest()
        if name=='height':need(value.get('native_import',{}).get('checks')==15 and value['native_import']['failures']==0,'Native height must execute15 checks')
        if name=='scenario-d':need(value['reports']['writer']['checks']==30 and value['reports']['reader']['checks']==4,'ScenarioD must retain30writer+4cold checks')
        print('PASS '+name+' '+str(round(row['seconds'],3))+'s',flush=True)
    result['status']='PASS'
except BaseException as exc:error=repr(exc)
finally:
    after=full.snapshot();(folder/'source-after.json').write_text(json.dumps(after,indent=2)+'\n',encoding='utf-8')
    current=receipts();new=[name for name in current if name not in prior]
    rows=[]
    for name in sorted(new):
        path=ROOT/'output/private-desktop'/name;raw=path.read_bytes();value=json.loads(raw)
        rows.append({'name':name,'sha256':hashlib.sha256(raw).hexdigest(),'value':value})
    closed=all(r['value'].get('job_closed') is True and r['value'].get('desktop_closed') is True
       and r['value'].get('child_desktop_confirmed') is True and r['value'].get('private_window_seen') is True
       and r['value'].get('foreground_child_observed') is False and r['value'].get('desktop_switch_requested') is False for r in rows)
    all_zero=all(r['value'].get('exit')==0 for r in rows)
    result.update(error=error,seconds=(time.time_ns()-began)/1e9,sources_unchanged=before==after,
      head_unchanged=git('rev-parse','HEAD')==head,parent_environment_preserved=parent_env==dict(os.environ),
      prior_receipts_unchanged=all(current.get(name)==digest for name,digest in prior.items()),
      current_private_jobs=len(rows),all_current_private_jobs_isolated_closed=closed,all_current_jobs_exit0=all_zero,private_jobs=rows)
    if error is not None or not all(result[k] for k in ('sources_unchanged','head_unchanged','parent_environment_preserved','prior_receipts_unchanged','all_current_private_jobs_isolated_closed','all_current_jobs_exit0')):
        result['status']='FAIL'
    if result['status']=='PASS':need(len(rows)==2,'Expected two scenario D actual private jobs')
    (folder/'completion.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='private_jobs'},indent=2),flush=True)
need(result['status']=='PASS','See retained scoped failure')
