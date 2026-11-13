"""Self-contained static Source choice CPU, control and private-app regression group."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));from run import command
BAD=('ERROR:','WARNING:','FAIL ','SCRIPT ERROR','ObjectDB instances leaked','unclaimed string names','Pages in use exist at exit')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(args,folder,label,timeout=120):
 p=subprocess.run(args,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',errors='replace',timeout=timeout);text=p.stdout+p.stderr;(folder/(label+'.log')).write_text(text,encoding='utf-8');assert p.returncode==0 and not any(x in text for x in BAD),str(folder)+'\n'+text[-5000:];return text

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path);opt=parser.parse_args();folder=(opt.output or ROOT/'output/source-choice-foundation'/str(time.time_ns())).resolve();assert folder.is_relative_to((ROOT/'output').resolve()) and not folder.exists();folder.mkdir(parents=True)
 names=['src/source_import.gd','src/source_choice_dialog.gd','tools/source_appearance.py','tools/source_mdl_choices.py','tools/source_choice_io.py','tools/prepare_source.py','tools/blender_source_bridge.py','tests/test_source_mdl_choices.py','tests/test_source_appearance.py','tests/source_choice_unit.gd','tests/source_choices_smoke.gd','tests/verify_source_choices.py',str(Path(__file__).relative_to(ROOT)),'run.py']
 before={n:sha(ROOT/n) for n in names};reports={}
 for label,test,expected,key in [('catalogue','test_source_mdl_choices.py',53,'folder'),('appearance','test_source_appearance.py',29,'run')]:
  text=run([sys.executable,'-B','tests/'+test],folder,label);rows=[json.loads(line) for line in text.splitlines() if line.startswith('{')];assert len(rows)==1;status=rows[0];assert status['passed'] and status['tests']==expected and status['failures']==status['errors']==0 and status['source_preserved'];reports[label]=json.loads((Path(status[key])/'result.json').read_bytes())
 unit=folder/'unit';unit.mkdir();text=run(command('tests/source_choice_unit.gd',headless=True,extra=['--log-file',str(unit/'engine.log'),'--',str(unit)]),folder,'unit');report=json.loads((unit/'result.json').read_bytes());assert report['checks']==65 and report['failures']==0 and report['graphics'] is False and report['native_conversion'] is False;reports['unit']=report
 text=run([sys.executable,'-B','tests/verify_source_choices.py','--output',str(folder/'ui')],folder,'ui',190);ui=json.loads((folder/'ui/verification.json').read_bytes());assert ui['result']['checks']==20 and ui['result']['failures']==0 and ui['source_unchanged'] and ui['originals_unchanged'];reports['ui']=ui
 assert before=={n:sha(ROOT/n) for n in names}
 result={'format':'has_source_choice_foundation_1','passed':True,'folder':str(folder),'checks':167,'reports':reports,'source_unchanged':True,'source_sha256':before,'private_receipt':ui['private_receipt'],'native_conversion':False,'scope':'53 authored native-table +29 appearance/IO +65 constructed-control/headless +20 actual private-app metadata checks; real native conversion/adoption separate'}
 (folder/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print('SOURCE_CHOICE_FOUNDATION '+json.dumps({'passed':True,'checks':167,'verification':str(folder/'verification.json')}))
if __name__=='__main__':main()
