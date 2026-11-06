"""Clean-scene lesson autosave scheduling, failure safety, SIGKILL and normal startup."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import configure_private_display,command

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--isolated-display',help='Linux: explicitly provisioned private dummy X display')
    parser.add_argument('--output',type=Path)
    options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Linux requires a private --isolated-display; no shared-desktop fallback')
        configure_private_display(options.isolated_display)
    folder=(options.output or ROOT/'output/lesson-autosave'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
    originals={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'examples/tutorials').rglob('*') if p.is_file()}
    reports={};receipts=[]
    def run(script,label,marker,scene=None,crash=False):
        args=command(script,extra=([str(scene)] if scene else [])+(['--audio-driver','Dummy'] if os.name!='nt' else [])+['--log-file',str(folder/(label+'-engine.log')),'--',str(folder)])
        p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=125)
        log=p.stdout+p.stderr;(folder/(label+'.log')).write_text(log,encoding='utf-8')
        assert p.returncode==(-9 if crash and os.name!='nt' else 0) and marker in log and not any(x in log for x in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
        reports[label]=json.loads(next(s[len(marker):] for s in log.splitlines() if s.startswith(marker)));assert reports[label]['failures']==0
        if os.name=='nt':
            path=Path(args[args.index('--receipt')+1]);r=json.loads(path.read_bytes());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];receipts.append(str(path))
    run('tests/lesson_autosave_smoke.gd','writer','LESSON_AUTOSAVE_WRITER ',crash=True)
    assert not (folder/'graceful-exit.txt').exists() and not (folder/'kill-returned.txt').exists()
    expected=json.loads((folder/'expected.json').read_bytes());manual=Path(expected['manual']).read_bytes()
    (folder/'writer-cache').rename(folder/'writer-cache.offline')
    scene=folder/'startup.tscn';scene.write_text('[gd_scene load_steps=3 format=3]\n[ext_resource type="Script" path="res://tests/lesson_recovery_app.gd" id="1"]\n[ext_resource type="Script" path="res://tests/lesson_autosave_observer.gd" id="2"]\n[node name="Studio" type="Control"]\nlayout_mode=3\nanchors_preset=15\nanchor_right=1.0\nanchor_bottom=1.0\ngrow_horizontal=2\ngrow_vertical=2\nscript=ExtResource("1")\n[node name="Observer" type="Node" parent="."]\nscript=ExtResource("2")\n',encoding='utf-8')
    run(None,'startup','LESSON_AUTOSAVE_STARTUP ',scene=scene)
    assert Path(expected['manual']).read_bytes()==manual and all(hashlib.sha256(p.read_bytes()).hexdigest()==digest for p,digest in originals.items())
    proof=dict(reports=reports,actual_abrupt_exit=True,manual_has_unchanged=True,included_assets_unchanged=True,writer_cache_unavailable_for_startup=True,private_receipts=receipts,isolated_display=options.isolated_display,folder=str(folder));(folder/'verification.json').write_text(json.dumps(proof,indent=2),encoding='utf-8');print(json.dumps(proof,indent=2))

if __name__=='__main__':main()
