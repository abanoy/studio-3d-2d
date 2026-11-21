from pathlib import Path
import ast,hashlib,json,time,shutil
r=Path.cwd();out=r/'output'/('voxel-port-refresh-'+str(time.time_ns()));out.mkdir(parents=True)
paths=['tests/verify_wind_review.py','tests/verify_helper_preview.py','tests/wind_review_port_files.json','tests/helper_preview_port_files.json']
before={n:(r/n).read_bytes() for n in paths};(out/'before').mkdir()
for n,b in before.items():(out/'before'/Path(n).name).write_bytes(b)
leaves=['src/renderer.gd','src/scene_indirect_runtime.gd','src/scene_lighting_document.gd','src/scene_lighting_editor.gd'];new='src/scene_voxel_runtime.gd'
source_before={p.relative_to(r).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'src').rglob('*') if p.is_file()}
changes=[]
for driver in paths[:2]:
 b=before[driver];old=b"'scene_indirect_runtime',";assert b.count(old)==1
 updated=b.replace(old,b"'scene_indirect_runtime', 'scene_voxel_runtime',")
 assert updated.replace(b"'scene_indirect_runtime', 'scene_voxel_runtime',",old)==b
 (r/driver).write_bytes(updated)
for manifest,driver in zip(paths[2:],paths[:2]):
 d=json.loads(before[manifest]);oldrows={x['path']:x.copy() for x in d['files']}
 assert new not in oldrows
 for row in d['files']:
  raw=(r/row['path']).read_bytes();sha=hashlib.sha256(raw).hexdigest()
  if row['path'] in leaves+[driver]:
   changes.append({'manifest':manifest,'path':row['path'],'before':row['sha256'],'after':sha});row.update(sha256=sha,lf_sha256=hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest())
  else:assert sha==row['sha256'],row['path']
 raw=(r/new).read_bytes();d['files'].append({'path':new,'category':'runtime','sha256':hashlib.sha256(raw).hexdigest(),'lf_sha256':hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest()})
 d['voxel_runtime_integration_revision']={'source_commit':'96e5d50b63964c1782515a0c70d22a5f0ed59e9e','integration_commit':'38b39ec7a057ad6c8a0ec8aaf557574cb5ce5706','added_runtime_row':new,'changed_runtime_rows':leaves,'scope':'Exact reviewed VoxelGI dependency and raw/LF leaf pins only. Existing membership, source-byte, lifecycle, native/refusal guards and assertion counts remain unchanged. This refresh supplies no inherited execution claim.'}
 assert {k:v for k,v in d.items() if k not in ('files','voxel_runtime_integration_revision')}=={k:v for k,v in json.loads(before[manifest]).items() if k!='files'}
 (r/manifest).write_bytes((json.dumps(d,indent=2)+'\n').encode())

def validator(driver,root):
 tree=ast.parse((r/driver).read_bytes());wind='wind' in driver
 names=({'UNITS','SCRIPTS','ALLOW_EOL','PORT_RUNTIME_FILES','PORT_TEST_FILES'} if wind else {'RUNTIME_FILES','TEST_FILES'})
 funcs=({'require','runtime_hashes'} if wind else {'require','relative','owned','validate_port'})
 nodes=[n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in names for t in n.targets) or isinstance(n,ast.FunctionDef) and n.name in funcs]
 ns={'Path':Path,'PureWindowsPath':__import__('pathlib').PureWindowsPath,'hashlib':hashlib,'json':json,'stat':__import__('stat'),'ROOT':root}
 exec(compile(ast.Module(body=nodes,type_ignores=[]),driver,'exec'),ns)
 return (lambda allow=False: (ns.update(ALLOW_EOL=allow),ns['runtime_hashes']())[1]) if wind else lambda allow=False:ns['validate_port'](root,allow)
results=[]
def check(label,call,refuse=False):
 try:call()
 except (RuntimeError,OSError,ValueError) as e:
  assert refuse,(label,str(e));results.append({'label':label,'expected_refusal':True,'error':str(e)});return
 assert not refuse,label;results.append({'label':label,'passed':True})
for driver,manifest,expected in zip(paths[:2],paths[2:],[55,71]):
 validate=validator(driver,r);check(driver+' actual exact bindings',lambda:len(validate())==expected or (_ for _ in ()).throw(AssertionError('count')))
 scratch=out/('wind' if 'wind' in driver else 'helper');scratch.mkdir();d=json.loads((r/manifest).read_bytes())
 for name in [manifest]+[x['path'] for x in d['files']]:
  target=scratch/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/name,target)
 v=validator(driver,scratch)
 for leaf in leaves+[new]:
  f=scratch/leaf;raw=f.read_bytes()
  try:
   f.unlink();check(driver+' missing '+leaf,v,True)
  finally:f.write_bytes(raw)
  try:
   f.write_bytes(raw+b'\n# scratch drift\n');check(driver+' drift '+leaf,v,True)
  finally:f.write_bytes(raw)
  m=scratch/manifest;original=m.read_bytes();doc=json.loads(original);doc['files']=[x for x in doc['files'] if x['path']!=leaf]
  try:
   m.write_bytes(json.dumps(doc).encode());check(driver+' omitted row '+leaf,v,True)
  finally:m.write_bytes(original)
 m=scratch/manifest;raw=m.read_bytes();doc=json.loads(raw);doc['files'].append(doc['files'][-1].copy())
 try:m.write_bytes(json.dumps(doc).encode());check(driver+' duplicate',v,True)
 finally:m.write_bytes(raw)
 f=scratch/new;raw=f.read_bytes()
 try:
  f.write_bytes(raw.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n'));check(driver+' default EOL refused',v,True);check(driver+' explicit EOL accepted',lambda:v(True))
 finally:f.write_bytes(raw)
source_after={p.relative_to(r).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'src').rglob('*') if p.is_file()};assert source_before==source_after
report={'status':'PASS','source_commit':'96e5d50b63964c1782515a0c70d22a5f0ed59e9e','controls':len(results),'results':results,'changes':changes,'src_unchanged':True,'driver_change':'One runtime-membership assignment line per driver only; exact reverse checked.','pins':[{'path':n,'bytes':len((r/n).read_bytes()),'sha256':hashlib.sha256((r/n).read_bytes()).hexdigest()} for n in paths]}
(out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'folder':str(out),'controls':len(results),'status':'PASS','pins':report['pins']},indent=2))
