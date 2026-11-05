extends SceneTree
const Model=preload("res://src/model.gd")
const Timeline=preload("res://src/timeline.gd")
const Drawing=preload("res://src/drawing.gd")
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(110).timeout.connect(func():push_error("Patch watchdog expired");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settled() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func wait_job(job) -> void:
	while job.pid>0:await process_frame
	await settled()
func indices_equal(values: Array,first: int,last: int) -> bool:
	if values.size()!=last-first:return false
	for i in range(values.size()):
		if float(values[i])!=float(first+i):return false
	return true
func close_pixels(a: Image,b: Image) -> bool:
	var aa:=a.get_data();var bb:=b.get_data();var changed:=0;var total:=0
	for i in range(aa.size()):
		if aa[i]!=bb[i]:changed+=1;total+=absi(int(aa[i])-int(bb[i]))
	return changed<=384 and float(total)/aa.size()<.002
func viewport_point(app,point: Vector2) -> Vector2:
	var rect: Rect2=app.canvas.image_rect()
	return app.canvas.get_global_transform_with_canvas()*(rect.position+point/Vector2(1920,1080)*rect.size)
func button(app,point: Vector2,pressed: bool) -> void:
	var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.pressed=pressed;event.button_mask=MOUSE_BUTTON_MASK_LEFT if pressed else 0;event.position=viewport_point(app,point);event.global_position=event.position
	app.get_viewport().push_input(event,true)
func motion(app,point: Vector2) -> void:
	var event:=InputEventMouseMotion.new();event.button_mask=MOUSE_BUTTON_MASK_LEFT;event.position=viewport_point(app,point);event.global_position=event.position;app.get_viewport().push_input(event,true)
func bounds(helper,indices: Array) -> Rect2:
	var lo:=Vector2(INF,INF);var hi:=Vector2(-INF,-INF)
	for index in indices:
		var p: Vector2=helper.projected_vertices[index];lo=lo.min(p);hi=hi.max(p)
	return Rect2(lo-Vector2(3,3),hi-lo+Vector2(6,6))
func choose(app,indices: Array,operation:=0) -> void:
	var helper=app.physics_editor.helper_editor;helper.draw_preview();var rect:=bounds(helper,indices);helper.patch_operation.select(operation)
	button(app,rect.position,true);await settled();motion(app,rect.end);button(app,rect.end,false);await wait_job(helper)
func run() -> void:
	var args:=OS.get_cmdline_user_args();var source: String=args[0];var folder: String=args[1];var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("patch-recovery");root.add_child(app);await settled();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("patch-cache")
	app.append_object(Model.definition(source),"model");var actor: RefCounted=app.renderer.active_model();var id: String=actor.data.id;var sha: String=actor.data.sha256;var before: Dictionary=actor.data.duplicate(true);var history: int=app.history.size()
	Drawing.insert(app.layers[1],0,48,Drawing.blank(1920,1080));Drawing.cel_at(app.layers[1],0).image.set_pixel(80,80,Color.CYAN);var paint: PackedByteArray=Drawing.cel_at(app.layers[1],0).image.get_data()
	app.renderer.camera.position=Vector3(0,1.2,4);app.renderer.camera.look_at(Vector3(0,1.1,0));app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,48)];var shots: Array=app.keys.duplicate(true)
	var helper=app.physics_editor.helper_editor;helper.button.pressed.emit();await wait_job(helper);helper.patch_toggle.button_pressed=true;await settled()
	check(not helper.preview.is_empty() and helper.preview.source_vertices.size()==20,"patch review has exact source vertices for the selected connected part")
	if helper.preview.is_empty():app.free();quit(1);return
	app.canvas.zoom=1.15;app.canvas.pan=Vector2(12,-8);app.canvas.queue_redraw();await settled()
	app.mode.select(0);app.change_mode(0)
	await choose(app,range(8,20))
	check(helper.request.get("vertex_mask",[])==range(8,20) and helper.preview.selected_vertices.size()==12 and not helper.apply_button.disabled,"routed canvas box selects the lower patch through zoom and pan")
	check(helper.preview.region.attachment_method=="pinned cut boundary" and int(helper.preview.region.attachment_vertices)==2,"review pins the actual connection to the surrounding surface")
	check(actor.data==before and app.history.size()==history and app.keys==shots and Drawing.cel_at(app.layers[1],0).image.get_data()==paint,"patch selection edits no model, history, camera keys or independent drawing")
	await choose(app,[6,7],1);check(helper.request.vertex_mask==range(6,20) and not helper.apply_button.disabled,"Add to patch grows the connected selection")
	await choose(app,[6,7],2);check(helper.request.vertex_mask==range(8,20) and not helper.apply_button.disabled,"Remove from patch restores the selected garment boundary")
	await choose(app,[0,1],1);check(helper.apply_button.disabled and helper.info.text.contains("connected"),"disconnected patch refuses Apply while retaining the source")
	await choose(app,range(8,20));check(not helper.apply_button.disabled,"a corrected connected patch recovers after a refused selection")
	var mask: Array=helper.request.vertex_mask.duplicate();var rect:=bounds(helper,[4,5]);button(app,rect.position,true);await settled();motion(app,rect.end)
	var escape:=InputEventKey.new();escape.keycode=KEY_ESCAPE;escape.pressed=true;app.get_viewport().push_input(escape,true);await settled();escape.pressed=false;app.get_viewport().push_input(escape,true);button(app,rect.end,false)
	check(not helper.box_dragging and not app.canvas.review_box_visible and helper.request.vertex_mask==mask,"Escape cancels a routed patch drag without changing the selection")
	button(app,rect.position,true);await settled();app._notification(Node.NOTIFICATION_WM_WINDOW_FOCUS_OUT);button(app,rect.end,false)
	check(not helper.box_dragging and helper.request.vertex_mask==mask,"focus loss cancels the patch rectangle safely")
	var ctrl:=InputEventMouseButton.new();ctrl.button_index=MOUSE_BUTTON_LEFT;ctrl.pressed=true;ctrl.ctrl_pressed=true
	check(not helper.patch_pointer(ctrl,rect.position),"Ctrl-left remains available for free camera movement")
	var navigation_click:=InputEventMouseButton.new();navigation_click.button_index=MOUSE_BUTTON_LEFT;navigation_click.pressed=true
	app.navigating=true;check(not helper.patch_pointer(navigation_click,rect.position),"patch tool does not interrupt an existing navigation gesture");app.navigating=false
	var baseline: Image=await app.renderer.capture(app.keys,app.layers,0,true);helper.window.get_texture().get_image().save_png(folder.path_join("patch-window.png"));root.get_texture().get_image().save_png(folder.path_join("patch-editor.png"))
	var cut_y:=int(helper.projected_vertices[8].y)-4
	helper.apply_button.pressed.emit();await wait_job(helper);actor=app.renderer.world_runtime.instance(id)
	check(actor.order.size()==6 and indices_equal(actor.data.metadata.generated_helpers.region.vertex_mask,8,20) and app.history.size()==history+1,"Apply installs only the reviewed patch as one immutable revision")
	var neutral: Image=await app.renderer.capture(app.keys,app.layers,0,true);check(close_pixels(baseline,neutral),"new patch skin retains the original neutral appearance within the existing rebuild bound");baseline=neutral
	check(not app.canvas.review_pointer.is_valid(),"closing review removes its canvas input interceptor")
	var def: Dictionary=actor.root.get_meta("has_secondary_rig");app.world_selection.select_entity(id,false);app.mode.select(2);app.change_mode(2);var editor=app.pose_editor;editor.selected=def.chains[0].joints[0].binding.id;editor.operation.select(0);editor.refresh_values();editor.fields[2].value=30;editor.apply_numeric();await settled()
	var bent: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	check(bent.get_data()!=baseline.get_data(),"a generated patch joint visibly deforms the chosen surface")
	check(bent.get_region(Rect2i(0,0,1920,cut_y)).get_data()==baseline.get_region(Rect2i(0,0,1920,cut_y)).get_data(),"surrounding upper surface keeps its actual rendered pixels")
	app.undo();check((await app.renderer.capture(app.keys,app.layers,0,true)).get_data()==baseline.get_data(),"normal pose Undo restores patch deformation exactly")
	app.undo();actor=app.renderer.world_runtime.instance(id);check(actor.data.sha256==sha and actor.order.size()==2,"asset Undo restores the original unsplit mesh")
	app.redo();app.world_selection.select_entity(id,false);await settled();helper.button.pressed.emit();await wait_job(helper)
	check(helper.parts.is_item_disabled(1),"partly rigged connected component remains protected in whole-part mode")
	helper.patch_toggle.button_pressed=true;helper.parts.select(1);helper.parts.item_selected.emit(1);await wait_job(helper)
	check(not helper.preview.can_apply and helper.apply_button.disabled and not helper.parts.is_item_disabled(1),"patch mode can inspect a protected component without allowing whole-part overwrite")
	await choose(app,range(10,20));check(helper.apply_button.disabled and not helper.preview.can_apply,"a patch overlapping earlier spring weights stays protected")
	await choose(app,range(8));check(not helper.apply_button.disabled,"a separate unrigged patch remains editable in the same connected mesh")
	helper.apply_button.pressed.emit();await wait_job(helper);actor=app.renderer.world_runtime.instance(id)
	check(actor.root.get_meta("has_secondary_rig").chains.size()==2 and actor.data.metadata.generated_helper_history.size()==2,"two disjoint patches coexist on one original connected surface")
	var project:=folder.path_join("patches.has");app.has_project.save_file(project,"packed");await wait_job(app.has_project);app.new_project();app.has_project.open_file(project);await wait_job(app.has_project);actor=app.renderer.world_runtime.instance(id)
	check(actor!=null and actor.root.get_meta("has_secondary_rig").chains.size()==2 and indices_equal(actor.data.metadata.generated_helper_history[0].region.vertex_mask,8,20),"packed HAS retains both patch rigs and exact reviewed mask provenance")
	check(Drawing.cel_at(app.layers[1],0).image.get_data()==paint and JSON.stringify(app.keys)==JSON.stringify(JSON.parse_string(JSON.stringify(shots,"",true,true))) and FileAccess.get_sha256(source)==sha,"patch authoring and reopening preserve drawings, camera and original source")
	var movie:=""
	if args.size()>2:
		app.physics_editor.fan_editor.add_fan();var fan: RefCounted=app.renderer.active_model();fan.data.position=[0,1.2,-1.5];fan.data.rotation_xyzw=[0,0,0,1];fan.data.metadata.airflow.speed=10;fan.apply(0);app.world_selection.select_entity(id,false)
		app.physics_editor.hair_toggle.button_pressed=true
		while app.physics_editor.pending.has(id):await process_frame
		check(app.physics_editor.active(id),"normal hair motion accepts two patches within one connected mesh")
		if not app.physics_editor.active(id):app.free();quit(1);return
		var record=app.physics_editor.recording;record.scope.select(0);record.button.pressed.emit()
		while record.active:await process_frame
		actor=app.renderer.world_runtime.instance(id);check(record.last_error.is_empty() and actor.authored_keys().size()==49,"ordinary Local Record captures weighted patch motion")
		var movement: Dictionary=actor.sample(24);var both_moved:=true
		for chain in actor.root.get_meta("has_secondary_rig").chains:
			var amount:=0.0
			for joint in chain.joints:amount=maxf(amount,Timeline.quaternion(movement.get(joint.binding.id,Model.identity()).rotation_xyzw).angle_to(Quaternion.IDENTITY))
			both_moved=both_moved and amount>.005
		check(both_moved,"both disjoint patches have measured recorded wind response")
		check(app.import_audio(args[2]).is_empty(),"patch animation keeps independent WAV audio")
		app.audio_start.value=24;app.audio_gain.value=-6;app.apply_audio_settings();app.set_frame(24)
		var recorded_project:=folder.path_join("recorded-patches.has");app.has_project.save_file(recorded_project,"packed");await wait_job(app.has_project);app.new_project();app.has_project.open_file(recorded_project);await wait_job(app.has_project)
		actor=app.renderer.world_runtime.instance(id);check(JSON.stringify(actor.sample(24))==JSON.stringify(movement),"recorded patch motion survives portable HAS reopening")
		var reference: Image=await app.renderer.capture(app.keys,app.layers,24,true);app.set_frame(5);app.set_frame(40);app.set_frame(24)
		check((await app.renderer.capture(app.keys,app.layers,24,true)).get_data()==reference.get_data(),"recorded patch motion seeks deterministically")
		var error: String=await app.export_movie(folder);check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000025.png")).get_data()==reference.get_data(),"recorded patch motion exports with exact reopened preview pixels");movie=app.last_export_folder.path_join("movie.mp4")
		app.world_selection.select_entity(id,false);helper.button.pressed.emit();var worker: int=helper.pid;app.audio_player.volume_db=-80;app.toggle_play();await settled();app.stop()
		check(not is_instance_valid(helper.window) and not app.canvas.review_pointer.is_valid() and not OS.is_process_running(worker),"starting playback cancels review and its owned worker")
		app.world_selection.select_entity(id,false);helper.button.pressed.emit();await wait_job(helper);var current_sha: String=app.renderer.active_model().data.sha256
		app.physics_editor.hair_toggle.button_pressed=true
		while app.physics_editor.pending.has(id):await process_frame
		await settled();check(not is_instance_valid(helper.window) and app.physics_editor.active(id) and app.renderer.active_model().data.sha256==current_sha,"starting live motion closes stale review while keeping the current asset")
		app.physics_editor.hair_toggle.button_pressed=false
	var result:={"checks":checks,"failures":failures,"folder":folder,"movie":movie};var f:=FileAccess.open(folder.path_join("patch-result.json"),FileAccess.WRITE);f.store_string(JSON.stringify(result));f.close();print("HELPER_PATCH "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
