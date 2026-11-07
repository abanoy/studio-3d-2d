"""Native720p/540p editing, coordinates, nested masks, cold HAS, checkpoint and MP4."""
from pathlib import Path
import argparse,array,hashlib,json,math,os,struct,subprocess,sys,time,wave
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command,configure_private_display

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--isolated-display');parser.add_argument('--output',type=Path);parser.add_argument('--profile',choices=['720p','540p','all'],default='all');args=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not args.isolated_display:parser.error('Linux requires an explicitly owned private display')
        configure_private_display(args.isolated_display)
    folder=(args.output or ROOT/'output/native-canvas'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False);reports={};receipts=[]
    unit_folder=folder/'metadata';unit_folder.mkdir()
    unit_process=subprocess.run(command('tests/native_canvas_unit.gd',headless=True,extra=['--log-file',str(unit_folder/'engine.log'),'--',str(unit_folder/'project')]),cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60)
    unit_log=unit_process.stdout+unit_process.stderr;(unit_folder/'console.log').write_text(unit_log)
    assert unit_process.returncode==0 and 'NATIVE_CANVAS_UNIT ' in unit_log and not any(x in unit_log for x in ['ERROR:','FAIL ','ObjectDB instances leaked']),unit_log
    metadata=json.loads(next(line.removeprefix('NATIVE_CANVAS_UNIT ') for line in unit_log.splitlines() if line.startswith('NATIVE_CANVAS_UNIT ')));assert metadata['failures']==0
    frozen={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for part in ['src','tests','tools'] for p in (ROOT/part).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
    for profile,size in [('720p',(1280,720)),('540p',(960,540))]:
        if args.profile not in ['all',profile]:continue
        case=folder/profile;case.mkdir();samples=array.array('h',(round(12000*math.sin(2*math.pi*1000*i/48000)) for i in range(24000)))
        if sys.byteorder!='little':samples.byteswap()
        with wave.open(str(case/'tone.wav'),'wb') as out:out.setparams((1,2,48000,0,'NONE','not compressed'));out.writeframes(samples.tobytes())
        sources={str(case/'tone.wav'):hashlib.sha256((case/'tone.wav').read_bytes()).hexdigest()}
        def run(label,marker,extra=()):
            argv=command('tests/native_canvas_smoke.gd',extra=['--audio-driver','Dummy','--log-file',str(case/(label+'-engine.log')),'--',str(case),profile,*extra])
            process=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=225)
            log=process.stdout+process.stderr;(case/(label+'.log')).write_text(log,encoding='utf-8')
            assert process.returncode==0 and marker in log and not any(x in log for x in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
            result=json.loads(next(line[len(marker):] for line in log.splitlines() if line.startswith(marker)));assert result['failures']==0
            if os.name=='nt':
                p=Path(argv[argv.index('--receipt')+1]);r=json.loads(p.read_text());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];receipts.append(str(p))
            return result
        writer=run('writer','NATIVE_CANVAS_SMOKE ');manual=(case/'native.has').read_bytes();nested=(case/'nested.has').read_bytes();(case/'writer-cache').rename(case/'writer-cache.offline')
        offline=[]
        try:
            for name in ['original.glb','tone.wav']:
                p=case/name;target=case/(name+'.offline');p.rename(target);offline.append((p,target))
            reader=run('reader','NATIVE_CANVAS_READ ',['--read'])
        finally:
            for p,target in offline:target.rename(p)
        assert (case/'native.has').read_bytes()==manual and (case/'nested.has').read_bytes()==nested
        ffmpeg=os.environ.get('HYBRID_FFMPEG','ffmpeg');probe=str(Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe'))
        assert all(int(writer[k])==writer[k] for k in ['fps_num','fps_den','duration_frames'])
        sequence=Path(writer['png_sequence']);metadata=json.loads((sequence/'sequence.json').read_text())
        assert metadata['rendered_frames']==writer['duration_frames'] and metadata['drawing_only'] and (metadata['video']['width'],metadata['video']['height'])==size
        frames=list(sequence.glob('frame_*.png'));assert len(frames)==writer['duration_frames']
        assert all(struct.unpack('>II',frame.read_bytes()[16:24])==size for frame in frames)
        media=json.loads(subprocess.check_output([probe,'-v','error','-count_frames','-show_streams','-of','json',writer['movie']]));video=next(s for s in media['streams'] if s['codec_type']=='video')
        assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',*size,str(int(writer['fps_num']))+'/'+str(int(writer['fps_den'])),str(int(writer['duration_frames']))) and any(s['codec_name']=='aac' for s in media['streams'])
        assert abs(float(video['duration'])-writer['duration_frames']*writer['fps_den']/writer['fps_num'])<.001
        pcm=array.array('h');pcm.frombytes(subprocess.check_output([ffmpeg,'-v','error','-i',writer['movie'],'-vn','-ac','1','-ar','48000','-f','s16le','pipe:1']))
        if sys.byteorder!='little':pcm.byteswap()
        onset=next(i for i,sample in enumerate(pcm) if abs(sample)>1000);assert abs(onset-round(24*writer['fps_den']/writer['fps_num']*48000))<96
        assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==digest for p,digest in sources.items())
        reports[profile]=dict(writer=writer,reader=reader,video=video,decoded_onset_sample=onset,manual_has_unchanged=True,originals_and_writer_cache_unavailable_for_reader=True)
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==digest for p,digest in frozen.items()),'functional source changed during verification'
    proof=dict(metadata=metadata,reports=reports,scope='Owned native profiles with actual GUI/GPU/native-size media and generated3D; not native ecosystem fidelity or hardware/artist acceptance.',private_receipts=receipts,isolated_display=args.isolated_display,functional_source_unchanged=True)
    (folder/'verification.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))
if __name__=='__main__':main()
