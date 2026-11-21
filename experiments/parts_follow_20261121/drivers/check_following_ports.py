"""Actual driver guards reject omitted or modified newly reviewed dependencies."""
from pathlib import Path
import importlib.util,json,shutil,sys,time
sys.dont_write_bytecode=True
ROOT=Path.cwd().resolve()
sys.path.insert(0,str(ROOT/'tests'))
folder=ROOT/'output'/('following-port-check-'+str(time.time_ns()))
folder.mkdir()
rows=[]
for label,filename,manifest,expected in [('wind','verify_wind_review.py','wind_review_port_files.json',33),('helper','verify_helper_preview.py','helper_preview_port_files.json',48)]:
    spec=importlib.util.spec_from_file_location('check_'+label,ROOT/'tests'/filename)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    scratch=folder/label;scratch.mkdir()
    doc=json.loads((ROOT/'tests'/manifest).read_bytes())
    for row in doc['files']:
        target=scratch/row['path'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/row['path'],target)
    target_manifest=scratch/'tests'/manifest
    def write_doc():target_manifest.write_bytes((json.dumps(doc,indent=2)+'\n').encode())
    write_doc()
    module.ROOT=scratch
    def check():return module.runtime_hashes() if label=='wind' else module.validate_port(scratch)
    assert len(check())==expected
    rows.append({'case':label+' exact combined-source bindings','passed':True,'files':expected})
    for name in ['src/character_part_follow.gd','src/part_pose_follow_math.gd']:
        target=scratch/name;original=target.read_bytes()
        target.write_bytes(original+b'\n# unreviewed drift\n')
        try:check()
        except RuntimeError as error:assert 'Unreviewed' in str(error)
        else:raise AssertionError('Driver accepted modified '+name)
        target.write_bytes(original)
        rows.append({'case':label+' refuses changed bytes '+name,'passed':True})
        entries=doc['files'];doc['files']=[r for r in entries if r['path']!=name];write_doc()
        try:check()
        except RuntimeError as error:assert 'membership' in str(error) or 'omits required' in str(error)
        else:raise AssertionError('Driver accepted omitted '+name)
        doc['files']=entries;write_doc()
        rows.append({'case':label+' refuses omitted '+name,'passed':True})
    assert len(check())==expected
report={'status':'PASS','checks':len(rows),'rows':rows,'mutated_shipping_files':False,'gpu_used':False}
(folder/'result.json').write_bytes((json.dumps(report,indent=2)+'\n').encode())
print(json.dumps({'folder':str(folder),'checks':len(rows),'status':'PASS'}))
