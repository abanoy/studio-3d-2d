"""Staged cold GUI edits/Undo, streamed HAS/checkpoint, late refusal, fresh reader and movie."""
from pathlib import Path
import argparse,array,hashlib,json,os,subprocess,sys,time,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import configure_private_display,command

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--isolated-display',help='Linux: explicitly provisioned private display')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--cool-history',action='store_true')
    parser.add_argument('--adaptive-open',action='store_true',help='Use staged normal adaptive directory/HAS loading instead of fixture injection')
    options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Linux requires --isolated-display; no shared-desktop fallback')
        configure_private_display(options.isolated_display)
    folder=(options.output or ROOT/'output/cel-raster-write'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
    flags=dict(creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    domain=subprocess.run([sys.executable,str(ROOT/'tests/verify_cel_raster_snapshot.py'),'--output',str(folder/'domain')],cwd=ROOT,capture_output=True,text=True,timeout=90,**flags)
    (folder/'domain.log').write_text(domain.stdout+domain.stderr,encoding='utf-8');assert domain.returncode==0,domain.stdout+domain.stderr
    reports={};receipts=[]
    def run(label,marker,extra=()):
        args=command('tests/cel_raster_write_smoke.gd',extra=(['--audio-driver','Dummy'] if os.name!='nt' else [])+['--log-file',str(folder/(label+'-engine.log')),'--',str(folder),*(['--adaptive-open'] if options.adaptive_open else []),*(['--cool-history'] if options.cool_history else []),*extra])
        result=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=380,**flags);log=result.stdout+result.stderr;(folder/(label+'.log')).write_text(log,encoding='utf-8')
        assert result.returncode==0 and marker in log and not any(s in log for s in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
        reports[label]=json.loads(next(s[len(marker):] for s in log.splitlines() if s.startswith(marker)));assert reports[label]['failures']==0
        if os.name=='nt':
            path=Path(args[args.index('--receipt')+1]);receipt=json.loads(path.read_bytes());assert receipt['exit']==0 and receipt['child_desktop_confirmed'] and not receipt['foreground_child_observed'] and receipt['job_closed'] and receipt['desktop_closed'];receipts.append(str(path))
    run('writer','CEL_RASTER_WRITE_SMOKE ')
    manual=folder/'Cold write.has';manual_bytes=manual.read_bytes();assert hashlib.sha256(manual_bytes).hexdigest()==reports['writer']['manual_sha256']
    (folder/'writer-cache').rename(folder/'writer-cache.offline');run('reader','CEL_RASTER_WRITE_READ ',['--read']);assert manual.read_bytes()==manual_bytes
    with zipfile.ZipFile(manual) as archive:
        raw=archive.read('project.json');manifest=json.loads(raw)
        assert not any(key in raw for key in [b'raster_owner',b'_payload',b'studio_pixels_revision'])
        expected=json.loads((folder/'expected.json').read_bytes())
        assert len(manifest['layers'][1]['cels'])==5
        for cel in manifest['layers'][1]['cels']:
            assert cel['start']==int(cel['start']) and cel['pixel_sha256']==expected['art'][str(int(cel['start']))]
        assert manifest['layers'][1]['cels'][4]['duration']==8
    ffmpeg=os.environ.get('HYBRID_FFMPEG','ffmpeg');probe=str(Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe'))
    movie=reports['writer']['movie'];media=json.loads(subprocess.check_output([probe,'-v','error','-show_streams','-show_format','-of','json',movie],**flags));video=next(s for s in media['streams'] if s['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_frames'])==('h264',1920,1080,'24/1','48') and abs(float(media['format']['duration'])-2)<.001 and any(s['codec_name']=='aac' for s in media['streams'])
    pcm=array.array('h');pcm.frombytes(subprocess.check_output([ffmpeg,'-v','error','-i',movie,'-vn','-ac','1','-ar','48000','-f','s16le','pipe:1'],**flags))
    if sys.byteorder!='little':pcm.byteswap()
    onset=next(i for i,value in enumerate(pcm) if abs(value)>1000);assert abs(onset-48000)<96
    sources=['tests/cel_raster_write_smoke.gd','tests/verify_cel_raster_write.py']
    proof=dict(scope='Explicit staged adaptive directory/HAS Open, cold GUI edits and streamed saves; default loading and abrupt startup recovery not certified.' if options.adaptive_open else 'Fixture-injected cold GUI edits and streamed saves. Normal loader and this fresh reader remain eager; cold adoption/abrupt cold recovery not enabled or certified.',domain=json.loads((folder/'domain/verification.json').read_bytes()),reports=reports,video=video,decoded_onset_sample=onset,manual_has_unchanged=True,writer_cache_unavailable_for_reader=True,private_receipts=receipts,isolated_display=options.isolated_display,source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sources})
    (folder/'verification.json').write_text(json.dumps(proof,indent=2),encoding='utf-8');print(json.dumps(proof,indent=2))

if __name__=='__main__':main()
