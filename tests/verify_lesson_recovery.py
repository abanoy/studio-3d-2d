"""Forced-crash lesson context, normal startup/fallback and whole-scene Previous."""
from pathlib import Path
import argparse,copy,hashlib,json,os,shutil,subprocess,sys,time,zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from run import configure_private_display,command

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--isolated-display',help='Linux: explicitly provisioned private dummy X display')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--case',choices=['all','newest'],default='all')
    options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Linux requires a private --isolated-display; no shared-desktop fallback')
        configure_private_display(options.isolated_display)
    folder=(options.output or ROOT/'output/lesson-recovery'/str(time.time_ns())).resolve()
    folder.mkdir(parents=True,exist_ok=False)
    originals={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'examples/tutorials').rglob('*') if p.is_file()}
    reports={};receipts=[]
    def run(script,label,marker,extra=(),scene=None,crash=False,argument_folder=None,headless=False):
        args=command(script,headless=headless,extra=([str(scene)] if scene else [])+(['--audio-driver','Dummy'] if os.name!='nt' else [])+['--log-file',str(folder/(label+'-engine.log')),'--',str(argument_folder or folder),*extra])
        result=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=165)
        log=result.stdout+result.stderr;(folder/(label+'.log')).write_text(log,encoding='utf-8')
        assert result.returncode==(-9 if crash and os.name!='nt' else 0) and marker in log and not any(x in log for x in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
        report=json.loads(next(x[len(marker):] for x in log.splitlines() if x.startswith(marker)));assert report['failures']==0,report
        reports[label]=report
        if os.name=='nt' and not headless:
            path=Path(args[args.index('--receipt')+1]);receipt=json.loads(path.read_bytes())
            assert receipt['exit']==0 and receipt['child_desktop_confirmed'] and not receipt['foreground_child_observed'] and receipt['job_closed'] and receipt['desktop_closed'],receipt
            receipts.append(str(path))
        return result
    run('tests/lesson_recovery_unit.gd','unit','LESSON_RECOVERY_UNIT ',headless=True)
    run('tests/lesson_recovery_writer.gd','writer','LESSON_RECOVERY_WRITER ',crash=True)
    assert not (folder/'graceful-exit.txt').exists() and not (folder/'kill-returned.txt').exists()
    expected=json.loads((folder/'expected.json').read_bytes());checkpoint=Path(expected['checkpoint'])
    assert checkpoint.resolve().is_relative_to((folder/'recovery').resolve())
    manual=Path(expected['manual']).read_bytes()
    with zipfile.ZipFile(expected['manual']) as archive:
        assert 'recovery' not in json.loads(archive.read('project.json'))['editor']
    # Every reader gets an independent copy of the same truly terminated writer's
    # state. Reader actions may legitimately update that copy's lesson progress.
    seed=folder/'seed';seed.mkdir()
    for name in ['recovery','tutorial-progress','writer-cache']:
        shutil.copytree(folder/name,seed/name)
    (folder/'writer-cache').rename(folder/'writer-cache.offline')
    cases=[('newest',18,True),('older-fallback',12,True),('legacy',18,False),('invalid-context',18,False),('missing-practice',18,False)]
    if options.case=='newest':cases=cases[:1]
    for label,target,attach in cases:
        case=folder/label;case.mkdir()
        for name in ['recovery','tutorial-progress']:
            shutil.copytree(seed/name,case/name)
        for name in ['frame12.png','frame18.png']:
            shutil.copy2(folder/name,case/name)
        case_expected=copy.deepcopy(expected)
        case_expected['checkpoint']=str(case/'recovery'/checkpoint.name)
        case_expected['lesson_folder']=str(case/'tutorial-progress'/expected['course']/expected['session'])
        (case/'expected.json').write_text(json.dumps(case_expected),encoding='utf-8')
        current=case/'recovery'/checkpoint.name/'project.json'
        doc=json.loads(current.read_bytes())
        if label=='older-fallback':
            # Also corrupt its matching immutable journal member; the journal
            # otherwise correctly offers the same newest generation again.
            digest=hashlib.sha256(current.read_bytes()).hexdigest()
            (current.parent/f'history_{digest}.json').write_text('{',encoding='utf-8')
            current.write_text('{',encoding='utf-8')
        elif label=='legacy':
            doc['editor']['recovery'].pop('lesson',None);current.write_text(json.dumps(doc),encoding='utf-8')
        elif label=='invalid-context':
            doc['editor']['recovery']['lesson']={'format':'studio_lesson_recovery_1','course':expected['course'],'session':'../escape','step':1,'done':False}
            current.write_text(json.dumps(doc),encoding='utf-8')
        elif label=='missing-practice':
            (case/'tutorial-progress').rename(case/'tutorial-progress.offline')
        # Frozen writer cache is not available; recovery must use its own assets.
        scene=case/'startup.tscn'
        scene.write_text('[gd_scene load_steps=3 format=3]\n[ext_resource type="Script" path="res://tests/lesson_recovery_app.gd" id="1"]\n[ext_resource type="Script" path="res://tests/lesson_recovery_observer.gd" id="2"]\n[node name="Studio" type="Control"]\nlayout_mode=3\nanchors_preset=15\nanchor_right=1.0\nanchor_bottom=1.0\ngrow_horizontal=2\ngrow_vertical=2\nscript=ExtResource("1")\n[node name="Observer" type="Node" parent="."]\nscript=ExtResource("2")\n',encoding='utf-8')
        run(None,label,'LESSON_RECOVERY_STARTUP ',extra=[label,str(target),'yes' if attach else 'no'],scene=scene,argument_folder=case)
        if label=='newest':
            with zipfile.ZipFile(case/'Saved recovered practice.has') as archive:
                assert 'recovery' not in json.loads(archive.read('project.json'))['editor']
        assert Path(expected['manual']).read_bytes()==manual
    movie=reports['newest']['movie'];ffmpeg=os.environ.get('HYBRID_FFMPEG','ffmpeg')
    ffprobe=str(Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe'))
    media=json.loads(subprocess.check_output([ffprobe,'-v','error','-show_streams','-show_format','-of','json',movie],creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0))
    video=next(x for x in media['streams'] if x['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_frames'])==('h264',1920,1080,'24/1','48') and abs(float(media['format']['duration'])-2)<.001
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==digest for p,digest in originals.items())
    assert not (folder/'writer-cache').exists()
    proof=dict(reports=reports,video=video,actual_abrupt_exit=True,manual_has_unchanged=True,included_assets_unchanged=True,writer_cache_unavailable_for_cold_startup=True,private_receipts=receipts,isolated_display=options.isolated_display,folder=str(folder))
    (folder/'verification.json').write_text(json.dumps(proof,indent=2),encoding='utf-8');print(json.dumps(proof,indent=2))

if __name__=='__main__':main()
