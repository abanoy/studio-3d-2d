"""Shared recovery quota plus detached writer, scheduling, preview and retention."""
from pathlib import Path
import argparse,hashlib,json,os,re,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command,configure_private_display

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--isolated-display');o=p.parse_args()
 if os.name!='nt':
  if sys.platform!='linux' or not o.isolated_display:p.error('Explicit private display required')
  configure_private_display(o.isolated_display)
 folder=o.output.resolve();folder.mkdir(parents=True,exist_ok=False)
 frozen={str(p.relative_to(ROOT)):digest(p) for part in ['src','tests','tools','examples'] for p in (ROOT/part).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts};reports={}
 r=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_recovery_quota.py'],cwd=ROOT,capture_output=True,text=True,timeout=45);(folder/'python.log').write_text(r.stdout+r.stderr);n=re.search(r'Ran ([1-9][0-9]*) tests',r.stderr);assert r.returncode==0 and n and 'skipped' not in r.stderr,r.stdout+r.stderr;reports['quota_python']={'checks':int(n.group(1)),'failures':0}
 for script,marker in [('recovery_blob_retention_unit','RECOVERY_BLOB_RETENTION '),('recovery_journal_unit','RECOVERY_JOURNAL_UNIT ')]:
  target=folder/script;target.mkdir();args=command('tests/'+script+'.gd',headless=True,extra=['--log-file',str(folder/(script+'-engine.log')),'--',str(target)]);r=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=90);log=r.stdout+r.stderr;(folder/(script+'.log')).write_text(log);assert r.returncode==0 and marker in log and not any(t in log for t in ['ERROR:','FAIL ','ObjectDB instances leaked']),log;report=json.loads(next(s[len(marker):] for s in log.splitlines() if s.startswith(marker)));assert report['failures']==0;reports[script]=report
 r=subprocess.run([sys.executable,'tests/verify_recovery_writer.py','--output',str(folder/'background-writer'),'--isolated-display',o.isolated_display],cwd=ROOT,capture_output=True,text=True,timeout=300);(folder/'background-writer.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stdout+r.stderr;reports['background_writer']=json.loads((folder/'background-writer/verification.json').read_bytes())
 assert all(digest(ROOT/name)==sha for name,sha in frozen.items())
 result=dict(reports=reports,source_sha256=frozen,isolated_display=o.isolated_display,scope='512MiB shared recovery admission, real parallel OS-lock clients, crash-incarnation reclamation without data deletion, fail-closed unknown/corrupt/linked cases, PNG bound, actual worker refusal and release, existing background app/preview/scheduling plus retained journal generations. Not whole-process/GPU RAM, arbitrary orphan cleanup, Windows run or physical power-loss certification.')
 (folder/'verification.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'},indent=2))
if __name__=='__main__':main()
