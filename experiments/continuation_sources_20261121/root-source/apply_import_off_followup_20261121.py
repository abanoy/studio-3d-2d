from pathlib import Path
import hashlib,json,os,shutil,stat,subprocess,time
ROOT=Path(__file__).resolve().parents[1]
PREP=ROOT/'output/source-import-off-followup-v3-prep-20261121'
EXPECTED={'tests/height_import_native_smoke.gd','src/first_movie_lesson.gd','tests/first_movie_smoke.gd','tests/scenario_d_smoke.gd','docs/physics.md','docs/scenario_d.md'}
def pin(path):
    s=path.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and not getattr(s,'st_file_attributes',0)&0x400
    raw=path.read_bytes()
    return {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'identity':[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_nlink,s.st_mode]}
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()=='435dc02426a7cdd313e43fe674c9008520845428'
manifest=(PREP/'SOURCE_PINS.json').read_bytes();assert hashlib.sha256(manifest).hexdigest()=='9eefa5ece644786feeaa2e9710fb55644a5e22f7de8ceef7bf85ab324c339463'
for row in json.loads(manifest)['files']:
    value=pin(PREP/row['path']);assert value['bytes']==row['bytes'] and value['sha256']==row['sha256']
names={p.relative_to(PREP/'payload').as_posix() for p in (PREP/'payload').rglob('*') if p.is_file()};assert names==EXPECTED
functional={}
for part in ('src','tests','tools','data','examples'):
    for p in (ROOT/part).rglob('*'):
        if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts:functional[p.relative_to(ROOT).as_posix()]=pin(p)
for name in ('project.godot','main.tscn','run.py','launch.pyw','dependencies.json',
 'experiments/reference_body_20261120/run_full.py','experiments/reference_body_20261120/stage_legacy_inputs.py',
 'experiments/reference_body_20261120/verify_units.py','experiments/reference_body_20261120/run_scoped.py',
 'experiments/reference_body_20261120/receipt_provenance.py','experiments/reference_body_20261120/test_receipt_provenance.py'):
    functional[name]=pin(ROOT/name)
assert len(functional)==1102
for name in names:assert (ROOT/name).read_bytes()==(PREP/'bases'/name).read_bytes()
journal=ROOT/'output'/('import-off-followup-adoption-'+str(time.time_ns()));journal.mkdir()
(journal/'before-functional.json').write_text(json.dumps(functional,indent=2)+'\n',encoding='utf-8')
for name in names:
    backup=journal/'bases'/name;backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,backup)
    assert backup.read_bytes()==(PREP/'bases'/name).read_bytes()
for name in sorted(names):
    target=ROOT/name
    assert target.read_bytes()==(PREP/'bases'/name).read_bytes()
    raw=(PREP/'payload'/name).read_bytes();assert target.write_bytes(raw)==len(raw) and target.read_bytes()==raw
unchanged=[name for name in functional if name not in names]
assert len(unchanged)==1098 and all(pin(ROOT/name)==functional[name] for name in unchanged)
result={'format':'has_import_off_followup_adoption_1','status':'APPLIED_SCOPED_RUNTIME_UNRUN','base_head':'435dc02426a7cdd313e43fe674c9008520845428',
 'changed_paths':sorted(names),'functional_changed':4,'functional_total':1102,'unrelated_functional_files_byte_identity_and_mtime_preserved':1098,
 'source_packet_sha256':hashlib.sha256(manifest).hexdigest(),'journal':str(journal),'paths':[{'path':name,**pin(ROOT/name)} for name in sorted(names)]}
(ROOT/'output/IMPORT_OFF_FOLLOWUP_ADOPTION_20261121.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='paths'}))
