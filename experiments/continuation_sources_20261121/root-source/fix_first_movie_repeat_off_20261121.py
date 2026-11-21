from pathlib import Path
import hashlib,json,time
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'tests/first_movie_smoke.gd';before=path.read_bytes()
baseline=ROOT/'output/source-import-off-followup-v3-prep-20261121/payload/tests/first_movie_smoke.gd'
assert before==baseline.read_bytes()
old='''\tawait import_practice("Practice figure.glb");rig=First.object(lesson,"model");for i in range(20):await physics_frame
\tlesson.next_tick=0;lesson._process(0);app.physics_editor.toggle.button_pressed=false;await settled();if not await advance(2):return
'''.encode()
new='''\tawait import_practice("Practice figure.glb");rig=First.object(lesson,"model")
\tcheck(not app.physics_editor.is_running() and not lesson.observed.get("physics_seen",false),"Previous and re-import preserve the Off default without reusing later Physics evidence")
\tapp.physics_editor.toggle.button_pressed=true
\tfor i in range(20):await physics_frame
\tlesson.next_tick=0;lesson._process(0)
\tcheck(lesson.observed.get("physics_seen",false) and app.physics_editor.body_active(rig.data.id),"repeated practice observes a new explicit Physics On session")
\tapp.physics_editor.toggle.button_pressed=false;await settled();if not await advance(2):return
'''.encode()
if old not in before:
    old=old.replace(b'\n',b'\r\n');new=new.replace(b'\n',b'\r\n')
assert before.count(old)==1
after=before.replace(old,new,1)
prep=ROOT/'output/source-import-off-first-movie-repeat-prep-20261121';prep.mkdir(exist_ok=False)
(prep/'before.gd').write_bytes(before);(prep/'after.gd').write_bytes(after)
failure=ROOT/'output/import-off-followup-scoped-1795256301357827900'
for name in ('completion.json','first-movie/stdout.log','first-movie/stderr.log'):
    target=prep/'failure'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((failure/name).read_bytes())
assert path.read_bytes()==before;path.write_bytes(after);assert path.read_bytes()==after
result={'format':'has_first_movie_repeat_off_test_correction_1','status':'APPLIED_REMAINDER_UNRUN',
 'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':hashlib.sha256(after).hexdigest(),
 'retained_failure':'First Physics On/Off exercise passed; repeated import after Previous still assumed automatic On and failed advancement.',
 'new_checks':2,'production_source_changed':False,'previous_height_native15_and_import_physics54_passes_retained':True,
 'source_head':'435dc02426a7cdd313e43fe674c9008520845428'}
(prep/'CORRECTION.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
rows=[]
for p in sorted(prep.rglob('*')):
    if p.is_file():
        raw=p.read_bytes();rows.append({'path':p.relative_to(prep).as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
(prep/'SOURCE_PINS.json').write_text(json.dumps({'format':'has_first_movie_repeat_correction_pins_1','files':rows},indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
