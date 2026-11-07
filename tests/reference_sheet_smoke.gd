extends "res://tests/movement_path_smoke.gd"
const Sheet=preload("res://src/reference_sheet.gd")
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
var sheet
func panel_button(text: String) -> Button:
	for node in sheet.window.find_children("","Button",true,false):
		if node.text==text:return node
	return null
func chooser() -> FileDialog:
	for child in app.get_children():
		if child is FileDialog and child.visible:return child
	return null
func choose(path: String) -> void:
	var dialog:=chooser();check(dialog!=null,"reference picker opens through actual control")
	if dialog:dialog.file_selected.emit(path)
	await settled()
func run() -> void:
	folder=OS.get_cmdline_user_args()[0];app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache");sheet=app.reference_sheet
	if "--read" in OS.get_cmdline_user_args():
		app.has_project.open_file(folder.path_join("Reference.has"));await wait_job()
		check(app.has_project.path==folder.path_join("Reference.has") and sheet.image==null and sheet.texture==null and not sheet.guide.visible,"cold project Open keeps session reference separate and disabled")
		var image: Image=await app.renderer.capture(app.keys,app.layers,0,true)
		check(image.get_data()==Image.load_from_file(folder.path_join("reference.png")).get_data(),"cold render repeats exactly without requiring reference PNG")
		sheet.open();await settled();check(sheet.note.text.contains("Open a PNG") and not sheet.overlay_toggle.button_pressed,"fresh reference viewer makes its empty state clear")
		print("REFERENCE_SHEET_READ ",JSON.stringify({"checks":checks,"failures":failures}));await app.quit_studio();quit(0 if failures==0 else 1);return
	check(app.load_demo_room(),"actual parent environment opens for reference/exclusion checks")
	var original:=Image.create(256,128,false,Image.FORMAT_RGBA8);original.fill(Color.RED);original.fill_rect(Rect2i(128,0,128,128),Color.GREEN)
	original.fill_rect(Rect2i(0,0,16,16),Color(1,.4,.2,.5))
	var path:=folder.path_join("My character sheet α.png");check(original.save_png(path)==OK,"original character-sheet fixture writes with Unicode and spaces")
	var digest:=FileAccess.get_sha256(path);var history: int=app.history.size();var revision: int=app.recovery_revision;var world: Dictionary=app.current_world().duplicate(true);var keys: Array=app.keys.duplicate(true)
	var render: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	app.inspector_scroll.ensure_control_visible(sheet.launch);await settled();await click(sheet.launch)
	check(is_instance_valid(sheet.window) and sheet.window.visible and not sheet.window.exclusive,"Simple reference control opens a modeless viewer")
	await click(panel_button("Open PNG…"));await choose(path)
	check(sheet.image!=null and sheet.image.get_data()==original.get_data() and sheet.source_hash==digest and not sheet.overlay_toggle.button_pressed,"actual picker loads exact reference pixels with guide initially off")
	check(app.history.size()==history and app.recovery_revision==revision and app.current_world()==world and app.keys==keys,"opening reference leaves scene shot history and dirty revision unchanged")
	var rect: Rect2=sheet.viewer.picture_rect();check(absf(rect.size.x/rect.size.y-2)<.00001,"reference viewer preserves source aspect ratio")
	# Return GUI focus from the synthetically completed file picker to the viewer.
	await click(sheet.viewer)
	var hover:=InputEventMouseMotion.new();event_at(sheet.viewer,sheet.viewer.size/2,hover);await process_frame
	var wheel:=InputEventMouseButton.new();wheel.button_index=MOUSE_BUTTON_WHEEL_UP;wheel.pressed=true;event_at(sheet.viewer,sheet.viewer.size/2,wheel);await process_frame
	wheel.pressed=false;event_at(sheet.viewer,sheet.viewer.size/2,wheel);await settled()
	check(sheet.viewer.zoom>1 and sheet.viewer.picture_rect().get_center().distance_to(rect.get_center())<.01,"routed wheel zoom anchors the pointer")
	var point: Vector2=sheet.viewer.size/2
	var press:=InputEventMouseButton.new();press.button_index=MOUSE_BUTTON_LEFT;press.pressed=true;event_at(sheet.viewer,point,press);await process_frame
	var motion:=InputEventMouseMotion.new();motion.button_mask=MOUSE_BUTTON_MASK_LEFT;motion.relative=Vector2(30,20);event_at(sheet.viewer,point+motion.relative,motion);await process_frame
	var release:=InputEventMouseButton.new();release.button_index=MOUSE_BUTTON_LEFT;event_at(sheet.viewer,point+motion.relative,release);await settled()
	check(sheet.viewer.pan.distance_to(Vector2(30,20))<.01 and not sheet.viewer.dragging,"routed sheet drag pans without scene edits")
	await click(panel_button("Fit sheet"));check(sheet.viewer.zoom==1 and sheet.viewer.pan==Vector2.ZERO,"Fit restores whole-sheet framing")
	sheet.window.get_texture().get_image().save_png(folder.path_join("sheet-panel.png"));sheet.window.hide();await settled()
	var sample_point: Vector2=app.canvas.get_global_transform_with_canvas()*app.canvas.image_rect().get_center();var baseline: Image=root.get_texture().get_image()
	sheet.overlay_toggle.button_pressed=true;sheet.opacity.value=50;await settled();var guided: Image=root.get_texture().get_image()
	check(sheet.guide.visible and sheet.guide.texture==sheet.texture and absf(sheet.guide.rect.size.x/sheet.guide.rect.size.y-2)<.00001 and sheet.guide.modulate.a==.5,"reference guide is a translucent aspect-correct canvas overlay")
	check(baseline.get_pixelv(Vector2i(sample_point))!=guided.get_pixelv(Vector2i(sample_point)),"actual working canvas pixels display the reference guide")
	guided.save_png(folder.path_join("guide-over-draw.png"));var final_image: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	check(final_image.get_data()==render.get_data(),"guide is absent from actual final renderer input")
	var canvas_point: Vector2=app.canvas.image_rect().position+Vector2(120,120)/Vector2(1920,1080)*app.canvas.image_rect().size
	await click_at(app.canvas,canvas_point)
	var cel: Dictionary=Drawing.cel_at(app.layers[app.active_layer],0)
	check(not cel.is_empty() and Drawing.image(cel).get_pixel(120,120).a>0 and sheet.image.get_data()==original.get_data(),"routed canvas drawing passes through guide and leaves reference pixels intact")
	var ink:=Drawing.composite(app.layers,0,1920,1080)
	app.toggle_play();await settled();check(not sheet.guide.visible,"guide hides during synchronized playback")
	app.stop();app.set_frame(0);await settled();check(sheet.guide.visible,"guide returns when drawing resumes")
	app.mode.select(1);app.change_mode(1);await settled();check(not sheet.guide.visible,"guide stays out of Scene editing")
	app.mode.select(0);app.change_mode(0);await settled()
	var malformed:=folder.path_join("Not a sheet.png");FileAccess.open(malformed,FileAccess.WRITE).store_string("unrelated file")
	var retained: Image=sheet.image;check(not sheet.load_sheet(malformed).is_empty() and sheet.image==retained and sheet.source==path,"invalid header keeps current reference intact")
	var forged:=FileAccess.get_file_as_bytes(path).slice(0,33);forged[16]=0;forged[17]=0;forged[18]=32;forged[19]=1
	check(not Sheet.header_error(forged).is_empty(),"oversized PNG dimensions refuse before decompression")
	check(not sheet.load_sheet(folder.path_join("Missing.png")).is_empty() and sheet.image==retained,"missing source keeps current reference intact")
	sheet.open();await settled();await click(panel_button("Open PNG…"));var stale:=chooser();sheet.clear()
	if stale:stale.file_selected.emit(path)
	await settled();check(sheet.image==null and not sheet.guide.visible and sheet.guide.texture==null,"Clear frees sheet and invalidates old picker callback")
	check(sheet.load_sheet(path).is_empty(),"original sheet can be reopened explicitly")
	var changed:=folder.path_join("Revised sheet.png");check(original.save_png(changed)==OK and sheet.load_sheet(changed).is_empty(),"separate revision source loads")
	var old_hash: String=sheet.source_hash;var revised:=original.duplicate();revised.fill(Color.BLUE);revised.save_png(changed);await settled()
	check(sheet.source_hash==old_hash and sheet.image.get_data()==original.get_data(),"external changes wait for explicit Reload")
	await click(panel_button("Reload"));check(sheet.source_hash!=old_hash and sheet.image.get_data()==revised.get_data(),"Reload installs the reviewed local revision")
	check(FileAccess.get_sha256(path)==digest,"original source PNG remains byte-identical")
	sheet.overlay_toggle.button_pressed=true;sheet.window.hide();app.set_frame(0);await settled();render=await app.renderer.capture(app.keys,app.layers,0,true);render.save_png(folder.path_join("reference.png"))
	var packed:=folder.path_join("Reference.has");app.has_project.save_file(packed,"packed");await wait_job();check(app.has_project.path==packed and sheet.image.get_data()==revised.get_data(),"ordinary Save keeps document and current reference separate")
	var error: String=await app.export_movie(folder);check(error.is_empty() and render.get_data()==Image.load_from_file(app.last_export_folder.path_join("frame_000001.png")).get_data(),"actual MP4 source excludes visible reference guide and preserves scene plus ink")
	var movie: String=app.last_export_folder.path_join("movie.mp4");error=await app.export_images(folder,true)
	check(error.is_empty() and ink.get_data()==Image.load_from_file(app.last_export_folder.path_join("frame_000001.png")).get_data(),"transparent drawing-only PNG export also excludes reference guide")
	await settled()
	check(sheet.guide.visible and FileAccess.get_sha256(path)==digest,"export restores editing guide and preserves original source")
	print("REFERENCE_SHEET_SMOKE ",JSON.stringify({"checks":checks,"failures":failures,"movie":movie}));await app.quit_studio();quit(0 if failures==0 else 1)
