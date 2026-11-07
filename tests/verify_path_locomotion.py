"""Read-only walking evaluator prototype; no editor or persistence acceptance claim."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path);options=parser.parse_args()
    folder=(options.output or ROOT/'output/path-locomotion'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
    source=ROOT/'examples/tutorials/Practice figure.glb';before=hashlib.sha256(source.read_bytes()).hexdigest()
    args=command('tests/path_locomotion_unit.gd',headless=True,extra=['--log-file',str(folder/'engine.log'),'--',str(folder)])
    result=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=45,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0);log=result.stdout+result.stderr;(folder/'run.log').write_text(log,encoding='utf-8');marker='PATH_LOCOMOTION_UNIT '
    assert result.returncode==0 and marker in log and not any(x in log for x in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
    proof=json.loads((folder/'verification.json').read_bytes());assert proof['failures']==0 and proof['samples']==97 and proof['maximum_foot_error']<.0002
    assert hashlib.sha256(source.read_bytes()).hexdigest()==before
    proof['source_sha256']={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['src/path_locomotion.gd','tests/path_locomotion_unit.gd','src/model.gd','src/foot_contacts.gd','src/limb_ik.gd','src/root_component_document.gd','examples/tutorials/Practice figure.glb']}
    proof['original_source_unchanged']=True;(folder/'verification.json').write_text(json.dumps(proof,indent=2),encoding='utf-8');print(json.dumps(proof,indent=2))

if __name__=='__main__':main()
