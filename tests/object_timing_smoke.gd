extends SceneTree
const Support=preload("res://tests/world_test_support.gd")
const SceneIO=preload("res://src/scene3d.gd")
const Model=preload("res://src/model.gd")
const Timing=preload("res://src/object_timing.gd")
const Timeline=preload("res://src/timeline.gd")
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
const World=preload("res://src/world_document.gd")
var checks:=0
var failures:=0

func _initialize() -> void:
	create_timer(110).timeout.connect(func():push_error("Object timing watchdog expired");quit(2))
	call_deferred("run")

func check(ok: bool,text: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+text)
	if not ok:failures+=1

func settled() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw

func wait_job(job) -> void:
	while job.pid>0:await process_frame
	await settled()

func press(timeline, index: int, at: int) -> void:
	var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.pressed=true
	event.position=Vector2(timeline.x(at),timeline.row_y(index)+12);timeline._gui_input(event)

func motion(app, at: int) -> void:
	var event:=InputEventMouseMotion.new();event.position=app.timeline.get_global_transform()*Vector2(app.timeline.x(at),-200)
	app._input(event)

func release(app) -> void:
	var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.pressed=false;event.position=Vector2(2,2)
	app._input(event)

func run() -> void:
	var folder:=ProjectSettings.globalize_path("res://output/object-timing/run_%d" % Time.get_ticks_usec());DirAccess.make_dir_recursive_absolute(folder)
	var asset:=folder.path_join("actor.glb");var map:=folder.path_join("room.glb");SceneIO.make_pose_fixture(asset);SceneIO.make_fixture(map)
	var original:=FileAccess.get_sha256(asset)
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled()
	app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	app.load_scene(map);var map_id: String=app.last_import_id
	app.pose_editor.add_model(asset,8);var id: String=app.last_import_id;var rig: RefCounted=app.renderer.active_model();var editor=app.pose_editor
	for frame in [8,16,24]:
		app.set_frame(frame);editor.operation.select(1);editor.selected="@root";editor.refresh_values();editor.fields[0].value=float(frame)/8;editor.apply_numeric()
	var bone: String=rig.order[1]
	app.set_frame(16);editor.tree_items[bone].select(0);editor.operation.select(0);editor.refresh_values();editor.fields[2].value=35;editor.apply_numeric()
	app.pose_editor.add_model(asset,4);var peer: String=app.last_import_id
	rig=app.renderer.world_runtime.instance(id);app.world_selection.select_entity(id);editor.frame_model();var camera: Camera3D=app.renderer.camera
	app.keys=[Timeline.key(0,camera.position,camera.quaternion,camera.fov)]
	app.mode.select(0);app.change_mode(0);app.set_frame(0);app.create_cel(false)
	Drawing.stroke(Drawing.image(Drawing.cel_at(app.layers[1],0)),Vector2(80,90),Vector2(180,90),5,Color.RED,false);app.changed()
	app.set_frame(12);await settled()
	var before: Dictionary=rig.data.duplicate(true);var peer_before: Dictionary=app.renderer.world_runtime.instance(peer).data.duplicate(true)
	var map_before: Dictionary=app.renderer.world_runtime.instance(map_id).data.duplicate(true)
	var shots: Array=app.keys.duplicate(true);var paint: PackedByteArray=Drawing.image(Drawing.cel_at(app.layers[1],0)).get_data()
	var view: Transform3D=camera.transform;var history: int=app.history.size();var timeline=app.timeline
	check(timeline.object_rows.size()==3 and timeline.object_rows[0].id==map_id and timeline.object_rows[1].id==id and timeline.object_rows[2].id==peer,"every map/model has an independent collapsed timeline row")
	var reference: Image=await app.renderer.capture(app.keys,app.layers,12,true)
	press(timeline,1,12);motion(app,20)
	check(timeline.moving_id==id and timeline.moving_delta==8 and rig.data==before and app.history.size()==history,"drag previews an eight-frame move without mutating document or Undo")
	app.changed();var checkpoint: int=app.checkpoint_revision;app.autosave_tick(true);await preload("res://tests/recovery_wait.gd").checkpoint(app)
	check(app.checkpoint_revision==checkpoint,"recovery defers during an active timeline drag")
	release(app)
	check(timeline.moving_id.is_empty() and rig.data.start_frame==16 and rig.authored_keys()[0].frame==16 and rig.authored_keys()[2].frame==32,"release outside timeline commits presence and every root/bone key together")
	check(app.history.size()==history+1 and app.history[-1].type=="world_object" and app.history[-1].object_id==id,"one drag creates one stable-object Undo command")
	check(app.frame==12 and app.keys==shots and camera.transform.is_equal_approx(view) and Drawing.image(Drawing.cel_at(app.layers[1],0)).get_data()==paint,"retiming preserves playhead, camera keys/view and independent drawing")
	check(app.renderer.world_runtime.instance(peer).data==peer_before and app.renderer.world_runtime.instance(map_id).data==map_before,"moving one take preserves other model and map data")
	var shifted: Dictionary=rig.data.duplicate(true);var old:=Model.new();old.data=before
	check(editor.same_transform(rig.sample_transform(20),old.sample_transform(12)) and rig.sample(24)==old.sample(16),"relative root and bone interpolation follows the shifted take")
	var after: Image=await app.renderer.capture(app.keys,app.layers,20,true)
	reference.save_png(folder.path_join("before.png"));after.save_png(folder.path_join("after.png"))
	var difference:=0;var total:=0;var aa:=reference.get_data();var bb:=after.get_data()
	for i in range(aa.size()):
		if aa[i]!=bb[i]:difference+=1;total+=absi(int(aa[i])-int(bb[i]))
	check(difference<=384 and float(total)/aa.size()<0.002,"same relative time retains camera/model/drawing pixels within existing GPU edge tolerance")
	print("TIMING_PIXEL_DIFFERENCE ",difference," mean=",float(total)/aa.size())
	app.renderer.world_runtime.evaluate(15);var absent: bool=not rig.root.visible;app.renderer.world_runtime.evaluate(16)
	check(absent and rig.root.visible,"shifted first presence remains absent before its new start")
	check(editor.same_transform(rig.sample_transform(45),rig.sample_transform(32)) and rig.sample(45)==rig.sample(32),"single take holds its last state after its authored end")
	app.world_selection.select_entity(peer);app.undo()
	check(rig.data==before and app.renderer.active_instance_id==peer,"Undo restores original timing after selecting a different object")
	app.redo();check(rig.data==shifted,"Redo restores the full shifted take")
	app.retime_object(id,-500,rig.data.duplicate(true))
	check(rig.data.start_frame==0 and rig.authored_keys()[0].frame==0 and rig.authored_keys()[2].frame==16,"left boundary clamps the whole take without dropping keys")
	app.undo();app.retime_object(id,500,rig.data.duplicate(true))
	check(rig.authored_keys()[-1].frame==48 and rig.authored_keys()[0].frame==32,"right boundary preserves relative spacing and the end-boundary key")
	app.undo();app.world_selection.select_entity(id);app.set_frame(12);await settled()
	history=app.history.size();press(timeline,1,20);motion(app,28)
	var escape:=InputEventKey.new();escape.keycode=KEY_ESCAPE;escape.pressed=true;app._input(escape)
	check(timeline.moving_id.is_empty() and rig.data==shifted and app.history.size()==history,"Escape cancels the preview without edits or history")
	press(timeline,1,20);motion(app,28);app._notification(Node.NOTIFICATION_WM_WINDOW_FOCUS_OUT)
	check(timeline.moving_id.is_empty() and rig.data==shifted,"focus loss cancels a timeline gesture safely")
	press(timeline,1,20);motion(app,28);editor.set_flag("visible",false);var hidden: Dictionary=rig.data.duplicate(true);release(app)
	check(rig.data==hidden and "changed while dragging" in app.status.text,"stale drag cannot overwrite another edit to the same object")
	app.undo();app.world_selection.select_entity(id);app.set_frame(20)
	app.exporting=true;app.export_controls(app,true);var selected: String=app.renderer.active_instance_id
	press(timeline,1,20)
	check(timeline.moving_id.is_empty() and app.renderer.active_instance_id==selected and not app.timeline_ruler.interactive,"timeline gestures and ruler are disabled during actual export control lock")
	app.exporting=false;app.export_controls(app,false)
	var project:=folder.path_join("retimed.has");app.has_project.save_file(project,"packed");await wait_job(app.has_project)
	app.new_project();app.has_project.open_file(project);await wait_job(app.has_project)
	rig=app.renderer.world_runtime.instance(id)
	check(rig.data.start_frame==16 and Support.same_keys(rig.data,shifted) and app.timeline.object_rows.size()==3,"normal packed HAS reopen preserves moved object presence/keys and all rows")
	var expected: Image=await app.renderer.capture(app.keys,app.layers,20,true)
	var error: String=await app.export_movie(folder)
	check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000021.png")).get_data()==expected.get_data(),"MP4 export uses the same retimed world and separate cel")
	var movie: String=app.last_export_folder.path_join("movie.mp4")
	# Full row limit uses shared authored geometry, never owner assets.
	var document:=World.empty()
	for i in range(64):
		var row:=World.object(asset,"model","Actor %02d" % i);document.objects.append(row)
	check(app.restore_world(document).is_empty(),"full64-object world still installs with timeline lanes")
	await settled();var scroll: ScrollContainer=timeline.get_parent();scroll.scroll_vertical=2000;await settled()
	check(timeline.object_rows.size()==64 and scroll.size.y<230 and scroll.get_v_scroll_bar().visible and app.canvas.size.y>100,"64rows scroll inside a bounded timeline without consuming the viewport")
	check(app.timeline_ruler.is_visible_in_tree() and app.timeline_ruler.global_position.y<scroll.global_position.y and absf(app.timeline_ruler.size.x-timeline.size.x)<0.1,"frame ruler/camera lane remain pinned and column-aligned after row scrolling")
	var last: Dictionary=timeline.object_rows[-1]
	var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.pressed=true;event.position=timeline.get_global_transform()*Vector2(40,timeline.row_y(63)+12)
	app.get_viewport().push_input(event,true);await settled();event.pressed=false;app.get_viewport().push_input(event,true);await settled()
	check(app.renderer.active_instance_id==last.id and app.timeline.selected_id==last.id,"routed click selects the scrolled last object's row and pose target")
	root.get_texture().get_image().save_png(folder.path_join("timeline-64.png"))
	check(FileAccess.get_sha256(asset)==original,"timeline edits never alter source geometry")
	var native_samples:=[];var native_world:=World.empty()
	for sample in ["pose-smoke/miku-project","source-smoke/source-project","sfm-smoke/project"]:
		var path:=ProjectSettings.globalize_path("res://output/"+sample)
		if not FileAccess.file_exists(path.path_join("project.json")):print("SKIP optional native timing fixture: "+sample);continue
		var source: Dictionary=Storage.load_project(path)
		var row: Dictionary=World.from_project(source).objects[-1]
		row=Support.legacy_model(row)
		row.id="native-%d" % native_samples.size();row.parent_id="";row.start_frame=0;row.pose_keys=[];row.pose={}
		var doc:=World.empty();doc.objects.append(row);app.restore_world(doc);app.world_selection.select_entity(row.id);app.set_frame(0)
		rig=app.renderer.active_model();editor=app.pose_editor
		var native_hash:=FileAccess.get_sha256(rig.data.source);var metadata: Dictionary=rig.data.metadata.duplicate(true)
		var native_bone:=""
		for candidate in rig.order:
			if str(rig.bones[candidate].name).ends_with({"pose-smoke/miku-project":"左腕","source-smoke/source-project":"L_UpperArm","sfm-smoke/project":"bip_upperArm_L"}[sample]):native_bone=candidate
		check(not native_bone.is_empty(),"native rig exposes its original arm for timeline motion: "+sample)
		if native_bone.is_empty():continue
		editor.frame_model();camera=app.renderer.camera;app.keys=[Timeline.key(0,camera.position,camera.quaternion,camera.fov)]
		editor.tree_items[native_bone].select(0);editor.record_key()
		var neutral: Image=await app.renderer.capture(app.keys,[],0,true)
		app.set_frame(8);editor.operation.select(0);editor.refresh_values();editor.fields[2].value=35;editor.apply_numeric()
		var posed: Image=await app.renderer.capture(app.keys,[],8,true);var pose4: Dictionary=rig.sample(4)
		var original_data: Dictionary=rig.data.duplicate(true);app.retime_object(row.id,12,original_data)
		check(neutral.get_data()!=posed.get_data() and rig.data.start_frame==12 and rig.authored_keys()[0].frame==12 and rig.authored_keys()[1].frame==20 and rig.sample(16)==pose4,"native skin motion and relative arm keys survive moving its block: "+sample)
		app.undo();var restored: bool=rig.data==original_data;app.redo()
		check(restored and rig.data.metadata==metadata and FileAccess.get_sha256(rig.data.source)==native_hash,"native timing Undo/Redo preserves provenance and original geometry: "+sample)
		native_world.objects.append(rig.data.duplicate(true));native_samples.append(sample)
	var native_project:=""
	if native_samples.size()==3:
		app.restore_world(native_world);native_project=folder.path_join("native-retimed.has")
		app.has_project.save_file(native_project,"packed");await wait_job(app.has_project)
		app.new_project();app.has_project.open_file(native_project);await wait_job(app.has_project)
		var retained:=true
		for row in native_world.objects:
			var loaded: RefCounted=app.renderer.world_runtime.instance(row.id)
			retained=retained and loaded!=null and loaded.data.start_frame==12 and Support.same_keys(loaded.data,row)
		check(retained and app.timeline.object_rows.size()==3,"packed HAS reopens all three retimed MMD/GMod/SFM rigs and timeline rows")
	var result:={"checks":checks,"failures":failures,"folder":folder,"project":project,"movie":movie,"native_samples":native_samples,"native_project":native_project,"changed_channels":difference,"mean_pixel_error":float(total)/aa.size()}
	var file:=FileAccess.open("res://output/object-timing-result.json",FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close()
	print("OBJECT_TIMING "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
