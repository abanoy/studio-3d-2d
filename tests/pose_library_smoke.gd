extends SceneTree
const Library=preload("res://src/pose_library.gd")
const Storage=preload("res://src/storage.gd")
const Drawing=preload("res://src/drawing.gd")
const Model=preload("res://src/model.gd")
var app
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(100).timeout.connect(func():push_error("Pose library watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settle() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func click(control: Control) -> void:
	var window: Window=control.get_window();var position:=control.get_global_rect().get_center()
	if window.is_embedded():position+=Vector2(window.position)
	var target: Window=root if window.is_embedded() else window;var motion:=InputEventMouseMotion.new();motion.position=position;target.push_input(motion,true)
	for down in [true,false]:
		var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.pressed=down;event.position=position;target.push_input(event,true);await process_frame
	await settle()
func jobs() -> void:
	while app.has_project.pid>0:await process_frame
	await settle()
func picker() -> FileDialog:
	for child in app.get_children():
		if child is FileDialog and child.visible:return child
	return null
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0];var reading: bool="--read" in OS.get_cmdline_user_args()
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery-cold" if reading else "recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache-cold" if reading else "cache")
	var editor=app.pose_editor;var library=editor.pose_library;var packed:=folder.path_join("Body poses.has")
	if reading:
		app.has_project.open_file(packed);await jobs();var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
		for object in app.current_world().objects:
			if object.metadata.has(Library.FIELD):app.world_selection.select_entity(object.id)
		var rig=editor.active_rig()
		check(rig!=null and Library.equivalent(rig.data.metadata.body_pose_library,expected.library),"fresh HAS restores exact named body poses and thumbnail bytes")
		app.mode.select(2);app.change_mode(2);app.set_frame(24);library.open();await settle();library.selected=expected.library.entries[0].id;var before: Dictionary=rig.data.duplicate(true);library.apply_pose()
		check(rig.authored_keys().any(func(k):return k.frame==24) and Library.equivalent(rig.sample_body(24),expected.pose),"fresh reopened library applies ordinary bone keys at another frame")
		app.undo();check(Library.equivalent(rig.data,before),"cold application Undo exactly restores previous data")
		app.has_project.open_file(folder.path_join("Body poses linked.has"));await jobs()
		for object in app.current_world().objects:
			if object.metadata.has(Library.FIELD):app.world_selection.select_entity(object.id)
		check(Library.equivalent(editor.active_rig().data.metadata.body_pose_library,expected.library),"fresh linked HAS retains body-pose values and thumbnail bytes")
		check(app.restore_checkpoint({"folder":folder.path_join("library-recovery/poses"),"manifest":"project.json","recovery":true}),"fresh recovery rebuilds actual standard scene with pose library")
		for object in app.current_world().objects:
			if object.metadata.has(Library.FIELD):app.world_selection.select_entity(object.id)
		check(Library.equivalent(editor.active_rig().data.metadata.body_pose_library,expected.library),"recovery keeps exact library across rebuilt rig bindings")
		print("POSE_LIBRARY_READ ",JSON.stringify({"checks":checks,"failures":failures}));app.free();quit(0 if failures==0 else 1);return
	check(app.load_demo_room(),"original 3D environment loads")
	var path:=folder.path_join("authored-rig.glb");check(preload("res://src/scene3d.gd").make_pose_fixture(path)==OK and editor.add_model(path).is_empty(),"original procedural rig imports through common model format")
	app.physics_editor.freeze_all();app.physics_editor.clear_previews();app.mode.select(2);app.change_mode(2);var rig=editor.active_rig();var bone: String=rig.order[-1];editor.selected=bone;editor.operation.select(0);editor.fields[2].value=45;editor.apply_numeric();editor.frame_model();await settle()
	var promoted: Dictionary=preload("res://src/root_component_document.gd").promote(rig.data,48);check(not promoted.has("error") and editor.restore_state(promoted.data).is_empty(),"independent root-component model remains the authoritative pose format")
	var pose: Dictionary=rig.sample_body(0,true);var keys: Array=app.keys.duplicate(true);var position: Dictionary=rig.sample_authored_transform(0,true);var source:=FileAccess.get_sha256(path)
	var image:=Drawing.blank(1920,1080);image.fill_rect(Rect2i(300,300,60,60),Color.CYAN);Drawing.insert(app.layers[1],0,48,image);app.changed();var pixels:=Storage.image_hash(image);app.history.clear();app.redo_history.clear();app.history_bytes=0
	app.set_advanced(false);root.size=Vector2i(1280,800);await settle();app.inspector_scroll.ensure_control_visible(library.launch);await settle();await click(library.launch)
	check(library.dialog.visible and not library.dialog.exclusive,"actual Simple button opens nonexclusive body-pose library")
	# Temporary authored metadata fixture checks byte accounting, then is removed.
	var base_bytes: int=editor.contacts.metadata_bytes(app.current_world());var origin:={"format":"studio_drawing_origin_1","kind":"krita","name":"Test provenance.kra","sha256":"a".repeat(64),"width":1920,"height":1080,"fps":24,"range":[],"visibility":{},"fit":[1920,1080,0,0],"rate":[24,1],"at":0,"duration":48};app.layers[1].origin=origin
	check(editor.contacts.metadata_bytes(app.current_world())-base_bytes==JSON.stringify(origin,"",true,true).to_utf8_buffer().size()+10,"metadata budget counts optional Krita drawing ancestry exactly")
	app.layers[1].erase("origin")
	library.name_edit.text="Wave";var authored: Dictionary=rig.data.duplicate(true);var view: Dictionary=app.renderer.view_state();await click(library.save_button)
	check(rig.data.metadata.has(Library.FIELD) and Library.get_library(rig).entries.size()==1 and app.history.size()==1,"actual Save stores one named thumbnail pose with one Undo")
	if not rig.data.metadata.has(Library.FIELD):print(app.status.text);app.free();quit(1);return
	var saved: Dictionary=Library.get_library(rig);var without_library: Dictionary=rig.data.duplicate(true);without_library.metadata.erase(Library.FIELD);check(Library.equivalent(without_library,authored),"saving library does not author body/root/camera animation")
	check(app.renderer.view_state()==view,"isolated thumbnail capture keeps the live camera exactly unchanged")
	check(Library.thumbnail(saved.entries[0].thumbnail_png).image.get_size()==Vector2i(96,54),"saved scene-view thumbnail decodes at bounded size")
	app.undo();check(not rig.data.metadata.has(Library.FIELD),"Undo removes saved library metadata");app.redo();check(Library.equivalent(Library.get_library(rig),saved),"Redo restores exact pose and thumbnail")
	var count: int=app.history.size();library.selected=saved.entries[0].id;library.apply_pose();check(app.history.size()==count,"using an identical current pose is a true no-op")
	app.set_frame(24);editor.selected=bone;editor.reset_selected();app.set_frame(12);library.selected=saved.entries[0].id;library.refresh();await click(library.use_button)
	check(rig.authored_keys().any(func(k):return k.frame==12) and Library.equivalent(rig.sample_body(12),pose),"actual Use creates ordinary current-frame auto-keys")
	check(app.keys==keys and rig.sample_authored_transform(12)==position and Storage.image_hash(image)==pixels,"reuse keeps camera, model placement and independent paint intact")
	var applied: Dictionary=rig.data.duplicate(true);app.undo();check(not rig.authored_keys().any(func(k):return k.frame==12),"one Undo removes the applied body-pose keys");app.redo();check(Library.equivalent(rig.data,applied),"Redo restores pose-key data exactly")
	library.name_edit.text="Raised arm";await click(library.rename_button);check(Library.get_library(rig).entries[0].name=="Raised arm","actual Rename updates saved pose only")
	await click(library.duplicate_button);check(Library.get_library(rig).entries.size()==2 and Library.get_library(rig).entries[1].name=="Raised arm 2","Duplicate creates independent named entry")
	app.undo();library.refresh();library.selected=saved.entries[0].id;library.refresh();editor.auto_key.button_pressed=false;app.set_frame(18);var before_keys: Array=rig.authored_keys().duplicate(true);await click(library.use_button)
	check(rig.authored_keys()==before_keys and rig.data.draft_frame==18 and Library.equivalent(rig.data.pose,pose),"Auto-key off applies a draft without adding keys")
	app.undo();editor.auto_key.button_pressed=true;app.set_frame(12);app.set_advanced(true);library.refresh();library.export_file();await settle();var file_dialog:=picker();check(file_dialog!=null,"Advanced export opens real save chooser")
	if file_dialog:file_dialog.file_selected.emit(folder.path_join("Body poses.hasposes.json"))
	await settle();var exported: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("Body poses.hasposes.json")));check(Library.equivalent(exported,Library.get_library(rig)),"native HAS-pose exchange preserves body/thumbnail identity")
	var previous_count: int=Library.get_library(rig).entries.size();library.import_file();await settle();file_dialog=picker()
	if file_dialog:file_dialog.file_selected.emit(folder.path_join("Body poses.hasposes.json"))
	await settle();check(Library.get_library(rig).entries.size()==previous_count,"reimporting identical library does not duplicate poses")
	var wrong:=exported.duplicate(true);wrong.sha256="b".repeat(64);FileAccess.open(folder.path_join("wrong-rig.json"),FileAccess.WRITE).store_string(JSON.stringify(wrong,"",true,true));var before_wrong: Dictionary=rig.data.duplicate(true);library.import_file();await settle();file_dialog=picker()
	if file_dialog:file_dialog.file_selected.emit(folder.path_join("wrong-rig.json"))
	await settle();check(Library.equivalent(rig.data,before_wrong),"actual wrong-rig library import preserves current scene data")
	var keys_before_remove: Array=rig.authored_keys().duplicate(true);await click(library.remove_button);var confirmation: ConfirmationDialog
	for child in app.get_children():
		if child is ConfirmationDialog and child.visible and child.title=="Remove saved body pose?":confirmation=child
	if confirmation:await click(confirmation.get_ok_button())
	check(Library.get_library(rig).entries.is_empty() and Library.equivalent(rig.authored_keys(),keys_before_remove),"actual Remove deletes library entry without erasing animation keys")
	app.undo();library.refresh();check(Library.get_library(rig).entries.size()==1,"Undo restores removed pose and thumbnail")
	var current_data: Dictionary=rig.data.duplicate(true);var current_history: int=app.history.size();app.playing=true;library.apply_pose();app.stop();check(Library.equivalent(rig.data,current_data) and app.history.size()==current_history,"playback refuses library edits without stopping or changing animation")
	library.name_edit.text="Stale capture";library.capture();app.set_frame(13);await settle();check(Library.get_library(rig).entries.size()==1 and app.history.size()==current_history,"frame change discards pending thumbnail capture")
	app.set_frame(12)
	var bad:=exported.duplicate(true);bad.sha256="b".repeat(64);check(not Library.compatible(bad,rig).is_empty(),"different rig source refuses automatic retargeting")
	var invalid: Dictionary=rig.data.duplicate(true);invalid.metadata.body_pose_library.bone_ids[0]="missing";check(not Model.validate(invalid,48).is_empty() or not Library.compatible(invalid.metadata.body_pose_library,rig).is_empty(),"unknown rig binding refuses")
	library.dialog.hide();app.has_project.save_file(packed,"packed");await jobs();check(app.has_project.path==packed,"ordinary packed HAS saves library alongside normal scene")
	app.has_project.save_file(folder.path_join("Body poses linked.has"),"linked");await jobs();check(FileAccess.file_exists(folder.path_join("Body poses linked.has")),"ordinary linked HAS saves same library")
	var recovery_error:=preload("res://src/recovery.gd").checkpoint(folder.path_join("library-recovery"),"poses",app.video,app.keys,app.layers,app.source,app.frame,app.audio_document(),"",app.recovery_revision,app.renderer.model_state(),app.renderer.world_state(),app.palette);check(recovery_error.is_empty(),"recovery checkpoint writes validated body-pose metadata and assets")
	var preview: Image=await app.renderer.capture(app.keys,app.layers,12,true);var export_error: String=await app.export_movie(folder);check(export_error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000013.png")).get_data()==preview.get_data(),"actual MP4 uses identical camera/body/independent drawing pixels with library metadata")
	FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify({"library":Library.get_library(rig),"pose":pose},"",true,true))
	check(FileAccess.get_sha256(path)==source and app.keys==keys and Storage.image_hash(image)==pixels,"all library actions preserve source, camera and drawing pixels")
	library.open();await settle();root.get_texture().get_image().save_png(folder.path_join("body-poses.png"));app.new_project();await settle();check(not library.dialog.visible,"New scene closes old model library context")
	print("POSE_LIBRARY_SMOKE ",JSON.stringify({"checks":checks,"failures":failures,"project":packed,"movie":app.last_export_folder.path_join("movie.mp4")}));app.free();quit(0 if failures==0 else 1)
