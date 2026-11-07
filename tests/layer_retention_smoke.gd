extends "res://tests/movement_path_smoke.gd"
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
const Snapshot=preload("res://src/cel_raster_snapshot.gd")
const Owner=preload("res://src/cel_raster_owner.gd")
const Cache=preload("res://src/cel_raster_snapshot_cache.gd")
func _initialize() -> void:
 create_timer(150).timeout.connect(func():push_error("Layer retained history watchdog");quit(2));call_deferred("run")
func run() -> void:
 folder=OS.get_cmdline_user_args()[0];app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
 var cache:=Cache.new();var originals: Array=[]
 for i in range(12):
  var image:=Drawing.blank(1920,1080);image.fill_rect(Rect2i(100+i*7,100,60,40),Color(float(i+1)/13.0,.3,.7,.5));var captured:=Snapshot.capture(image);originals.append(Storage.image_hash(image));app.layers[1].cels.append({"id":"art"+str(i),"start":i*4,"duration":4,"raster_owner":Owner.from_snapshot(captured.raster,cache).owner})
 app.raster_budget.install(cache);app.mode.select(0);app.change_mode(0);app.active_layer=1;app.refresh_layer_choices();app.set_frame(0);await settled();var world: Dictionary=app.current_world().duplicate(true);var keys: Array=app.keys.duplicate(true)
 app.tool.select(0);app.color.color=Color.RED;app.radius.value=6
 var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.pressed=true;app.canvas_input(event,Vector2(300,200));app.paint_segment(Vector2(330,200));event.pressed=false;app.canvas_input(event,Vector2(330,200));await settled()
 var owner=app.layers[1].cels[0].raster_owner;var edited:=Storage.image_hash(Drawing.image(app.layers[1].cels[0]))
 check(edited!=originals[0] and app.history.size()==1 and app.history[0].type=="pixels","actual brush creates prior useful pixel history")
 check(owner.cool().get("cooled",false),"prior brush owner can cool with owner-addressed history")
 var retained:=0
 for cel in app.layers[1].cels:retained+=Drawing.raster_bytes(cel)
 check(retained<1024*1024 and app.raster_budget.sample().cold_payload_bytes==retained,"twelve unique cold drawings retain under1MiB with measured shared ownership")
 app.layer_editor.request_remove();check(app.layer_editor.confirmation.visible,"populated layer removal uses actual confirmation")
 app.layer_editor.confirm_remove();await settled()
 check(app.layers.size()==1 and app.history.size()==2 and app.history[0].type=="pixels","deleting compact cold layer retains the preceding brush Undo")
 var charge: int=app.history[-1].bytes
 check(charge==retained and charge<1024*1024,"layer removal charges retained pixels rather than twelve full decoded canvases")
 check(app.raster_budget.sample().owners==12,"deleted drawings stay registered while structural Undo owns them")
 app.undo();await settled();check(app.layers.size()==2 and app.layers[1].cels.size()==12 and Storage.image_hash(Drawing.image(app.layers[1].cels[0]))==edited,"layer Undo restores all drawings and exact edited first cel")
 app.undo();await settled();check(Storage.image_hash(Drawing.image(app.layers[1].cels[0]))==originals[0],"preceding brush Undo remains useful after restoring the deleted layer")
 app.redo();app.redo();await settled();check(app.layers.size()==1,"brush and layer Redo restore deletion in the correct order")
 app.undo();await settled();var exact:=true
 for i in range(12):exact=exact and Storage.image_hash(Drawing.image(app.layers[1].cels[i]))==(edited if i==0 else originals[i])
 check(exact and app.current_world()==world and app.keys==keys,"restored editable drawings remain exact without changing 3D or camera")
 var before: Image=await app.renderer.capture(app.keys,app.layers,0,true);app.has_project.save_file(folder.path_join("retained.has"),"packed");await wait_job()
 check(FileAccess.file_exists(folder.path_join("retained.has")),"ordinary packed Save accepts restored layer after history navigation")
 app.has_project.open_file(folder.path_join("retained.has"));await wait_job();var after: Image=await app.renderer.capture(app.keys,app.layers,0,true)
 check(app.layers[1].cels.size()==12 and after.get_data()==before.get_data(),"ordinary packed reopen keeps restored pixels and exact final composition")
 var proof:={"checks":checks,"failures":failures,"retained_pixel_bytes":retained,"removal_charge":charge,"decoded_reservation":12*1920*1080*4,"scope":"unique owned sparse cold layer and preceding brush history; not global RSS/admission or native-platform acceptance"}
 var file:=FileAccess.open(folder.path_join("verification.json"),FileAccess.WRITE);file.store_string(JSON.stringify(proof));file.close();print("LAYER_RETENTION_SMOKE "+JSON.stringify(proof));await app.quit_studio();quit(0 if failures==0 else 1)
