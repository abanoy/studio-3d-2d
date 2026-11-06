extends "res://tests/movement_path_smoke.gd"
const Drawing=preload("res://src/drawing.gd")
func _initialize() -> void:
	create_timer(90).timeout.connect(func():push_error("Cel timing/tool arbitration watchdog");quit(2));call_deferred("run")
func run() -> void:
	folder=OS.get_cmdline_user_args()[0];app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false
	app.mode.select(0);app.change_mode(0);var image:=Drawing.blank(1920,1080);image.fill_rect(Rect2i(100,100,80,40),Color.CYAN);Drawing.touch(image);Drawing.insert(app.layers[1],0,48,image);app.layers[1].cels[0].duration=12;app.changed();app.set_frame(4)
	var source: PackedByteArray=image.get_data();var view=app.timeline;var point:=Vector2(view.x(4),view.layer_y(1)+12);var target:=Vector2(view.x(28),point.y)
	for tool in [4,3]:
		app.set_frame(4)
		if tool==4:
			app.drawing_selection_editor.arm();app.drawing_selection_editor.snapshot();app.drawing_selection_editor.selected=Rect2i(100,100,80,40);app.drawing_selection_editor.outline(app.drawing_selection_editor.selected)
		else:app.tool.select(3)
		await settled();var history: int=app.history.size();var before: Array=app.layers[1].cels.duplicate(true)
		var press:=InputEventMouseButton.new();press.button_index=MOUSE_BUTTON_LEFT;press.pressed=true;event_at(view,point,press);await process_frame
		check(app.drawing_selection_editor.context.is_empty() and app.canvas.selection_preview==null,"exposure start clears pending pixel preview for tool%d" % tool)
		var motion:=InputEventMouseMotion.new();motion.button_mask=MOUSE_BUTTON_MASK_LEFT;event_at(view,target,motion);await process_frame
		check(view.cel_gesture_active() and view.cel_preview==24,"exposure preview starts with drawing tool%d selected" % tool)
		var escape:=InputEventKey.new();escape.keycode=KEY_ESCAPE;escape.pressed=true;root.push_input(escape,true);await process_frame
		check(not view.cel_gesture_active(),"first Escape cancels exposure before other tool%d handlers" % tool)
		var release:=InputEventMouseButton.new();release.button_index=MOUSE_BUTTON_LEFT;event_at(view,target,release);await settled()
		check(app.layers[1].cels==before and app.history.size()==history and image.get_data()==source,"tool%d cancellation cannot commit timing or change RGBA/history" % tool)
		check(app.tool.selected==tool,"timing navigation preserves chosen drawing tool%d" % tool)
		# Keep each independent probe on the identical initial source range.
		while app.history.size()>history:app.undo()
	print("CEL_TIMING_TOOLS ",JSON.stringify({"checks":checks,"failures":failures}));await app.quit_studio();quit(0 if failures==0 else 1)
