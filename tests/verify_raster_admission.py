"""Owned raster admission domains, actual refusal paths and existing32cel noisy-art workflow."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command,configure_private_display

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--isolated-display');parser.add_argument('--output',type=Path);args=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not args.isolated_display:parser.error('Linux requires an explicitly owned private display')
        configure_private_display(args.isolated_display)
    folder=(args.output or ROOT/'output/raster-admission'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
    domain=subprocess.run([sys.executable,str(ROOT/'tests/verify_cel_raster_snapshot.py'),'--output',str(folder/'domain')],cwd=ROOT,capture_output=True,text=True,timeout=100)
    (folder/'domain.log').write_text(domain.stdout+domain.stderr);assert domain.returncode==0,domain.stdout+domain.stderr
    app=folder/'app';app.mkdir();argv=command('tests/cel_raster_admission_smoke.gd',extra=['--audio-driver','Dummy','--log-file',str(app/'engine.log'),'--',str(app)])
    process=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=195);log=process.stdout+process.stderr;(app/'console.log').write_text(log)
    assert process.returncode==0 and 'RASTER_ADMISSION_SMOKE ' in log and not any(x in log for x in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
    proof=dict(domain=json.loads((folder/'domain/verification.json').read_text()),actual_refusals=json.loads((app/'verification.json').read_text()))
    if os.name=='nt':
        p=Path(argv[argv.index('--receipt')+1]);r=json.loads(p.read_text());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];proof['private_receipt']=str(p)
    reader=subprocess.run([sys.executable,str(ROOT/'tests/verify_cel_raster_reader.py'),*(['--isolated-display',args.isolated_display] if os.name!='nt' else []),'--auto-open','--noise-art','--output',str(folder/'noise32')],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=400)
    (folder/'noise32.log').write_text(reader.stdout+reader.stderr);assert reader.returncode==0,reader.stdout+reader.stderr
    proof['noise32']=json.loads((folder/'noise32/verification.json').read_text());proof['source_sha256']={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['src/cel_raster_snapshot_cache.gd','src/cel_raster_owner.gd','src/cel_raster_budget.gd','tests/cel_raster_admission_unit.gd','tests/cel_raster_admission_smoke.gd','tests/verify_raster_admission.py']};proof['scope']='Bounded registered authority+decoded cache, conservative logical bytes; not total processRSS, GPU, history tiles or all transient buffers.';proof['isolated_display']=args.isolated_display
    (folder/'verification.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))
if __name__=='__main__':main()
