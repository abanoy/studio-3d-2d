extends SceneTree
const Support = preload("res://tests/world_test_support.gd")
const Timeline = preload("res://src/timeline.gd")
const Drawing = preload("res://src/drawing.gd")
const Recovery = preload("res://src/recovery.gd")
var checks := 0
var failures := 0

func _initialize() -> void:
	create_timer(180).timeout.connect(func(): push_error("Generic import watchdog expired"); quit(2))
	call_deferred("run")

func check(ok: bool, text: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+text)
	if not ok:failures+=1

func wait_import(app) -> void:
	while app.source_import.pid>0:await process_frame
	await process_frame

func run() -> void:
	var folder := ProjectSettings.globalize_path("res://output/generic-smoke/run_%d" % Time.get_ticks_usec())
	DirAccess.make_dir_recursive_absolute(folder)
	var app = load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await process_frame;app.home.hide();app.autosave_enabled.button_pressed=false
	var fixtures := ProjectSettings.globalize_path("res://output/generic-fixtures")
	var base_scene: String = app.source
	app.source_import.gmod_root=folder.path_join("not-installed")
	var bundles := {}
	for name in ["rig-linked.fbx","rig.gltf","embedded-only/rig.fbx","embedded-gltf/rig.gltf"]:
		var saved_keys := JSON.stringify(app.keys)
		app.pose_editor.add_model(fixtures.path_join(name))
		var dialog: ConfirmationDialog
		for child in app.get_children():
			if child is ConfirmationDialog and child.title=="Import 3D model":dialog=child
		check(dialog!=null,"model picker dispatches generic preparation: "+name)
		if dialog==null:quit(1);return
		if name=="rig-linked.fbx":
			await process_frame;await RenderingServer.frame_post_draw
			check(dialog.position.y>=0 and dialog.position.y+dialog.size.y<=root.size.y,"generic preparation dialog fits current studio window")
			root.get_texture().get_image().save_png(folder.path_join("generic-dialog.png"))
		dialog.confirmed.emit();await wait_import(app)
		check(Support.rig(app)!=null and app.source==base_scene and JSON.stringify(app.keys)==saved_keys,"generic import installs actor without requiring GMod or changing environment/shot: "+name)
		if Support.rig(app)==null:print(app.status.text);quit(1);return
		bundles[name]=app.source_import.folder
		var report := Recovery.read_json(app.source_import.folder.path_join("parameters.json"))
		check(report.get("adapter")=="studio_generic_1" and report.counts.bones>=2 and report.counts.textures>=1,"native rig and embedded/resolved texture survive: "+name)
		check(report.counts.meshes==1,"conversion excludes editor-only bone display geometry: "+name)
		var bounds: AABB=app.renderer.scene_bounds(Support.rig(app).root)
		check(report.scale==1 and absf(bounds.size.y-2)<0.02,"default scale and imported up-axis retain two-unit height: "+name)
		var arm := ""
		for id in Support.rig(app).order:
			if Support.rig(app).bones[id].name=="Tip":arm=id
		check(not arm.is_empty(),"native Tip bone is selectable: "+name)
		if arm.is_empty():quit(1);return
		app.pose_editor.frame_model()
		var camera: Camera3D=app.renderer.camera
		app.keys=[Timeline.key(0,camera.position,camera.quaternion,camera.fov),Timeline.key(48,camera.position,camera.quaternion,camera.fov)]
		app.pose_editor.tree_items[arm].select(0);app.pose_editor.refresh_values();app.pose_editor.operation.select(0)
		var before: Image=await app.renderer.capture(app.keys,app.layers,0)
		app.pose_editor.fields[2].value=55;app.pose_editor.apply_numeric()
		var after: Image=await app.renderer.capture(app.keys,app.layers,0)
		check(before.get_data()!=after.get_data(),"shared pose controls visibly deform imported skin: "+name)
		after.save_png(folder.path_join(name.get_file()+".png"))
		app.undo();var undo: Image=await app.renderer.capture(app.keys,app.layers,0)
		check(before.get_data()==undo.get_data(),"pose undo restores exact pixels: "+name)
		app.pose_editor.set_flag("visible",false)
	# OBJ environment through the same UI, preserving the last imported actor.
	var actor_hash: String=Support.rig(app).data.sha256
	app.load_scene(fixtures.path_join("textured.obj"))
	var scene_dialog: ConfirmationDialog
	for child in app.get_children():
		if child is ConfirmationDialog and child.title=="Import 3D environment":scene_dialog=child
	check(scene_dialog!=null,"OBJ Add scene opens scale/asset-folder/up-axis dialog")
	if scene_dialog:
		for field in scene_dialog.find_children("*","SpinBox",true,false):field.value=2
		scene_dialog.confirmed.emit()
	await wait_import(app)
	check(FileAccess.get_sha256(app.source)==FileAccess.get_sha256(app.source_import.folder.path_join("scene.glb")) and app.source!=base_scene and Support.rig(app).data.sha256==actor_hash and app.renderer.world_runtime.instances.size()==5,"OBJ/MTL environment appends beside all four independent actors")
	var obj_bundle: String=app.source_import.folder;bundles["textured.obj"]=obj_bundle
	var obj_report:=Recovery.read_json(obj_bundle.path_join("parameters.json"))
	check(obj_report.counts.textures>=1 and obj_report.counts.bones==0,"OBJ material texture loads from checked MTL path with spaces")
	var environment_bounds: AABB=app.renderer.scene_bounds(app.renderer.environment_root())
	check(obj_report.scale==2 and absf(environment_bounds.size.y-4)<0.02,"chosen import scale changes normalized OBJ geometry to four-unit height")
	# Frame actor, key pose and camera, draw independently, pack, reopen and export.
	Support.select_rig(app);app.pose_editor.set_flag("visible",true)
	Support.rig(app).data.position=[1,0,0];Support.rig(app).apply(app.frame)
	app.pose_editor.frame_model();var camera: Camera3D=app.renderer.camera
	app.keys=[Timeline.key(0,camera.position,camera.quaternion,camera.fov),Timeline.key(48,camera.position+Vector3(.1,0,0),camera.quaternion,camera.fov)]
	app.pose_editor.record_key();app.set_frame(48);app.pose_editor.fields[2].value=70;app.pose_editor.apply_numeric();app.pose_editor.record_key();app.set_frame(24)
	app.mode.select(0);app.change_mode(0);app.create_cel(false)
	Drawing.stroke(Drawing.image(Drawing.cel_at(app.layers[1],24)),Vector2(100,100),Vector2(260,100),6,Color.RED,false)
	var packed:=folder.path_join("generic.has");app.has_project.cache_root=folder.path_join("has-cache")
	app.has_project.save_file(packed,"packed")
	while app.has_project.pid>0:await process_frame
	app.has_project.open_file(packed)
	while app.has_project.pid>0:await process_frame
	check(app.has_project.path==packed and Support.rig(app)!=null,"OBJ environment and FBX actor preserve metadata/poses through packed HAS")
	var expected: Image=await app.renderer.capture(app.keys,app.layers,24,true)
	var error: String=await app.export_movie(folder)
	var movie: String=app.last_export_folder.path_join("movie.mp4")
	var frame:=Image.load_from_file(app.last_export_folder.path_join("frame_000025.png"))
	check(error.is_empty() and frame.get_data()==expected.get_data(),"converted formats export camera/pose/cel MP4 with exact preview frame24")
	var retained: String=app.source
	var previous_objects: Array=app.current_world().objects.duplicate(true)
	var broken:=folder.path_join("missing.gltf");var input:=FileAccess.open(broken,FileAccess.WRITE)
	var document:=FileAccess.get_file_as_string(fixtures.path_join("rig.gltf"))
	input.store_string(document.replace('"rig.bin"','"missing.bin"'));input.close()
	DirAccess.make_dir_recursive_absolute(folder.path_join("textures"))
	check(DirAccess.copy_absolute(fixtures.path_join("textures/surface color.png"),folder.path_join("textures/surface color.png"))==OK,"stage intact texture alongside the test model")
	app.source_import.launch(broken,"",true,1);await wait_import(app)
	check(app.current_world().objects==previous_objects and "Missing dependency: missing.bin" in app.status.text and "then import again" in app.status.text and not DirAccess.dir_exists_absolute(app.source_import.folder),"missing glTF sidecar names the file and retry step before staging and preserves the live project")
	check(DirAccess.copy_absolute(fixtures.path_join("rig.bin"),folder.path_join("missing.bin"))==OK,"restore the named companion without editing the glTF")
	app.source_import.launch(broken,"",true,1);await wait_import(app)
	var recovered: Array=app.current_world().objects
	check(recovered.size()==previous_objects.size()+1 and recovered.slice(0,previous_objects.size())==previous_objects and app.source==retained,"retry adds one actor and keeps all previously authored objects intact")
	app.source_import.launch(fixtures.path_join("rig-linked.fbx"),"",true,1)
	app.source_import.cancel();await wait_import(app)
	check(app.source==retained and app.source_import.cancelled,"cancelled generic conversion preserves current project")
	# Common-format workers must retain request intent after the playhead moves.
	var timed_before: Array=app.current_world().objects.duplicate(true);app.set_frame(40)
	app.import_actions.add(fixtures.path_join("rig-linked.fbx"),true,40)
	var timed_dialog: ConfirmationDialog
	for child in app.get_children():
		if child is ConfirmationDialog and child.title=="Import 3D model":timed_dialog=child
	check(timed_dialog!=null,"chosen-frame FBX import opens the normal preparation dialog")
	if not timed_dialog:quit(1);return
	timed_dialog.confirmed.emit();check(app.source_import.pid>0,"chosen-frame FBX uses a real asynchronous worker")
	app.set_frame(5);app.import_actions.drop(PackedStringArray([fixtures.path_join("rig.gltf")]),app.canvas.get_global_rect().get_center())
	check(app.current_world().objects==timed_before and app.source_import.pid>0 and app.status.text.contains("Finish"),"a second import cannot replace the pending common-format request")
	await wait_import(app);var timed_id: String=app.last_import_id;var timed_actor: RefCounted=app.renderer.world_runtime.instance(timed_id)
	check(timed_actor!=null and timed_actor.data.start_frame==40 and app.frame==5,"asynchronous FBX retains requested frame40 after playhead moves to5")
	check(app.current_world().objects.size()==timed_before.size()+1 and app.current_world().objects.slice(0,timed_before.size())==timed_before,"completed timed FBX leaves every earlier object unchanged")
	app.renderer.world_runtime.evaluate(39);var timed_absent: bool=not timed_actor.root.visible;app.renderer.world_runtime.evaluate(40)
	check(timed_absent and timed_actor.root.visible,"prepared common-format object has exact first-presence boundary")
	var timed_packed:=folder.path_join("timed-generic.has");app.has_project.save_file(timed_packed,"packed")
	while app.has_project.pid>0:await process_frame
	check(app.has_project.path==timed_packed,"ordinary packed Save retains timed common-format import")
	app.new_project();app.has_project.open_file(timed_packed)
	while app.has_project.pid>0:await process_frame
	check(app.renderer.world_runtime.instance(timed_id).data.start_frame==40 and app.frame==5,"fresh New/Open preserves async import presence and independent playhead")
	var result:={"checks":checks,"failures":failures,"folder":folder,"movie":movie,"bundles":bundles}
	var file:=FileAccess.open("res://output/generic-result.json",FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close()
	print("GENERIC_SMOKE "+JSON.stringify(result));quit(0 if failures==0 else 1)
