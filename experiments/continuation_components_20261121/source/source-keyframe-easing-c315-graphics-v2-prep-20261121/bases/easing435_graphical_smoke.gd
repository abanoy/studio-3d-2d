extends "res://tests/camera_transform_smoke.gd"
# Authored, unrun integration controls. Uses only the repository's sample room.
const ColdWire=preload("res://tests/camera_cold_wire_oracle.gd")
func _initialize() -> void:
	create_timer(210).timeout.connect(func():push_error("Camera easing graphics watchdog");quit(2));call_deferred("run")
func button_named(parent: Node,text: String) -> Button:
	for child in parent.get_children():
		if child is Button and child.text==text:return child
		var found:=button_named(child,text)
		if found:return found
	return null
func reveal_click(control: Control) -> void:
	app.inspector_scroll.ensure_control_visible(control);await settle();await click(control)
func camera_matches(value: Dictionary) -> bool:
	var camera: Camera3D=app.renderer.camera
	return camera.position.is_equal_approx(value.position) and absf(camera.quaternion.dot(value.rotation))>0.999999 and absf(camera.fov-value.fov)<0.00001 and absf(camera.near-value.near)<0.00001 and absf(camera.far-value.far)<0.00001
func displayed_with_paint() -> Image:
	await settle()
	var image: Image=app.renderer.viewport.get_texture().get_image();image.convert(Image.FORMAT_RGBA8)
	var overlay: Dictionary=Drawing.composite_result(app.layers,app.frame,image.get_width(),image.get_height())
	if overlay.has("error"):return null
	image.blend_rect(overlay.image,Rect2i(Vector2i.ZERO,image.get_size()),Vector2i.ZERO)
	return image
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0]
	var reading: bool="--read" in OS.get_cmdline_user_args()
	var movies: bool="--movies" in OS.get_cmdline_user_args()
	var prefs:=ConfigFile.new();prefs.set_value("display","theme","light" if "--classic" in OS.get_cmdline_user_args() else "neon");prefs.set_value("display","percent",150 if "--150" in OS.get_cmdline_user_args() else 100);prefs.save(folder.path_join("prefs.cfg"))
	root.size=Vector2i(3440,1440) if "--150" in OS.get_cmdline_user_args() else Vector2i(1600,1000)
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery-cold" if reading else "recovery");app.recent_path=folder.path_join("recent.json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false
	app.has_project.cache_root=folder.path_join("cache-cold" if reading else "cache")
	app.set_advanced("--advanced" in OS.get_cmdline_user_args());await settle()
	var editor=app.camera_easing
	if reading:
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
		var originals: Array=FileAccess.open(folder.path_join("original-keys.var"),FileAccess.READ).get_var()
		var baked: Array=FileAccess.open(folder.path_join("baked-keys.var"),FileAccess.READ).get_var()
		var unbaked_path:=folder.path_join("Unbaked.has");app.has_project.open_file(unbaked_path);await wait_job()
		check(app.has_project.path==unbaked_path,"fresh reader opens unbaked packed project")
		check(ColdWire.matches(app.keys,expected.original_wire,originals,48) and editor.context.is_empty() and not editor.preview_active(),"cold unbaked keys exclude temporary recipe")
		check(Storage.image_hash(await app.renderer.capture(app.keys,app.layers,12,true))==expected.authored,"cold unbaked camera and paint match authored pixels")
		check(Storage.image_hash(Drawing.image(Drawing.cel_at(app.layers[1],0)))==expected.paint,"cold unbaked independent paint remains editable")
		var baked_path:=folder.path_join("Baked.has");app.has_project.open_file(baked_path);await wait_job()
		check(app.has_project.path==baked_path,"fresh reader opens baked packed project")
		check(ColdWire.matches(app.keys,expected.baked_wire,baked,48) and editor.context.is_empty() and not editor.preview_active(),"cold baked ordinary keys need no temporary recipe")
		check(Storage.image_hash(await app.renderer.capture(app.keys,app.layers,12,true))==expected.preview,"cold baked render matches prior preview pixels")
		check(FileAccess.get_sha256(app.source)==expected.source and Storage.image_hash(Drawing.image(Drawing.cel_at(app.layers[1],0)))==expected.paint,"cold source and independent drawing remain exact")
		print("EASING435_GRAPHICS_READ ",JSON.stringify({"checks":checks,"failures":failures}));await app.quit_studio();quit(0 if failures==0 else 1);return
	check(app.load_demo_room(),"repository room loads without native conversion")
	check(not app.renderer.empty_environment,"nonempty sample makes image comparison meaningful")
	var original_source:=FileAccess.get_sha256(app.source)
	var middle: Dictionary=Timeline.key(24,Vector3(0,1.8,4),Quaternion(Vector3.UP,-.075),56.,"linear")
	app.keys=[app.keys[0].duplicate(true),middle,app.keys[-1].duplicate(true)]
	for key in app.keys:key.interpolation="linear";key.near=.05;key.far=2000.
	var painting:=Drawing.blank(1920,1080);painting.fill_rect(Rect2i(760,420,120,90),Color.CYAN);Drawing.insert(app.layers[1],0,48,painting);app.changed()
	var paint:=Storage.image_hash(painting);var world: Dictionary=app.current_world().duplicate(true)
	app.mode.select(1);app.change_mode(1);app.set_frame(12);app.renderer.evaluate(app.keys,12)
	var authored: Image=await app.renderer.capture(app.keys,app.layers,12,true)
	var keys: Array=app.keys.duplicate(true);var history: int=app.history.size()
	var launch: Button=button_named(editor.panel,"Camera timing / easing…")
	check(is_instance_valid(launch),"timing button exists in actual camera inspector")
	await reveal_click(launch)
	check(editor.details.is_visible_in_tree() and editor.key_choice.item_count==3,"routed click reveals current key recipe")
	await type_number(editor.leave,"100")
	check(editor.leave.get_line_edit().text=="100","actual typing enters departure percentage")
	await reveal_click(button_named(editor.details,"Set timing on selected key"))
	check(editor.controls.size()==1 and editor.controls[0].leave==1. and app.keys==keys and app.history.size()==history,"routed set stages recipe without authoring keys")
	await reveal_click(button_named(editor.details,"Preview / Recalculate smooth timing"))
	check(editor.preview_active(),"routed recalculate starts temporary preview")
	check(app.keys==keys and app.history.size()==history,"visible preview preserves authored keys and history")
	var expected: Dictionary=editor.sample_preview(keys,12)
	check(camera_matches(expected),"visible camera matches temporary timing including lens ranges")
	var preview: Image=await displayed_with_paint()
	check(preview!=null and Storage.image_hash(preview)!=Storage.image_hash(authored),"live preview pixels differ from original authored shot")
	check(Storage.image_hash(await app.renderer.capture(keys,app.layers,12,true))==Storage.image_hash(authored),"unbaked final capture bypasses temporary preview")
	app.set_frame(12);await settle()
	var unbaked_path:=folder.path_join("Unbaked.has");app.has_project.save_file(unbaked_path,"packed");await wait_job()
	check(app.has_project.path==unbaked_path,"actual save writes unbaked packed project")
	check(editor.preview_active() and app.keys==keys and app.history.size()==history,"unbaked save leaves live recipe and keys separate")
	var unbaked_movie:="";var baked_movie:=""
	if movies:
		var before_export: Dictionary=app.renderer.view_state();var error: String=await app.export_movie(folder)
		check(error.is_empty(),"unbaked recipe exports real MP4")
		check(Storage.image_hash(Image.load_from_file(app.last_export_folder.path_join("frame_000013.png")))==Storage.image_hash(authored),"unbaked MP4 input uses authored frame")
		check(editor.preview_active() and app.keys==keys and app.renderer.view_state()==before_export,"export restores temporary preview view without baking")
		unbaked_movie=app.last_export_folder.path_join("movie.mp4")
	await reveal_click(button_named(editor.details,"Bake preview into camera keys (one Undo)"))
	check(app.keys.size()==26 and app.history.size()==history+1 and not editor.preview_active(),"routed Bake installs one ordinary key transaction")
	var baked: Array=app.keys.duplicate(true);var originals_kept:=true
	for original in keys:
		var matching: Array=app.keys.filter(func(key):return key.frame==original.frame)
		originals_kept=originals_kept and matching.size()==1 and matching[0]==original
	check(originals_kept,"Bake preserves exact original key dictionaries")
	check(Storage.image_hash(await app.renderer.capture(app.keys,app.layers,12,true))==Storage.image_hash(preview),"baked final pixels equal temporary live preview")
	app.undo();check(app.keys==keys and camera_matches(Timeline.sample(keys,12)),"real Undo restores original keys and visible camera")
	check(Storage.image_hash(await app.renderer.capture(app.keys,app.layers,12,true))==Storage.image_hash(authored),"Undo restores authored pixels")
	app.redo();check(app.keys==baked and camera_matches(Timeline.sample(baked,12)),"real Redo restores baked keys and visible camera")
	check(Storage.image_hash(await app.renderer.capture(app.keys,app.layers,12,true))==Storage.image_hash(preview),"Redo restores baked pixels")
	check(app.current_world()==world and FileAccess.get_sha256(app.source)==original_source and Storage.image_hash(painting)==paint,"camera timing preserves source world and independent paint")
	var baked_path:=folder.path_join("Baked.has");app.has_project.save_file(baked_path,"packed");await wait_job()
	check(app.has_project.path==baked_path,"actual save writes baked packed project")
	if movies:
		var before_export: Dictionary=app.renderer.view_state();var error: String=await app.export_movie(folder)
		check(error.is_empty(),"baked camera exports real MP4")
		check(Storage.image_hash(Image.load_from_file(app.last_export_folder.path_join("frame_000013.png")))==Storage.image_hash(preview),"baked MP4 input matches prior preview")
		check(app.renderer.view_state()==before_export and app.keys==baked,"baked export preserves edit view and keys")
		baked_movie=app.last_export_folder.path_join("movie.mp4")
	FileAccess.open(folder.path_join("original-keys.var"),FileAccess.WRITE).store_var(keys)
	FileAccess.open(folder.path_join("baked-keys.var"),FileAccess.WRITE).store_var(baked)
	FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify({"original_wire":JSON.parse_string(JSON.stringify(keys,"",true,true)),"baked_wire":JSON.parse_string(JSON.stringify(baked,"",true,true)),"authored":Storage.image_hash(authored),"preview":Storage.image_hash(preview),"paint":paint,"source":original_source},"",true,true))
	root.get_texture().get_image().save_png(folder.path_join("easing-inspector.png"))
	print("EASING435_GRAPHICS ",JSON.stringify({"checks":checks,"failures":failures,"movies":[unbaked_movie,baked_movie],"application_adopted":false}))
	await app.quit_studio();quit(0 if failures==0 else 1)
