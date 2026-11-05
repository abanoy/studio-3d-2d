from pathlib import Path
import array,json,os,subprocess,sys,time,wave
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command
if __name__=='__main__':
    folder=ROOT/'output/png-export'/str(time.time_ns());folder.mkdir(parents=True)
    with wave.open(str(folder/'tone.wav'),'wb') as out:out.setparams((1,2,48000,0,'NONE','not compressed'));out.writeframes(array.array('h',[1000]*48000).tobytes())
    args=command('tests/png_export_smoke.gd',extra=['--',str(folder)])
    p=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=190,creationflags=subprocess.CREATE_NO_WINDOW)
    data=p.stdout+p.stderr;(folder/'app.log').write_bytes(data)
    assert p.returncode==0 and b'PNG_EXPORT_SMOKE ' in data and not any(s in data for s in (b'SCRIPT ERROR',b'SHADER ERROR',b'FAIL ',b'ObjectDB instances leaked')),data.decode('utf-8',errors='replace')
    result=json.loads((folder/'result.json').read_bytes());assert result['failures']==0
    for field,count in [('full',48),('transparent',48),('silent',6)]:
        path=Path(result[field]);images=sorted(p.name for p in path.glob('frame_*.png') if p.is_file());assert images==['frame_%06d.png'%n for n in range(1,count+1)]
        assert json.loads((path/'sequence.json').read_bytes())['rendered_frames']==count
    receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_bytes());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed']
    result.update(folder=str(folder),private_receipt=str(receipt));(ROOT/'output/png-export-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print('PASS PNG-only scene/transparent export, exact WAV, rational timing, cancellation/failures and editor isolation without FFmpeg')
