"""Actual Home workflow plus unchanged production startup before/after recovery."""
from pathlib import Path
import argparse,json,os,shutil,subprocess,sys,time,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command,configure_private_display
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--isolated-display');parser.add_argument('--output',type=Path);o=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not o.isolated_display:parser.error('Explicit private display required; no shared fallback')
        configure_private_display(o.isolated_display)
    folder=(o.output or ROOT/'output/home'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False);receipts=[];results=[]
    frozen={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for part in ['src','tests','tools','examples'] for p in (ROOT/part).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts}
    dummy=["--audio-driver","Dummy"] if os.name!="nt" else []
    def run(args,label,marker):
        p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=150)
        log=p.stdout+p.stderr;(folder/(label+'.log')).write_text(log,encoding='utf-8')
        assert p.returncode==0 and marker in log and '"failures":0' in log and not any(x in log for x in ('ERROR:','FAIL ','ObjectDB instances leaked','another exclusive child')),log
        if os.name=='nt':
            receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_text(encoding='utf-8'));assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'],r
            receipts.append(str(receipt))
        return json.loads(log.split(marker)[-1].splitlines()[0])
    result=run(command('tests/home_smoke.gd',extra=dummy+['--',str(folder)]),'home','HOME_SMOKE ')
    scene=folder/'startup.tscn';scene.write_text('[gd_scene load_steps=3 format=3]\n[ext_resource type="Script" path="res://tests/home_startup_app.gd" id="1"]\n[ext_resource type="Script" path="res://tests/home_startup_observer.gd" id="2"]\n[node name="Studio" type="Control"]\nlayout_mode=3\nanchors_preset=15\nanchor_right=1.0\nanchor_bottom=1.0\ngrow_horizontal=2\ngrow_vertical=2\nscript=ExtResource("1")\n[node name="Observer" type="Node" parent="."]\nscript=ExtResource("2")\n',encoding='utf-8')
    for label in ('empty','recovered'):
        if label=='recovered':shutil.copytree(folder/'pending/recovery/interrupted',folder/'recovery/interrupted')
        results.append(run(command(extra=dummy+[str(scene),'--',str(folder),label]),label,'HOME_STARTUP '))
    assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha for name,sha in frozen.items())
    result.update(startup=results,private_receipts=receipts,source_sha256=frozen,isolated_display=o.isolated_display);
    (folder/'verification.json').write_text(json.dumps(result,indent=2));(ROOT/'output/home-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!="source_sha256"},indent=2))
if __name__=='__main__':main()
