extends SceneTree
const Drawing = preload("res://src/drawing.gd")
const Storage = preload("res://src/storage.gd")
var checks := 0
var failures := 0

func _initialize() -> void:
	create_timer(80).timeout.connect(func(): push_error("New-scene watchdog expired"); quit(2))
	call_deferred("run")

func check(ok: bool, text: String) -> void:
	checks += 1; print(("PASS " if ok else "FAIL ")+text)
	if not ok: failures += 1

func bright_pixels(image: Image) -> int:
	var bytes := image.get_data(); var count := 0
	for i in range(0,bytes.size(),4):
		if bytes[i]>5 or bytes[i+1]>5 or bytes[i+2]>5: count+=1
	return count

func run() -> void:
	var folder := ProjectSettings.globalize_path("res://output/new-scene/run_%d" % Time.get_ticks_usec())
	DirAccess.make_dir_recursive_absolute(folder)
	var app = load("res://main.tscn").instantiate()
	app.recovery_root=folder.path_join("recovery")
	root.add_child(app); await process_frame
	check(app.source.is_empty() and app.renderer.world_runtime!=null and app.renderer.world_runtime.instances.is_empty() and app.renderer.empty_environment and app.renderer.model==null,"normal startup is an empty world without placeholder geometry or selected actor")
	check(app.mode.selected==1 and app.pose_editor.tree.get_selected()==null and not app.advanced_mode,"startup is Simple free-camera workspace with nothing selected")
	check(app.keys.size()==1 and app.keys[0].frame==0 and app.frame==0 and not app.dirty and app.history.is_empty(),"new project has one stationary initial shot and clean empty history")
	check(app.has_project.path.is_empty() and app.project_folder.is_empty() and app.layers[0].cels.is_empty() and app.layers[1].cels.is_empty() and app.audio_clip.is_empty(),"new project is unsaved with independent empty layers and no audio")
	var source: String=app.source
	var original_world: Dictionary=app.renderer.world_state()
	var preview: Image=await app.renderer.capture(app.keys,app.layers,0)
	var final: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	preview.save_png(folder.path_join("grid-preview.png")); final.save_png(folder.path_join("empty-final.png"))
	check(bright_pixels(preview)>10000 and bright_pixels(final)==0,"white perspective grid is visible in editor but final empty world is black")
	check(app.renderer.editor_grid.position.y==0 and app.renderer.editor_grid.mesh.size==Vector2(256,256),"grid is a bounded horizontal 3D reference plane")
	check(app.renderer.editor_grid.visible and not app.renderer.capturing_final,"capture restores editor guide after hiding it from final output")
	var keys:=JSON.stringify(app.keys)
	app.camera_button(MOUSE_BUTTON_LEFT,true,true); app.camera_motion(Vector2(15,-5)); app.camera_button(MOUSE_BUTTON_LEFT,false)
	check(not app.navigating and JSON.stringify(app.keys)==keys,"free-camera gesture releases normally without changing shot keys")
	app.renderer.evaluate(app.keys,0)
	app.mode.select(0); app.change_mode(0); app.create_cel(false)
	Drawing.stroke(Drawing.cel_at(app.layers[1],0).image,Vector2(100,100),Vector2(250,100),6,Color.RED,false); app.changed()
	var with_drawing: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	check(bright_pixels(with_drawing)>0 and app.renderer.world_state()==original_world,"drawing over empty world stays independent of empty 3D document")
	var dirty_layers:=JSON.stringify(app.layers)
	app.new_dialog(); var prompt: ConfirmationDialog
	for child in app.get_children():
		if child is ConfirmationDialog and child.visible: prompt=child
	check(prompt!=null,"New protects unsaved edits with a real confirmation")
	if prompt: prompt.canceled.emit()
	await process_frame
	check(app.source==source and JSON.stringify(app.layers)==dirty_layers and app.dirty,"cancelling New preserves original document")
	var has=app.has_project; has.cache_root=folder.path_join("cache")
	var project:=folder.path_join("empty-with-drawing.has")
	has.save_file(project,"packed")
	while has.pid>0: await process_frame
	check(has.path==project and not app.dirty,"empty world and editable drawing save in existing packed HAS")
	var saved_hash:=FileAccess.get_sha256(project)
	has.open_file(project)
	while has.pid>0: await process_frame
	check(app.renderer.empty_environment and has.path==project and app.renderer.world_runtime.instances.is_empty(),"packed empty world reopens with no fabricated source asset")
	var reopened: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	check(reopened.get_data()==with_drawing.get_data(),"packed reopen retains exact black background and independent drawing pixels")
	var error: String=await app.export_movie(folder)
	var exported:=Image.load_from_file(app.last_export_folder.path_join("frame_000001.png"))
	check(error.is_empty() and exported.get_data()==with_drawing.get_data(),"empty-world drawing exports MP4 without editor grid and matches preview")
	check(FileAccess.get_sha256(project)==saved_hash,"render preserves manually saved HAS bytes")
	var movie: String=app.last_export_folder.path_join("movie.mp4")
	app.changed(); app.new_dialog()
	for child in app.get_children():
		if child is ConfirmationDialog and child.visible: child.confirmed.emit(); break
	await process_frame
	check(app.renderer.empty_environment and app.has_project.path.is_empty() and app.history.is_empty() and app.layers[1].cels.is_empty() and not app.dirty,"confirmed New clears prior content/save identity/history and opens clean world")
	app.load_demo_room()
	check(not app.renderer.empty_environment and app.keys.size()==2 and app.mode.selected==0 and app.has_project.path.is_empty(),"original sample room remains an explicit unsaved example")
	var legacy_video: Dictionary=app.video.duplicate(); legacy_video.erase("world_background")
	var legacy_folder:=folder.path_join("legacy-project")
	var legacy_error:=Storage.save_project(legacy_folder,legacy_video,app.keys,app.layers,app.source,0)
	check(legacy_error.is_empty() and app.open_project(legacy_folder) and app.renderer.world_environment.environment.background_color==Color("263646"),"older project without new background setting retains its original rendered background")
	var manifest_path:=legacy_folder.path_join("project.json")
	var manifest_bytes:=FileAccess.get_file_as_bytes(manifest_path)
	var invalid: Dictionary=JSON.parse_string(manifest_bytes.get_string_from_utf8()); invalid.video.world_background="invalid"
	var manifest:=FileAccess.open(manifest_path,FileAccess.WRITE);manifest.store_string(JSON.stringify(invalid));manifest.close()
	var prior_source: String=app.source
	check(not app.open_project(legacy_folder) and app.source==prior_source and app.renderer.world_environment.environment.background_color==Color("263646"),"invalid optional background setting rejects open before replacing live document")
	manifest=FileAccess.open(manifest_path,FileAccess.WRITE);manifest.store_buffer(manifest_bytes);manifest.close()
	app.new_project(); await process_frame; await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(folder.path_join("new-workspace.png"))
	var report:={"checks":checks,"failures":failures,"folder":folder,"movie":movie}
	var file:=FileAccess.open(ProjectSettings.globalize_path("res://output/new-scene-result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(report));file.close()
	print("NEW_SCENE_SMOKE "+JSON.stringify(report));quit(0 if failures==0 else 1)
