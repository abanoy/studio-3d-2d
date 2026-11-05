from pathlib import Path
import hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command
if __name__=='__main__':
    folder=ROOT/'output/joint-authoring'/str(time.time_ns());folder.mkdir(parents=True)
    probe=Path(json.loads((ROOT/'output/joint-constraints-verification.json').read_bytes())['folder'])
    cases=json.loads((probe/'cases.json').read_bytes());(folder/'cases.json').write_text(json.dumps(cases),encoding='utf-8')
    hashes={c['source']:hashlib.sha256(Path(c['source']).read_bytes()).hexdigest() for c in cases}
    args=command('tests/joint_authoring_smoke.gd',extra=['--',str(folder)])
    proc=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=180,creationflags=subprocess.CREATE_NO_WINDOW)
    data=proc.stdout+proc.stderr;(folder/'app.log').write_bytes(data)
    assert proc.returncode==0 and b'JOINT_AUTHORING_SMOKE ' in data and not any(x in data for x in (b'SCRIPT ERROR',b'SHADER ERROR',b'ObjectDB instances leaked')),data.decode('utf-8',errors='replace')
    receipt=Path(args[args.index('--receipt')+1]);desktop=json.loads(receipt.read_bytes())
    assert desktop['exit']==0 and desktop['child_desktop_confirmed'] and not desktop['foreground_child_observed'] and desktop['job_closed'] and desktop['desktop_closed']
    result=json.loads((folder/'authoring-result.json').read_bytes())
    for item in result['cases']:
        proc=subprocess.run([r'C:\Program Files\ffmpeg\bin\ffprobe.exe','-v','error','-count_frames','-show_streams','-show_format','-of','json',item['movie']],capture_output=True,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
        metadata=json.loads(proc.stdout);video=next(s for s in metadata['streams'] if s['codec_type']=='video')
        assert (video['codec_name'],video['width'],video['height'],video['nb_read_frames'],video['r_frame_rate'])==('h264',1920,1080,'48','24/1') and abs(float(metadata['format']['duration'])-2)<.01
        (folder/(item['label']+'-ffprobe.json')).write_bytes(proc.stdout)
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())
    result.update(folder=str(folder),private_receipt=str(receipt),original_inputs_unchanged=True)
    (ROOT/'output/joint-authoring-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print('PASS standard joint authoring: handles, numeric, opt-out, Undo, packed HAS and two movies')
