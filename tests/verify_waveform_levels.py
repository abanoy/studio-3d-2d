"""Cached waveform detail, exact audio regression and private timeline GUI checks."""
from pathlib import Path
import argparse,array,hashlib,json,os,subprocess,sys,time,wave
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import configure_private_display, command

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--isolated-display',help='Linux: explicitly provisioned private dummy X display')
    parser.add_argument('--output',type=Path)
    options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Linux requires a private --isolated-display; no shared-desktop fallback')
        configure_private_display(options.isolated_display)
    folder=(options.output or ROOT/'output/waveform-levels'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
    frozen={p:hashlib.sha256(p.read_bytes()).hexdigest() for name in ['src','tests','tools','data','examples'] for p in (ROOT/name).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts}
    samples=array.array('h',[0]*9600)
    for index,value in [(0,26000),(2400,18000),(4800,-10000),(7200,3200)]:samples[index]=value
    if sys.byteorder!='little':samples.byteswap()
    with wave.open(str(folder/'impulses.wav'),'wb') as out:out.setparams((1,2,48000,0,'NONE','not compressed'));out.writeframes(samples.tobytes())
    original=hashlib.sha256((folder/'impulses.wav').read_bytes()).hexdigest();reports={};receipts=[]
    for script,label,marker,headless in [('tests/waveform_levels_unit.gd','unit','WAVEFORM_LEVELS_UNIT ',True),('tests/waveform_levels_smoke.gd','app','WAVEFORM_LEVELS_SMOKE ',False)]:
        args=command(script,headless=headless,extra=(['--audio-driver','Dummy'] if os.name!='nt' else [])+['--',str(folder)])
        result=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
        log=result.stdout+result.stderr;(folder/(label+'.log')).write_text(log,encoding='utf-8')
        assert result.returncode==0 and marker in log and not any(v in log for v in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
        report=json.loads(next(line[len(marker):] for line in log.splitlines() if line.startswith(marker)));assert report['failures']==0;reports[label]=report
        if os.name=='nt' and not headless:
            receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_bytes())
            assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'],r
            receipts.append(str(receipt))
    for script,label in [('verify_sparse_audio.py','audio-regression'),('verify_timeline_navigation.py','navigation-regression')]:
        args=[sys.executable,str(ROOT/'tests'/script),'--output',str(folder/label)]
        if options.isolated_display:args+=['--isolated-display',options.isolated_display]
        result=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=480)
        (folder/(label+'.log')).write_text(result.stdout+result.stderr,encoding='utf-8')
        assert result.returncode==0,result.stdout+result.stderr
        reports[label]=json.loads((folder/label/'verification.json').read_bytes())
    assert hashlib.sha256((folder/'impulses.wav').read_bytes()).hexdigest()==original
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==digest for p,digest in frozen.items())
    proof=dict(reports=reports,source_audio_unchanged=True,functional_unchanged=True,private_receipts=receipts,isolated_display=options.isolated_display,folder=str(folder))
    (folder/'verification.json').write_text(json.dumps(proof,indent=2),encoding='utf-8');print(json.dumps(proof,indent=2))

if __name__=='__main__':main()
