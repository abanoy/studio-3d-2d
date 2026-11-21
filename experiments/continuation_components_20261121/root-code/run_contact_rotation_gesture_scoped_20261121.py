"""Qualify only the proposed contact-test correction on an owned c315 snapshot."""
from pathlib import Path
import hashlib,importlib.util,json,os,subprocess,sys,time
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output'
PREP=OUT/'source-contact-rotation-gesture-v2-prep-20261121'
HELP=OUT/'source-miku-contact-c315-1103-successor-prep-20261121'
REV='c31576d0c1d84030d51ec886f2f3976a60a70c7b'
def load(name,path,digest):
 raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==digest
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
H=load('_contact_scoped_ownership',HELP/'qualified_helpers.py','990c37ddca7b1301613f5efc5a7e5a30ce2723369112ef274ee78d2d4dc34087')
Q=load('_contact_scoped_private_case',HELP/'qualified_ui_host.py','dfb0cf83cef6dc455d5da9f1c1631f1f0ee053b6e4a646c9045e90e7e9967a3e')
full_path=ROOT/'experiments/reference_body_20261120/run_full.py'
F=load('_contact_scoped_snapshot',full_path,'74231a770fa282aee11326b05661063c2662c261bad33c1c58d63b696a018f34')
assert H.ROOT==ROOT and H.head()==REV
pins=H.read(PREP/'SOURCE_PINS.json');assert H.sha(pins)=='5c8eef061c8e025197899db01292a3d7b5f1a21a6f7c0246e5565c11576a6f51'
for row in H.parse(pins)['files']:H.read(PREP/row['path'],row['bytes'],row['sha256'])
before=F.snapshot();assert len(before)==1103
runtime={'python':sys.executable,'pythonw':str(Path(sys.executable).with_name('pythonw.exe')),
 'godot':'C:/a/tools/Godot/Godot_v4.6-stable_win64.exe','ffmpeg':'C:/Program Files/ffmpeg/bin/ffmpeg.exe','ffprobe':'C:/Program Files/ffmpeg/bin/ffprobe.exe'}
for path in runtime.values():H.read(Path(path))
assert H.sha(H.read(Path(runtime['godot'])))=='63913d01be2c2d1f929b4a626f5347117126b34e9c64cbf350ea9f35a9657ebf'
source_report=ROOT.parent/'has-import-off-full-20261121-c31576d/output/contact-persistence-verification.json'
reference=Path(H.parse(H.read(source_report))['writer']['packed'])
assert reference.resolve(strict=True).is_relative_to(ROOT.parent/'has-import-off-full-20261121-c31576d/output')
reference_raw=H.read(reference,limit=64*1024*1024)
stage=ROOT.parent/('has-contact-rotation-scoped-'+str(time.time_ns()));stage.mkdir();studio=stage/'Studio'
builder=load('_contact_scoped_builder',ROOT/'tools/build_owner_review_snapshot.py',before['tools/build_owner_review_snapshot.py']['sha256'])
revision,base=builder.freeze_source(ROOT,studio,REV,runtime_scope=True);assert revision==REV and len(base)==1106
for path in (PREP/'payload').rglob('*'):
 if path.is_file():target=studio/path.relative_to(PREP/'payload');target.write_bytes(H.read(path))
H.new(studio/'override.cfg',b'[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name="HAS contact scope initial"\n')
for path in studio.rglob('*'):
 if path.is_file():H.read(path)
(studio/'output/private-desktop').mkdir(parents=True);(stage/'Verification').mkdir();(stage/'Data').mkdir()
copy=stage/'Data/native-contacts.has';H.new(copy,reference_raw)
case_data=stage/'Data/contact-transform';case_data.mkdir()
result={'format':'has_contact_rotation_scoped_root_1','status':'FAIL','baseline_revision':REV,'purpose':'Existing planted-foot regression correction only',
 'source_manifest_sha256':H.sha(pins),'cases':[],'jobs':[],'Full_qualification_claimed':False,'application_changed':False,
 'original_reference_sha256':H.sha(reference_raw),'protected_original_reference':str(reference),'stage':str(stage)}
parent=dict(os.environ);primary=None
try:
 Q.run_case(H,stage,studio,runtime,result,'contact-transform','tests/contact_transform_smoke.gd',[case_data,copy],
            'CONTACT_TRANSFORM ',129,graphical=True,timeout=200,report=case_data/'result.json')
 value=result['cases'][0]['result'];assert len(value['native_reports'])==5 and all(r['checks']==25 and r['failures']==0 for r in value['native_reports'])
 probe_case=stage/'Verification/movie-probe';probe_case.mkdir()
 argv=[runtime['ffprobe'],'-v','error','-count_frames','-show_streams','-show_format','-of','json',value['movie']]
 with (probe_case/'stdout.json').open('xb') as out,(probe_case/'stderr.log').open('xb') as err:
  proc=subprocess.Popen(argv,cwd=studio,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
  try:code=proc.wait(timeout=30)
  finally:
   if proc.poll() is None:proc.kill();proc.wait(timeout=5)
 result['probe']={'pid':proc.pid,'exit':code,'reaped':proc.poll() is not None,'hidden':True}
 assert code==0 and not (probe_case/'stderr.log').read_bytes()
 metadata=H.parse(H.read(probe_case/'stdout.json'));video=next(r for r in metadata['streams'] if r['codec_type']=='video')
 assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48')
 assert abs(float(metadata['format']['duration'])-2)<.001
 result['status']='PASS';result['checks']=129;result['native_contexts']=5
except BaseException as error:primary=error;result['error_type']=type(error).__name__;result['error']=str(error)
finally:
 for process,row in H.OWNED:row['reaped']=H.reap(process)
 result['all_owned_launchers_reaped']=all(row['reaped'] for process,row in H.OWNED)
 result['all_private_jobs_closed_isolated']=all(r.get('private_job_closed') is True and r.get('desktop_closed') is True
  and r.get('child_desktop_observed') is True and r.get('foreground_child_observed') is False for r in result['jobs'])
 result['parent_environment_unchanged']=dict(os.environ)==parent
 result['main_source_and_head_unchanged']=F.snapshot()==before and H.head()==REV
 failures=H.preserve();result['all_admitted_inputs_preserved']=not failures;result['preservation_failures']=failures
 if not all(result[k] for k in ('all_owned_launchers_reaped','all_private_jobs_closed_isolated','parent_environment_unchanged','main_source_and_head_unchanged','all_admitted_inputs_preserved')):result['status']='FAIL'
 H.json_new(stage/'PRIVATE_RESULT.json',result)
 public={k:v for k,v in result.items() if k not in ('cases','jobs','preservation_failures')}
 public['cases']=[{k:v for k,v in row.items() if k in ('name','status','checks','expected_checks','graphical')} for row in result['cases']]
 public['preservation_failure_count']=len(failures);public['private_job_count']=len(result['jobs'])
 H.json_new(stage/'PUBLIC_RESULT.json',public);print(json.dumps(public),flush=True)
raise SystemExit(0 if primary is None and result['status']=='PASS' else 1)
