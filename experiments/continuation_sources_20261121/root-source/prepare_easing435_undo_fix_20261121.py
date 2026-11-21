"""Keep original port/failure; propose narrowly tagged camera refresh on Undo."""
from pathlib import Path
import hashlib,json

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'output/source-keyframe-easing435-port-prep-20261121'
NEW=ROOT/'output/source-keyframe-easing435-undo-fix-prep-20261121'
assert not NEW.exists()
manifest=json.loads((OLD/'SOURCE_PINS.json').read_bytes())
NEW.mkdir()
for row in manifest['files']:
    raw=(OLD/row['path']).read_bytes()
    assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
    target=NEW/row['path'];target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
(NEW/'bases/original_port_SOURCE_PINS.json').write_bytes((OLD/'SOURCE_PINS.json').read_bytes())
app=NEW/'payload/src/app.gd';raw=app.read_bytes()
before=b'\tset_frame(frame)\r\n\tif command.type=="video":renderer.restore_view(view)\r\n'
after=b'\tset_frame(frame)\r\n\tif command.type=="keys" and command.get("camera_timing_bake",false):renderer.evaluate(keys,frame,false)\r\n\tif command.type=="video":renderer.restore_view(view)\r\n'
assert raw.count(before)==1
app.write_bytes(raw.replace(before,after,1))
editor=NEW/'payload/src/camera_easing_editor.gd';raw=editor.read_bytes()
old=b'app.push_history({"type":"keys","before":before,'
new=b'app.push_history({"type":"keys","camera_timing_bake":true,"before":before,'
assert raw.count(old)==1
editor.write_bytes(raw.replace(old,new,1))
patch_path=NEW/'PATCHES.json';patch=json.loads(patch_path.read_bytes())
patch['patches'].append({'path':'src/app.gd','base_sha256':patch['patches'][0]['base_sha256'],
 'before':before.decode(),'after':after.decode()})
patch['editor_payload_change']={'path':'src/camera_easing_editor.gd','before':old.decode(),'after':new.decode()}
patch_path.write_text(json.dumps(patch,indent=2)+'\n',encoding='utf-8')
failure=ROOT.parent/'has-easing435-app-cpu-1795254695259497400'
(NEW/'evidence').mkdir()
for name in ['PUBLIC_RESULT.json','classic-simple/result.json','classic-simple/stdout.log','classic-simple/stderr.log','classic-simple/engine.log']:
    target=NEW/'evidence'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((failure/name).read_bytes())
(NEW/'evidence/reproduction_fixture.gd').write_bytes((ROOT/'output/easing435_app_headless_v2.gd').read_bytes())
(NEW/'UNDO_CORRECTION.md').write_text('''# Reproduced actual camera Undo defect

The original435 port remains unchanged. Its88 headless controls prove key-array Undo/Redo, not camera-view restoration. A stronger24-control fixture reproduced one failure in Classic Simple: all24 controls executed,23 passed, and Undo restored original keys while the renderer retained the baked preview position. Root process exited1, was reaped, and every admitted source/runtime input and the parent environment stayed unchanged. Exact result/logs/fixture are retained here. Other variants were correctly unrun after the first failed case.

This successor tags only its own Bake history command with camera_timing_bake. The ordinary app history path refreshes the authored camera only for this explicit keys command after restoring before/after keys. Existing free-camera behavior for all untagged camera edits is unchanged. The tag is session history, not saved animation metadata. The editor spy controls still require complete deep before/after dictionaries; additional real-app controls now require both Undo and Redo camera positions at the current frame.

This correction is not adopted into Main. Headless requalification and independent source review are pending for these exact successor bytes; visible camera/lens behavior, actual capture/movie, packed save/cold reopen, GUI input and performance remain separate unrun gates.
''',encoding='utf-8')
rows=[]
for p in sorted(NEW.rglob('*')):
    if p.is_file():
        raw=p.read_bytes();rows.append({'path':p.relative_to(NEW).as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
(NEW/'SOURCE_PINS.json').write_text(json.dumps({'format':'has_easing435_undo_fix_preparation_1','application_adopted':False,
 'runtime_qualification':'UNRUN_FOR_THIS_SUCCESSOR','files':rows,'file_count':len(rows),'total_bytes':sum(r['bytes'] for r in rows)},indent=2)+'\n',encoding='utf-8')
host=(ROOT/'output/run_easing435_app_headless_v2_20261121.py').read_bytes().replace(
 b'source-keyframe-easing435-port-prep-20261121',b'source-keyframe-easing435-undo-fix-prep-20261121')
target=ROOT/'output/run_easing435_app_headless_v3_20261121.py';assert not target.exists();target.write_bytes(host)
print(json.dumps({'status':'FROZEN_SUCCESSOR_UNRUN','folder':str(NEW),'files':len(rows),
 'source_pins_sha256':hashlib.sha256((NEW/'SOURCE_PINS.json').read_bytes()).hexdigest()}))
