extends "res://tests/movement_path_smoke.gd"
const Preset=preload("res://src/movement_path_preset.gd")
const Drawing=preload("res://src/drawing.gd")
const Recovery=preload("res://src/recovery.gd")
func chooser() -> FileDialog:
	for child in app.get_children():
		if child is FileDialog and child.visible:return child
	return null
func choose(path: String) -> void:
	var dialog:=chooser();check(dialog!=null,"ordinary preset picker opens")
	if dialog:dialog.file_selected.emit(path)
	await settled()
func samples(rig: RefCounted) -> Array:
	var result:=[]
	for half in range(97):result.append({"root":rig.sample_authored_transform(float(half)/2),"body":rig.sample_body(float(half)/2),"shapes":rig.sample_shapes(float(half)/2)})
	return result
func run() -> void:
	folder=OS.get_cmdline_user_args()[0];app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	if "--read" in OS.get_cmdline_user_args():
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
		for mode in ["packed","linked"]:
			var path:=folder.path_join("Route "+mode+".has");app.has_project.open_file(path);await wait_job();app.world_selection.select_entity(expected.id)
			var rig: RefCounted=app.renderer.active_model();check(app.has_project.path==path and rig!=null and rig.data.format=="studio_model_9","cold "+mode+" ordinary Open retains independent editable movement")
			var image: Image=await app.renderer.capture(app.keys,app.layers,24,true)
			check(image.get_data()==Image.load_from_file(folder.path_join("reference.png")).get_data(),"cold "+mode+" path pose camera and ink repeat exact picture")
		check(app.restore_checkpoint({"folder":folder.path_join("path-recovery/test"),"manifest":"project.json","recovery":true}),"ordinary recovery restores assigned movement with source assets")
		var recovered: Image=await app.renderer.capture(app.keys,app.layers,24,true);check(recovered.get_data()==Image.load_from_file(folder.path_join("reference.png")).get_data(),"recovery restores exact composite")
		print("MOVEMENT_PATH_PRESET_READ ",JSON.stringify({"checks":checks,"failures":failures}));await app.quit_studio();quit(0 if failures==0 else 1);return
	var arm:=folder.path_join("arm.glb");var leg:=folder.path_join("leg.glb")
	check(preload("res://tests/limb_fixture.gd").create(arm)==OK and preload("res://tests/limb_fixture.gd").create(leg,true,true)==OK,"two different original procedural rigs export")
	var placement: Dictionary=app.import_actions.placement();placement.physics_on_import=false
	check(app.pose_editor.add_model(arm,0,placement).is_empty(),"source rig imports through ordinary controls")
	var rig: RefCounted=app.renderer.active_model();var source: Dictionary=rig.data.duplicate(true)
	for at in [0,24,48]:
		var transform:=Model.identity();transform.scale=1.;transform.position=[float(at)/120,float(at%48)/120,0]
		source.pose_keys.append({"frame":at,"pose":{},"transform":transform,"interpolation":"ease"})
	var source_error: String=app.pose_editor.restore_state(source)
	check(source_error.is_empty(),"source accepts authored waypoint path")
	if not source_error.is_empty():print("SOURCE ERROR ",source_error," ",JSON.stringify(source));await app.quit_studio();quit(1);return
	app.mode.select(2);app.change_mode(2);app.set_frame(24);var editor=app.pose_editor.movement_path;editor.open();await settled()
	editor.preset_name.text="Cross-rig route";var history: int=app.history.size();var file:=folder.path_join("Route.haspaths.json")
	await click(editor.save_preset_button);await choose(file)
	check(FileAccess.file_exists(file) and Preset.read_file(file).preset.name=="Cross-rig route" and app.history.size()==history and rig.data==source,"save exchanges only data and leaves scene/history untouched")
	await click(editor.save_preset_button);var stale:=chooser();editor.frame.value=12;editor.add_point()
	if stale:stale.file_selected.emit(folder.path_join("stale.json"))
	await settled();check(not FileAccess.file_exists(folder.path_join("stale.json")),"changed staged path invalidates an older save dialog")
	editor.close();check(app.pose_editor.add_model(leg,0,placement).is_empty(),"different skeleton target imports normally")
	rig=app.renderer.active_model();var static_before: Dictionary=rig.data.duplicate(true);history=app.history.size()
	editor.open();await settled();await click(editor.load_preset_button);await choose(file);var static_staged: Dictionary=editor.draft.duplicate(true)
	check(static_staged!=static_before and rig.data==static_before,"ordinary static model reviews a continuous route before Apply")
	await click(editor.apply_button);check(rig.data==static_staged and app.history.size()==history+1 and not is_instance_valid(editor.window),"static model Apply commits continuous movement in one action")
	app.undo();await settled();check(rig.data==static_before,"static route Undo restores original model and version")
	var target: Dictionary=rig.data.duplicate(true)
	for at in [0,48]:
		var transform:=Model.identity();transform.position=[-.5+float(at)/240,0,0];transform.scale=1.+float(at)/480
		var q:=Quaternion(Vector3.UP,float(at)/240);transform.rotation_xyzw=[q.x,q.y,q.z,q.w]
		var bone:=Model.identity();var rotation:=Quaternion(Vector3.RIGHT,float(at)/480);bone.rotation_xyzw=[rotation.x,rotation.y,rotation.z,rotation.w]
		target.pose_keys.append({"frame":at,"pose":{rig.order[1]:bone},"transform":transform,"interpolation":"ease"})
	check(app.pose_editor.restore_state(target).is_empty(),"target contains independently animated pose turn and size")
	var peers:=samples(rig);var arm_hash:=FileAccess.get_sha256(arm);var leg_hash:=FileAccess.get_sha256(leg)
	editor.open();await settled();history=app.history.size();await click(editor.load_preset_button);await choose(file)
	var staged: Dictionary=editor.draft.duplicate(true)
	check(staged!=target and rig.data==target and app.history.size()==history and editor.note.text.contains("whole position path"),"Load reviews replacement path without changing model or history")
	var current:=Model.new();current.data=staged;current.motion_video=app.video
	check(Model.Timeline.vector(current.sample_authored_transform(24).position).distance_to(Vector3(-.3,.2,0))<.00001,"route starts at target position and reuses source-relative displacement")
	var exact:=true
	for half in range(97):
		var at:=float(half)/2;var root_value:=current.sample_authored_transform(at)
		exact=exact and root_value.rotation_xyzw==peers[half].root.rotation_xyzw and root_value.scale==peers[half].root.scale and current.sample_body(at)==peers[half].body and current.sample_shapes(at)==peers[half].shapes
	check(exact,"different skeleton retains all97 sampled pose turn size expression peers")
	editor.window.get_texture().get_image().save_png(folder.path_join("path-preset-panel.png"));await click(editor.apply_button)
	check(rig.data==staged and app.history.size()==history+1 and not is_instance_valid(editor.window),"Apply validates native bindings and commits as one Undo")
	app.undo();await settled();check(rig.data==target,"one Undo restores complete prior movement and pose")
	app.redo();await settled();check(rig.data==staged,"Redo restores assigned independent position path")
	editor.open();await settled();await click(editor.load_preset_button);stale=chooser();editor.close();editor.open();await settled()
	var fresh: Dictionary=editor.draft.duplicate(true)
	if stale:stale.file_selected.emit(file)
	await settled();check(editor.draft==fresh,"closing and reopening invalidates an old load picker")
	await click(editor.load_preset_button);await choose(arm);check(editor.draft==fresh and rig.data==staged,"non-preset source file refuses without editing draft or scene")
	editor.close();app.pose_editor.frame_model();app.keys=[Model.Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,60)]
	app.mode.select(0);app.change_mode(0);app.set_frame(0);app.create_cel(false);Drawing.stroke(Drawing.cel_at(app.layers[1],0).image,Vector2(80,80),Vector2(180,80),5,Color.CYAN,false);app.changed();app.set_frame(24)
	var picture: Image=await app.renderer.capture(app.keys,app.layers,24,true);picture.save_png(folder.path_join("reference.png"))
	for mode in ["packed","linked"]:
		var path:=folder.path_join("Route "+mode+".has");app.has_project.save_file(path,mode);await wait_job();check(app.has_project.path==path,"ordinary "+mode+" HAS saves editable position tracks")
	var snapshot: Dictionary=app.project_snapshot();var why:=Recovery.checkpoint(folder.path_join("path-recovery"),"test",snapshot.video,snapshot.camera_keys,snapshot.layers,"",24,snapshot.audio,"",app.recovery_revision,{},snapshot.world,snapshot.palette,snapshot.sequence_graph)
	check(why.is_empty(),"ordinary recovery checkpoint includes editable path and original rigs")
	FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify({"id":rig.data.id}))
	var error: String=await app.export_movie(folder);check(error.is_empty() and picture.get_data()==Image.load_from_file(app.last_export_folder.path_join("frame_000025.png")).get_data(),"MP4 export frame matches committed route pose camera and independent ink")
	check(FileAccess.get_sha256(arm)==arm_hash and FileAccess.get_sha256(leg)==leg_hash,"original source rig files remain byte-identical")
	var movie: String=app.last_export_folder.path_join("movie.mp4")
	var figure:=folder.path_join("figure.glb");check(preload("res://src/tutorial_assets.gd").figure(figure)==OK,"original full figure fixture exports for contact checks")
	app.set_frame(0);app.mode.select(2);app.change_mode(2);check(app.pose_editor.add_model(figure,0,placement).is_empty(),"contact figure imports without live physics")
	rig=app.renderer.active_model();var continuous: Dictionary=rig.data.duplicate(true)
	for at in [0,48]:
		continuous.pose_keys.append({"frame":at,"pose":{},"transform":{"position":continuous.position.duplicate(),"rotation_xyzw":continuous.rotation_xyzw.duplicate(),"scale":continuous.scale},"interpolation":"ease"})
	check(app.pose_editor.restore_state(continuous).is_empty(),"contact fixture establishes one continuous authored movement interval")
	var contacts=app.pose_editor.contacts;contacts.control.pressed.emit();await settled();contacts.end_frame.value=48;contacts.plant_button.pressed.emit();await settled()
	var planted: Dictionary=rig.data.duplicate(true);FileAccess.open(folder.path_join("planted.json"),FileAccess.WRITE).store_string(JSON.stringify(planted,"",true,true));check(Model.is_contact(planted),"actual Plant feet establishes authored constraints")
	var unsafe: Dictionary=Preset.read_file(file).preset;unsafe.keys[1].offset=[100,0,0];unsafe.keys[2].offset=[0,0,0]
	app.set_frame(12)
	var distant:=folder.path_join("Distant.haspaths.json");check(Preset.write_file(distant,unsafe).is_empty(),"extreme but structurally valid route writes independently")
	editor.open();await settled();await click(editor.load_preset_button);await choose(distant);history=app.history.size()
	if editor.draft==planted:print("CONTACT PRESET REFUSED ",editor.note.text)
	check(editor.draft!=planted,"unreachable route can be reviewed as a staged path")
	await click(editor.apply_button);check(is_instance_valid(editor.window) and rig.data==planted and app.history.size()==history and not editor.note.text.is_empty(),"actual Apply refuses unreachable planted feet without changing data/history")
	editor.close();unsafe.keys[1].offset=[0,-.03,0];var nearby:=folder.path_join("Nearby.haspaths.json");check(Preset.write_file(nearby,unsafe).is_empty(),"reachable crouch route saves as ordinary data")
	editor.open();await settled();await click(editor.load_preset_button);await choose(nearby);var crouch: Dictionary=editor.draft.duplicate(true)
	await click(editor.apply_button);check(not is_instance_valid(editor.window) and rig.data==crouch and app.history.size()==history+1 and rig.evaluation_error.is_empty(),"actual Apply accepts reachable path while retaining foot constraints")
	app.undo();await settled();check(rig.data==planted,"contact path Undo restores exact pre-preset model")
	var parameters:=folder.path_join("parameters.json");FileAccess.open(parameters,FileAccess.WRITE).store_string("original owner parameters")
	editor.open();await settled();await click(editor.save_preset_button);await choose(parameters)
	check(FileAccess.get_file_as_string(parameters)=="original owner parameters" and editor.note.text.contains("original source"),"actual preset Save protects adjacent original parameters report")
	editor.close()
	print("MOVEMENT_PATH_PRESET_SMOKE ",JSON.stringify({"checks":checks,"failures":failures,"movie":movie}));await app.quit_studio();quit(0 if failures==0 else 1)
