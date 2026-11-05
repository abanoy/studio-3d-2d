extends SceneTree
const Catalog=preload("res://src/shape_catalog.gd")
const Drawing=preload("res://src/drawing.gd")
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(180).timeout.connect(func():push_error("Shape study watchdog");quit(2));call_deferred("run")
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func settled() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func wait_study(study) -> int:
	var frames:=0
	while study.pid>0:await process_frame;frames+=1
	await settled();return frames
func choose(editor,target: int) -> bool:
	for i in range(editor.shapes.item_count):
		if int(editor.shapes.get_item_metadata(i))==target:editor.shapes.select(i);editor.shapes.item_selected.emit(i);return true
	return false
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0]
	var plans: Array=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("plans.json")))
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled()
	app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("has-cache")
	if OS.get_cmdline_user_args().size()>1:
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
		app.has_project.open_file(folder.path_join("study-adopted.has"))
		while app.has_project.pid>0:await process_frame
		var restored: RefCounted=app.renderer.world_runtime.instance(expected.id)
		check(restored!=null and restored.data.metadata==expected.metadata,"cold engine preserves exact adopted catalogue and native metadata")
		check(Drawing.cel_at(app.layers[1],0).image.get_pixel(80,80)==Color.CYAN,"cold engine preserves independent editable cyan paint")
		app.pose_editor.open_shapes();app.set_advanced(true);await settled()
		check(app.pose_editor.animated_shapes.study.observations.is_empty() and app.pose_editor.animated_shapes.study.pid<0,"cold engine has no resumed study or inferred auto-assignment")
		var cold:={"checks":checks,"failures":failures};FileAccess.open(folder.path_join("reader-result.json"),FileAccess.WRITE).store_string(JSON.stringify(cold));print("SHAPE_STUDY_READER "+JSON.stringify(cold));app.free();quit(0 if failures==0 else 1);return
	var error: String=app.pose_editor.add_model(plans[0].source);check(error.is_empty(),"study opens authored standard skin")
	app.pose_editor.frame_model();app.set_advanced(true);app.pose_editor.open_shapes();await settled()
	var editor=app.pose_editor.animated_shapes;var study=editor.study;choose(editor,0)
	editor.assigned_area.select(Catalog.AREAS.find("Hair"));editor.assign_control();await settled()
	var actor: RefCounted=app.renderer.active_model();var before: Dictionary=actor.data.duplicate(true);var history: int=app.history.size();var camera: Transform3D=app.renderer.camera.transform
	check(not study.start_button.disabled and study.start_button.is_visible_in_tree(),"Advanced exposes a real available study action")
	study.start_button.pressed.emit();var first_pid: int=study.pid
	check(first_pid>0,"study starts an actual owned Python worker")
	var frames: int=await wait_study(study)
	check(study.last_exit==0 and study.observations.size()==2,"real worker returns exact authored control inventory")
	check(actor.data==before and app.history.size()==history and app.renderer.camera.transform==camera,"neutral study preserves model, history and temporary camera exactly")
	choose(editor,1);await settled()
	check(study.selected().get("region_estimate",{}).get("area")=="Hair" and not study.adopt_button.disabled,"observed unknown control offers a labelled-region suggestion")
	check("Loose part shape" in study.info.text and "Manual choice" in study.info.text and "not a probability" in study.info.text,"review explains its exact example provenance and uncertainty")
	var scroller=editor.panel.get_parent().get_parent();scroller.ensure_control_visible(study.adopt_button);await settled()
	check(study.adopt_button.get_global_rect().end.y<=app.pose_editor.shape_window.size.y and app.pose_editor.shape_close.get_global_rect().end.y<=app.pose_editor.shape_window.size.y,"scrolling reaches adoption while Close remains inside the actual window")
	root.get_texture().get_image().save_png(folder.path_join("study-suggestion.png"))
	study.adopt_button.pressed.emit();await settled()
	var assigned: Dictionary=actor.data.duplicate(true);var entry:=Catalog.lookup(actor.data,editor.node_index,1,str(editor.row().names[1]))
	check(entry.manual and entry.area=="Hair" and app.history.size()==history+1,"explicit suggestion adoption saves one ordinary catalogue Undo")
	var unrelated:=assigned.duplicate(true);unrelated.metadata=before.metadata
	check(unrelated==before and assigned.metadata.shape_catalog.controls[str(editor.node_index)]["0"]==before.metadata.shape_catalog.controls[str(editor.node_index)]["0"],"adoption preserves all motion, native data and other manual controls")
	app.undo();await settled();check(actor.data==before,"Undo restores exact pre-adoption model")
	app.redo();await settled();check(actor.data==assigned,"Redo restores exact explicit adoption")
	study.start();await wait_study(study)
	var report: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(study.folder.path_join("result.json"))).value
	var original: Dictionary=study.observations.duplicate(true);var bad:=report.duplicate(true);bad.rows[0].native_name="changed"
	check(not study.install_report(bad).is_empty() and study.observations==original,"stale native identity refuses without replacing valid observations")
	bad=report.duplicate(true);bad.rows.append(bad.rows[0].duplicate(true))
	check(not study.install_report(bad).is_empty() and study.observations==original,"duplicate result binding refuses transactionally")
	bad=report.duplicate(true);bad.rows[1].region_estimate.matches[0].seed_target=999
	check(not study.install_report(bad).is_empty() and study.observations==original,"foreign study example identity refuses without replacing evidence")
	editor.amount.value=editor.amount.value+.123;study.start()
	check(study.pid<0 and editor.dirty and actor.data==assigned,"study defers unapplied amounts without consuming edits")
	editor.load_amount();study.start();study.cancel();await wait_study(study)
	check(study.cancelled and study.observations.is_empty() and actor.data==assigned,"explicit Cancel discards worker data and preserves the whole scene")
	app.physics_editor.queue_import_start(actor.data.id,true,false);var ticket: Dictionary=app.physics_editor.import_starts.duplicate(true);var generation: int=app.physics_editor.generation
	study.start();check(study.pid<0 and app.physics_editor.import_starts==ticket and app.physics_editor.generation==generation and actor.data==assigned,"pending physics defers study without consuming its real startup ticket");app.physics_editor.clear()
	study.start();app.pose_editor.shape_window.hide();await wait_study(study)
	check(study.cancelled and study.observations.is_empty(),"closing the shape window cancels its outstanding study")
	app.pose_editor.open_shapes();await settled();study.start();app.new_project();await wait_study(study)
	check(app.renderer.active_model()==null and study.observations.is_empty(),"New cancels old-source results without touching the new scene")
	var natives:=[];var total_frames:=0
	for plan in plans.slice(1):
		app.new_project();error=app.pose_editor.add_model(plan.source);app.pose_editor.open_shapes();app.set_advanced(true);await settled()
		actor=app.renderer.active_model();editor=app.pose_editor.animated_shapes;study=editor.study
		check(error.is_empty() and actor!=null,"study loads actual native preparation: "+plan.label)
		if not actor:continue
		before=actor.data.duplicate(true);history=app.history.size();study.start();frames=await wait_study(study);total_frames+=frames
		var count:=0
		for row in editor.rows():count+=row.names.size()
		check(study.last_exit==0 and study.observations.size()==count,"real native worker binds every control: "+plan.label)
		check(actor.data==before and app.history.size()==history,"native study leaves original authored data unchanged: "+plan.label)
		if plan.label=="SFM":check(frames>=10,"editor renders actual frames during Scout geometry study")
		natives.append({"label":plan.label,"targets":count,"frames":frames,"worker_folder":study.folder})
	# Final authored adoption uses normal HAS persistence, not a stored report cache.
	app.new_project();app.pose_editor.add_model(plans[0].source);app.pose_editor.open_shapes();await settled()
	editor=app.pose_editor.animated_shapes;study=editor.study;choose(editor,0);editor.assigned_area.select(Catalog.AREAS.find("Hair"));editor.assign_control();await settled()
	study.start();await wait_study(study);choose(editor,1);study.adopt();await settled();actor=app.renderer.active_model()
	var saved: Dictionary=actor.data.metadata.duplicate(true);var id: String=actor.data.id
	Drawing.insert(app.layers[1],0,48,Drawing.blank(1920,1080));Drawing.cel_at(app.layers[1],0).image.set_pixel(80,80,Color.CYAN)
	app.pose_editor.shape_window.hide();app.has_project.save_file(folder.path_join("study-adopted.has"),"packed")
	while app.has_project.pid>0:await process_frame
	app.new_project();app.has_project.open_file(folder.path_join("study-adopted.has"))
	while app.has_project.pid>0:await process_frame
	actor=app.renderer.world_runtime.instance(id)
	check(actor!=null and actor.data.metadata==saved,"ordinary packed HAS retains explicit adopted areas without analysis cache")
	app.pose_editor.open_shapes();app.set_advanced(true);await settled();editor=app.pose_editor.animated_shapes
	check(editor.study.observations.is_empty() and editor.study.pid<0,"Open never resumes an old study or installs inferred categories")
	root.get_texture().get_image().save_png(folder.path_join("study-ui.png"))
	app.pose_editor.shape_window.hide();var preview: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	var export_error: String=await app.export_movie(folder)
	check(export_error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000001.png")).get_data()==preview.get_data(),"explicit adoption preserves normal MP4 composition and exact independent drawing pixels")
	FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify({"id":id,"metadata":saved},"",true,true))
	var result:={"checks":checks,"failures":failures,"native":natives,"ui_frames":total_frames,"movie":app.last_export_folder.path_join("movie.mp4")};FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("SHAPE_STUDY_APP "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
