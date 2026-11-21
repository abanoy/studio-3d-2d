extends SceneTree
# Real app controls and history, with no GPU readback or native asset import.
const Timeline=preload("res://src/timeline.gd")
var checks:=0
var failures:=0
var app

func check(ok: bool,text: String) -> void:
	checks+=1
	if not ok:failures+=1
	print(("PASS " if ok else "FAIL ")+text)

func button_named(parent: Node,text: String) -> Button:
	for child in parent.get_children():
		if child is Button and child.text==text:return child
		var found: Button=button_named(child,text)
		if found:return found
	return null

func _initialize() -> void:
	create_timer(45).timeout.connect(func():push_error("Camera easing app watchdog");quit(2))
	call_deferred("run")

func run() -> void:
	var args: PackedStringArray=OS.get_cmdline_user_args()
	var folder: String=args[0]
	var classic: bool="--classic" in args
	var prefs:=ConfigFile.new()
	prefs.set_value("display","theme","light" if classic else "neon")
	prefs.set_value("display","percent",100)
	prefs.save(folder.path_join("prefs.cfg"))
	root.size=Vector2i(1600,1000);root.gui_embed_subwindows=true
	app=load("res://main.tscn").instantiate()
	app.display_prefs_path=folder.path_join("prefs.cfg")
	app.recovery_root=folder.path_join("recovery")
	app.recent_path=folder.path_join("recent.json")
	root.add_child(app)
	for i in range(4):await process_frame
	app.home.hide();app.autosave_enabled.button_pressed=false
	app.mode.select(1);app.change_mode(1);app.set_advanced(false)
	app.keys=[Timeline.key(0,Vector3(0,1,4),Quaternion.IDENTITY,60.,"linear"),Timeline.key(12,Vector3(12,1,4),Quaternion.IDENTITY,50.,"linear"),Timeline.key(24,Vector3(24,1,4),Quaternion.IDENTITY,40.,"linear")]
	app.set_frame(6);app.renderer.evaluate(app.keys,6)
	var original: Array=app.keys.duplicate(true)
	var world: Dictionary=app.current_world().duplicate(true)
	var history: int=app.history.size()
	var editor=app.camera_easing
	var launch: Button=button_named(editor.panel,"Camera timing / easing…")
	check(launch!=null and launch.is_visible_in_tree(),"timing is available in Simple camera controls")
	launch.pressed.emit()
	check(editor.details.is_visible_in_tree() and editor.key_choice.item_count==3,"button opens the actual current camera keys")
	check(not editor.arrive.editable and editor.leave.editable and "frame 0 → 12" in editor.neighbors.text,"first key identifies its outgoing neighbor")
	# Enter text directly in the real SpinBox, then press Preview without Set.
	editor.leave.get_line_edit().text="100"
	button_named(editor.details,"Preview / Recalculate smooth timing").pressed.emit()
	check(editor.preview_active() and editor.controls.size()==1 and editor.controls[0].leave==1.,"Preview reads pending percentage text without an extra Set")
	check(app.keys==original and app.history.size()==history,"temporary timing leaves keys and history untouched")
	check(app.renderer.camera.position.x<6.,"actual camera responds to slower departure")
	editor.key_choice.select(1);editor.key_choice.item_selected.emit(1)
	await process_frame # Let SpinBox display the newly selected key before typing.
	check("frame 0 → 12" in editor.neighbors.text and "frame 12 → 24" in editor.neighbors.text,"middle key labels both independent neighboring intervals")
	editor.arrive.get_line_edit().text="75"
	button_named(editor.details,"Preview / Recalculate smooth timing").pressed.emit()
	var expected: Dictionary=editor.sample_preview(app.keys,6)
	check(editor.controls.size()==2 and editor.controls[1].arrive==0.75,"recalculate retains the previous key and applies arrival")
	check(app.renderer.camera.position==expected.position,"visible camera uses the recalculated sample")
	app.set_advanced(true);app.set_advanced(false)
	check(editor.preview_active() and editor.details.is_visible_in_tree(),"workspace presentation preserves the timing recipe")
	button_named(editor.details,"Bake preview into camera keys (one Undo)").pressed.emit()
	var baked: Array=app.keys.duplicate(true)
	check(baked.size()==14 and app.history.size()==history+1 and not editor.preview_active(),"Bake authors ordinary keys in one history transaction")
	check(app.keys[0]==original[0] and app.keys[12]==original[1] and app.keys[13]==original[2],"Bake preserves all original camera keys")
	check(Timeline.sample(baked,6).position==expected.position,"ordinary baked camera reproduces the temporary sample")
	app.undo()
	check(app.keys==original and app.renderer.camera.position==Timeline.sample(original,6).position,"real Undo restores original keys and the camera")
	app.redo()
	check(app.keys==baked and app.renderer.camera.position==Timeline.sample(baked,6).position,"real Redo restores baked keys and the camera")
	check(app.current_world()==world,"camera timing preserves the independent world")
	editor.open();editor.leave.get_line_edit().text="50";editor.preview()
	var before_discard: Array=app.keys.duplicate(true)
	editor.discard()
	check(not editor.preview_active() and editor.context.is_empty() and app.keys==before_discard and app.history.size()==history+1,"Discard removes only the temporary recipe")
	app.set_frame(18);editor.open()
	check(editor.key_choice.get_selected_id()==12,"opening between keys selects the current interval's starting key")
	print("CAMERA_EASING_APP ",JSON.stringify({"checks":checks,"failures":failures,"theme":"classic" if classic else "neon","gpu_readback":false}))
	await app.quit_studio()
	quit(0 if failures==0 else 1)
