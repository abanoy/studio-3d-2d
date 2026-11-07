extends SceneTree
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
const World=preload("res://src/world_document.gd")
var app
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(130).timeout.connect(func():push_error("Layers watchdog");quit(2));call_deferred("run")
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
func signature() -> Array:
	var result: Array=[]
	for layer in app.layers:
		var cels: Array=[]
		for cel in layer.cels:cels.append([cel.id,cel.start,cel.duration,Storage.image_hash(Drawing.image(cel))])
		result.append([layer.id,layer.name,layer.visible,cels])
	return result
func paint(point: Vector2) -> void:
	var e:=InputEventMouseButton.new();e.button_index=MOUSE_BUTTON_LEFT;e.pressed=true
	var rect: Rect2=app.canvas.image_rect();e.position=rect.position+point/Vector2(1920,1080)*rect.size;app.canvas._gui_input(e);e.pressed=false;app.canvas._gui_input(e)
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0];app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settled()
	app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache");app.mode.select(0);app.change_mode(0)
	var editor=app.layer_editor
	check(app.layers.size()==2 and app.layers[0].name=="Rough" and app.layers[1].name=="Ink","New retains the two familiar default layers")
	var world: Dictionary=World.portable(app.current_world());var keys: Array=app.keys.duplicate(true);var view: Dictionary=app.renderer.view_state();var source:=FileAccess.get_sha256(app.source)
	var history: int=app.history.size();var actions: int=app.autosave_actions
	editor.launch.pressed.emit();await settled()
	check(editor.dialog.visible and editor.listing.get_item_metadata(0)==1 and app.active_layer==1,"Simple Layers opens the real dialog with topmost Ink first")
	check(app.history.size()==history and app.autosave_actions==actions,"opening the layer list is not an authored edit")
	editor.add.pressed.emit();await settled();var third: Dictionary=app.layers[2]
	check(app.layers.size()==3 and third.name=="Layer" and app.active_layer==2 and third.cels.is_empty(),"New layer inserts a blank layer above the selected drawing")
	editor.name_edit.text="Color glow";editor.name_edit.text_submitted.emit("Color glow")
	check(third.name=="Color glow" and app.layer_choice.get_item_text(2)=="Color glow","actual name field renames the layer and chooser together")
	app.undo();check(third.name=="Layer","rename Undo restores the same dictionary")
	app.redo();check(third.name=="Color glow","rename Redo restores the user name")
	var size: int=app.history.size();editor.rename_layer(" ink ");editor.rename_layer("\n");editor.rename_layer("bad\nname");editor.rename_layer("x".repeat(65))
	check(app.history.size()==size and third.name=="Color glow","duplicate, empty, multiline and overlong names refuse without history")
	editor.rename_layer("Color glow");editor.move_layer(1)
	check(app.history.size()==size,"identical rename and out-of-range reorder add no history")
	editor.effects.pressed.emit();var fx: Dictionary=app.layers[3]
	check(app.layers.size()==4 and fx.name=="Effects" and app.active_layer==3,"Effects is a real fourth editable layer")
	editor.add_layer("Fifth");check(app.layers.size()==4 and editor.add.disabled and editor.effects.disabled,"four-layer capacity is enforced before allocation")
	app.undo();check(app.layers.size()==3 and app.layers[2].id==third.id,"adding a layer undoes to the previous logical selection")
	app.redo();check(app.layers[3].id==fx.id,"Redo preserves the new layer identity")
	editor.select_row(1);check(app.active_layer==2 and app.layer_choice.selected==2,"top-first list selection addresses the correct underlying layer")
	editor.dialog.hide();app.create_cel(false);app.color.color=Color.RED;paint(Vector2(700,500));await settled()
	var painted: Image=Drawing.image(app.layers[2].cels[0]);var painted_hash:=Storage.image_hash(painted)
	editor.open();editor.move_layer(-1);editor.request_remove();await settled()
	check(editor.confirmation.visible and not editor.dialog.visible and app.layers.size()==4,"populated removal asks once before changing the layer stack")
	editor.confirmation.canceled.emit();editor.confirmation.hide();check(app.layers.size()==4 and Storage.image_hash(painted)==painted_hash,"cancelled removal keeps original drawings")
	editor.open();editor.request_remove();editor.confirmation.confirmed.emit();await settled()
	check(app.layers.size()==3 and app.history[-1].bytes==painted.get_data_size(),"confirmed removal charges retained drawing bytes to bounded history")
	app.undo();check(app.layers.size()==4 and is_same(app.layers[1],third) and is_same(Drawing.image(app.layers[1].cels[0]),painted),"removal Undo restores exact layer dictionary and cel Image identities")
	app.undo();check(app.active_layer==2 and is_same(app.layers[2],third),"reorder Undo follows the selected layer back to its old position")
	app.undo();check(Storage.image_hash(painted)!=painted_hash,"older real brush Undo still reaches its drawing after structural changes")
	app.redo();check(Storage.image_hash(painted)==painted_hash,"older brush Redo restores the exact original paint bytes")
	# Put overlapping opaque marks in Ink and Color glow to prove actual order.
	var red:=Drawing.blank(1920,1080);red.fill_rect(Rect2i(800,400,160,160),Color.RED)
	var blue:=Drawing.blank(1920,1080);blue.fill_rect(Rect2i(800,400,160,160),Color.BLUE)
	app.layers[1].cels=[{"id":"blue","start":0,"duration":48,"image":blue}]
	third.cels=[{"id":"red","start":0,"duration":48,"image":red}];app.changed();editor.dialog.hide()
	check(Drawing.composite(app.layers,0,1920,1080).get_pixel(850,450)==Color.RED,"higher drawing composites over lower ink")
	var red_capture: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	editor.move_layer(-1);var blue_capture: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	check(Drawing.composite(app.layers,0,1920,1080).get_pixel(850,450)==Color.BLUE and blue_capture.get_data()!=red_capture.get_data(),"Move down changes actual final GPU composition in the same order as the list")
	app.undo();var restored: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	check(restored.get_data()==red_capture.get_data(),"reorder Undo restores exact final rendered pixels")
	app.layer_visibility.button_pressed=false
	check(not third.visible and app.history[-1].type=="layer_properties" and Drawing.composite(app.layers,0,1920,1080).get_pixel(850,450)==Color.BLUE,"main visibility control is an undoable compositing edit")
	app.active_layer=0;app.layer_choice.select(0);app.refresh_layer();app.undo()
	check(third.visible and app.active_layer==0,"property Undo changes its original layer while preserving another selection")
	app.redo();check(not third.visible and app.active_layer==0,"property Redo retains inactive-layer ownership")
	app.undo();app.active_layer=2;app.refresh_layer_choices();editor.rename_layer("Glow final")
	check(equal(world,World.portable(app.current_world())) and equal(keys,app.keys) and equal(view,app.renderer.view_state()) and FileAccess.get_sha256(app.source)==source,"layer edits preserve world/native source, explicit camera keys and editor view")
	var expected:=signature();var packed:=folder.path_join("layers.has");app.has_project.save_file(packed,"packed");await job();var manual:=FileAccess.get_sha256(packed)
	app.new_project();await settled();app.has_project.open_file(packed);await job()
	check(equal(signature(),expected),"packed HAS reopens exact names, layer order, visibility, exposure IDs and raster hashes")
	app.has_project.save_file(folder.path_join("linked.has"),"linked");await job();app.new_project();app.has_project.open_file(folder.path_join("linked.has"));await job()
	check(equal(signature(),expected),"linked HAS preserves the same editable layer stack")
	app.changed();app.autosave_tick(true)
	while app.recovery_preview.busy():app.poll_recovery_preview();await process_frame
	check(app.open_project(app.recovery_root.path_join(app.recovery_session)) and equal(signature(),expected) and FileAccess.get_sha256(packed)==manual,"recovery restores all layer edits without rewriting the manual HAS")
	app.set_frame(0);var reference: Image=await app.renderer.capture(app.keys,app.layers,0,true);var error: String=await app.export_movie(folder)
	check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000001.png")).get_data()==reference.get_data(),"MP4 PNG matches the recovered reordered drawing stack exactly")
	root.size=Vector2i(1200,760);app.mode.select(0);app.change_mode(0);editor.open();await settled();root.get_texture().get_image().save_png(folder.path_join("layers-1200.png"))
	check(editor.dialog.size.x<800 and editor.dialog.size.y<650 and app.canvas.size.x>=500 and editor.remove.is_visible_in_tree(),"real layer dialog fits the1200pixel workspace with accessible controls")
	# A queued confirmation may never delete artwork in a replacement document.
	app.active_layer=2;editor.request_remove();check(editor.confirmation.visible,"stale-removal fixture has a real pending populated layer")
	app.new_project();editor.confirm_remove();await settled()
	check(app.layers.size()==2 and app.layers[0].name=="Rough" and not editor.dialog.visible and not editor.confirmation.visible,"New cancels old-dialog and confirmation ownership")
	editor.session=app.recovery_session;editor.dialog.hide();app.active_layer=1;editor.request_remove();await settled();editor.dialog.hide();editor.request_remove()
	check(app.layers.size()==1 and editor.remove.disabled,"last remaining layer cannot be removed")
	app.undo();check(app.layers.size()==2,"removing an empty layer remains undoable")
	editor.dialog.hide();app.active_layer=0;app.refresh_layer_choices();editor.rename_layer("flats");app.fill_editor.color_layer()
	check(app.layers.size()==2 and app.active_layer==0,"Fill selects a renamed lowercase flats layer without creating a duplicate")
	editor.add_layer("Effects");editor.add_layer("Effects")
	check(app.layers.size()==4 and app.layers[2].name=="Effects 2","new layer names receive an unambiguous suffix")
	editor.dialog.hide();app.tool.select(2);app.fill_editor.start(Vector2(100,100));editor.rename_layer("Fresh effect")
	while app.fill_editor.busy():await process_frame
	check(app.fill_editor.context.is_empty() and app.fill_editor.pending.is_empty() and app.layers[2].cels.is_empty(),"layer edits discard an unfinished fill without changing drawing pixels")
	print("LAYERS_SMOKE "+JSON.stringify({"checks":checks,"failures":failures,"folder":folder,"project":packed,"movie":app.last_export_folder.path_join("movie.mp4")}));app.free();quit(0 if failures==0 else 1)
