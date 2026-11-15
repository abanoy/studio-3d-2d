"""Actual original-rig motion controls; native ecosystem tests remain separate."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command,configure_private_display

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--isolated-display');parser.add_argument('--output',type=Path,required=True);o=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not o.isolated_display:parser.error('Explicit private display required; no shared fallback')
        configure_private_display(o.isolated_display)
    folder=o.output.resolve();folder.mkdir(parents=True,exist_ok=False);reports={};receipts=[]
    frozen={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for part in ['src','tests','tools','data','examples'] for p in (ROOT/part).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts}
    for label,extra,marker in [('writer',[],'MOTION_ORIGINAL_WRITE '),('reader',['--read'],'MOTION_ORIGINAL_READ ')]:
        args=command('tests/motion_feeling_original_smoke.gd',extra=['--audio-driver','Dummy','--log-file',str(folder/(label+'-engine.log')),'--',str(folder),*extra]);r=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=180);log=r.stdout+r.stderr;(folder/(label+'.log')).write_text(log)
        assert r.returncode==0 and marker in log and not any(t in log for t in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
        reports[label]=json.loads(next(line[len(marker):] for line in log.splitlines() if line.startswith(marker)));assert reports[label]['failures']==0
        if os.name=='nt':
            p=Path(args[args.index('--receipt')+1]);v=json.loads(p.read_bytes());assert v['exit']==0 and v['child_desktop_confirmed'] and not v['foreground_child_observed'] and v['job_closed'] and v['desktop_closed'];receipts.append(str(p))
        if label=='writer':
            source=folder/'original-branches.glb';source_sha=hashlib.sha256(source.read_bytes()).hexdigest();source.rename(folder/'original-branches.glb.offline');(folder/'writer-cache').rename(folder/'writer-cache.offline');manual=hashlib.sha256((folder/'Motion feeling.has').read_bytes()).hexdigest()
    ffmpeg=os.environ.get('HYBRID_FFMPEG','ffmpeg');probe=str(Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe'));media=json.loads(subprocess.check_output([probe,'-v','error','-count_frames','-show_streams','-of','json',reports['writer']['movie']]));video=next(s for s in media['streams'] if s['codec_type']=='video');assert(video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48')
    assert hashlib.sha256((folder/'original-branches.glb.offline').read_bytes()).hexdigest()==source_sha and hashlib.sha256((folder/'Motion feeling.has').read_bytes()).hexdigest()==manual
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in frozen.items())
    proof=dict(reports=reports,video=video,source_sha256=frozen,original_and_writer_cache_offline=True,source_and_manual_has_unchanged=True,private_receipts=receipts,isolated_display=o.isolated_display,scope='Original two-branch skinned rig: actual Simple trial/Apply/Cancel, editable per-part/helper corrections, Off, Undo, exact main keys, reverse seek, cold packed replay and movie. No native ecosystem, planted-contact, artist or physical-device certification.')
    (folder/'verification.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items() if k!='source_sha256'},indent=2))
if __name__=='__main__':main()
