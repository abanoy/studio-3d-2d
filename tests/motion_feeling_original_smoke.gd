extends "res://tests/shortcut_editor_smoke.gd"
const Fixture=preload("res://tests/body_curve_fixture.gd")
const Model=preload("res://src/model.gd")
const Motion=preload("res://src/motion_animation.gd")
var actor_id:=""
func actor():return app.renderer.world_runtime.instance(actor_id)
func same(a,b) -> bool:return JSON.parse_string(JSON.stringify(a,"",true,true))==JSON.parse_string(JSON.stringify(b,"",true,true))
func values(at: float) -> Dictionary:return {"pose":actor().sample(at),"root":actor().sample_transform(at)}
func stamp(at: float) -> String:return JSON.stringify(JSON.parse_string(JSON.stringify(values(at),"",true,true)),"",true,true).sha256_text()
func button_named(node: Node,text: String) -> Button:
	if node is Button and node.text==text:return node
	for child in node.get_children():
		var found:=button_named(child,text)
		if found:return found
	return null
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0];var reading: bool="--read" in OS.get_cmdline_user_args()
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("reader-cache" if reading else "writer-cache")
	var packed:=folder.path_join("Motion feeling.has");var source:=folder.path_join("original-branches.glb")
	if reading:
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")));actor_id=expected.id;app.has_project.open_file(packed);await wait_job()
		check(actor()!=null and actor().motion_enabled() and str(actor().data.source).begins_with(app.has_project.cache_root) and not FileAccess.file_exists(source),"cold packed motion uses its new cache with original source offline")
		check(same(actor().data.motion_assist,expected.settings),"cold reader retains exact part and helper correction intent")
		var exact:=true
		for at in [48,36,24,18,12,10,6,0]:exact=exact and stamp(at)==expected.samples[str(at)]
		check(exact,"cold reverse seek reproduces all authored and assisted samples exactly")
		check(Storage.image_hash(Drawing.image(Drawing.cel_at(app.layers[1],0)))==expected.paint,"cold motion replay preserves independent editable drawing")
		check(Storage.image_hash(await app.renderer.capture(app.keys,app.layers,10,true))==expected.render,"cold movie frame input matches the writer exactly")
		print("MOTION_ORIGINAL_READ ",JSON.stringify({"checks":checks,"failures":failures}));app.free();quit(0 if failures==0 else 1);return
	check(Fixture.create(source)==OK and app.pose_editor.add_model(source).is_empty(),"original two-branch skinned model loads through normal editor")
	actor_id=app.renderer.active_model().data.id;app.physics_editor.freeze_all();var left: String=actor().order[0];var right: String=actor().order[1]
	var base: Dictionary=actor().data.duplicate(true)
	for at in [0,12,24]:
		var pose: Dictionary={}
		for id in [left,right]:
			var value:=Model.identity();var q:=Quaternion(Vector3.FORWARD,(.8 if id==left else -.4) if at==12 else 0.);value.rotation_xyzw=[q.x,q.y,q.z,q.w];pose[id]=value
		var root_value: Dictionary=Model.Clips.transform(base);root_value.position[0]=.1 if at==12 else 0.
		base.pose_keys.append({"frame":at,"pose":pose,"transform":root_value,"interpolation":"ease"})
	check(app.pose_editor.restore_state(base).is_empty(),"normal authored three-pose study installs without native ecosystem declarations")
	app.history.clear();app.redo_history.clear();app.history_bytes=0;app.mode.select(2);app.change_mode(2);app.set_frame(10);app.set_advanced(false);app.pose_editor.frame_model();var camera: Camera3D=app.renderer.camera;app.keys=[Model.Timeline.key(0,camera.position,camera.quaternion,camera.fov)]
	var image:=Drawing.blank(1920,1080);image.fill_rect(Rect2i(100,100,80,60),Color.CYAN);Drawing.insert(app.layers[1],0,48,image);app.changed();var paint:=Storage.image_hash(image);var source_sha:=FileAccess.get_sha256(source);var shots: Array=app.keys.duplicate(true)
	var baseline: Dictionary={};var main: Dictionary={}
	for at in [0,6,10,12,18,24,36,48]:baseline[str(at)]=values(at)
	for at in [0,12,24]:main[str(at)]=values(at)
	var original: Dictionary=actor().data.duplicate(true);var ui=app.pose_editor.motion;ui.sync();await settle();app.inspector_scroll.ensure_control_visible(ui.button);await settle();check(app.inspector_scroll.get_global_rect().encloses(ui.button.get_global_rect()),"complete Simple motion button is scroll-accessible");await click(ui.button)
	root.get_texture().get_image().save_png(folder.path_join("simple-motion.png"))
	check(ui.window.visible and ui.enabled.button_pressed and actor().data==original and app.history.is_empty(),"actual Simple trial opens without changing scene or history")
	await click(button_named(ui.window,"Cancel"));check(actor().data==original and app.history.is_empty(),"Cancel leaves exact authored study and history intact")
	await click(ui.button);await click(button_named(ui.window,"Apply"))
	check(actor().data.format==Model.MOTION_FORMAT and actor().motion_enabled() and app.history.size()==1,"actual Apply saves assistance once in ordinary model data")
	if not actor().motion_enabled():app.free();quit(1);return
	check(not same(values(10),baseline["10"]),"normal sampler visibly changes in-between motion")
	var exact:=true
	for at in [0,12,24]:exact=exact and same(values(at),main[str(at)])
	check(exact,"all authoritative main poses and root controls remain exact")
	var enabled: Dictionary=actor().data.duplicate(true);app.undo();check(same(actor().data,original) and same(values(10),baseline["10"]),"one Undo restores exact original model and motion");app.redo();check(same(actor().data,enabled),"Redo restores exact assistance intent")
	var samples: Array=[];var unchanged: Dictionary=actor().data.duplicate(true)
	for half in range(97):samples.append(stamp(float(half)/2))
	var reverse:=true
	for half in range(96,-1,-1):reverse=reverse and stamp(float(half)/2)==samples[half]
	check(reverse and actor().data==unchanged and actor().evaluation_error.is_empty(),"half-frame seek is reverse exact and leaves authored data unchanged")
	app.set_advanced(true);ui.open();await settle();check(ui.helpers.visible and ui.helpers.get_root().get_child_count()>0,"Advanced exposes generated helper records")
	ui.part_choice.select(ui.part_ids.find(left));ui.refresh_part();ui.part_override.button_pressed=true;ui.part_strength.value=0.;await click(button_named(ui.window,"Apply"))
	check(same(actor().sample(10)[left],baseline["10"].pose[left]) and not same(actor().sample_transform(10),baseline["10"].root),"per-part zero keeps the chosen arm authored while the root remains assisted")
	var roots_before_helper: Array=[]
	for half in range(97):roots_before_helper.append(actor().sample_transform(float(half)/2))
	ui.open();await settle();var chosen: TreeItem=ui.helpers.get_root().get_first_child()
	while chosen:
		var data: Dictionary=chosen.get_metadata(0)
		if data.part=="@root" and data.helper.get("editable",false):break
		chosen=chosen.get_next()
	check(chosen!=null,"an editable generated root helper is available for correction")
	if not chosen:app.free();quit(1);return
	chosen.select(0);ui.refresh_helper();var helper: Dictionary=chosen.get_metadata(0);ui.helper_phase.value=.25;ui.helper_amount.value=.5;await click(button_named(ui.window,"Apply"))
	check(actor().data.motion_assist.track_helper_edits["@root"][helper.helper.id]=={"phase":.25,"amount":.5},"Apply stores exact user helper timing and amount correction")
	var helper_changes_motion:=false
	for half in range(97):helper_changes_motion=helper_changes_motion or not same(actor().sample_transform(float(half)/2),roots_before_helper[half])
	check(helper_changes_motion,"user helper correction changes actual intermediate root motion")
	exact=true
	for at in [0,12,24]:exact=exact and same(values(at),main[str(at)])
	check(exact,"part and helper corrections preserve every main endpoint")
	var corrected: Dictionary=actor().data.duplicate(true);ui.open();await settle();ui.enabled.button_pressed=false;await click(button_named(ui.window,"Apply"));check(not actor().motion_enabled() and same(values(10),baseline["10"]),"saved Off restores exact authored motion");app.undo();check(same(actor().data,corrected),"Undo Off restores corrected assistance")
	check(app.keys==shots and Storage.image_hash(image)==paint and FileAccess.get_sha256(source)==source_sha,"all motion controls preserve camera keys, drawing and original source")
	app.set_frame(10);var preview: Image=await app.renderer.capture(app.keys,app.layers,10,true);app.has_project.save_file(packed,"packed");await wait_job();check(app.has_project.path==packed,"ordinary packed Save includes editable assistance intent")
	var error: String=await app.export_movie(folder);check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000011.png")).get_data()==preview.get_data(),"actual movie input equals assisted camera/model plus independent drawing")
	var saved_samples: Dictionary={}
	for at in [0,6,10,12,18,24,36,48]:saved_samples[str(at)]=stamp(at)
	var expected:={"id":actor_id,"settings":actor().data.motion_assist,"samples":saved_samples,"paint":paint,"render":Storage.image_hash(preview)};var file:=FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE);file.store_string(JSON.stringify(expected,"",true,true));file.close()
	print("MOTION_ORIGINAL_WRITE ",JSON.stringify({"checks":checks,"failures":failures,"movie":app.last_export_folder.path_join("movie.mp4")}));app.free();quit(0 if failures==0 else 1)
