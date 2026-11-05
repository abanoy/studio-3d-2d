from pathlib import Path
import array
import hashlib
import json
import math
import os
import subprocess
import sys
import time
import wave

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command
if __name__=='__main__':
    folder=ROOT/'output/audio-edge'/str(time.time_ns());folder.mkdir(parents=True)
    originals={}
    for name,frequency,amplitude,seconds in [('voice.wav',1000,12000,1),('peer.wav',1500,4000,.5)]:
        data=array.array('h',(round(amplitude*math.sin(2*math.pi*frequency*i/44100)) for i in range(round(44100*seconds))))
        if sys.byteorder!='little':data.byteswap()
        with wave.open(str(folder/name),'wb') as out:out.setparams((1,2,44100,0,'NONE','not compressed'));out.writeframes(data.tobytes())
        originals[name]=hashlib.sha256((folder/name).read_bytes()).hexdigest()
    args=command('tests/audio_edge_smoke.gd',extra=['--',str(folder)])
    result=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=170,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    log=result.stdout+result.stderr;(folder/'app.log').write_bytes(log)
    assert result.returncode==0 and b'AUDIO_EDGE_SMOKE ' in log and not any(s in log for s in (b'SCRIPT ERROR',b'SHADER ERROR',b'ObjectDB instances leaked')),log.decode('utf-8',errors='replace')
    receipt=Path(args[args.index('--receipt')+1]);value=json.loads(receipt.read_bytes())
    assert value['exit']==0 and value['child_desktop_confirmed'] and not value['foreground_child_observed'] and value['job_closed'] and value['desktop_closed']
    report=json.loads((folder/'app-result.json').read_bytes())
    ffmpeg=os.environ.get('HYBRID_FFMPEG',r'C:\Program Files\ffmpeg\bin\ffmpeg.exe');probe=str(Path(ffmpeg).with_name('ffprobe.exe'))
    p=subprocess.run([probe,'-v','error','-count_frames','-show_streams','-show_format','-of','json',report['movie']],capture_output=True,check=True)
    (folder/'ffprobe.json').write_bytes(p.stdout);media=json.loads(p.stdout);video=next(s for s in media['streams'] if s['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48')
    assert any(s.get('codec_name')=='aac' for s in media['streams']) and abs(float(media['format']['duration'])-2)<.001
    p=subprocess.run([ffmpeg,'-v','error','-i',report['movie'],'-vn','-ac','2','-ar','48000','-f','s16le','-'],capture_output=True,check=True)
    data=array.array('h');data.frombytes(p.stdout)
    if sys.byteorder!='little':data.byteswap()
    def amplitude(at,frequency):
        values=data[round(at*48000)*2:round((at+.1)*48000)*2:2];count=len(values)
        return 2*abs(sum(v*complex(math.cos(2*math.pi*frequency*i/48000),math.sin(2*math.pi*frequency*i/48000)) for i,v in enumerate(values)))/count
    levels={'voice':amplitude(.4,1000),'voice_after_end':amplitude(.85,1000),'peer':amplitude(1.1,1500)}
    assert 10500<levels['voice']<13000 and levels['voice_after_end']<100 and 3300<levels['peer']<4700,levels
    assert originals=={name:hashlib.sha256((folder/name).read_bytes()).hexdigest() for name in originals}
    report.update(folder=str(folder),private_receipt=str(receipt),decoded_magnitudes=levels,original_inputs_unchanged=True)
    (ROOT/'output/audio-edge-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('PASS sound end handle preview/cancel/stale/capture, exact Undo, extension and min bounds, old move, HAS and timed AAC movie')
