extends "res://tests/workspace_docking_smoke.gd"
func run() -> void:
	folder=OS.get_cmdline_user_args()[0];var reader: bool="--read" in OS.get_cmdline_user_args()
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recent.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;root.size=Vector2i(1800,1100);await settle()
	var ws=app.workspace_layout;ws.path=folder.path_join("layout.json")
	if reader:
		app.has_project.cache_root=folder.path_join("reader-cache");app.has_project.open_file(folder.path_join("scene.has"))
		while app.has_project.pid>0:await process_frame
		check(ws.load_layout(),"fresh process loads nested workspace v3");await settle()
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
		check(JSON.parse_string(JSON.stringify(ws.state()))==expected.layout,"fresh process restores exact nested split tree, tabs, offsets and native floating geometry")
		check(ws.slots.top.get_child(0) is HSplitContainer and ws.dock_tree.book_for("timeline").get_parent() is VSplitContainer,"cold nested workspace retains two columns with two rows on one side")
		check(ws.floating.has("world") and ws.floating.world.force_native,"cold nested layout retains independent native World window")
		check((await app.renderer.capture(app.keys,app.layers,0,true)).get_data()==Image.load_from_file(folder.path_join("before.png")).get_data(),"cold nested workspace preserves exact model and camera render")
	else:
		if FileAccess.file_exists(folder.path_join("input.has")):
			app.has_project.cache_root=folder.path_join("writer-cache");app.has_project.open_file(folder.path_join("input.has"))
			while app.has_project.pid>0:await process_frame
			check(app.current_world().objects.size()==1,"actual native Avatar opens for recursive docking")
			app.world_selection.select_entity(app.current_world().objects[0].id)
		else:
			var placement: Dictionary=app.import_actions.placement();placement.physics_on_import=false
			check(app.pose_editor.add_model(ProjectSettings.globalize_path("res://examples/tutorials/Practice figure.glb"),0,placement).is_empty() and app.current_world().objects.size()==1,"actual included rig opens for recursive docking");app.world_selection.select_entity(app.last_import_id)
		app.mode.select(2);app.change_mode(2);ws.reset();await settle()
		var world: Dictionary=World.portable(app.current_world());var view: Dictionary=app.renderer.view_state();var history: int=app.history.size();var ids:=[app.canvas.get_instance_id(),app.timeline.get_instance_id(),app.controls.get_instance_id()]
		var image: Image=await app.renderer.capture(app.keys,app.layers,0,true);image.save_png(folder.path_join("before.png"))
		await heading("timeline",ws.vertical.get_global_rect().position+Vector2(ws.vertical.size.x*.5,12));check(ws.slot_of("timeline")=="top","actual title drag moves Timeline above the scene")
		var timeline_book: TabContainer=ws.dock_tree.book_for("timeline");var target: Rect2=timeline_book.get_global_rect();var right_point:=Vector2(target.end.x-target.size.x*.15,target.get_center().y)
		await heading("world",right_point);var world_book: TabContainer=ws.dock_tree.book_for("world");timeline_book=ws.dock_tree.book_for("timeline")
		check(ws.slot_of("world")=="top" and timeline_book.get_parent()==world_book.get_parent() and timeline_book.get_parent() is HSplitContainer,"dragging World to the right edge of top Timeline creates two top docks instead of moving to the global right edge")
		check(timeline_book.get_global_rect().end.x<=world_book.global_position.x and timeline_book.is_visible_in_tree() and world_book.is_visible_in_tree(),"both top docks are visible side by side")
		var top_split: SplitContainer=timeline_book.get_parent();var previous: float=timeline_book.size.x;await resize_side(top_split,-140)
		check(timeline_book.size.x<previous-100 and world_book.size.x>previous+80,"actual nested divider drag adjusts the two top widths")
		target=timeline_book.get_global_rect();await heading("properties",Vector2(target.get_center().x,target.end.y-target.size.y*.15));var properties_book: TabContainer=ws.dock_tree.book_for("properties");timeline_book=ws.dock_tree.book_for("timeline")
		check(properties_book.get_parent()==timeline_book.get_parent() and properties_book.get_parent() is VSplitContainer and properties_book.get_parent().get_parent()==top_split,"a second edge drop creates nested rows inside the left top column")
		check(timeline_book.get_global_rect().end.y<=properties_book.global_position.y and world_book.get_global_rect().end.x<=ws.vertical.get_global_rect().end.x,"nested rows remain separate from the full-height World column")
		root.get_texture().get_image().save_png(folder.path_join("top-two-columns-with-left-rows.png"))
		await heading("properties",timeline_book.get_global_rect().get_center());timeline_book=ws.dock_tree.book_for("timeline")
		check(timeline_book==ws.dock_tree.book_for("properties") and timeline_book.get_parent()==top_split and top_split.get_child_count()==2,"tabbing nested Properties back into Timeline removes the empty split without disturbing World")
		target=timeline_book.get_global_rect();await heading("properties",Vector2(target.get_center().x,target.end.y-12));timeline_book=ws.dock_tree.book_for("timeline");properties_book=ws.dock_tree.book_for("properties")
		var left_column: Control=timeline_book.get_parent();var left_width: float=left_column.size.x;await heading("world",app.canvas.get_global_rect().get_center())
		check(ws.floating.has("world") and left_column.size.x>left_width*1.4,"floating a nested World dock collapses its empty visual column")
		if ws.floating.has("world"):ws.floating.world.close_requested.emit();await settle()
		world_book=ws.dock_tree.book_for("world");check(not ws.floating.has("world") and world_book.get_parent()==top_split and world_book.is_visible_in_tree(),"closing native World window restores its exact nested home")
		ws.float_panel("world");await settle();ws.floating.world.position=DisplayServer.screen_get_usable_rect().position+Vector2i(120,160);ws.floating.world.size=Vector2i(420,520);await settle()
		check(World.portable(app.current_world())==world and app.renderer.view_state()==view and app.history.size()==history,"recursive docking changes no model, camera or Undo history")
		check(ids==[app.canvas.get_instance_id(),app.timeline.get_instance_id(),app.controls.get_instance_id()],"recursive arrangements retain all original live editor controls")
		check((await app.renderer.capture(app.keys,app.layers,0,true)).get_data()==image.get_data(),"recursive layout preserves exact output pixels")
		app.has_project.save_file(folder.path_join("scene.has"),"packed")
		while app.has_project.pid>0:await process_frame
		ws.timer.stop();ws.save();FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify({"layout":ws.state()}))
	var result:={"checks":checks,"failures":failures,"reader":reader};FileAccess.open(folder.path_join("reader.json" if reader else "writer.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("WORKSPACE_NESTED "+JSON.stringify(result));app.free();quit(1 if failures else 0)
