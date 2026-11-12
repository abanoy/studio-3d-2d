extends SceneTree
const World=preload("res://src/world_document.gd")
const Drawing=preload("res://src/drawing.gd")
var app
var checks:=0
var failures:=0
var folder: String
func _initialize() -> void:
	create_timer(100).timeout.connect(func():push_error("Workspace controls watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settled() -> void:
	for i in range(5):await process_frame
	await RenderingServer.frame_post_draw
func same(a,b) -> bool:return JSON.parse_string(JSON.stringify(a,"",true,true))==JSON.parse_string(JSON.stringify(b,"",true,true))
func middle(pressed: bool) -> void:
	var e:=InputEventMouseButton.new();e.button_index=MOUSE_BUTTON_MIDDLE;e.pressed=pressed;e.position=app.canvas.size/2;app.canvas._gui_input(e)
func move_middle(delta: Vector2) -> void:
	var e:=InputEventMouseMotion.new();e.relative=delta;e.position=app.canvas.size/2+delta;e.button_mask=MOUSE_BUTTON_MASK_MIDDLE;app.canvas._gui_input(e)
func click(control: Control) -> void:
	var point:=control.get_global_rect().get_center();var motion:=InputEventMouseMotion.new();motion.position=point;root.push_input(motion,true)
	for pressed in [true,false]:
		var event:=InputEventMouseButton.new();event.position=point;event.button_index=MOUSE_BUTTON_LEFT;event.pressed=pressed;root.push_input(event,true);await settled()
func run() -> void:
	folder=OS.get_cmdline_user_args()[0]
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recent.json");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false
	var ws=app.workspace_layout;ws.path=folder.path_join("layout.json")
	check(ws.locations==ws.DEFAULT and app.canvas.get_parent()!=null,"default workspace has World left, Properties right, Timeline below")
	app.load_scene(ProjectSettings.globalize_path("res://examples/tutorials/Practice room.glb"));var placement: Dictionary=app.import_actions.placement();placement.physics_on_import=false
	check(app.pose_editor.add_model(ProjectSettings.globalize_path("res://examples/tutorials/Practice figure.glb"),0,placement).is_empty(),"actual included rig imports into shared world")
	app.world_selection.select_entity(app.last_import_id);await settled()
	app.mode.select(0);app.change_mode(0);app.color.color=Color.CYAN
	var pen:=InputEventMouseButton.new();pen.button_index=MOUSE_BUTTON_LEFT;pen.pressed=true
	var rect: Rect2=app.canvas.image_rect();pen.position=rect.position+Vector2(80,80)/Vector2(1920,1080)*rect.size;app.canvas._gui_input(pen)
	var ink:=InputEventMouseMotion.new();ink.position=rect.position+Vector2(180,80)/Vector2(1920,1080)*rect.size;ink.button_mask=MOUSE_BUTTON_MASK_LEFT;app.canvas._gui_input(ink)
	pen.pressed=false;pen.position=ink.position;app.canvas._gui_input(pen)
	check(Drawing.image(Drawing.cel_at(app.layers[1],0)).get_pixel(120,80).a>0,"actual canvas coordinates still paint an independent visible Ink cel")
	app.mode.select(2);app.change_mode(2);await settled()
	# This fixture asserts the retained Focus paper-pan behavior. Setup camera
	# navigation has its own independent scene_view_smoke interaction checks.
	app.scene_view.set_setup(false,false)
	var id: String=app.world_selection.selected;var world: Dictionary=World.portable(app.current_world());var shots: Array=app.keys.duplicate(true);var view: Dictionary=app.renderer.view_state();var history: int=app.history.size();var operation: int=app.pose_editor.operation.selected
	middle(true);middle(false);await settled()
	check(app.pose_editor.operation.selected==1-operation and app.world_selection.selected==id,"middle click cycles Rotate/Move without deselecting the model")
	middle(true);middle(false);check(app.pose_editor.operation.selected==operation,"repeated middle click cycles back")
	check(same(World.portable(app.current_world()),world) and app.keys==shots and app.renderer.view_state()==view and app.history.size()==history,"tool cycling changes no pose/key/shot/view or Undo history")
	var pan: Vector2=app.canvas.pan;middle(true);move_middle(Vector2(20,10));middle(false)
	check(app.canvas.pan==pan+Vector2(20,10) and app.pose_editor.operation.selected==operation,"middle drag still pans in Pose and does not cycle tools")
	app.canvas.pan=pan;app.mode.select(1);app.change_mode(1);var before: Dictionary=app.renderer.view_state();middle(true);move_middle(Vector2(0,20));middle(false)
	check(app.renderer.view_state()!=before and app.pose_editor.operation.selected==operation,"middle drag still dollies in Scene mode")
	app.renderer.restore_view(view);middle(true);middle(false)
	check(app.mode.selected==2 and app.renderer.view_state()==view,"middle click from Scene reveals the pose tool without moving the camera")
	app.mode.select(0);app.change_mode(0);operation=app.pose_editor.operation.selected;middle(true);middle(false)
	check(app.mode.selected==0 and app.pose_editor.operation.selected==operation,"Draw keeps its own middle-button navigation")
	app.mode.select(2);app.change_mode(2);middle(true);app.release_mouse();middle(false)
	check(app.canvas.middle_pending.is_empty() and app.pose_editor.operation.selected==operation,"Escape/focus cancellation cannot create a late tool switch")
	app.layer_editor.open();await settled()
	check(app.layer_editor.dialog.visible and not app.layer_editor.dialog.exclusive and not app.has_dialog(app),"Layers is a resizable non-blocking editing panel")
	var advanced: bool=app.advanced_mode;await click(app.advanced_toggle)
	check(app.advanced_mode!=advanced and app.layer_editor.dialog.visible,"actual main-window button remains clickable while Layers stays open")
	app.layer_choice.item_selected.emit(0);await settled()
	check(app.layer_editor.name_edit.text==app.layers[0].name and app.layer_editor.listing.get_item_metadata(app.layer_editor.listing.get_selected_items()[0])==0,"open modeless Layers follows a selection changed in the main inspector")
	app.layer_choice.item_selected.emit(1);await settled()
	app.layer_editor.name_edit.select_all();await settled()
	check(app.layer_editor.name_edit.get_theme_color("font_selected_color")==Color("163854"),"selected field text is dark against pale blue in the child panel")
	check(app.get_window().theme==app.theme and app.theme.get_color("font_selected_color","TextEdit")==Color("163854"),"native/embedded child windows and multiline selection inherit readable text colors")
	root.get_texture().get_image().save_png(folder.path_join("modeless-layers.png"));app.layer_editor.dialog.hide();app.set_advanced(false)
	app.show_project_options();await settled();check(not app.project_options.exclusive and not app.has_dialog(app),"Project options permits main-window interaction too");app.project_options.hide()
	app.confirm_action("Keep real confirmations modal",func():pass);await settled()
	check(app.has_dialog(app),"actual decision confirmation still blocks conflicting shortcuts")
	for child in app.get_children():
		if child is ConfirmationDialog and child.visible:child.hide();child.queue_free()
	await settled()
	app.source_browser.open();await settled();check(not app.source_browser.window.exclusive and not app.has_dialog(app),"installed content browser no longer disables the main window")
	advanced=app.advanced_mode;await click(app.advanced_toggle);check(app.advanced_mode!=advanced,"main toolbar still responds with installed browser open")
	app.source_browser.locations();await settled();var locations: Window
	for child in app.source_browser.window.get_children():
		if child is Window and child.title=="Local content locations":locations=child
	check(locations!=null and not locations.exclusive and not app.has_dialog(app),"content-location settings also permit main-window interaction")
	if locations:locations.hide();locations.queue_free()
	app.source_browser.close();await settled();app.set_advanced(false)
	app.tutorials.open_catalog();await settled();var catalog: Window
	for child in app.get_children():
		if child is Window and child.visible and child.title=="Tutorials":catalog=child
	check(catalog!=null and not catalog.exclusive and not app.has_dialog(app),"tutorial browsing remains non-blocking; starting a lesson still has its separate discard check")
	if catalog:catalog.hide();catalog.queue_free()
	app.changed();app.autosave_tick(true);await preload("res://tests/recovery_wait.gd").checkpoint(app);app.show_recovery(true);await settled();var recovery: Window
	for child in app.get_children():
		if child is Window and child.visible and child.title=="Recovery History":recovery=child
	check(recovery!=null and not recovery.exclusive and not app.has_dialog(app),"recovery history browsing permits main-window interaction without restoring anything")
	if recovery:recovery.hide();recovery.queue_free()
	var state: Dictionary=World.portable(app.current_world());shots=app.keys.duplicate(true);history=app.history.size();view=app.renderer.view_state();var original: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	var canvas_id: int=app.canvas.get_instance_id();var timeline_id: int=app.timeline.get_instance_id();var controls_id: int=app.controls.get_instance_id()
	ws.vertical.split_offset-=70;ws.horizontal.split_offset+=35;ws.right_split.split_offset-=25;await settled()
	check(app.canvas.size.x>0 and app.timeline.size.x>0 and ws.vertical.get_child_count()==2,"real workspace splitters resize the live view and panels")
	ws.dock("world","right");await settled()
	check(ws.locations.right=="world" and ws.locations.left=="properties" and ws.panels.world.get_parent()==ws.tabs.right,"docking swaps panels instead of losing an occupied panel")
	# Real heading press/motion/release through the main viewport input router.
	var handle: Control=ws.panels.timeline.get_child(0).get_child(0)
	var press_at:=handle.get_global_rect().get_center();var drop_at: Vector2=ws.slots.left.get_global_rect().get_center()
	var hover:=InputEventMouseMotion.new();hover.position=press_at;root.push_input(hover,true)
	var press:=InputEventMouseButton.new();press.button_index=MOUSE_BUTTON_LEFT;press.pressed=true;press.position=press_at;root.push_input(press,true);await settled()
	var motion:=InputEventMouseMotion.new();motion.position=drop_at;motion.relative=drop_at-press_at;motion.button_mask=MOUSE_BUTTON_MASK_LEFT;root.push_input(motion,true);await settled()
	press.pressed=false;press.position=drop_at;root.push_input(press,true);await settled()
	print("AFTER_HEADING_DRAG ",JSON.stringify(ws.state()))
	check("timeline" in ws.groups.left and "properties" in ws.groups.left and ws.tabs.left.get_child_count()==2,"dragging a panel heading onto another panel creates selectable tabs")
	ws.float_panel("properties");await settled()
	check(ws.floating.has("properties") and not ws.floating.properties.exclusive and not app.has_dialog(app),"floating Properties is a movable, non-blocking tool window")
	var floating: Window=ws.floating.properties;var size_before: Vector2i=floating.size;floating.size+=Vector2i(60,30);floating.position+=Vector2i(25,20);await settled()
	check(floating.size!=size_before and not floating.unresizable,"floating gadget can resize and reposition")
	floating.close_requested.emit();await settled();check(not ws.floating.has("properties") and ws.panels.properties.get_parent()==ws.tabs.left,"closing a floating panel docks it back rather than removing controls")
	check(app.canvas.get_instance_id()==canvas_id and app.timeline.get_instance_id()==timeline_id and app.controls.get_instance_id()==controls_id,"layout operations preserve exact live canvas, timeline and inspector nodes")
	check(same(World.portable(app.current_world()),state) and app.keys==shots and app.renderer.view_state()==view and app.history.size()==history,"layout moves leave scene, authored keys, view and Undo history unchanged")
	var image: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	check(image.get_data()==original.get_data(),"layout operations preserve exact final 3D/2D output pixels")
	ws.save();var saved: Dictionary=ws.state();ws.reset();await settled();check(ws.locations==ws.DEFAULT,"Reset workspace restores familiar Simple layout")
	# reset schedules a future write; reload the existing explicit saved state first.
	ws.timer.stop();ws.load_layout();await settled();check(ws.locations==saved.slots,"saved docking preferences reload without a project-format change")
	ws.reset();await settled();app.get_window().size=Vector2i(1200,760);await settled()
	var visible: Rect2=root.get_visible_rect();var screen: Image=root.get_texture().get_image()
	var timeline_scroll: ScrollContainer=ws.panels.timeline.get_node("TimelineContentScroll")
	print("WORKSPACE_BOUNDS ",JSON.stringify({"window":str(app.get_window().size),"visible":str(visible),"canvas":str(app.canvas.get_global_rect()),"timeline":str(app.timeline.get_parent().get_global_rect()),"footer":str(app.status.get_parent().get_global_rect())}))
	check(app.canvas.get_global_rect().end.x<=visible.end.x and timeline_scroll.get_global_rect().end.y<=visible.end.y and screen.get_width()<=app.get_window().size.x and screen.get_height()<=app.get_window().size.y,"default resizable layout remains accessible in logical and physical bounds at1200x760")
	app.mode.select(0);app.change_mode(0);app.color.color=Color.MAGENTA;await settled()
	var mapped_rect: Rect2 = app.canvas.image_rect()
	for pixel in [Vector2i(960,540),Vector2i(480,810),Vector2i(1440,270)]:
		var point: Vector2 = app.canvas.global_position + mapped_rect.position + mapped_rect.size * Vector2(pixel) / Vector2(1920,1080)
		var hover_canvas := InputEventMouseMotion.new();hover_canvas.position=point;root.push_input(hover_canvas,true)
		for down in [true,false]:
			var touch := InputEventMouseButton.new();touch.position=point;touch.button_index=MOUSE_BUTTON_LEFT;touch.pressed=down
			root.push_input(touch,true);await settled()
		var ink_pixel: Color = Drawing.image(Drawing.cel_at(app.layers[1],0)).get_pixelv(pixel)
		check(ink_pixel.r>0.9 and ink_pixel.b>0.9 and ink_pixel.g<0.1 and ink_pixel.a>0.9,"resized workspace routes viewport pointer to Ink pixel "+str(pixel))
	var expected: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	for window_case in [{"size":Vector2i(1120,720),"scale":1.},{"size":Vector2i(1400,900),"scale":1.25}]:
		app.get_window().content_scale_factor=window_case.scale;app.get_window().size=window_case.size;await settled()
		var area: Rect2=root.get_visible_rect();var footer: Rect2=app.status.get_parent().get_global_rect()
		check(app.canvas.get_global_rect().end.x<=area.end.x and timeline_scroll.get_global_rect().end.y<=area.end.y and footer.end.y<=area.end.y and footer.end.x<=area.end.x,"same-aspect resize and125percent interface keep camera timeline and footer reachable: "+str(window_case))
		timeline_scroll.ensure_control_visible(app.timeline.get_parent());await settled()
		check(timeline_scroll.get_global_rect().encloses(app.timeline.get_parent().get_global_rect()),"compressed Timeline scrolls its complete interactive ruler into view")
		var scroll: ScrollContainer=ws.panels.world.get_node("WorldContentScroll");var asset_actions: Array=app.find_children("*","Button",true,false).filter(func(node):return node.text=="Save asset .has...")
		check(asset_actions.size()==1 and scroll.is_visible_in_tree(),"compact World retains asset action inside a scrollable dock")
		if asset_actions.size()==1:
			scroll.ensure_control_visible(asset_actions[0]);await settled();check(scroll.get_global_rect().encloses(asset_actions[0].get_global_rect()),"World action can be brought into the visible dock without changing layout")
		check((await app.renderer.capture(app.keys,app.layers,0,true)).get_data()==expected.get_data(),"responsive dock and interface scale preserve exact final3D/2D output")
	app.get_window().content_scale_factor=1.;app.get_window().size=Vector2i(1200,760);await settled()
	root.get_texture().get_image().save_png(folder.path_join("workspace-1200.png"));app.get_window().size=Vector2i(1400,900);await settled();root.get_texture().get_image().save_png(folder.path_join("workspace.png"))
	var file:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify({"checks":checks,"failures":failures}));file.close();app.free();await process_frame
	print("WORKSPACE_CONTROLS "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
