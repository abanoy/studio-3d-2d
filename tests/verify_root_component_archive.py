"""Model9 metadata roundtrip and ordinary Godot document loading."""
from pathlib import Path
import hashlib,json,subprocess,sys,time,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from run import command
import has_project as has
def main():
    folder=ROOT/'output/component-archive'/str(time.time_ns());folder.mkdir(parents=True)
    source=Path(json.loads((ROOT/'output/contact-persistence-verification.json').read_text())['writer']['packed']);digest=has.sha(source)
    snapshot=folder/'snapshot';assert has.unpack({'path':str(source),'folder':str(snapshot)})['ok']
    def run(path,cold=False):
        a=command('tests/root_component_archive.gd',headless=True,extra=['--',str(path),*(['cold']if cold else [])]);p=subprocess.run(a,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60);s=p.stdout+p.stderr;(folder/('cold.log'if cold else'writer.log')).write_text(s,encoding='utf-8');assert p.returncode==0 and '"failures":0'in s and 'ERROR:'not in s,s
    run(snapshot);expected=json.loads((snapshot/'project.json').read_text(encoding='utf-8'));target=folder/'components.has'
    has.pack({'folder':str(snapshot),'path':str(target),'storage':'packed','references':{},'cache_root':str(folder/'cache')})
    opened=folder/'opened';assert has.unpack({'path':str(target),'folder':str(opened)})['ok'];assert json.loads((opened/'project.json').read_text(encoding='utf-8'))==expected
    run(opened,True);assert has.sha(source)==digest
    result={'folder':str(folder),'packed':str(target),'source_unchanged':True,'metadata_exact':True,'ordinary_reader_accepts':True,'normal_app_updated':False}
    (ROOT/'output/component-archive-verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
