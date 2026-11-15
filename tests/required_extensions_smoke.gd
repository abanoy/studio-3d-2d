extends SceneTree
const World=preload("res://src/world_document.gd")
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func _initialize() -> void:
	create_timer(90).timeout.connect(func():quit(2));call_deferred("run")
func settle() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0];var native: String=args[1]
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recent.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false
	app.load_demo_room();check(app.pose_editor.add_model(ProjectSettings.globalize_path("res://examples/tutorials/Practice figure.glb")).is_empty(),"ordinary supported model loads through the same extension gate")
	app.create_cel(false);var cel: Dictionary=Drawing.cel_at(app.layers[1],0);var image:=Drawing.edit_image(cel);image.image.fill_rect(Rect2i(20,20,30,30),Color.CYAN);Drawing.touch(image.image);app.changed();await settle()
	var world: Dictionary=World.portable(app.renderer.world_state());var keys: Array=app.keys.duplicate(true);var history: int=app.history.size();var paint:=Storage.image_hash(Drawing.image(cel));var original:=FileAccess.get_sha256(native)
	app.source_import.start(native,true)
	check(app.source_import.pid>0,"native VRM worker starts for required-feature refusal case")
	while app.source_import.pid>0:await process_frame
	await settle()
	check(app.status.text.contains("HAS_unknown_required_for_test") and app.status.text.contains("compatible export"),"ordinary native import names the unsupported required feature and action")
	check(World.portable(app.renderer.world_state())==world and app.keys==keys and app.history.size()==history,"refused native import preserves entire world, authored camera and Undo history")
	check(Storage.image_hash(Drawing.image(Drawing.cel_at(app.layers[1],0)))==paint and FileAccess.get_sha256(native)==original,"refusal preserves editable independent pixels and original file")
	var result:={"checks":checks,"failures":failures,"status":app.status.text};FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("REQUIRED_EXTENSIONS_APP "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
