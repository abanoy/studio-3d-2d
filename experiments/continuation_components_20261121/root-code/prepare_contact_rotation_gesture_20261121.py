"""Propose real projected-angle test gestures; retain all129 assertions and thresholds."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1];DEST=ROOT/'output/source-contact-rotation-gesture-v2-prep-20261121'
REV='c31576d0c1d84030d51ec886f2f3976a60a70c7b'
assert not DEST.exists();DEST.mkdir()
def put(name,raw):
 p=DEST/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
def baseline(name):
 raw=subprocess.check_output(['git','show',REV+':'+name],cwd=ROOT);assert raw==(ROOT/name).read_bytes();put('bases/'+name,raw);return raw
name='tests/contact_transform_smoke.gd';raw=baseline(name)
anchor=b'\treturn best\nfunc case_for(plan: Dictionary) -> Dictionary:\n'
helper='''	return best
func rotation_points(editor,start: Vector2) -> Dictionary:
	# Request real world-Y angles, independent of ring size, screen tangent or
	# the obsolete pixels-to-angle sensitivity. Numeric +90 already refuses above.
	var camera: Camera3D=app.renderer.camera
	var origin: Vector3=editor.drag_world.origin
	var direction:=camera.project_ray_normal(start)
	var invalid:={"valid":start,"invalid":start,"error":"No supported world-Y ray/plane gesture"}
	if absf(direction.dot(Vector3.UP))<0.08:return invalid
	var hit=Plane(Vector3.UP,origin).intersects_ray(camera.project_ray_origin(start),direction)
	if hit==null:return invalid
	var radial: Vector3=hit-origin
	if radial.length_squared()<0.00000001:return invalid
	var one:=camera.unproject_position(origin+Quaternion(Vector3.UP,deg_to_rad(1))*radial)
	var ninety:=camera.unproject_position(origin+Quaternion(Vector3.UP,deg_to_rad(90))*radial)
	if not one.is_finite() or not ninety.is_finite():return invalid
	return {"valid":one,"invalid":ninety}
func case_for(plan: Dictionary) -> Dictionary:
'''.encode()
assert raw.count(anchor)==1;raw=raw.replace(anchor,helper,1)
before=b'\tcheck(editor.dragging and absf(editor.drag_axis.normalized().dot(Vector3.UP))>.99,'
after=b'\tvar gesture:=rotation_points(editor,point)\n\tcheck(editor.dragging and absf(editor.drag_axis.normalized().dot(Vector3.UP))>.99 and not gesture.has("error"),'
assert raw.count(before)==1;raw=raw.replace(before,after,1)
old=b'point+Vector2(1,-1)*deg_to_rad(1)/.02';assert raw.count(old)==4;raw=raw.replace(old,b'gesture.valid')
old=b'point+Vector2(1,-1)*deg_to_rad(90)/.02';assert raw.count(old)==1;raw=raw.replace(old,b'gesture.invalid')
before=b'editor.input(press,point);editor.input(motion,gesture.valid);press.pressed=false'
after=b'editor.input(press,point);gesture=rotation_points(editor,point);editor.input(motion,gesture.valid);press.pressed=false'
assert raw.count(before)==1;raw=raw.replace(before,after,1)
before=b'\tcheck(actor("group").data==preview and peak()<.0002,"unreachable rotation drag'
after=(b'\tdiagnostics["unreachable_drag"]={"status":app.status.text,"kept_last_valid":actor("group").data==preview,"peak":peak(),"requested_degrees":90.,"measured_ring_degrees":rad_to_deg(editor.drag_ring_angle)}\n'
 b'\tcheck(actor("group").data==preview and peak()<.0002 and app.status.text.contains(plan.name) and app.status.text.contains("out of reach"),"unreachable rotation drag')
assert raw.count(before)==1;raw=raw.replace(before,after,1)
assert raw.count(b'check(')==(ROOT/name).read_bytes().count(b'check(')
assert raw.count(b'peak()<.0002')==(ROOT/name).read_bytes().count(b'peak()<.0002')
assert b'/.02' not in raw
put('payload/'+name,raw)
name='tests/verify_contact_transform.py';raw=baseline(name)
before=b"assert r['failures']==0 and len(r['native_reports'])==5"
after=b"assert type(r['checks']) is int and r['checks']==129 and r['failures']==0 and len(r['native_reports'])==5 and all(type(row['checks']) is int and row['checks']==25 and row['failures']==0 for row in r['native_reports'])"
assert raw.count(before)==1;put('payload/'+name,raw.replace(before,after,1))
note='''# Contact rotation gesture correction proposal

c315 Full failed four of129 contact-transform assertions; all167 private jobs closed, source1103/HEAD preserved, all626 new UI/camera and height routes passed. The failed Full is not qualified. Preserve source-full-c315-failed-prep-20261121 separately.

The test still generated pointer deltas using a fixed .02 radians-per-pixel assumption. Current rings calculate signed ray/plane angles (or a projected tangent at edge-on views), so that pointer does not request the intended90 degrees. This proposal projects an independently constructed world-Y one-degree and90-degree rotation of the picked plane radial. Its setup refuses the unsupported edge-on profile; existing ring309 regressions separately cover that fallback. Numeric+90 is already proven unreachable immediately before the gesture in each of five native contexts.

All129 assertions, native5×25 counts, original .0002 contact threshold, exact last-valid data, Undo/Redo/Record/physics guards,49frame reach, packed HAS and exact movie comparisons remain. The invalid gesture assertion is stronger: it requires the named native out-of-reach diagnostic. The Python wrapper now requires the exact129 and25-per-native counts. No production file, solver, parser or tolerance changes. This is a SOURCE ONLY proposal; actual private scoped requalification is required before adoption.
'''
put('PREPARATION.md',note.encode());put('code_used/prepare_contact_rotation_gesture_20261121.py',Path(__file__).read_bytes())
put('code_used/initial_preparation.py',(ROOT/'output/prepare_contact_rotation_gesture_initial_20261121.py').read_bytes())
put('evidence/initial_preparation_refusal.json',(ROOT/'output/source-contact-rotation-gesture-prep-20261121/PREPARATION_REFUSAL.json').read_bytes())
rows=[]
for p in sorted(DEST.rglob('*')):
 if p.is_file():
  data=p.read_bytes();rows.append({'path':p.relative_to(DEST).as_posix(),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
put('SOURCE_PINS.json',(json.dumps({'format':'has_contact_rotation_gesture_preparation_1','baseline_revision':REV,'application_changed':False,'runtime_status':'UNRUN','files':rows},indent=2)+'\n').encode())
print(json.dumps({'status':'SOURCE_ONLY_UNRUN','folder':str(DEST),'files':len(rows)+1,'source_pins_sha256':hashlib.sha256((DEST/'SOURCE_PINS.json').read_bytes()).hexdigest()}))
