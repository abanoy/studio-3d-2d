"""Author original practice assets through the same standard GLB/HAS contract."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys,time,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command
from tools.has_project import pack
def main():
    stage=ROOT/'output/tutorial-authoring'/str(time.time_ns());stage.mkdir(parents=True)
    p=subprocess.run(command('tools/build_tutorial.gd',headless=True,extra=['--',str(stage)]),capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60)
    log=p.stdout+p.stderr;(stage/'build.log').write_text(log,encoding='utf-8')
    assert p.returncode==0 and '"error":""' in log and 'ERROR:' not in log,log
    pack({'folder':str(stage/'project'),'path':str(stage/'practice.has'),'storage':'packed'})
    pack({'folder':str(stage/'first-movie'),'path':str(stage/'first-movie.has'),'storage':'packed'})
    names=['Practice room.glb','Practice figure.glb','practice.has','first-movie.has']
    manifest={'format':'studio_tutorial_assets_1','version':2,'source':'Original procedural project geometry; example license remains owner decision','files':{name:{'sha256':hashlib.sha256((stage/name).read_bytes()).hexdigest(),'bytes':(stage/name).stat().st_size} for name in names}}
    if '--install' in sys.argv:
        destination=ROOT/'examples/tutorials';destination.mkdir(parents=True,exist_ok=True)
        old=json.loads((destination/'manifest.json').read_text(encoding='utf-8')) if (destination/'manifest.json').exists() else None
        for name in names:
            target=destination/name
            if target.exists():
                assert old and hashlib.sha256(target.read_bytes()).hexdigest()==old['files'][name]['sha256'],'Preserve edited sample: '+name
        for name in names:
            # ZIP timestamps may differ while every project/payload byte is the
            # same. Keep unchanged installed examples byte-identical.
            if name.endswith('.has') and (destination/name).exists():
                with zipfile.ZipFile(destination/name) as prior,zipfile.ZipFile(stage/name) as fresh:
                    if {n:prior.read(n) for n in prior.namelist()}=={n:fresh.read(n) for n in fresh.namelist()}:
                        manifest['files'][name]={'sha256':hashlib.sha256((destination/name).read_bytes()).hexdigest(),'bytes':(destination/name).stat().st_size}
                        continue
            if (destination/name).exists():
                (stage/'before').mkdir(exist_ok=True);shutil.copy2(destination/name,stage/'before'/name)
            shutil.copy2(stage/name,destination/name)
        (destination/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps({'stage':str(stage),'files':manifest['files']},indent=2))
if __name__=='__main__':main()
