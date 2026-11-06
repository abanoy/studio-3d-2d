"""Actual completed edits, natural timer, failure/retry and independent HAS save identity."""
from pathlib import Path
import argparse,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import configure_private_display,command
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--isolated-display',help='Linux: explicitly provisioned private dummy X display')
    parser.add_argument('--output',type=Path)
    options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Linux requires a private --isolated-display; no shared-desktop fallback')
        configure_private_display(options.isolated_display)
    folder=(options.output or ROOT/'output/recovery-schedule'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
    args=command('tests/recovery_schedule_smoke.gd',extra=(['--audio-driver','Dummy'] if os.name!='nt' else [])+['--log-file',str(folder/'godot.log'),'--',str(folder)])
    p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=130)
    text=p.stdout+p.stderr;(folder/'engine.log').write_text(text,encoding='utf-8')
    assert p.returncode==0 and 'RECOVERY_SCHEDULE ' in text and '"failures":0' in text and not any(x in text for x in ('ERROR:','FAIL ','ObjectDB instances leaked','another exclusive child')),text
    result=json.loads((folder/'result.json').read_text(encoding='utf-8'));assert result['failures']==0
    receipt=None
    if os.name=='nt':
        receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_text(encoding='utf-8'))
        assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'],r
    result['private_receipt']=str(receipt) if receipt else None;result['isolated_display']=options.isolated_display
    (folder/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');(ROOT/'output/recovery-schedule-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
