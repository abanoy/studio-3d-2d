extends SceneTree
const Model=preload("res://src/model.gd")
const Contact=preload("res://src/contact_animation.gd")
const World=preload("res://src/world_document.gd")
var app
var checks:=0
var failures:=0
var folder: String
var native_reports:={}
func _initialize() -> void:
	create_timer(100).timeout.connect(func():push_error("Contact animation watchdog");quit(2));call_deferred("run")
func check(ok: bool,text: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+text)
	if not ok:failures+=1
func settled() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func root_value(y: float) -> Dictionary:return {"position":[0,y,0],"rotation_xyzw":[0,0,0,1],"scale":1.}
func bone_state(rig) -> Array:
	var result:=[]
	for id in rig.order:
		var b: Dictionary=rig.bones[id]
		result.append([b.skeleton.get_bone_pose_position(b.index),b.skeleton.get_bone_pose_rotation(b.index),b.skeleton.get_bone_pose_scale(b.index)])
	return result
func native_evaluation(rig,label: String) -> void:
	rig.apply(0,false,false,app.video)
	var track:=Contact.Contacts.capture(rig,0,25,"native-"+label)
	check(not track.has("error"),"native normal contact capture: "+label)
	if track.has("error"):return
	var foot: Dictionary=track.segments[0].feet[0]
	var upper: Vector3=rig.bone_transform(foot.ids[0]).origin
	var down: Vector3=Model.Timeline.vector(foot.position)-upper
	var delta: Vector3=rig.root.get_parent().global_basis.inverse()*down*.2
	var initial: Dictionary=rig.sample_transform(0);var source_sha:=FileAccess.get_sha256(rig.data.source);var metadata: Dictionary=rig.data.metadata.duplicate(true)
	for frame in [0,24]:
		var value: Dictionary=initial.duplicate(true);var p: Vector3=Model.Timeline.vector(value.position)+delta*(0. if frame==0 else 1.);value.position=[p.x,p.y,p.z]
		var before: Dictionary=rig.data.duplicate(true)
		var error: String=rig.put_pose_key({"frame":frame,"pose":{},"transform":value,"authored_channels":["@root"],"interpolation":"ease"},48,false,before)
		if not error.is_empty():check(false,error);return
	var data:=Contact.promote(rig.data,48);data.animation_clips[0]["foot_contacts"]=track
	var world: Dictionary=app.current_world();world.objects=[data]
	check(app.restore_world(world).is_empty(),"native model7 validates and binds through ordinary world loader: "+label)
	rig=app.renderer.world_runtime.instance(data.id)
	var peak:=0.;var exact:=true;var poses:=[]
	for pass_index in range(2):
		var frames:=range(49)
		if pass_index==1:frames.reverse()
		for half in frames:
			var at:=float(half)/2;var pose: Dictionary=rig.sample(at)
			exact=exact and rig.evaluation_error.is_empty()
			if pass_index==0:poses.append(pose)
			else:exact=exact and poses[half]==pose
			if half%2==0:
				app.renderer.world_runtime.evaluate(int(at),false,"",app.video)
				for target in track.segments[0].feet:peak=maxf(peak,rig.bone_transform(target.ids[2]).origin.distance_to(Model.Timeline.vector(target.position)))
	check(exact and peak<.0002,"native normal preview and fractional reverse sampling retain both pins: "+label)
	check(rig.data.metadata==metadata and FileAccess.get_sha256(rig.data.source)==source_sha,"native identities, provenance and source bytes stay unchanged: "+label)
	native_reports[label]={"peak_error":peak,"samples":98}
