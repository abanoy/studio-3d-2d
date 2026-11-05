"""Actual platform process identity plus domain/file ownership decisions, no GUI."""
from pathlib import Path
import json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command
def main():
    folder=ROOT/'output/recovery-identity'/str(time.time_ns());folder.mkdir(parents=True)
    parent=json.loads(subprocess.check_output([sys.executable,str(ROOT/'tools/recovery_processes.py'),str(os.getpid())],text=True));assert parent['owners'][str(os.getpid())]=='alive' and (isinstance(parent.get('linux_start',{}).get(str(os.getpid())),str) if sys.platform=='linux' else parent['created_100ns'][str(os.getpid())].isdigit()),parent
    p=subprocess.run(command('tests/recovery_identity_unit.gd',headless=True,extra=['--',str(folder),str(os.getpid())]),cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60)
    log=p.stdout+p.stderr;(folder/'unit.log').write_text(log,encoding='utf-8');assert p.returncode==0 and 'RECOVERY_IDENTITY_UNIT ' in log and '"failures":0' in log and not any(s in log for s in ('ERROR:','FAIL ')),log
    result=json.loads(log.split('RECOVERY_IDENTITY_UNIT ')[-1].splitlines()[0]);result['folder']=str(folder);(ROOT/'output/recovery-identity-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
