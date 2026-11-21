"""Versioned c315 source preparation only; no application edits or runtime."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output'
OLD=OUT/'source-keyframe-easing435-undo-fix-prep-20261121'
NEW=OUT/'source-keyframe-easing-c315-graphics-prep-20261121'
REV='c31576d0c1d84030d51ec886f2f3976a60a70c7b'
def sha(raw):return hashlib.sha256(raw).hexdigest()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()==REV
assert not NEW.exists()
old_raw=(OLD/'SOURCE_PINS.json').read_bytes();assert sha(old_raw)=='472cd37a7dd4717880fe341fa1beea942e4d58f756038a4d78b00d16451b128b'
old=json.loads(old_raw)
for row in old['files']:
 data=(OLD/row['path']).read_bytes();assert len(data)==row['bytes'] and sha(data)==row['sha256']
patch=json.loads((OLD/'PATCHES.json').read_bytes())
for name in ('src/app.gd','src/renderer.gd'):
 raw=(ROOT/name).read_bytes();expected=next(r['base_sha256'] for r in patch['patches'] if r['path']==name)
 assert sha(raw)==expected
 actual=subprocess.check_output(['git','show',REV+':'+name],cwd=ROOT);assert actual==raw
 for row in patch['patches']:
  if row['path']==name:
   before=row['before'].encode();assert raw.count(before)==1;raw=raw.replace(before,row['after'].encode(),1)
 assert raw==(OLD/'payload'/name).read_bytes()
NEW.mkdir()
def put(name,data):
 p=NEW/name;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as stream:assert stream.write(data)==len(data)
 assert p.read_bytes()==data
for row in old['files']:
 if row['path'].startswith('payload/'):
  put(row['path'],(OLD/row['path']).read_bytes())
put('bases/435_undo_SOURCE_PINS.json',old_raw)
put('bases/435_PATCHES.json',(OLD/'PATCHES.json').read_bytes())
put('bases/easing435_graphical_smoke.gd',(OUT/'easing435_graphical_smoke.gd').read_bytes())
fixture=(OUT/'easing435_graphical_smoke.gd').read_bytes()
assert sha(fixture)=='9d102e42bfe1273f36690f1cb701f6045aa2587bdccdf00c514d0aa088dd0f8d'
before=b'\tawait settle()\r\n\tvar image: Image=app.renderer.viewport.get_texture().get_image();image.convert(Image.FORMAT_RGBA8)\r\n'
after=(b'\tawait settle()\r\n'
 b'\tvar before_view: Dictionary=app.renderer.view_state()\r\n'
 b'\tif not app.renderer.begin_native_readback():return null\r\n'
 b'\tvar notification=app.renderer.native_frame_notification\r\n'
 b'\tawait notification.ready\r\n'
 b'\tvar image: Image=app.renderer.finish_native_readback()\r\n'
 b'\tcheck(app.renderer.native_readbacks==0 and app.renderer.view_state()==before_view,"live preview readback balances its scope and preserves the camera")\r\n'
 b'\tif image==null:return null\r\n'
 b'\timage.convert(Image.FORMAT_RGBA8)\r\n')
assert fixture.count(before)==1;fixture=fixture.replace(before,after,1)
fixture=fixture.replace(b'EASING435_GRAPHICS',b'EASING_C315_GRAPHICS')
fixture=fixture.replace(b'Authored, unrun integration controls.',b'Authored, unrun c315 integration controls; balanced live native readback.')
put('payload/tests/easing_c315_graphical_smoke.gd',fixture)
catalogue=(OUT/'IMPORT_OFF_FINAL_FUNCTIONAL_CATALOGUE_20261121.json').read_bytes();assert len(json.loads(catalogue))==1103
put('BASE_FUNCTIONAL_SOURCE.json',catalogue)
patch['format']='has_camera_easing_c315_source_port_1';patch['baseline_revision']=REV
patch['preserved_435_payloads_byte_identical']=True
put('PATCHES.json',(json.dumps(patch,indent=2)+'\n').encode())
for label,path in [
 ('easing69-fixed',ROOT.parent/'has-easing-headless-1795254831934151300/PUBLIC_RESULT.json'),
 ('easing96-fixed',ROOT.parent/'has-easing435-app-cpu-1795254761995523000/PUBLIC_RESULT.json'),
 ('435-graphics-parse-only',ROOT.parent/'has-easing435-graphics-parse-1795258322734840400/RESULT.json')]:
 put('evidence/'+label+'.json',path.read_bytes())
note='''# Camera easing source port to c315

Source/API preparation only; not adopted, no new runtime assertion. The two modified production bases (app and renderer) are raw-byte-identical between435dc024 and c31576d. Exact anchors reconstruct the qualified435 Undo-corrected overlay. The old69 pure/spy and96 real-app headless passes are retained as historical435 evidence, not relabeled as c315 execution.

The original graphical fixture was parsed only and read the native texture directly. Scene Setup deliberately suspends that texture. This successor waits for a balanced native readback of the current temporary camera without invoking the final capture sampler or changing the personal view. One additional assertion requires no camera-state change and no retained readback counter. All prior pixel, authored-vs-preview separation, original-key preservation, Undo/Redo, packed save, cold replay, paint and optional actual-MP4 assertions remain.

Future Root graphical execution requires a successful actual c315 Full182 bound to the exact1103 base catalogue and all626 new checks/21 movie groups/isolated closure receipts. No GPU runs while that Full is active. Use the approved private-desktop path, unique profiles and retained/reaped processes. Prepare a versioned runtime host with strict result counts before execution. Planned matrix: Classic/Neon, Simple/Advanced,100% laptop and150% ultrawide; actual movies in one explicit context. Reader proof must be a separate process using packed copies and no writer source/cache. A parse-only result is not UI/pixel/video qualification. Invalid source/revision/count/receipt gates must refuse.
'''
put('PREPARATION.md',note.encode())
put('code_used/prepare_easing_c315_graphics_source_20261121.py',Path(__file__).read_bytes())
rows=[]
for p in sorted(NEW.rglob('*')):
 if p.is_file():
  raw=p.read_bytes();rows.append({'path':p.relative_to(NEW).as_posix(),'bytes':len(raw),'sha256':sha(raw)})
record={'format':'has_easing_c315_graphics_preparation_1','baseline_revision':REV,'functional_base_count':1103,
 'status':'SOURCE_ONLY_UNRUN','application_adopted':False,'graphics_executed':False,'files':rows}
put('SOURCE_PINS.json',(json.dumps(record,indent=2)+'\n').encode())
print(json.dumps({'folder':str(NEW),'files':len(rows)+1,'bytes':sum(r['bytes'] for r in rows),
 'source_pins_sha256':sha((NEW/'SOURCE_PINS.json').read_bytes()),'status':'SOURCE_ONLY_UNRUN'}))
