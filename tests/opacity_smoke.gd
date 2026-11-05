extends SceneTree
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
const World=preload("res://src/world_document.gd")
const Journal=preload("res://src/recovery_journal.gd")
var app
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(140).timeout.connect(func():push_error("Opacity watchdog");quit(2));call_deferred("run")
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
func paint(point: Vector2) -> void:
	var e:=InputEventMouseButton.new();e.button_index=MOUSE_BUTTON_LEFT;e.pressed=true;app.canvas_input(e,point);e.pressed=false;app.canvas_input(e,point)
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0];app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recent.json");root.add_child(app);await settled()
	app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache");app.mode.select(0);app.change_mode(0);app.create_cel(false)
	var layer: Dictionary=app.layers[1];var image: Image=layer.cels[0].image;image.fill_rect(Rect2i(0,0,384,216),Color.RED);Drawing.touch(image);app.changed();await settled()
	var original:=image.get_data();var world: Dictionary=World.portable(app.current_world());var view: Dictionary=app.renderer.view_state();var keys: Array=app.keys.duplicate(true);var source:=FileAccess.get_sha256(app.source)
	var editor=app.layer_editor;editor.open();await settled();var history: int=app.history.size();var actions: int=app.autosave_actions
	check(editor.opacity.value==100 and not layer.has("opacity"),"old layers start at100percent without a new stored field")
	editor.opacity.value=25;await settled()
	check(app.history.size()==history and app.autosave_actions==actions and not layer.has("opacity") and app.canvas.overlay.get_image().get_data()==original,"typing an amount alone does not modify the project or preview")
	var started:=Time.get_ticks_usec();editor.apply_opacity.pressed.emit();await settled();var apply_ms:=(Time.get_ticks_usec()-started)/1000.0
	check(layer.opacity==.25 and app.history.size()==history+1 and app.autosave_actions==actions+1,"Apply opacity creates one real edit and one autosave action")
	var overlay: Image=app.canvas.overlay.get_image();check(overlay.get_data()[3]==64 and overlay.get_data()[0]==255 and image.get_data()==original,"quarter opacity rounds alpha to64 without flattening or changing original red pixels")
	editor.opacity.get_line_edit().text="35";editor.opacity.get_line_edit().text_submitted.emit("35")
	check(editor.opacity.value==35 and layer.opacity==.35,"Enter applies the actual typed opacity field");app.undo();await settled()
	layer.cels[0].duration=36;layer.cels.append({"id":"next","start":36,"duration":12,"image":image.duplicate()});app.changed();app.onion_editor.enabled.button_pressed=true;await settled()
	check(app.onion_editor.views[1].visible and is_equal_approx(app.onion_editor.views[1].material.get_shader_parameter("ghost_color").a,.0625),"onion guides combine their personal strength with the active layer opacity")
	editor.rename_layer("Faint ink");editor.set_visible(false);editor.set_visible(true)
	check(layer.opacity==.25,"rename and visibility edits retain opacity")
	app.undo();app.undo();app.undo();app.active_layer=0;app.refresh_layer_choices();app.undo();await settled()
	check(not layer.has("opacity") and app.active_layer==0,"opacity Undo restores missing-field compatibility on the original inactive layer")
	app.redo();check(layer.opacity==.25 and app.active_layer==0,"opacity Redo preserves another selected layer")
	app.active_layer=1;app.refresh_layer_choices();editor.dialog.hide();await settled()
	var before: PackedByteArray=app.canvas.overlay.get_image().get_data();var pixels:=Drawing.opacity_pixels
	app.color.color=Color.CYAN;paint(Vector2(700,500));await settled();var painted: PackedByteArray=app.canvas.overlay.get_image().get_data();var stroke_pixels:=Drawing.opacity_pixels-pixels
	check(painted!=before and stroke_pixels>0 and stroke_pixels<4096,"a real faded-layer stroke refreshes a small dirty region instead of all2million pixels")
	pixels=Drawing.opacity_pixels;app.undo();await settled()
	check(app.canvas.overlay.get_image().get_data()==before,"tile Undo restores exact faded preview")
	check(Drawing.opacity_pixels-pixels==128*64,"Undo refreshes the two affected64pixel tiles, not the full image")
	app.redo();await settled();check(app.canvas.overlay.get_image().get_data()==painted,"tile Redo restores exact faded preview")
	var builds:=Drawing.opacity_builds;app.set_frame(10);await settled()
	view=app.renderer.view_state()
	check(Drawing.opacity_builds==builds,"scrubbing inside a held exposure reuses its faded cache")
	editor.set_opacity(0);await settled();check(app.canvas.overlay.get_image().get_used_rect().get_area()==0,"zero opacity removes the layer from actual preview")
	check(not app.onion_editor.views[0].visible and not app.onion_editor.views[1].visible,"zero-opacity layers hide their editor onion guides too")
	var hidden_pixels:=image.get_data();paint(Vector2(900,600));app.fill_editor.start(Vector2(900,600))
	check(image.get_data()==hidden_pixels and not app.fill_editor.busy(),"zero-opacity pen and fill refuse invisible edits")
	var no_layer: Image=await app.renderer.capture(app.keys,[],10,true);var zero: Image=await app.renderer.capture(app.keys,app.layers,10,true)
	check(no_layer.get_data()==zero.get_data(),"zero opacity excludes paint from final GPU capture exactly")
	editor.set_opacity(25);await settled();editor.dialog.hide()
	app.onion_editor.enabled.button_pressed=false
	editor.set_opacity(100);await settled();check(not layer.has("opacity") and app.canvas.overlay.get_image().get_data()==image.get_data(),"full opacity returns to the exact legacy drawing path")
	var unchanged: int=app.history.size();editor.set_opacity(100);check(app.history.size()==unchanged,"applying unchanged full opacity adds no history")
	app.undo();await settled();check(layer.opacity==.25,"Undo of full opacity restores the prior amount")
	# Sampling visible drawings must see layer alpha, while target-only samples raw paint.
	app.tool.select(2);app.fill_editor.start(Vector2(80,80));check(app.fill_editor.context.size()>0,"faded visible layer still participates in the normal fill worker")
	while app.fill_editor.busy():await process_frame
	check(app.fill_editor.last_result.get("region",0)==384*216 and not app.fill_editor.pending.is_empty(),"visible-stack fill samples the faded region boundary and retains its edge preview")
	app.fill_editor.apply_pending()
	app.undo();await settled();app.tool.select(0)
	check(image.get_data()==hidden_pixels,"fill Undo restores original cel bytes without baking layer opacity")
	check(equal(world,World.portable(app.current_world())) and equal(keys,app.keys) and equal(view,app.renderer.view_state()) and FileAccess.get_sha256(app.source)==source,"opacity workflow preserves world, native geometry, explicit shot keys and editor view")
	var packed:=folder.path_join("opacity.has");app.has_project.save_file(packed,"packed");await job();var manual:=FileAccess.get_sha256(packed);var expected:=image.get_data();app.new_project();app.has_project.open_file(packed);await job()
	check(app.layers[1].opacity==.25 and app.layers[1].cels[0].image.get_data()==expected,"packed HAS reopens raw editable pixels and separate layer opacity")
	app.has_project.save_file(folder.path_join("linked.has"),"linked");await job();app.new_project();app.has_project.open_file(folder.path_join("linked.has"));await job()
	check(app.layers[1].opacity==.25 and app.layers[1].cels[0].image.get_data()==expected,"linked HAS keeps the same independent opacity parameter")
	app.changed();app.autosave_tick(true);await settled()
	while app.recovery_preview.busy():app.poll_recovery_preview();await process_frame
	var checkpoint: String=app.recovery_root.path_join(app.recovery_session);var entries:=Journal.entries(checkpoint);var thumbnail: Image=Journal.preview(checkpoint,entries[0].preview)
	var expected_preview: Image=app.renderer.viewport.get_texture().get_image();expected_preview.convert(Image.FORMAT_RGBA8);expected_preview.resize(256,144,Image.INTERPOLATE_BILINEAR)
	var dot:=Image.create(1,1,false,Image.FORMAT_RGBA8);dot.fill(Color8(255,0,0,64));expected_preview.blend_rect(dot,Rect2i(0,0,1,1),Vector2i(8,8))
	check(thumbnail!=null and thumbnail.get_pixel(8,8)==expected_preview.get_pixel(8,8),"actual background recovery worker thumbnail honors the saved layer opacity")
	check(app.open_project(checkpoint) and app.layers[1].opacity==.25 and app.layers[1].cels[0].image.get_data()==expected and FileAccess.get_sha256(packed)==manual,"recovery restores opacity and raw paint without overwriting manual HAS")
	var good:=folder.path_join("directory");check(Storage.save_project(good,app.video,app.keys,app.layers,app.source,app.frame,{}, {}, {},false,app.current_world()).is_empty(),"directory project stores the new optional layer parameter")
	var manifest:=good.path_join("project.json");var saved:=FileAccess.get_file_as_bytes(manifest);app.layers[1].opacity=NAN
	check(not Storage.save_project(good,app.video,app.keys,app.layers,app.source,app.frame).is_empty() and FileAccess.get_file_as_bytes(manifest)==saved,"invalid live opacity refuses before any existing save is rewritten")
	app.layers[1].opacity=.25
	var bad: Dictionary=JSON.parse_string(saved.get_string_from_utf8());bad.layers[1].opacity=2
	var file:=FileAccess.open(manifest,FileAccess.WRITE);file.store_string(JSON.stringify(bad,"",true,true));file.close()
	check(not Storage.readable_manifest(manifest) and not app.open_project(good) and app.layers[1].opacity==.25,"invalid saved opacity rejects Open and cannot qualify as a good backup")
	file=FileAccess.open(manifest,FileAccess.WRITE);file.store_buffer(saved);file.close()
	app.set_frame(10);var reference: Image=await app.renderer.capture(app.keys,app.layers,10,true);var error: String=await app.export_movie(folder)
	check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000011.png")).get_data()==reference.get_data(),"exported MP4 PNG equals reopened faded preview exactly")
	root.size=Vector2i(1200,760);app.mode.select(0);app.change_mode(0);editor.open();await settled();root.get_texture().get_image().save_png(folder.path_join("opacity-1200.png"))
	check(editor.dialog.size.x<800 and editor.dialog.size.y<650 and editor.apply_opacity.is_visible_in_tree(),"Simple layer opacity fits the actual1200pixel workspace")
	print("OPACITY_SMOKE "+JSON.stringify({"checks":checks,"failures":failures,"folder":folder,"project":packed,"movie":app.last_export_folder.path_join("movie.mp4"),"apply_with_frames_ms":apply_ms,"stroke_pixels":stroke_pixels}));app.free();quit(0 if failures==0 else 1)
