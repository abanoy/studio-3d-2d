extends "res://tests/contact_transform_smoke.gd"
var target
func open_target(kind: String="position",foot:=0) -> void:
	app.set_frame(12);app.world_selection.select_entity("child");app.pose_editor.frame_model();app.pose_editor.contacts.control.pressed.emit();await settled()
	var dialog=app.pose_editor.contacts;dialog.end_frame.value=18;dialog.foot_choice.select(foot);dialog.foot_choice.item_selected.emit(foot)
	(dialog.drag_foot if kind=="position" else dialog.drag_knee).pressed.emit();await settled();target=dialog.viewport
func press_at(point: Vector2) -> void:
	var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.pressed=true;app.canvas_input(event,point)
func move_global(point: Vector2) -> void:
	var event:=InputEventMouseMotion.new();var rect: Rect2=app.canvas.image_rect();event.position=app.canvas.get_global_transform()*(rect.position+point/Vector2(1920,1080)*rect.size);app._input(event)
func release_global() -> void:
	var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.pressed=false;app._input(event)
func escape() -> void:
	var event:=InputEventKey.new();event.keycode=KEY_ESCAPE;event.pressed=true;app._input(event)
func target_error() -> float:
	var rig:=actor("child");var point: Vector3=rig.bone_transform(Contacts.active(rig.data.animation_clips,12).feet[target.foot_index].ids[2]).origin
	return point.distance_to(target.accepted)
