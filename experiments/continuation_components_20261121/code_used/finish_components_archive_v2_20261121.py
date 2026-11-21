"""Resume owned BUILDING archive; admit the exact legacy entries schema."""
from pathlib import Path
import importlib.util,json,time
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output';DEST=ROOT/'experiments/continuation_components_20261121'
spec=importlib.util.spec_from_file_location('_archive_resume',OUT/'finalize_continuation_archive_20261121.py');A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A);A.EXT.update({'.godot','.tscn','.cfg','.bat','.sh','.svg'})
assert (DEST/'BUILDING.json').is_file()
old_raw=A.read(DEST/'CONTENTS.json');old=A.load(old_raw);expected={r['path'] for r in old['files']}
assert {p.relative_to(DEST).as_posix() for p in A.files(DEST)}==expected|{'CONTENTS.json','BUILDING.json'}
for row in old['files']:
 raw=A.read(DEST/A.rel(row['path']));assert len(raw)==row['bytes'] and A.digest(raw)==row['sha256'];A.privacy(row['path'],raw)
prior=DEST/'root-addendum/FAILED_INITIAL_CONTENTS.json';assert not prior.exists();(DEST/'CONTENTS.json').rename(prior)
old_audit=DEST/'code_used/audit_components_archive.py';preserved=DEST/'code_used/audit_components_archive_v1.py';assert not preserved.exists();old_audit.rename(preserved)
text=A.read(preserved).decode();needle="manifests+=1; m=load(data); declared=m['files']; names=set()";assert text.count(needle)==1
replace="""manifests+=1; m=load(data); names=set()
            if 'files' in m: declared=m['files']
            else:
                need(m.get('format')=='has_import_capability_diagnostics_source_candidate_1' and isinstance(m.get('entries'),list), 'unknown source manifest schema')
                declared=m['entries']"""
text=text.replace(needle,replace);old_audit.write_text(text,encoding='utf-8')
failure={'status':'ARCHIVE_AUDIT_FAILED_BEFORE_FINALIZATION','tool_result':'ea42e4 exit1','error_type':'KeyError','missing_key':'files','cause':'One fully preserved historical source manifest declares its five exact payloads under entries. No payload was missing or altered.','repair':'Recognize only that explicit historical format/entries schema and retain all exact membership/SHA/privacy checks. Prior inventory and auditor source preserved.','Full_claimed':False,'recorded_ns':time.time_ns()}
(DEST/'root-addendum/INITIAL_ARCHIVE_AUDIT_FAILURE.json').write_text(json.dumps(failure,indent=2)+'\n')
target=DEST/'code_used/finish_components_archive_v2_20261121.py';target.write_bytes(Path(__file__).read_bytes())
with (DEST/'README.md').open('a',encoding='utf-8') as stream:stream.write('\nThe initial archive audit refused one historical SOURCE_PINS manifest using its\nexplicit `entries` schema. Both the failed draft inventory and first auditor are\nretained. The current auditor recognizes only that named schema in addition to\n`files`, with identical payload membership and raw SHA checks.\n')
origins={r['path']:r.get('source','Frozen declared payload') for r in old['files']};origins['root-addendum/FAILED_INITIAL_CONTENTS.json']='Exact unfinalized first inventory; its failed audit is retained';origins['code_used/audit_components_archive_v1.py']='Exact first auditor before explicit legacy schema recognition'
rows=[]
for path in A.files(DEST):
 name=path.relative_to(DEST).as_posix()
 if name=='BUILDING.json':continue
 raw=A.read(path);A.privacy(name,raw);rows.append({'path':name,'source':origins.get(name,'Explicit Root finalization addendum'),'bytes':len(raw),'sha256':A.digest(raw)})
contents={**{k:v for k,v in old.items() if k not in ('files','payload_files','payload_bytes')},'payload_files':len(rows),'payload_bytes':sum(r['bytes'] for r in rows),'files':rows}
(DEST/'CONTENTS.json').write_text(json.dumps(contents,indent=2)+'\n')
spec=importlib.util.spec_from_file_location('_fixed_source_auditor',old_audit);fixed=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixed)
result=fixed.audit(DEST,True);marker=DEST/'BUILDING.json';assert marker.resolve().parent==DEST.resolve();marker.unlink();assert fixed.audit(DEST)==result
result.update(format='has_components_archive_finalization_v2_1',archive=str(DEST),new_Full_claimed=False,recorded_ns=time.time_ns())
(OUT/'IMPORT_INFO_COMPONENT_ARCHIVE_FINAL_20261121.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
