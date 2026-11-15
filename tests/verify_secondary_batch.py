"""Atomic checked-part setup through the real helper, Undo, portable save and media."""
from pathlib import Path
import array
import copy
import hashlib
import json
import math
import os
import subprocess
import sys
import time
import wave

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
import run
from test_secondary_helpers import two_panel_fixture, write_glb


def main():
    subprocess.run([sys.executable,'tests/test_secondary_helpers_batch.py'],cwd=ROOT,check=True)
    folder=ROOT/'output/secondary-batch'/str(time.time_ns());folder.mkdir(parents=True)
    original=folder/'original.glb';g=two_panel_fixture(original)
    shared=folder/'shared.glb'
    g.doc['meshes'].append({'primitives':[copy.deepcopy(g.doc['meshes'][0]['primitives'][1])]})
    g.doc['nodes'] += [{'name':'SharedA','mesh':1,'skin':0},{'name':'SharedB','mesh':1,'skin':0}]
    g.doc['nodes'][0]['children'] += [4,5];write_glb(shared,g.doc,bytes(g.binary))
    bad=folder/'broken.glb';bad.write_bytes(b'Not a GLB')
    originals={str(p):(hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns) for p in (original,shared)}
    wav=folder/'voice.wav';pcm=array.array('h',(int(15000*math.sin(2*math.pi*1000*n/44100)) for n in range(22050)))
    if sys.byteorder!='little':pcm.byteswap()
    with wave.open(str(wav),'wb') as f:f.setparams((1,2,44100,0,'NONE','not compressed'));f.writeframes(pcm.tobytes())
    paths=sorted([*ROOT.glob('src/*.gd'),*ROOT.glob('src/*.gdshader'),ROOT/'main.tscn',ROOT/'project.godot',ROOT/'tools/secondary_helpers.py',ROOT/'tools/secondary_helpers_batch.py',ROOT/'tools/secondary_helper_worker.py',ROOT/'tests/secondary_batch_smoke.gd',ROOT/'tests/secondary_batch_unit.gd',Path(__file__)])
    source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths};(folder/'source-sha256.json').write_text(json.dumps(source_hashes,indent=2)+'\n')
    unit_proc=subprocess.run(run.command('tests/secondary_batch_unit.gd',headless=True,extra=['--log-file',str(folder/'unit-engine.log')]),cwd=ROOT,capture_output=True,text=True,timeout=30)
    unit_text=unit_proc.stdout+unit_proc.stderr;(folder/'unit-stdout.log').write_text(unit_text,encoding='utf-8')
    if unit_proc.returncode or any(x in unit_text for x in ['SCRIPT ERROR','ERROR:','FAIL ','ObjectDB instances leaked']):raise RuntimeError(f'Batch unit verification failed; inspect {folder}')
    unit=json.loads(next(line.split(' ',1)[1] for line in unit_text.splitlines() if line.startswith('SECONDARY_BATCH_UNIT ')));assert unit['failures']==0
    args=run.command('tests/secondary_batch_smoke.gd',extra=['--audio-driver','Dummy','--log-file',str(folder/'engine.log'),'--',str(folder),str(original),str(shared),str(bad),str(wav)])
    with (folder/'stdout.log').open('w',encoding='utf-8') as log:proc=subprocess.run(args,cwd=ROOT,stdout=log,stderr=log,timeout=175)
    text=(folder/'stdout.log').read_text(encoding='utf-8',errors='replace')
    if proc.returncode or any(x in text for x in ['SCRIPT ERROR','SHADER ERROR','ERROR:','FAIL ','ObjectDB instances leaked']):raise RuntimeError(f'Batch app verification failed; inspect {folder}')
    result=json.loads((folder/'result.json').read_bytes());assert result['failures']==0
    receipt=None
    if os.name=='nt':
        receipt=json.loads(Path(args[args.index('--receipt')+1]).read_bytes());assert receipt['exit']==0 and receipt['child_desktop_confirmed'] and not receipt['foreground_child_observed'] and receipt['job_closed'] and receipt['desktop_closed']
    ffmpeg=Path(os.environ.get('HYBRID_FFMPEG',r'C:\Program Files\ffmpeg\bin\ffmpeg.exe'));ffprobe=ffmpeg.with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe')
    media=json.loads(subprocess.check_output([str(ffprobe),'-v','error','-count_frames','-show_streams','-of','json',result['movie']]))
    video=next(s for s in media['streams'] if s['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'],float(video['duration']))==('h264',1920,1080,'24/1','48',2.)
    assert any(s['codec_type']=='audio' and s['codec_name']=='aac' for s in media['streams'])
    decoded=folder/'decoded.wav';subprocess.run([str(ffmpeg),'-v','error','-y','-i',result['movie'],'-vn','-ac','1','-ar','48000','-c:a','pcm_s16le',str(decoded)],check=True)
    with wave.open(str(decoded),'rb') as f:samples=array.array('h',f.readframes(f.getnframes()))
    if sys.byteorder!='little':samples.byteswap()
    onset=next(i/48000 for i,v in enumerate(samples) if abs(v)>2000);assert abs(onset-1)<.002
    assert source_hashes=={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    assert all(before==(hashlib.sha256(Path(path).read_bytes()).hexdigest(),Path(path).stat().st_mtime_ns) for path,before in originals.items())
    proof={'unit':unit,'result':result,'private_receipt':receipt,'originals':originals,'audio_onset_seconds':onset,'video':{k:video[k] for k in ('codec_name','width','height','r_frame_rate','nb_read_frames','duration')}}
    (folder/'verification.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps({'folder':str(folder),**proof},indent=2))


if __name__=='__main__':main()
