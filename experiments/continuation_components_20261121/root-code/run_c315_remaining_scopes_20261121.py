"""Run remaining independent canonical wrappers; never fabricate a Full report."""
from pathlib import Path
import hashlib,importlib.util,json,os,subprocess,sys,time
sys.dont_write_bytecode=True
CONTROL=Path(__file__).resolve().parent
ROOT=CONTROL.parent.parent/'has-import-off-full-20261121-c31576d'
REV='c31576d0c1d84030d51ec886f2f3976a60a70c7b'
spec=importlib.util.spec_from_file_location('_remaining_source_snapshot',ROOT/'experiments/reference_body_20261120/run_full.py')
F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)
def git(*v):return subprocess.check_output(['git','-c','core.autocrlf=false',*v],cwd=ROOT).decode().strip()
assert git('rev-parse','HEAD')==REV
failed=json.loads((ROOT/'output/windows-reference-body-1795260488673286600/completion.json').read_bytes())
assert failed['exit']==1 and failed['all_private_jobs_isolated_closed'] and failed['child_reaped']
before=F.snapshot();assert len(before)==1103 and {k:v['git_sha1'] for k,v in before.items()}==F.committed_sources(REV)
prior=F.receipts();folder=ROOT/'output'/('remaining-scopes-'+str(time.time_ns()));folder.mkdir()
(folder/'source-before.json').write_text(json.dumps(before,indent=2)+'\n')
cases=[
 ('contact_viewport','verify_contact_viewport.py','contact-viewport-verification.json',340),
 ('multi_audio','verify_multi_audio.py','multi-audio-verification.json',1000),
 ('project_duration','verify_project_duration.py','project-duration-verification.json',1000),
 ('motion_assist','verify_motion_assist.py','motion-assist-verification.json',90),
 ('motion_tracks','verify_motion_assist_tracks.py','motion-assist-tracks-verification.json',90),
 ('motion_native_preview','verify_motion_assist_native.py','motion-assist-native-verification.json',240),
 ('motion_model','verify_motion_animation.py','motion-animation-unit-verification.json',90),
 ('motion_editor','verify_motion_animation_app.py','motion-animation-app-verification.json',360),
 ('opacity','verify_opacity.py','opacity-verification.json',220),
 ('brush_opacity','verify_brush_opacity.py','brush-opacity-verification.json',380),
 ('brush_pressure','verify_brush_pressure.py','brush-pressure-verification.json',400),
 ('layers','verify_layers.py','layers-verification.json',200),
 ('onion','verify_onion.py','onion-verification.json',200),
 ('fill','verify_fill.py','fill-verification.json',240),
 ('fill_gaps','verify_fill_gaps.py','fill-gaps-verification.json',500),
 ('fill_expand','verify_fill_expand.py','fill-expand-verification.json',500),
 ('fill_connections','verify_fill_connections.py','fill-connections-verification.json',500),
 ('palette','verify_palette.py','palette-verification.json',500),
 ('drawing_history','verify_drawing_history.py','drawing-history-verification.json',400),
 ('drawing_selection','verify_drawing_selection.py','drawing-selection-verification.json',500),
 ('drawing_transform','verify_drawing_transform.py','drawing-transform-verification.json',600),
 ('recovery_identity','verify_recovery_identity.py','recovery-identity-verification.json',90),
 ('recovery_startup','verify_recovery_startup.py','recovery-startup-verification.json',300),
 ('recovery_history','verify_recovery_history.py','recovery-history-verification.json',300),
 ('recovery_schedule','verify_recovery_schedule.py','recovery-schedule-verification.json',180),
 ('recovery_preview','verify_recovery_preview.py','recovery-preview-verification.json',180),
 ('home','verify_home.py','home-verification.json',240),
 ('tutorials','verify_tutorials.py','tutorials-verification.json',260),
 ('first_movie','verify_first_movie.py','first-movie-verification.json',300)]
assert len(cases)==29
parent=dict(os.environ);result={'format':'has_c315_remaining_scopes_1','status':'FAIL','revision':REV,'cases':[],
 'expected_wrapper_count':29,'failed_Full_reclassified':False,'whole_verifier_pass_claimed':False,'human_device_acceptance_claimed':False}
