from pathlib import Path
import hashlib,importlib.util,json,shutil,time
ROOT=Path(__file__).resolve().parents[1];PREP=ROOT/'output/source-scenario-d-wire-prep-20261121'
spec=importlib.util.spec_from_file_location('wire_adoption_source',ROOT/'experiments/reference_body_20261120/run_full.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
before=helper.snapshot();assert len(before)==1102
raw=(PREP/'SOURCE_PINS.json').read_bytes();assert hashlib.sha256(raw).hexdigest()=='227d1bf5f140ae559495e9654e21de173fcef9829899d3faeef542c52de7db3a'
for row in json.loads(raw)['files']:
    data=(PREP/row['path']).read_bytes();assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
targets=json.loads((PREP/'TARGETS.json').read_bytes())['targets']
assert {r['path'] for r in targets}=={'tests/scenario_d_smoke.gd','tests/scenario_d_wire_unit.gd','tests/verify_scenario_d.py'}
folder=ROOT/'output'/('scenario-d-wire-adoption-'+str(time.time_ns()));folder.mkdir()
for row in targets:
    path=ROOT/row['path'];source=PREP/'payload'/row['path'];data=source.read_bytes()
    assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
    if row['operation']=='new':assert not path.exists()
    else:
        old=path.read_bytes();assert len(old)==row['base_bytes'] and hashlib.sha256(old).hexdigest()==row['base_sha256']
        backup=folder/'bases'/row['path'];backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,backup)
for row in targets:
    path=ROOT/row['path'];data=(PREP/'payload'/row['path']).read_bytes()
    if row['operation']=='new':
        with path.open('xb') as stream:assert stream.write(data)==len(data)
    else:
        assert hashlib.sha256(path.read_bytes()).hexdigest()==row['base_sha256'];path.write_bytes(data)
    assert path.read_bytes()==data
after=helper.snapshot();assert len(after)==1103
unchanged=set(before)-{r['path'] for r in targets}
assert len(unchanged)==1100 and all(before[name]==after[name] for name in unchanged)
for name,value in [('source-before.json',before),('source-after.json',after)]:
    (folder/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
result={'format':'has_scenario_d_wire_adoption_1','status':'APPLIED_RUNTIME_UNRUN','functional_before':1102,'functional_after':1103,
 'unrelated_functional_hashes_and_mtime_preserved':1100,'targets':targets,'journal':str(folder),'whole_full_claimed':False,
 'numeric_or_pixel_tolerances_added':False,'production_sampler_or_persistence_changed':False}
(ROOT/'output/SCENARIO_D_WIRE_ADOPTION_20261121.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
host=(ROOT/'output/run_import_off_scenario_d_scoped_20261121.py').read_text().replace('1102','1103')
target=ROOT/'output/run_import_off_scenario_d_wire_scoped_20261121.py';assert not target.exists();target.write_text(host,encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='targets'}))
