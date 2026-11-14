from pathlib import Path
import hashlib,json,os,subprocess,sys,time
root=Path(__file__).resolve().parents[1]
folder=root/'output/contact-selection-wasapi-repeat-20261114'
assert not folder.exists();folder.mkdir()
expected=json.loads((root/'output/windows-canonical-inert-20261114T014831592/source-before.json').read_bytes())
def unchanged():
 return subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()==expected['commit'] and all(hashlib.sha256((root/n).read_bytes()).hexdigest()==digest for n,digest in expected['source_sha256'].items())
assert unchanged()
started=time.time_ns()
args=[sys.executable,'-B','-u',str(root/'tests/verify_contact_selection.py')]
with (folder/'console.log').open('w',encoding='utf-8') as stream:
 p=subprocess.run(args,cwd=root,stdout=stream,stderr=subprocess.STDOUT,timeout=230,creationflags=subprocess.CREATE_NO_WINDOW)
assert unchanged()
result={'format':'has_contact_selection_unchanged_WASAPI_repeat_1','exit':p.returncode,'source_commit':expected['commit'],'functional_sources':996,'source_and_head_unchanged':True,'started_ns':started,'finished_ns':time.time_ns(),'driver':'Original default WASAPI unchanged; no new driver option supplied.'}
if p.returncode==0:
 report_path=root/'output/contact-selection-verification.json'
 assert report_path.stat().st_mtime_ns>=started
 report=json.loads(report_path.read_bytes());result.update(checks=report['checks'],failures=report['failures'],report=report,report_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest())
(folder/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='report'}))
raise SystemExit(p.returncode)
