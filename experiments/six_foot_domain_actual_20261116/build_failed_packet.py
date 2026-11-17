"""Archive only synthetic failed-domain metadata; never copy a staged app/model."""
from pathlib import Path
import gzip,hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'output/six-foot-domain-20261116-attempt1'
DEST=ROOT/'experiments/six_foot_domain_initial_actual_packet_20261116'
v=json.loads((RUN/'verification.json').read_bytes());r=json.loads((RUN/'Studio/output/domain/result.json').read_bytes())
assert not v['passed'] and r['checks']==444 and r['failures']==7 and r['complete_assertion_set'] and v['runtime_lease_released']
DEST.mkdir();manifest=[]
files=['before-closure.json','before-inventory-stdout.log','before-inventory-stderr.log','after-closure.json','after-inventory-stdout.log','after-inventory-stderr.log','verification.json']
for prefix in ('domain-parse','domain-run'):
    files.extend(prefix+suffix for suffix in ('-command.json','-start.json','-process.json','-stdout.log','-stderr.log','-engine.log'))
files += ['Studio/output/domain/job.json','Studio/output/domain/result.json']
for name in files:
    p=RUN/name;target=DEST/'actual'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
    manifest.append({'source':p.relative_to(ROOT).as_posix(),'stored':target.relative_to(DEST).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
p=RUN/'SOURCE.json';target=DEST/'actual/SOURCE.json.gz';target.write_bytes(gzip.compress(p.read_bytes(),mtime=0))
manifest.append({'source':p.relative_to(ROOT).as_posix(),'stored':target.relative_to(DEST).as_posix(),'raw_bytes':p.stat().st_size,'raw_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'encoding':'gzip'})
for source in ('experiments/six_foot_domain_actual_20261116/run_owned.py','experiments/six_foot_import_basis_gd_candidate_20261116/basis_domain_unit.gd','experiments/six_foot_import_basis_gd_candidate_20261116/import_basis_domain.gd'):
    p=ROOT/source;target=DEST/'code'/p.name;target.parent.mkdir(exist_ok=True);shutil.copyfile(p,target)
    manifest.append({'source':source,'stored':target.relative_to(DEST).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
def save(name,value):(DEST/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
save('SOURCE_MANIFEST.json',{'format':'has_synthetic_domain_failed_exact_copies_1','files':manifest})
save('BENCHMARK.json',{'status':'FAILED_SYNTHETIC_DOMAIN','checks':444,'failures':7,'failed_names':[n for n,value in r['named_checks'].items() if not value],'parser_exit':0,'domain_exit':1,'boundary':'UNRUN_AFTER_FAILURE','runtime_lease_released':True,'main_source_modified':False,'actual_import_activation':False})
(DEST/'README.md').write_text('Initial isolated Godot domain run: parse passed,444 checks executed,7schema_encode cases failed; boundary probe unrun. All children exited/reaped and owned native absence was observed. Main source and import activation are unchanged. This archive contains generated synthetic test metadata and code only, with a compressed source-hash catalogue; no owner model, geometry, rest, pose, image, audio or scene payload. Preserve this failed run when testing a successor. Root diagnosis is ongoing; no corrected result is inferred.\n',encoding='utf-8')
index=[]
for p in sorted(DEST.rglob('*')):
    if p.is_file():index.append({'path':p.relative_to(DEST).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
save('INDEX.json',{'format':'has_synthetic_domain_failed_actual_index_1','files':index})
print(json.dumps({'files':len(index),'index_sha256':hashlib.sha256((DEST/'INDEX.json').read_bytes()).hexdigest(),'failure_preserved':True}))
