"""Editable crop/cutout masks with correct shadows, nested audio and portable scene storage."""
from pathlib import Path
import argparse,array,json,os,subprocess,sys,time,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--isolated-display',help='Linux: pre-provisioned private dummy X display')
    parser.add_argument('--output',type=Path)
    options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Linux requires an explicit private --isolated-display; no shared-desktop fallback')
        os.environ['DISPLAY']=options.isolated_display
    folder=(options.output or ROOT/'output/sequence-masks'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
    reports=[];receipts=[];manual={}
    for label,extra,marker in [('writer',[],'SEQUENCE_MASKS_SMOKE '),('reader',['--read'],'SEQUENCE_MASKS_READ ')]:
        args=command('tests/sequence_masks_smoke.gd',extra=(['--audio-driver','Dummy'] if os.name!='nt' else [])+['--',str(folder),*extra])
        p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=260)
        log=p.stdout+p.stderr;(folder/(label+'.log')).write_text(log,encoding='utf-8')
        assert p.returncode==0 and marker in log and not any(s in log for s in ['ERROR:','FAIL ','ObjectDB instances leaked','another exclusive child']),log
        report=json.loads(log.split(marker)[-1].splitlines()[0]);assert report['failures']==0;reports.append(report)
        if os.name=='nt':
            receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_bytes())
            assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'],r
            receipts.append(str(receipt))
        if label=='writer':manual={p:p.read_bytes() for p in folder.glob('*.has')}
        else:assert all(p.read_bytes()==blob for p,blob in manual.items())
    ffmpeg=os.environ.get('HYBRID_FFMPEG','ffmpeg');probe=str(Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe'))
    flags=dict(creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    media=json.loads(subprocess.check_output([probe,'-v','error','-show_streams','-show_format','-of','json',reports[0]['movie']],**flags))
    video=next(s for s in media['streams'] if s['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_frames'])==('h264',1920,1080,'24/1','48') and abs(float(media['format']['duration'])-2)<.001 and any(s['codec_name']=='aac' for s in media['streams']),media
    pcm=array.array('h');pcm.frombytes(subprocess.check_output([ffmpeg,'-v','error','-i',reports[0]['movie'],'-vn','-ac','1','-ar','48000','-f','s16le','pipe:1'],**flags))
    if sys.byteorder!='little':pcm.byteswap()
    onset=next(i for i,s in enumerate(pcm) if abs(s)>1000)/48000;assert abs(onset-.25)<.005,onset
    for path in manual:
        with zipfile.ZipFile(path) as archive:
            data=json.loads(archive.read('project.json'));graph=data['sequence_graph']
            assert data['schema_version']==6 and graph['format']=='studio_sequences_3' and len(graph['clips'])==2
            assert all(c['mask']==dict(rect=[800,400,50,100],invert=False) for c in graph['clips'])
            assert graph['assets'][0]['scene']['layers'][1]['cels'] and graph['assets'][0]['scene']['audio']
    proof=dict(reports=reports,video=video,child_audio_onset=onset,private_receipts=receipts,isolated_display=options.isolated_display,manual_has_unchanged=True,native_fixtures=0,folder=str(folder))
    (folder/'verification.json').write_text(json.dumps(proof,indent=2),encoding='utf-8');print(json.dumps(proof,indent=2))

if __name__=='__main__':main()
