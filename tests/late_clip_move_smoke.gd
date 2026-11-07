extends "res://tests/movement_path_smoke.gd"
const Drawing=preload("res://src/drawing.gd")
const World=preload("res://src/world_document.gd")
const Components=preload("res://src/root_component_document.gd")
const Timeline=preload("res://src/timeline.gd")
const Clips=preload("res://src/animation_clips.gd")
const Storage=preload("res://src/storage.gd")
func _initialize() -> void:
	create_timer(220).timeout.connect(func():push_error("Late clip move watchdog");quit(2));call_deferred("run")
func canonical(value):return JSON.parse_string(JSON.stringify(value,"",true,true))
func digest(value: PackedByteArray) -> String:
	var context:=HashingContext.new();context.start(HashingContext.HASH_SHA256);context.update(value);return context.finish().hex_encode()
func run() -> void:
	var args:=OS.get_cmdline_user_args();folder=args[0];app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("reader-cache" if "--read" in args else "writer-cache")
	if "--read" in args:
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
		var path:=folder.path_join("packed.has");app.has_project.open_file(path);await wait_job()
		check(app.has_project.path==path and app.video.duration_frames==3600 and app.video.fps_num==60,"cold packed project restores60fps/60seconds")
		check(canonical(World.portable(app.current_world()))==expected.world,"cold reader preserves every relative source control and independent world row")
		check(digest(app.audio_mix.pcm)==expected.pcm and Storage.image_hash(Drawing.image(Drawing.cel_at(app.layers[1],0)))==expected.paint,"cold reader retains independent sound/ink exactly")
		var rig: RefCounted=app.renderer.world_runtime.instance(expected.id)
		check(rig.data.start_frame==0 and rig.data.animation_clips[0].start==0 and rig.data.animation_clips[0].keys==expected.piece.keys,"cold reader retains source-time keys after3000frame move")
		var picture: Image=await app.renderer.capture(app.keys,[],12,true)
		check(picture.get_data()==Image.load_from_file(folder.path_join("moved.png")).get_data(),"cold moved model reproduces original frame12 picture")
		print("LATE_CLIP_MOVE_READ ",JSON.stringify({"checks":checks,"failures":failures}));await app.quit_studio();quit(0 if failures==0 else 1);return
	app.show_project_options();app.project_options.hide()
	check(app.project_timing.apply_values(60,1).is_empty() and app.project_timing.apply_duration(3600).is_empty(),"project supports the decided frame3000 operation")
	# Explicit hard visibility cuts isolate structural motion from elapsed fades.
	app.video.visibility_fade_ms=0;app.renderer.video_settings=app.video
	var asset:=folder.path_join("actor.glb");var map:=folder.path_join("room.glb");preload("res://src/scene3d.gd").make_pose_fixture(asset);preload("res://src/scene3d.gd").make_fixture(map)
	check(app.load_scene(map).is_empty(),"original independent background imports")
	var map_id: String=app.last_import_id;var placement: Dictionary=app.import_actions.placement();placement.physics_on_import=false
	check(app.pose_editor.add_model(asset,3000,placement).is_empty(),"original actor is introduced at frame3000")
	var id: String=app.last_import_id;var rig: RefCounted=app.renderer.active_model();var editor=app.pose_editor
	for at in [3000,3012,3024]:
		app.set_frame(at);editor.selected="@root";editor.operation.select(1);editor.refresh_values();editor.fields[0].value=float(at-3000)/12;editor.apply_numeric()
	var bone: String=rig.order[1]
	for at in [3012,3024]:
		app.set_frame(at);editor.tree_items[bone].select(0);editor.operation.select(0);editor.refresh_values();editor.fields[2].value=35 if at==3012 else 60;editor.apply_numeric()
	if "--components" in args:
		var promoted:=Components.promote(rig.data,3600);check(not promoted.has("error") and editor.restore_state(promoted.data).is_empty(),"independent Model9 components accept late source controls")
	check(rig.data.animation_clips.size()==1 and rig.data.animation_clips[0].start==3000,"authored late take stays one editable source interval")
	var peer_placement:=placement.duplicate(true);check(app.pose_editor.add_model(asset,0,peer_placement).is_empty(),"same original asset has an independent peer")
	var peer: String=app.last_import_id;rig=app.renderer.world_runtime.instance(id);app.world_selection.select_entity(id);app.set_frame(3012);editor.frame_model()
	var camera: Camera3D=app.renderer.camera;app.keys=[Timeline.key(0,camera.position,camera.quaternion,camera.fov)]
	Drawing.insert(app.layers[1],0,3600,Drawing.blank(1920,1080));var ink: Dictionary=Drawing.cel_at(app.layers[1],0);Drawing.edit_image(ink).image.fill_rect(Rect2i(80,80,80,20),Color.CYAN);Drawing.touch(Drawing.image(ink));app.changed()
	check(app.import_audio(folder.path_join("tone.wav"),3000).is_empty(),"independent sound stays at frame3000")
	app.world_selection.select_entity(id);app.set_frame(3012);await settled()
	var before: Dictionary=rig.data.duplicate(true);var peer_before: Dictionary=app.renderer.world_runtime.instance(peer).data.duplicate(true);var map_before: Dictionary=app.renderer.world_runtime.instance(map_id).data.duplicate(true)
	var audio: Dictionary=app.audio_document().duplicate(true);var pcm:=digest(app.audio_mix.pcm);var paint:=Storage.image_hash(Drawing.image(ink));var shots: Array=app.keys.duplicate(true);var history: int=app.history.size()
	var reference: Image=await app.renderer.capture(app.keys,[],3012,true);reference.save_png(folder.path_join("before.png"))
	var view=app.timeline;app.timeline_navigation.fit_all();await settled()
	var row: int=view.object_rows.find_custom(func(item):return item.id==id)
	var point:=Vector2(view.x(3006),view.row_y(row)+12);var piece_id: String=view.piece_at(before,row,point)
	check(row>=0 and not piece_id.is_empty(),"fitted timeline exposes the late editable block as a pointer target")
	var press:=InputEventMouseButton.new();press.button_index=MOUSE_BUTTON_LEFT;press.pressed=true;event_at(view,point,press);await process_frame
	var motion:=InputEventMouseMotion.new();motion.button_mask=MOUSE_BUTTON_MASK_LEFT;motion.relative=Vector2(view.x(6)-view.x(3006),0);event_at(view,point+motion.relative,motion);await process_frame
	check(view.moving_id==id and view.moving_delta==-3000 and rig.data==before and app.history.size()==history,"real drag previews exactly minus3000frames without changing keys/history")
	var release:=InputEventMouseButton.new();release.button_index=MOUSE_BUTTON_LEFT;event_at(view,point+motion.relative,release);await settled()
	var expected_piece: Dictionary=before.animation_clips[0].duplicate(true);expected_piece.start=0
	FileAccess.open(folder.path_join("before-model.json"),FileAccess.WRITE).store_string(JSON.stringify(before,"\t",true,true))
	FileAccess.open(folder.path_join("moved-model.json"),FileAccess.WRITE).store_string(JSON.stringify(rig.data,"\t",true,true))
	check(rig.data.start_frame==0 and rig.data.animation_clips[0]==expected_piece,"one direct timeline drag moves introduction and full source interval to frame0")
	check(app.history.size()==history+1 and view.moving_id.is_empty(),"3000frame move is one Undo command")
	check(rig.data.get("root_components",{})==before.get("root_components",{}),"component source curves remain exact during structural movement")
	check(app.renderer.world_runtime.instance(peer).data==peer_before and app.renderer.world_runtime.instance(map_id).data==map_before,"moving the take preserves peer and background documents")
	check(app.audio_document()==audio and digest(app.audio_mix.pcm)==pcm and Storage.image_hash(Drawing.image(ink))==paint and app.keys==shots,"independent sound ink and camera keys stay unchanged")
	var moved: Dictionary=rig.data.duplicate(true);var old:=Model.new();old.data=before;old.motion_video=app.video;var current:=Model.new();current.data=moved;current.motion_video=app.video
	var exact:=true
	for quarter in range(97):
		var at:=float(quarter)/4
		var same: bool=old.sample_transform(at+3000)==current.sample_transform(at) and old.sample(at+3000)==current.sample(at)
		if not same and exact:print("LATE_SAMPLE_DIFF ",at," ",JSON.stringify({"old_transform":old.sample_transform(at+3000),"new_transform":current.sample_transform(at),"old_pose":old.sample(at+3000),"new_pose":current.sample(at)},"",true,true))
		exact=exact and same
	check(exact,"all97quarter-frame root and bone samples retain original relative motion")
	var picture: Image=await app.renderer.capture(app.keys,[],12,true);picture.save_png(folder.path_join("moved.png"));check(picture.get_data()==reference.get_data(),"moved frame12 exactly repeats original frame3012 world pixels")
	app.undo();check(rig.data==before and digest(app.audio_mix.pcm)==pcm,"Undo restores exact late take and independent PCM")
	app.redo();check(rig.data==moved,"Redo restores exact moved take")
	app.set_frame(12);app.has_project.save_file(folder.path_join("packed.has"),"packed");await wait_job();check(app.has_project.path==folder.path_join("packed.has"),"moved long project saves as packed schema8")
	app.changed();while app.recovery_preview.busy():app.poll_recovery_preview();await process_frame
	app.autosave_tick(true);await preload("res://tests/recovery_wait.gd").checkpoint(app);check(app.checkpoint_revision==app.recovery_revision,"ordinary recovery commits moved relative motion")
	FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify({"world":World.portable(app.current_world()),"id":id,"pcm":pcm,"paint":paint,"piece":moved.animation_clips[0],"recovery":app.recovery_session},"",true,true))
	app.tree_exiting.connect(func():FileAccess.open(folder.path_join("graceful-exit.txt"),FileAccess.WRITE).store_string("unexpected"))
	print("LATE_CLIP_MOVE_SMOKE ",JSON.stringify({"checks":checks,"failures":failures,"components":"--components" in args}))
	if "--crash" in args:OS.kill(OS.get_process_id());quit(2);return
	await app.quit_studio();quit(0 if failures==0 else 1)
