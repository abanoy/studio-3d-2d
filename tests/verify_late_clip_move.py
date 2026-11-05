"""Decided frame3000→0 operation: source motion, private GUI, cold Open and actual crash."""
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
    folder=(options.output or ROOT/'output/late-clip-move'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
    frozen={p:hashlib.sha256(p.read_bytes()).hexdigest() for name in ['src','tests','tools','data','examples'] for p in (ROOT/name).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts};reports={};receipts=[]
    def run(target,script,label,marker,extra=(),crash=False,scene=None):
        args=command(script,extra=([str(scene)] if scene else [])+(['--audio-driver','Dummy'] if os.name!='nt' else [])+['--',str(target),*extra])
        result=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=240)
        log=result.stdout+result.stderr;(target/(label+'.log')).write_text(log,encoding='utf-8')
        assert result.returncode==(-9 if crash and os.name!='nt' else 0) and marker in log and not any(v in log for v in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
        report=json.loads(next(line[len(marker):] for line in log.splitlines() if line.startswith(marker)));assert report['failures']==0;reports[str(target.name)+'-'+label]=report
        if os.name=='nt':
            receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_bytes())
            assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'],r
            receipts.append(str(receipt))
    for mode in ['body','components']:
        target=folder/mode;target.mkdir();data=array.array('h',(round(12000*math.sin(2*math.pi*1000*i/48000)) for i in range(24000)))
        if sys.byteorder!='little':data.byteswap()
        with wave.open(str(target/'tone.wav'),'wb') as out:out.setparams((1,2,48000,0,'NONE','not compressed'));out.writeframes(data.tobytes())
        run(target,'tests/late_clip_move_smoke.gd','writer','LATE_CLIP_MOVE_SMOKE ',['--crash']+(['--components'] if mode=='components' else []),True)
        assert not (target/'graceful-exit.txt').exists();manual=(target/'packed.has').read_bytes()
        with zipfile.ZipFile(target/'packed.has') as archive:
            manifest=json.loads(archive.read('project.json'));assert manifest['schema_version']==8 and manifest['timing_content_schema_version']==4 and manifest['video']['duration_frames']==3600
        originals={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in [target/'actor.glb',target/'room.glb',target/'tone.wav']};moved=[]
        try:
            for name in ['actor.glb','room.glb','tone.wav','writer-cache']:
                source=target/name;offline=target/(name+'.offline');source.rename(offline);moved.append((source,offline))
            run(target,'tests/late_clip_move_smoke.gd','reader','LATE_CLIP_MOVE_READ ',['--read'])
            scene=target/'startup.tscn';scene.write_text('[gd_scene load_steps=3 format=3]\n[ext_resource type="Script" path="res://tests/sequence_startup_app.gd" id="1"]\n[ext_resource type="Script" path="res://tests/late_clip_move_startup.gd" id="2"]\n[node name="Studio" type="Control"]\nlayout_mode=3\nanchors_preset=15\nanchor_right=1.0\nanchor_bottom=1.0\ngrow_horizontal=2\ngrow_vertical=2\nscript=ExtResource("1")\n[node name="Observer" type="Node" parent="."]\nscript=ExtResource("2")\n',encoding='utf-8')
            run(target,None,'startup','LATE_CLIP_MOVE_STARTUP ',scene=scene)
        finally:
            for source,offline in moved:offline.rename(source)
        assert (target/'packed.has').read_bytes()==manual
        assert all(hashlib.sha256(p.read_bytes()).hexdigest()==digest for p,digest in originals.items())
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==digest for p,digest in frozen.items())
    proof=dict(reports=reports,actual_abrupt_exit=True,originals_and_writer_cache_unavailable_during_read=True,source_assets_unchanged=True,manual_has_unchanged=True,functional_unchanged=True,private_receipts=receipts,isolated_display=options.isolated_display,folder=str(folder))
    (folder/'verification.json').write_text(json.dumps(proof,indent=2),encoding='utf-8');print(json.dumps(proof,indent=2))

if __name__=='__main__':main()
