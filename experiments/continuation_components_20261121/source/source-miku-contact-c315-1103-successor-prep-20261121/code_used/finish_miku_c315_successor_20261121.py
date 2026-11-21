"""Finish source construction; never imports or runs the candidate."""
from pathlib import Path
import ast,hashlib,json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output';NEW=OUT/'source-miku-contact-c315-1103-successor-prep-20261121'
OLD=OUT/'source-miku-contact-1102-successor-prep-20261121'
REV='c31576d0c1d84030d51ec886f2f3976a60a70c7b'
def raw(p):return p.read_bytes()
def pin(p):
 b=raw(p);return (len(b),hashlib.sha256(b).hexdigest())
def put(name,b):
 p=NEW/name
 if p.exists():assert raw(p)==b,name
 else:p.write_bytes(b)
 return pin(p)
def replace(s,a,b):assert s.count(a)==1,a;return s.replace(a,b)
source=raw(NEW/'source1103_base.py')+b'\n'+raw(NEW/'full1103_guard_extension.py')
ast.parse(source);sp=put('source1103.py',source)
oldinputs=json.loads(raw(OLD/'INPUT_PINS.json'))
inputs={'format':'has_miku_contact_source_inputs_1103_1','baseline_revision':REV,'current_functional_source_count':1103,
 'application_adopted':False,'files':[],'targets':oldinputs['targets'],'completed_canonical_full_required':True,
 'completed_outer_isolated_full_required':True,'actual_private_receipts_required':True}
names=['qualified_ui_host.py','qualified_helpers.py','source1103.py','BASELINE_SOURCE1103.json','FULL182_GROUP_CONTRACT.json']+[r['path'] for r in oldinputs['files'] if r['path'].startswith('payload/')]
for name in names:
 n,h=pin(NEW/name);inputs['files'].append({'path':name,'bytes':n,'sha256':h})
ip=put('INPUT_PINS.json',(json.dumps(inputs,indent=2)+'\n').encode())
driver=raw(OLD/'run_miku_contact_qualification.py').decode()
driver=driver.replace('435dc02426a7cdd313e43fe674c9008520845428',REV).replace('1102','1103')
driver=replace(driver,"S_PIN = (11485, '1cc8384a4ad167b336eaccd819559b11a754c66ed2f0bc8ef4b7778cd7b063ce')",'S_PIN = '+repr(sp))
driver=replace(driver,"INPUT_PIN = (5757, '9ced328d471927d00fb6e40b8d0f8b0c840a5f69338d713acd85eaba96465e74')",'INPUT_PIN = '+repr(ip))
driver=replace(driver,"    parser.add_argument('--full-report-sha256', required=True)","    parser.add_argument('--full-report-sha256', required=True)\n    parser.add_argument('--full-outer-folder', type=Path, required=True)\n    parser.add_argument('--full-outer-launch-sha256', required=True)\n    parser.add_argument('--full-outer-completion-sha256', required=True)")
driver=replace(driver,'        options.full_completion_sha256, options.full_source_sha256, options.full_report_sha256)',
 '        options.full_completion_sha256, options.full_source_sha256, options.full_report_sha256,\n        options.full_outer_folder, options.full_outer_launch_sha256, options.full_outer_completion_sha256)')
driver=replace(driver,"              'full_source_sha256': options.full_source_sha256, 'full_report_sha256': options.full_report_sha256,",
 "              'full_source_sha256': options.full_source_sha256, 'full_report_sha256': options.full_report_sha256,\n              'full_outer_launch_sha256': options.full_outer_launch_sha256,\n              'full_outer_completion_sha256': options.full_outer_completion_sha256,")
ast.parse(driver);dp=put('run_miku_contact_qualification.py',driver.encode())
print(json.dumps({'helper':sp,'inputs':ip,'driver':dp}))
