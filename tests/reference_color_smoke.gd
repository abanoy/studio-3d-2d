extends "res://tests/movement_path_smoke.gd"
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
var sheet
func sample_at(point: Vector2) -> void:
	var hover:=InputEventMouseMotion.new();event_at(sheet.viewer,point,hover);await process_frame
	for down in [true,false]:
		var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_RIGHT;event.pressed=down;event_at(sheet.viewer,point,event);await process_frame
	await settled()
func sample_pixel(point: Vector2i) -> void:
	var rect: Rect2=sheet.viewer.picture_rect();await sample_at(rect.position+(Vector2(point)+Vector2(.5,.5))/Vector2(sheet.image.get_size())*rect.size)
func run() -> void:
	folder=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder)
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("has-cache");sheet=app.reference_sheet;sheet.cache_root=folder.path_join("sheet-cache")
	check(app.load_demo_room(),"ordinary scene opens for reference-color drawing")
	app.mode.select(0);app.change_mode(0);app.set_frame(0);app.create_cel(false)
	var image:=Image.create(96,64,false,Image.FORMAT_RGBA8);image.fill(Color(.8,.2,.3,.5));image.fill_rect(Rect2i(48,0,48,64),Color(.2,.6,.9,1));image.fill_rect(Rect2i(0,0,16,16),Color(1,0,1,0))
	var png:=folder.path_join("Character colors α.png");image.save_png(png);var original_hash:=FileAccess.get_sha256(png);sheet.open();await settled();check(sheet.load_sheet(png).is_empty(),"original RGBA color sheet opens")
	sheet.keep.button_pressed=true;await settled();var reference: Dictionary=sheet.document();var history: int=app.history.size();var revision: int=app.recovery_revision;var world: Dictionary=app.current_world().duplicate(true);var keys: Array=app.keys.duplicate(true)
	await click(sheet.viewer);await sample_pixel(Vector2i(24,32))
	check(app.color.color==image.get_pixel(24,32) and app.color.color.a<1,"routed right click selects exact source color including alpha")
	var center: Vector2=sheet.viewer.size/2
	for down in [true,false]:
		var wheel:=InputEventMouseButton.new();wheel.button_index=MOUSE_BUTTON_WHEEL_UP;wheel.pressed=down;event_at(sheet.viewer,center,wheel);await process_frame
	await drag(sheet.viewer,center,Vector2(35,20));await sample_pixel(Vector2i(72,32))
	check(app.color.color==image.get_pixel(72,32) and sheet.viewer.zoom>1 and sheet.viewer.pan!=Vector2.ZERO,"zoomed and panned sheet sampling resolves the original source pixel")
	var selected: Color=app.color.color;await sample_pixel(Vector2i(8,8))
	check(app.color.color==selected and sheet.note.text.contains("transparent"),"fully transparent source pixel keeps the previous brush color with feedback")
	sheet.viewer.fit();await settled();await sample_at(Vector2(1,1));check(app.color.color==selected,"letterbox margin does not select an unrelated pixel")
	await sample_pixel(Vector2i(24,32));selected=app.color.color
	check(app.history.size()==history and app.recovery_revision==revision and app.current_world()==world and app.keys==keys and sheet.document()==reference,"color selection preserves document history revision world camera and kept identity")
	check(sheet.image.get_data()==image.get_data() and FileAccess.get_sha256(png)==original_hash,"sampling leaves every source pixel and original PNG byte unchanged")
	sheet.window.get_texture().get_image().save_png(folder.path_join("sampled-reference.png"));sheet.window.hide();await settled();app.brush_opacity.value=100;app.tool.select(0)
	var rect: Rect2=app.canvas.image_rect();await click_at(app.canvas,rect.position+Vector2(120.5,120.5)/Vector2(1920,1080)*rect.size)
	var cel: Dictionary=Drawing.cel_at(app.layers[app.active_layer],0)
	check(cel.image.get_pixel(120,120)==selected and app.history.size()==history+1,"next routed pen stroke paints exact selected color and alpha as one pixel Undo")
	app.undo();await settled();check(cel.image.get_pixel(120,120).a==0 and app.color.color==selected and sheet.document()==reference,"Undo removes painted pixels while preserving selected brush color and reference")
	app.redo();await settled();check(cel.image.get_pixel(120,120)==selected,"Redo restores exact reference-colored artwork")
	var picture: Image=await app.renderer.capture(app.keys,app.layers,0,true);picture.save_png(folder.path_join("reference.png"))
	var error: String=await app.export_movie(folder);check(error.is_empty() and picture.get_data()==Image.load_from_file(app.last_export_folder.path_join("frame_000001.png")).get_data(),"actual MP4 frame matches reference-colored drawing with source guide excluded")
	check(FileAccess.get_sha256(png)==original_hash and sheet.document()==reference,"export preserves original reference source and document ownership")
	print("REFERENCE_COLOR_SMOKE ",JSON.stringify({"checks":checks,"failures":failures,"movie":app.last_export_folder.path_join("movie.mp4")}));await app.quit_studio();quit(0 if failures==0 else 1)