func viewport_case(plan: Dictionary) -> Dictionary:
	var first_check:=checks;var first_failure:=failures;setup(plan);await open_target();var rig:=actor("child");var original: Dictionary=rig.data.duplicate(true);var history: int=app.history.size();var sample: Dictionary=rig.sample(12);var shots: Array=app.keys.duplicate(true);var view: Dictionary=app.renderer.view_state();var peer: Dictionary=actor("peer").data.duplicate(true)
	check(target.active and target.target_visible and target.handles.size()==3 and not app.pose_editor.contacts.window.visible,"actual foot button opens world axes and visible range: "+plan.name)
	check(target.panel.is_visible_in_tree() and app.canvas.get_global_rect().encloses(target.panel.get_global_rect()) and target.hint.text.contains("12–18"),"range and Done remain enclosed in the actual viewport: "+plan.name)
	var point: Vector2=target.center;press_at(point);check(target.dragging and app.pose_editor.dragging,"actual center press begins camera-plane target gesture: "+plan.name)
	move_global(point+Vector2(0,-3));await settled();var desired: Vector3=target.accepted;var preview: Dictionary=target.candidate.duplicate(true)
	check(desired!=target.drag_origin and target_error()<.0002 and not preview.is_empty(),"global canvas-mapped motion visibly solves the foot preview: "+plan.name)
	check(rig.data==original and rig.sample(12)==sample and app.history.size()==history and rig.preview_frame==12,"preview never changes authored data, read-only samples or Undo: "+plan.name)
	move_global(point+Vector2(0,-100000));check(target.accepted==desired and target.candidate==preview and app.status.text.contains("Last valid"),"unreachable motion keeps last valid preview and useful feedback: "+plan.name)
	escape();await settled();check(target.active and not target.dragging and not app.pose_editor.dragging and rig.data==original and rig.preview_frame==-1 and app.history.size()==history,"Escape cancels only the preview with exact authored state: "+plan.name)
	point=target.center;press_at(point);move_global(point+Vector2(0,-3));move_global(point);release_global();check(rig.data==original and app.history.size()==history and rig.preview_frame==-1,"returning to the origin creates no key or history: "+plan.name)
	await settled();point=target.center;press_at(point);move_global(point+Vector2(0,-3));desired=target.accepted;release_global();await settled();var edited: Dictionary=rig.data.duplicate(true)
	check(edited!=original and app.history.size()==history+1 and peak()<.0002 and rig.preview_frame==-1,"release commits one correction and clears transient pose: "+plan.name)
	var changed: Dictionary=Contacts.active(edited.animation_clips,12);var old: Dictionary=Contacts.active(original.animation_clips,12)
	check(Model.Timeline.vector(changed.feet[0].position)==desired and changed.feet[1]==old.feet[1] and Contacts.active(edited.animation_clips,11).feet==old.feet and Contacts.active(edited.animation_clips,19).feet==old.feet,"drag changes only selected foot in inclusive12–18: "+plan.name)
	var body:=Model.new();body.data=original;var exact:=true
	for half in range(97):exact=exact and rig.sample_body(float(half)/2)==body.sample_body(float(half)/2) and rig.sample_transform(float(half)/2)==body.sample_transform(float(half)/2)
	check(exact and app.keys==shots and actor("peer").data==peer and app.renderer.view_state()==view,"drag preserves every body half-frame, peer and explicit camera: "+plan.name)
	target.stop();app.undo();check(rig.data==original,"target Undo restores exact native contact data: "+plan.name);app.redo();check(rig.data==edited,"target Redo restores exact corrected range: "+plan.name)
	await open_target("pole");history=app.history.size();original=rig.data.duplicate(true);point=target.center;press_at(point);move_global(point+Vector2(3,0));var pole: Vector3=target.accepted;release_global();await settled()
	check(rig.data!=original and app.history.size()==history+1 and Model.Timeline.vector(Contacts.active(rig.data.animation_clips,12).feet[0].pole)==pole and peak()<.0002,"Advanced knee target uses same one-Undo drag without losing foot pins: "+plan.name)
	target.stop();app.undo();check(rig.data==original,"knee-target Undo restores exact original pole: "+plan.name)
	await open_target();history=app.history.size();original=rig.data.duplicate(true);var longest: Dictionary=target.handles[0]
	for handle in target.handles:
		if handle.points[0].distance_to(handle.points[1])>longest.points[0].distance_to(longest.points[1]):longest=handle
	point=longest.points[0].lerp(longest.points[1],.7);press_at(point)
	check(target.dragging and not target.plane and target.drag_axis==longest.axis,"world-axis handle selects its actual constrained axis: "+plan.name)
	var direction: Vector2=target.screen_axis.normalized();move_global(point-direction*2);check(target.dragging and target.accepted!=target.drag_origin,"axis gesture previews a reachable constrained target: "+plan.name)
	escape();check(rig.data==original and app.history.size()==history,"axis Escape cancels without authoring: "+plan.name)
	var ctrl:=InputEventMouseButton.new();ctrl.button_index=MOUSE_BUTTON_LEFT;ctrl.pressed=true;ctrl.ctrl_pressed=true;app.canvas_input(ctrl,target.center)
	check(not target.dragging and app.navigating,"Ctrl-left retains camera navigation priority over target mode: "+plan.name);app.release_mouse();await settled()
	if plan.name=="AvatarSample_Avrm0.vrm":root.get_texture().get_image().save_png(folder.path_join("viewport-target.png"))
	await open_target("position",1);check(target.foot_index==1,"right-foot selector directs the viewport target: "+plan.name);point=target.center;press_at(point);move_global(point+Vector2(0,-2));escape();escape();check(not target.active and not target.dragging,"second Escape exits target mode: "+plan.name)
	await open_target();original=rig.data.duplicate(true);history=app.history.size();app.mode.select(0);app.change_mode(0);await settled()
	check(not target.active and not target.panel.visible and rig.data==original and app.history.size()==history,"switching to Draw closes idle target controls without an edit: "+plan.name)
	await open_target();app.home.open_home();await settled();check(not target.active and not target.panel.visible and app.home.visible,"Home closes target controls rather than reviving an old range on return: "+plan.name);app.home.hide()
	await open_target();original=rig.data.duplicate(true);history=app.history.size();point=target.center;press_at(point);move_global(point+Vector2(0,-2));app.physics_editor.queue_import_start("child",true,false);var ticket: Dictionary=app.physics_editor.import_starts.duplicate(true);move_global(point+Vector2(0,-3))
	check(not target.active and not target.dragging and not app.pose_editor.dragging and rig.preview_frame==-1 and rig.data==original and app.history.size()==history and app.physics_editor.import_starts==ticket,"pending physics cancels only the target preview and preserves its startup ticket: "+plan.name);app.physics_editor.clear()
	await open_target();original=rig.data.duplicate(true);history=app.history.size();point=target.center;press_at(point);move_global(point+Vector2(0,-2));app.set_frame(13);await settled()
	check(not target.active and not target.panel.visible and not target.dragging and rig.preview_frame==-1 and app.history.size()==history+1,"seeking finishes one correction at its original frame and closes the old range: "+plan.name)
	app.undo();check(rig.data==original,"seek-boundary Undo restores exact original target: "+plan.name)
	await open_target();original=rig.data.duplicate(true);history=app.history.size();var foot: Dictionary=Contacts.active(original.animation_clips,12).feet[0];var hip: Vector3=rig.bone_transform(foot.ids[0]).origin;var knee: Vector3=rig.bone_transform(foot.ids[1]).origin;var end: Vector3=rig.bone_transform(foot.ids[2]).origin;var length: float=hip.distance_to(knee)+knee.distance_to(end)
	point=target.center;press_at(point);target.preview(hip+Vector3.UP*(length*.999))
	check(not target.candidate.is_empty() and target.candidate!=original and rig.data==original,"current-frame reachable target remains only a preview: "+plan.name)
	release_global();check(rig.data==original and app.history.size()==history and rig.preview_frame==-1 and app.status.text.contains("Frame"),"future-frame reach failure refuses the entire release without partial authoring: "+plan.name);target.stop()
	await open_target();original=rig.data.duplicate(true);history=app.history.size();foot=Contacts.active(original.animation_clips,12).feet[0];var baseline_end: Vector3=rig.bone_transform(foot.ids[2]).origin;point=target.center;press_at(point);move_global(point+Vector2(0,-3));await settled()
	check(rig.bone_transform(foot.ids[2]).origin.distance_to(baseline_end)>.0001,"actual visible preview exists before an unrelated layer edit: "+plan.name)
	app.layer_visibility.button_pressed=not app.layer_visibility.button_pressed;await settled()
	check(not target.active and not target.dragging and rig.preview_frame==-1 and rig.data==original and app.history.size()==history+1,"unrelated layer edit cancels only transient foot editing: "+plan.name)
	check(rig.bone_transform(foot.ids[2]).origin.distance_to(baseline_end)<.0002,"stale-preview cancellation immediately restores the visible authored foot: "+plan.name);app.undo()
	await open_target();point=target.center;press_at(point);move_global(point+Vector2(0,-3));var replacement: Dictionary=rig.sample(12);rig.preview_pose=replacement.duplicate(true);rig.preview_frame=12;app.layer_visibility.button_pressed=not app.layer_visibility.button_pressed;await settled()
	check(not target.active and rig.preview_frame==12 and rig.preview_pose==replacement,"stale target cleanup preserves a different preview owner's pose: "+plan.name)
	check(rig.bone_transform(foot.ids[2]).origin.distance_to(baseline_end)<.0002,"replacement preview remains visibly applied after target cleanup: "+plan.name);app.physics_editor.clear_previews();app.undo()
	return {"name":plan.name,"checks":checks-first_check,"failures":failures-first_failure,"preview_ms":target.last_preview_ms,"commit_ms":target.last_commit_ms}
