from pathlib import Path
import hashlib,importlib.util,json,subprocess
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output';REV='c31576d0c1d84030d51ec886f2f3976a60a70c7b'
def git(*args):return subprocess.check_output(['git','-c','core.autocrlf=false','-c','core.longpaths=true','-c','core.whitespace=cr-at-eol',*args],cwd=ROOT)
assert git('rev-parse','HEAD').decode().strip()==REV and not git('diff','--cached','--name-only')
plan=json.loads((OUT/'source-import-info-adoption-plan-prep-20261121/READY_ADOPTION_PLAN.json').read_bytes())
names={r['path'] for r in plan['targets']}|{'tests/wind_review_port_files.json','tests/helper_preview_port_files.json'}
docs=['LLM.md','docs/progress_memo.md','docs/RESUME_MASTER_PLAN.md','docs/NEXT_SESSION_PLAN_2026-11-20.md','docs/windows_acceptance_followup.md','docs/completion_checklist.json','docs/import_info.md','docs/benchmarks/components_followup_2026-11-21.json','docs/benchmarks/import_info_increment_2026-11-21.json']
names.update(docs);archive=ROOT/'experiments/continuation_components_20261121'
assert not (archive/'BUILDING.json').exists()
inv=json.loads((archive/'CONTENTS.json').read_bytes());assert len(inv['files'])==1108 and len(list(archive.rglob('SOURCE_PINS.json')))==35
names.update('experiments/continuation_components_20261121/'+r['path'] for r in inv['files']);names.add('experiments/continuation_components_20261121/CONTENTS.json')
assert len(names)==1136 and not any(n.startswith('output/') for n in names)
publication=ROOT/'experiments/import_info_publication_20261121'
publication_files=[p for p in publication.rglob('*') if p.is_file()]
assert len(publication_files)==14
names.update(p.relative_to(ROOT).as_posix() for p in publication_files)
assert len(names)==1150
tree={}
for raw in git('ls-tree','-rz','HEAD').split(b'\0'):
 if raw:
  meta,path=raw.split(b'\t',1);mode,kind,oid=meta.decode().split();tree[path.decode()]=(mode,oid)
rows=[]
for name in sorted(names):
 raw=(ROOT/name).read_bytes();blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest();assert name not in tree or tree[name][1]!=blob,name
 rows.append({'path':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'git_sha1':blob,'mode':tree.get(name,('100644',None))[0]})
value={'format':'has_import_info_publication_selection_1','base':REV,'paths':rows,'functional_source_count':1109,'canonical_groups':183,'selected_bytes':sum(r['bytes'] for r in rows),'generated_output_excluded':True,'new_Full_pass_claimed':False}
(OUT/'IMPORT_INFO_PUBLICATION_SELECTION_20261121.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({'paths':len(rows),'bytes':value['selected_bytes'],'base':REV}))
