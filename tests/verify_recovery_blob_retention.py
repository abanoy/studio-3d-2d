"""Recovery payload retirement after checked catalog publication; no arbitrary cache sweep."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);o=p.parse_args();folder=o.output.resolve();folder.mkdir(parents=True,exist_ok=False)
 frozen={str(p.relative_to(ROOT)):digest(p) for part in ['src','tests','tools','examples'] for p in (ROOT/part).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts};reports={}
 for script,marker in [('recovery_blob_retention_unit','RECOVERY_BLOB_RETENTION '),('recovery_journal_unit','RECOVERY_JOURNAL_UNIT ')]:
  case=folder/script;case.mkdir();args=command('tests/'+script+'.gd',headless=True,extra=['--log-file',str(case/'engine.log'),'--',str(case)]);r=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=90);log=r.stdout+r.stderr;(case/'console.log').write_text(log);assert r.returncode==0 and marker in log and not any(x in log for x in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
  result=json.loads(next(line[len(marker):] for line in log.splitlines() if line.startswith(marker)));assert result['checks']>0 and result['failures']==0;reports[script]=result;print(script+': PASS',flush=True)
 assert all(digest(ROOT/path)==sha for path,sha in frozen.items())
 proof=dict(reports=reports,source_sha256=frozen,scope='Only formerly referenced owned blobs after successful checkpoint/journal publication; current, backup, both catalog roots, corrupt/foreign-owner/link/unrelated preservation. No global cache sweep or concurrent whole-root quota claim.')
 (folder/'verification.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items() if k!='source_sha256'},indent=2))
if __name__=='__main__':main()
