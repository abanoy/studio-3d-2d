from pathlib import Path
import hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output'
PREP=OUT/'source-posed-head-native-2f1acbd-1109-qualification-prep-20261121'
FULL=ROOT.parent/'has-import-info-full-20261121-2f1acbd';RUN=FULL/'output/windows-reference-body-1795270518404649600';OUTER=FULL/'output/root-full-launch-1795270518224140000'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
postflight=OUT/'IMPORT_INFO_FULL183_ROOT_POSTFLIGHT_20261121.json';p=json.loads(postflight.read_bytes());assert p['status']=='PASS' and p['canonical_groups']==183 and p['functional_sources']==1109
assert json.loads((OUTER/'completion.json').read_bytes())['child_reaped'] is True
assert sha(PREP/'SOURCE_PINS.json')=='72fc1f2f6626db08bb23e3330f39401b0cf0202dc43df01b433342e16d2e5402'
for row in json.loads((PREP/'SOURCE_PINS.json').read_bytes())['files']:assert (PREP/row['path']).stat().st_size==row['bytes'] and sha(PREP/row['path'])==row['sha256']
script=PREP/'run_posed_head_controls.py';assert sha(script)=='8df403b1edf2a99bfac5af8b397fbca677455342f5e6aff2da1b1b8f4ed57e41'
argv=[sys.executable,'-I','-S','-B','-u',str(script),'--self-sha256',sha(script),'--expected-head',p['revision'],'--full-folder',str(RUN),'--full-completion-sha256',sha(RUN/'completion.json'),'--full-source-sha256',sha(RUN/'source-before.json'),'--full-report-sha256',sha(FULL/'output/verification.json'),'--full-outer-folder',str(OUTER),'--full-outer-launch-sha256',sha(OUTER/'launch.json'),'--full-outer-completion-sha256',sha(OUTER/'completion.json'),'--full-postflight-sha256',sha(postflight),'--root-exclusive-lane-confirmed']
stage=OUT/('root-face114-launch-'+str(time.time_ns()));stage.mkdir();env=dict(os.environ);env['PYTHONDONTWRITEBYTECODE']='1';start=time.time_ns()
with (stage/'stdout.log').open('xb') as out,(stage/'stderr.log').open('xb') as err:
 child=subprocess.Popen(argv,cwd=ROOT,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
 (stage/'launch.json').write_text(json.dumps({'argv':argv,'pid':child.pid,'started_ns':start,'source_packet_sha256':sha(PREP/'SOURCE_PINS.json'),'only_current_graphics_owner':True},indent=2)+'\n');print(json.dumps({'stage':str(stage),'pid':child.pid,'scope':'Face114/private16images'}),flush=True)
 code=child.wait()
(stage/'completion.json').write_text(json.dumps({'exit':code,'pid':child.pid,'child_reaped':child.poll() is not None,'seconds':(time.time_ns()-start)/1e9},indent=2)+'\n')
print(json.dumps({'exit':code,'stage':str(stage),'stdout':(stage/'stdout.log').read_text()}),flush=True)
raise SystemExit(code)
