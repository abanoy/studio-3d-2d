extends "res://tests/movement_path_smoke.gd"
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
var layer_id:=""
var a_id:=""
var b_id:=""
func _initialize() -> void:
	create_timer(1200).timeout.connect(func():push_error("Cel timing watchdog");quit(2));call_deferred("run")
func cel(id: String) -> Dictionary:
	for row in app.cel_timing.layer_by_id(layer_id).get("cels",[]):
		if row.id==id:return row
	return {}
func signature(value: PackedByteArray) -> String:
	var context:=HashingContext.new();context.start(HashingContext.HASH_SHA256);context.update(value);return context.finish().hex_encode()
func press_at(view: Control,point: Vector2) -> void:
	var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.pressed=true;event_at(view,point,event);await process_frame
func move_to(view: Control,point: Vector2) -> void:
	var event:=InputEventMouseMotion.new();event.button_mask=MOUSE_BUTTON_MASK_LEFT;event_at(view,point,event);await process_frame
func release_at(view: Control,point: Vector2) -> void:
	var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event_at(view,point,event);await settled()
func run() -> void:
	var args:=OS.get_cmdline_user_args();folder=args[0];app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("reader-cache" if "--read" in args else "writer-cache")
	if "--read" in args:
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
		for kind in (["packed"] if "--packed-only" in args else ["linked"] if "--linked-only" in args else ["packed","linked"]):
			var path:=folder.path_join(kind+".has");app.has_project.open_file(path);await wait_job()
			layer_id=expected.layer;a_id=expected.a;b_id=expected.b
			check(app.has_project.path==path and cel(a_id).start==1300 and cel(a_id).duration==24 and cel(b_id).start==1376,"cold "+kind+" retains exact moved exposure ranges")
			check(Storage.image_hash(cel(a_id).image)==expected.pixels and signature(app.audio_mix.pcm)==expected.pcm,"cold "+kind+" preserves original RGBA and independent PCM")
			var child_data: Dictionary=app.sequence_editor.asset(expected.child).scene
			check(child_data.layers[1].cels[0].start==80 and child_data.layers[1].cels[0].duration==48 and child_data.layers[1].opacity==.35,"cold "+kind+" preserves independent child exposure and opacity")
			var picture: Image=await app.renderer.capture(app.keys,app.layers,1430,true)
			check(picture.get_data()==Image.load_from_file(folder.path_join("expected-1430.png")).get_data(),"cold "+kind+" reproduces edited child in parent picture")
		print("CEL_TIMING_READ ",JSON.stringify({"checks":checks,"failures":failures}));await app.quit_studio();quit(0 if failures==0 else 1);return
	app.show_project_options();app.project_options.hide();check(app.project_timing.apply_duration(1440).is_empty(),"long parent opens for exposure moves")
	var source:=folder.path_join("room.glb");preload("res://src/scene3d.gd").make_fixture(source);check(app.load_scene(source).is_empty(),"original independent world imports")
	app.video.visibility_fade_ms=0;app.renderer.video_settings=app.video
	var layer: Dictionary=app.layers[1];layer_id=layer.id;layer["opacity"]=.35
	var image_a:=Drawing.blank(1920,1080);image_a.fill_rect(Rect2i(100,100,80,40),Color(.1,.4,.7,.5));Drawing.touch(image_a)
	var image_b:=Drawing.blank(1920,1080);image_b.fill_rect(Rect2i(200,100,60,50),Color(.9,.2,.1,.75));Drawing.touch(image_b)
	Drawing.insert(layer,1300,1440,image_a);layer.cels[0].duration=24;a_id=layer.cels[0].id
	Drawing.insert(layer,1376,1440,image_b);layer.cels[1].duration=24;b_id=layer.cels[1].id;app.changed()
	check(app.import_audio(folder.path_join("tone.wav"),1344).is_empty(),"independent audio imports")
	app.mode.select(0);app.change_mode(0);app.set_frame(1304)
	var nav=app.timeline_navigation;var view=app.timeline;nav.zoom(1.0/16,1304);nav.scrollbar.value=1280;await settled()
	var hold_history: int=app.history.size();var hold_bytes: int=app.history_bytes
	app.exposure.value=12;app.set_exposure()
	check(cel(a_id).start==1300 and cel(a_id).duration==12 and is_same(cel(a_id).image,image_a),"existing exposure control changes only duration and retains exact Image")
	check(app.history.size()==hold_history+1 and app.history[-1].type=="cel_exposure" and app.history_bytes==hold_bytes+512 and not app.history[-1].has("layer") and not app.history[-1].has("image"),"duration edit stores one512byte identity-only command without cel/raster snapshots")
	app.set_exposure();check(app.history.size()==hold_history+1,"unchanged duration creates no redundant history")
	app.undo();check(cel(a_id).duration==24 and is_same(cel(a_id).image,image_a),"duration Undo restores hold without raster copy")
	app.redo();check(cel(a_id).duration==12 and is_same(cel(a_id).image,image_a),"duration Redo restores same image")
	app.undo();app.exposure.value=100;app.set_exposure()
	check(cel(a_id).duration==76 and cel(b_id).start==1376,"existing exposure control clamps at next cel without overwriting it")
	app.undo();app.set_frame(1376);app.exposure.value=100;app.set_exposure()
	check(cel(b_id).duration==64 and cel(a_id).duration==24,"existing exposure control clamps last hold at scene end")
	app.undo();app.set_frame(1304)
	var world: Dictionary=app.current_world().duplicate(true);var shots: Array=app.keys.duplicate(true);var pcm:=signature(app.audio_mix.pcm);var a_pixels:=Storage.image_hash(image_a);var b_pixels:=Storage.image_hash(image_b);var history: int=app.history.size();var bytes: int=app.history_bytes
	var expected: Image=await app.renderer.capture(app.keys,app.layers,1304,true)
	var row:=1;var point:=Vector2(view.x(1304),view.layer_y(row)+12);await press_at(view,point)
	var rig: RefCounted=app.renderer.active_model();var live:=Transform3D(Basis.IDENTITY,Vector3(3,2,1));rig.live_world_transform=live
	check(view.cel_gesture_active() and app.active_layer==1 and app.frame==1304,"press selects exact drawing layer/frame before drag")
	await move_to(view,Vector2(view.x(1344),point.y))
	check(view.cel_preview==1340 and view.cel_valid and cel(a_id).start==1300 and app.history.size()==history,"drag previews new timing without mutating hold/history")
	var checkpoint: int=app.checkpoint_revision;app.autosave_tick(true);check(app.checkpoint_revision==checkpoint,"ordinary recovery defers while exposure gesture is active")
	check(not app.project_timing.apply_duration(1400).is_empty() and app.video.duration_frames==1440,"scene timing refuses mid-gesture coordinate changes")
	await release_at(view,Vector2(view.x(1344),point.y))
	check(cel(a_id).start==1340 and cel(a_id).duration==24 and cel(b_id).start==1376,"release moves complete hold and keeps neighboring timing")
	check(app.history.size()==history+1 and app.history[-1].type=="cel_timing" and app.history_bytes==bytes+512,"move creates one bounded metadata-only Undo command")
	check(is_same(cel(a_id).image,image_a) and Storage.image_hash(image_a)==a_pixels and Storage.image_hash(image_b)==b_pixels,"move retains original Image identity and all RGBA pixels")
	check(app.current_world()==world and app.keys==shots and signature(app.audio_mix.pcm)==pcm and rig.live_world_transform==live,"drawing move preserves world/camera/audio and live preview")
	var moved: Image=await app.renderer.capture(app.keys,app.layers,1344,true);check(moved.get_data()==expected.get_data(),"moved exposure renders identical world+ink at its relative new frame")
	app.undo();check(cel(a_id).start==1300 and is_same(cel(a_id).image,image_a) and rig.live_world_transform==live,"Undo restores timing without raster copy or physics reset")
	app.redo();check(cel(a_id).start==1340 and rig.live_world_transform==live,"Redo reapplies timing without resetting live preview")
	nav.scrollbar.value=1330;await settled();history=app.history.size();var revision: int=app.recovery_revision;point=Vector2(view.x(1344),view.layer_y(row)+12)
	await press_at(view,point);await move_to(view,Vector2(view.x(1374),point.y))
	check(not view.cel_valid and cel(a_id).start==1340,"overlap preview marks invalid without truncating either hold")
	app.get_viewport().get_texture().get_image().save_png(folder.path_join("collision.png"));await release_at(view,Vector2(view.x(1374),point.y))
	check(cel(a_id).start==1340 and cel(b_id).start==1376 and app.history.size()==history and app.recovery_revision==revision,"collision release refuses with exact timing/history/revision preserved")
	nav.scrollbar.value=1350;await settled();point=Vector2(view.x(1354),view.layer_y(row)+12)
	await press_at(view,point);await move_to(view,Vector2(view.size.x-17,point.y));await release_at(view,Vector2(view.size.x-17,point.y))
	check(cel(a_id).start==1416 and cel(a_id).duration==24,"right boundary clamps full hold to scene end without shortening")
	app.undo();check(cel(a_id).start==1340,"boundary move Undo restores original start")
	nav.scrollbar.value=1330;await settled();history=app.history.size();point=Vector2(view.x(1344),view.layer_y(row)+12)
	await press_at(view,point);await move_to(view,Vector2(view.x(1408),point.y))
	var escape:=InputEventKey.new();escape.keycode=KEY_ESCAPE;escape.pressed=true;root.push_input(escape,true);await release_at(view,Vector2(view.x(1408),point.y))
	check(not view.cel_gesture_active() and cel(a_id).start==1340 and app.history.size()==history,"Escape cancels pending exposure without history")
	await click_at(view,point);check(not view.cel_gesture_active() and app.history.size()==history and app.frame==1344,"ordinary click selects/ seeks without moving or history")
	await press_at(view,point);await move_to(view,point+Vector2(2,0));await release_at(view,point+Vector2(2,0))
	check(cel(a_id).start==1340 and app.history.size()==history,"sub-threshold hand motion does not become a timing edit")
	await press_at(view,point);await move_to(view,Vector2(view.x(1408),point.y));history=app.history.size();app.undo();await release_at(view,Vector2(view.x(1408),point.y))
	check(cel(a_id).start==1340 and app.history.size()==history and not view.cel_gesture_active(),"Undo during drag cancels preview instead of undoing an unrelated edit")
	await press_at(view,point);await move_to(view,Vector2(view.x(1408),point.y));var right:=InputEventMouseButton.new();right.button_index=MOUSE_BUTTON_RIGHT;right.pressed=true;event_at(view,point,right);await process_frame;right=InputEventMouseButton.new();right.button_index=MOUSE_BUTTON_RIGHT;event_at(view,point,right);await release_at(view,point)
	check(cel(a_id).start==1340 and app.history.size()==history,"right-click cancellation leaves exact document/history")
	var context: Dictionary=app.cel_timing.begin(layer_id,a_id,1344);app.changed();history=app.history.size();app.cel_timing.commit(a_id,1404,context)
	check(cel(a_id).start==1340 and app.history.size()==history,"stale revision refuses without changing hold or history")
	app.set_frame(1344);var editor=app.sequence_editor;var child: String=editor.new_sequence("Nested drawing timing");check(not child.is_empty() and editor.enter(child).is_empty(),"editable child opens for history rebinding")
	app.mode.select(0);app.change_mode(0);app.active_layer=1;app.set_frame(0);app.create_cel(false)
	var child_layer: String=app.layers[1].id;var child_cel: String=app.layers[1].cels[0].id;var child_image: Image=app.layers[1].cels[0].image;child_image.fill_rect(Rect2i(300,100,60,40),Color.MAGENTA);Drawing.touch(child_image);app.changed();app.layer_editor.set_opacity(35)
	editor.return_to_parent();editor.enter(child);await settled();check(app.frame==0 and app.frame_box.value==0 and app.frame_box.max_value==240,"shorter child restores its saved frame without range-clamp reentry");app.undo()
	check(app.cel_timing.layer_by_id(child_layer).get("opacity",1.0)==1.0,"existing layer-property Undo resolves live layer after scene switch")
	app.undo();check(app.cel_timing.layer_by_id(child_layer).cels.is_empty(),"existing cel-creation Undo resolves live layer after scene switch")
	app.redo();app.redo();check(app.cel_timing.layer_by_id(child_layer).cels[0].id==child_cel and is_same(app.cel_timing.layer_by_id(child_layer).cels[0].image,child_image) and app.cel_timing.layer_by_id(child_layer).opacity==.35,"existing Redo restores same image and opacity in rebuilt child")
	app.exposure.value=48;app.set_exposure();check(app.history[-1].type=="cel_exposure" and app.history[-1].bytes==512,"nested exposure uses bounded duration-only history");editor.return_to_parent();editor.enter(child);await settled();app.undo()
	check(app.cel_timing.layer_by_id(child_layer).cels[0].duration==240,"existing exposure Undo rebinds across child switch")
	app.redo();check(app.cel_timing.layer_by_id(child_layer).cels[0].duration==48 and is_same(app.cel_timing.layer_by_id(child_layer).cels[0].image,child_image),"existing exposure Redo retains its source image")
	var child_context: Dictionary=app.cel_timing.begin(child_layer,child_cel,8);app.cel_timing.commit(child_cel,80,child_context);var child_command: Dictionary=app.history[-1]
	check(app.cel_timing.layer_by_id(child_layer).cels[0].start==80,"child exposure uses same timing command and local clock")
	editor.return_to_parent();await settled();context=app.cel_timing.begin(layer_id,a_id,1344);app.cel_timing.commit(a_id,1300,context);editor.enter(child);editor.return_to_parent();await settled();app.undo()
	check(cel(a_id).start==1340,"parent move Undo resolves stable cel ID after child round trip")
	app.redo();check(cel(a_id).start==1300,"parent move Redo remains independent of child history")
	history=app.history.size();check(not app.apply_command(child_command,"before") and app.history.size()==history and cel(a_id).start==1300,"child timing command cannot mutate parent context")
	check(Storage.image_hash(cel(a_id).image)==a_pixels and Storage.image_hash(cel(b_id).image)==b_pixels and app.current_world()==world and signature(app.audio_mix.pcm)==pcm,"all timing/history operations preserve original pixels/world/audio")
	app.set_frame(1304)
	for kind in ["packed","linked"]:
		var path:=folder.path_join(kind+".has");app.has_project.save_file(path,kind);await wait_job();check(app.has_project.path==path,"nested exposure timings save "+kind)
	for at in [1304,1390,1430]:
		var picture: Image=await app.renderer.capture(app.keys,app.layers,at,true);picture.save_png(folder.path_join("expected-%d.png" % at))
	var movie:="";var seconds:=0.0
	if "--export" in args:
		var export_history: int=app.history.size();point=Vector2(view.x(1304),view.layer_y(1)+12);await press_at(view,point);await move_to(view,Vector2(view.x(1314),point.y))
		var started:=Time.get_ticks_usec();var error: String=await app.export_movie(folder);seconds=(Time.get_ticks_usec()-started)/1000000.0;check(error.is_empty(),"complete60second edited project exports: "+error);movie=app.last_export_folder.path_join("movie.mp4")
		await release_at(view,point);check(not view.cel_gesture_active() and cel(a_id).start==1300 and app.history.size()==export_history,"export cancels uncommitted exposure preview without changing document/history")
		for at in [1304,1390,1430]:check(Image.load_from_file(app.last_export_folder.path_join("frame_%06d.png" % (at+1))).get_data()==Image.load_from_file(folder.path_join("expected-%d.png" % at)).get_data(),"full movie frame%d equals exact exposure/child preview" % at)
	app.set_frame(1304);app.changed()
	while app.recovery_preview.busy():app.poll_recovery_preview();await process_frame
	app.autosave_tick(true);check(app.checkpoint_revision==app.recovery_revision,"ordinary recovery commits moved parent/child exposures")
	FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify({"a":a_id,"b":b_id,"layer":layer_id,"child":child,"pixels":a_pixels,"pcm":pcm,"movie":movie,"render_seconds":seconds,"recovery":app.recovery_session},"",true,true))
	app.get_viewport().get_texture().get_image().save_png(folder.path_join("timing.png"))
	app.tree_exiting.connect(func():FileAccess.open(folder.path_join("graceful-exit.txt"),FileAccess.WRITE).store_string("unexpected"))
	print("CEL_TIMING_SMOKE ",JSON.stringify({"checks":checks,"failures":failures,"movie":movie,"render_seconds":seconds}))
	if "--crash" in args:OS.kill(OS.get_process_id());quit(2);return
	await app.quit_studio();quit(0 if failures==0 else 1)
