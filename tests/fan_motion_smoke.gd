extends SceneTree
const Fixture=preload("res://tests/secondary_fixture.gd")
const Model=preload("res://src/model.gd")
const Timeline=preload("res://src/timeline.gd")
const Airflow=preload("res://src/airflow.gd")
const Secondary=preload("res://src/secondary_live.gd")
const Drawing=preload("res://src/drawing.gd")
const Spring=preload("res://src/secondary_spring.gd")
const Definition=preload("res://src/secondary_rig.gd")
var checks:=0
var failures:=0
var folder: String
var metrics:={}
func _initialize() -> void:
	create_timer(220).timeout.connect(func():push_error("Fan watchdog expired");quit(2));call_deferred("run")
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func settled() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func wait_job(job) -> void:
	while job.pid>0:await process_frame
	await settled()
func wait_hair(physics,id: String) -> void:
	while physics.pending.has(id):await process_frame
	await settled()
func difference(a: Dictionary,b: Dictionary) -> float:
	var result:=0.0
	var ids: Array=a.keys()
	for id in b:
		if not id in ids:ids.append(id)
	for id in ids:result=maxf(result,Timeline.quaternion(a.get(id,Model.identity()).rotation_xyzw).angle_to(Timeline.quaternion(b.get(id,Model.identity()).rotation_xyzw)))
	return result
