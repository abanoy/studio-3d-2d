from pathlib import Path
import hashlib,json,time
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output'
old='485179125adccc303c5064bd8812740c10499ffd0415990f08c6517d758fa01c';new='75e9754e0c5b1d7a423340b4d5c62dafe40a167945999d9af2d4720c3e7c2565'
pose=(ROOT/'src/pose_editor.gd').read_bytes();assert hashlib.sha256(pose).hexdigest()==new and b'\r' not in pose
changes=[]
for name in ['tests/wind_review_port_files.json','tests/helper_preview_port_files.json']:
 path=ROOT/name;raw=path.read_bytes();value=json.loads(raw);rows=[r for r in value['files'] if r['path']=='src/pose_editor.gd'];assert len(rows)==1 and rows[0]['sha256']==rows[0]['lf_sha256']==old and raw.count(old.encode())==2
 changed=raw.replace(old.encode(),new.encode());after=json.loads(changed)
 assert len(after['files'])==len(value['files']) and [r['path'] for r in after['files']]==[r['path'] for r in value['files']]
 for row in after['files']:
  data=(ROOT/row['path']).read_bytes();assert hashlib.sha256(data).hexdigest()==row['sha256'] and hashlib.sha256(data.replace(b'\r\n',b'\n')).hexdigest()==row['lf_sha256']
 path.write_bytes(changed);changes.append({'path':name,'before_sha256':hashlib.sha256(raw).hexdigest(),'after_sha256':hashlib.sha256(changed).hexdigest(),'changed_fields':2,'membership_and_other_rows_preserved':True})
(OUT/'IMPORT_INFO_POSE_PIN_REFRESH_20261121.json').write_text(json.dumps({'format':'has_import_info_pose_pin_refresh_1','status':'PASS','scope':'Only the raw/LF SHA fields for the qualified four-line pose-editor Import info setup change. All memberships/other hashes and verifier assertions exact.','paths':changes,'full_regression_required':True,'recorded_ns':time.time_ns()},indent=2)+'\n')
print(json.dumps(changes))
