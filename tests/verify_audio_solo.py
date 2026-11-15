"""Versioned scene-local Solo across real UI, nested audio, persistence and AAC."""
from pathlib import Path
import argparse,array,hashlib,json,math,os,struct,subprocess,sys,wave
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from run import command,configure_private_display
import has_project as has

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--isolated-display');parser.add_argument('--output',type=Path,required=True);o=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not o.isolated_display:parser.error('Explicit private display required; no shared fallback')
        configure_private_display(o.isolated_display)
    folder=o.output.resolve();folder.mkdir(parents=True,exist_ok=False);reports={};receipts=[]
    frozen={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for part in ['src','tests','tools','data','examples'] for p in (ROOT/part).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts}
    def run(script,label,marker,extra=(),headless=False):
        args=command(script,headless=headless,extra=['--audio-driver','Dummy','--log-file',str(folder/(label+'-engine.log')),'--',str(folder),*extra]);r=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=240);log=r.stdout+r.stderr;(folder/(label+'.log')).write_text(log);assert r.returncode==0 and marker in log and not any(t in log for t in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
        reports[label]=json.loads(next(line[len(marker):] for line in log.splitlines() if line.startswith(marker)));assert reports[label]['failures']==0
        if os.name=='nt' and not headless:
            p=Path(args[args.index('--receipt')+1]);v=json.loads(p.read_bytes());assert v['exit']==0 and v['child_desktop_confirmed'] and not v['foreground_child_observed'] and v['job_closed'] and v['desktop_closed'];receipts.append(str(p))
    run('tests/audio_solo_unit.gd','unit','AUDIO_SOLO_UNIT ',headless=True)
    cases=json.loads((folder/'solo-cases.json').read_text())
    for case in cases:
        manifest={'schema_version':3,'scene':{'path':'assets/'+'0'*64+'.glb','sha256':'0'*64},'model':{},'layers':[],'video':{'duration_frames':24},'audio':case['audio']}
        try:has.members(manifest);valid=True
        except has.HasError:valid=False
        assert valid==case['valid'],case
    originals={}
    for name,frequency,level in [('voice.wav',1000,12000),('peer.wav',1500,4000),('nested.wav',500,6000)]:
        with wave.open(str(folder/name),'wb') as out:out.setparams((1,2,44100,0,'NONE','not compressed'));out.writeframes(b''.join(struct.pack('<h',round(level*math.sin(2*math.pi*frequency*i/44100))) for i in range(44100)))
        originals[name]=hashlib.sha256((folder/name).read_bytes()).hexdigest()
    run('tests/audio_solo_smoke.gd','writer','AUDIO_SOLO_WRITE ')
    manual={p:hashlib.sha256((folder/p).read_bytes()).hexdigest() for p in ['Solo.has','Solo linked.has']}
    for name in originals:(folder/name).rename(folder/(name+'.offline'))
    (folder/'writer-cache').rename(folder/'writer-cache.offline')
    run('tests/audio_solo_smoke.gd','packed','AUDIO_SOLO_READ ',['packed'])
    run('tests/audio_solo_smoke.gd','recovery','AUDIO_SOLO_READ ',['recovery'])
    for name in originals:(folder/(name+'.offline')).rename(folder/name)
    run('tests/audio_solo_smoke.gd','linked','AUDIO_SOLO_READ ',['linked'])
    ffmpeg=os.environ.get('HYBRID_FFMPEG','ffmpeg');probe=str(Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe'));info=json.loads(subprocess.check_output([probe,'-v','error','-count_frames','-show_streams','-of','json',reports['writer']['movie']]));video=next(s for s in info['streams'] if s['codec_type']=='video');assert(video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48');assert any(s['codec_name']=='aac' for s in info['streams'])
    pcm=array.array('h');pcm.frombytes(subprocess.check_output([ffmpeg,'-v','error','-i',reports['writer']['movie'],'-vn','-ac','1','-ar','48000','-f','s16le','-']))
    if sys.byteorder!='little':pcm.byteswap()
    def magnitude(frequency):
        values=pcm[14400:19200];return 2*abs(sum(v*complex(math.cos(2*math.pi*frequency*i/48000),math.sin(2*math.pi*frequency*i/48000)) for i,v in enumerate(values)))/len(values)
    levels={str(f):magnitude(f) for f in [1000,1500,500]};assert 5500<levels['1000']<6500 and levels['1500']<80 and levels['500']<80,levels
    assert max(map(abs,pcm[52800:57600]))<10
    assert all(hashlib.sha256((folder/name).read_bytes()).hexdigest()==h for name,h in originals.items()) and all(hashlib.sha256((folder/p).read_bytes()).hexdigest()==h for p,h in manual.items())
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in frozen.items())
    proof=dict(reports=reports,video=video,decoded_magnitudes=levels,cross_runtime_cases=len(cases),source_sha256=frozen,private_receipts=receipts,isolated_display=o.isolated_display,originals_and_manual_has_unchanged=True,packed_and_recovery_sources_and_writer_cache_offline=True,scope='Actual scene-local Solo UI, authoritative mute, multiple solos, gain/fades/trim, nested suppression, Undo/Redo, packed/linked/recovery, exact editable art/render and decoded AAC isolation. No physical audio-device/Windows certification.')
    (folder/'verification.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items() if k!='source_sha256'},indent=2))
if __name__=='__main__':main()
