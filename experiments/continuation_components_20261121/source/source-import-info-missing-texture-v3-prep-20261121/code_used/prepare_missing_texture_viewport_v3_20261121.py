"""Narrow fixture-only viewport successor; no engine or Main modifications."""
from pathlib import Path
import hashlib,json,shutil
R=Path(__file__).resolve().parents[1]
D=R/'output/source-import-info-missing-texture-v3-prep-20261121'
P=R/'output/source-import-info-legacy-tests-v2-prep-20261121'
def pin(b):return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
assert not D.exists();D.mkdir()
name='tests/mmd_missing_texture_smoke.gd'
base=(P/'payload'/name).read_bytes()
assert pin(base)=={'bytes':3949,'sha256':'aaaa50b191f7aff04501dafbbfc9f0bcaf2253b007e90e3964c521898d3e2626'}
anchor=b'\troot.add_child(app)\n';assert base.count(anchor)==1
addition=b'\troot.size = Vector2i(1400,900)\n\troot.gui_embed_subwindows = true\n'
payload=base.replace(anchor,addition+anchor)
assert payload.replace(addition,b'',1)==base
for folder,raw in [('bases/v2',base),('bases/main',(P/'bases'/name).read_bytes()),('payload',payload)]:
 p=D/folder/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
(D/'code_used').mkdir();shutil.copyfile(__file__,D/'code_used'/Path(__file__).name)
def write(name,value):(D/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
write('TARGETS.json',{'format':'has_import_info_optional_missing_texture_v3_1','status':'SOURCE_ONLY_UNRUN_PENDING_PEER','targets':[{'path':name,'operation':'replace',**pin(payload),'base_bytes':len((P/'bases'/name).read_bytes()),'base_sha256':pin((P/'bases'/name).read_bytes())['sha256']}]})
write('CORRECTION.json',{'root_reported_legacy_owner':{'checks':53,'completed_cases':6,'status':'PASS','rerun_required':False},'root_reported_prior_combined_result':'FAIL: optional missing-texture progress popups had invalid 0-sized root positions, despite MISSING_TEXTURE_REOPEN true','actual_prior_stage':'C:/a/Programming/cloudflare/has-import-info-legacy-scopes-1795268756730492500','change':'Only set root viewport1400x900 and embedded subwindows before adding real app, matching existing headless app/map fixture setup.','all_v2_report_and_packed_offline_checks_byte_exact':True,'production_modified':False,'this_successor_executed':False})
(D/'README.md').write_text('Fixture-only viewport setup successor. Original v2 optional native run remains failed; its REOPEN true marker alone does not override strict window errors. Actual owner53 passed separately and needs no repeat. This successor preserves all v2 persistent-info and packed/cold/offline checks byte-exact. Native successor remains UNRUN pending Root execution. No production change.\n',encoding='utf-8')
files=[{'path':p.relative_to(D).as_posix(),**pin(p.read_bytes())} for p in sorted(D.rglob('*')) if p.is_file()]
write('SOURCE_PINS.json',{'format':'has_source_only_pins_1','status':'SOURCE_ONLY_UNRUN_PENDING_PEER','files':files})
print(json.dumps({'packet':str(D),'files':len(files)+1,'manifest':pin((D/'SOURCE_PINS.json').read_bytes()),'target':pin(payload)},indent=2))
