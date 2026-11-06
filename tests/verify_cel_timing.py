"""Direct held-drawing moves, nested history, full60second movie and cold/crash restoration."""
from pathlib import Path
import argparse,array,hashlib,json,math,os,subprocess,sys,time,wave,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--isolated-display',help='Linux: explicitly provisioned private dummy X display')
    parser.add_argument('--output',type=Path)
    options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Linux requires a private --isolated-display; no shared-desktop fallback')
        os.environ['DISPLAY']=options.isolated_display
    folder=(options.output or ROOT/'output/cel-timing'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
    frozen={p:hashlib.sha256(p.read_bytes()).hexdigest() for name in ['src','tests','tools','data','examples'] for p in (ROOT/name).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts};reports={};receipts=[]
    def run(script,label,marker,extra=(),headless=False,crash=False,scene=None):
        args=command(script,headless=headless,extra=([str(scene)] if scene else [])+(['--audio-driver','Dummy'] if os.name!='nt' else [])+['--',str(folder),*extra])
        result=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=1250 if label=='writer' else 180)
        log=result.stdout+result.stderr;(folder/(label+'.log')).write_text(log,encoding='utf-8')
        assert result.returncode==(-9 if crash and os.name!='nt' else 0) and marker in log and not any(v in log for v in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
        report=json.loads(next(line[len(marker):] for line in log.splitlines() if line.startswith(marker)));assert report['failures']==0;reports[label]=report
        if os.name=='nt' and not headless:
            receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_bytes())
            assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'],r
            receipts.append(str(receipt))
    run('tests/cel_timing_unit.gd','unit','CEL_TIMING_UNIT ',headless=True)
    data=array.array('h',(round(12000*math.sin(2*math.pi*1000*i/48000)) for i in range(24000)))
    if sys.byteorder!='little':data.byteswap()
    with wave.open(str(folder/'tone.wav'),'wb') as out:out.setparams((1,2,48000,0,'NONE','not compressed'));out.writeframes(data.tobytes())
    run('tests/cel_timing_tools_smoke.gd','tools','CEL_TIMING_TOOLS ')
    run('tests/cel_timing_smoke.gd','writer','CEL_TIMING_SMOKE ',['--export','--crash'],crash=True)
    assert not (folder/'graceful-exit.txt').exists();expected=json.loads((folder/'expected.json').read_bytes())
    manual={p:p.read_bytes() for p in [folder/'packed.has',folder/'linked.has']}
    for p in manual:
        with zipfile.ZipFile(p) as archive:
            manifest=json.loads(archive.read('project.json'));assert manifest['schema_version']==8 and manifest['timing_content_schema_version']==6
            assert [(c['start'],c['duration']) for c in manifest['layers'][1]['cels']]==[(1300,24),(1376,24)]
            assert manifest['sequence_graph']['assets'][0]['scene']['layers'][1]['cels'][0]['start']==80
    originals={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in [folder/'room.glb',folder/'tone.wav']};moved=[]
    try:
        for name in ['room.glb','tone.wav','writer-cache']:
            source=folder/name;offline=folder/(name+'.offline');source.rename(offline);moved.append((source,offline))
        run('tests/cel_timing_smoke.gd','reader-packed','CEL_TIMING_READ ',['--read','--packed-only'])
        scene=folder/'startup.tscn';scene.write_text('[gd_scene load_steps=3 format=3]\n[ext_resource type="Script" path="res://tests/sequence_startup_app.gd" id="1"]\n[ext_resource type="Script" path="res://tests/cel_timing_startup.gd" id="2"]\n[node name="Studio" type="Control"]\nlayout_mode=3\nanchors_preset=15\nanchor_right=1.0\nanchor_bottom=1.0\ngrow_horizontal=2\ngrow_vertical=2\nscript=ExtResource("1")\n[node name="Observer" type="Node" parent="."]\nscript=ExtResource("2")\n',encoding='utf-8')
        run(None,'startup','CEL_TIMING_STARTUP ',scene=scene)
    finally:
        for source,offline in moved:offline.rename(source)
    cache=folder/'writer-cache';offline=folder/'writer-cache.offline';cache.rename(offline)
    try:run('tests/cel_timing_smoke.gd','reader-linked','CEL_TIMING_READ ',['--read','--linked-only'])
    finally:offline.rename(cache)
    ffmpeg=os.environ.get('HYBRID_FFMPEG','ffmpeg');probe=str(Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe'));flags=dict(creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    media=json.loads(subprocess.check_output([probe,'-v','error','-show_streams','-show_format','-of','json',expected['movie']],**flags));video=next(v for v in media['streams'] if v['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_frames'])==('h264',1920,1080,'24/1','1440') and abs(float(media['format']['duration'])-60)<.01
    assert any(v['codec_name']=='aac' and v['sample_rate']=='48000' for v in media['streams'])
    pcm=array.array('h');pcm.frombytes(subprocess.check_output([ffmpeg,'-v','error','-i',expected['movie'],'-vn','-ac','1','-ar','48000','-f','s16le','pipe:1'],**flags))
    if sys.byteorder!='little':pcm.byteswap()
    onset=next(i for i,v in enumerate(pcm) if abs(v)>1000);assert abs(onset-2688000)<240,onset
    assert all(p.read_bytes()==blob for p,blob in manual.items()) and all(hashlib.sha256(p.read_bytes()).hexdigest()==digest for p,digest in originals.items())
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==digest for p,digest in frozen.items())
    proof=dict(reports=reports,video=video,decoded_onset_sample=onset,render_seconds=expected['render_seconds'],actual_abrupt_exit=True,originals_unavailable_for_packed_recovery=True,linked_sources_available=True,source_assets_unchanged=True,manual_has_unchanged=True,functional_unchanged=True,private_receipts=receipts,isolated_display=options.isolated_display,folder=str(folder))
    (folder/'verification.json').write_text(json.dumps(proof,indent=2),encoding='utf-8');print(json.dumps(proof,indent=2))

if __name__=='__main__':main()
