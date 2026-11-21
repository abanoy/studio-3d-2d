extends "res://tests/import_capability_app_headless.gd"
# Authored UNRUN private UI/packed-cold follow-up; synthetic repository room only.
func click_control(control: Control) -> void:
	var win: Window=control.get_window();var position: Vector2=control.get_global_rect().get_center()
	if win.is_embedded():position+=Vector2(win.position)
	var target: Window=root if win.is_embedded() else win
	var motion:=InputEventMouseMotion.new();motion.position=position;target.push_input(motion,true)
	for down in [true,false]:
		var event:=InputEventMouseButton.new();event.position=position;event.button_index=MOUSE_BUTTON_LEFT;event.pressed=down;target.push_input(event,true);await process_frame
	await settle()
func run() -> void:
	var args:=OS.get_cmdline_user_args()
	if args.is_empty() or DisplayServer.get_name()=="headless":push_error("Use a private graphical job with fresh owned data");quit(2);return
	var folder: String=args[0];var reading: bool="--read" in args
	root.size=Vector2i(3440,1440) if "--150" in args else Vector2i(1600,1000)
	await setup_app(folder)
	var info=app.pose_editor.import_capabilities;var packed: String=folder.path_join("Import info.has")
	if reading:
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
		app.has_project.open_file(packed);await wait_job()
		check(app.has_project.path==packed,"fresh process opens copied packed report project")
		var actor: RefCounted=select_first();info._process(0.)
		check(info.report_for(actor)==expected.report,"packed replay preserves the complete raw report including unknown properties")
		check(FileAccess.get_sha256(actor.data.source)==expected.source,"cold source is restored from managed packed assets")
		app.inspector_scroll.ensure_control_visible(info.button);await settle();await click_control(info.button)
		check(is_instance_valid(info.window) and info.window.visible and info.matches(),"fresh reader exposes the persistent report through the ordinary action")
		check(info.summary_text.text==expected.text and not info.window.exclusive,"fresh read-only text retains exact warnings omissions and actions without modal")
		var before: Dictionary=app.current_world().duplicate(true);var keys: Array=app.keys.duplicate(true);var history: int=app.history.size();info.close()
		check(app.current_world()==before and app.keys==keys and app.history.size()==history,"cold report inspection and Close preserve authored data")
		print("IMPORT_CAPABILITY_GUI_READ "+JSON.stringify({"checks":checks,"failures":failures,"synthetic_only":true,"native_conversion_qualified":false,"application_adopted":false}));await shutdown();return
	var loaded: bool=app.load_demo_room()
	if loaded:loaded=app.restore_world(app.current_world()).is_empty()
	check(loaded,"actual graphical sample loads through existing source-independent World")
	var actor: RefCounted=select_first();actor.data.metadata.native_parameters=report_fixture();app.changed();info._process(0.)
	var before: Dictionary=app.current_world().duplicate(true);var keys: Array=app.keys.duplicate(true);var history: int=app.history.size()
	app.inspector_scroll.ensure_control_visible(info.button);await settle();await click_control(info.button)
	check(is_instance_valid(info.window) and info.window.visible and info.matches(),"routed pointer opens the current asset report")
	check(info.summary_text.text.contains("Unknown fixture") and info.summary_text.text.contains("budget): 42"),"native widget displays warnings and concrete omissions")
	var text: String=info.summary_text.text;info.window.size=Vector2i(800,600);await settle()
	check(info.window.size==Vector2i(800,600) and not info.window.unresizable,"native report window accepts resizing without scaling the interface")
	check(app.current_world()==before and app.keys==keys and app.history.size()==history,"actual popup and resize do not author world or camera edits")
	info.close();app.has_project.save_file(packed,"packed");await wait_job()
	check(app.has_project.path==packed,"ordinary packed save stores report with its managed asset")
	var report: Dictionary=info.report_for(actor)
	check(report==report_fixture() and Summary.plain_text(Summary.summarize(report,actor))==text,"save leaves raw report and read-only display content unchanged")
	var expected:={"report":report,"source":FileAccess.get_sha256(actor.data.source),"text":text}
	var file:=FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE)
	if file==null:push_error("Cannot write bounded synthetic expectation");quit(2);return
	file.store_string(JSON.stringify(expected,"",true,true));file.flush();file.close()
	print("IMPORT_CAPABILITY_GUI "+JSON.stringify({"checks":checks,"failures":failures,"synthetic_only":true,"native_conversion_qualified":false,"application_adopted":false}));await shutdown()
