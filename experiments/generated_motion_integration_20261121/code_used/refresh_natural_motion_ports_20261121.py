from pathlib import Path
import ast,hashlib,json,shutil,time
r=Path.cwd();out=r/'output'/('natural-motion-port-bindings-'+str(time.time_ns()));out.mkdir(parents=True)
drivers=['tests/verify_wind_review.py','tests/verify_helper_preview.py'];manifests=['tests/wind_review_port_files.json','tests/helper_preview_port_files.json'];new=['src/generated_secondary_motion.gd','src/generated_secondary_editor.gd'];changed={'src/physics_editor.gd','src/secondary_spring.gd','src/secondary_skin_contact.gd','src/wind_review.gd','src/pending_helper_wind_player.gd'}
def sha(b):return hashlib.sha256(b).hexdigest()
base={n:(r/n).read_bytes() for n in drivers+manifests};src={p.relative_to(r).as_posix():sha(p.read_bytes()) for p in (r/'src').rglob('*') if p.is_file()}
for name,b in base.items():(out/Path(name).name).write_bytes(b)
for driver in drivers:
 b=base[driver];anchor=b"'secondary_skin_contact',";replacement=b"'secondary_skin_contact', 'generated_secondary_motion', 'generated_secondary_editor',";assert b.count(anchor)==1
 raw=b.replace(anchor,replacement);assert raw.replace(replacement,anchor)==b;(r/driver).write_bytes(raw)
changes=[]
for name,driver in zip(manifests,drivers):
 doc=json.loads(base[name]);old=json.loads(base[name]);assert not any(x['path'] in new for x in doc['files'])
 for row in doc['files']:
  raw=(r/row['path']).read_bytes();actual=sha(raw)
  if row['path'] in changed|{driver}:
   changes.append({'manifest':name,'path':row['path'],'before':row['sha256'],'after':actual});row.update(sha256=actual,lf_sha256=sha(raw.replace(b'\r\n',b'\n')))
  else:assert actual==row['sha256'],row['path']
 for path in new:
  raw=(r/path).read_bytes();doc['files'].append({'path':path,'category':'runtime','sha256':sha(raw),'lf_sha256':sha(raw.replace(b'\r\n',b'\n'))})
 doc['generated_secondary_integration_revision']={'source_commit':'a43beca451bd332f967a427bed4f78a5aa102dd6','integration_commit':'e79f7989380390362ee8ec59d51e43bfe0312c69','added_runtime_rows':new,'changed_existing_rows':[x['path'] for x in doc['files'] if x['path'] in changed],'scope':'Generated natural motion/editor dependencies via SecondarySpring and PhysicsEditor. Membership and exact raw/LF successor pins only; prior provenance, all other driver bytes, assertion counts, native/refusal and lifecycle checks preserved. This refresh supplies no inherited execution claim.'}
 assert {k:v for k,v in old.items() if k!='files'}=={k:v for k,v in doc.items() if k not in ('files','generated_secondary_integration_revision')}
 for a,b in zip(old['files'],doc['files']):
  if a['path'] not in changed|{driver}:assert a==b
 (r/name).write_bytes((json.dumps(doc,indent=2)+'\n').encode())
tree=ast.parse((r/'output/refresh_voxel_ports_20261121.py').read_text(encoding='utf-8-sig'));function=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='validator');exec(compile(ast.Module(body=[function],type_ignores=[]),'pure-validator-extraction','exec'))
controls=[]
def check(name,fn,refusal=False):
 try:fn()
 except (RuntimeError,OSError,ValueError) as e:
  assert refusal,(name,str(e));controls.append({'label':name,'expected_refusal':str(e),'status':'PASS'});return
 assert not refusal,name;controls.append({'label':name,'status':'PASS'})
for driver,manifest,count in zip(drivers,manifests,[57,73]):
 v=validator(driver,r);assert len(v())==count;controls.append({'label':driver+' exact binding','count':count,'status':'PASS'})
 scratch=out/('wind' if 'wind' in driver else 'helper');scratch.mkdir();doc=json.loads((r/manifest).read_bytes())
 for name in [manifest]+[x['path'] for x in doc['files']]:
  dst=scratch/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/name,dst)
 v=validator(driver,scratch);leaves=[x['path'] for x in doc['files'] if x['path'] in changed|set(new)]
 for leaf in leaves:
  f=scratch/leaf;raw=f.read_bytes()
  try:f.unlink();check(driver+' missing '+leaf,v,True)
  finally:f.write_bytes(raw)
  try:f.write_bytes(raw+b'\n# owned scratch drift\n');check(driver+' drift '+leaf,v,True)
  finally:f.write_bytes(raw)
  m=scratch/manifest;raw=m.read_bytes();d=json.loads(raw);d['files']=[x for x in d['files'] if x['path']!=leaf]
  try:m.write_bytes(json.dumps(d).encode());check(driver+' omitted row '+leaf,v,True)
  finally:m.write_bytes(raw)
 assert len(leaves)==(6 if 'wind' in driver else 7)
assert src=={p.relative_to(r).as_posix():sha(p.read_bytes()) for p in (r/'src').rglob('*') if p.is_file()}
report={'status':'PASS','control_count':len(controls),'controls':controls,'src_unchanged':True,'driver_only_change':'Exactly one membership assignment line per driver; reverse recovers original bytes.','dependency_review':{'editor':'physics_editor.gd directly preloads generated_secondary_editor.gd; editor preloads generated_secondary_motion.gd','motion':'secondary_spring.gd directly preloads generated_secondary_motion.gd; motion uses pre-existing LimbIK dependency already used by Spring','existing_changed_pending_helper':'pending_helper_wind_player.gd is already a declared Helper dependency; absent from existing Wind manifest scope, not newly added.'},'changes':changes,'pins':[{'path':n,'bytes':len((r/n).read_bytes()),'sha256':sha((r/n).read_bytes())} for n in drivers+manifests]}
p=out/'result.json';p.write_bytes((json.dumps(report,indent=2)+'\n').encode());print(json.dumps({'proof':str(p),'bytes':len(p.read_bytes()),'sha256':sha(p.read_bytes()),'control_count':len(controls),'pins':report['pins']},indent=2))
