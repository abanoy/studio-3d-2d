extends "res://tests/movement_path_smoke.gd"
const Drawing=preload("res://src/drawing.gd")
func _initialize() -> void:
	create_timer(90).timeout.connect(func():push_error("Exposure history watchdog");quit(2));call_deferred("run")
func run() -> void:
	folder=OS.get_cmdline_user_args()[0].path_join("exposure-history");DirAccess.make_dir_recursive_absolute(folder);app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false
	app.active_layer=1;app.set_frame(0);app.create_cel(false)
	var layer: Dictionary=app.layers[1];var original: Image=layer.cels[0].image;original.fill(Color(.2,.6,.8,.5));Drawing.touch(original);layer.cels[0].duration=12
	for at in [24,36]:
		var other:=Drawing.blank(1920,1080);Drawing.insert(layer,at,48,other);layer.cels[-1].duration=12
	app.changed();var old: int=app.history.size();var bytes: int=app.history_bytes;var first: Dictionary=app.history[0];var pixels:=original.get_data();var live: Array=[]
	for cel in layer.cels:live.append([cel.id,cel.start,cel.duration,Drawing.image(cel)])
	for i in range(48):app.exposure.value=6 if i%2==0 else 12;app.set_exposure()
	check(app.history.size()==old+48 and is_same(app.history[0],first),"48 duration edits preserve earlier drawing history under64MiB budget")
	check(app.history_bytes==bytes+48*512,"48 edits charge24576bytes regardless of three1080p rasters")
	for i in range(48):app.undo()
	check(app.history.size()==old and app.redo_history.size()==48 and layer.cels[0].duration==12,"all48 duration edits Undo without consuming earlier drawing creation")
	for i in range(48):app.redo()
	check(app.history.size()==old+48 and layer.cels[0].duration==12,"all48 duration edits Redo")
	var intact:=original.get_data()==pixels
	for i in range(3):intact=intact and layer.cels[i].id==live[i][0] and layer.cels[i].start==live[i][1] and layer.cels[i].duration==live[i][2] and is_same(layer.cels[i].image,live[i][3])
	check(intact,"all three cel identities, ranges, Images and original RGBA remain exact")
	var count: int=app.history.size();var revision: int=app.recovery_revision
	for length in [0,-1]:app.cel_timing.set_exposure(layer.id,layer.cels[0].id,length)
	check(app.history.size()==count and app.recovery_revision==revision and layer.cels[0].duration==12,"invalid lengths preserve duration/history/revision")
	var context: Dictionary=app.cel_timing.begin(layer.id,layer.cels[0].id,0);app.timeline.moving_cel=layer.cels[0].id;app.timeline.cel_context=context;app.exposure.value=6;app.set_exposure()
	check(app.history.size()==count and layer.cels[0].duration==12,"latched timeline gesture refuses conflicting duration edit")
	app.timeline.cancel_cel();app.exporting=true;app.set_exposure();app.exporting=false
	check(app.history.size()==count and layer.cels[0].duration==12,"export refuses duration edit")
	print("CEL_EXPOSURE_HISTORY ",JSON.stringify({"checks":checks,"failures":failures,"edits":48,"charged_bytes":48*512}));await app.quit_studio();quit(0 if failures==0 else 1)
