extends "res://tests/workspace_resize_smoke.gd"
const Airflow=preload("res://src/airflow.gd")
const Definition=preload("res://src/secondary_rig.gd")
const Timeline=preload("res://src/timeline.gd")
var actor_id: String
var fan_id: String
func angular_difference(a: Dictionary,b: Dictionary) -> float:
	var value:=0.0
	for id in a:
		if b.has(id):value=maxf(value,Timeline.quaternion(a[id].rotation_xyzw).angle_to(Timeline.quaternion(b[id].rotation_xyzw)))
	return value
func scalar_difference(a: Dictionary,b: Dictionary) -> float:
	var value:=0.0
	for id in a:
		for i in range(4):value=maxf(value,absf(a[id].rotation_xyzw[i]-b[id].rotation_xyzw[i]))
	return value
func select(id: String) -> void:app.world_selection.select_entity(id,false);app.physics_editor.sync()
func start_hair() -> void:
	select(actor_id);app.physics_editor.hair_toggle.button_pressed=true
	while app.physics_editor.pending.has(actor_id):await process_frame
	await settle()
func reached(actor: RefCounted,fan: RefCounted) -> int:
	var count:=0
	for chain in actor.root.get_meta("has_secondary_rig").chains:
		var point:=Definition.binding_transform(actor,chain.joints[0].binding).origin
		if Airflow.field(fan.root.global_transform,fan.data.metadata.airflow,point).length_squared()>.00000001:count+=1
	return count
func measure(speed: float) -> Dictionary:
	app.physics_editor.clear();select(fan_id);app.physics_editor.fan_editor.speed.value=speed;await start_hair()
	var physics=app.physics_editor;var actor: RefCounted=app.renderer.world_runtime.instance(actor_id);var sim: RefCounted=physics.simulations[actor_id];var fields:=Airflow.collect(app.renderer,0.,physics.simulations)
	var reference: Dictionary={};var previous: Dictionary={};var peak:=0.0;var step_peak:=0.0;var samples:=[]
	for tick in range(1200):
		var error: String=sim.advance(1./120.,0,0.,false,fields,app.renderer.world_runtime)
		if not error.is_empty():push_error(error);return {"error":error}
		if tick==960:reference=sim.latest.duplicate(true);previous=reference
		if tick>960:
			peak=maxf(peak,angular_difference(reference,sim.latest));step_peak=maxf(step_peak,angular_difference(previous,sim.latest));previous=sim.latest.duplicate(true)
			if tick%4==0:samples.append(sim.latest.duplicate(true))
	var reversals:=0
	for id in reference:
		for axis in range(3):
			var prior_sign:=0;var turns:=0
			for i in range(1,samples.size()):
				var delta: float=samples[i][id].rotation_xyzw[axis]-samples[i-1][id].rotation_xyzw[axis]
				if absf(delta)<.00001:continue
				var sign_now:=1 if delta>0 else -1
				if prior_sign!=0 and sign_now!=prior_sign:turns+=1
				prior_sign=sign_now
			reversals=maxi(reversals,turns)
	return {"speed":speed,"late_range_degrees":rad_to_deg(peak),"max_step_degrees":rad_to_deg(step_peak),"direction_reversals":reversals,"final_pose":sim.latest.duplicate(true),"chains":sim.runner.chains.size()}