func run() -> void:
	var args:=OS.get_cmdline_user_args();folder=args[0];DirAccess.make_dir_recursive_absolute(folder);empty=folder.path_join("empty.glb");preload("res://src/scene3d.gd").make_empty(empty);app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache");app.has_project.open_file(args[1]);await job();var plans:=[];var hashes:={}
	for row in app.current_world().objects:
		if row.get("format")==Model.CONTACT_FORMAT:plans.append(row);hashes[row.source]=FileAccess.get_sha256(row.source)
	check(plans.size()==5,"five prepared native rigs available for viewport target acceptance")
	var reports:=[]
	for plan in plans:reports.append(await viewport_case(plan))
	# Start with unsplit contact blocks: changing an existing target can be smaller
	# than the original and is not an overflow fixture, even near the limit.
	setup(plans[-1]);var budget_rig:=actor("child");var budget_original: Dictionary=budget_rig.data.duplicate(true);var padding: int=1024*1024-app.pose_editor.contacts.metadata_bytes(app.current_world())-128;var padded: Dictionary=budget_original.duplicate(true);padded.metadata["viewport_budget_probe"]="x".repeat(padding);app.renderer.world_runtime.restore_instance("child",padded);await open_target();var budget_history: int=app.history.size()
	check(app.pose_editor.contacts.metadata_bytes(app.current_world())<=1024*1024,"capacity fixture fits before a viewport correction")
	var budget_foot: Dictionary=Contacts.active(padded.animation_clips,12).feet[0];var budget_position: Vector3=Model.Timeline.vector(budget_foot.position)+Vector3.UP*.001;var budget_change: Dictionary=app.pose_editor.contacts.Correction.edit(padded,12,19,0,{"position":[budget_position.x,budget_position.y,budget_position.z]},48);var budget_world: Dictionary=app.current_world()
	for i in range(budget_world.objects.size()):
		if budget_world.objects[i].id=="child":budget_world.objects[i]=budget_change.data
	check(app.pose_editor.contacts.metadata_bytes(budget_world)>1024*1024,"correction fixture actually exceeds the metadata cap before exercising refusal")
	var budget_point: Vector2=target.center;press_at(budget_point);move_global(budget_point+Vector2(0,-3));check(budget_rig.data==padded and target.candidate==padded and budget_rig.preview_frame==-1 and app.status.text.contains("metadata"),"oversized correction keeps original data and does not publish a partial preview")
	release_global();check(budget_rig.data==padded and app.history.size()==budget_history,"metadata refusal creates no Undo edit on release");target.stop();app.renderer.world_runtime.restore_instance("child",budget_original)
	app.set_frame(0);app.create_cel(false);preload("res://src/drawing.gd").stroke(app.layers[1].cels[0].image,Vector2(40,40),Vector2(130,40),8,Color.CYAN,false);app.changed();await open_target();var rig:=actor("child");var baseline: Dictionary=rig.data.duplicate(true);var history: int=app.history.size();var point: Vector2=target.center;press_at(point);move_global(point+Vector2(0,-3));var candidate: Dictionary=target.candidate.duplicate(true)
	check(candidate!=baseline and rig.data==baseline,"Save boundary begins with an actual uncommitted target preview")
	var path:=folder.path_join("viewport-contacts.has");app.has_project.save_file(path,"packed");await job()
	check(rig.data==candidate and not target.dragging and rig.preview_frame==-1 and app.history.size()==history+1 and FileAccess.file_exists(path),"normal packed Save finishes the target gesture once before taking its snapshot")
	var poses:=[]
	for half in range(97):poses.append(JSON.stringify(rig.sample(float(half)/2),"",true,true).sha256_text())
	var expected: Dictionary=World.portable(app.current_world());var layer_sha: String=app.layers[1].cels[0].image.get_data().hex_encode().sha256_text();app.set_frame(12);app.pose_editor.frame_model();app.keys=[Model.Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,app.renderer.camera.fov)];app.has_project.save_file(path,"packed");await job()
	var reference: Image=await app.renderer.capture(app.keys,app.layers,12,true);reference.save_png(folder.path_join("saved-frame.png"));var error: String=await app.export_movie(folder)
	check(error.is_empty() and reference.get_data()==Image.load_from_file(app.last_export_folder.path_join("frame_000013.png")).get_data(),"viewport-corrected native model and independent paint match actual MP4 frame12 exactly")
	var unchanged:=true
	for source in hashes:unchanged=unchanged and FileAccess.get_sha256(source)==hashes[source]
	check(unchanged,"all prepared native source bytes remain unchanged")
	var result:={"checks":checks,"failures":failures,"folder":folder,"native_reports":reports,"project":path,"expected_world":expected,"pose_hashes":poses,"layer_sha":layer_sha,"movie":app.last_export_folder.path_join("movie.mp4")};var file:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(result,"",true,true));file.close();app.free();await settled();print("CONTACT_VIEWPORT "+JSON.stringify({"checks":checks,"failures":failures,"folder":folder}));quit(0 if failures==0 else 1)
