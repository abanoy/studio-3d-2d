from pathlib import Path
import hashlib,json,subprocess,time,shutil
r=Path.cwd();packet=r/'experiments/local_wind_review/production_port_candidate_20261112';proposal=r/'experiments/local_wind_review/main_driver_proposal_20261113/proposed/tests';manifest=json.loads((packet/'manifest.json').read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();lf=lambda b:b.replace(b'\r\n',b'\n')
head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();assert head=='2a54f252d128e4c800ae608ae798e0041a996b6b'
record=r/'output'/('wind-main-port-'+str(time.time_ns()));record.mkdir();before={};prepared=[]
selection=sha(r/'src/world_selection.gd');assert selection=='7c36ec46c6ba7a9e52eada2d08f5356c23e6312c47a05330cdb37ecbde3161c3'
rows=manifest['overlay_files'];assert len(rows)==16
for row in rows:
 n=row['path'];p=packet/row['candidate_path'];assert sha(p)==row['sha256'] and p.stat().st_size==row['bytes'];d=r/n
 if d.exists():
  assert n.startswith('src/') and lf(d.read_bytes())==lf(subprocess.check_output(['git','show','85fa482b3ef1ed752e8a97191b5ea7b235cea7aa:'+n])),n
  before[n]={'sha256':sha(d),'bytes':d.stat().st_size,'mtime_ns':d.stat().st_mtime_ns};backup=record/'before'/n;backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(d,backup)
 else:assert n not in ['src/app.gd','src/renderer.gd']
 prepared.append((n,p.read_bytes()))
for n in ['tests/verify_wind_review.py','tests/wind_review_port_files.json']:assert not (r/n).exists(),n
plans=r/'tests/native_fixture_plans.py';old_plans=plans.read_text(encoding='utf-8');assert 'WIND_REVIEW_PINS' not in old_plans
(record/'native_fixture_plans.before.py').write_bytes(plans.read_bytes())
for n,data in prepared:(r/n).write_bytes(data)
(r/'tests/wind_review_gpu_common.gd').write_bytes((proposal/'wind_review_gpu_common.gd').read_bytes())
for n in ['verify_wind_review.py','wind_review_port_files.json']:(r/'tests'/n).write_bytes((proposal/n).read_bytes())
plans.write_text(old_plans+'\n'+(proposal/'native_fixture_plans.wind_review.append.py').read_text(encoding='utf-8'),encoding='utf-8',newline='\n')
assert sha(r/'src/world_selection.gd')==selection
pins=json.loads((r/'tests/wind_review_port_files.json').read_bytes())
for row in pins['files']:assert sha(r/row['path'])==row['sha256'],row['path']
proof={'format':'has_wind_actual_main_port_source_1','base_commit':head,'port_folder':str(record),'overlay_files':16,'new_driver_files':2,'native_resolver_appended':True,'canonical_registration_pending':True,'preserved_selection_sha256':selection,'previous_runtime':before,'ported_files':{row['path']:sha(r/row['path']) for row in pins['files']},'main_graphics_or_validation_run':False,'private_art_payloads_copied_into_source':False}
(record/'source-port.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps({'record':str(record),'files':16,'selection_preserved':True,'runtime_validation':'not yet run'}))
