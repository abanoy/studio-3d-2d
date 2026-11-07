extends "res://tests/fill_smoke.gd"
func _initialize() -> void:
 create_timer(90).timeout.connect(func():push_error("Fill history watchdog");quit(2));call_deferred("run")
func run() -> void:
 var folder: String=OS.get_cmdline_user_args()[0];app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.new_project();app.mode.select(0);app.change_mode(0)
 for i in range(31):app.set_frame(i);app.create_cel(false)
 app.raster_budget_due=Time.get_ticks_msec()+60000;app.exposure.value=1;app.set_exposure();app.set_frame(0);app.radius.value=3;app.brush_pressure.button_pressed=false;app.tool.select(0);app.color.color=Color.BLUE
 var layer: Dictionary=app.layers[1];var empty:=Storage.image_hash(Drawing.image(layer.cels[0]));pointer(Vector2(700,400),true);pointer(Vector2(700,400),false);await settled();var painted:=Storage.image_hash(Drawing.image(layer.cels[0]));var stroke: Dictionary=app.history[-1]
 check(layer.cels.size()==31 and painted!=empty and stroke.type=="pixels","real brush history precedes a new fill near the32cel limit")
 app.set_frame(40);app.tool.select(2);app.color.color=Color.RED;click(Vector2(900,500));await wait_fill()
 check(not app.fill_editor.pending.is_empty() and layer.cels.size()==31,"spill preview does not create a cel or alter history before Apply")
 await click_control(button("Apply fill",app.fill_editor.preview_row));var command: Dictionary=app.history[-1];var filled:=Drawing.cel_at(layer,40)
 check(layer.cels.size()==32 and filled.has("raster_owner") and command.type=="cel_patch" and command.before.is_empty() and command.after.size()==1,"real fill Apply records only one newly owned cel")
 check(command.bytes<=8294400+8192 and app.history.any(func(value):return is_same(value,stroke)),"new fill charges one raster and preserves preceding real brush Undo at31cels")
 var filled_hash:=Storage.image_hash(Drawing.image(filled));check(Drawing.image(filled).get_pixel(900,500)==Color.RED,"new fill installs actual requested pixels")
 app.undo();check(layer.cels.size()==31 and Drawing.cel_at(layer,40).is_empty() and Storage.image_hash(Drawing.image(layer.cels[0]))==painted,"fill Undo removes only its cel and preserves earlier stroke")
 app.undo();check(Storage.image_hash(Drawing.image(layer.cels[0]))==empty,"earlier brush Undo remains reachable after near-limit fill")
 app.redo();app.redo();check(layer.cels.size()==32 and Storage.image_hash(Drawing.image(Drawing.cel_at(layer,40)))==filled_hash and Storage.image_hash(Drawing.image(layer.cels[0]))==painted,"brush and fill Redo restore both authored rasters exactly")
 var proof:={"checks":checks,"failures":failures,"fill_command_bytes":command.bytes,"history_bytes":app.history_bytes,"cels":layer.cels.size()};FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE).store_string(JSON.stringify(proof));print("FILL_CEL_PATCH_SMOKE "+JSON.stringify(proof));await app.quit_studio();quit(0 if failures==0 else 1)
