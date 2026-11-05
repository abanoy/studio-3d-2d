extends SceneTree
const SceneIO=preload("res://src/scene3d.gd")
const Placement=preload("res://src/import_placement.gd")
const Timeline=preload("res://src/timeline.gd")
const Storage=preload("res://src/storage.gd")
var checks:=0
var failures:=0

func _initialize() -> void:
	create_timer(100).timeout.connect(func():push_error("Placement watchdog expired");quit(2))
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
	var folder:=ProjectSettings.globalize_path("res://output/import-placement/run_%d" % Time.get_ticks_usec());DirAccess.make_dir_recursive_absolute(folder)
	var map:=folder.path_join("room.glb");var asset:=folder.path_join("actor.glb");SceneIO.make_fixture(map);SceneIO.make_pose_fixture(asset)
	var original:=FileAccess.get_sha256(asset)
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled()
	app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	var unchanged: Dictionary=app.current_world();var history: int=app.history.size()
	var invalid: String=app.pose_editor.add_model(asset,0,{"physics_on_import":false})
	check(not invalid.is_empty() and app.current_world()==unchanged and app.history.size()==history,"incomplete placement context refuses without script errors or scene edits")
	check(Placement.plan(app.renderer,asset,{"camera":Transform3D.IDENTITY,"fov":NAN,"aspect":1.}).has("error"),"nonfinite projection refuses before geometry allocation")
	app.load_scene(map);var map_id: String=app.last_import_id
	var editor=app.pose_editor;editor.operation.select(1);editor.refresh_values();editor.fields[0].value=100;editor.fields[1].value=4;editor.fields[2].value=100;editor.apply_numeric()
	var map_data: Dictionary=app.renderer.active_model().data.duplicate(true)
	var camera: Camera3D=app.renderer.camera;camera.position=Vector3(100,6,105);camera.quaternion=Quaternion.IDENTITY
	var view: Transform3D=camera.transform;var context: Dictionary=app.import_actions.placement()
	var shots: Array=app.keys.duplicate(true)
	var started:=Time.get_ticks_usec();app.import_actions.add(asset,true,0);var elapsed:=Time.get_ticks_usec()-started
	var first: String=app.last_import_id;var one: RefCounted=app.renderer.active_model();var first_bounds: AABB=app.renderer.scene_bounds(one.root)
	check(one.data.position[0]>90 and one.data.position[2]>90 and camera.transform==view,"model spawns near distant camera without changing the view")
	check(one.data.metadata.initial_placement.support=="mesh" and absf(first_bounds.position.y-4)<0.01,"spawned feet rest on translated imported floor rather than world origin")
	check(Placement.in_view(first_bounds,context),"whole initial model bounds fit the import camera view")
	check(app.renderer.world_runtime.instance(map_id).data==map_data and app.keys==shots,"placement preserves map root animation and explicit shot keys")
	check(one.data.pose_keys.is_empty(),"import placement is a static root choice, not an implicit animation key")
	var first_data: Dictionary=one.data.duplicate(true)
	app.import_actions.add(asset,true,0);var second: String=app.last_import_id;var two: RefCounted=app.renderer.active_model();var second_bounds: AABB=app.renderer.scene_bounds(two.root)
	check(not first_bounds.grow(-0.01).intersects(second_bounds) and two.data.metadata.initial_placement.attempts>1,"nearby candidate search avoids an existing actor")
	check(app.renderer.world_runtime.instance(first).data==first_data,"new placement does not move existing actor")
	app.undo();app.redo()
	check(app.renderer.world_runtime.instance(second).data==two.data,"Undo/Redo restores the chosen root placement exactly")
	# A large model bounding volume occupies all useful nearby candidates.
	app.pose_editor.add_model(map);var blocker: RefCounted=app.renderer.active_model();editor.operation.select(1);editor.refresh_values();editor.fields[0].value=100;editor.fields[1].value=4;editor.fields[2].value=100;editor.apply_numeric()
	app.renderer.camera.transform=view;app.import_actions.add(asset,true,0)
	var fallback: RefCounted=app.renderer.active_model()
	check(fallback.data.metadata.initial_placement.attempts==9 and fallback.data.metadata.initial_placement.overlap,"all blocked candidates still import visibly with overlap explicitly recorded")
	check(Placement.in_view(app.renderer.scene_bounds(fallback.root),context),"overlap fallback retains visible placement")
	# High aerial view should prefer visible fallback to an offscreen ground plane.
	app.new_project();camera.position=Vector3(300,100,305);camera.quaternion=Quaternion.IDENTITY
	var aerial_context: Dictionary=app.import_actions.placement()
	app.keys=[Timeline.key(0,camera.position,camera.quaternion,camera.fov)]
	app.import_actions.add(asset,true,24);var aerial: RefCounted=app.renderer.active_model();var aerial_id: String=app.last_import_id
	check(aerial.data.metadata.initial_placement.support=="view" and aerial.data.start_frame==24,"no nearby support retains visible aerial fallback and requested presence")
	app.set_frame(24);check(Placement.in_view(app.renderer.scene_bounds(aerial.root),aerial_context),"aerial fallback remains inside camera frustum")
	var saved_data: Dictionary=aerial.data.duplicate(true);app.keys=[Timeline.key(0,camera.position,camera.quaternion,camera.fov)]
	var project:=folder.path_join("placed.has");app.has_project.save_file(project,"packed");await wait_job(app.has_project)
	app.new_project();app.has_project.open_file(project);await wait_job(app.has_project)
	var reopened: Dictionary=app.renderer.world_runtime.instance(aerial_id).data
	check(Timeline.vector(reopened.position).distance_to(Timeline.vector(saved_data.position))<0.0001 and reopened.metadata==JSON.parse_string(JSON.stringify(saved_data.metadata,"",true,true)),"packed HAS preserves chosen placement and fallback diagnostics")
	var image: Image=await app.renderer.capture(app.keys,app.layers,24,true)
	var error: String=await app.export_movie(folder)
	check(error.is_empty() and image.get_data()==Image.load_from_file(app.last_export_folder.path_join("frame_000025.png")).get_data(),"placed model exports with same presence/root as preview")
	check(FileAccess.get_sha256(asset)==original,"placement never modifies source GLB")
	var tip:=PopupPanel.new();tip.set_flag(Window.FLAG_NO_FOCUS,true);tip.set_flag(Window.FLAG_MOUSE_PASSTHROUGH,true);tip.set_flag(Window.FLAG_POPUP,false)
	var text:=Label.new();text.text="Placement hint";tip.add_child(text);app.add_child(tip);tip.popup();await settled()
	check(not app.has_dialog(app),"passive tooltip-style window cannot defer recovery")
	app.changed();app.autosave_tick(true)
	check(not Storage.load_project(app.recovery_root.path_join(app.recovery_session)).has("error"),"actual recovery checkpoint succeeds while passive hint is visible")
	var dialog:=AcceptDialog.new();app.add_child(dialog);dialog.popup_centered();await settled()
	app.changed();var checkpoint: int=app.checkpoint_revision;app.autosave_tick(true)
	check(app.has_dialog(app) and app.checkpoint_revision==checkpoint and app.checkpoint_revision!=app.recovery_revision,"interactive dialog still defers recovery")
	dialog.hide();dialog.queue_free();tip.hide();tip.queue_free()
	var movie: String=app.last_export_folder.path_join("movie.mp4")
	var native_ms:=-1.0;var native_support:="not tested"
	var source_record:=ProjectSettings.globalize_path("res://output/source-verification.json")
	if FileAccess.file_exists(source_record):
		var source_report: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(source_record))
		var map_path: String=str(source_report.map_bundle).path_join("scene.glb")
		if FileAccess.file_exists(map_path):
			app.new_project();app.load_scene(map_path)
			var parameters: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(str(source_report.map_bundle).path_join("parameters.json")))
			app.source_import.apply_view(parameters)
			var native_context: Dictionary=app.import_actions.placement()
			var query_started:=Time.get_ticks_usec()
			var native: Dictionary=Placement.plan(app.renderer,asset,native_context)
			native_ms=(Time.get_ticks_usec()-query_started)/1000.0;native_support=native.get("support","error")
			check(not native.has("error") and native.triangles<=Placement.TRIANGLE_BUDGET and native.attempts<=9,"actual GMod map uses bounded geometry query and candidate count")
			var decoded: Dictionary=SceneIO.load_glb(asset);var native_bounds: AABB=Placement.local_bounds(decoded.scene);decoded.scene.free()
			check(native.position.is_finite() and Placement.in_view(AABB(native_bounds.position+native.position,native_bounds.size),native_context),"actual GMod query returns whole-model placement inside import view")
			app.keys=[Timeline.key(0,camera.position,camera.quaternion,camera.fov)]
			var native_before: Image=await app.renderer.capture(app.keys,app.layers,0,true)
			app.import_actions.add(asset,true,0)
			var native_after: Image=await app.renderer.capture(app.keys,app.layers,0,true)
			check(native_before.get_data()!=native_after.get_data(),"actor placed in actual GMod map contributes rendered pixels without reframing")
			native_after.save_png(folder.path_join("native-placement.png"))
	var result:={"checks":checks,"failures":failures,"folder":folder,"project":project,"movie":movie,"authored_import_microseconds":elapsed,"native_query_ms":native_ms,"native_support":native_support}
	var file:=FileAccess.open("res://output/import-placement-result.json",FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close()
	print("IMPORT_PLACEMENT "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
