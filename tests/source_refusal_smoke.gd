extends "res://tests/scenario_b_smoke.gd"
const Drawing=preload("res://src/drawing.gd")
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0]
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false
	check(app.load_demo_room(),"existing independent 3D scene is loaded before refused import")
	var ink:=Drawing.blank(1920,1080);ink.fill_rect(Rect2i(40,40,50,50),Color.RED);Drawing.insert(app.layers[1],0,48,ink);app.changed()
	var world: Dictionary=World.portable(app.current_world());var camera: Array=app.keys.duplicate(true);var paint:=Drawing.image(Drawing.cel_at(app.layers[1],0)).get_data();var history: int=app.history.size()
	app.import_actions.add(args[1],false,0);await settle()
	var confirmation: ConfirmationDialog
	for child in app.get_children():
		if child is ConfirmationDialog and child.title=="Import Source map" and child.visible:confirmation=child;break
	check(confirmation!=null,"native map review appears before an unsupported conversion")
	if confirmation:confirmation.confirmed.emit();await settle()
	check(app.source_import.pid>0,"confirmed native unsupported map starts actual owned worker")
	await jobs()
	check("exceeds64supported static lights" in app.status.text and "split or simplify" in app.status.text,"ordinary app error names the actual light limit and compatible-input action")
	check(World.portable(app.current_world())==world and app.keys==camera and Drawing.image(Drawing.cel_at(app.layers[1],0)).get_data()==paint and app.history.size()==history,"native refusal preserves existing world, camera, independent paint and Undo")
	var result:={"checks":checks,"failures":failures,"diagnostic":app.status.text,"conversion_folder":app.source_import.folder}
	FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("SOURCE_NATIVE_REFUSAL "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
