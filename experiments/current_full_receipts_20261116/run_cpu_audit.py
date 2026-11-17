"""Run the read-only terminal auditor, retaining the exact Python child and logs."""
from pathlib import Path
import datetime,hashlib,json,subprocess,sys,time
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
RUN=ROOT/'output/windows-canonical-bone-binding-20261116T041518335'
OUT=ROOT/'output/current-full-receipts-20261116-attempt1'
LOG=ROOT/'output/current-full-receipts-driver-20261116-attempt1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2);f.write('\n')
assert not LOG.exists() and not OUT.exists();LOG.mkdir()
command=[sys.executable,'-B',str(HERE/'audit_receipts.py'),'--terminal-permission','--host-proof-sha256',sha(RUN/'authoritative-host-termination.json'),'--host-raw-sha256',sha(RUN/'authoritative-host-terminal.json'),'--output',str(OUT)]
save(LOG/'command.json',command)
start=time.monotonic();p=subprocess.Popen(command,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
save(LOG/'start.json',{'pid':p.pid,'retained_Popen':True,'launch_requested_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
out,err=p.communicate(timeout=180)
(LOG/'stdout.log').write_bytes(out);(LOG/'stderr.log').write_bytes(err)
result={'format':'has_current_full_cpu_receipt_audit_execution_1','exit':p.returncode,'pid':p.pid,'retained_Popen_reaped':p.poll() is not None,'seconds':time.monotonic()-start,'output':str(OUT),'engine_CIM_or_Git_actions':False,'private_raw_reports_not_published':True}
save(LOG/'process.json',result)
if (OUT/'receipt-inventory.json').exists():result['receipt_inventory_sha256']=sha(OUT/'receipt-inventory.json')
result['full_report_sha256']=sha(ROOT/'output/verification.json')
if (OUT/'receipt-ready-final.json').exists():result['summary']=json.loads((OUT/'receipt-ready-final.json').read_bytes())
save(LOG/'verification.json',result)
print(json.dumps(result));raise SystemExit(p.returncode)
