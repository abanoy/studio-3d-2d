"""Actual Home workflow plus unchanged production startup before/after recovery."""
from pathlib import Path
import json,shutil,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command
def main():
    folder=ROOT/'output/home'/str(time.time_ns());folder.mkdir(parents=True);receipts=[];results=[]
    def run(args,label,marker):
        p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=150)
        log=p.stdout+p.stderr;(folder/(label+'.log')).write_text(log,encoding='utf-8')
        assert p.returncode==0 and marker in log and '"failures":0' in log and not any(x in log for x in ('ERROR:','FAIL ','ObjectDB instances leaked','another exclusive child')),log
        receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_text(encoding='utf-8'));assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'],r
        receipts.append(str(receipt));return json.loads(log.split(marker)[-1].splitlines()[0])
    result=run(command('tests/home_smoke.gd',extra=['--',str(folder)]),'home','HOME_SMOKE ')
    scene=folder/'startup.tscn';scene.write_text('[gd_scene load_steps=3 format=3]\n[ext_resource type="Script" path="res://tests/home_startup_app.gd" id="1"]\n[ext_resource type="Script" path="res://tests/home_startup_observer.gd" id="2"]\n[node name="Studio" type="Control"]\nlayout_mode=3\nanchors_preset=15\nanchor_right=1.0\nanchor_bottom=1.0\ngrow_horizontal=2\ngrow_vertical=2\nscript=ExtResource("1")\n[node name="Observer" type="Node" parent="."]\nscript=ExtResource("2")\n',encoding='utf-8')
    for label in ('empty','recovered'):
        if label=='recovered':shutil.copytree(folder/'pending/recovery/interrupted',folder/'recovery/interrupted')
        results.append(run(command(extra=[str(scene),'--',str(folder),label]),label,'HOME_STARTUP '))
    result.update(startup=results,private_receipts=receipts);(ROOT/'output/home-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
