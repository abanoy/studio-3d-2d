extends "res://tests/movement_path_smoke.gd"
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
var sheet
func action(text: String) -> void:
	for button in sheet.window.find_children("","Button",true,false):
		if button.text==text:button.pressed.emit();break
	await settled()
func screen_pixel(point: Vector2) -> Color:return root.get_texture().get_image().get_pixelv(Vector2i(point))
func run() -> void:
	folder=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder)
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("has-cache");sheet=app.reference_sheet;sheet.cache_root=folder.path_join("sheet-cache");check(app.load_demo_room(),"actual scene opens for reference guide alignment")
	var original:=Image.create(128,64,false,Image.FORMAT_RGBA8);original.fill(Color.RED);original.fill_rect(Rect2i(64,0,64,32),Color.GREEN);original.fill_rect(Rect2i(0,32,64,32),Color.BLUE);original.fill_rect(Rect2i(64,32,64,32),Color.YELLOW)
	var png:=folder.path_join("Four views α.png");original.save_png(png);var hash:=FileAccess.get_sha256(png);sheet.open();await settled();await action("Whole sheet");check(sheet.note.text.contains("Open a PNG") and sheet.image==null,"empty Whole sheet action asks for an image without changing state");check(sheet.load_sheet(png).is_empty(),"original multi-view color sheet opens")
	sheet.keep.button_pressed=true;await settled();var reference: Dictionary=sheet.document();var history: int=app.history.size();var revision: int=app.recovery_revision
	await action("Align guide…");check(sheet.alignment.visible,"actual Align guide control exposes size and output-pixel offsets")
	sheet.viewer.zoom=4.;sheet.viewer.pan=Vector2.ZERO;sheet.viewer.queue_redraw();await settled()
	var picture: Rect2=sheet.viewer.picture_rect();sheet.viewer.pan+=sheet.viewer.size/2-(picture.position+Vector2(32,16)/Vector2(128,64)*picture.size);sheet.viewer.queue_redraw();await settled();await action("Use viewed region")
	var region: Rect2i=sheet.guide_region
	check(region.has_area() and region.position.x>0 and region.position.y>0 and region.end.x<64 and region.end.y<32,"visible region selects only the intended top-left sheet view")
	check(sheet.overlay_toggle.button_pressed and sheet.guide.region==region and sheet.guide.texture==sheet.texture,"selected region becomes guide using the original shared texture")
	check(sheet.image.get_data()==original.get_data() and sheet.document()==reference and app.history.size()==history and app.recovery_revision==revision,"crop and alignment tools preserve full PNG project identity history and revision")
	sheet.opacity.value=100;sheet.window.hide();await settled();var canvas_rect: Rect2=app.canvas.image_rect();var canvas_center: Vector2=app.canvas.get_global_transform_with_canvas()*canvas_rect.get_center();var center_color:=screen_pixel(canvas_center)
	check(center_color.r>.99 and center_color.g<.01 and center_color.b<.01,"actual Draw canvas shows only the selected red source region")
	var original_center: Vector2=sheet.guide.rect.get_center();var original_size: Vector2=sheet.guide.rect.size;sheet.guide_scale.value=50;sheet.guide_x.value=800;sheet.guide_y.value=-200;await settled()
	check(sheet.guide.rect.size.distance_to(original_size*.5)<.001 and sheet.guide.rect.get_center().distance_to(original_center+Vector2(800./1920,-200./1080)*canvas_rect.size)<.001,"size and output-pixel offsets produce exact canvas guide geometry")
	check(screen_pixel(canvas_center)!=center_color,"actual guide pixels move away from their previous canvas position")
	app.canvas.zoom=1.3;app.canvas.pan=Vector2(30,-20);app.canvas.queue_redraw();await settled();canvas_rect=app.canvas.image_rect()
	check(sheet.guide.rect.get_center().distance_to(canvas_rect.get_center()+Vector2(800./1920,-200./1080)*canvas_rect.size)<.001,"canvas zoom/pan preserves output-space guide registration")
	var kept_region: Rect2i=sheet.guide_region;var kept_rect: Rect2=sheet.guide.rect;sheet.clear();app.undo();await settled()
	check(sheet.document()==reference and sheet.guide_region==kept_region and sheet.guide.rect.is_equal_approx(kept_rect) and sheet.guide_scale.value==50 and sheet.guide_x.value==800 and sheet.guide_y.value==-200,"Undo Clear restores source plus exact personal crop/alignment state")
	sheet.open();await settled();history=app.history.size();revision=app.recovery_revision;await action("Whole sheet")
	check(sheet.guide_region==Rect2i(0,0,128,64) and sheet.guide_scale.value==100 and sheet.guide_x.value==0 and sheet.guide_y.value==0,"Whole sheet restores full-source centered fit")
	var previous: Rect2i=sheet.guide_region;sheet.viewer.pan=Vector2(100000,100000);sheet.viewer.queue_redraw();await settled();await action("Use viewed region")
	check(sheet.guide_region==previous and sheet.note.text.contains("Bring part"),"empty viewed region keeps the last valid guide")
	check(app.history.size()==history and app.recovery_revision==revision and FileAccess.get_sha256(png)==hash,"personal guide changes add no document commands and preserve original PNG")
	var bad: Dictionary=sheet.state();bad.region=[0,0,1000,1000];check(not sheet.restore_state(bad).is_empty() and sheet.guide_region==previous and sheet.document()==reference,"invalid guide history refuses atomically without changing source")
	var packed:=folder.path_join("Guide.has");app.has_project.save_file(packed,"packed");await wait_job();check(app.has_project.path==packed,"ordinary kept-reference save preserves original full PNG")
	app.new_project();app.has_project.open_file(packed);await wait_job();check(sheet.image.get_size()==Vector2i(128,64) and sheet.image.get_data()==original.get_data() and sheet.guide_region==Rect2i(0,0,128,64) and not sheet.guide.visible and not sheet.overlay_toggle.button_pressed,"Open restores full reference with session guide alignment reset and off")
	sheet.open();await settled();sheet.guide_region=kept_region;sheet.overlay_toggle.button_pressed=true;sheet.guide_scale.value=150;sheet.guide_x.value=200;sheet.guide_y.value=100;sheet.window.hide();app.mode.select(0);app.change_mode(0);app.set_frame(0);app.create_cel(false);Drawing.stroke(Drawing.cel_at(app.layers[1],0).image,Vector2(80,80),Vector2(180,80),5,Color.CYAN,false);app.changed();await settled()
	var preview: Image=await app.renderer.capture(app.keys,app.layers,0,true);preview.save_png(folder.path_join("reference.png"));var error: String=await app.export_movie(folder)
	check(error.is_empty() and preview.get_data()==Image.load_from_file(app.last_export_folder.path_join("frame_000001.png")).get_data(),"actual movie frame excludes cropped moved/scaled guide while preserving scene and ink")
	check(FileAccess.get_sha256(png)==hash and sheet.image.get_data()==original.get_data(),"save reopen and export preserve every original reference pixel and byte")
	print("REFERENCE_ALIGNMENT_SMOKE ",JSON.stringify({"checks":checks,"failures":failures,"movie":app.last_export_folder.path_join("movie.mp4")}));await app.quit_studio();quit(0 if failures==0 else 1)
