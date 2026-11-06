"""Kept reference PNGs: Undo, packed/linked portability, actual crash and normal startup."""
from pathlib import Path
import argparse,array,hashlib,json,os,subprocess,sys,time,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import configure_private_display, command

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--isolated-display',help='Linux: explicit pre-provisioned private X display')
    parser.add_argument('--output',type=Path)
    options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Linux requires an explicit private --isolated-display; no shared-desktop fallback')
        configure_private_display(options.isolated_display)
    folder=(options.output or ROOT/'output/project-reference'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
    frozen={p:hashlib.sha256(p.read_bytes()).hexdigest() for name in ['src','tests','tools','data','examples'] for p in (ROOT/name).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts}
    reports={};receipts=[]
    def run(script,label,extra,marker,headless=False,abrupt=False,scene=None):
        args=command(script,headless=headless,extra=([str(scene)] if scene else [])+(['--audio-driver','Dummy'] if os.name!='nt' else [])+['--',str(folder/'unit-files' if headless else folder/'lesson-files' if label=='lesson' else folder),*extra])
        p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=280)
        log=p.stdout+p.stderr;(folder/(label+'.log')).write_text(log,encoding='utf-8')
        assert p.returncode==(-9 if abrupt and os.name!='nt' else 0) and marker in log and not any(s in log for s in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
        report=json.loads(next(line[len(marker):] for line in log.splitlines() if line.startswith(marker)));assert report['failures']==0;reports[label]=report
        if os.name=='nt' and not headless:
            receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_bytes())
            assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'],r
            receipts.append(str(receipt))
    run('tests/reference_sheet_storage_unit.gd','unit',[],'REFERENCE_SHEET_STORAGE_UNIT ',True)
    run('tests/reference_project_smoke.gd','writer',['--crash'],'REFERENCE_PROJECT_SMOKE ',abrupt=True)
    assert not (folder/'graceful-exit.txt').exists() and not (folder/'kill-returned.txt').exists()
    manual={p:p.read_bytes() for p in folder.glob('*.has')}
    expected=json.loads((folder/'expected.json').read_bytes())
    for p in manual:
        with zipfile.ZipFile(p) as archive:
            data=json.loads(archive.read('project.json'));assert data['schema_version']==7 and data['content_schema_version']==(6 if p.name.startswith('Nested') else 3)
            reference=data['reference_sheet'];assert reference['sha256']==expected['reference'] and reference['path']=='references/'+expected['reference']+'.png'
            header=json.loads(archive.read('has.json'));record=next(r for r in header['assets'] if r['path']==reference['path'])
            if header['storage']=='packed':assert hashlib.sha256(archive.read(reference['path'])).hexdigest()==reference['sha256']
            else:assert (p.parent/record['reference']).is_file() and hashlib.sha256((p.parent/record['reference']).read_bytes()).hexdigest()==reference['sha256']
    # A valid container with an invalid kept PNG must fail in Studio before
    # replacing the current scene, identity or reference state.
    from tools import has_project as has
    invalid_folder=folder/'invalid-reference-work'
    has.unpack(dict(path=str(folder/'Nested packed.has'),folder=str(invalid_folder)))
    invalid_manifest=json.loads((invalid_folder/'project.json').read_bytes())
    invalid_bytes=b'invalid PNG data';digest=hashlib.sha256(invalid_bytes).hexdigest();name='references/'+digest+'.png'
    (invalid_folder/name).write_bytes(invalid_bytes);invalid_manifest['reference_sheet'].update(path=name,sha256=digest)
    (invalid_folder/'project.json').write_bytes(has.json_bytes(invalid_manifest))
    has.pack(dict(folder=str(invalid_folder),path=str(folder/'Invalid PNG.has'),storage='packed',references={},cache_root=str(folder)))
    moved=[]
    try:
        for name in ['Original sheet α.png','Replacement.png','writer-sheet-cache']:
            source=folder/name;target=folder/(name+'.unavailable');source.rename(target);moved.append((source,target))
        run('tests/reference_project_smoke.gd','reader',['--read'],'REFERENCE_PROJECT_READ ')
        scene=folder/'startup.tscn';scene.write_text('[gd_scene load_steps=3 format=3]\n[ext_resource type="Script" path="res://tests/sequence_startup_app.gd" id="1"]\n[ext_resource type="Script" path="res://tests/reference_project_startup.gd" id="2"]\n[node name="Studio" type="Control"]\nlayout_mode=3\nanchors_preset=15\nanchor_right=1.0\nanchor_bottom=1.0\ngrow_horizontal=2\ngrow_vertical=2\nscript=ExtResource("1")\n[node name="Observer" type="Node" parent="."]\nscript=ExtResource("2")\n',encoding='utf-8')
        run(None,'startup',[],'REFERENCE_PROJECT_STARTUP ',scene=scene)
    finally:
        for source,target in moved:target.rename(source)
    run('tests/reference_lesson_smoke.gd','lesson',[],'REFERENCE_LESSON_SMOKE ')
    assert all(p.read_bytes()==blob for p,blob in manual.items())
    ffmpeg=os.environ.get('HYBRID_FFMPEG','ffmpeg');probe=str(Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe'))
    flags=dict(creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    media=json.loads(subprocess.check_output([probe,'-v','error','-show_streams','-show_format','-of','json',reports['writer']['movie']],**flags))
    video=next(s for s in media['streams'] if s['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_frames'])==('h264',1920,1080,'24/1','48') and abs(float(media['format']['duration'])-2)<.001 and any(s['codec_name']=='aac' for s in media['streams']),media
    pcm=array.array('h');pcm.frombytes(subprocess.check_output([ffmpeg,'-v','error','-i',reports['writer']['movie'],'-vn','-ac','1','-ar','48000','-f','s16le','pipe:1'],**flags))
    if sys.byteorder!='little':pcm.byteswap()
    onset=next(i for i,s in enumerate(pcm) if abs(s)>1000)/48000;assert abs(onset-.25)<.005,onset
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==digest for p,digest in frozen.items())
    result=dict(reports=reports,video=video,audio_onset=onset,private_receipts=receipts,isolated_display=options.isolated_display,actual_abrupt_exit=True,manual_has_unchanged=True,originals_and_writer_cache_unavailable_for_readers=True,functional_unchanged=True,native_fixtures=0,folder=str(folder))
    (folder/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
