extends "res://tests/movement_path_smoke.gd"
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
const Cache=preload("res://src/cel_raster_snapshot_cache.gd")
const Owner=preload("res://src/cel_raster_owner.gd")
const Snapshot=preload("res://src/cel_raster_snapshot.gd")
func _initialize() -> void:
 create_timer(180).timeout.connect(func():push_error("Raster admission app watchdog");quit(2));call_deferred("run")
func stroke() -> void:
 var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.pressed=true;app.canvas_input(event,Vector2(300,200));app.paint_segment(Vector2(330,200));event.pressed=false;app.canvas_input(event,Vector2(330,200))
func copy(at: int) -> void:
 app.set_frame(at);var cel:=Drawing.cel_at(app.layers[1],at);app.cel_clipboard.open_menu(app.layers[1].id,cel.id,at,Vector2i(300,200));app.cel_clipboard.menu.id_pressed.emit(0);await settled()
func run() -> void:
 folder=OS.get_cmdline_user_args()[0];app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache");app.mode.select(0);app.change_mode(0);app.raster_budget.install(Cache.new(0,3*8294400));app.active_layer=1
 app.set_frame(0);app.create_cel(false);app.set_frame(4);app.create_cel(false);app.set_frame(0);app.color.color=Color.RED;app.radius.value=6;app.tool.select(0);stroke();await settled()
 var painted:=Storage.image_hash(Drawing.image(app.layers[1].cels[0]));await copy(0);var clipboard: Dictionary=app.cel_clipboard.clipboard.duplicate();var owner=clipboard.raster_owner
 check(app.raster_budget.sample().accounted_bytes==3*8294400 and app.raster_budget.sample().owners==3,"live cels and separate clipboard fill configured owned budget together")
 var before: Array=app.layers[1].cels.duplicate(true);var history: int=app.history.size();var revision: int=app.recovery_revision
 app.set_frame(8);app.create_cel(false);await settled()
 check(app.layers[1].cels==before and app.history.size()==history and app.recovery_revision==revision,"over-budget Create restores prior exposure structure and preserves history/revision")
 check(app.raster_budget.sample().owners==3 and Storage.image_hash(Drawing.image(app.layers[1].cels[0]))==painted,"rejected creation leaves no registered orphan or pixel damage")
 await copy(4)
 check(app.cel_clipboard.clipboard==clipboard and is_same(app.cel_clipboard.clipboard.raster_owner,owner) and Storage.image_hash(Drawing.image(app.cel_clipboard.clipboard))==painted,"failed replacement Copy keeps the previous frozen clipboard pixels")
 check(app.history.size()==history and app.recovery_revision==revision,"refused Copy remains a nondestructive transient operation")
 clipboard={};owner=null;app.cel_clipboard.clipboard.clear();app.set_frame(8);app.create_cel(false);await settled()
 check(app.layers[1].cels.size()==3 and app.raster_budget.sample().accounted_bytes<=app.raster_budget.sample().owner_limit_bytes,"releasing clipboard authority makes capacity available for an independent new cel")
 app.undo();await settled();check(app.layers[1].cels.size()==2,"admitted Create remains exactly undoable under pressure")
 app.redo();await settled();check(app.layers[1].cels.size()==3 and Storage.image_hash(Drawing.image(app.layers[1].cels[0]))==painted,"admitted Create Redo preserves earlier authored artwork")
 app.has_project.save_file(folder.path_join("admitted.has"),"packed");await wait_job();check(FileAccess.file_exists(folder.path_join("admitted.has")),"normal packed Save streams drawings at the configured ownership bound")
 app.has_project.open_file(folder.path_join("admitted.has"));await wait_job();check(app.has_project.path==folder.path_join("admitted.has") and app.layers[1].cels.size()==3 and Storage.image_hash(Drawing.image(app.layers[1].cels[0]))==painted,"normal packed Open restores exact drawings after budget refusals")
 app.new_project();await settled();app.mode.select(0);app.change_mode(0);app.active_layer=1
 var pixels:=Drawing.blank(1920,1080);pixels.fill_rect(Rect2i(100,100,40,30),Color.BLUE);var captured:=Snapshot.capture(pixels);var cache:=Cache.new(0,8294400+captured.raster.storage_bytes());var cold:=Owner.from_snapshot(captured.raster,cache);var hot:=Owner.from_image(Drawing.blank(1920,1080),cache)
 app.raster_budget.install(cache);app.layers[1].cels=[{"id":"cold","start":0,"duration":4,"raster_owner":cold.owner},{"id":"held","start":4,"duration":44,"raster_owner":hot.owner}];app.set_frame(0);await settled();var original:=Storage.image_hash(pixels);var token: Array=cold.owner.token();history=app.history.size();revision=app.recovery_revision;stroke();await settled()
 check(not cold.owner.is_pinned() and cold.owner.token()==token and Storage.image_hash(Drawing.image(app.layers[1].cels[0]))==original,"over-budget actual brush press leaves cold authority/token/pixels unchanged")
 check(app.history.size()==history and app.recovery_revision==revision and not app.drawing,"refused brush leaves no partial stroke or history entry")
 var picture: Image=await app.renderer.capture(app.keys,app.layers,0,true)
 check(picture!=null and app.raster_budget.sample().accounted_bytes<=cache.owner_limit,"read-only final composition still works at the ownership bound")
 var proof:={"checks":checks,"failures":failures,"scope":"actual app Create/Copy/brush refusal, usable Undo/save/Open and full-bound read; no globalRSS/GPU/temporary-byte bound"};var file:=FileAccess.open(folder.path_join("verification.json"),FileAccess.WRITE);file.store_string(JSON.stringify(proof));file.close();print("RASTER_ADMISSION_SMOKE "+JSON.stringify(proof));await app.quit_studio();quit(0 if failures==0 else 1)
