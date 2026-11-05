extends SceneTree
const Model=preload("res://src/model.gd")
const World=preload("res://src/world_document.gd")
const Correction=preload("res://src/contact_correction.gd")
const Ranges=Correction.Ranges
const Contacts=Correction.Contacts
const T=Model.Timeline
var app
var dialog
var folder: String
var checks:=0
var failures:=0
var natives:={}
func _initialize() -> void:
	create_timer(150).timeout.connect(func():push_error("Contact correction watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settled() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func rig() -> RefCounted:return app.renderer.active_model()
func segment(data: Dictionary,at: float) -> Dictionary:return Contacts.active(data.animation_clips,at)
func root_value(y: float) -> Dictionary:return {"position":[0,y,0],"rotation_xyzw":[0,0,0,1],"scale":1.}
func open(at: int,last: int,foot:=0) -> void:
	app.set_frame(at);dialog.control.pressed.emit();await settled();dialog.end_frame.value=last;dialog.foot_choice.select(foot);dialog.foot_choice.item_selected.emit(foot);await settled()
func endpoint_error(actor: RefCounted,at: int) -> float:
	actor.apply(at,false,false,app.video);var peak:=0.
	for foot in segment(actor.data,at).get("feet",[]):peak=maxf(peak,actor.bone_transform(foot.ids[2]).origin.distance_to(T.vector(foot.position)))
	return peak
func native_correct(actor: RefCounted,label: String) -> void:
	actor.apply(0,false,false,app.video);var sha:=FileAccess.get_sha256(actor.data.source);var metadata: Dictionary=actor.data.metadata.duplicate(true);var order: Array=actor.order.duplicate()
	var captured:=Contacts.capture(actor,0,25,"native-correction")
	check(not captured.has("error"),"native correction captures supported legs: "+label)
	if captured.has("error"):return
	var foot: Dictionary=captured.segments[0].feet[0];var hip: Vector3=actor.bone_transform(foot.ids[0]).origin;var end:=T.vector(foot.position);var axis: Vector3=(end-hip).normalized();var length: float=hip.distance_to(end)
	var sideways:=Vector3.RIGHT if absf(axis.dot(Vector3.RIGHT))<.8 else Vector3.UP;sideways=(sideways-axis*sideways.dot(axis)).normalized()
	var target:=end-axis*length*.03;var pole:=hip+sideways*length
	var original: Dictionary=actor.data.duplicate(true);var planted:=Ranges.edit(original,0,25,captured.segments[0],48)
	var corrected:=Correction.edit(planted.data,0,25,0,{"position":[target.x,target.y,target.z],"pole":[pole.x,pole.y,pole.z],"flip_bend":true},48)
	if corrected.has("error"):check(false,label+": "+corrected.error);return
	app.renderer.world_runtime.restore_instance(actor.data.id,corrected.data);var before: Dictionary=actor.data.duplicate(true);var poses:=[];var exact:=true;var peak:=0.
	for half in range(49):
		poses.append(actor.sample(float(half)/2));exact=exact and actor.evaluation_error.is_empty()
		if half%2==0:peak=maxf(peak,endpoint_error(actor,half/2))
	for half in range(48,-1,-1):exact=exact and actor.sample(float(half)/2)==poses[half]
	check(exact and peak<.0002 and actor.data==before and actor.order==order and actor.data.metadata==metadata and FileAccess.get_sha256(actor.data.source)==sha,"native corrected pin/pole/reversed knee is stable with original IDs, source and provenance: "+label)
	natives[label]={"peak_error":peak,"samples":98}
func run() -> void:
	folder=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder)
	var asset:=folder.path_join("figure.glb");preload("res://src/tutorial_assets.gd").figure(asset);var sha:=FileAccess.get_sha256(asset)
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache");dialog=app.pose_editor.contacts;app.pose_editor.add_model(asset)
	for at in [0,24]:
		var before: Dictionary=rig().data.duplicate(true);rig().put_pose_key({"frame":at,"pose":{},"transform":root_value(0. if at==0 else -.15),"authored_channels":["@root"],"interpolation":"ease"},48,false,before)
	app.set_frame(0);var capture:=Contacts.capture(rig(),0,49,"original");var planted:=Ranges.edit(rig().data,0,49,capture.segments[0],48);app.renderer.world_runtime.restore_instance(rig().data.id,planted.data)
	var original: Dictionary=rig().data.duplicate(true);var shots: Array=app.keys.duplicate(true);var history: int=app.history.size();var body:=Model.new();body.data=original
	await open(6,18);check(dialog.correction_box.visible and not dialog.precise.visible and app.history.size()==history,"Simple shows foot nudges and hides precise fields without authoring")
	var old: Dictionary=segment(original,6);var expected: Vector3=T.vector(old.feet[0].position)+app.renderer.camera.global_basis.y*dialog.step.value;dialog.nudge_buttons[1].pressed.emit();await settled();var corrected: Dictionary=rig().data.duplicate(true)
	check(not dialog.window.visible and app.history.size()==history+1 and T.vector(segment(corrected,6).feet[0].position)==expected,"actual Simple Up moves the left foot target relative to the view in one Undo")
	check(segment(corrected,6).feet[1]==old.feet[1] and segment(corrected,5).feet==segment(original,5).feet and segment(corrected,19).feet==segment(original,19).feet,"single-foot correction retains the other foot and both outside boundaries")
	var exact:=true
	for half in range(97):exact=exact and rig().sample_body(float(half)/2)==body.sample_body(float(half)/2) and rig().sample_transform(float(half)/2)==body.sample_transform(float(half)/2)
	check(exact and app.keys==shots,"corrected contacts preserve every half-frame body curve and explicit shot key")
	app.undo();check(rig().data==original,"correction Undo restores the exact original descriptor")
	app.redo();check(rig().data==corrected,"correction Redo restores the exact changed pin")
	app.set_advanced(true);await open(12,18);history=app.history.size();dialog.apply_target.pressed.emit()
	check(dialog.window.visible and rig().data==corrected and app.history.size()==history and dialog.note.text.contains("unchanged"),"unchanged Advanced Apply preserves raw target precision and creates no history")
	dialog.position_fields[1].value+=.005;dialog.rotation_fields[1].value=15.;dialog.use_pole.button_pressed=true;dialog.apply_target.pressed.emit();await settled();var precise: Dictionary=rig().data.duplicate(true);var foot: Dictionary=segment(precise,12).feet[0]
	check(foot.has("pole") and absf(T.quaternion(foot.rotation_xyzw).angle_to(Quaternion.from_euler(Vector3(0,deg_to_rad(15),0))))<.000001 and endpoint_error(rig(),12)<.0002,"Advanced applies exact world position/orientation and an explicit knee target")
	var descriptor:=Contacts.track([segment(precise,12)]);check(descriptor.format==Contacts.CORRECTION_FORMAT and Contacts.validate(descriptor).is_empty(),"new knee settings explicitly version the contact descriptor")
	descriptor.format=Contacts.FORMAT;check(not Contacts.validate(descriptor).is_empty(),"old descriptor version cannot silently carry ignored knee settings")
	check(not Contacts.validate(Contacts.track([{}])).is_empty(),"descriptor version selection leaves malformed data for explicit validation")
	var knee_before: Vector3=rig().bone_transform(foot.ids[1]).origin;await open(12,18);dialog.reverse_button.pressed.emit();await settled();var reversed: Dictionary=rig().data.duplicate(true);endpoint_error(rig(),12)
	check(segment(reversed,12).feet[0].flip_bend and knee_before.distance_to(rig().bone_transform(foot.ids[1]).origin)>.001 and endpoint_error(rig(),12)<.0002,"Simple knee reversal changes the bend while preserving the planted endpoint")
	await open(12,18);history=app.history.size();dialog.position_fields[1].value=1000.;dialog.apply_target.pressed.emit()
	check(dialog.window.visible and rig().data==reversed and app.history.size()==history and dialog.note.text.contains("Frame"),"unreachable exact target refuses without partial correction or history")
	dialog.window.hide();await open(12,18);dialog.apply_correction({"pole":segment(reversed,12).feet[0].position})
	check(rig().data==reversed and app.history.size()==history and dialog.note.text.contains("knee target"),"a pole on the leg line refuses with useful direction guidance")
	dialog.window.hide();await open(12,18);app.set_frame(13);dialog.reverse_button.pressed.emit();check(rig().data==reversed and dialog.note.text.contains("changed"),"stale correction frame cannot author the old range")
	dialog.window.hide();await open(12,18);app.physics_editor.queue_import_start(rig().data.id,true,false);dialog.reverse_button.pressed.emit();check(rig().data==reversed and app.physics_editor.import_starts.has(rig().data.id),"pending physics defers correction without consuming its ticket");app.physics_editor.clear();dialog.window.hide()
	# Correct left across a changed right-foot interval and a deliberate release gap.
	var right: Vector3=T.vector(old.feet[1].position)+Vector3.UP*.01
	var varied:=Correction.edit(original,10,13,1,{"position":[right.x,right.y,right.z]},48);var release:=Ranges.edit(varied.data,14,16,{},48)
	var left: Vector3=T.vector(old.feet[0].position)+Vector3.UP*.02;var mixed:=Correction.edit(release.data,6,19,0,{"position":[left.x,left.y,left.z]},48)
	check(not mixed.has("error") and segment(mixed.data,14).is_empty() and segment(mixed.data,15).is_empty() and T.vector(segment(mixed.data,11).feet[1].position)==right and segment(mixed.data,8).feet[1]==old.feet[1] and segment(mixed.data,17).feet[1]==old.feet[1],"correcting one foot across blocks preserves the other foot's changing targets and explicit release gap")
	var bad:=Correction.edit(original,0,4,0,{"pole":[0,NAN,0]},48);check(bad.has("error") and Correction.edit(original,0,4,0,{"flip_bend":1},48).has("error"),"nonfinite pole and non-boolean bend fields reject before installation")
	var piece: Dictionary=reversed.animation_clips.filter(func(item):return item.start==12)[0];var destination:=Transform3D(Basis(Quaternion(Vector3.UP,.3)).scaled(Vector3.ONE*1.2),Vector3(2,1,0));var moved:=preload("res://src/contact_clipboard.gd").reanchor(piece,Transform3D.IDENTITY,destination)
	var mapped: Dictionary=moved.piece.foot_contacts.segments.filter(func(item):return item.has("feet") and item.feet[0].has("pole"))[0]
	check(T.vector(mapped.feet[0].pole).distance_to(destination*T.vector(foot.pole))<.000001 and mapped.feet[0].flip_bend,"clipboard reanchoring also maps world knee targets and preserves bend choices")
	app.set_frame(12);app.pose_editor.frame_model();await settled();await open(12,18);dialog.window.get_texture().get_image().save_png(folder.path_join("advanced-window.png"));check(dialog.window.size.x<=root.size.x and dialog.window.size.y<=root.size.y and dialog.apply_target.is_visible_in_tree(),"Advanced correction controls fit the actual window with Apply reachable")
	check(Rect2(Vector2.ZERO,Vector2(dialog.window.size)).encloses(dialog.apply_target.get_global_rect()),"Advanced Apply remains inside the window without scrolling to the last field")
	dialog.window.hide();app.set_advanced(false);await open(12,18);dialog.window.get_texture().get_image().save_png(folder.path_join("simple-window.png"));dialog.window.hide()
	app.set_frame(0);app.create_cel(false);preload("res://src/drawing.gd").stroke(app.layers[1].cels[0].image,Vector2(40,40),Vector2(140,40),8,Color.CYAN,false);app.changed();app.set_frame(12);app.keys=[T.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,app.renderer.camera.fov)]
	var expected_pose: Dictionary=rig().sample(12);var id: String=rig().data.id;var has_path:=folder.path_join("corrected-feet.has");app.has_project.save_file(has_path,"packed")
	while app.has_project.pid>0:await process_frame
	app.new_project();app.has_project.open_file(has_path)
	while app.has_project.pid>0:await process_frame
	app.world_selection.select_entity(id);app.set_frame(12);check(rig().sample(12)==expected_pose and segment(rig().data,12).feet[0].has("pole") and segment(rig().data,12).feet[0].flip_bend,"normal packed HAS reopens exact corrected FK, world pole and knee direction")
	var reference: Image=await app.renderer.capture(app.keys,app.layers,12,true);reference.save_png(folder.path_join("corrected-frame.png"));var error: String=await app.export_movie(folder);var movie: String=app.last_export_folder.path_join("movie.mp4")
	check(error.is_empty() and reference.get_data()==Image.load_from_file(app.last_export_folder.path_join("frame_000013.png")).get_data(),"corrected feet, knee direction and independent paint match reopened preview and actual MP4")
	check(FileAccess.get_sha256(asset)==sha,"original authored model bytes remain unchanged")
	for label in ["pose-smoke/miku-project","source-smoke/source-project","sfm-smoke/project"]:
		var path:=ProjectSettings.globalize_path("res://output/"+label)
		if not FileAccess.file_exists(path.path_join("project.json")):print("SKIP private "+label);continue
		var loaded:=preload("res://src/storage.gd").load_project(path);var row:=preload("res://tests/world_test_support.gd").legacy_model(World.from_project(loaded).objects[-1]);row.id="corrected-native";row.parent_id="";row.start_frame=0;row.pose_keys=[];row.pose={};row.draft_frame=0
		app.new_project();var world:=World.empty();world.objects=[row];app.restore_world(world);native_correct(app.renderer.world_runtime.instance(row.id),label)
	for name in ["AvatarSample_A.vrm","AvatarSample_Avrm0.vrm"]:
		var path: String=preload("res://tests/native_sample_paths.gd").vrm(name)
		if not FileAccess.file_exists(path):print("SKIP private "+name);continue
		var native_sha:=FileAccess.get_sha256(path);app.new_project();app.pose_editor.add_model(path)
		while app.source_import.pid>0:await process_frame
		for node in app.get_children():
			if node is AcceptDialog and node.title=="Imported with limitations":node.hide();node.queue_free()
		await settled();native_correct(rig(),name);check(FileAccess.get_sha256(path)==native_sha,"raw native VRM stays unchanged: "+name)
	var result:={"checks":checks,"failures":failures,"folder":folder,"movie":movie,"native_reports":natives};var file:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close();app.free();await settled();print("CONTACT_CORRECTION "+JSON.stringify(result));quit(0 if failures==0 else 1)
