"""Opaque cel IDs must never become paths or merge layer pixels on directory Save."""
from pathlib import Path
import argparse,array,hashlib,json,math,os,subprocess,sys,time,wave
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import configure_private_display,command

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--isolated-display',help='Linux: explicitly provisioned private dummy X display');parser.add_argument('--output',type=Path);options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Linux requires a private --isolated-display; no shared-desktop fallback')
        configure_private_display(options.isolated_display)
    folder=(options.output or ROOT/'output/cel-file-paths'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False);reports={};receipts=[]
    frozen={p:hashlib.sha256(p.read_bytes()).hexdigest() for name in ['src','tests','tools','data','examples'] for p in (ROOT/name).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts}
    samples=array.array('h',(round(12000*math.sin(2*math.pi*1000*i/48000)) for i in range(24000)))
    if sys.byteorder!='little':samples.byteswap()
    with wave.open(str(folder/'tone.wav'),'wb') as out:out.setparams((1,2,48000,0,'NONE','not compressed'));out.writeframes(samples.tobytes())
    audio=hashlib.sha256((folder/'tone.wav').read_bytes()).hexdigest()
    def run(script,label,marker,headless=False,extra=()):
        destination=folder/'unit' if headless else folder;destination.mkdir(exist_ok=True)
        args=command(script,headless=headless,extra=(['--audio-driver','Dummy'] if os.name!='nt' else [])+['--log-file',str(folder/(label+'-engine.log')),'--',str(destination),*extra]);p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=165)
        log=p.stdout+p.stderr;(folder/(label+'.log')).write_text(log,encoding='utf-8');assert p.returncode==0 and marker in log and not any(x in log for x in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
        reports[label]=json.loads(next(x[len(marker):] for x in log.splitlines() if x.startswith(marker)));assert reports[label]['failures']==0
        if os.name=='nt' and not headless:
            path=Path(args[args.index('--receipt')+1]);receipt=json.loads(path.read_bytes());assert receipt['exit']==0 and receipt['child_desktop_confirmed'] and not receipt['foreground_child_observed'] and receipt['job_closed'] and receipt['desktop_closed'];receipts.append(str(path))
    run('tests/cel_file_paths_unit.gd','unit','CEL_FILE_PATHS_UNIT ',True)
    run('tests/cel_file_paths_smoke.gd','writer','CEL_FILE_PATHS_SMOKE ')
    manual=(folder/'safe.has').read_bytes();moved=[]
    try:
        for name in ['directory','tone.wav','writer-cache']:
            p=folder/name;offline=folder/(name+'.offline');p.rename(offline);moved.append((p,offline))
        run('tests/cel_file_paths_smoke.gd','reader','CEL_FILE_PATHS_READ ',extra=['--read'])
    finally:
        for p,offline in moved:offline.rename(p)
    assert (folder/'safe.has').read_bytes()==manual and hashlib.sha256((folder/'tone.wav').read_bytes()).hexdigest()==audio
    ffmpeg=os.environ.get('HYBRID_FFMPEG','ffmpeg');probe=str(Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe'));flags=dict(creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    media=json.loads(subprocess.check_output([probe,'-v','error','-show_streams','-show_format','-of','json',reports['writer']['movie']],**flags));video=next(s for s in media['streams'] if s['codec_type']=='video');assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_frames'])==('h264',1920,1080,'24/1','48') and abs(float(media['format']['duration'])-2)<.001 and any(s['codec_name']=='aac' for s in media['streams'])
    pcm=array.array('h');pcm.frombytes(subprocess.check_output([ffmpeg,'-v','error','-i',reports['writer']['movie'],'-vn','-ac','1','-ar','48000','-f','s16le','pipe:1'],**flags))
    if sys.byteorder!='little':pcm.byteswap()
    onset=next(i for i,v in enumerate(pcm) if abs(v)>1000);assert abs(onset-48000)<96
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==digest for p,digest in frozen.items())
    proof=dict(reports=reports,video=video,decoded_onset_sample=onset,originals_and_writer_cache_unavailable_for_cold=True,manual_has_unchanged=True,source_audio_unchanged=True,functional_unchanged=True,private_receipts=receipts,isolated_display=options.isolated_display,folder=str(folder));(folder/'verification.json').write_text(json.dumps(proof,indent=2));print(json.dumps(proof,indent=2))

if __name__=='__main__':main()
