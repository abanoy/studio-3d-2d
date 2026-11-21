from pathlib import Path
import hashlib,json,ast,time,shutil
r=Path.cwd();out=r/'output'/('voxel-fixed-leaf-bindings-'+str(time.time_ns()));out.mkdir(parents=True)
source={p.relative_to(r).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'src').rglob('*') if p.is_file()};drivers=['tests/verify_wind_review.py','tests/verify_helper_preview.py'];driver_before={n:(r/n).read_bytes() for n in drivers};leaf='src/scene_voxel_runtime.gd';b=(r/leaf).read_bytes();assert len(b)==3188 and hashlib.sha256(b).hexdigest()=='a99f28128f963a84133e1e862f67b1d48b012bde6fb9865c17cb90598dcb1816'
changes=[];manifests=['tests/wind_review_port_files.json','tests/helper_preview_port_files.json']
for name in manifests:
 p=r/name;raw=p.read_bytes();(out/p.name).write_bytes(raw);doc=json.loads(raw);before=json.loads(raw)
 rows=[x for x in doc['files'] if x['path']==leaf];assert len(rows)==1;row=rows[0];old=row.copy();row.update(sha256=hashlib.sha256(b).hexdigest(),lf_sha256=hashlib.sha256(b.replace(b'\r\n',b'\n')).hexdigest())
 doc['voxel_runtime_integration_revision']['post_review_fix']='After integration38b39ec7, reviewed stale-bake-data visibility/error recovery fix; only scene_voxel_runtime.gd runtime leaf repinned. Prior38-control proof remains historical before this correction; new pure binding/missing/drift proof recorded separately. No inherited graphics PASS.'
 assert all(x==y for x,y in zip(before['files'],doc['files']) if x['path']!=leaf)
 p.write_bytes((json.dumps(doc,indent=2)+'\n').encode());changes.append({'manifest':name,'leaf':leaf,'old':old,'new':row.copy()})
text=(r/'output/refresh_voxel_ports_20261121.py').read_text(encoding='utf-8-sig');tree=ast.parse(text);node=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='validator');exec(compile(ast.Module(body=[node],type_ignores=[]),'validator','exec'))
controls=[]
for driver,manifest,count in zip(drivers,manifests,[55,71]):
 v=validator(driver,r);assert len(v())==count;controls.append({'driver':driver,'control':'exact_bindings','count':count,'status':'PASS'})
 scratch=out/('wind' if 'wind' in driver else 'helper');scratch.mkdir();doc=json.loads((r/manifest).read_bytes())
 for name in [manifest]+[x['path'] for x in doc['files']]:
  dst=scratch/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/name,dst)
 v=validator(driver,scratch);f=scratch/leaf
 for label,mutation in [('missing',None),('drift',b+b'\n# scratch byte drift\n')]:
  if mutation is None:f.unlink()
  else:f.write_bytes(mutation)
  try:
   v();raise AssertionError('Expected refusal '+label)
  except (RuntimeError,OSError) as e:controls.append({'driver':driver,'control':label,'status':'PASS','expected_refusal':str(e)})
  finally:f.write_bytes(b)
assert driver_before=={n:(r/n).read_bytes() for n in drivers}
assert source=={p.relative_to(r).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'src').rglob('*') if p.is_file()}
report={'status':'PASS','controls':controls,'control_count':len(controls),'src_unchanged':True,'drivers_unchanged':True,'changes':changes,'pins':[{'path':n,'bytes':len((r/n).read_bytes()),'sha256':hashlib.sha256((r/n).read_bytes()).hexdigest()} for n in manifests]};p=out/'result.json';p.write_bytes((json.dumps(report,indent=2)+'\n').encode());print(json.dumps({'proof':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'controls':len(controls),'pins':report['pins']},indent=2))
