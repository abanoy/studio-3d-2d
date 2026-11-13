from pathlib import Path
import hashlib,json,os,subprocess,sys,time,uuid
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from run import command
OUT=Path(__file__).resolve().parent/('attempt-'+str(time.time_ns())+'-'+uuid.uuid4().hex[:8]);OUT.mkdir(exist_ok=False)
tracked=['src/source_choice_dialog.gd','src/source_import.gd','tests/source_choice_unit.gd','run.py']
def sources():return {name:{'bytes':(ROOT/name).stat().st_size,'sha256':hashlib.sha256((ROOT/name).read_bytes()).hexdigest()} for name in tracked}
before=sources();(OUT/'source-before.json').write_text(json.dumps(before,indent=2)+'\n',encoding='utf-8')
args=command('tests/source_choice_unit.gd',headless=True,extra=['--log-file',str(OUT/'engine.log'),'--',str(OUT)])
(OUT/'command.json').write_text(json.dumps(args,indent=2)+'\n',encoding='utf-8')
error=None;exitcode=None
try:
 p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=45,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
 exitcode=p.returncode;log=p.stdout+p.stderr
except subprocess.TimeoutExpired as exc:
 log=((exc.stdout or b'').decode('utf-8','replace') if isinstance(exc.stdout,bytes) else (exc.stdout or ''))+((exc.stderr or b'').decode('utf-8','replace') if isinstance(exc.stderr,bytes) else (exc.stderr or ''));error='headless timeout'
(OUT/'console.log').write_text(log,encoding='utf-8')
engine=(OUT/'engine.log').read_text(encoding='utf-8',errors='replace') if (OUT/'engine.log').exists() else ''
markers=[line for text in [log,engine] for line in text.splitlines() if any(x in line for x in ['ERROR:','FAIL ','SCRIPT ERROR','ObjectDB instances leaked','resources still in use'])]
lines=[line[len('SOURCE_CHOICE_UNIT '):] for line in log.splitlines() if line.startswith('SOURCE_CHOICE_UNIT ')];result=json.loads(lines[0]) if len(lines)==1 else None
after=sources();(OUT/'source-after.json').write_text(json.dumps(after,indent=2)+'\n',encoding='utf-8')
passed=exitcode==0 and error is None and not markers and before==after and result is not None and result['checks']>0 and result['failures']==0
report=dict(passed=passed,exit=exitcode,error=error,result=result,source_unchanged=before==after,error_markers=markers,headless=True,native_conversion=False,graphics=False)
(OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(folder=str(OUT),**report),ensure_ascii=True));print(log[-10000:] if not passed else '')
sys.exit(0 if passed else 1)
