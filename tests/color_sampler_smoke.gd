extends SceneTree
const Drawing=preload("res://src/drawing.gd")
const Sampler=preload("res://src/color_sampler.gd")
const Storage=preload("res://src/storage.gd")
const World=preload("res://src/world_document.gd")
const SceneIO=preload("res://src/scene3d.gd")
const Support=preload("res://tests/world_test_support.gd")
var app
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(140).timeout.connect(func():push_error("Color picker watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func equal(a,b) -> bool:return JSON.parse_string(JSON.stringify(a,"",true,true))==JSON.parse_string(JSON.stringify(b,"",true,true))
func settled() -> void:
	for i in range(5):await process_frame
	await RenderingServer.frame_post_draw
func job() -> void:
	while app.has_project.pid>0:await process_frame
	await settled()
func click(point: Vector2) -> void:
	var e:=InputEventMouseButton.new();e.button_index=MOUSE_BUTTON_LEFT;e.pressed=true
	var rect: Rect2=app.canvas.image_rect();e.position=rect.position+point/Vector2(1920,1080)*rect.size;app.canvas._gui_input(e);e.pressed=false;app.canvas._gui_input(e)
func key(code: int) -> void:
	var e:=InputEventKey.new();e.keycode=code;e.pressed=true;app._unhandled_key_input(e)
func id_point(image: Image,color: Vector3) -> Vector2:
	for y in range(50,image.get_height()-50):
		for x in range(50,image.get_width()-50):
			var pixel:=image.get_pixel(x,y)
			if Vector3(pixel.r,pixel.g,pixel.b).distance_squared_to(color)<.001:return Vector2(x*2+1,y*2+1)
	return Vector2(-1,-1)
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0]
	var pixel:=Drawing.blank(2,2);pixel.fill(Color8(200,60,20,201))
	var lower:={"visible":true,"opacity":.25,"cels":[{"start":0,"duration":48,"image":pixel}]}
	var foreground:=Drawing.blank(2,2);foreground.fill(Color8(10,240,100,80))
	var upper:={"visible":true,"cels":[{"start":0,"duration":48,"image":foreground}]}
	var expected:=Drawing.composite([lower,upper],0,2,2).get_pixel(0,0)
	check(Sampler.drawing_pixel([lower,upper],0,Vector2i.ZERO).color==expected,"one-pixel visible drawing sampling matches native stacked alpha/opacity composition")
	lower.visible=false;check(Sampler.drawing_pixel([lower],0,Vector2i.ZERO).is_empty(),"visible source excludes hidden layers")
	check(Sampler.drawing_pixel([lower],0,Vector2i.ZERO,null,0).color==pixel.get_pixel(0,0),"original source reads hidden raw RGBA before layer opacity")
	check(Sampler.drawing_pixel([lower],48,Vector2i.ZERO,null,0).is_empty(),"original sampling never invents a drawing outside its exposure")
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recent.json");root.add_child(app);await settled();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache");app.mode.select(0);app.change_mode(0)
	var picker=app.color_sampler
	check(picker.viewport==null and picker.source.selected==0,"Simple picker defaults to view plus drawings without allocating an idle second view")
	key(KEY_I);await settled();check(app.tool.selected==3 and picker.panel.is_visible_in_tree() and not picker.source.is_visible_in_tree(),"I arms the real Simple color tool while detailed sources stay Advanced")
	var old: Color=app.color.color;var history: int=app.history.size();var revision: int=app.recovery_revision;var actions: int=app.autosave_actions
	var world: Dictionary=World.portable(app.current_world());var view: Dictionary=app.renderer.view_state();var keys: Array=app.keys.duplicate(true);var source:=FileAccess.get_sha256(app.source)
	var base: Image=app.renderer.viewport.get_texture().get_image();var target:=Vector2(500,300);var expected_3d:=base.get_pixel(500,300)
	click(target);await settled()
	check(picker.captures==1 and app.tool.selected==0 and app.color.color==expected_3d,"actual zoom-mapped canvas click picks the 3D pixel and returns to Pen")
	check(picker.viewport.render_target_update_mode==SubViewport.UPDATE_DISABLED and picker.viewport.size==Vector2i(1920,1080),"scratch view stops rendering after its single full-resolution sample")
	check(app.history.size()==history and app.recovery_revision==revision and app.autosave_actions==actions and equal(world,World.portable(app.current_world())) and equal(view,app.renderer.view_state()) and equal(keys,app.keys) and FileAccess.get_sha256(app.source)==source,"picking changes only drawing color, preserving native world/view/keys/history/recovery counters")
	app.frame_box.get_line_edit().grab_focus();key(KEY_I);check(app.tool.selected==0,"typing I in a numeric field cannot arm the drawing tool");app.frame_box.get_line_edit().release_focus()
	app.mode.select(1);app.change_mode(1);key(KEY_I);check(app.tool.selected==0,"Scene navigation keeps I from becoming a drawing shortcut");app.mode.select(0);app.change_mode(0)
	app.home.show();key(KEY_I);check(app.tool.selected==0,"Home blocks the drawing shortcut behind its cover");app.home.hide()
	app.exporting=true;picker.arm();check(app.tool.selected==0 and picker.context.is_empty(),"export blocks arming the picker");app.exporting=false
	app.tool.select(3);app.tool.item_selected.emit(3);await settled();check(app.tool.selected==3 and app.status.text.contains("Click a color"),"tool-menu selection arms the picker with current instructions");picker.cancel()
	# Two independently timed cels create a real onion guide, not another drawing at this frame.
	var ink:=Drawing.blank(1920,1080);ink.fill_rect(Rect2i(400,200,200,200),Color8(255,20,40,200))
	var future:=Drawing.blank(1920,1080);future.fill_rect(Rect2i(900,200,200,200),Color.BLACK)
	app.layers[1].cels=[{"id":"ink","start":0,"duration":12,"image":ink},{"id":"next","start":24,"duration":24,"image":future}];app.layers[1].opacity=.5;app.changed();app.onion_editor.enabled.button_pressed=true;await settled()
	check(app.onion_editor.views[1].visible,"onion exclusion fixture has an actual visible next-drawing guide")
	var original:=ink.get_data();var native: Image=await app.renderer.capture(app.keys,app.layers,0,true);var expected_paint:=native.get_pixel(500,300)
	picker.arm();click(target);await settled();check(app.color.color==expected_paint and ink.get_data()==original,"picker includes faded paint over3D with exact existing compositor rounding and unchanged original ink")
	var expected_ghost:=base.get_pixel(1000,300);picker.arm();click(Vector2(1000,300));await settled()
	check(app.color.color==expected_ghost,"visible pink onion guides do not contaminate picked colors")
	app.advanced_toggle.button_pressed=true;await settled();picker.source.select(1);picker.source.item_selected.emit(1);picker.arm();click(target);await settled()
	check(app.color.color==Drawing.composite(app.layers,0,1920,1080).get_pixel(500,300) and picker.captures==3,"visible-drawings mode picks faded RGBA without another GPU capture")
	picker.source.select(2);picker.source.item_selected.emit(2);app.layers[1].visible=false;app.changed();picker.arm();click(target);await settled()
	check(app.color.color==Color8(255,20,40,200) and ink.get_data()==original,"original-cel mode can recover exact hidden ink RGBA before50percent layer opacity")
	picker.source.select(1);picker.source.item_selected.emit(1);picker.arm();old=app.color.color;click(Vector2(1300,800));await settled()
	check(app.color.color==old and app.tool.selected==3,"blank drawing sampling preserves the previous color and stays ready for another point")
	var escape:=InputEventKey.new();escape.keycode=KEY_ESCAPE;escape.pressed=true;app._input(escape);check(app.tool.selected==0,"Escape cancels the armed picker without painting")
	app.layers[1].visible=true;app.changed();picker.source.select(0);picker.source.item_selected.emit(0)
	app.canvas.zoom=1.7;app.canvas.pan=Vector2(21,-18);await settled();picker.arm();click(target);await settled()
	check(app.color.color==expected_paint and ink.get_data()==original,"zoom and pan retain output-pixel mapping without an accidental pen mark")
	picker.arm();var count_before: int=picker.captures;picker.start(target);picker.start(Vector2(1000,300));await settled()
	check(app.color.color==expected_ghost and picker.captures==count_before+1,"rapid second click wins without letting the older request cancel its render")
	# Intentional changes while a view is rendering invalidate its color result.
	picker.arm();old=app.color.color;picker.start(target);app.set_frame(6);await settled();check(app.color.color==old and picker.context.is_empty(),"seeking rejects a pending color from an earlier frame")
	picker.arm();picker.start(target);app.renderer.camera.position.x+=.3;var moved: Dictionary=app.renderer.view_state();await settled()
	check(app.color.color==old and equal(moved,app.renderer.view_state()),"camera navigation rejects the old pixel without restoring or overwriting the new view")
	app.renderer.restore_view(view);app.set_frame(0);await settled()
	picker.arm();picker.start(target);app.color.color=Color.GREEN;await settled();check(app.color.color==Color.GREEN,"a newer manual color cannot be overwritten by an older pending pick")
	picker.arm();picker.start(target);app.new_project();await settled();check(picker.context.is_empty() and app.tool.selected==0 and app.layers[1].cels.is_empty(),"New invalidates pending color results and clears the armed tool")
	app.mode.select(0);app.change_mode(0);app.canvas.zoom=1;app.canvas.pan=Vector2.ZERO;app.canvas.queue_redraw();await settled()
	# The new-world grid remains visible in the editor but not in sampled paint colors.
	var grid_screen: Image=app.renderer.viewport.get_texture().get_image();var grid_point:=Vector2i(-1,-1)
	for y in range(540,1080,8):
		for x in range(0,1920,8):
			if grid_screen.get_pixel(x,y).r>.15:grid_point=Vector2i(x,y);break
		if grid_point.x>=0:break
	check(grid_point.x>=0 and app.renderer.editor_grid.visible,"empty-world fixture contains a real visible white grid pixel")
	if grid_point.x>=0:
		picker.arm();click(Vector2(grid_point));await settled();check(app.color.color==Color.BLACK and app.renderer.editor_grid.visible,"read-only color view excludes the grid without hiding or flashing the main editor grid")
	root.size=Vector2i(1200,760);app.advanced_toggle.button_pressed=false;picker.arm();await settled();root.get_texture().get_image().save_png(folder.path_join("picker-1200.png"));check(app.canvas.size.x>=500 and picker.panel.is_visible_in_tree() and not picker.source.is_visible_in_tree(),"Simple picker instructions fit the1200pixel workspace")
	picker.cancel();app.create_cel(false);var color_image: Image=Drawing.image(app.layers[1].cels[0]);color_image.fill_rect(Rect2i(700,400,80,80),Color8(42,120,210,255));Drawing.touch(color_image);app.changed();await settled()
	picker.arm();click(Vector2(740,440));await settled();click(Vector2(800,500));await settled()
	check(app.color.color==Color8(42,120,210,255) and color_image.get_pixel(800,500)==app.color.color,"the actual picked color paints a new mark with Pen after the same click has finished")
	var drawn: PackedByteArray=color_image.get_data()
	var packed:=folder.path_join("picker.has");app.has_project.save_file(packed,"packed");await job();app.new_project();app.has_project.open_file(packed);await job()
	check(Drawing.image(app.layers[1].cels[0]).get_data()==drawn,"painting with a picked color stays normally editable through packed HAS reopen")
	app.set_frame(0);var reference: Image=await app.renderer.capture(app.keys,app.layers,0,true);var error: String=await app.export_movie(folder)
	check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000001.png")).get_data()==reference.get_data(),"eyedropper helper view stays absent from actual MP4 PNG output")
	var movie: String=app.last_export_folder.path_join("movie.mp4");var native_models: Array=[]
	for name in ["pose-smoke/miku-project","source-smoke/source-project","sfm-smoke/project"]:
		var path:=ProjectSettings.globalize_path("res://output/"+name)
		if not FileAccess.file_exists(path.path_join("project.json")):print("SKIP private color fixture absent: "+name);continue
		check(app.open_project(path),"native model color fixture opens: "+name);await settled();var rig:=Support.select_rig(app)
		if not rig:check(false,"native model exists for color sampling");continue
		app.mode.select(0);app.change_mode(0);app.renderer.frame_scene(rig.root);await settled()
		var native_point:=id_point(app.world_selection.viewport.get_texture().get_image(),app.world_selection.color_for(Support.key(app,rig)))
		check(native_point.x>=0 and app.world_selection.outline.visible,"actual native skin pixels and selected green outline are visible: "+name)
		if native_point.x<0:continue
		var native_view: Dictionary=app.renderer.view_state();var native_world: Dictionary=World.portable(app.current_world());var original_hash:=FileAccess.get_sha256(rig.data.source)
		var reference_pixel: Image=app.renderer.viewport.get_texture().get_image();reference_pixel.convert(Image.FORMAT_RGBA8);reference_pixel.blend_rect(Drawing.composite(app.layers,app.frame,1920,1080),Rect2i(0,0,1920,1080),Vector2i.ZERO)
		var wanted:=reference_pixel.get_pixel(int(native_point.x),int(native_point.y));var count: int=picker.captures;picker.arm();click(native_point);await settled()
		check(picker.captures==count+1 and app.color.color==wanted and equal(native_view,app.renderer.view_state()) and equal(native_world,World.portable(app.current_world())) and FileAccess.get_sha256(rig.data.source)==original_hash,"native color excludes selection helpers while preserving rig/source/view: "+name)
		root.get_texture().get_image().save_png(folder.path_join("native-pick-"+str(native_models.size())+".png"))
		if native_models.is_empty():
			app.physics_editor.toggle.button_pressed=true;await settled();picker.arm();var previous_color: Color=app.color.color;count=picker.captures;click(native_point);await settled()
			check(app.physics_editor.is_running() and picker.captures==count and app.color.color==previous_color,"live native physics refuses an unstable3D pick without stopping simulation or changing the color")
			app.physics_editor.toggle.button_pressed=false;picker.cancel()
		native_models.append(name)
	var captures: int=picker.captures;picker.arm();picker.start(Vector2(960,540));var disposed: WeakRef=weakref(picker);app.free();app=null;await settled()
	check(disposed.get_ref()==null,"closing the app disposes a pending color capture without keeping its helper view alive")
	print("COLOR_SAMPLER_SMOKE "+JSON.stringify({"checks":checks,"failures":failures,"folder":folder,"project":packed,"movie":movie,"captures":captures,"native_projects":native_models}));quit(0 if failures==0 else 1)
