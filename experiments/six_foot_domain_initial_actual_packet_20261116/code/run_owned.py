"""Root-owned isolated, windowless engine checks of the six-foot prototype."""
from pathlib import Path
import hashlib,importlib.util,json,shutil,sys,time
ROOT=Path(__file__).resolve().parents[2]
PACKET=ROOT/'experiments/six_foot_import_basis_gd_candidate_20261116'
ENGINE=Path(r'C:\a\tools\Godot\Godot_v4.6-stable_win64.exe')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def module(p,name):
    spec=importlib.util.spec_from_file_location(name,p);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
observer=module(ROOT/'experiments/normal_boundary_probe_actual_20261116/run_owned.py','six_foot_process_observer')
assert sha(ENGINE)=='63913d01be2c2d1f929b4a626f5347117126b34e9c64cbf350ea9f35a9657ebf'
assert sha(PACKET/'INDEX.json')=='921579101eb9e97feeb62e8f7b0f22a392fe6536fa8fa9006ecb58650ead7125'
for row in load(PACKET/'INDEX.json')['files']:
    p=PACKET/row['path'];assert p.resolve().is_relative_to(PACKET.resolve()) and sha(p)==row['sha256'] and p.stat().st_size==row['bytes']
folder=ROOT/'output/six-foot-domain-20261116-attempt1';folder.mkdir()
observer.closure(folder,'before')
freeze=module(ROOT/'tools/build_owner_review_snapshot.py','six_foot_frozen_runtime')
studio=folder/'Studio';revision,sources=freeze.freeze_source(ROOT,studio,'52f63c944ded7a651da871524d23a345b606424d',runtime_scope=True)
target=studio/'experiments'/PACKET.name;target.mkdir(parents=True)
for p in PACKET.rglob('*'):
    if p.is_file():
        assert not p.is_symlink();to=target/p.relative_to(PACKET);to.parent.mkdir(parents=True,exist_ok=True);to.write_bytes(p.read_bytes());sources[to.relative_to(studio).as_posix()]=sha(to)
(studio/'override.cfg').write_text('[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name="HAS Six Foot Domain '+str(time.time_ns())+'"\n',encoding='utf-8')
observer.save(folder/'SOURCE.json',{'source_revision':revision,'source_sha256':sources,'prototype_packet_sha256':sha(PACKET/'INDEX.json'),'main_source_modified':False})
results=[];passed=True
for label,script,count in [('domain','basis_domain_unit.gd',444),('boundary','basis_boundary_unit.gd',21)]:
    out=studio/'output'/label;out.mkdir(parents=True)
    relative='experiments/'+PACKET.name+'/'+script
    job={'format':'has_six_foot_'+label+'_job_1','phase':'ROOT_APPROVED_SIX_FOOT_'+label.upper(),'root_closed_all':True,'expires_unix':time.time()+600,'script_sha256':sha(studio/relative),'folder':out.as_posix()}
    if label=='domain':job.update(corpus=(target/'PARITY_CORPUS_v3.json').as_posix(),corpus_sha256=sha(target/'PARITY_CORPUS_v3.json'))
    observer.save(out/'job.json',job)
    for phase,extra in [('parse',['--check-only']),('run',[])]:
        name=label+'-'+phase
        command=[str(ENGINE),'--headless','--audio-driver','Dummy','--path',str(studio),'--log-file',str(folder/(name+'-engine.log')),'--script','res://'+relative,*extra,'--',str(out/'job.json')]
        process,stdout=observer.invoke(folder,name,command,35 if phase=='parse' else 180)
        stderr=(folder/(name+'-stderr.log')).read_text(encoding='utf-8',errors='replace')
        logs=stdout+stderr+(folder/(name+'-engine.log')).read_text(encoding='utf-8',errors='replace')
        errors=[s for s in logs.splitlines() if any(t in s for t in ('SCRIPT ERROR','ERROR:','WARNING:','ObjectDB instances leaked','resources still in use','FAIL basis_'))]
        good=process['exit']==0 and not process['timed_out'] and not errors
        results.append({'label':name,'process':process,'passed':good,'error_markers':errors})
        if not good:passed=False;break
    if not passed:break
    result=load(out/'result.json')
    good=result['checks']==count and result['failures']==0 and result['complete_assertion_set'] is True and all(result['named_checks'].values())
    results[-1].update(assertion_set_passed=good,checks=result['checks'],result_sha256=sha(out/'result.json'))
    if not good:passed=False;break
preserved=all(sha(studio/n)==v for n,v in sources.items())
after=observer.closure(folder,'after')
record={'format':'has_root_six_foot_domain_execution_1','passed':passed and len(results)==4 and preserved,'results':results,'frozen_sources_preserved':preserved,'runtime_lease_released':after['owned_count']==0,'headless_no_graphical_window_requested':True,'actual_import_activation':False,'main_source_modified':False}
observer.save(folder/'verification.json',record);print(json.dumps(record));raise SystemExit(0 if record['passed'] else 1)
