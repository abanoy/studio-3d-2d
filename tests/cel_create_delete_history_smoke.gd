extends "res://tests/movement_path_smoke.gd"
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
const Snapshot=preload("res://src/cel_raster_snapshot.gd")
const Owner=preload("res://src/cel_raster_owner.gd")
const Cache=preload("res://src/cel_raster_snapshot_cache.gd")
func _initialize() -> void:
	create_timer(120).timeout.connect(func():push_error("Create/delete history watchdog");quit(2));call_deferred("run")
func hash_cel(cel: Dictionary) -> String:return Storage.image_hash(Drawing.image(cel))
func run() -> void:
	folder=OS.get_cmdline_user_args()[0];app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.mode.select(0);app.change_mode(0)
	var owned: bool="--owned" in OS.get_cmdline_user_args();var layer: Dictionary=app.layers[1];var image:=Drawing.blank(1920,1080);image.fill_rect(Rect2i(100,100,80,50),Color.CYAN);var original:=Storage.image_hash(image)
	layer.cels=[{"id":"source","start":0,"duration":8,"image":image}]
	for i in range(30):layer.cels.append({"id":"peer"+str(i),"start":8+i,"duration":1,"image":image.duplicate()})
	if owned:
		var cache:=Cache.new();layer.cels[0].erase("image");layer.cels[0].raster_owner=Owner.from_snapshot(Snapshot.capture(image).raster,cache).owner;app.raster_budget.install(cache)
	app.changed();app.set_frame(0);app.active_layer=1;app.layer_choice.select(1);app.tool.select(0);app.color.color=Color.RED;app.radius.value=6;app.brush_pressure.button_pressed=false
	var press:=InputEventMouseButton.new();press.button_index=MOUSE_BUTTON_LEFT;press.pressed=true;app.canvas_input(press,Vector2(300,200));app.paint_segment(Vector2(340,200));press.pressed=false;app.canvas_input(press,Vector2(340,200));await settled()
	check(app.history.size()==1 and app.history[0].type=="pixels","real stroke creates prior Undo in31cel layer")
	var stroke: Dictionary=app.history[0];var painted:=hash_cel(layer.cels[0]);var peers: Array=layer.cels.slice(1);app.set_frame(4);app.create_cel(true);var created: Dictionary=app.history[-1]
	check(layer.cels.size()==32 and app.history.size()==2 and is_same(app.history[0],stroke),"Copy cel in32drawing fixture preserves preceding real stroke Undo")
	if "--probe" in OS.get_cmdline_user_args():
		print("CREATE_DELETE_PROBE "+JSON.stringify({"checks":checks,"failures":failures,"command_bytes":created.get("bytes",0)}));await app.quit_studio();quit(0 if failures==0 else 1);return
	check(created.type=="cel_patch" and created.before.size()==1 and created.after.size()==2 and not created.has("layer"),"copy records only split exposure and new independent cel")
	check(created.bytes<=2*8294400+8192,"copy charges two distinct rasters rather than31unchanged peers")
	var copied:=Drawing.cel_at(layer,4);check(copied.start==4 and copied.duration==4 and hash_cel(copied)==painted and not is_same(Drawing.image(copied),Drawing.image(layer.cels[0])),"copy preserves exact pixels and independent editable identity")
	var generation: int=app.physics_editor.generation
	app.undo();check(layer.cels.size()==31 and layer.cels[0].duration==8 and hash_cel(layer.cels[0])==painted,"copy Undo restores original hold")
	app.undo();check(hash_cel(layer.cels[0])==original,"preceding stroke Undo remains reachable")
	app.redo();app.redo();check(layer.cels.size()==32 and hash_cel(layer.cels[0])==painted and hash_cel(Drawing.cel_at(layer,4))==painted,"stroke and copy Redo restore exact independent drawings")
	app.delete_cel();var removed: Dictionary=app.history[-1]
	check(layer.cels.size()==31 and removed.type=="cel_patch" and removed.before.size()==1 and removed.after.is_empty() and removed.bytes<=8294400+8192,"delete retains only removed cel and preserves earlier Undo")
	check(app.history.size()==3 and is_same(app.history[0],stroke),"delete does not evict prior stroke or copy")
	app.undo();check(layer.cels.size()==32 and hash_cel(Drawing.cel_at(layer,4))==painted,"delete Undo restores exact removed drawing")
	app.redo();check(layer.cels.size()==31 and Drawing.cel_at(layer,4).is_empty(),"delete Redo restores empty exposure slot")
	check(app.physics_editor.generation==generation,"copy/delete Undo/Redo preserve independent physics generation")
	app.set_frame(40);app.create_cel(false);var blank: Dictionary=app.history[-1];var empty:=Drawing.blank(1920,1080);var empty_hash:=Storage.image_hash(empty)
	check(blank.type=="cel_patch" and blank.before.is_empty() and blank.after.size()==1 and blank.bytes<=8294400+8192,"blank creation in a gap retains only inserted cel")
	check(hash_cel(Drawing.cel_at(layer,40))==empty_hash and app.history.size()==4,"new blank is transparent and earlier history remains useful")
	generation=app.physics_editor.generation
	app.undo();check(Drawing.cel_at(layer,40).is_empty(),"blank Undo restores gap")
	app.redo();check(hash_cel(Drawing.cel_at(layer,40))==empty_hash,"blank Redo restores exact pixels")
	check(app.physics_editor.generation==generation,"blank Undo/Redo preserve independent physics generation")
	var saved_duration: int=app.video.duration_frames;app.video.duration_frames=401
	for i in range(368):app.layers[0].cels.append({"id":"limit"+str(i),"start":i,"duration":1,"image":image})
	var count: int=app.history.size();app.set_frame(39);app.create_cel(false);check(layer.cels.size()==32 and app.history.size()==count and app.sequence_editor.used("cels")==400,"global400drawing limit refuses additional creation without history mutation")
	app.layers[0].cels.clear();app.video.duration_frames=saved_duration
	var before: Array=layer.cels.duplicate(true);check(not app.apply_command(created,"before") and layer.cels==before,"stale create Undo refuses atomically without erasing later drawings")
	var intact:=true
	for peer in peers:
		var matches: Array=layer.cels.filter(func(cel):return cel.id==peer.id);intact=intact and matches.size()==1 and is_same(matches[0],peer) and hash_cel(peer)==original
	check(intact,"all30peer dictionaries and original pixels stay untouched")
	var child: String=app.sequence_editor.new_sequence("Create isolation");check(not child.is_empty() and app.sequence_editor.enter(child).is_empty(),"actual child opens with shared global cel limit")
	var child_before: Array=app.layers.duplicate(true);check(not app.apply_command(blank,"before") and app.layers==child_before,"parent creation refuses another sequence owner")
	app.sequence_editor.return_to_parent();await settled();layer=app.cel_timing.layer_by_id(blank.layer_id)
	check(app.apply_command(blank,"before") and Drawing.cel_at(layer,40).is_empty() and app.apply_command(blank,"after") and hash_cel(Drawing.cel_at(layer,40))==empty_hash,"stable create target works after actual child round trip")
	print("CREATE_DELETE_HISTORY "+JSON.stringify({"checks":checks,"failures":failures,"owned":owned,"copy_bytes":created.bytes,"delete_bytes":removed.bytes,"blank_bytes":blank.bytes}));await app.quit_studio();quit(0 if failures==0 else 1)
