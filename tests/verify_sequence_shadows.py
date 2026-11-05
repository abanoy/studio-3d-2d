"""Real editable sequence shadows, source/alpha safety, cold HAS/recovery and MP4."""
from pathlib import Path
import argparse,json,os,subprocess,sys,time,zipfile
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
    folder=(options.output or ROOT/'output/sequence-shadows'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
    reports=[];receipts=[];manual={}
    for label,extra,marker in [('writer',[],'SEQUENCE_SHADOW_SMOKE '),('reader',['--read'],'SEQUENCE_SHADOW_READ ')]:
        args=command('tests/sequence_shadow_smoke.gd',extra=(['--audio-driver','Dummy'] if os.name!='nt' else [])+['--',str(folder),*extra])
        result=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=220)
        log=result.stdout+result.stderr;(folder/(label+'.log')).write_text(log,encoding='utf-8')
        assert result.returncode==0 and marker in log and not any(s in log for s in ['ERROR:','FAIL ','ObjectDB instances leaked','another exclusive child']),log
        report=json.loads(log.split(marker)[-1].splitlines()[0]);assert report['failures']==0;reports.append(report)
        if os.name=='nt':
            receipt=Path(args[args.index('--receipt')+1]);proof=json.loads(receipt.read_bytes())
            assert proof['exit']==0 and proof['child_desktop_confirmed'] and not proof['foreground_child_observed'] and proof['job_closed'] and proof['desktop_closed'],proof
            receipts.append(str(receipt))
        if label=='writer':manual={p:p.read_bytes() for p in folder.glob('*.has')}
        else:assert all(p.read_bytes()==blob for p,blob in manual.items())
    probe=str(Path(os.environ['HYBRID_FFMPEG']).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe')) if os.environ.get('HYBRID_FFMPEG') else 'ffprobe'
    video=json.loads(subprocess.check_output([probe,'-v','error','-select_streams','v:0','-show_entries','stream=codec_name,width,height,r_frame_rate,nb_frames','-of','json',reports[0]['movie']]))['streams'][0]
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_frames'])==('h264',1920,1080,'24/1','48'),video
    for path in manual:
        with zipfile.ZipFile(path) as archive:
            data=json.loads(archive.read('project.json'));graph=data['sequence_graph']
            assert data['schema_version']==6 and graph['format']=='studio_sequences_2'
            assert graph['clips'][0]['shadow']==dict(offset=[120,0],color=[0,0,0,.5],softness=0)
            assert graph['assets'][0]['scene']['layers'][1]['cels']
    proof=dict(reports=reports,video=video,private_receipts=receipts,isolated_display=options.isolated_display,manual_has_unchanged=True,native_fixtures=0,folder=str(folder))
    (folder/'verification.json').write_text(json.dumps(proof,indent=2),encoding='utf-8');print(json.dumps(proof,indent=2))

if __name__=='__main__':main()
