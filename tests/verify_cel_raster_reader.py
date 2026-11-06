"""Independent cel Images over shared decoded PNG storage; real edits, cold HAS, SIGKILL and AAC."""
from pathlib import Path
import argparse,array,hashlib,json,math,os,subprocess,sys,time,wave,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import configure_private_display,command
from png_reader_fixtures import make_fixtures

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--isolated-display',help='Linux: explicitly provisioned private dummy X display');parser.add_argument('--output',type=Path);parser.add_argument('--adaptive-open',action='store_true');options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Linux requires a private --isolated-display; no shared-desktop fallback')
        configure_private_display(options.isolated_display)
    folder=(options.output or ROOT/'output/cel-raster-reader'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
    frozen={p:hashlib.sha256(p.read_bytes()).hexdigest() for name in ['src','tests','tools','data','examples'] for p in (ROOT/name).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts};reports={};receipts=[]
    samples=array.array('h',(round(12000*math.sin(2*math.pi*1000*i/48000)) for i in range(24000)))
    if sys.byteorder!='little':samples.byteswap()
    with wave.open(str(folder/'tone.wav'),'wb') as out:out.setparams((1,2,48000,0,'NONE','not compressed'));out.writeframes(samples.tobytes())
    audio=hashlib.sha256((folder/'tone.wav').read_bytes()).hexdigest()
    corpus=folder/"png-corpus";make_fixtures(corpus)
    def run(script,label,marker,headless=False,extra=(),crash=False,scene=None,argument_folder=None):
        args=command(script,headless=headless,extra=([str(scene)] if scene else [])+(['--audio-driver','Dummy'] if os.name!='nt' else [])+['--log-file',str(folder/(label+'-engine.log')),'--',str(argument_folder or folder),*(['--adaptive-open'] if options.adaptive_open else []),*extra])
        result=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=195)
        log=result.stdout+result.stderr;(folder/(label+'.log')).write_text(log,encoding='utf-8')
        assert result.returncode==(-9 if crash and os.name!='nt' else 0) and marker in log and not any(x in log for x in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
        reports[label]=json.loads(next(x[len(marker):] for x in log.splitlines() if x.startswith(marker)));assert reports[label]['failures']==0
        if os.name=='nt' and not headless:
            path=Path(args[args.index('--receipt')+1]);receipt=json.loads(path.read_bytes());assert receipt['exit']==0 and receipt['child_desktop_confirmed'] and not receipt['foreground_child_observed'] and receipt['job_closed'] and receipt['desktop_closed'];receipts.append(str(path))
    run('tests/cel_raster_reader_unit.gd','unit','CEL_RASTER_READER_UNIT ',True)
    run('tests/png_reader_compatibility.gd','png-compatibility','PNG_READER_COMPATIBILITY ',True,extra=['--adaptive'] if options.adaptive_open else [],argument_folder=corpus)
    run('tests/cel_raster_reader_smoke.gd','writer','CEL_RASTER_READER_SMOKE ',extra=['--crash'],crash=True)
    assert not (folder/'graceful-exit.txt').exists();expected=json.loads((folder/'expected.json').read_bytes());manual=(folder/'shared.has').read_bytes()
    with zipfile.ZipFile(folder/'shared.has') as archive:
        manifest=json.loads(archive.read('project.json'));cels=manifest['layers'][0]['cels'];assert len(cels)==32 and len({row['id'] for row in cels})==32 and len({row['path'] for row in cels})==2
        assert all(row['path'] in archive.namelist() for row in cels) and manifest['schema_version']==4
    source=folder/'source-project';assert hashlib.sha256((source/'drawing.png').read_bytes()).hexdigest()==expected['source_png_sha256'] and hashlib.sha256((source/'project.json').read_bytes()).hexdigest()==expected['source_manifest_sha256']
    moved=[]
    try:
        for name in ['source-project','tone.wav','writer-cache']:
            p=folder/name;offline=folder/(name+'.offline');p.rename(offline);moved.append((p,offline))
        run('tests/cel_raster_reader_smoke.gd','reader','CEL_RASTER_READER_READ ',extra=['--read'])
        scene=folder/'startup.tscn';scene.write_text('[gd_scene load_steps=3 format=3]\n[ext_resource type="Script" path="res://tests/sequence_startup_app.gd" id="1"]\n[ext_resource type="Script" path="res://tests/cel_raster_reader_startup.gd" id="2"]\n[node name="Studio" type="Control"]\nlayout_mode=3\nanchors_preset=15\nanchor_right=1.0\nanchor_bottom=1.0\ngrow_horizontal=2\ngrow_vertical=2\nscript=ExtResource("1")\n[node name="Observer" type="Node" parent="."]\nscript=ExtResource("2")\n',encoding='utf-8')
        run(None,'startup','CEL_RASTER_READER_STARTUP ',scene=scene)
    finally:
        for p,offline in moved:offline.rename(p)
    assert (folder/'shared.has').read_bytes()==manual and hashlib.sha256((folder/'tone.wav').read_bytes()).hexdigest()==audio
    ffmpeg=os.environ.get('HYBRID_FFMPEG','ffmpeg');probe=str(Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe'));flags=dict(creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    media=json.loads(subprocess.check_output([probe,'-v','error','-show_streams','-show_format','-of','json',reports['writer']['movie']],**flags));video=next(x for x in media['streams'] if x['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_frames'])==('h264',1920,1080,'24/1','48') and abs(float(media['format']['duration'])-2)<.001 and any(x['codec_name']=='aac' for x in media['streams'])
    pcm=array.array('h');pcm.frombytes(subprocess.check_output([ffmpeg,'-v','error','-i',reports['writer']['movie'],'-vn','-ac','1','-ar','48000','-f','s16le','pipe:1'],**flags))
    if sys.byteorder!='little':pcm.byteswap()
    onset=next(i for i,v in enumerate(pcm) if abs(v)>1000);assert abs(onset-48000)<96
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==digest for p,digest in frozen.items())
    proof=dict(adaptive_open=options.adaptive_open,reports=reports,video=video,decoded_onset_sample=onset,actual_abrupt_exit=True,originals_and_writer_cache_unavailable_for_cold_startup=True,manual_has_unchanged=True,source_assets_unchanged=True,functional_unchanged=True,private_receipts=receipts,isolated_display=options.isolated_display,folder=str(folder))
    (folder/'verification.json').write_text(json.dumps(proof,indent=2),encoding='utf-8');print(json.dumps(proof,indent=2))

if __name__=='__main__':main()
