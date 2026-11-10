extends "res://tests/workspace_resize_smoke.gd"
func pointer(window: Window,point: Vector2,kind: String) -> void:
	if kind=="motion":
		var event:=InputEventMouseMotion.new();event.position=point;event.global_position=point;event.button_mask=MOUSE_BUTTON_MASK_LEFT;window.push_input(event,true)
	else:
		var event:=InputEventMouseButton.new();event.position=point;event.global_position=point;event.button_index=MOUSE_BUTTON_LEFT;event.pressed=kind=="press";window.push_input(event,true)
	await settle()
func heading(id: String,destination: Vector2) -> void:
	var panel: Control=app.workspace_layout.panels[id];var window:=panel.get_window();var point: Vector2=panel.get_child(0).get_child(0).get_global_rect().get_center()
	await pointer(window,point,"motion");await pointer(window,point,"press")
	var local:=destination
	if window!=root:local=(Vector2(root.position-window.position)+destination*root.content_scale_factor)/window.content_scale_factor
	await pointer(window,local,"motion");await pointer(window,local,"release")
func resize_side(split: SplitContainer,delta: float) -> void:
	var point:=split.get_drag_area_control().get_global_rect().get_center()
	await pointer(root,point,"motion");await pointer(root,point,"press");await pointer(root,point+Vector2(delta,0),"motion");await pointer(root,point+Vector2(delta,0),"release")
