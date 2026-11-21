"""Preserve old tests; cover default-Off and explicit-On imports and teaching."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
PREP=ROOT/'output/source-import-off-followup-v3-prep-20261121'
REV='435dc02426a7cdd313e43fe674c9008520845428'
assert not PREP.exists();PREP.mkdir()
files={};patches=[]
def change(name,before,after):
    if name not in files:
        raw=subprocess.check_output(['git','-c','core.autocrlf=false','show',REV+':'+name],cwd=ROOT)
        assert (ROOT/name).read_bytes()==raw,'Base differs: '+name
        files[name]={'base':raw,'target':raw}
    variants={before.encode(),before.replace('\n','\r\n').encode()}
    matches=[value for value in variants if files[name]['target'].count(value)==1]
    assert len(matches)==1,'Missing/nonunique exact newline variant: '+name
    before=matches[0];ending='\r\n' if b'\r\n' in before else '\n'
    after=after.replace('\n',ending).encode()
    assert files[name]['target'].count(before)==1,'Missing or nonunique anchor '+name
    files[name]['target']=files[name]['target'].replace(before,after,1)
    patches.append({'path':name,'before':before.decode(),'after':after.decode()})
name='tests/height_import_native_smoke.gd'
change(name,'\tapp.source_import.start(input.source,true,0,context)\n','\tcheck(context.has("physics_on_import") and typeof(context.physics_on_import)==TYPE_BOOL and not context.physics_on_import,"normal native import explicitly requests Physics Off")\n\tapp.source_import.start(input.source,true,0,context)\n')
change(name,'\tcheck(actor!=null and app.physics_editor.active(id) and actor.authored_keys().is_empty(),"default body physics starts only after accepting the fitted import, without recording keys")\n','\tcheck(actor!=null and not app.physics_editor.active(id) and not app.physics_editor.is_running() and app.physics_editor.pending.is_empty() and app.physics_editor.import_starts.is_empty() and not app.physics_editor.toggle.button_pressed and not app.physics_editor.hair_toggle.button_pressed and actor.authored_keys().is_empty(),"accepted default native import keeps body and hair Physics Off without queued starts or recorded keys")\n\tcheck(app.keys==keys,"default-Off acceptance preserves authored camera keys")\n')
change(name,'\t# A stale source file cannot be accepted after review. Only owned fixture bytes change.\n', '''\t# Explicit opt-in stays supported, and must still wait for height acceptance.
\tapp.new_project();var optin_context: Dictionary=app.import_actions.placement();optin_context.physics_on_import=true
\tvar optin_keys: Array=app.keys.duplicate(true)
\tapp.source_import.start(input.source,true,0,optin_context)
\twhile app.source_import.pid>0:await process_frame
\twhile app.height_review.pending and not app.height_review.prepared:await process_frame
\tawait settled();review=app.height_review
\tcheck(review.pending and review.prepared and review.assessment.get("complete",false) and not app.physics_editor.is_running() and app.renderer.active_model()==null,"explicit native Physics opt-in still waits for completed height acceptance")
\tif not review.pending:app.free();quit(1);return
\tfor child in app.get_children():
\t\tif child is AcceptDialog and child.visible:child.hide();child.queue_free()
\tvar optin_data: Dictionary=review.data.duplicate(true);var optin_id: String=optin_data.id
\treview.fit.button_pressed=true;review.apply();await settled()
\tdeadline=Time.get_ticks_msec()+10000
\twhile (not app.physics_editor.pending.is_empty() or not app.physics_editor.import_starts.is_empty()) and Time.get_ticks_msec()<deadline:await process_frame
\tawait settled();var optin_actor: RefCounted=app.renderer.world_runtime.instance(optin_id)
\tcheck(optin_actor!=null and optin_actor.data.scale>1 and optin_actor.data.metadata.import_height.source_sha256==optin_data.sha256,"explicit native fit installs once with source provenance intact")
\tcheck(optin_actor!=null and app.physics_editor.body_active(optin_id) and optin_actor.authored_keys().is_empty() and app.keys==optin_keys,"explicit Physics On starts after acceptance without recording pose or camera keys")
\tif optin_actor:
\t\tvar optin_scale: float=optin_actor.data.scale;app.physics_editor.freeze_all();await settled()
\t\tcheck(not app.physics_editor.is_running() and optin_actor.data.scale==optin_scale and optin_actor.authored_keys().is_empty(),"explicit Physics Off freezes without losing chosen height or adding keys")
\t# A stale source file cannot be accepted after review. Only owned fixture bytes change.
''')
name='src/first_movie_lesson.gd'
change(name,'\t"Add the practice figure. Let Physics run, then switch Physics off to freeze it.",\n','\t"Add the practice figure. Switch Physics on, let it move, then switch Physics off to freeze it.",\n')
change(name,'\t"Choose Practice figure.glb. Compatible imports begin with Physics on. Try grabbing it, then turn Physics off; nothing is recorded without Record.",\n','\t"Choose Practice figure.glb. Imports start with Physics off. Select the figure and switch Physics on. Try grabbing it, then turn Physics off; nothing is recorded without Record.",\n')
name='tests/first_movie_smoke.gd'
change(name,'\tfor i in range(20):await physics_frame\n\tlesson.next_tick=0;lesson._process(0);await settled()\n\tcheck(lesson.step==1 and lesson.observed.get("physics_seen",false) and app.physics_editor.body_active(rig.data.id),"actual default-on ragdoll is observed without advancing or freezing it")\n', '''\tfor i in range(20):await physics_frame
\tlesson.next_tick=0;lesson._process(0);await settled()
\tcheck(lesson.step==1 and not lesson.observed.get("physics_seen",false) and not app.physics_editor.is_running() and app.physics_editor.import_starts.is_empty() and not lesson.satisfied(),"default-Off practice import cannot falsely satisfy the Physics exercise")
\tcheck(lesson.instruction.text==First.DEFINITION.steps[1] and "Switch Physics on" in lesson.instruction.text,"practice explicitly teaches the opt-in Physics step")
\tapp.physics_editor.toggle.button_pressed=true
\tfor i in range(20):await physics_frame
\tlesson.next_tick=0;lesson._process(0);await settled()
\tcheck(lesson.step==1 and lesson.observed.get("physics_seen",false) and app.physics_editor.body_active(rig.data.id),"explicit Physics On is observed without advancing or freezing it")
''')
name='tests/scenario_d_smoke.gd'
change(name,' check(actor.order.size()>=17 and physics.body_active(id) and not app.advanced_mode and physics.toggle.is_visible_in_tree() and recording.button.is_visible_in_tree(),"D1 original humanoid imports with compatible Physics ON and Record visible in Simple")\n',' check(actor.order.size()>=17 and not physics.body_active(id) and not physics.is_running() and physics.import_starts.is_empty() and actor.authored_keys().is_empty(),"D1 normal humanoid import starts Physics Off without queued activation or recorded keys")\n await enable(id)\n check(physics.body_active(id) and not app.advanced_mode and physics.toggle.is_visible_in_tree() and recording.button.is_visible_in_tree(),"D1 explicit visible Physics toggle activates compatible humanoid and keeps Record available in Simple")\n')
name='docs/physics.md'
change(name,'Interactive imports of compatible ragdolls start with **Physics on** after the import\ndialogs close. The immediate on/off control is visible in Simple. Existing models\nand solid props can also use that toggle explicitly. Left-click a simulated body to grab it, move the\n','Interactive model imports start with **Physics off** and **Hair & clothes off**.\nSelect a compatible ragdoll or solid prop and turn Physics on explicitly using\nthe control visible in Simple. Height review preserves that Off default; an\nexplicit import opt-in waits until the review is accepted. Left-click a simulated\nbody to grab it, move the\n')
name='docs/scenario_d.md'
change(name,'# Physics scenario D: integrated software verification\n','# Physics scenario D: integrated software verification\n\nCurrent behavior (2026-11-21): models import with Physics Off. The scenario now\nchecks that default and explicitly turns Physics On before the grab/record\nexercise. The recorded baseline measurements below used the earlier On default;\nthey remain historical observations. No contact, recording or replay assertion\nis removed by the default change.\n')
for name,row in files.items():
    for tree,key in [('bases','base'),('payload','target')]:
        path=PREP/tree/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(row[key])
(PREP/'PATCHES.json').write_text(json.dumps({'baseline_revision':REV,'application_adopted':False,'patches':patches},indent=2)+'\n',encoding='utf-8')
(PREP/'README.md').write_text('''# Import Physics Off follow-up

Source candidate, unrun. Canonical435 Full failed after1961.792seconds at the old native-height expectation of automatic Physics On; source1102/HEAD stayed exact and all113 current private jobs closed. Earlier626 newly added editor/camera controls passed. No fresh aggregate report exists. Preserve that failure.

Owner-requested Off defaults are implemented. The native-height test now checks Off/no queued startup/no pose or camera keys, plus a separate real raw-VRM explicit-On request that waits for height acceptance and still stops without losing fitted scale. Old source is retained under bases. Expected native assertion count becomes15, up from9.

The same audit found two later routes that would still assume automatic startup. The beginner lesson now explicitly teaches On then Off, retaining its observed-Physics requirement and stable course/step identities. Its real-app test asserts an Off import does not falsely grade, then turns On explicitly. ScenarioD adds a default-Off/no-recording check, uses its existing visible-toggle helper, and keeps every grab/contact/Local/World/media/cold assertion. No production import policy or simulator code changes.

Run complete character-height, interactive import-physics, first-movie/resume and scenarioD writer/cold/movie wrappers on private Windows desktops, with exact source/HEAD/fixture preservation and all job closure. Then publish and retrieve a fresh committed source for Full182 again. Do not use this failed435 run to admit private Miku/face native qualification. Their frozen435 hosts need an explicit successor source/revision port after the new successful Full. Formal scores remain52/54 and55/62; no human/device evidence is inferred.
''',encoding='utf-8')
rows=[]
for path in sorted(PREP.rglob('*')):
    if path.is_file():
        raw=path.read_bytes();rows.append({'path':path.relative_to(PREP).as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
(PREP/'SOURCE_PINS.json').write_text(json.dumps({'format':'has_import_off_followup_source_1','baseline_revision':REV,'qualification':'UNRUN','files':rows,'file_count':len(rows)},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'SOURCE_PREPARED_NOT_APPLIED','files':list(files),'source_pins_sha256':hashlib.sha256((PREP/'SOURCE_PINS.json').read_bytes()).hexdigest()}))