func select(app,id: String) -> void:app.world_selection.select_entity(id,false)
func native(app,path: String,label: String) -> void:
	app.new_project();app.load_demo_room();app.pose_editor.add_model(path);await wait_job(app.source_import)
	for child in app.get_children():
		if child is AcceptDialog and child.title=="Imported with limitations":child.hide();child.queue_free()
	var physics=app.physics_editor;var actor: RefCounted=app.renderer.active_model()
	if not actor:check(false,"native model loaded: "+label);return
	var id: String=actor.data.id;actor.data.position=[0,3,0];actor.apply(0)
	physics.fan_editor.add_fan();var fan: RefCounted=app.renderer.active_model();var fan_id: String=fan.data.id;actor=app.renderer.world_runtime.instance(id)
	fan.data.position=[0,3.7,-2];fan.data.rotation_xyzw=[0,0,0,1];fan.data.metadata.airflow.speed=8;fan.apply(0)
	var before: Dictionary=actor.data.duplicate(true);var root_pose: Transform3D=actor.root.global_transform
	var raw_created: Dictionary=await Spring.create(actor);var raw: RefCounted=raw_created.runner;var raw_maximum:=0.0;var raw_previous: Dictionary=actor.sample(0,true)
	var fields:=Airflow.collect(app.renderer,0,{})
	for i in range(120):
		var forces: Array=[]
		for chain in raw.chains:forces.append(Airflow.force(fields,Definition.binding_transform(actor,chain.source.joints[0].binding).origin))
		var raw_pose: Dictionary=raw.step(1.0/120,Vector3.ZERO,forces).pose;raw_maximum=maxf(raw_maximum,difference(raw_pose,raw_previous));raw_previous=raw_pose
	raw.dispose()
	select(app,id);app.mode.select(2);app.change_mode(2);physics.hair_toggle.button_pressed=true;await wait_hair(physics,id)
	check(physics.active(id) and physics.simulations[id] is Secondary,"actual native rig enters the same Simple hair simulation: "+label)
	if not physics.active(id):return
	var sim: RefCounted=physics.simulations[id];var previous: Dictionary=sim.pose();var maximum:=0.0
	for i in range(120):
		await physics_frame;var pose: Dictionary=sim.pose();maximum=maxf(maximum,difference(pose,previous));previous=pose
	check(maximum<deg_to_rad(1.6) and actor.root.global_transform.is_equal_approx(root_pose) and not physics.toggle.button_pressed,"native activation bounds local joint jumps while keeping the body posed: "+label)
	check(maximum<raw_maximum*0.25,"controlled activation reduces native peak joint steps versus the same unsmoothed wind setup: "+label)
	metrics[label]={"maximum_step_radians":maximum,"raw_maximum_step_radians":raw_maximum,"chains":sim.runner.chains.size()}
	check(actor.data==before and not actor.has_animation(),"native live hair retains original parameters and creates no automatic take: "+label)
	if label.ends_with("vrm0"):
		# Exercise the reverse activation order as well as Hair-first on VRM1.
		var off_history: int=app.history.size();physics.hair_toggle.button_pressed=false;await settled()
		check(actor.data==before and app.history.size()==off_history,"native hair off restores authored state without a freeze edit: "+label)
		select(app,id)
		physics.toggle.button_pressed=true;await settled()
		check(physics.body_active(id) and not physics.hair_toggle.button_pressed,"body starts independently before secondary setup: "+label)
		physics.hair_toggle.button_pressed=true;await wait_hair(physics,id)
	physics.toggle.button_pressed=true;await settled();sim=physics.simulations[id]
	check(sim is Secondary and sim.primary!=null and physics.toggle.button_pressed and physics.hair_toggle.button_pressed,"body ragdoll and secondary motion can run together: "+label)
	if not sim.primary:return
	var preserved:=true
	for chain in sim.runner.chains:
		for bone in chain.ids:
			preserved=preserved and Timeline.quaternion(sim.primary.initial_pose.get(bone,Model.identity()).rotation_xyzw).angle_to(Timeline.quaternion(before.pose.get(bone,Model.identity()).rotation_xyzw))<0.000001
	check(preserved,"adding body physics preserves authored secondary rest instead of reusing simulated sway: "+label)
	var primary: RefCounted=sim.primary;var body_count: int=primary.bodies.size();var live_before: Dictionary=actor.data.duplicate(true)
	physics.hair_toggle.button_pressed=false;await settled()
	check(physics.simulations.get(id)==primary and primary.running and primary.bodies.size()==body_count and body_count>0 and actor.data==live_before,"native hair off retains the same active body solver and authored data: "+label)
	physics.hair_toggle.button_pressed=true
	check(physics.pending.has(id),"native hair setup actually enters its asynchronous pending stage: "+label)
	physics.change_hair(false)
	for i in range(8):await process_frame
	await settled()
	check(physics.simulations.get(id)==primary and primary.running and primary.bodies.size()==body_count and actor.data==live_before,"cancelling pending native hair setup keeps its borrowed body solver alive: "+label)
	physics.hair_toggle.button_pressed=true;await wait_hair(physics,id);sim=physics.simulations[id]
	var body: PhysicsBody3D=sim.bodies.values()[0]
	check(physics.begin_grab(body,body.global_position),"combined simulation retains actual body grab controls: "+label);physics.release_grab()
	select(app,fan_id);physics.toggle.button_pressed=true;await settled()
	check(physics.active(fan_id),"fan can also act as an ordinary dynamic prop during World capture: "+label)
	select(app,id);var record=physics.recording;record.scope.select(1);record.button.pressed.emit()
	check(record.active and record.targets.has(id) and record.targets.has(fan_id),"World Record includes combined native rig and dynamic fan: "+label)
	select(app,fan_id);physics.sync();physics.fan_editor.edit("speed",12)
	check(fan.data.metadata.airflow.speed==8 and physics.fan_editor.enabled.disabled and not physics.fan_editor.speed.editable,"captured fan settings stay locked without invalidating the World take: "+label)
	select(app,id)
	while record.active:await process_frame
	actor=app.renderer.world_runtime.instance(id);fan=app.renderer.world_runtime.instance(fan_id)
	check(record.last_error.is_empty() and actor.authored_keys().size()==49 and fan.authored_keys().size()==49 and not physics.is_running(),"native combined World take completes and leaves ordinary editable motion: "+label)
	var state: Dictionary=actor.sample(24);var project:=folder.path_join(label+"-wind.has");app.has_project.save_file(project,"packed");await wait_job(app.has_project)
	app.new_project();app.has_project.open_file(project);await wait_job(app.has_project);actor=app.renderer.world_runtime.instance(id)
	check(JSON.stringify(actor.sample(24))==JSON.stringify(state) and actor.data.metadata==before.metadata,"native combined hair/body take and provenance survive packed reopen: "+label)
	app.set_frame(24);app.renderer.camera.position=Vector3(1.8,1.4,3);app.renderer.camera.look_at(Vector3(0,0.9,0))
	await settled();root.get_texture().get_image().save_png(folder.path_join(label+"-editor.png"))