started=time.time_ns();error=None
try:
 for name,script,report_name,timeout in cases:
  case=folder/name;case.mkdir();env=dict(parent)
  for key in tuple(env):
   if key.startswith('HYBRID_'):env.pop(key)
  env.update(PYTHONDONTWRITEBYTECODE='1',HYBRID_PYTHON=sys.executable,HYBRID_GODOT='C:/a/tools/Godot/Godot_v4.6-stable_win64.exe',
   HYBRID_FFMPEG='C:/Program Files/ffmpeg/bin/ffmpeg.exe',HYBRID_NATIVE_FIXTURES='C:/a/Programming/cloudflare/has-acceptance-session-20261111/output',
   HYBRID_HECATIA_KRA='C:/a/Programming/HAS/hecatia.kra',HYBRID_NATIVE_INPUTS='C:/a/dump',
   HYBRID_SOURCEIO='C:/a/Programming/cloudflare/has-neon-review-20261116-c2d52ff/output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647')
  for key,leaf in [('APPDATA','Roaming'),('LOCALAPPDATA','Local'),('TEMP','Temp'),('TMP','Temp')]:
   path=case/'User'/leaf;path.mkdir(parents=True,exist_ok=True);env[key]=str(path)
  begin=time.time_ns()
  with (case/'stdout.log').open('xb') as out,(case/'stderr.log').open('xb') as err:
   child=subprocess.Popen([sys.executable,'-B','-u','tests/'+script],cwd=ROOT,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
   (case/'launch.json').write_text(json.dumps({'pid':child.pid,'script':script,'started_ns':begin,'private_graphics_required':True},indent=2)+'\n')
   print(json.dumps({'case':name,'pid':child.pid,'folder':str(folder)}),flush=True)
   try:code=child.wait(timeout=timeout+30)
   finally:
    if child.poll() is None:child.kill();child.wait(timeout=5)
  row={'name':name,'exit':code,'pid':child.pid,'reaped':child.poll() is not None,'seconds':(time.time_ns()-begin)/1e9};result['cases'].append(row)
  assert code==0,'Wrapper failed: '+name
  report=ROOT/'output'/report_name;assert report.is_file() and report.stat().st_mtime_ns>=begin,'Fresh report required: '+name
  raw=report.read_bytes();value=json.loads(raw);(case/'verification.json').write_bytes(raw);row['report_sha256']=hashlib.sha256(raw).hexdigest()
  assert value.get('failures',0)==0
  if name in ('contact_viewport','motion_editor'):assert value['reader']['failures']==0
  if name=='project_duration':assert len(value['fresh_readers'])==4
  row['status']='PASS';print('PASS remaining '+name,flush=True)
 result['status']='SCOPED_29_WRAPPERS_PASS_NOT_FULL'
except BaseException as exc:error=repr(exc);result['error']=error
finally:
 after=F.snapshot();(folder/'source-after.json').write_text(json.dumps(after,indent=2)+'\n')
 classified=F.classify(prior,F.receipts());(folder/'receipt-provenance.json').write_text(json.dumps(classified,indent=2)+'\n')
 unique={r['value']['desktop']:r for r in classified['current']}
 closed=all(r['value'].get('job_closed') is True and r['value'].get('desktop_closed') is True and r['value'].get('child_desktop_confirmed') is True
  and r['value'].get('foreground_child_observed') is False and r['value'].get('desktop_switch_requested') is False for r in unique.values())
 result.update(functional_source_count=len(before),source_and_head_unchanged=before==after and git('rev-parse','HEAD')==REV,
  parent_environment_unchanged=dict(os.environ)==parent,all_private_jobs_isolated_closed=closed,current_private_jobs=len(unique),
  all_current_private_jobs_exit0=all(r['value']['exit']==0 for r in unique.values()),
  prior_receipts_preserved=not classified['conflicts'] and not classified['changed_original_archives'],
  private_jobs=list(unique.values()),seconds=(time.time_ns()-started)/1e9)
 if error or not all(result[k] for k in ('source_and_head_unchanged','parent_environment_unchanged','all_private_jobs_isolated_closed','all_current_private_jobs_exit0','prior_receipts_preserved')):result['status']='FAIL'
 (folder/'completion.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k not in ('private_jobs','cases')}),flush=True)
raise SystemExit(0 if result['status']=='SCOPED_29_WRAPPERS_PASS_NOT_FULL' else 1)
