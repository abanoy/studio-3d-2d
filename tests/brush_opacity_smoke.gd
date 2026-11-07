extends SceneTree
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
const World=preload("res://src/world_document.gd")
const Timeline=preload("res://src/timeline.gd")
var app
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(150).timeout.connect(func():push_error("Brush watchdog");quit(2));call_deferred("run")
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
func mouse(point: Vector2,pressed: bool) -> void:
	var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.pressed=pressed
	var rect: Rect2=app.canvas.image_rect();event.position=rect.position+point/Vector2(1920,1080)*rect.size;app.canvas._gui_input(event)
func motion(point: Vector2) -> void:
	var event:=InputEventMouseMotion.new();event.button_mask=MOUSE_BUTTON_MASK_LEFT
	var rect: Rect2=app.canvas.image_rect();event.position=rect.position+point/Vector2(1920,1080)*rect.size;app.canvas._gui_input(event)
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0];var reader: bool="--read" in args
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery-reader" if reader else "recovery");app.recent_path=folder.path_join("recents-reader.json" if reader else "recents.json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cold-cache" if reader else "cache")
	var project:=folder.path_join("Opacity.has")
	if reader:
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
		app.has_project.open_file(project);await job()
		check(Storage.image_hash(Drawing.image(Drawing.cel_at(app.layers[1],0)))==expected.pixels,"fresh process reopens exact half-opacity pen and gentle eraser pixels")
		check(app.brush_opacity.value==100 and equal(app.keys,expected.keys) and equal(World.portable(app.current_world()),expected.world),"brush preference is session-only; authored world and camera keys survive exactly")
		FileAccess.open(folder.path_join("cold-state.json"),FileAccess.WRITE).store_string(JSON.stringify({"opacity":app.brush_opacity.value,"keys":app.keys,"world":World.portable(app.current_world())}))
		var reference: Image=await app.renderer.capture(app.keys,app.layers,0,true)
		check(Storage.image_hash(reference)==expected.render and FileAccess.get_sha256(project)==expected.project_hash,"cold preview matches writer and leaves original HAS unchanged")
		print("BRUSH_OPACITY_SMOKE ",JSON.stringify({"checks":checks,"failures":failures,"reader":true}));app.free();quit(0 if failures==0 else 1);return
	# Use an explicit common-format world and exactly representable moving shot.
	# Legacy single-scene saves deliberately reconstruct display names on loading;
	# arbitrary quaternion JSON doubles also have a separate known round-trip limit.
	check(app.restore_world(app.current_world()).is_empty(),"shared-format environment is installed for the drawing workflow")
	app.keys=[Timeline.key(0,Vector3(-1.5,2,5),Quaternion.IDENTITY,60),Timeline.key(48,Vector3(1.5,1.5,3),Quaternion.IDENTITY,52)]
	app.mode.select(0);app.change_mode(0);app.set_frame(0);app.layers[1].cels.clear();var image:=Drawing.blank(1920,1080);Drawing.insert(app.layers[1],0,24,image);app.history.clear();app.redo_history.clear();app.history_bytes=0
	var empty:=image.get_data();var world: Dictionary=World.portable(app.current_world());var keys: Array=app.keys.duplicate(true);var view: Dictionary=app.renderer.view_state();var source_hash:=FileAccess.get_sha256(app.source)
	check(app.brush_opacity.value==100 and app.brush_opacity.is_visible_in_tree(),"Simple Draw exposes opacity with existing full-strength default")
	app.brush_opacity.value=0;app.set_frame(24);var revision: int=app.recovery_revision;mouse(Vector2(300,400),true);mouse(Vector2(300,400),false)
	check(Drawing.cel_at(app.layers[1],24).is_empty() and app.history.is_empty() and revision==app.recovery_revision,"zero opacity creates no empty drawing, Undo step or recovery action")
	app.set_frame(0);app.brush_opacity.value=50;app.radius.value=12;app.color.color=Color.CYAN
	mouse(Vector2(300,400),true);motion(Vector2(650,400));var line:=image.get_data();motion(Vector2(300,400));motion(Vector2(650,400))
	check(app.drawing and app.history.is_empty() and line==image.get_data() and absf(image.get_pixel(500,400).a-.5)<.005,"routed mouse retraces keep half-alpha ink even before one stroke commits")
	var release:=InputEventMouseButton.new();release.button_index=MOUSE_BUTTON_LEFT;release.pressed=false;release.position=Vector2(-40,-40);app._input(release)
	check(not app.drawing and app.active_brush==null and app.before_tiles.is_empty() and app.history.size()==1,"release outside view commits one pixel Undo and frees transient brush state")
	app.undo();check(image.get_data()==empty,"one Undo restores exact original RGBA pixels");app.redo();check(image.get_data()==line,"Redo restores exact translucent edges")
	mouse(Vector2(300,550),true);app.brush_opacity.value=100;app.color.color=Color.RED;app.radius.value=30;motion(Vector2(650,550));mouse(Vector2(650,550),false)
	check(absf(image.get_pixel(500,550).a-.5)<.005 and image.get_pixel(500,550).g>.99 and image.get_pixel(500,570).a==0,"stroke captures color, radius and opacity until release")
	app.tool.select(1);app.brush_opacity.value=25;app.radius.value=12;app.color.color.a=0;mouse(Vector2(300,400),true);motion(Vector2(650,400));var erased:=image.get_data();motion(Vector2(300,400));mouse(Vector2(300,400),false)
	check(erased==image.get_data() and absf(image.get_pixel(500,400).a-.375)<.006,"quarter-strength eraser stays even and ignores pen color transparency")
	app.undo();check(absf(image.get_pixel(500,400).a-.5)<.005,"eraser Undo restores previous pen alpha");app.redo();check(image.get_data()==erased,"eraser Redo is exact")
	app.layers[1].opacity=.5;app.changed();check(absf(Drawing.composite(app.layers,0,1920,1080).get_pixel(500,400).a-.1875)<.006,"whole-layer opacity remains independent of brush strength")
	app.tool.select(0);app.brush_opacity.value=65;app.color.color=Color.CYAN;mouse(Vector2(800,550),true);motion(Vector2(950,550));app._notification(Window.NOTIFICATION_WM_WINDOW_FOCUS_OUT)
	check(not app.drawing and app.active_brush==null,"finishing a stroke releases masks and leaves its pixels committed")
	app.advanced_toggle.button_pressed=true;await settle();app.advanced_toggle.button_pressed=false;await settle();check(app.brush_opacity.value==65 and app.brush_opacity.is_visible_in_tree(),"returning to Simple preserves current brush setting")
	check(equal(world,World.portable(app.current_world())) and equal(keys,app.keys) and equal(view,app.renderer.view_state()) and FileAccess.get_sha256(app.source)==source_hash,"drawing keeps 3D scene, shot keys, editor view and source geometry unchanged")
	app.has_project.save_file(project,"packed");await job();check(FileAccess.file_exists(project),"ordinary packed HAS saves translucent strokes")
	app.set_frame(0);var reference: Image=await app.renderer.capture(app.keys,app.layers,0,true);var error: String=await app.export_movie(folder)
	check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000001.png")).get_data()==reference.get_data(),"normal MP4 frame is exactly the shared 3D plus translucent drawing preview")
	var expected:={"pixels":Storage.image_hash(image),"render":Storage.image_hash(reference),"keys":keys,"world":world,"project_hash":FileAccess.get_sha256(project)};FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify(expected))
	root.size=Vector2i(1280,720);await settle();app.inspector_scroll.ensure_control_visible(app.brush_opacity);await settle();root.get_texture().get_image().save_png(folder.path_join("brush-1280.png"));check(app.canvas.size.x>=500 and app.inspector_scroll.get_global_rect().encloses(app.brush_opacity.get_global_rect()),"scrolling exposes the complete opacity control in the1280pixel Simple workspace")
	var result:={"checks":checks,"failures":failures,"project":project,"movie":app.last_export_folder.path_join("movie.mp4"),"source_hash":source_hash};FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("BRUSH_OPACITY_SMOKE ",JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
