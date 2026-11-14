"""Run only the amended authored stdlib tests in this output-owned directory."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
BASE=Path(__file__).resolve().parent
run=BASE/('cpu-launch-'+str(time.time_ns()));run.mkdir(exist_ok=False)
source=BASE/'source'
before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in source.glob('*.py')}
args=[sys.executable,'-B',str(source/'test_source_jiggle_metadata.py')]
(run/'command.json').write_text(json.dumps(args,indent=2)+'\n',encoding='utf-8')
process=subprocess.run(args,cwd=BASE,capture_output=True,timeout=30,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
(run/'stdout.log').write_bytes(process.stdout);(run/'stderr.log').write_bytes(process.stderr)
reports=sorted(BASE.glob('minimal-cpu-*/verification.json'))
report=json.loads(reports[-1].read_bytes()) if reports else None
after={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in source.glob('*.py')}
summary={'format':'has_minimal_jiggle_amendment_actual_cpu_1','exit':process.returncode,'source_before':before,'source_after':after,'source_unchanged':before==after,'report_path':str(reports[-1]) if reports else None,'report':report,'passed':process.returncode==0 and before==after and report is not None and report['passed'] and report['checks']==25 and report['failures']==report['errors']==0,'runtime_import_or_launch':False,'output_only':True}
(run/'verification.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'run':str(run),'passed':summary['passed'],'exit':process.returncode,'report':report},indent=2))
raise SystemExit(0 if summary['passed'] else 1)
