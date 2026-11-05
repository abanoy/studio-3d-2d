extends SceneTree
const SceneIO=preload("res://src/scene3d.gd")
const Timeline=preload("res://src/timeline.gd")
var checks:=0
var failures:=0

func _initialize() -> void:
	create_timer(90).timeout.connect(func():push_error("Import timing watchdog expired");quit(2))
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

func run() -> void:
	var folder:=ProjectSettings.globalize_path("res://output/import-timing/run_%d" % Time.get_ticks_usec());DirAccess.make_dir_recursive_absolute(folder)
	var asset:=folder.path_join("actor.glb");SceneIO.make_pose_fixture(asset);var original:=FileAccess.get_sha256(asset)
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled()
	app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	var point: Vector2=app.canvas.get_global_rect().get_center()
	var screen_point: Vector2=app.canvas.get_screen_transform()*(app.canvas.size/2)
	check(app.import_actions.canvas_point(screen_point).distance_to(point)<0.01,"OS screen coordinates map into the viewport using actual window/stretch transform")
	check(not app.get_window().get_signal_connection_list("files_dropped").is_empty(),"native window file-drop signal has an application handler")
	app.set_frame(32);app.playing=true
	app.import_actions.drop(PackedStringArray([asset]),point);await settled()
	var choice: ConfirmationDialog=null
	for child in app.get_children():
		if child is ConfirmationDialog and child.title=="Add actor.glb":choice=child;break
	check(choice!=null and not app.playing,"viewport drop handler opens model/map choice and pauses playback")
	if not choice:print(app.status.text);app.free();quit(1);return
	choice.confirmed.emit();await settled()
	var first: String=app.last_import_id
	check(app.renderer.world_runtime.instances.size()==1 and app.renderer.active_model().data.start_frame==0 and app.frame==32,"viewport drop imports at frame0 regardless of viewed frame")
	var before: Dictionary=app.renderer.world_state().duplicate(true)
	app.import_actions.drop(PackedStringArray([asset,asset]),point)
	check(app.renderer.world_state()==before and "one file" in app.status.text,"multiple-file drop rejects whole request without silently losing files")
	app.import_actions.drop(PackedStringArray([asset]),Vector2(-100,-100))
	check(app.renderer.world_state()==before,"drop outside viewport cannot import")
	app.import_actions.drop(PackedStringArray([folder.path_join("no.png")]),point)
	check(app.renderer.world_state()==before and "supported" in app.status.text,"unsupported drop preserves world with useful message")
	var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_RIGHT;event.pressed=true;event.position=Vector2(app.timeline.x(24),40)
	app.timeline._gui_input(event);await settled()
	check(app.timeline.import_menu.visible and app.frame==32 and not app.timeline.dragging,"timeline right-click opens import menu without scrubbing or starting a drag")
	app.timeline.import_menu.id_pressed.emit(0);await settled()
	var picker: FileDialog=null
	for child in app.get_children():
		if child is FileDialog and child.visible:picker=child;break
	check(picker!=null and app.frame==24,"timeline model action opens native picker at chosen frame")
	if not picker:app.free();quit(1);return
	picker.file_selected.emit(asset);await settled()
	var second: String=app.last_import_id;var rig: RefCounted=app.renderer.world_runtime.instance(second)
	check(second!=first and rig.data.start_frame==24 and app.renderer.world_runtime.instance(first).data.start_frame==0,"timeline import preserves existing instance and records independent presence")
	app.renderer.world_runtime.evaluate(23);var absent: bool=not rig.root.visible
	app.renderer.world_runtime.evaluate(24)
	check(absent and rig.root.visible,"timeline object is absent before24 and present at24")
	app.undo();check(not app.renderer.world_runtime.instances.has(second),"Undo timed import removes only added object")
	app.redo();check(app.renderer.world_runtime.instance(second).data.start_frame==24,"Redo restores chosen first presence")
	# Real asynchronous native importer must retain request frame, not completion frame.
	var vrm:=preload("res://tests/native_sample_paths.gd").vrm("AvatarSample_A.vrm")
	var native_tested:=false
	if FileAccess.file_exists(vrm):
		app.import_actions.add(vrm,true,40);check(app.source_import.pid>0,"timed native import starts actual asynchronous worker")
		app.import_actions.drop(PackedStringArray([asset]),point)
		check(app.renderer.world_runtime.instances.size()==2 and app.source_import.pid>0 and "Finish" in app.status.text,"second drop cannot overwrite a pending asynchronous import request")
		app.set_frame(5);await wait_job(app.source_import)
		for child in app.get_children():
			if child is AcceptDialog and child.title=="Imported with limitations":child.hide();child.queue_free()
		check(app.renderer.active_model().data.start_frame==40 and app.frame==5,"asynchronous VRM import keeps chosen frame40 after playhead moves to5")
		native_tested=true
	app.world_selection.select_entity(second);app.pose_editor.frame_model();app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,app.renderer.camera.fov)]
	app.mode.select(0);app.change_mode(0);app.set_frame(24)
	var project:=folder.path_join("timed.has");app.has_project.save_file(project,"packed");await wait_job(app.has_project)
	app.new_project();app.has_project.open_file(project);await wait_job(app.has_project)
	check(app.renderer.world_runtime.instance(first).data.start_frame==0 and app.renderer.world_runtime.instance(second).data.start_frame==24,"packed HAS preserves independent import presence after fresh New/Open")
	app.world_selection.select_entity(first);app.pose_editor.set_flag("visible",false)
	var at23: Image=await app.renderer.capture(app.keys,app.layers,23,true);var at24: Image=await app.renderer.capture(app.keys,app.layers,24,true)
	check(at23.get_data()!=at24.get_data(),"actual rendered pixels change when timed actor first appears")
	var error: String=await app.export_movie(folder)
	check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000024.png")).get_data()==at23.get_data() and Image.load_from_file(app.last_export_folder.path_join("frame_000025.png")).get_data()==at24.get_data(),"MP4 frame evaluation honors exact presence boundary")
	check(FileAccess.get_sha256(asset)==original,"drop/timeline import preserves original GLB bytes")
	var report:={"checks":checks,"failures":failures,"folder":folder,"project":project,"movie":app.last_export_folder.path_join("movie.mp4"),"native_tested":native_tested}
	var file:=FileAccess.open("res://output/import-timing-result.json",FileAccess.WRITE);file.store_string(JSON.stringify(report));file.close()
	print("IMPORT_TIMING "+JSON.stringify(report));app.free();quit(0 if failures==0 else 1)