func run() -> void:
	folder=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder)
	var asset:=folder.path_join("figure.glb");preload("res://src/tutorial_assets.gd").figure(asset);var sha:=FileAccess.get_sha256(asset)
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false
	app.pose_editor.add_model(asset);var rig: RefCounted=app.renderer.active_model()
	for frame in [0,24]:
		var before: Dictionary=rig.data.duplicate(true)
		var error: String=rig.put_pose_key({"frame":frame,"pose":{},"transform":root_value(0. if frame==0 else -.15),"authored_channels":["@root"],"interpolation":"ease"},48,false,before)
		check(error.is_empty(),"ordinary root control installs at "+str(frame))
	app.set_frame(0);var legacy: Dictionary=rig.data.duplicate(true)
	var track:=Contact.Contacts.capture(rig,0,25,"planted")
	check(not track.has("error"),"capture native world endpoints before version promotion")
	if track.has("error"):app.free();quit(1);return
	var data:=Contact.promote(legacy,48);data.animation_clips[0]["foot_contacts"]=track
	check(Model.validate(data,48).is_empty() and data.format==Model.CONTACT_FORMAT,"normal model validation accepts versioned contacts and body controls")
	var bad:=data.duplicate(true);bad.format=Model.BODY_FORMAT
	check(not Model.validate(bad,48).is_empty(),"model6 cannot silently accept contacts")
	bad=data.duplicate(true);bad.animation_clips[0].foot_contacts.segments[0].feet[1].position[0]=NAN
	check(not Model.validate(bad,48).is_empty(),"nonfinite contact targets reject in ordinary validation")
	var world: Dictionary=app.current_world();world.objects[0]=data
	check(app.restore_world(world).is_empty(),"normal world preparation accepts exact contact leg bindings")
	rig=app.renderer.world_runtime.instance(data.id);app.world_selection.select_entity(data.id);app.pose_editor.frame_model()
	var original: Dictionary=rig.data.duplicate(true);var shots: Array=app.keys.duplicate(true)
	var peak:=0.;var solved:=[];var errors:=0;var began:=Time.get_ticks_usec();var isolated:=true
	for pass_index in range(2):
		var addresses:=range(49)
		if pass_index==1:addresses.reverse()
		for half in addresses:
			var frame:=float(half)/2;var root_before: Transform3D=rig.root.transform;var bones_before:=bone_state(rig)
			var pose: Dictionary=rig.sample(frame)
			isolated=isolated and rig.root.transform==root_before and bone_state(rig)==bones_before
			if not rig.evaluation_error.is_empty():errors+=1;print("CONTACT_EVALUATION_ERROR ",frame," ",rig.evaluation_error)
			if pass_index==0:solved.append(pose)
			else:isolated=isolated and pose==solved[half]
			if half%2==0:
				app.renderer.world_runtime.evaluate(int(frame),false,"",app.video)
				for foot in track.segments[0].feet:peak=maxf(peak,rig.bone_transform(foot.ids[2]).origin.distance_to(Model.Timeline.vector(foot.position)))
	var evaluation_probe_ms:=float(Time.get_ticks_usec()-began)/1000.
	check(errors==0 and peak<.0002,"normal world playback holds both endpoints between authored root keys")
	check(isolated,"fractional/reverse read-only samples are exact and restore displayed root and bones")
	check(rig.data==original and app.keys==shots and FileAccess.get_sha256(asset)==sha,"evaluation preserves authored document, camera keys and source bytes")
	app.set_frame(12);await settled();var image: Image=app.renderer.viewport.get_texture().get_image();image.save_png(folder.path_join("midpoint.png"))
	var split:=Model.Clips.split(rig.data,12)
	check(not split.has("error") and Model.validate(split.data,48).is_empty() and split.data.format==Model.CONTACT_FORMAT,"real source split retains valid versioned contacts")
	var saved:=folder.path_join("contacts.has")
	app.has_project.save_file(saved,"packed")
	while app.has_project.pid>0:await process_frame
	check(FileAccess.file_exists(saved),"ordinary packed HAS saves editable model7 contact state")
	app.new_project();app.has_project.open_file(saved)
	while app.has_project.pid>0:await process_frame
	check(app.renderer.world_runtime!=null and app.renderer.world_runtime.instance(data.id)!=null,"ordinary HAS Open restores model7 through complete world preparation")
	rig=app.renderer.world_runtime.instance(data.id);app.set_frame(12)
	var portable: Dictionary=rig.data.duplicate(true);portable.source=original.source
	for pair in [["expected",original],["reopened",portable]]:
		var diagnostic:=FileAccess.open(folder.path_join(pair[0]+".json"),FileAccess.WRITE);diagnostic.store_string(JSON.stringify(pair[1],"",true,true));diagnostic.close()
	portable.erase("path")
	var expected: Dictionary=JSON.parse_string(JSON.stringify(original,"",true,true))
	check(JSON.stringify(portable,"",true,true)==JSON.stringify(expected,"",true,true),"contact/body serialized values survive packed reopen without sampled-key replacement")
	var motion_exact:=true;var raw_position_delta:=0.
	for half in range(49):motion_exact=motion_exact and rig.sample(float(half)/2)==solved[half]
	for i in range(2):
		var old_foot: Dictionary=original.animation_clips[0].foot_contacts.segments[0].feet[i];var new_foot: Dictionary=rig.data.animation_clips[0].foot_contacts.segments[0].feet[i]
		motion_exact=motion_exact and Model.Timeline.vector(old_foot.position)==Model.Timeline.vector(new_foot.position) and Model.Timeline.quaternion(old_foot.rotation_xyzw)==Model.Timeline.quaternion(new_foot.rotation_xyzw)
		for axis in range(3):raw_position_delta=maxf(raw_position_delta,absf(float(old_foot.position[axis])-float(new_foot.position[axis])))
	check(motion_exact,"all half-frame resolved poses and engine targets are exact after real HAS reopen")
	var reference: Image=await app.renderer.capture(app.keys,app.layers,12,true)
	var visible:=0
	for y in range(0,1080,3):
		for x in range(0,1920,3):
			var color:=reference.get_pixel(x,y)
			if maxf(color.r,maxf(color.g,color.b))-minf(color.r,minf(color.g,color.b))>.12:visible+=1
	check(visible>100,"final shot contains positively visible colored planted skin")
	var error: String=await app.export_movie(folder)
	check(error.is_empty(),"normal MP4 export samples the same planted-foot evaluator")
	var exported:=Image.load_from_file(app.last_export_folder.path_join("frame_000013.png"))
	check(reference.get_data()==exported.get_data(),"reopened planted midpoint and exported PNG are byte-exact")
	var movie: String=app.last_export_folder.path_join("movie.mp4")
	# An animated parent is sampled at query time even when the display is on another frame.
	var empty:=folder.path_join("empty.glb");preload("res://src/scene3d.gd").make_empty(empty)
	var parent: Dictionary=World.object(empty,"group","Moving parent");var parent_rig:=Model.new();parent_rig.data=parent
	for at in [0,24]:
		var before: Dictionary=parent_rig.data.duplicate(true);var value:=root_value(0.);value.position[0]=.03*float(at)/24.;value.scale=1.+.02*float(at)/24.
		parent_rig.put_pose_key({"frame":at,"pose":{},"transform":value,"authored_channels":["@root"],"interpolation":"ease"},48,false,before)
	parent=parent_rig.data;data=rig.data.duplicate(true);data.parent_id=parent.id
	world=World.empty();world.objects=[data,parent]
	check(app.restore_world(world).is_empty(),"contact child installs before animated parent in serialized world")
	rig=app.renderer.world_runtime.instance(data.id);var parent_peak:=0.;var parent_exact:=true
	for half in range(49):
		var at:=float(half)/2;app.renderer.world_runtime.evaluate(24,false,"",app.video)
		var parent_before: Transform3D=app.renderer.world_runtime.instance(parent.id).root.transform;var child_before: Transform3D=rig.root.transform;var bones_before:=bone_state(rig)
		var pose: Dictionary=rig.sample(at)
		parent_exact=parent_exact and rig.evaluation_error.is_empty() and app.renderer.world_runtime.current_frame==24 and app.renderer.world_runtime.instance(parent.id).root.transform==parent_before and rig.root.transform==child_before and bone_state(rig)==bones_before
		if half%2==0:
			app.renderer.world_runtime.evaluate(int(at),false,"",app.video);parent_exact=parent_exact and rig.sample(at)==pose
			for target in track.segments[0].feet:parent_peak=maxf(parent_peak,rig.bone_transform(target.ids[2]).origin.distance_to(Model.Timeline.vector(target.position)))
	check(parent_exact and parent_peak<.0002,"read-only queries sample animated parent at requested time, not displayed time")
	world=app.current_world();world.objects[0].animation_clips[0].foot_contacts.segments[0].feet[1].position=[99999,99999,99999]
	check(app.restore_world(world).is_empty(),"valid but unreachable targets remain an explicit evaluation error")
	error=await app.export_movie(folder)
	check(not error.is_empty() and error.contains("Frame 0") and not FileAccess.file_exists(app.last_export_folder.path_join("movie.mp4")),"unreachable contact aborts the real exporter before an unconstrained movie is written")
	for label in ["pose-smoke/miku-project","source-smoke/source-project","sfm-smoke/project"]:
		var path:=ProjectSettings.globalize_path("res://output/"+label)
		if not FileAccess.file_exists(path.path_join("project.json")):print("SKIP private "+label);continue
		var loaded:=preload("res://src/storage.gd").load_project(path)
		var row:=preload("res://tests/world_test_support.gd").legacy_model(World.from_project(loaded).objects[-1]);row.id="contact-native";row.parent_id="";row.start_frame=0;row.pose_keys=[];row.pose={};row.draft_frame=0
		app.new_project();world=World.empty();world.objects=[row];app.restore_world(world);native_evaluation(app.renderer.world_runtime.instance(row.id),label)
	for name in ["AvatarSample_A.vrm","AvatarSample_Avrm0.vrm"]:
		var path: String=preload("res://tests/native_sample_paths.gd").vrm(name)
		if not FileAccess.file_exists(path):print("SKIP private "+name);continue
		var sha_before:=FileAccess.get_sha256(path);app.new_project();app.pose_editor.add_model(path)
		while app.source_import.pid>0:await process_frame
		for node in app.get_children():
			if node is AcceptDialog and node.title=="Imported with limitations":node.hide();node.queue_free()
		await settled();native_evaluation(app.renderer.active_model(),name);check(FileAccess.get_sha256(path)==sha_before,"raw VRM source unchanged: "+name)
	var result:={"checks":checks,"failures":failures,"peak_error":peak,"samples":98,"evaluation_probe_ms":evaluation_probe_ms,"scenario_ms":float(Time.get_ticks_usec()-began)/1000.,"folder":folder,"movie":movie,"raw_position_delta":raw_position_delta,"visible_samples":visible,"native_reports":native_reports,"parent_peak_error":parent_peak}
	var file:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close();app.free();await settled();print("CONTACT_ANIMATION "+JSON.stringify(result));quit(0 if failures==0 else 1)
