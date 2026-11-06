"""Real abrupt writer exit and unmodified normal startup with corrupt-generation fallback."""
from pathlib import Path
import argparse,array,atexit,copy,hashlib,json,math,os,re,shutil,subprocess,sys,time,wave
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import configure_private_display, command as engine_command

def command(*args,**kwargs):
    result=engine_command(*args,**kwargs)
    if os.name!='nt':
        position=result.index('--') if '--' in result else len(result)
        result[position:position]=['--audio-driver','Dummy']
    return result
from windows_owner_guard import WriterHandleGuard

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--isolated-display',help='Linux: pre-provisioned private dummy X display')
    options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Linux requires an explicit private --isolated-display; no shared-desktop fallback')
        configure_private_display(options.isolated_display)
    identity_field='created_100ns' if os.name=='nt' else 'linux_start'
    sys.stdout.reconfigure(encoding='utf-8')
    folder=ROOT/'output/recovery-startup'/str(time.time_ns());folder.mkdir(parents=True)
    def details(pid):return json.loads(subprocess.check_output([sys.executable,str(ROOT/'tools/recovery_processes.py'),str(pid)],text=True))
    def probe(pid):return details(pid)['owners'][str(pid)]
    assert probe(os.getpid())=='alive','unrelated parent process must be seen from the separate helper'
    child=subprocess.Popen([sys.executable,'-c','pass']);child.wait(timeout=20)
    assert probe(child.pid)=='exited','joined test child must be seen as stopped'
    base=Path(r'C:\a\Programming\cloudflare\prototypes\studio-3d-2d\output') if os.name=='nt' else folder/'no-native-fixtures';plans=[];originals={}
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
    def run(args,label,abrupt=False):
        p=subprocess.Popen(args,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',errors='replace')
        try:stdout,stderr=p.communicate(timeout=160)
        except subprocess.TimeoutExpired:
            p.kill();p.communicate(timeout=5);raise
        text=stdout+stderr;(folder/(label+'.log')).write_text(text,encoding='utf-8')
        r={'exit':p.returncode,'child_pid':p.pid}
        if os.name=='nt':
            receipt_path=Path(args[args.index('--receipt')+1]);r=json.loads(receipt_path.read_text(encoding='utf-8'))
            assert r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'],r
            receipts.append({'path':str(receipt_path),'expected_abrupt_exit':abrupt,'exit':r['exit']})
        assert not any(x in text for x in ('ERROR:','FAIL ','ObjectDB instances leaked','another exclusive child')),text
        if abrupt:
            # Godot's Windows OS.kill uses TerminateProcess(..., 0); zero does not
            # imply a graceful exit. Assert the post-call and teardown hooks did NOT run.
            assert (p.returncode==0 and r['exit']==0 if os.name=='nt' else p.returncode==-9) and 'RECOVERY_STARTUP_WRITER_READY' in text and (folder/'expected.json').is_file(),(p.returncode,text,r)
            assert not (folder/'graceful-exit.txt').exists() and not (folder/'kill-returned.txt').exists()
        else:assert p.returncode==0 and r['exit']==0 and 'RECOVERY_STARTUP ' in text,(p.returncode,text,r)
        return p
    guard=WriterHandleGuard(folder/'recovery') if os.name=='nt' else None
    if guard:atexit.register(guard.close)
    writer_process=run(command('tests/recovery_startup_writer.gd',extra=['--',str(folder)]),'writer',True)
    owner_proof=guard.writer_finished(json.loads(Path(receipts[-1]['path']).read_text(encoding='utf-8'))['child_pid']) if guard else {'pid':writer_process.pid,'writer_exit_verified':True,'verification':'joined SIGKILL writer and absent graceful hooks'}
    expected=json.loads((folder/'expected.json').read_text(encoding='utf-8'));checkpoint=Path(expected['checkpoint'])
    # Preserve this matrix as an actual legacy two-generation cache test. Current
    # journals/deeper fallback have their own normal-startup verification suite.
    assert checkpoint.resolve().is_relative_to((folder/'recovery').resolve())
    for path in checkpoint.iterdir():
        if path.is_file() and (path.name in ('journal.json','journal.backup.json') or re.fullmatch(r'(?:history_[0-9a-f]{64}\.json|preview_[0-9a-f]{64}\.png)',path.name)):path.unlink()
    primary=checkpoint/'project.json';backup=checkpoint/'project.backup.json';owner=checkpoint/'session.json';resolved=checkpoint/'resolved.json'
    original={p:p.read_bytes() for p in [primary,backup,owner]};latest=json.loads(original[primary]);prior=json.loads(original[backup])
    writer_identity=json.loads(original[owner]);parent_identity=details(os.getpid())[identity_field][str(os.getpid())]
    assert writer_identity[identity_field]!=parent_identity
    if os.name!='nt':assert writer_identity['pid']==writer_process.pid
    assert latest['editor']['frame']==24 and prior['editor']['frame']==12
    identity={'position':[0,0,0],'rotation_xyzw':[0,0,0,1]}
    cases=[('newest',24,1),('broken-json',12,1),('missing-asset',12,2),('bad-binding',12,2),('missing-audio',12,2),('all-invalid',-1,2),('live-writer',-1,0),('resolved',-1,0),('save',24,1)]
    cases.extend([('live-identified-writer',-1,0),('reused-pid',24,1),('invalid-owner-identity',-1,0),('helper-unavailable',-1,0),('current-pid-mismatch',24,1),('current-pid-match',-1,0)])
    results=[]
    for label,target,attempts in cases:
        if guard:guard.assert_exited()
        else:
            observed=details(writer_identity['pid']);key=str(writer_identity['pid'])
            assert observed['owners'][key]=='exited' or (observed['owners'][key]=='alive' and observed.get(identity_field,{}).get(key) not in (None,writer_identity[identity_field])),observed
        for path,data in original.items():path.write_bytes(data)
        if resolved.exists():resolved.unlink() # Only this fixture's explicitly known marker.
        data=copy.deepcopy(latest)
        if label=='broken-json':primary.write_bytes(b'{')
        elif label=='missing-asset':data['world']['objects'][0]['path']='assets/missing.glb'
        elif label in ('bad-binding','all-invalid'):
            row=next(x for x in data['world']['objects'] if x['kind']=='model');row['pose']['missing::bone']=identity
            if label=='all-invalid':
                bad=copy.deepcopy(prior);bad['world']['objects'][0]['path']='assets/missing.glb';backup.write_text(json.dumps(bad),encoding='utf-8')
        elif label=='missing-audio':data['audio']['path']='assets/missing.wav'
        elif label=='live-writer':owner.write_text(json.dumps({'pid':os.getpid()}),encoding='utf-8')
        elif label in ('live-identified-writer','helper-unavailable'):owner.write_text(json.dumps({'pid':os.getpid(),identity_field:parent_identity}),encoding='utf-8')
        elif label=='reused-pid':owner.write_text(json.dumps({'pid':os.getpid(),identity_field:writer_identity[identity_field]}),encoding='utf-8')
        elif label=='invalid-owner-identity':owner.write_text(json.dumps({'pid':os.getpid(),identity_field:123}),encoding='utf-8')
        elif label=='resolved':resolved.write_text(json.dumps({'sha256':hashlib.sha256(original[primary]).hexdigest()}),encoding='utf-8')
        if label in ('missing-asset','bad-binding','missing-audio','all-invalid'):primary.write_text(json.dumps(data),encoding='utf-8')
        # An ordinary scene launch, without --script or a smoke argument, exercises
        # app._ready's actual default startup path. The child only observes completion.
        scene=folder/'reader.tscn'
        scene_text='[gd_scene load_steps=3 format=3]\n[ext_resource type="Script" path="res://tests/recovery_startup_app.gd" id="1"]\n[ext_resource type="Script" path="res://tests/recovery_startup_observer.gd" id="2"]\n[node name="Studio" type="Control"]\nlayout_mode=3\nanchors_preset=15\nanchor_right=1.0\nanchor_bottom=1.0\ngrow_horizontal=2\ngrow_vertical=2\nscript=ExtResource("1")\n[node name="Observer" type="Node" parent="."]\nscript=ExtResource("2")\n'
        if label in ('current-pid-mismatch','current-pid-match','helper-unavailable'):scene_text=scene_text.replace('recovery_startup_app.gd','recovery_identity_app.gd')
        scene.write_text(scene_text,encoding='utf-8')
        before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in (primary,backup)}
        run(command(extra=[str(scene),'--',str(folder),label,str(target),str(attempts)]),label)
        result=json.loads((folder/(label+'-result.json')).read_text(encoding='utf-8'));assert result['failures']==0,result
        if label in ('invalid-owner-identity','helper-unavailable'):assert result['startup'].get('warning'),result
        assert before=={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in before},label
        assert hashlib.sha256(Path(expected['manual']).read_bytes()).hexdigest()==expected['manual_sha256'],label
        for path,state in originals.items():assert (hashlib.sha256(path.read_bytes()).hexdigest(),path.stat().st_mtime_ns)==state,path
        results.append(result);print('PASS normal startup '+label,flush=True)
    movie=results[0]['movie']
    ffmpeg=os.environ.get('HYBRID_FFMPEG') or (r'C:\Program Files\ffmpeg\bin\ffmpeg.exe' if os.name=='nt' else shutil.which('ffmpeg'))
    ffprobe=str(Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe'))
    probe=json.loads(subprocess.check_output([ffprobe,'-v','error','-count_frames','-show_streams','-of','json',movie],text=True))
    video=next(s for s in probe['streams'] if s['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48')
    assert abs(float(video['duration'])-2)<.001 and any(s['codec_name']=='aac' for s in probe['streams'])
    pcm=array.array('h');pcm.frombytes(subprocess.check_output([ffmpeg,'-v','error','-i',movie,'-vn','-ar','48000','-ac','1','-f','s16le','pipe:1']))
    if sys.byteorder!='little':pcm.byteswap()
    onset=next(i for i,x in enumerate(pcm) if abs(x)>1000)/48000;assert abs(onset-1)<.002,onset
    if guard:guard.close();assert guard.closed
    result={'checks':sum(x['checks'] for x in results),'failures':0,'cases':results,'native_models':len(plans),'folder':str(folder),'movie':movie,'audio_onset':onset,'private_receipts':receipts,'writer_abrupt_exit_verified':True,'owner_identity':owner_proof,'owner_handle_closed':guard.closed if guard else None,'isolated_display':options.isolated_display}
    (ROOT/'output/recovery-startup-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
