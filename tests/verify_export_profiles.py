"""Actual named quality profiles, fixed source pixels/audio, cancellation/retry and decoding."""
from pathlib import Path
import argparse,array,hashlib,json,os,subprocess,sys,time,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import configure_private_display, command

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--isolated-display',help='Linux: pre-provisioned private dummy X display')
    parser.add_argument('--output',type=Path)
    options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Linux requires an explicit private --isolated-display; no shared-desktop fallback')
        configure_private_display(options.isolated_display)
    folder=(options.output or ROOT/'output/export-profiles'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
    reports=[];receipts=[];manual=None
    for label,extra,marker in [('writer',[],'EXPORT_PROFILES_SMOKE '),('reader',['--read'],'EXPORT_PROFILES_READ ')]:
        args=command('tests/export_profiles_smoke.gd',extra=(['--audio-driver','Dummy'] if os.name!='nt' else [])+['--',str(folder),*extra])
        p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=240)
        log=p.stdout+p.stderr;(folder/(label+'.log')).write_text(log,encoding='utf-8')
        assert p.returncode==0 and marker in log and not any(s in log for s in ['ERROR:','FAIL ','ObjectDB instances leaked','another exclusive child']),log
        report=json.loads(log.split(marker)[-1].splitlines()[0]);assert report['failures']==0;reports.append(report)
        if os.name=='nt':
            receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_bytes())
            assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'],r
            receipts.append(str(receipt))
        if label=='writer':manual=(folder/'Profiles.has').read_bytes()
        else:assert (folder/'Profiles.has').read_bytes()==manual
    ffmpeg=os.environ.get('HYBRID_FFMPEG','ffmpeg');probe=str(Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe'))
    flags=dict(creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    def rgb(path):return subprocess.check_output([ffmpeg,'-v','error','-i',str(path),'-an','-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],**flags)
    reference=rgb(reports[0]['reference']);assert len(reference)==1920*1080*3
    media={};decoded={}
    for profile,movie in reports[0]['movies'].items():
        info=json.loads(subprocess.check_output([probe,'-v','error','-show_streams','-show_format','-of','json',movie],**flags))
        video=next(s for s in info['streams'] if s['codec_type']=='video');audio=next(s for s in info['streams'] if s['codec_type']=='audio')
        assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_frames'])==('h264',1920,1080,'24/1','48') and audio['codec_name']=='aac' and abs(float(info['format']['duration'])-2)<.001,info
        pcm=array.array('h');pcm.frombytes(subprocess.check_output([ffmpeg,'-v','error','-i',movie,'-vn','-ac','1','-ar','48000','-f','s16le','pipe:1'],**flags))
        if sys.byteorder!='little':pcm.byteswap()
        onset=next(i for i,s in enumerate(pcm) if abs(s)>1000)/48000;assert abs(onset-1)<.005,onset
        pixels=rgb(movie);assert len(pixels)==len(reference)
        decoded[profile]=hashlib.sha256(pixels).hexdigest()
        media[profile]=dict(video=video,bytes=Path(movie).stat().st_size,audio_onset=onset,frame0_rgb_mse=sum((a-b)**2 for a,b in zip(reference,pixels))/len(reference),frame0_rgb_sha256=decoded[profile])
    assert decoded['small']!=decoded['standard'] and decoded['high']!=decoded['small'],decoded
    with zipfile.ZipFile(folder/'Profiles.has') as archive:
        data=json.loads(archive.read('project.json'));assert 'encoder_quality' not in data and 'export_profile' not in data['video']
    proof=dict(reports=reports,media=media,private_receipts=receipts,isolated_display=options.isolated_display,manual_has_unchanged=True,native_fixtures=0,folder=str(folder))
    (folder/'verification.json').write_text(json.dumps(proof,indent=2),encoding='utf-8');print(json.dumps(proof,indent=2))

if __name__=='__main__':main()
