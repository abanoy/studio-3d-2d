extends SceneTree
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
const World=preload("res://src/world_document.gd")
const Timeline=preload("res://src/timeline.gd")
var app
var checks:=0
var failures:=0
var event_ms: Array=[]
func _initialize() -> void:
	create_timer(160).timeout.connect(func():push_error("Pressure watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settle() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func job() -> void:
	while app.has_project.pid>0:await process_frame
	await settle()
func equal(a,b) -> bool:return JSON.parse_string(JSON.stringify(a,"",true,true))==JSON.parse_string(JSON.stringify(b,"",true,true))
func point(event: InputEventMouse,p: Vector2) -> void:
	var rect: Rect2=app.canvas.image_rect();event.position=rect.position+p/Vector2(1920,1080)*rect.size;var start:=Time.get_ticks_usec();app.canvas._gui_input(event);event_ms.append((Time.get_ticks_usec()-start)/1000.0)
func button(p: Vector2,pressed: bool) -> void:
	var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.pressed=pressed;point(event,p)
func pressure(p: Vector2,value: float) -> void:
	var event:=InputEventMouseMotion.new();event.button_mask=MOUSE_BUTTON_MASK_LEFT;event.pressure=value;point(event,p)
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0];var reader: bool="--read" in args
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery-cold" if reader else "recovery");app.recent_path=folder.path_join("recents-cold.json" if reader else "recents.json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache-cold" if reader else "cache")
	var project:=folder.path_join("Pressure.has")
	if reader:
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")));app.has_project.open_file(project);await job()
		check(Storage.image_hash(Drawing.image(Drawing.cel_at(app.layers[1],24)))==expected.pixels,"fresh Open restores exact tapered pen and eraser pixels")
		check(not app.brush_pressure.button_pressed and equal(app.keys,expected.keys) and equal(World.portable(app.current_world()),expected.world),"session pressure default and saved standard world/shot remain separate")
		var preview: Image=await app.renderer.capture(app.keys,app.layers,24,true)
		check(Storage.image_hash(preview)==expected.render and FileAccess.get_sha256(project)==expected.project_hash,"cold render matches writer exactly and leaves original HAS unchanged")
		print("BRUSH_PRESSURE_SMOKE ",JSON.stringify({"checks":checks,"failures":failures,"reader":true}));app.free();quit(0 if failures==0 else 1);return
	check(app.restore_world(app.current_world()).is_empty(),"common-format environment is available for pressure drawing")
	app.keys=[Timeline.key(0,Vector3(-1.5,2,5),Quaternion.IDENTITY,60),Timeline.key(48,Vector3(1.5,1.5,3),Quaternion.IDENTITY,52)]
	app.mode.select(0);app.change_mode(0);app.layers[1].cels.clear();var blank:=Drawing.blank(1920,1080);Drawing.insert(app.layers[1],0,24,blank);app.set_frame(0);app.history.clear();app.redo_history.clear();app.history_bytes=0
	var world: Dictionary=World.portable(app.current_world());var keys: Array=app.keys.duplicate(true);var view: Dictionary=app.renderer.view_state();var source_hash:=FileAccess.get_sha256(app.source);var initial_accumulated:=Input.use_accumulated_input
	check(not app.brush_pressure.button_pressed,"pressure is off by default for ordinary mouse drawing")
	app.radius.value=16;app.color.color=Color.CYAN;button(Vector2(200,250),true);pressure(Vector2(400,250),0);button(Vector2(400,250),false)
	check(blank.get_pixel(300,260).a>.99 and Input.use_accumulated_input==initial_accumulated,"ordinary zero-pressure mouse motions retain full brush size and input settings")
	app.brush_pressure.button_pressed=true;app.set_frame(24);view=app.renderer.view_state();var revision: int=app.recovery_revision;var history: int=app.history.size();button(Vector2(300,400),true);pressure(Vector2(350,400),0)
	check(app.drawing and app.stroke_image==null and Drawing.cel_at(app.layers[1],24).is_empty() and not Input.use_accumulated_input,"tablet press/zero pressure waits without a cel and temporarily disables event accumulation")
	app.autosave_tick(true);check(app.history.size()==history and app.recovery_revision==revision,"waiting pressure makes no edit or Undo/recovery action")
	button(Vector2(350,400),false);check(not app.drawing and app.history.size()==history and Input.use_accumulated_input==initial_accumulated and app.status.text.contains("No pen pressure"),"missing pressure finishes cleanly with mouse-fallback guidance")
	button(Vector2(300,400),true);app.undo();check(not app.drawing and Drawing.cel_at(app.layers[1],24).is_empty() and blank.get_pixel(300,250).a==0 and Input.use_accumulated_input==initial_accumulated,"Undo while waiting ends the pending tablet gesture and undoes the previous real edit")
	app.redo();check(blank.get_pixel(300,250).a>.99,"Redo still restores the preceding mouse stroke after pending tablet cancellation")
	var retained: Array=app.layers[1].cels.duplicate()
	for i in range(31):app.layers[1].cels.append({"id":"capacity-"+str(i),"start":0,"duration":1,"image":blank})
	button(Vector2(300,400),true);pressure(Vector2(300,400),.5)
	check(not app.drawing and Drawing.cel_at(app.layers[1],24).is_empty() and app.history.size()==history and Input.use_accumulated_input==initial_accumulated and app.status.text.contains("32"),"lazy cel allocation refuses the cel limit without leaking state or hiding its error")
	app.layers[1].cels=retained;button(Vector2(300,400),true);app.set_frame(0)
	check(not app.drawing and Input.use_accumulated_input==initial_accumulated and Drawing.cel_at(app.layers[1],24).is_empty(),"changing frames finishes a waiting gesture without inventing artwork")
	app.set_frame(24);view=app.renderer.view_state()
	app.canvas.zoom=1.3;app.canvas.pan=Vector2(17,-9);await settle();app.radius.value=32;app.brush_opacity.value=50;button(Vector2(300,400),true);pressure(Vector2(300,400),.1)
	var image: Image=Drawing.image(Drawing.cel_at(app.layers[1],24))
	check(image.get_pixel(300,400).a>.49 and image.get_pixel(300,410).a==0 and app.history.size()==history+1,"first light pressure creates only a small dot and one new-cel command")
	pressure(Vector2(450,400),.2);pressure(Vector2(600,400),0);pressure(Vector2(900,400),.8);pressure(Vector2(1100,400),1)
	check(image.get_pixel(750,400).a==0 and image.get_pixel(1000,420).a>.49,"pressure lift breaks the path; resumed contact and stronger size map through zoom/pan")
	var before_invalid:=Storage.image_hash(image);pressure(Vector2(1300,400),NAN);check(Storage.image_hash(image)==before_invalid,"nonfinite pressure is ignored without changing the image")
	app.brush_pressure.button_pressed=false;pressure(Vector2(1200,400),0)
	check(image.get_pixel(1200,400).a==0,"changing the toggle during a stroke does not change its captured tablet behavior")
	var release:=InputEventMouseButton.new();release.button_index=MOUSE_BUTTON_LEFT;release.pressed=false;release.position=Vector2(-40,-40);app._input(release)
	var painted:=image.get_data();check(app.history.size()==history+2 and app.active_brush==null and Input.use_accumulated_input==initial_accumulated,"outside release commits one pixel step and restores event accumulation")
	app.undo();check(image.get_data()==Drawing.blank(1920,1080).get_data(),"one pixel Undo removes the complete pressure stroke");app.redo();check(image.get_data()==painted,"Redo restores tapered alpha exactly")
	app.brush_pressure.button_pressed=true;app.tool.select(1);app.brush_opacity.value=25;button(Vector2(900,400),true);pressure(Vector2(900,400),.2);pressure(Vector2(1100,400),1);button(Vector2(1100,400),false)
	check(absf(image.get_pixel(1050,400).a-.375)<.006 and image.get_pixel(900,420).a>.49,"pressure eraser keeps gentle strength while its footprint widens")
	var erased:=image.get_data();app.undo();check(image.get_data()==painted,"pressure eraser Undo is exact");app.redo();check(image.get_data()==erased,"pressure eraser Redo is exact")
	app.tool.select(0);app.brush_opacity.value=100;button(Vector2(400,600),true);pressure(Vector2(400,600),2);pressure(Vector2(500,600),-1);button(Vector2(500,600),false)
	check(image.get_pixel(400,630).a>.99 and image.get_pixel(400,635).a==0 and image.get_pixel(500,600).a==0,"finite pressure clamps to0-1 without enlarging the selected radius or bridging negative input")
	Input.use_accumulated_input=false;button(Vector2(800,600),true);pressure(Vector2(850,600),.5);app._notification(Window.NOTIFICATION_WM_WINDOW_FOCUS_OUT)
	check(not app.drawing and not Input.use_accumulated_input and app.active_brush==null,"focus completion restores a previously disabled accumulation setting")
	Input.use_accumulated_input=initial_accumulated
	app.radius.value=1;button(Vector2(1400,600),true);pressure(Vector2(1400,600),.001);button(Vector2(1400,600),false)
	check(image.get_pixel(1400,600).a>0 and image.get_pixel(1402,600).a==0,"positive pressure retains a drawable half-pixel minimum at the smallest brush size")
	app.advanced_toggle.button_pressed=true;await settle();app.advanced_toggle.button_pressed=false;await settle();check(app.brush_pressure.button_pressed,"Simple/Advanced preserves the current pressure choice")
	check(equal(keys,app.keys) and equal(world,World.portable(app.current_world())) and equal(view,app.renderer.view_state()) and FileAccess.get_sha256(app.source)==source_hash,"pressure drawing preserves world, authored shot, editor camera and original geometry")
	app.has_project.save_file(project,"packed");await job();var reference: Image=await app.renderer.capture(app.keys,app.layers,24,true);var error: String=await app.export_movie(folder)
	check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000025.png")).get_data()==reference.get_data(),"ordinary MP4 uses exact preview pixels for the pressure cel")
	var expected:={"pixels":Storage.image_hash(image),"render":Storage.image_hash(reference),"world":world,"keys":keys,"project_hash":FileAccess.get_sha256(project)};FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify(expected))
	root.size=Vector2i(1280,720);await settle();app.inspector_scroll.ensure_control_visible(app.brush_pressure);await settle();root.get_texture().get_image().save_png(folder.path_join("pressure-1280.png"));check(app.inspector_scroll.get_global_rect().encloses(app.brush_pressure.get_global_rect()),"complete pressure toggle is reachable in the laptop-sized Properties panel")
	var drivers: Array=[]
	if OS.get_name()=="Windows":
		for i in range(DisplayServer.tablet_get_driver_count()):drivers.append(DisplayServer.tablet_get_driver_name(i))
	var maximum:=0.0
	for value in event_ms:maximum=maxf(maximum,value)
	var result:={"checks":checks,"failures":failures,"project":project,"movie":app.last_export_folder.path_join("movie.mp4"),"max_routed_event_ms":maximum,"overlay_ms":app.elapsed_overlay_ms,"tablet_drivers":drivers,"tablet_current":DisplayServer.tablet_get_current_driver() if OS.get_name()=="Windows" else "","physical_tablet_tested":false};FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("BRUSH_PRESSURE_SMOKE ",JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
