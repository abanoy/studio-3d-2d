"""Bounded journal, real Advanced preview/restore, and fresh-process deep fallback."""
from pathlib import Path
from native_fixture_root import fixture_output
import argparse,os,array,atexit,hashlib,json,math,subprocess,sys,time,wave
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command as engine_command,configure_private_display
from windows_owner_guard import WriterHandleGuard
def command(*args,**kwargs):
    argv=engine_command(*args,**kwargs)
    if os.name!='nt':
        pos=argv.index('--') if '--' in argv else len(argv);argv[pos:pos]=['--audio-driver','Dummy']
    return argv

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser();parser.add_argument('--isolated-display');parser.add_argument('--output',type=Path);options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Explicit private display required; no visible fallback')
        configure_private_display(options.isolated_display)
    folder=(options.output or ROOT/'output/recovery-history'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
    frozen={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for part in ['src','tests','tools','examples','data'] for p in (ROOT/part).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts}
    args=command('tests/recovery_journal_unit.gd',headless=True)
    p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=50)
    unit=p.stdout+p.stderr or (ROOT/'output/recovery_journal_unit-engine.log').read_text(encoding='utf-8')
    assert p.returncode==0 and 'RECOVERY_JOURNAL_UNIT ' in unit and '"failures":0' in unit and 'ERROR:' not in unit,unit
    unit_result=json.loads(unit.split('RECOVERY_JOURNAL_UNIT ')[-1].splitlines()[0])
    (folder/'unit.log').write_text(unit,encoding='utf-8')
    plans=[];base=fixture_output();originals={}
    for label,relative in [('MMD','pose-smoke/miku-project'),('GMod','source-smoke/source-project'),('SFM','sfm-smoke/project')]:
        project=base/relative
        if not (project/'project.json').is_file():continue
        doc=json.loads((project/'project.json').read_text(encoding='utf-8'));row=doc.get('model',{}) or doc['world']['objects'][-1]
        plans.append({'label':label,'source':str(project/row['path']),'metadata':row.get('metadata',{})})
    report=base/'native-import-verification.json'
    if report.is_file():
        for name in json.loads(report.read_text(encoding='utf-8')).get('bundles',[]):
            bundle=Path(name);parameters=json.loads((bundle/'parameters.json').read_text(encoding='utf-8'))
            if parameters.get('kind')=='vrm_preparation':plans.append({'label':'VRM'+parameters['vrm_version'],'source':str(bundle/'scene.glb'),'metadata':{}})
    for plan in plans:
        path=Path(plan['source']);originals[path]=(hashlib.sha256(path.read_bytes()).hexdigest(),path.stat().st_mtime_ns)
    (folder/'plan.json').write_text(json.dumps({'native':plans}),encoding='utf-8')
    samples=array.array('h',(int(16000*math.sin(2*math.pi*1000*n/44100)) for n in range(22050)))
    if sys.byteorder!='little':samples.byteswap()
    with wave.open(str(folder/'voice.wav'),'wb') as f:f.setparams((1,2,44100,0,'NONE','not compressed'));f.writeframes(samples.tobytes())
    receipts=[]
    def run(args,label,marker):
        p=subprocess.Popen(args,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',errors='replace')
        stdout,stderr=p.communicate(timeout=240)
        text=stdout+stderr;(folder/(label+'.log')).write_text(text,encoding='utf-8')
        assert p.returncode==0 and marker in text and '"failures":0' in text and not any(x in text for x in ('ERROR:','FAIL ','ObjectDB instances leaked','another exclusive child')),text
        if os.name=='nt':
            receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_text(encoding='utf-8'))
            assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'],r
            receipts.append(str(receipt))
        return p.pid
    guard=WriterHandleGuard(folder/'recovery') if os.name=='nt' else None
    if guard:atexit.register(guard.close)
    writer_pid=run(command('tests/recovery_history_smoke.gd',extra=['--',str(folder)]),'history','RECOVERY_HISTORY ')
    if guard:owner_proof=guard.writer_finished(json.loads(Path(receipts[-1]).read_text(encoding='utf-8'))['child_pid'])
    else:
        identity=json.loads(subprocess.check_output([sys.executable,str(ROOT/'tools/recovery_processes.py'),str(writer_pid)],text=True))
        assert identity['owners'][str(writer_pid)]=='exited',identity
        owner_proof=dict(pid=writer_pid,joined_writer_exit_verified=True,probe=identity)
    result=json.loads((folder/'result.json').read_text(encoding='utf-8'));expected=json.loads((folder/'expected.json').read_text(encoding='utf-8'))
    checkpoint=Path(expected['checkpoint']);assert checkpoint.resolve().is_relative_to((folder/'recovery').resolve())
    catalog=json.loads(json.loads((checkpoint/'journal.json').read_text(encoding='utf-8'))['payload'])
    selected=[checkpoint/'project.json',checkpoint/'project.backup.json',checkpoint/'journal.json',*[checkpoint/('history_'+e['sha256']+'.json') for e in catalog[:2]]]
    original={path:path.read_bytes() for path in selected}
    cases=[]
    for label,target in [('history-newest',17),('history-deep-fallback',15),('history-index-fallback',15)]:
        if guard:guard.assert_exited()
        for path,data in original.items():path.write_bytes(data)
        resolved=checkpoint/'resolved.json'
        if resolved.exists():resolved.unlink() # Only the owned fixture's explicit marker.
        if label!='history-newest':
            for path in selected:
                if path.name!='journal.json':path.write_bytes(b'{')
        if label=='history-index-fallback':(checkpoint/'journal.json').write_bytes(b'{')
        scene=folder/'reader.tscn'
        scene.write_text('[gd_scene load_steps=3 format=3]\n[ext_resource type="Script" path="res://tests/recovery_startup_app.gd" id="1"]\n[ext_resource type="Script" path="res://tests/recovery_startup_observer.gd" id="2"]\n[node name="Studio" type="Control"]\nlayout_mode=3\nanchors_preset=15\nanchor_right=1.0\nanchor_bottom=1.0\ngrow_horizontal=2\ngrow_vertical=2\nscript=ExtResource("1")\n[node name="Observer" type="Node" parent="."]\nscript=ExtResource("2")\n',encoding='utf-8')
        run(command(extra=[str(scene),'--',str(folder),label,str(target),'1']),label,'RECOVERY_STARTUP ')
        cases.append(json.loads((folder/(label+'-result.json')).read_text(encoding='utf-8')))
    for path,data in original.items():path.write_bytes(data)
    for path,state in originals.items():assert (hashlib.sha256(path.read_bytes()).hexdigest(),path.stat().st_mtime_ns)==state,path
    assert hashlib.sha256(Path(expected['manual']).read_bytes()).hexdigest()==expected['manual_sha256']
    ffmpeg=os.environ.get('HYBRID_FFMPEG','C:/Program Files/ffmpeg/bin/ffmpeg.exe' if os.name=='nt' else '/usr/bin/ffmpeg');ffprobe=str(Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe'))
    metadata=json.loads(subprocess.check_output([ffprobe,'-v','error','-count_frames','-show_streams','-of','json',result['movie']],text=True))
    video=next(s for s in metadata['streams'] if s['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48') and abs(float(video['duration'])-2)<.001
    assert any(s['codec_name']=='aac' for s in metadata['streams'])
    pcm=array.array('h');pcm.frombytes(subprocess.check_output([ffmpeg,'-v','error','-i',result['movie'],'-vn','-ar','48000','-ac','1','-f','s16le','pipe:1']))
    if sys.byteorder!='little':pcm.byteswap()
    onset=next(i for i,x in enumerate(pcm) if abs(x)>1000)/48000;assert abs(onset-1)<.002,onset
    if guard:guard.close();assert guard.closed
    result.update(unit_checks=unit_result['checks'],startup_cases=cases,private_receipts=receipts,audio_onset=onset,owner_identity=owner_proof,owner_handle_closed=guard.closed if guard else None,isolated_display=options.isolated_display,source_sha256=frozen)
    assert all(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest for path,digest in frozen.items())
    (folder/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    (ROOT/'output/recovery-history-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'},indent=2))
if __name__=='__main__':main()
