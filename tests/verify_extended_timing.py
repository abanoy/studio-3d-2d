"""Long parents, bounded children/imports, explicit schema8, cold storage and SIGKILL recovery."""
from pathlib import Path
import argparse,array,hashlib,json,math,os,subprocess,sys,time,wave,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import configure_private_display, command
from tools import has_project

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--isolated-display',help='Linux: explicitly provisioned private dummy X display')
    parser.add_argument('--output',type=Path)
    options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Linux requires a private --isolated-display; no shared desktop fallback')
        configure_private_display(options.isolated_display)
    folder=(options.output or ROOT/'output/extended-timing'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
    frozen={p:hashlib.sha256(p.read_bytes()).hexdigest() for name in ['src','tests','tools','data','examples'] for p in (ROOT/name).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts}
    reports={};receipts=[]
    def run(script,label,marker,extra=(),headless=False,crash=False,scene=None):
        args=command(script,headless=headless,extra=([str(scene)] if scene else [])+(['--audio-driver','Dummy'] if os.name!='nt' else [])+['--',str(folder/'unit' if headless else folder),*extra])
        result=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=920)
        log=result.stdout+result.stderr;(folder/(label+'.log')).write_text(log,encoding='utf-8')
        assert result.returncode==(-9 if crash and os.name!='nt' else 0) and marker in log and not any(v in log for v in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
        report=json.loads(next(line[len(marker):] for line in log.splitlines() if line.startswith(marker)));assert report['failures']==0;reports[label]=report
        if os.name=='nt' and not headless:
            receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_bytes())
            assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'],r
            receipts.append(str(receipt))
    run('tests/extended_timing_unit.gd','unit','EXTENDED_TIMING_UNIT ',headless=True)
    run('tests/extended_motion_unit.gd','motion-unit','EXTENDED_MOTION_UNIT ',headless=True)
    for p in (folder/'unit').glob('*/project.json'):has_project.members(json.loads(p.read_bytes()))
    samples=array.array('h',(round(12000*math.sin(2*math.pi*1000*i/48000)) for i in range(24000)))
    if sys.byteorder!='little':samples.byteswap()
    with wave.open(str(folder/'tone.wav'),'wb') as out:out.setparams((1,2,48000,0,'NONE','not compressed'));out.writeframes(samples.tobytes())
    ffmpeg=os.environ.get('HYBRID_FFMPEG','ffmpeg');flags=dict(creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    subprocess.run([ffmpeg,'-v','error','-f','lavfi','-i','color=c=0x204080:s=64x32:r=24:d=0.25','-an','-c:v','libx264','-pix_fmt','yuv420p',str(folder/'artwork.mp4')],check=True,**flags)
    originals={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in [folder/'tone.wav',folder/'artwork.mp4']}
    run('tests/extended_timing_smoke.gd','writer','EXTENDED_TIMING_SMOKE ',['--crash'],crash=True)
    assert not (folder/'graceful-exit.txt').exists()
    manual={p:p.read_bytes() for p in [folder/'packed.has',folder/'linked.has']}
    for p in manual:
        with zipfile.ZipFile(p) as archive:
            manifest=json.loads(archive.read('project.json'))
            assert manifest['schema_version']==8 and manifest['timing_content_schema_version']==7 and manifest['content_schema_version']==6 and manifest['video']['duration_frames']==1440
            assert manifest['sequence_graph']['assets'][0]['scene']['video']['duration_frames']==240
            assert any(layer.get('origin',{}).get('format')=='studio_drawing_origin_4' for layer in manifest['layers'])
            has_project.members(manifest)
    expected=json.loads((folder/'expected.json').read_bytes());moved=[]
    try:
        for name in ['figure.glb','reference.png','artwork.mp4','tone.wav','writer-cache']:
            source=folder/name;target=folder/(name+'.offline');source.rename(target);moved.append((source,target))
        run('tests/extended_timing_smoke.gd','reader-packed','EXTENDED_TIMING_READ ',['--read','--packed-only'])
        scene=folder/'startup.tscn';scene.write_text('[gd_scene load_steps=3 format=3]\n[ext_resource type="Script" path="res://tests/sequence_startup_app.gd" id="1"]\n[ext_resource type="Script" path="res://tests/extended_timing_startup.gd" id="2"]\n[node name="Studio" type="Control"]\nlayout_mode=3\nanchors_preset=15\nanchor_right=1.0\nanchor_bottom=1.0\ngrow_horizontal=2\ngrow_vertical=2\nscript=ExtResource("1")\n[node name="Observer" type="Node" parent="."]\nscript=ExtResource("2")\n',encoding='utf-8')
        run(None,'startup','EXTENDED_TIMING_STARTUP ',scene=scene)
    finally:
        for source,target in moved:target.rename(source)
    # Linked mode deliberately retains external source references. Its originals
    # remain available while the writer cache is still taken offline.
    cache=folder/'writer-cache';offline=folder/'writer-cache.offline';cache.rename(offline)
    try:run('tests/extended_timing_smoke.gd','reader-linked','EXTENDED_TIMING_READ ',['--read','--linked-only'])
    finally:offline.rename(cache)
    assert all(p.read_bytes()==blob for p,blob in manual.items())
    probe=str(Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe'))
    media=json.loads(subprocess.check_output([probe,'-v','error','-show_streams','-show_format','-of','json',expected['movie']],**flags));video=next(v for v in media['streams'] if v['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_frames'])==('h264',1920,1080,'12/1','252') and abs(float(media['format']['duration'])-21)<.01
    assert any(v['codec_name']=='aac' and v['sample_rate']=='48000' for v in media['streams'])
    decoded=array.array('h');decoded.frombytes(subprocess.check_output([ffmpeg,'-v','error','-i',expected['movie'],'-vn','-ac','1','-ar','48000','-f','s16le','pipe:1'],**flags))
    if sys.byteorder!='little':decoded.byteswap()
    onset=next(i for i,v in enumerate(decoded) if abs(v)>1000);assert abs(onset-976000)<240,onset
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==digest for p,digest in originals.items())
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==digest for p,digest in frozen.items())
    proof=dict(reports=reports,video=video,decoded_onset_sample=onset,private_receipts=receipts,isolated_display=options.isolated_display,original_sources_unchanged=True,originals_unavailable_for_packed_lesson_and_recovery=True,linked_originals_available=True,manual_has_unchanged=True,functional_unchanged=True,folder=str(folder))
    (folder/'verification.json').write_text(json.dumps(proof,indent=2),encoding='utf-8');print(json.dumps(proof,indent=2))

if __name__=='__main__':main()