func moving_anchor(app,asset: String) -> void:
	app.new_project();var data:=Model.definition(asset)
	data.pose_keys=[{"frame":0,"pose":{},"transform":{"position":[0,0,0],"rotation_xyzw":[0,0,0,1],"scale":1},"interpolation":"linear"},{"frame":48,"pose":{},"transform":{"position":[0.6,0,0],"rotation_xyzw":[0,0,0,1],"scale":1},"interpolation":"linear"}]
	app.append_object(data,"model");var id: String=app.last_import_id;var physics=app.physics_editor
	physics.fan_editor.add_fan();var fan: RefCounted=app.renderer.active_model();fan.data.position=[0,1,-2];fan.data.rotation_xyzw=[0,0,0,1];fan.apply(0)
	var actor: RefCounted=app.renderer.world_runtime.instance(id)
	check(absf(actor.sample_transform(0.5).position[0]-0.00625)<0.000001,"fractional physics sampling preserves continuous authored motion between integer keys")
	select(app,id);physics.hair_toggle.button_pressed=true;await wait_hair(physics,id);var record=physics.recording;record.scope.select(0);record.button.pressed.emit()
	var step:=0.0;var previous: float=actor.root.global_position.x
	while record.active:
		await physics_frame;var x: float=actor.root.global_position.x;step=maxf(step,absf(x-previous));previous=x
	check(record.last_error.is_empty() and absf(actor.sample_transform(24).position[0]-0.3)<0.0001 and step<0.003,"recorded authored anchors advance at120Hz without24fps stair steps or phase drift")
	metrics["anchor_max_step"]=step
func lifecycle(app,asset: String) -> void:
	app.new_project();app.append_object(Model.definition(asset),"model");var id: String=app.last_import_id
	var actor: RefCounted=app.renderer.active_model();var before: Dictionary=actor.data.duplicate(true);var physics=app.physics_editor;var record=physics.recording
	physics.hair_toggle.button_pressed=true;await wait_hair(physics,id);var history: int=app.history.size();record.start()
	while record.active and record.last_frame<4:await process_frame
	record.cancel()
	check(not physics.is_running() and actor.data==before and app.history.size()==history,"cancelled secondary recording restores authoring without a take or extra Undo")
	physics.hair_toggle.button_pressed=true;await wait_hair(physics,id);record.start()
	while record.active and record.last_frame<4:await process_frame
	app.set_frame(12)
	check(not record.active and not physics.is_running() and actor.has_animation() and app.frame==12,"seeking commits the partial secondary take and stops its solver")
	app.undo();app.set_frame(0);physics.hair_toggle.button_pressed=true;await wait_hair(physics,id);record.start()
	while record.active and record.last_frame<4:await process_frame
	var project:=folder.path_join("partial-secondary.has");app.has_project.save_file(project,"packed");await wait_job(app.has_project)
	var state: Dictionary=actor.data.duplicate(true)
	app.new_project();app.has_project.open_file(project);await wait_job(app.has_project);actor=app.renderer.world_runtime.instance(id)
	check(not record.active and not physics.is_running() and actor.has_animation() and JSON.stringify(actor.sample(4))==JSON.stringify(Model.curve_pose(preload("res://src/animation_clips.gd").location(state,4).a)),"Save during secondary capture preserves an ordinary partial take through reopen")
func hair_off(app,asset: String) -> void:
	app.new_project();app.append_object(Model.definition(asset),"model")
	var actor: RefCounted=app.renderer.active_model();var id: String=actor.data.id;var physics=app.physics_editor
	var definition: Dictionary=actor.root.get_meta("has_secondary_rig");var joint: String=definition.chains[0].joints[0].binding.id
	var transform: Dictionary=actor.sample_transform(0)
	var posed: Dictionary={joint:{"position":[0,0,0],"rotation_xyzw":[0,0,sin(0.18),cos(0.18)]}}
	actor.data.pose_keys=[{"frame":0,"pose":{},"transform":transform.duplicate(true),"interpolation":"linear"},{"frame":24,"pose":posed.duplicate(true),"transform":transform.duplicate(true),"interpolation":"linear"}]
	app.mode.select(2);app.change_mode(2);app.set_frame(12)
	# A manual current-frame draft differs from the recorded track and must survive.
	actor.data.draft_frame=12;actor.data.pose=posed.duplicate(true);app.pose_editor.apply_frame()
	var expected: Transform3D=actor.bone_transform(joint);var recorded: Dictionary=actor.sample(24).duplicate(true)
	physics.fan_editor.add_fan();var fan: RefCounted=app.renderer.active_model()
	fan.data.position=[0,1,-2];fan.data.rotation_xyzw=[0,0,0,1];fan.data.metadata.airflow.speed=8;fan.apply(12)
	select(app,id);var before: Dictionary=actor.data.duplicate(true);var history: int=app.history.size()
	for cycle in range(2):
		select(app,id);physics.hair_toggle.button_pressed=true;await wait_hair(physics,id)
		if not physics.active(id):check(false,"hair-off regression starts actual solver");return
		for i in range(90):await physics_frame
		check(difference(physics.simulations[id].pose(),posed)>0.01,"hair-off regression actually deforms a non-rest authored pose")
		physics.hair_toggle.button_pressed=false;await settled()
		actor=app.renderer.world_runtime.instance(id)
		check(not physics.active(id) and actor.data==before and app.history.size()==history,"Hair & clothes off restores exact authored data and adds no freeze draft or history")
		var restored: Transform3D=actor.bone_transform(joint)
		check(actor.live_pose==null and restored.is_equal_approx(expected),"Hair & clothes off restores the visible manual pose rather than rest or simulated sway")
	app.set_frame(24)
	check(actor.sample(24)==recorded and actor.authored_keys().size()==2,"hair toggle cycles preserve the explicit recorded track when seeking")
