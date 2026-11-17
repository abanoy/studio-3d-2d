"""Observe unchanged strict runtime checks, then call the unchanged staged builder."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,runpy,sys,time
ROOT=Path(__file__).resolve().parents[2]
READER=ROOT/'experiments/resume_root_20261115/audit_protected_inputs_before_cleanup.py'
PACKET=ROOT/'experiments/normal_boundary_probe_sentinel_20261116'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(READER)=='5be1d34aa6aced8fc112bee3ecadd489be9b7f38ab710553385bfd77ca500d83'
assert sha(PACKET/'INDEX.json')=='a2475b28c03c6b87cc0d98d537433204b9553122a97f1197321455a491e2ef64'
spec=importlib.util.spec_from_file_location('unchanged_protected_identity',READER);reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
lock=json.loads((ROOT/'experiments/replay_audio_fix_20261115/builder/input-lock.json').read_bytes())
rows=[]
def failure(error):
    observed={'error':str(error),'type':type(error).__name__};tb=error.__traceback__
    while tb:
        frame=tb.tb_frame
        if Path(frame.f_code.co_filename).resolve()==READER and frame.f_code.co_name=='identity':
            observed['actual_failure_stamps']={n:list(reader.stamp(frame.f_locals[n])) for n in ('before','opened','after','final') if n in frame.f_locals}
        tb=tb.tb_next
    return observed
for name,expected in lock['runtime_executables'].items():
    try:
        actual=reader.identity(Path(name));assert actual==expected;rows.append({'path':name,'passed':True,'identity':actual})
    except Exception as error:rows.append({'path':name,'passed':False,**failure(error)})
record={'format':'has_normal_strict_runtime_preflight_trace_1','observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'samples':rows,'all_six_passed':len(rows)==6 and all(x['passed'] for x in rows),'no_gate_modified':True,'stager_invoked':False}
path=ROOT/'output'/('normal-runtime-stage-trace-'+str(time.time_ns())+'.json')
def save():path.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
save()
if not record['all_six_passed']:print(json.dumps({'passed':False,'trace':str(path),'samples':rows}));raise SystemExit(1)
sys.argv=[str(PACKET/'stage_after_full_pass.py'),'--full-run',str(ROOT/'output/windows-canonical-bone-binding-20261116T041518335'),'--expected-full-commit','52f63c944ded7a651da871524d23a345b606424d','--expected-head','52f63c944ded7a651da871524d23a345b606424d','--expected-functional-count','1019','--output',str(ROOT/'output/normal-boundary-20261116-attempt2')]
record['stager_invoked']=True;save()
sys.path.insert(0,str(PACKET))
try:runpy.run_path(sys.argv[0],run_name='__main__');record['stager_passed']=True
except Exception as error:
    record['stager_passed']=False;record['stager_refusal']=failure(error);save();print(json.dumps({'passed':False,'trace':str(path),'refusal':record['stager_refusal']}));raise
save();print(json.dumps({'passed':True,'trace':str(path),'unchanged_strict_stager_passed':True}))
