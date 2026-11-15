extends SceneTree
const Fixture=preload("res://tests/limb_fixture.gd")
const Model=preload("res://src/model.gd")
const SceneIO=preload("res://src/scene3d.gd")
const Timeline=preload("res://src/timeline.gd")
const PhysicsRig=preload("res://src/physics_rig.gd")
const Storage=preload("res://src/storage.gd")
const World=preload("res://src/world_document.gd")
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(120).timeout.connect(func():push_error("Physics watchdog expired");quit(2))
	call_deferred("run")
func check(ok: bool, text: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+text)
	if not ok:failures+=1
func settled() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func wait_job(job) -> void:
	while job.pid>0:await process_frame
	await settled()
func close_warnings(app) -> void:
	for child in app.get_children():
		if child is AcceptDialog and child.title=="Imported with limitations":child.hide();child.queue_free()
func collision_floor(simulation: RefCounted) -> float:
	var minimum:=INF
	for body in simulation.bodies.values():
		var collision: CollisionShape3D=body.get_child(0);var shape: Shape3D=collision.shape
		var transform: Transform3D=collision.global_transform
		if shape is SphereShape3D:minimum=minf(minimum,transform.origin.y-shape.radius)
		elif shape is CapsuleShape3D:
			var half: float=shape.height*0.5-shape.radius
			minimum=minf(minimum,minf((transform*Vector3(0,half,0)).y,(transform*Vector3(0,-half,0)).y)-shape.radius)
		elif shape is BoxShape3D:
			for x in [-0.5,0.5]:
				for y in [-0.5,0.5]:
					for z in [-0.5,0.5]:minimum=minf(minimum,(transform*(shape.size*Vector3(x,y,z))).y)
	return minimum
func pixels(a: Image,b: Image) -> Dictionary:
	var aa:=a.get_data();var bb:=b.get_data();var count:=0;var total:=0
	for i in range(aa.size()):
		if aa[i]!=bb[i]:count+=1;total+=absi(int(aa[i])-int(bb[i]))
	return {"channels":count,"mean":float(total)/aa.size(),"close":count<=384 and float(total)/aa.size()<0.002}
