extends "res://tests/cel_raster_budget_smoke.gd"
func run() -> void:
 folder=OS.get_cmdline_user_args()[0];app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache");app.new_project();app.mode.select(0);app.change_mode(0);app.raster_budget_due=Time.get_ticks_msec()+60000
 var layer: Dictionary=app.layers[1]
 for i in range(12):app.set_frame(i);app.create_cel(false)
 check(layer.cels.size()==12 and layer.cels.all(func(cel):return cel.has("raster_owner") and not cel.has("image")) and app.raster_budget.sample().owners==12,"ordinary New and twelve blank cels install independent registered ownership before history")
 var blank:=Drawing.blank(1920,1080);var blank_hash:=Storage.image_hash(blank);blank=null;var edited: Array=[]
 app.tool.select(0);app.brush_pressure.button_pressed=false;app.radius.value=3;app.color.color=Color.RED;app.raster_budget_due=Time.get_ticks_msec()+60000
 for i in range(12):
  app.set_frame(i);var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.pressed=true;app.canvas_input(event,Vector2(400+i,300));app.paint_segment(Vector2(420+i,310));event.pressed=false;app.canvas_input(event,Vector2(420+i,310));await process_frame;edited.append(pixel_hash(layer.cels[i]))
 var peak: Dictionary=app.raster_budget.sample();check(peak.hot_owners==12 and peak.hot_bytes==12*8294400,"new authored artwork is counted in the soft budget without needing Save/Open")
 check(app.history.slice(-12).all(func(command):return command.type=="pixels" and command.has("raster_owner") and not command.has("image")),"new cel brush history owns logical targets rather than full writable Image handles")
 var created_owner=layer.cels[11].raster_owner;app.raster_budget_due=0;var start:=Time.get_ticks_msec()
 while Time.get_ticks_msec()-start<16000:
  var state: Dictionary=app.raster_budget.sample()
  if state.hot_bytes+state.decoded_cache_bytes<=state.target_bytes:break
  await process_frame
 var cooled: Dictionary=app.raster_budget.sample();var idle_ms:=Time.get_ticks_msec()-start
 check(cooled.hot_bytes+cooled.decoded_cache_bytes<=cooled.target_bytes and app.raster_budget.releases>0 and created_owner.is_pinned(),"natural idle cools inactive newly authored drawings while preserving current editable cel")
 app.raster_budget_due=Time.get_ticks_msec()+60000;var exact:=true
 for i in range(12):exact=exact and pixel_hash(layer.cels[i])==edited[i]
 check(exact,"all twelve authored RGBA rasters remain exact after idle cooling")
 for i in range(11,-1,-1):app.undo();exact=exact and pixel_hash(layer.cels[i])==blank_hash
 check(exact and app.redo_history.size()==12,"all twelve real brush Undo commands restore exact new blank cels after cooling")
 app.undo();check(layer.cels.size()==11,"creation Undo still removes only last logical cel after pixel Undo")
 app.redo();check(layer.cels.size()==12 and is_same(layer.cels[11].raster_owner,created_owner),"creation Redo restores exact logical owner needed by later pixel history")
 for i in range(12):app.redo();exact=exact and pixel_hash(layer.cels[i])==edited[i]
 check(exact,"creation and all later brush Redo restore every authored pixel exactly")
 app.set_frame(24);app.create_cel(true);var copied:=Drawing.cel_at(layer,24);check(copied.has("raster_owner") and copied.raster_owner!=created_owner and pixel_hash(copied)==edited[11],"ordinary Copy creates an independent budgeted owner with exact source pixels")
 app.has_project.save_file(folder.path_join("New drawing.has"),"packed");await wait_job();check(FileAccess.file_exists(folder.path_join("New drawing.has")),"new owned drawings save through ordinary packed HAS")
 app.has_project.open_file(folder.path_join("New drawing.has"));await wait_job();var loaded: Dictionary=app.layers[1];exact=loaded.cels.size()==13
 for i in range(12):exact=exact and pixel_hash(loaded.cels[i])==edited[i]
 check(exact and pixel_hash(loaded.cels[12])==edited[11],"ordinary packed reopen restores all new/copy drawing pixels and identities")
 var proof:={"checks":checks,"failures":failures,"peak":peak,"cooled":cooled,"idle_ms":idle_ms,"released_bytes":peak.hot_bytes+peak.decoded_cache_bytes-cooled.hot_bytes-cooled.decoded_cache_bytes,"scope":"new authored drawing owned-hot/decoded-cache accounting only; not RSS/GPU/global/history/raw fallback bound"};FileAccess.open(folder.path_join("new-cel-owner-result.json"),FileAccess.WRITE).store_string(JSON.stringify(proof));print("NEW_CEL_OWNER_SMOKE "+JSON.stringify(proof));await app.quit_studio();quit(0 if failures==0 else 1)