func run() -> void:
	folder=OS.get_cmdline_user_args()[0];app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recent.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.physics_editor.set_physics_process(false);root.size=Vector2i(2200,1200);await settle()
	if FileAccess.file_exists(folder.path_join("input/project.json")):
		check(app.open_project(folder.path_join("input")),"actual owned native avatar-and-fan recovery opens")
	else:
		var asset:=folder.path_join("hair.glb");preload("res://tests/secondary_fixture.gd").create(asset);check(app.append_object(load("res://src/model.gd").definition(asset),"model").is_empty(),"included declared-chain fixture opens");app.physics_editor.fan_editor.add_fan()
	await settle()
	for id in app.renderer.world_runtime.order:
		var actor: RefCounted=app.renderer.world_runtime.instance(id)
		if Airflow.is_fan(actor.data):fan_id=id
		else:actor_id=id
	var actor: RefCounted=app.renderer.world_runtime.instance(actor_id);var original: Dictionary=actor.data.duplicate(true);app.mode.select(2);app.change_mode(2);await start_hair()
	check(app.physics_editor.active(actor_id) and not app.physics_editor.toggle.button_pressed,"Hair & clothes runs with body physics off")
	select(fan_id);var fan: RefCounted=app.renderer.world_runtime.instance(fan_id);var ui=app.physics_editor.fan_editor
	# Reproduce a missed stream using normal root authoring, without touching the character.
	var before: Dictionary=fan.data.duplicate(true);app.pose_editor.selected="@root";app.pose_editor.set_delta(Vector3(0,40,0),Quaternion.IDENTITY);app.pose_editor.commit(before,true);ui.update_status()
	check(reached(actor,fan)==0 and ui.status.text=="Air misses hair/clothes","fan reports that strength cannot fix a stream which misses the active joints")
	var missed: Dictionary=fan.data.duplicate(true);var history: int=app.history.size();ui.aim.pressed.emit();await settle()
	check(reached(actor,fan)>0 and "Air reaches" in ui.status.text,"Aim at hair places the existing fan where its stream reaches native chains")
	check(app.history.size()==history+1 and app.physics_editor.active(actor_id) and actor.data==original,"aiming is one Undo and keeps live hair and the original character pose")
	app.physics_editor.clear();app.undo();fan=app.renderer.world_runtime.instance(fan_id);actor=app.renderer.world_runtime.instance(actor_id)
	check(fan.data==missed and actor.data==original,"Undo restores the exact missed fan placement without resetting the character")
	select(fan_id);ui.aim.pressed.emit();await settle()
	fan=app.renderer.world_runtime.instance(fan_id);before=fan.data.duplicate(true);app.pose_editor.begin_draft();fan.data.scale=2.;app.pose_editor.commit(before,true);ui.aim.pressed.emit();await settle()
	check(is_equal_approx(fan.sample_transform(0,true).scale,2.) and reached(actor,fan)>0,"Aim at hair preserves a scaled fan and accounts for its scaled head position")
	before=fan.data.duplicate(true);app.pose_editor.begin_draft();fan.data.scale=1.;app.pose_editor.commit(before,true);ui.aim.pressed.emit();await settle()
	var zero:=await measure(0.);var gentle:=await measure(3.);var strong:=await measure(12.);var repeat:=await measure(3.)
	check(not zero.has("error") and zero.late_range_degrees<.1,"zero fan speed has no artificial late flutter")
	check(gentle.late_range_degrees>.5 and gentle.direction_reversals>=2,"gentle fan continues moving loose joints back and forth after settling time")
	check(strong.late_range_degrees>gentle.late_range_degrees*1.2,"stronger fan produces a larger continuing response")
	check(gentle.max_step_degrees<1.61 and strong.max_step_degrees<1.61,"gust response respects the existing bounded angular-step limit")
	check(scalar_difference(gentle.final_pose,repeat.final_pose)<.00001,"same fixed-step state and fan settings reproduce the same flutter")
	actor=app.renderer.world_runtime.instance(actor_id);check(actor.data==original and actor.authored_keys().is_empty(),"live flutter adds no implicit character keys or source changes")
	app.physics_editor.clear();select(actor_id);ui.add_fan();var added: RefCounted=app.renderer.active_model()
	actor=app.renderer.world_runtime.instance(actor_id)
	check(Airflow.is_fan(added.data) and reached(actor,added)>0,"Add fan automatically aims at the selected character's actual joint height")
	check(actor.data==original,"auto-aiming a new fan does not repair or reset the owner's saved pose")
	var metrics:={"zero":zero,"gentle":gentle,"strong":strong,"repeat":repeat}
	for item in metrics.values():item.erase("final_pose")
	var result:={"checks":checks,"failures":failures,"metrics":metrics};FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE).store_string(JSON.stringify(result,"\t"));print("FAN_FLUTTER "+JSON.stringify(result));app.physics_editor.clear();app.free();quit(1 if failures else 0)