func run() -> void:
	folder=OS.get_cmdline_user_args()[0];var reader: bool="--read" in OS.get_cmdline_user_args()
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recent.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;root.size=Vector2i(1800,1100);await settle()
	var ws=app.workspace_layout;ws.path=folder.path_join("layout.json")
	if reader:
		app.has_project.cache_root=folder.path_join("reader-cache");app.has_project.open_file(folder.path_join("scene.has"))
		while app.has_project.pid>0:await process_frame
		check(ws.load_layout(),"cold reader restores saved workspace");await settle()
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
		check(JSON.parse_string(JSON.stringify(ws.state()))==expected.layout,"cold reader restores exact serialized tabs, selected tab, split offsets and floating geometry")
		check(ws.floating.has("world") and ws.floating.world.force_native and ws.groups.top.size()==2,"cold reader recreates independent World window and top tab group")
		check((await app.renderer.capture(app.keys,app.layers,0,true)).get_data()==Image.load_from_file(folder.path_join("before.png")).get_data(),"cold workspace replay preserves exact scene pixels")
	else:
		var legacy:={"format":"studio_workspace_1","slots":{"left":"world","right":"properties","bottom":"timeline"},"split":[-367,0,-120]}
		FileAccess.open(ws.path,FileAccess.WRITE).store_string(JSON.stringify(legacy));check(ws.load_layout() and ws.groups.left==["world"] and ws.groups.top.is_empty(),"owner's previous three-dock layout migrates to the tab-capable format")
		var tabbed:={"format":"studio_workspace_2","slots":{"left":"world","right":"","bottom":"","top":"timeline"},"groups":{"left":["world"],"right":[],"bottom":[],"top":["timeline","properties"]},"split":[-234,0,0,180],"selected":{"top":"Properties"},"floating":{"world":{"position":[120,160],"size":[420,520]}}}
		FileAccess.open(ws.path,FileAccess.WRITE).store_string(JSON.stringify(tabbed));check(ws.load_layout() and ws.floating.has("world") and ws.tabs.top.get_child_count()==2 and ws.tabs.top.get_current_tab_control()==ws.panels.properties,"previous v2 tab group, selection and native floating window migrate to nested layout v3")
		var unchanged: Dictionary=ws.state();var invalid:=unchanged.duplicate(true);invalid.groups.left=["world","world"]
		FileAccess.open(ws.path,FileAccess.WRITE).store_string(JSON.stringify(invalid));check(not ws.load_layout() and ws.state()==unchanged,"invalid duplicated panel layout leaves live controls unchanged")
		var placement: Dictionary=app.import_actions.placement();placement.physics_on_import=false
		check(app.pose_editor.add_model(ProjectSettings.globalize_path("res://examples/tutorials/Practice figure.glb"),0,placement).is_empty() and app.current_world().objects.size()==1,"actual included rig opens for docking checks");app.world_selection.select_entity(app.last_import_id);app.mode.select(2);app.change_mode(2);ws.reset();await settle()
		var state: Dictionary=World.portable(app.current_world());var view: Dictionary=app.renderer.view_state();var history: int=app.history.size();var ids:=[app.canvas.get_instance_id(),app.timeline.get_instance_id(),app.controls.get_instance_id()]
		var image: Image=await app.renderer.capture(app.keys,app.layers,0,true);image.save_png(folder.path_join("before.png"))
		var width: float=ws.slots.left.size.x;await resize_side(ws.horizontal,140);check(ws.slots.left.size.x>width+100,"actual World divider mouse drag widens the left bar")
		check(app.world_selection.tree.size.x>ws.slots.left.size.x-24,"World tree fills the widened dock instead of staying clipped in a fixed narrow column")
		var world_scroll: ScrollContainer=ws.panels.world.get_node("WorldContentScroll")
		check(world_scroll.get_child(0).size.x>=world_scroll.size.x-20,"World actions fill their scroll body width")
		root.get_texture().get_image().save_png(folder.path_join("world-expanded.png"))
		await resize_side(ws.horizontal,-100);check(ws.slots.left.size.x<width+70,"actual World divider mouse drag narrows the left bar again")
		await heading("world",app.canvas.get_global_rect().get_center());check(ws.floating.has("world") and ws.floating.world.force_native and not ws.floating.world.exclusive,"dragging World into open space detaches a real nonblocking native window")
		if ws.floating.has("world"):
			ws.floating.world.position+=Vector2i(70,40);ws.floating.world.size+=Vector2i(80,30);await settle()
			await heading("world",ws.vertical.get_global_rect().position+Vector2(12,150));check(not ws.floating.has("world") and ws.panels.world.get_parent()==ws.tabs.left,"dragging detached World onto the main left edge docks the same live panel")
		await heading("timeline",ws.slots.right.get_global_rect().get_center());check(ws.groups.right.has("timeline") and ws.groups.right.has("properties") and ws.tabs.right.tabs_visible,"body drop creates real selectable Timeline and Properties tabs")
		root.get_texture().get_image().save_png(folder.path_join("tabs-before-click.png"))
		var bar: TabBar=ws.tabs.right.get_tab_bar();var index: int=ws.panels.properties.get_index();var click: Vector2=bar.global_position+bar.get_tab_rect(index).get_center();await pointer(root,click,"motion");await pointer(root,click,"press");await pointer(root,click,"release")
		print("TAB_CLICK ",JSON.stringify({"bar":str(bar.get_global_rect()),"click":str(click),"index":index,"current":ws.tabs.right.current_tab,"names":ws.tabs.right.get_children().map(func(c):return str(c.name))}))
		check(ws.tabs.right.get_current_tab_control()==ws.panels.properties and ws.panels.properties.is_visible_in_tree(),"actual tab click reveals Properties controls")
		var tab_point: Vector2=bar.global_position+bar.get_tab_rect(ws.panels.timeline.get_index()).get_center()
		var top_point: Vector2=ws.vertical.get_global_rect().position+Vector2(ws.vertical.size.x*.5,12)
		await pointer(root,tab_point,"motion");await pointer(root,tab_point,"press");await pointer(root,top_point,"motion");await pointer(root,top_point,"release")
		check(ws.groups.top.has("timeline") and ws.slots.top.visible,"dragging the actual Timeline tab label snaps it above the scene")
		ws.tab_panel("properties","timeline");ws.float_panel("world");await settle();ws.floating.world.size=Vector2i(420,520);ws.floating.world.position=DisplayServer.screen_get_usable_rect().position+Vector2i(120,160);await settle()
		await create_timer(.5).timeout
		var saved_geometry: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(ws.path))
		check(saved_geometry.floating.world.position==[120.,160.] and saved_geometry.floating.world.size==[420.,520.],"floating geometry saves automatically after window movement")
		check(ws.tabs.top.get_child_count()==2 and ws.floating.has("world"),"top tab group and floating World coexist")
		check(World.portable(app.current_world())==state and app.renderer.view_state()==view and app.history.size()==history,"docking leaves world, camera and Undo history unchanged")
		check(ids==[app.canvas.get_instance_id(),app.timeline.get_instance_id(),app.controls.get_instance_id()],"all original live editor nodes survive docking")
		check((await app.renderer.capture(app.keys,app.layers,0,true)).get_data()==image.get_data(),"docking preserves exact final render pixels")
		app.has_project.save_file(folder.path_join("scene.has"),"packed")
		while app.has_project.pid>0:await process_frame
		ws.timer.stop();ws.save();FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify({"layout":ws.state()}))
		root.get_texture().get_image().save_png(folder.path_join("docking.png"))
	var result:={"checks":checks,"failures":failures,"reader":reader};FileAccess.open(folder.path_join("reader.json" if reader else "writer.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("WORKSPACE_DOCKING "+JSON.stringify(result));app.free();quit(1 if failures else 0)
