extends "res://tests/movement_path_smoke.gd"
const Storage=preload("res://src/storage.gd")
func _initialize() -> void:
	create_timer(120).timeout.connect(func():push_error("Output settings watchdog");quit(2));call_deferred("run")
func choose(index: int) -> void:app.output_size.select(index);app.output_size.item_selected.emit(index)
func run() -> void:
	folder=OS.get_cmdline_user_args()[0];app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	if "--read" in OS.get_cmdline_user_args():
		app.has_project.open_file(folder.path_join("Settings.has"));await wait_job();check(app.video.get("output_size")=="540p" and app.selected_output_size()=="540p","fresh packed Open restores saved delivery choice")
		print("OUTPUT_SETTINGS_READ "+JSON.stringify({"checks":checks,"failures":failures}));await app.quit_studio();quit(0 if failures==0 else 1);return
	check(app.new_project() and app.selected_output_size()=="1080p","new project defaults to1080p delivery")
	var before: Dictionary=app.video.duplicate(true);var generation: int=app.physics_editor.generation;choose(1)
	check(app.video.get("output_size")=="720p" and app.dirty and app.history.size()==1,"delivery choice belongs to dirty project with Undo")
	if "--probe" in OS.get_cmdline_user_args():
		print("OUTPUT_SETTINGS_PROBE "+JSON.stringify({"checks":checks,"failures":failures}));await app.quit_studio();quit(0 if failures==0 else 1);return
	app.undo();check(app.selected_output_size()=="1080p" and app.video==before,"Undo restores default and original video metadata")
	app.redo();check(app.selected_output_size()=="720p" and app.video.get("output_size")=="720p","Redo restores saved delivery choice")
	check(app.physics_editor.generation==generation,"delivery history leaves independent physics unchanged")
	choose(2);var source: Dictionary=app.video.duplicate(true);var count: int=app.history.size();app.exporting=true;choose(1);app.exporting=false
	check(app.video==source and app.history.size()==count,"export-time control event cannot mutate saved settings/history")
	app.sync_output_size();check(app.selected_output_size()=="540p","control refresh reflects authoritative saved choice")
	app.autosave_tick(true);await preload("res://tests/recovery_wait.gd").checkpoint(app);await settled();var recovered:=Storage.load_project(app.recovery_root.path_join(app.recovery_session));check(not recovered.has("error") and recovered.video.get("output_size")=="540p","real recovery checkpoint preserves saved delivery setting")
	app.has_project.save_file(folder.path_join("Settings.has"),"packed");await wait_job();check(FileAccess.file_exists(folder.path_join("Settings.has")),"ordinary packed save includes delivery settings")
	var direct:=folder.path_join("direct");var error:=Storage.save_project(direct,app.video,app.keys,app.layers,"",0,{}, {},{},false,app.current_world());check(error.is_empty() and Storage.load_project(direct).video.output_size=="540p","directory save/load preserves selected size")
	var bad: Dictionary=app.video.duplicate(true);bad.output_size="broken";var manifest:=FileAccess.get_sha256(direct.path_join("project.json"));error=Storage.save_project(direct,bad,app.keys,app.layers,"",0,{}, {},{},false,app.current_world());check(not error.is_empty() and FileAccess.get_sha256(direct.path_join("project.json"))==manifest,"invalid saved output size cannot replace previous manifest")
	var data: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(direct.path_join("project.json")));data.video.output_size=17;FileAccess.open(direct.path_join("bad.json"),FileAccess.WRITE).store_string(JSON.stringify(data));check(Storage.load_project(direct,"bad.json").has("error") and not Storage.readable_manifest(direct.path_join("bad.json")),"invalid typed size refuses both normal and readable-manifest paths")
	var current: Dictionary=app.video.duplicate(true);check(not app.open_project(direct,"bad.json") and app.video==current and app.selected_output_size()=="540p","refused Open preserves active choice and document")
	var child: String=app.sequence_editor.new_sequence("Output child");app.sequence_editor.enter(child);choose(1);app.sequence_editor.return_to_parent();check(app.selected_output_size()=="540p","parent delivery setting survives child navigation")
	app.sequence_editor.enter(child);check(app.selected_output_size()=="720p","child scene restores its own delivery setting");app.sequence_editor.return_to_parent()
	app.new_project();check(app.selected_output_size()=="1080p" and not app.video.has("output_size"),"successful New resets choice to default")
	print("OUTPUT_SETTINGS_SMOKE "+JSON.stringify({"checks":checks,"failures":failures}));await app.quit_studio();quit(0 if failures==0 else 1)
