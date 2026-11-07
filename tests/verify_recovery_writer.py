"""Detached checkpoint ownership, real background writes and routed recovery scheduling."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command,configure_private_display

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--isolated-display');parser.add_argument('--output',type=Path);o=parser.parse_args()
 if os.name!='nt':
  if sys.platform!='linux' or not o.isolated_display:parser.error('Linux requires an explicitly private display; no shared fallback')
  configure_private_display(o.isolated_display)
 folder=(o.output or ROOT/'output/recovery-writer'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False);reports={};receipts=[]
 for script,label,marker,headless in [('recovery_snapshot_unit','snapshot','RECOVERY_SNAPSHOT_UNIT ',True),('recovery_writer_unit','writer-unit','RECOVERY_WRITER_UNIT ',True),('recovery_writer_smoke','app','RECOVERY_WRITER_SMOKE ',False),('recovery_preview_smoke','preview','RECOVERY_PREVIEW ',False),('recovery_schedule_smoke','schedule','RECOVERY_SCHEDULE ',False)]:
  target=folder/label;target.mkdir();args=command('tests/'+script+'.gd',headless=headless,extra=['--audio-driver','Dummy','--log-file',str(target/'engine.log'),'--',str(target)])
  started=time.monotonic();p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=150);text=p.stdout+p.stderr;(target/'console.log').write_text(text)
  assert p.returncode==0 and marker in text and not any(s in text for s in ['ERROR:','FAIL ','ObjectDB instances leaked']),text
  result=json.loads(next(line[len(marker):] for line in text.splitlines() if line.startswith(marker)));assert result['failures']==0,result
  reports[label]=dict(result=result,seconds=time.monotonic()-started)
  if os.name=='nt' and not headless:
   path=Path(args[args.index('--receipt')+1]);receipt=json.loads(path.read_bytes());assert receipt['exit']==0 and receipt['child_desktop_confirmed'] and not receipt['foreground_child_observed'] and receipt['job_closed'] and receipt['desktop_closed'];receipts.append(str(path))
 proof=dict(reports=reports,private_receipts=receipts,isolated_display=o.isolated_display,source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'src/app.gd',ROOT/'src/recovery_writer.gd',ROOT/'src/recovery_snapshot.gd',ROOT/'src/recovery.gd',ROOT/'tests/recovery_wait.gd']})
 (folder/'verification.json').write_text(json.dumps(proof,indent=2));print(json.dumps(proof,indent=2))
if __name__=='__main__':main()
