extends "res://tests/movement_path_smoke.gd"
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
func _initialize() -> void:
	create_timer(100).timeout.connect(func():push_error("Cel patch history watchdog");quit(2));call_deferred("run")
func edit(action: int,at: int) -> void:
	var cel:=Drawing.cel_at(app.layers[1],at)
	app.cel_clipboard.open_menu(app.layers[1].id,str(cel.get("id","")),at,Vector2i(300,200));app.cel_clipboard.menu.id_pressed.emit(action);await settled()
func run() -> void:
	folder=OS.get_cmdline_user_args()[0];app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.mode.select(0);app.change_mode(0)
	var layer: Dictionary=app.layers[1];var image:=Drawing.blank(1920,1080);image.fill_rect(Rect2i(100,100,80,50),Color.CYAN);var original:=Storage.image_hash(image)
	layer.cels=[{"id":"source","start":0,"duration":8,"image":image}]
	for i in range(30):layer.cels.append({"id":"peer"+str(i),"start":8+i,"duration":1,"image":image.duplicate()})
	app.changed();app.set_frame(0);app.active_layer=1;app.layer_choice.select(1);app.tool.select(0);app.color.color=Color.RED;app.radius.value=6
	var press:=InputEventMouseButton.new();press.button_index=MOUSE_BUTTON_LEFT;press.pressed=true;app.canvas_input(press,Vector2(300,200));app.paint_segment(Vector2(340,200));press.pressed=false;app.canvas_input(press,Vector2(340,200));await settled()
	check(app.history.size()==1 and app.history[0].type=="pixels","real brush stroke creates prior Undo in a31cel layer")
	var stroke: Dictionary=app.history[0];var painted:=Storage.image_hash(image);var peers: Array=layer.cels.slice(1)
	await edit(3,4);var split: Dictionary=app.history[-1]
	check(layer.cels.size()==32 and app.history.size()==2 and is_same(app.history[0],stroke),"one split preserves earlier real stroke history near the cel limit")
	print("CEL_PATCH_CHARGE "+JSON.stringify({"command_bytes":split.get("bytes",0),"history_bytes":app.history_bytes}))
	if "--probe" in OS.get_cmdline_user_args():
		print("CEL_PATCH_PROBE "+JSON.stringify({"checks":checks,"failures":failures}));await app.quit_studio();quit(0 if failures==0 else 1);return
	check(split.type=="cel_patch" and split.before.size()==1 and split.after.size()==2 and not split.has("layer"),"split history retains only affected cels, not the layer or30peer Images")
	check(split.bytes<=2*8294400+8192,"split charges only two distinct source/right rasters plus bounded metadata")
	var generation: int=app.physics_editor.generation
	app.undo();check(layer.cels.size()==31 and layer.cels[0].duration==8 and Storage.image_hash(Drawing.image(layer.cels[0]))==painted,"split Undo restores original exposure and painted source")
	app.undo();check(Storage.image_hash(Drawing.image(layer.cels[0]))==original,"earlier actual stroke Undo remains reachable after split")
	app.redo();app.redo();check(layer.cels.size()==32 and Storage.image_hash(Drawing.image(layer.cels[0]))==painted and Storage.image_hash(Drawing.image(layer.cels[1]))==painted,"stroke and split Redo restore exact independent halves")
	check(app.physics_editor.generation==generation,"split/stroke Undo/Redo does not reset independent physics")
	var intact:=true
	for i in range(30):intact=intact and is_same(layer.cels[i+2],peers[i]) and Storage.image_hash(Drawing.image(layer.cels[i+2]))==original
	check(intact,"unaffected peer dictionaries, images and original RGBA remain untouched")
	await edit(1,4);var cut: Dictionary=app.history[-1]
	check(cut.before.size()==1 and cut.after.is_empty() and cut.bytes<=8294400+8192 and layer.cels.size()==31,"Cut retains and charges only its removed cel")
	await edit(2,40);var paste: Dictionary=app.history[-1]
	check(paste.before.is_empty() and paste.after.size()==1 and paste.bytes<=8294400+8192 and app.history.size()==4,"Paste retains only the inserted cel and preserves preceding history")
	var before: Array=layer.cels.duplicate(true);var count: int=app.history.size()
	check(not app.apply_command(split,"before") and layer.cels==before and app.history.size()==count,"stale split cannot erase a later moved/pasted drawing")
	generation=app.physics_editor.generation
	app.undo();app.undo();check(layer.cels.size()==32 and not Drawing.cel_at(layer,4).is_empty() and Drawing.cel_at(layer,40).is_empty(),"Paste and Cut Undo restore their own slots without replacing peers")
	app.redo();app.redo();check(layer.cels.size()==32 and Drawing.cel_at(layer,4).is_empty() and Storage.image_hash(Drawing.image(Drawing.cel_at(layer,40)))==painted,"Cut/Paste Redo restores moved copy with exact pixels")
	check(app.physics_editor.generation==generation,"patch Undo/Redo never resets the independent physics generation")
	app.set_frame(40);var child: String=app.sequence_editor.new_sequence("History isolation");check(not child.is_empty() and app.sequence_editor.enter(child).is_empty(),"real child sequence opens without changing global cel budget")
	var child_before: Array=app.layers.duplicate(true)
	check(not app.apply_command(paste,"before") and app.layers==child_before,"parent patch refuses to apply to another sequence owner")
	app.sequence_editor.return_to_parent();await settled();app.undo();app.undo();app.undo();layer=app.cel_timing.layer_by_id(split.layer_id)
	check(layer.cels.size()==32 and not Drawing.cel_at(layer,4).is_empty() and Drawing.cel_at(layer,40).is_empty(),"stable layer/cel patch Undo works after actual child round trip")
	print("CEL_PATCH_HISTORY "+JSON.stringify({"checks":checks,"failures":failures,"split_bytes":split.bytes,"cut_bytes":cut.bytes,"paste_bytes":paste.bytes}));await app.quit_studio();quit(0 if failures==0 else 1)