func run() -> void:
	folder=ProjectSettings.globalize_path("res://output/fan-motion/run_"+str(Time.get_ticks_usec()));DirAccess.make_dir_recursive_absolute(folder)
	var asset:=folder.path_join("hair-skirt.glb");Fixture.create(asset)
	var app=load("res://main.tscn").instantiate();root.add_child(app);await settled()
	app.new_project();app.append_object(Model.definition(asset),"model");var id: String=app.last_import_id
	var actor: RefCounted=app.renderer.active_model();var before: Dictionary=actor.data.duplicate(true);var source_sha:=FileAccess.get_sha256(asset)
	var physics=app.physics_editor;var fan_ui=physics.fan_editor
	fan_ui.add_fan();var fan: RefCounted=app.renderer.active_model();var fan_id: String=fan.data.id
	actor=app.renderer.world_runtime.instance(id)
	check(fan_id!=id and Airflow.is_fan(fan.data) and app.renderer.world_runtime.order.size()==2,"Simple Add fan appends a standard selectable object without replacing the character")
	fan.data.position=[0,1,-2];fan.data.rotation_xyzw=[0,0,0,1];fan.apply(0);fan_ui.sync()
	check(fan_ui.panel.visible and fan_ui.enabled.button_pressed and fan_ui.speed.value==3,"selected fan exposes simple on/off and blowing-speed controls")
	var settings:=Airflow.defaults();var t:=Transform3D.IDENTITY
	check(Airflow.field(t,settings,Vector3(0,0.85,2)).z>2.9 and Airflow.field(t,settings,Vector3(0,0.85,-1))==Vector3.ZERO and Airflow.field(t,settings,Vector3(10,0.85,2))==Vector3.ZERO and Airflow.field(t,settings,Vector3(0,0.85,6))==Vector3.ZERO,"fan field is directional and bounded by range and width")
	settings.speed=6;check(Airflow.field(t,settings,Vector3(0,0.85,2)).z>5.9,"blowing speed changes local airflow strength")
	var rotated:=Transform3D(Basis(Vector3.UP,PI/2),Vector3.ZERO)
	check(Airflow.field(rotated,settings,Vector3(2,0.85,0)).x>5.9 and Airflow.field(rotated,settings,Vector3(0,0.85,2)).length()<0.0001,"rotating the ordinary fan root aims airflow in world space")
	select(app,id);app.mode.select(2);app.change_mode(2);physics.hair_toggle.button_pressed=true;await wait_hair(physics,id)
	check(physics.active(id) and physics.simulations[id] is Secondary and not physics.toggle.button_pressed and physics.hair_toggle.button_pressed,"Hair & clothes runs through connected Simple control while body physics stays off")
	var sim: RefCounted=physics.simulations[id];var first: Dictionary=sim.latest.duplicate(true);var largest:=0.0;var previous: Dictionary=first
	for tick in range(120):
		await physics_frame;var current: Dictionary=sim.latest.duplicate(true);largest=maxf(largest,difference(current,previous));previous=current
	check(difference(sim.latest,first)>0.01 and largest<deg_to_rad(1.6),"fan deforms the standing model with a bounded activation transition")
	metrics["authored_step_radians"]=largest
	check(actor.data==before and actor.data.pose_keys.is_empty() and FileAccess.get_sha256(asset)==source_sha,"live hair motion creates no implicit keys and leaves original geometry/data unchanged")
	# Real standard root authoring on a nonphysical fan must not stop its target.
	select(app,fan_id);var old_position: Vector3=fan.root.position;app.pose_editor.selected="@root";app.pose_editor.operation.select(1)
	var old: Dictionary=fan.data.duplicate(true);app.pose_editor.begin_draft();fan.data.position=[0.3,1,-2];app.pose_editor.commit(old,true)
	check(physics.active(id) and fan.root.position.distance_to(old_position)>0.1 and fan.authored_keys().size()==1,"moving a fan with standard root authoring keeps hair simulation running")
	fan_ui.speed.value=8;check(fan.data.metadata.airflow.speed==8 and physics.active(id),"connected blowing-speed edit affects the live fan without stopping the character")
	var old_size:=root.size;root.size=Vector2i(1200,800);await settled()
	check(app.get_combined_minimum_size().x<=1200 and fan_ui.speed.get_global_rect().end.x<=app.size.x and physics.hair_toggle.get_global_rect().end.x<=app.size.x and app.canvas.size.x>=600,"wrapped simulation toolbar keeps fan controls and canvas usable at1200pixels")
	root.get_texture().get_image().save_png(folder.path_join("fan-running-editor.png"));root.size=old_size;await settled()
	select(app,id);var pose: Dictionary=sim.pose();var history: int=app.history.size();physics.hair_toggle.button_pressed=false;await settled()
	check(not physics.is_running() and app.history.size()==history and actor.data==before and actor.data.pose_keys.is_empty(),"Hair off restores authored state without creating a freeze edit or keys")
	var fan_before: Dictionary=fan.data.duplicate(true);app.undo();app.redo()
	actor=app.renderer.world_runtime.instance(id);fan=app.renderer.world_runtime.instance(fan_id)
	check(actor.data==before and fan.data==fan_before,"hair restoration preserves ordinary fan Undo/Redo without a phantom history command")
	# Use the existing connected recorder, not a test-only range installation.
	select(app,id);physics.hair_toggle.button_pressed=true;await wait_hair(physics,id)
	var record=physics.recording;record.scope.select(0);record.button.pressed.emit()
	check(record.active and record.targets.keys()==[id],"Local Record captures the selected hair simulation through the normal button")
	while record.active:await process_frame
	actor=app.renderer.world_runtime.instance(id)
	check(record.last_error.is_empty() and actor.authored_keys().size()==49 and not physics.is_running(),"secondary-only Local take reaches the full two-second range and stops cleanly")
	var sampled: Dictionary=actor.sample(24)
	Drawing.insert(app.layers[1],0,48,Drawing.blank(1920,1080));Drawing.edit_image(Drawing.cel_at(app.layers[1],0)).image.set_pixel(100,100,Color.RED)
	app.renderer.camera.position=Vector3(2,1.5,4);app.renderer.camera.look_at(Vector3(0,1,0));app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,55)]
	var project:=folder.path_join("fan.has");app.has_project.save_file(project,"packed");await wait_job(app.has_project)
	app.new_project();app.has_project.open_file(project);await wait_job(app.has_project)
	actor=app.renderer.world_runtime.instance(id);fan=app.renderer.world_runtime.instance(fan_id)
	check(fan.data.metadata.airflow.speed==8 and fan.authored_keys().size()==1 and JSON.stringify(actor.sample(24))==JSON.stringify(sampled),"packed HAS retains fan parameters, authored fan movement and recorded secondary motion")
	var valid_fan: Dictionary=fan.data.duplicate(true);var invalid:=valid_fan.duplicate(true);invalid.metadata.airflow.speed=INF
	check(not Model.validate(invalid,48).is_empty(),"nonfinite fan settings reject under standard model validation")
	app.set_frame(24);var image: Image=await app.renderer.capture(app.keys,app.layers,24,true)
	var error: String=await app.export_movie(folder)
	check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000025.png")).get_data()==image.get_data(),"normal recorded fan response exports with exact reopened preview pixels")
	var movie: String=app.last_export_folder.path_join("movie.mp4")
	for path in OS.get_cmdline_user_args():
		if path.ends_with(".vrm"):await native(app,path,path.get_file().get_basename())
	await moving_anchor(app,asset)
	await lifecycle(app,asset)
	await hair_off(app,asset)
	# Cancel asynchronous setup using an actual world replacement.
	app.new_project();app.append_object(Model.definition(asset),"model");physics.hair_toggle.button_pressed=true;app.new_project();await settled()
	check(physics.pending.is_empty() and not physics.is_running() and app.renderer.world_runtime.order.is_empty(),"New during asynchronous hair setup leaves no stale solver or object")
	var output:={"checks":checks,"failures":failures,"folder":folder,"movie":movie,"metrics":metrics}
	var file:=FileAccess.open("res://output/fan-motion-result.json",FileAccess.WRITE);file.store_string(JSON.stringify(output));file.close();print("FAN_MOTION "+JSON.stringify(output));app.free();quit(0 if failures==0 else 1)
