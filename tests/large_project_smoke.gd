extends "res://tests/movement_path_smoke.gd"
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
func _initialize() -> void:
 create_timer(600).timeout.connect(func():push_error("Large project watchdog");quit(2));call_deferred("run")
func total() -> int:
 var n:=0
 for layer in app.layers:n+=layer.cels.size()
 return n
func hashes() -> Array:
 var result: Array=[]
 for layer in app.layers:
  for cel in layer.cels:
   var captured: Dictionary=cel.raster_owner.snapshot()
   if captured.has("error"):return []
   result.append(captured.raster.pixel_sha256())
 return result
func run() -> void:
 var args:=OS.get_cmdline_user_args();folder=args[0];app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
 var start:=Time.get_ticks_msec();check(app.open_project(args[1]),"ordinary Open accepts four layers of100unique drawings");await settled();var load_ms:=Time.get_ticks_msec()-start
 if total()!=400:print("LARGE_PROJECT_ABORT ",app.open_project_error);await app.quit_studio();quit(1);return
 var original:=hashes();var ids:={}
 for layer in app.layers:
  for cel in layer.cels:ids[Drawing.raster_token(cel)[0]]=true
 check(original.size()==400 and ids.size()==400 and app.raster_budget.sample().owners==400,"all400drawings have independent admitted owners")
 app.mode.select(0);app.change_mode(0)
 for at in [99,0,37,73]:
  app.set_frame(at);await settled();check(app.canvas.overlay.get_image().get_data()==Drawing.composite(app.layers,at,1920,1080).get_data(),"actual GPU preview matches dense composition at frame"+str(at))
 app.active_layer=3;app.refresh_layer_choices();app.set_frame(100);var history: int=app.history.size();var revision: int=app.recovery_revision;app.create_cel(false)
 check(total()==400 and app.history.size()==history and app.recovery_revision==revision,"401st Create refuses without changing drawings/history")
 app.set_frame(99);app.delete_cel();app.set_frame(100);app.create_cel(false);check(total()==400,"deleting one drawing permits another within the count and byte budgets")
 app.undo();app.undo();check(total()==400 and hashes()==original,"structural Undo restores every original dense drawing exactly")
 app.active_layer=1;app.refresh_layer_choices();app.set_frame(37);app.tool.select(0);app.brush_pressure.button_pressed=false;app.color.color=Color.RED;app.radius.value=6
 var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.pressed=true;app.canvas_input(event,Vector2(300,200));app.paint_segment(Vector2(330,200));event.pressed=false;app.canvas_input(event,Vector2(330,200));await settled();var edited:=hashes()
 check(edited.size()==400 and edited[137]!=original[137] and edited.slice(0,137)==original.slice(0,137) and edited.slice(138)==original.slice(138),"actual brush changes one of400drawings without touching399peers")
 app.undo();check(hashes()==original,"dense brush Undo restores exact original pixels");app.redo();check(hashes()==edited,"dense brush Redo restores exact authored pixels")
 var picture: Image=await app.renderer.capture(app.keys,app.layers,37,true);picture.save_png(folder.path_join("expected.png"));picture=null
 start=Time.get_ticks_msec();app.has_project.save_file(folder.path_join("large.has"),"packed");await wait_job();var save_ms:=Time.get_ticks_msec()-start
 check(FileAccess.file_exists(folder.path_join("large.has")) and app.has_project.path==folder.path_join("large.has"),"ordinary packed Save commits400unique drawing payloads")
 start=Time.get_ticks_msec();app.has_project.open_file(folder.path_join("large.has"));await wait_job();var open_ms:=Time.get_ticks_msec()-start
 check(app.has_project.path==folder.path_join("large.has") and total()==400 and hashes()==edited,"ordinary packed Open retains all400editable pixel identities")
 picture=await app.renderer.capture(app.keys,app.layers,37,true);check(picture.get_data()==Image.load_from_file(folder.path_join("expected.png")).get_data(),"packed reopen final GPU composition equals original exactly")
 var state: Dictionary=app.raster_budget.sample();check(state.accounted_bytes<=state.owner_limit_bytes,"large project remains inside registered drawing admission")
 var proof:={"checks":checks,"failures":failures,"load_ms":load_ms,"save_ms":save_ms,"packed_open_ms":open_ms,"memory":state,"scope":"ordinary400drawing GUI/edit/packed roundtrip; separate cold/crash/media verification remains"};var file:=FileAccess.open(folder.path_join("verification.json"),FileAccess.WRITE);file.store_string(JSON.stringify(proof));file.close();print("LARGE_PROJECT_SMOKE "+JSON.stringify(proof));await app.quit_studio();quit(0 if failures==0 else 1)
