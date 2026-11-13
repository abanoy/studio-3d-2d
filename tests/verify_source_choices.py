"""Actual optional Source appearance widgets and metadata worker on private Windows desktop."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
from run import command
from test_source_mdl_choices import fixture
BAD=('ERROR:','WARNING:','FAIL ','SCRIPT ERROR','ObjectDB instances leaked','unclaimed string names','Pages in use exist at exit')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path);opt=parser.parse_args()
 folder=(opt.output or ROOT/'output/source-choices-ui'/str(time.time_ns())).resolve();assert folder.is_relative_to((ROOT/'output').resolve()) and not folder.exists();folder.mkdir(parents=True)
 raw,_=fixture(groups=[(b'tools',[(b'blank',7),(b'',0)]),(b'hat',[(b'hat',11),(b'',0)])]);(folder/'choices.mdl').write_bytes(raw);(folder/'bad.mdl').write_bytes(b'IDST broken native input')
 originals={n:sha(folder/n) for n in ['choices.mdl','bad.mdl']}
 names=['src/source_import.gd','src/source_choice_dialog.gd','tools/prepare_source.py','tools/source_appearance.py','tools/source_mdl_choices.py','tools/source_choice_io.py','tools/blender_source_bridge.py','tests/source_choices_smoke.gd',str(Path(__file__).relative_to(ROOT))]
 frozen={n:sha(ROOT/n) for n in names};(folder/'source-before.json').write_text(json.dumps(frozen,indent=2)+'\n',encoding='utf-8')
 args=command('tests/source_choices_smoke.gd',extra=['--audio-driver','Dummy','--log-file',str(folder/'engine.log'),'--',str(folder)])
 (folder/'command.json').write_text(json.dumps(args,indent=2)+'\n',encoding='utf-8')
 proc=subprocess.run(args,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',errors='replace',timeout=170)
 text=proc.stdout+proc.stderr;(folder/'stdout.log').write_text(text,encoding='utf-8');assert proc.returncode==0 and 'SOURCE_CHOICES_UI 'in text and not any(s in text for s in BAD),str(folder)+'\n'+text[-5000:]
 result=json.loads((folder/'result.json').read_bytes());assert result['failures']==0 and result['checks']>=19 and result['render_and_project_preserved']
 receipt_path=Path(args[args.index('--receipt')+1]);receipt=json.loads(receipt_path.read_bytes());assert receipt['exit']==0 and all(receipt.get(k)is True for k in ['private_window_seen','child_desktop_confirmed','job_closed','desktop_closed']) and all(receipt.get(k)is False for k in ['foreground_child_observed','desktop_switch_requested'])
 assert all(sha(folder/n)==v for n,v in originals.items());assert frozen=={n:sha(ROOT/n) for n in names}
 out={'format':'has_source_choices_ui_actual_1','result':result,'private_receipt':str(receipt_path),'receipt':receipt,'source_sha256':frozen,'source_unchanged':True,'originals':originals,'originals_unchanged':True,'scope':'Actual main app/dialog and real metadata Python processes; hand-authored tables only; native conversion/adoption remain separate'}
 (folder/'verification.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'checks':result['checks'],'folder':str(folder)}))
if __name__=='__main__':main()
