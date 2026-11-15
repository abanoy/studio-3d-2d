extends SceneTree
const Timeline=preload("res://src/timeline.gd")
const Storage=preload("res://src/storage.gd")
const World=preload("res://src/world_document.gd")
var app
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(180).timeout.connect(func():push_error("Owner review preparation watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settle() -> void:
	for i in range(5):await process_frame
	await RenderingServer.frame_post_draw
func jobs() -> void:
	while app.has_project.pid>0:await process_frame
	await settle()
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0];var plan: Array=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("plan.json")))
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("preparation-recovery");app.display_prefs_path=folder.path_join("preparation-prefs.cfg");app.recent_path=folder.path_join("preparation-recents.json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cold-cache" if "--read" in args else "writer-cache")
	var observations:=[]
	for item in plan:
		var project: String=folder.path_join(item.name+".has")
		if "--read" in args:
			var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join(item.name+"-expected.json")))
			app.new_project();app.has_project.open_file(project);await jobs()
			check(app.has_project.path==project and not app.dirty and app.current_world().objects.size()==1,item.name+" cold Open restores one isolated native asset")
			check(World.portable(app.renderer.world_state())==expected.world and app.keys==expected.camera,item.name+" cold Open retains exact native metadata and camera")
			for kind in ["unshaded","lit"]:
				app.lighting_choice.item_selected.emit(app.Renderer.Lighting.MODES.find(kind));await settle()
				var image: Image=await app.renderer.capture(app.keys,[],0,true)
				check(Storage.image_hash(image)==expected.pixels[kind],item.name+" cold "+kind+" pixels match exactly")
			continue
		app.new_project()
		var error: String=app.pose_editor.add_model(item.glb) if item.kind=="model" else app.load_scene(item.glb)
		check(error.is_empty() and app.current_world().objects.size()==1,item.name+" loads independently without overlapping environments")
		if not error.is_empty():continue
		app.world_selection.select_entity(app.last_import_id)
		if item.kind=="model":app.pose_editor.frame_model()
		else:
			app.frame_3d_scene()
			if item.name=="Flatgrass":
				var report: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(item.glb.get_base_dir().path_join("parameters.json")))
				check(app.source_import.apply_view(report),"Flatgrass uses its actual native player-start view")
		await settle()
		var camera: Camera3D=app.renderer.camera
		var key:=Timeline.key(0,camera.position,camera.quaternion,camera.fov);key["near"]=camera.near;key["far"]=camera.far
		app.keys=[key];app.video.duration_frames=48;app.set_frame(0)
		var pixels:={}
		for kind in ["unshaded","lit"]:
			app.lighting_choice.item_selected.emit(app.Renderer.Lighting.MODES.find(kind));await settle()
			var image: Image=await app.renderer.capture(app.keys,[],0,true);image.save_png(folder.path_join(item.name+"-"+kind+".png"));pixels[kind]=Storage.image_hash(image)
		app.lighting_choice.item_selected.emit(0);await settle()
		app.has_project.save_file(project,"packed");await jobs()
		check(app.has_project.path==project and not app.dirty,item.name+" normal packed Save creates a runnable reviewer project")
		var expected:={"world":World.portable(app.renderer.world_state()),"camera":app.keys,"pixels":pixels}
		FileAccess.open(folder.path_join(item.name+"-expected.json"),FileAccess.WRITE).store_string(JSON.stringify(expected,"",true,true))
		observations.append({"name":item.name,"source":app.current_world().objects[0].source,"sha256":app.current_world().objects[0].sha256,"project":project})
	var result:={"checks":checks,"failures":failures,"observations":observations,"mode":"reader" if "--read" in args else "writer"}
	FileAccess.open(folder.path_join("reader.json" if "--read" in args else "writer.json"),FileAccess.WRITE).store_string(JSON.stringify(result,"",true,true));print("OWNER_REVIEW "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
