"""Measure full-span held-art reuse without changing animation, alpha or source pixels."""
from pathlib import Path
import argparse,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--isolated-display',help='Linux: pre-provisioned private dummy X display')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--baseline-report',type=Path,help='Optional archived pre-optimization report; checks pixel hashes, never a machine-dependent timing threshold')
    options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Linux requires an explicit private --isolated-display; no shared-desktop fallback')
        os.environ['DISPLAY']=options.isolated_display
    folder=(options.output or ROOT/'output/sequence-cache'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
    args=command('tests/sequence_cache_smoke.gd',extra=(['--audio-driver','Dummy'] if os.name!='nt' else [])+['--',str(folder)])
    result=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=320)
    log=result.stdout+result.stderr;(folder/'engine.log').write_text(log,encoding='utf-8')
    assert result.returncode==0 and 'SEQUENCE_CACHE_SMOKE ' in log and not any(s in log for s in ['ERROR:','FAIL ','ObjectDB instances leaked','another exclusive child']),log
    proof=json.loads((folder/'verification.json').read_bytes());assert not proof['baseline'] and proof['failures']==0 and proof['frames']==240 and proof['source_builds']==2 and proof['peak_cached_assets']==1,proof
    if os.name=='nt':
        receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_bytes())
        assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'],r
        proof['private_receipt']=str(receipt)
    if options.baseline_report:
        baseline=json.loads(options.baseline_report.read_bytes());assert baseline['baseline'] and baseline['frames']==240 and baseline['source_builds']==240 and baseline['failures']==0,baseline
        assert all(proof[k]==baseline[k] for k in ['first_sha256','last_sha256']),[proof,baseline]
        proof['baseline_report']=str(options.baseline_report.resolve());proof['baseline_mean_ms']=baseline['mean_ms'];proof['baseline_source_builds']=baseline['source_builds']
    proof['isolated_display']=options.isolated_display
    (folder/'verification.json').write_text(json.dumps(proof,indent=2),encoding='utf-8');print(json.dumps(proof,indent=2))

if __name__=='__main__':main()
