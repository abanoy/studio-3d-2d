"""Actual400drawing private background Open with cancellation and transaction failures."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command,configure_private_display

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--fixture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--isolated-display');o=p.parse_args()
 if os.name!='nt':
  if sys.platform!='linux' or not o.isolated_display:p.error('Explicit private display required; no shared fallback')
  configure_private_display(o.isolated_display)
 folder=o.output.resolve();folder.mkdir(parents=True,exist_ok=False);fixture=o.fixture.resolve();inputs=[fixture/'Background400.has',fixture/'expected.json',fixture/'expected.png'];before={str(q):digest(q) for q in inputs}
 frozen={str(q.relative_to(ROOT)):digest(q) for part in ['src','tests','tools','examples'] for q in (ROOT/part).rglob('*') if q.is_file() and q.suffix!='.pyc' and '__pycache__' not in q.parts}
 args=command('tests/has_background_open_smoke.gd',extra=['--audio-driver','Dummy','--log-file',str(folder/'engine.log'),'--',str(folder),*[str(q) for q in inputs]])
 started=time.monotonic();peak=0;hwm=0
 with (folder/'console.log').open('wb') as out:
  process=subprocess.Popen(args,cwd=ROOT,stdout=out,stderr=subprocess.STDOUT)
  while process.poll() is None:
   if time.monotonic()-started>195:process.terminate();process.wait(timeout=15);raise TimeoutError('background Open')
   if sys.platform=='linux':
    try:
     for line in Path(f'/proc/{process.pid}/status').read_text().splitlines():
      if line.startswith('VmRSS:'):peak=max(peak,int(line.split()[1])*1024)
      if line.startswith('VmHWM:'):hwm=max(hwm,int(line.split()[1])*1024)
    except FileNotFoundError:pass
   time.sleep(.05)
 log=(folder/'console.log').read_text(errors='replace');marker='HAS_BACKGROUND_OPEN ';assert process.returncode==0 and marker in log and not any(x in log for x in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
 result=json.loads(next(line[len(marker):] for line in log.splitlines() if line.startswith(marker)));assert result['checks']>=12 and result['failures']==0
 assert all(digest(Path(q))==sha for q,sha in before.items()) and all(digest(ROOT/q)==sha for q,sha in frozen.items())
 receipts=[]
 if os.name=='nt':
  path=Path(args[args.index('--receipt')+1]);r=json.loads(path.read_bytes());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];receipts.append(str(path))
 proof=dict(result=result,source_sha256=frozen,inputs=before,isolated_display=o.isolated_display,private_receipts=receipts,process_memory=dict(RSS_sample_peak_bytes=peak,HWM_observed_bytes=hwm,scope='Godot process only; not whole-session or GPU hard admission'),wall_seconds=time.monotonic()-started)
 (folder/'verification.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items() if k!='source_sha256'},indent=2))
if __name__=='__main__':main()
