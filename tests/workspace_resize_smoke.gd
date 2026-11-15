extends SceneTree
const World=preload("res://src/world_document.gd")
var app
var folder: String
var checks:=0
var failures:=0
var measurements:=[]
func _initialize() -> void:
	create_timer(80).timeout.connect(func():push_error("Workspace resize watchdog");quit(2));call_deferred("run")
func settle() -> void:
	for i in range(8):await process_frame
	await RenderingServer.frame_post_draw
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func drag(delta: float) -> void:
	var point: Vector2=app.workspace_layout.vertical.get_drag_area_control().get_global_rect().get_center()
	var hover:=InputEventMouseMotion.new();hover.position=point;root.push_input(hover,true);await settle()
	var press:=InputEventMouseButton.new();press.position=point;press.button_index=MOUSE_BUTTON_LEFT;press.pressed=true;root.push_input(press,true);await settle()
	var motion:=InputEventMouseMotion.new();motion.position=point+Vector2(0,delta);motion.relative=Vector2(0,delta);motion.button_mask=MOUSE_BUTTON_MASK_LEFT;root.push_input(motion,true);await settle()
	press.position=motion.position;press.pressed=false;root.push_input(press,true);await settle()
func run() -> void:
	folder=OS.get_cmdline_user_args()[0]
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recent.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false
	if OS.get_cmdline_user_args().size()>1:
		app.has_project.cache_root=folder.path_join("cache");app.has_project.open_file(OS.get_cmdline_user_args()[1])
		while app.has_project.pid>0:await process_frame
		check(app.current_world().objects.size()==1,"actual native review project opens")
		app.world_selection.select_entity(app.current_world().objects[0].id)
	else:
		var placement: Dictionary=app.import_actions.placement();placement.physics_on_import=false
		check(app.pose_editor.add_model(ProjectSettings.globalize_path("res://examples/tutorials/Practice figure.glb"),0,placement).is_empty() and app.current_world().objects.size()==1,"actual included rig opens for resize checks");app.world_selection.select_entity(app.last_import_id)
	app.mode.select(2);app.change_mode(2)
	var ws=app.workspace_layout;ws.path=folder.path_join("layout.json")
	var world: Dictionary=World.portable(app.current_world());var history: int=app.history.size();var view: Dictionary=app.renderer.view_state()
	var ids:=[app.canvas.get_instance_id(),app.timeline.get_instance_id(),app.controls.get_instance_id()]
	var image: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	for window_size in [Vector2i(3440,1440),Vector2i(1400,900),Vector2i(1200,760)]:
		root.size=window_size;await settle();ws.reset();await settle()
		check(root.get_visible_rect().size.is_equal_approx(Vector2(window_size)),"100 percent uses actual window pixels rather than automatic magnification")
		var before: float=app.canvas.size.y
		check(ws.slots.right.size.x<root.get_visible_rect().size.x*.3,"Properties default leaves scene width at "+str(window_size))
		await drag(200)
		var after: float=app.canvas.size.y
		check(after>before+60,"actual downward mouse drag enlarges scene at "+str(window_size))
		check(ws.slots.bottom.size.y>=ws.slots.bottom.get_combined_minimum_size().y,"compressed Timeline respects its scrollable minimum")
		check(ws.panels.timeline.find_child("TimelineContentScroll",true,false) is ScrollContainer,"Timeline retains scroll access to its live controls")
		var scroll: ScrollContainer=ws.panels.timeline.find_child("TimelineContentScroll",true,false)
		check(scroll.get_child(0).size.x>scroll.size.x-24,"Timeline content fills the available width without wrapping every transport button")
		root.get_texture().get_image().save_png(folder.path_join("resized-%d.png"%window_size.x))
		ws.save();var saved: Dictionary=ws.state();ws.vertical.split_offset-=80;await settle();check(ws.load_layout(),"saved layout loads");await settle()
		check(ws.state()==saved and absf(app.canvas.size.y-after)<2,"resized scene survives layout reload")
		await drag(-160);check(app.canvas.size.y<after-60,"actual upward mouse drag restores Timeline space")
		measurements.append({"window":str(window_size),"canvas_before":before,"canvas_after":after,"bottom_minimum":ws.slots.bottom.get_combined_minimum_size().y})
	check(World.portable(app.current_world())==world and app.history.size()==history and app.renderer.view_state()==view,"layout does not change pose, camera or Undo history")
	check(ids==[app.canvas.get_instance_id(),app.timeline.get_instance_id(),app.controls.get_instance_id()],"layout retains the exact live scene, Timeline and Properties controls")
	var after_image: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	check(image.get_data()==after_image.get_data(),"scene render pixels remain identical after resizing")
	var result:={"checks":checks,"failures":failures,"measurements":measurements};FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE).store_string(JSON.stringify(result,"\t"));print("WORKSPACE_RESIZE "+JSON.stringify(result));app.free();quit(1 if failures else 0)
