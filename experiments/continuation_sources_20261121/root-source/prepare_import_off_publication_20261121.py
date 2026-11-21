from pathlib import Path
import hashlib,json,stat,subprocess,time
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output'
ARCHIVE=ROOT/'experiments/continuation_sources_20261121'
BASE='435dc02426a7cdd313e43fe674c9008520845428'
SELECTED=['LLM.md','docs/NEXT_SESSION_PLAN_2026-11-20.md','docs/RESUME_MASTER_PLAN.md',
 'docs/completion_checklist.json','docs/physics.md','docs/progress_memo.md','docs/scenario_d.md',
 'docs/windows_acceptance_followup.md','docs/benchmarks/import_off_followup_2026-11-21.json',
 'docs/benchmarks/character_parts_headless_2026-11-21.json',
 'src/first_movie_lesson.gd','tests/first_movie_smoke.gd','tests/height_import_native_smoke.gd',
 'tests/scenario_d_smoke.gd','tests/scenario_d_wire_unit.gd','tests/verify_scenario_d.py']
def git(*args):return subprocess.check_output(['git','-c','core.autocrlf=false',*args],cwd=ROOT)
assert git('rev-parse','HEAD').decode().strip()==BASE
assert not git('diff','--cached','--name-only'), 'Prior staged work must be preserved'
assert not (ARCHIVE/'BUILDING.json').exists(),'Archive not final'
inventory=json.loads((ARCHIVE/'CONTENTS.json').read_bytes())
assert isinstance(inventory,dict)
actual=[p for p in ARCHIVE.rglob('*') if p.is_file()]
for p in actual:
 assert not p.is_symlink() and p.lstat().st_nlink==1 and not getattr(p.lstat(),'st_file_attributes',0)&0x400
SELECTED+=sorted(p.relative_to(ROOT).as_posix() for p in actual)
assert len(set(p.casefold() for p in SELECTED))==len(SELECTED)
rows=[]
tree={}
for raw in git('ls-tree','-rz','HEAD').split(b'\0'):
 if not raw:continue
 meta,name=raw.split(b'\t',1);mode,kind,oid=meta.decode().split()
 tree[name.decode()]={'mode':mode,'oid':oid,'kind':kind}
for name in SELECTED:
 p=ROOT/name;s=p.lstat();raw=p.read_bytes();raw.decode('utf-8-sig')
 assert stat.S_ISREG(s.st_mode) and s.st_nlink==1
 row={'path':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
      'git_sha1':hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest(),
      'mode':tree.get(name,{}).get('mode','100644')}
 assert row['git_sha1']!=tree.get(name,{}).get('oid'),'Selected unchanged file '+name
 rows.append(row)
source=json.loads((OUT/'IMPORT_OFF_FINAL_FUNCTIONAL_CATALOGUE_20261121.json').read_bytes())
assert len(source)==1103
for name,row in source.items():
 raw=(ROOT/name).read_bytes()
 assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
record={'format':'has_import_off_publication_selection_1','base':BASE,'paths':rows,'count':len(rows),
 'bytes':sum(r['bytes'] for r in rows),'functional_count':1103,'archive_contents_sha256':hashlib.sha256((ARCHIVE/'CONTENTS.json').read_bytes()).hexdigest(),
 'created_ns':time.time_ns(),'tracked_generated_outputs_excluded':True}
target=OUT/'IMPORT_OFF_PUBLICATION_SELECTION_20261121.json';assert not target.exists()
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in record.items() if k!='paths'}))