func run() -> void:
	var folder:=ProjectSettings.globalize_path("res://output/physics/run_%d" % Time.get_ticks_usec());DirAccess.make_dir_recursive_absolute(folder)
	var asset:=folder.path_join("arm.glb");Fixture.create(asset);var digest:=FileAccess.get_sha256(asset)
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settled();app.home.hide()
	app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache");app.load_demo_room()
	var data:=Model.definition(asset);data.position=[0,3,0];app.append_object(data,"model")
	var actor: RefCounted=app.renderer.active_model();var id: String=actor.data.id;var physics=app.physics_editor
	app.renderer.camera.position=Vector3(3,3,6);app.renderer.camera.look_at(Vector3(0.7,1.3,0));app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,60)]
	var before: Dictionary=actor.data.duplicate(true);var history: int=app.history.size();var shots: Array=app.keys.duplicate(true)
	check(not app.advanced_mode and physics.toggle.is_visible_in_tree(),"Physics toggle is accessible in Simple")
	check(ProjectSettings.get_setting("physics/3d/physics_engine")=="Jolt Physics" and Engine.physics_ticks_per_second==120,"live physics uses explicit pinned Jolt with120Hz stepping")
	check(is_equal_approx(float(ProjectSettings.get_setting("physics/jolt_physics_3d/simulation/penetration_slop")),0.002),"contact penetration allowance is reduced to two millimeters in meter-scaled scenes")
	physics.toggle.button_pressed=true;await settled()
	check(physics.active(id) and physics.collider_triangles>0 and physics.simulations[id].bodies.size()==3,"connected Simple toggle starts a real three-body ragdoll against imported map geometry")
	var limits:=true
	for bone_id in physics.simulations[id].bodies:
		var bone: PhysicalBone3D=physics.simulations[id].bodies[bone_id];var profile: Dictionary=physics.simulations[id].joint_profiles[bone_id]
		if profile.has("lower"):limits=limits and bone.joint_type==PhysicalBone3D.JOINT_TYPE_HINGE and bool(bone.get("joint_constraints/angular_limit_enabled")) and is_equal_approx(float(bone.get("joint_constraints/angular_limit_upper")),profile.upper)
		else:limits=limits and is_equal_approx(float(bone.get("joint_constraints/swing_span")),profile.swing) and is_equal_approx(float(bone.get("joint_constraints/twist_span")),profile.twist)
	check(limits,"physical-bone properties receive separate anatomical joint types and degree ranges")
	for i in range(300):await physics_frame
	var simulation: RefCounted=physics.simulations[id];var simulated: Dictionary=simulation.pose();var end: Vector3=simulation.latest[actor.order[2]].origin
	check(actor.data==before and app.history.size()==history and actor.data.pose_keys.is_empty(),"live simulation never writes data, history or automatic motion keys")
	var low:=INF;var high:=-INF
	for body in simulation.bodies.values():low=minf(low,body.global_position.y);high=maxf(high,body.global_position.y)
	check(low>-0.02 and high<0.5,"ragdoll falls and settles against the visible map floor")
	check(simulation.bodies[actor.order[2]].get_child(0).shape is BoxShape3D,"terminal hand collider fits its weighted skin instead of a tiny generic sphere")
	physics.toggle.button_pressed=false;await settled()
	check(not physics.is_running() and actor.data.pose==simulated and actor.data.pose_keys.is_empty() and app.history.size()==history+1,"Physics off freezes the current pose in one Undo step without recording animation")
	var tip: Vector3=actor.bone_transform(actor.order[2]).origin
	for i in range(30):await physics_frame
	check(actor.bone_transform(actor.order[2]).origin.distance_to(tip)<0.00001 and absf(tip.y)<0.4,"disabled physics holds its actual fallen pose instead of snapping to rest")
	var fit:=PhysicsRig.weighted_bounds(actor,actor.bones[actor.order[0]].skeleton,actor.order)
	var mesh_low:=INF
	for bone in fit:
		for x in [0,1]:
			for y in [0,1]:
				for z in [0,1]:mesh_low=minf(mesh_low,(actor.bone_transform(bone)*(fit[bone].position+fit[bone].size*Vector3(x,y,z))).y)
	check(mesh_low>-0.015,"actual authored skinned geometry rests above the map floor within contact tolerance")
	var frozen: Dictionary=actor.data.duplicate(true)
	app.undo();check(actor.data==before,"Undo restores the exact pre-simulation authored state")
	app.redo();check(actor.data==frozen,"Redo restores the frozen pose with physics off")
	check(app.keys==shots and FileAccess.get_sha256(asset)==digest,"physics leaves explicit camera keys and source GLB unchanged")
	app.mode.select(0);app.change_mode(0);var final: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	final.save_png(folder.path_join("frozen.png"));root.get_texture().get_image().save_png(folder.path_join("physics-editor.png"))
	var project:=folder.path_join("physics.has");app.has_project.save_file(project,"packed");await wait_job(app.has_project)
	app.new_project();app.has_project.open_file(project);await wait_job(app.has_project);actor=app.renderer.world_runtime.instance(id)
	check(actor!=null and not actor.has_animation() and actor.data.pose==JSON.parse_string(JSON.stringify(frozen.pose,"",true,true)),"packed HAS preserves an unanimated frozen pose without adding motion keys")
	var reopened: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	reopened.save_png(folder.path_join("reopened.png"));var rebuilt:=pixels(final,reopened)
	check(rebuilt.close,"independent frozen-pose reimport stays within established GPU edge tolerance")
	var export_error: String=await app.export_movie(folder)
	var frame:=Image.load_from_file(app.last_export_folder.path_join("frame_000001.png"))
	check(export_error.is_empty() and frame!=null and frame.get_data()==reopened.get_data(),"MP4 rendering uses the stored frozen pose and does not restart live simulation")
	var movie: String=app.last_export_folder.path_join("movie.mp4")
	app.world_selection.select_entity(id);physics.toggle.button_pressed=true;await settled()
	simulation=physics.simulations[id]
	var ccd:=true
	for body in simulation.bodies.values():ccd=ccd and PhysicsServer3D.body_is_continuous_collision_detection_enabled(body.get_rid())
	check(ccd,"every physical bone uses continuous collision detection")
	simulation.bodies[actor.order[0]].apply_central_impulse(Vector3(0,25,-100))
	var closest:=0.0
	for i in range(120):
		await physics_frame
		for body in simulation.bodies.values():closest=minf(closest,body.global_position.z)
	check(closest>-8.2 and closest<-6.0,"impulsed ragdoll travels toward the back wall without tunneling through it")
	physics.toggle.button_pressed=false;await settled()
	app.undo();physics.toggle.button_pressed=true;await settled();simulation=physics.simulations[id]
	var grabbed_body: PhysicalBone3D=simulation.bodies[actor.order[0]]
	var body_start: Vector3=grabbed_body.global_position
	var point: Vector2=app.renderer.camera.unproject_position(body_start)
	var press:=InputEventMouseButton.new();press.button_index=MOUSE_BUTTON_LEFT;press.pressed=true
	app.canvas_input(press,point);await settled()
	check(physics.grabbing() and physics.grab_joint!=null,"actual viewport left-click grabs a simulated physical body")
	var wheel:=InputEventMouseButton.new();wheel.button_index=MOUSE_BUTTON_WHEEL_UP;wheel.pressed=true
	var depth: float=physics.grab_depth;app.canvas_input(wheel,point)
	check(physics.grab_depth<depth,"wheel changes the held body's target distance")
	physics.grab_depth=depth
	var initial_bend:=Timeline.quaternion(simulation.pose()[actor.order[1]].rotation_xyzw)
	var peak_bend:=1.0
	var motion:=InputEventMouseMotion.new();app.canvas_input(motion,point+Vector2(100,-120))
	for i in range(120):
		await physics_frame
		peak_bend=minf(peak_bend,absf(initial_bend.dot(Timeline.quaternion(simulation.pose()[actor.order[1]].rotation_xyzw))))
	check(grabbed_body.global_position.y>body_start.y+0.5,"dragging the cursor lifts the constrained ragdoll against gravity")
	var bend: float=absf(simulation.pose()[actor.order[1]].rotation_xyzw[3])
	print("GRAB_BEND ",JSON.stringify({"peak_change_degrees":rad_to_deg(2*acos(clampf(peak_bend,0,1))),"end_offset_degrees":rad_to_deg(2*acos(clampf(bend,0,1)))}))
	check(peak_bend<cos(deg_to_rad(5)*0.5),"live dragging bends an articulated joint by more than five degrees")
	app.canvas_input(motion,point+Vector2(180,-160))
	for i in range(12):await physics_frame
	var throwing_velocity: Vector3=grabbed_body.linear_velocity
	var release:=InputEventMouseButton.new();release.button_index=MOUSE_BUTTON_LEFT;release.pressed=false;release.position=Vector2(-30,-30)
	app._input(release);check(not physics.grabbing() and physics.grab_joint==null and physics.active(id),"release outside the viewport removes the grab constraint while live physics continues")
	check(throwing_velocity.length()>0.1 and grabbed_body.linear_velocity.is_equal_approx(throwing_velocity),"release retains actual drag velocity to throw without keying the model")
	point=app.renderer.camera.unproject_position(grabbed_body.global_position);app.canvas_input(press,point);await settled()
	var held_before_escape: bool=physics.grabbing()
	var escape:=InputEventKey.new();escape.keycode=KEY_ESCAPE;escape.pressed=true;app._input(escape)
	check(held_before_escape and not physics.grabbing() and physics.active(id),"Escape drops the grab safely while simulation continues")
	# Focus cleanup is independent of trying to ray-pick a freely falling thin limb.
	# Viewport picking/lifting and outside release were already tested above.
	var held_before_focus: bool=physics.begin_grab(grabbed_body,grabbed_body.global_position)
	app._notification(Control.NOTIFICATION_WM_WINDOW_FOCUS_OUT)
	check(held_before_focus and not physics.grabbing() and physics.active(id),"focus loss releases the grab constraint without keying simulation")
	physics.toggle.button_pressed=false;await settled();app.undo();app.pose_editor.record_key();app.set_frame(8)
	app.pose_editor.selected="@root";app.pose_editor.operation.select(1);app.pose_editor.refresh_values();app.pose_editor.fields[0].value=2;app.pose_editor.apply_numeric()
	app.set_frame(4);var keyed: Array=actor.authored_keys();var root_before: Transform3D=actor.root.global_transform
	physics.toggle.button_pressed=true;await settled()
	for i in range(90):await physics_frame
	physics.toggle.button_pressed=false;await settled()
	var held_tip: Transform3D=actor.bone_transform(actor.order[2])
	check(actor.root.global_transform.is_equal_approx(root_before) and actor.authored_keys()==keyed,"freezing an animated model preserves its sampled root and original keys")
	app.set_advanced(true);app.set_advanced(false);app.mode.select(0);app.change_mode(0);await settled()
	check(actor.bone_transform(actor.order[2]).is_equal_approx(held_tip),"unrecorded frozen preview survives workspace and Draw switches at the same frame")
	app.set_frame(5)
	check(actor.preview_frame==-1 and actor.authored_keys()==keyed,"scrubbing resumes the existing authored take without baking live motion")
	app.new_project();app.load_demo_room()
	var first_data:=Model.definition(asset);first_data.position=[0,3,0];app.append_object(first_data,"model");var first_id: String=app.last_import_id
	var second_data:=Model.definition(asset);second_data.position=[2,3,0];app.append_object(second_data,"model");var second_id: String=app.last_import_id
	app.world_selection.select_entity(first_id);await settled();physics.toggle.button_pressed=true;await settled()
	app.world_selection.select_entity(second_id);await settled();physics.toggle.button_pressed=true;await settled()
	check(physics.simulations.size()==2,"two independently selected ragdolls can simulate in the same world")
	app.world_selection.select_entity(first_id);await settled();physics.toggle.button_pressed=false;await settled()
	check(not physics.active(first_id) and physics.active(second_id),"Physics toggle freezes only the selected object while its peer keeps simulating")
	app.set_frame(1)
	check(not physics.is_running() and app.renderer.world_runtime.instance(first_id).data.pose_keys.is_empty() and app.renderer.world_runtime.instance(second_id).data.pose_keys.is_empty(),"scrubbing stops the remaining simulation without filling either timeline with motion keys")
	app.world_selection.select_entity(first_id);await settled();physics.toggle.button_pressed=true;await settled()
	var valid_before: Dictionary=app.renderer.active_model().data.duplicate(true);var history_before: int=app.history.size()
	simulation=physics.simulations[first_id]
	var invalid_pose: Transform3D=simulation.latest[simulation.rig.order[0]];invalid_pose.origin.y=200001;simulation.latest[simulation.rig.order[0]]=invalid_pose
	var rejected_save:=folder.path_join("invalid-physics.has");app.has_project.save_file(rejected_save,"packed")
	check(not physics.is_running() and app.renderer.active_model().data==valid_before and app.history.size()==history_before and app.has_project.pid<0 and not FileAccess.file_exists(rejected_save),"out-of-range simulated pose cannot corrupt authored data, history or a saved project")
	check(not physics.toggle.button_pressed,"a stopped/rejected simulation updates its visible Physics toggle immediately")
	var native_samples:=[];var native_metrics:={}
	for sample in ["pose-smoke/miku-project","source-smoke/source-project","sfm-smoke/project"]:
		var path:=ProjectSettings.globalize_path("res://output/"+sample)
		if not FileAccess.file_exists(path.path_join("project.json")):print("SKIP optional native physics fixture: "+sample);continue
		var original: Dictionary=World.from_project(Storage.load_project(path)).objects[-1]
		var old:=Model.new();old.data=original;var original_root: Dictionary=old.sample_transform(0)
		var native_sha:=FileAccess.get_sha256(original.source);var native_data:=Model.definition(original.source)
		native_data.name=original.name;native_data.metadata=original.metadata.duplicate(true);native_data.position=[0,3,0];native_data.rotation_xyzw=original_root.rotation_xyzw;native_data.scale=original_root.scale
		app.new_project();app.load_demo_room();app.append_object(native_data,"model");actor=app.renderer.active_model()
		var native_before: Dictionary=actor.data.duplicate(true);physics.toggle.button_pressed=true;await settled()
		check(physics.active(actor.data.id),"native standardized rig starts real ragdoll physics: "+sample)
		if not physics.active(actor.data.id):continue
		simulation=physics.simulations[actor.data.id];var initial_height: float=simulation.bodies.values()[0].global_position.y
		for i in range(360):await physics_frame
		var minimum:=INF;var maximum:=-INF;var speed:=0.0
		for body in simulation.bodies.values():minimum=minf(minimum,body.global_position.y);maximum=maxf(maximum,body.global_position.y);speed=maxf(speed,body.linear_velocity.length())
		var contact_min:=collision_floor(simulation)
		check(is_finite(minimum) and minimum>-0.05 and contact_min>-0.015 and maximum<initial_height-0.5 and speed<2,"native body centers and collision surfaces settle above the floor with bounded contact motion: "+sample)
		var center:=Vector3.ZERO
		for body in simulation.bodies.values():center+=body.global_position
		center/=simulation.bodies.size()
		var body_count: int=simulation.bodies.size();var expected: Dictionary=simulation.pose();physics.toggle.button_pressed=false;await settled()
		check(actor.data.pose==expected and actor.data.pose_keys.is_empty() and FileAccess.get_sha256(original.source)==native_sha and actor.data.metadata==native_before.metadata,"native freeze preserves skin bindings/provenance/source and makes no motion keys: "+sample)
		app.renderer.camera.position=center+Vector3(1.4,0.8,2);app.renderer.camera.look_at(center)
		var inspection_keys: Array=[Timeline.key(app.frame,app.renderer.camera.position,app.renderer.camera.quaternion,55)]
		var inspected: Image=await app.renderer.capture(inspection_keys,[],app.frame,true);inspected.save_png(folder.path_join("native-%d-final.png" % native_samples.size()))
		await settled();root.get_texture().get_image().save_png(folder.path_join("native-%d-editor.png" % native_samples.size()))
		native_metrics[sample]={"bodies":body_count,"poses":expected.size(),"min":minimum,"collision_min":contact_min,"max":maximum,"speed":speed};native_samples.append(sample)
	var vrm_samples:=[]
	for name in ["AvatarSample_A.vrm","AvatarSample_Avrm0.vrm"]:
		var source: String=preload("res://tests/native_sample_paths.gd").vrm(name)
		if not FileAccess.file_exists(source):print("SKIP optional VRM physics sample: "+name);continue
		var native_sha:=FileAccess.get_sha256(source);app.new_project();app.load_demo_room();app.pose_editor.add_model(source);await wait_job(app.source_import);close_warnings(app);await settled()
		actor=app.renderer.active_model()
		check(actor!=null,"ordinary VRM preparation produces a shared physics-ready rig: "+name)
		if not actor:continue
		actor.data.position[1]+=3;actor.apply(app.frame);var vrm_before: Dictionary=actor.data.duplicate(true)
		physics.toggle.button_pressed=true;await settled()
		check(physics.active(actor.data.id),"VRM humanoid map supports actual ragdoll startup: "+name)
		if not physics.active(actor.data.id):continue
		simulation=physics.simulations[actor.data.id]
		for i in range(360):await physics_frame
		var lowest:=INF;var speed:=0.0
		for body in simulation.bodies.values():lowest=minf(lowest,body.global_position.y);speed=maxf(speed,body.linear_velocity.length())
		physics.toggle.button_pressed=false;await settled()
		check(lowest>-0.05 and speed<2 and not actor.data.pose.is_empty() and actor.data.pose_keys.is_empty() and actor.data.metadata==vrm_before.metadata and FileAccess.get_sha256(source)==native_sha,"VRM falls, freezes and preserves native data without recording: "+name)
		var center:=Vector3.ZERO
		for bone in actor.order:center+=actor.bone_transform(bone).origin
		center/=actor.order.size()
		app.renderer.camera.position=center+Vector3(1.4,0.8,2);app.renderer.camera.look_at(center)
		var inspected: Image=await app.renderer.capture([Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,55)],[],0,true)
		inspected.save_png(folder.path_join(name+"-fallen.png"))
		vrm_samples.append(name)
	var no_rig:=Model.new()
	check(PhysicsRig.create(no_rig).has("error"),"unrigged props get an actionable fallback rather than an invalid ragdoll")
	actor=app.renderer.active_model()
	var sk: Skeleton3D=actor.bones[actor.order[0]].skeleton;var previous_scale:=sk.scale;var children:=sk.get_child_count();var unchanged: Dictionary=actor.data.duplicate(true)
	sk.scale=Vector3(1,2,1);var unsupported:=PhysicsRig.create(actor);sk.scale=previous_scale
	check(unsupported.has("error") and sk.get_child_count()==children and actor.data==unchanged,"unsupported skeleton scale fails without adding bodies or changing authored data")
	app.new_project();app.load_demo_room()
	var reset_data:=Model.definition(asset);reset_data.position=[0,3,0];app.append_object(reset_data,"model")
	actor=app.renderer.active_model();var reset_id: String=actor.data.id
	physics.toggle.button_pressed=true;await settled()
	for i in range(90):await physics_frame
	physics.toggle.button_pressed=false;await settled()
	app.pose_editor.auto_key.button_pressed=false
	var frozen_reset: Dictionary=actor.data.duplicate(true);var reset_shots: Array=app.keys.duplicate(true);var reset_history: int=app.history.size()
	check(not frozen_reset.pose.is_empty() and frozen_reset.pose_keys.is_empty(),"context reset starts from a real frozen unrecorded ragdoll")
	app.world_selection.context_action(1);await settled();actor=app.renderer.world_runtime.instance(reset_id)
	check(actor.data.pose.is_empty() and actor.data.pose_keys.is_empty() and not physics.is_running() and app.history.size()==reset_history+1,"Simple object context Reset pose restores rest pose as one undoable action without recording")
	app.undo();await settled();actor=app.renderer.world_runtime.instance(reset_id)
	check(actor.data==frozen_reset and app.keys==reset_shots,"Undo context reset restores the exact frozen pose and leaves camera keys unchanged")
	app.redo();await settled();actor=app.renderer.world_runtime.instance(reset_id)
	check(actor.data.pose.is_empty() and actor.data.pose_keys.is_empty() and FileAccess.get_sha256(asset)==digest,"Redo context reset preserves original rig and creates no motion take")
	var result:={"checks":checks,"failures":failures,"folder":folder,"movie":movie,"project":project,"floor_min":low,"floor_max":high,"skin_min":mesh_low,"reimport_pixels":rebuilt,"native_samples":native_samples,"native_metrics":native_metrics,"vrm_samples":vrm_samples,"wall_z":closest}
	var file:=FileAccess.open("res://output/physics-result.json",FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close()
	print("PHYSICS_SMOKE "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
