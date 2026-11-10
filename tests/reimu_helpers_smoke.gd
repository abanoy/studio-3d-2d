extends SceneTree
const Storage=preload("res://src/storage.gd")
const Drawing=preload("res://src/drawing.gd")
const Timeline=preload("res://src/timeline.gd")
const Airflow=preload("res://src/airflow.gd")
var checks:=0
var failures:=0
var app
func _initialize() -> void:
	create_timer(240).timeout.connect(func():push_error("Reimu helper watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settle() -> void:
	for i in range(5):await process_frame
	await RenderingServer.frame_post_draw
func review_ready(helper) -> void:
	while helper.pid>0:await process_frame
	await settle()
func project_ready() -> void:
	while app.has_project.pid>0:await process_frame
	await settle()
func start_hair(id: String) -> bool:
	app.world_selection.select_entity(id,false);await settle();app.physics_editor.hair_toggle.button_pressed=true
	while app.physics_editor.pending.has(id):await process_frame
	await settle();return app.physics_editor.active(id)
func image_difference(a: Image,b: Image) -> Dictionary:
	var aa:=a.get_data();var bb:=b.get_data();var changed:=0;var total:=0
	for i in range(aa.size()):
		if aa[i]!=bb[i]:changed+=1;total+=absi(int(aa[i])-int(bb[i]))
	return {"changed_channels":changed,"mean":float(total)/aa.size()}
func finish(folder: String,extra: Dictionary={}) -> void:
	var result:={"checks":checks,"failures":failures};result.merge(extra)
	FileAccess.open(folder.path_join(str(extra.get("mode","probe"))+"-result.json"),FileAccess.WRITE).store_string(JSON.stringify(result,"",true,true));print("REIMU_HELPERS "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0];var source: String=args[1]
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("reader-cache" if "--read" in args else "cache")
	if "--read" in args:
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
		# authored_keys projects integer timeline frames; JSON reads them as floats.
		# Match that documented projection without rounding any recorded pose values.
		# Python independently checks packed decimals against the writer oracle.
		var archive:=ZIPReader.new();archive.open(folder.path_join("Reimu helpers.has"))
		var packed: Dictionary=JSON.parse_string(archive.read_file("project.json").get_string_from_utf8());archive.close()
		var packed_actor: Dictionary=packed.world.objects.filter(func(row):return row.id==expected.actor_id)[0]
		for key in packed_actor.animation_clips[0].keys:key.frame=int(key.frame)
		app.has_project.open_file(folder.path_join("Reimu helpers.has"));await project_ready()
		var restored=app.renderer.world_runtime.instance(expected.actor_id)
		FileAccess.open(folder.path_join("read-snapshot.json"),FileAccess.WRITE).store_string(JSON.stringify({"keys":restored.authored_keys(),"report":restored.data.metadata.generated_helpers,"sha256":restored.data.sha256,"format":restored.data.format},"",true,true))
		check(restored!=null and restored.order.size()==int(expected.bones),"fresh packed reader restores the real derived native rig")
		check(JSON.stringify(restored.authored_keys(),"",true,true)==JSON.stringify(packed_actor.animation_clips[0].keys,"",true,true),"fresh packed reader keeps exact packed keys")
		check(JSON.stringify(restored.data.metadata.generated_helpers,"",true,true)==JSON.stringify(packed_actor.metadata.generated_helpers,"",true,true),"fresh packed reader keeps exact helper provenance")
		check(restored.data.sha256==expected.derived_sha256,"fresh packed reader keeps the derived model checksum")
		check(restored.data.source.begins_with(folder.path_join("reader-cache")),"fresh reader resolves the embedded helper model into its own cache")
		check(restored.root.get_meta("has_secondary_rig").chains.size()==1 and not app.physics_editor.active(expected.actor_id),"reopened helpers replay from the authored take without a live solver")
		var image: Image=await app.renderer.capture(app.keys,app.layers,12,true);image.save_png(folder.path_join("cold.png"))
		check(Storage.image_hash(image)==expected.pixels,"fresh native helper replay retains exact composite pixels")
		finish(folder,{"mode":"reader"});return
	check(app.pose_editor.add_model(source).is_empty(),"actual supplied Bikini Reimu loads through normal Add model")
	await settle();var actor=app.renderer.active_model();app.pose_editor.frame_model();app.keys=[Timeline.from_camera(0,app.renderer.camera,"linear")];await settle()
	var physics=app.physics_editor;var definition: Dictionary=actor.root.get_meta("has_secondary_rig")
	check(definition.error.is_empty() and definition.chains.is_empty(),"native Reimu has no declared secondary chains and no malformed-rig error")
	check(not physics.hair_toggle.disabled,"Hair & clothes offers setup when native chains are missing")
	check(not physics.hair_toggle.tooltip_text.to_lower().contains("not implemented"),"missing-chain guidance describes the implemented helper setup")
	if "--probe" in args:
		finish(folder,{"tooltip":physics.hair_toggle.tooltip_text,"hair_disabled":physics.hair_toggle.disabled,"setup_button_disabled":physics.helper_editor.button.disabled,"bones":actor.order.size()});return
	app.video.duration_frames=24;var id: String=actor.data.id;var original_sha:=FileAccess.get_sha256(source);var original_ids: Array=actor.order.duplicate();var original_data: Dictionary=actor.data.duplicate(true);var history: int=app.history.size();var shots: Array=app.keys.duplicate(true)
	app.create_cel(false);var cel: Dictionary=Drawing.cel_at(app.layers[1],0);var drawing: Image=Drawing.edit_image(cel).image;drawing.fill_rect(Rect2i(40,40,60,30),Color.CYAN);Drawing.touch(drawing);app.changed();history=app.history.size()
	var helper=physics.helper_editor;physics.hair_toggle.button_pressed=true;await review_ready(helper)
	check(is_instance_valid(helper.window) and physics.hair_toggle.disabled and not physics.hair_toggle.button_pressed and not physics.active(id),"Hair & clothes opens real reviewed generation instead of claiming a running simulation")
	check(not helper.preview.is_empty() and helper.preview.can_apply and "hair" in str(helper.preview.region.material_name).to_lower() and "ribbon" in str(helper.preview.region.anchor_name).to_lower(),"native hair ribbon is the initial usable preview ahead of the face-surface suggestion")
	check(actor.data==original_data and app.history.size()==history and app.keys==shots,"review leaves native model, Undo history and shot keys untouched")
	helper.window.close_requested.emit();await settle()
	check(not is_instance_valid(helper.window) and actor.data==original_data and not physics.hair_toggle.disabled,"Cancel retains the original model and permits a new setup attempt")
	physics.hair_toggle.button_pressed=true;await review_ready(helper)
	if helper.preview.is_empty() or not helper.preview.can_apply:finish(folder);return
	helper.window.get_texture().get_image().save_png(folder.path_join("review.png"))
	var selected: Dictionary=helper.preview.region.duplicate(true);var neutral: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	helper.apply_button.pressed.emit();await review_ready(helper);actor=app.renderer.world_runtime.instance(id)
	check(not is_instance_valid(helper.window) and actor.order.size()==original_ids.size()+4 and actor.data.metadata.has("generated_helpers") and app.history.size()==history+1,"reviewed Apply appends actual weighted helper joints as one undoable asset revision")
	check(original_ids.all(func(b):return actor.bones.has(b)) and actor.data.metadata.native_parameters==original_data.metadata.native_parameters and actor.authored_keys()==original_data.pose_keys,"generated native revision retains every original bone, source provenance and authored keys")
	var derived_data: Dictionary=actor.data.duplicate(true);var derived_image: Image=await app.renderer.capture(app.keys,app.layers,0,true);var bind_difference:=image_difference(neutral,derived_image)
	check(bind_difference.changed_channels<=384 and bind_difference.mean<0.002,"generated native skin preserves neutral appearance within the established helper bind-rebuild bound")
	app.undo();await settle();actor=app.renderer.world_runtime.instance(id)
	check(actor.data==original_data and not physics.hair_toggle.disabled,"one Undo restores exact original native data and missing-chain setup")
	app.redo();await settle();actor=app.renderer.world_runtime.instance(id)
	check(actor.data==derived_data and actor.root.get_meta("has_secondary_rig").chains.size()==1,"one Redo restores the derived weighted chain")
	physics.fan_editor.add_fan();await settle();var fan=app.renderer.active_model();var fan_id: String=fan.data.id;actor=app.renderer.world_runtime.instance(id);definition=actor.root.get_meta("has_secondary_rig")
	var target: Vector3=actor.bone_transform(definition.chains[0].joints[1].binding.id).origin
	fan.data.position=[target.x,target.y-0.85,target.z-1];fan.data.rotation_xyzw=[0,0,0,1];app.pose_editor.apply_frame();app.changed();await settle();physics.fan_editor.speed.value=12;physics.fan_editor.enabled.button_pressed=false;await settle()
	var ready_world: Dictionary=app.current_world().duplicate(true)
	check(await start_hair(id),"generated Reimu chain starts through the ordinary Hair & clothes control")
	if not physics.active(id):finish(folder);return
	for i in range(120):await physics_frame
	var no_wind: Dictionary=physics.simulations[id].pose().duplicate(true);var quiet: Image=await app.renderer.capture(app.keys,app.layers,0,false)
	physics.clear();check(app.restore_world(ready_world).is_empty(),"controlled fan comparison restores the same native starting scene")
	app.world_selection.select_entity(fan_id,false);await settle();physics.fan_editor.enabled.button_pressed=true;await settle()
	check(await start_hair(id),"reviewed helpers run with the actual fan enabled")
	if not physics.active(id):finish(folder);return
	actor=app.renderer.world_runtime.instance(id);var before_live: Dictionary=actor.data.duplicate(true)
	for i in range(120):await physics_frame
	var windy: Dictionary=physics.simulations[id].pose();var wind_difference:=0.0
	for bone in windy:
		if not bone in original_ids:wind_difference=maxf(wind_difference,Timeline.quaternion(windy[bone].rotation_xyzw).angle_to(Timeline.quaternion(no_wind[bone].rotation_xyzw)))
	var force:=Airflow.force(Airflow.collect(app.renderer,0,physics.simulations),target).length();var moving: Image=await app.renderer.capture(app.keys,app.layers,0,false);moving.save_png(folder.path_join("wind.png"))
	check(force>0.01 and wind_difference>0.005 and quiet.get_data()!=moving.get_data(),"ordinary fan changes real native helper motion and rendered geometry versus fan-off control")
	check(actor.data==before_live and actor.authored_keys().is_empty(),"unrecorded native hair motion changes no authored keys or model data")
	var record=physics.recording;record.scope.select(0);record.button.pressed.emit()
	while record.active:await process_frame
	actor=app.renderer.world_runtime.instance(id)
	check(record.last_error.is_empty() and actor.authored_keys().size()==25,"normal Local Record captures the generated native helper take")
	physics.clear();app.set_frame(12);var image: Image=await app.renderer.capture(app.keys,app.layers,12,true);image.save_png(folder.path_join("recorded.png"))
	var expected:={"actor_id":id,"bones":actor.order.size(),"keys":actor.authored_keys(),"report":actor.data.metadata.generated_helpers,"derived_sha256":actor.data.sha256,"pixels":Storage.image_hash(image)}
	FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify(expected,"",true,true))
	app.has_project.save_file(folder.path_join("Reimu helpers.has"),"packed");await project_ready()
	check(not app.dirty and not app.has_project.path.is_empty(),"ordinary packed Save includes the native derived rig, fan, take and independent drawing")
	var error: String=await app.export_movie(folder)
	check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000013.png")).get_data()==image.get_data(),"native generated-helper movie uses exact recorded composite preview")
	check(FileAccess.get_sha256(source)==original_sha,"native source GLB remains byte-identical through setup, fan, recording and Save")
	finish(folder,{"mode":"writer","region":selected,"bind_difference":bind_difference,"wind_radians":wind_difference,"force":force,"movie":app.last_finished_movie})
