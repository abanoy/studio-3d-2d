extends SceneTree
const Support = preload("res://tests/world_test_support.gd")
const Storage = preload("res://src/storage.gd")
const SceneIO = preload("res://src/scene3d.gd")
const Drawing = preload("res://src/drawing.gd")
const Timeline = preload("res://src/timeline.gd")
const Recovery = preload("res://src/recovery.gd")
var checks := 0
var failures := 0

func _initialize() -> void:
	create_timer(150).timeout.connect(func(): push_error("HAS watchdog expired"); quit(2))
	call_deferred("run")

func check(ok: bool, text: String) -> void:
	checks += 1; print(("PASS " if ok else "FAIL ") + text)
	if not ok: failures += 1

func wait_job(has) -> void:
	while has.pid > 0: await process_frame
	await process_frame

func find_button(node: Node, title: String) -> Button:
	if node is Button and node.text == title: return node
	for child in node.get_children():
		var found := find_button(child, title)
		if found: return found
	return null

func directory_picker(app) -> FileDialog:
	for child in app.get_children():
		if child is FileDialog and child.visible and child.file_mode == FileDialog.FILE_MODE_OPEN_DIR: return child
	return null

func run() -> void:
	var folder := ProjectSettings.globalize_path("res://output/has-smoke/run_%d" % Time.get_ticks_usec())
	var app = load("res://main.tscn").instantiate()
	app.recovery_root = folder.path_join("recovery")
	root.add_child(app); await process_frame
	var input := folder.path_join("inputs"); DirAccess.make_dir_recursive_absolute(input)
	var source := input.path_join("room.glb"); SceneIO.make_fixture(source); app.load_scene(source)
	var rig := input.path_join("rig.glb"); SceneIO.make_pose_fixture(rig); app.pose_editor.add_model(rig)
	var audio := input.path_join("voice.wav")
	DirAccess.copy_absolute(ProjectSettings.globalize_path("res://output/fixtures/voice — тест.wav"), audio)
	check(app.import_audio(audio).is_empty(), "fixture has independent scene, rig and audio assets")
	app.audio_clip.start_frame = 24; app.audio_clip.gain_db = -6; app.rebuild_audio()
	app.pose_editor.frame_model()
	var camera: Camera3D = app.renderer.camera
	app.keys = [Timeline.key(0,camera.position,camera.quaternion,camera.fov),Timeline.key(48,camera.position+Vector3(0.1,0,0),camera.quaternion,camera.fov)]
	app.pose_editor.record_key(); app.set_frame(48); app.pose_editor.record_key()
	app.set_frame(24); app.create_cel(false)
	Drawing.stroke(Drawing.cel_at(app.layers[1],24).image,Vector2(100,100),Vector2(260,100),6,Color.RED,false)
	var expected: Image = await app.renderer.capture(app.keys,app.layers,24,true)
	var has = app.has_project
	has.cache_root = folder.path_join("cache")
	app.export_dialog()
	var unsaved_picker := directory_picker(app)
	check(unsaved_picker != null and not app.exporting, "unsaved project Export asks for a destination without starting a render")
	if unsaved_picker: unsaved_picker.canceled.emit()
	await process_frame
	check(app.last_export_folder.is_empty(), "cancelling destination leaves project and output untouched")
	var packed := folder.path_join("film.has")
	has.save_file(packed,"packed"); await wait_job(has)
	check(FileAccess.file_exists(packed) and not app.dirty and has.path == packed, "packed HAS commits atomically and becomes current Save target")
	var moved := folder.path_join("moved-inputs")
	DirAccess.rename_absolute(input,moved)
	has.open_file(packed); await wait_job(has)
	check(has.path == packed and not app.dirty and Support.rig(app) != null and not app.audio_clip.is_empty(), "packed HAS reopens after original 3D/audio paths disappear")
	var reopened: Image = await app.renderer.capture(app.keys,app.layers,24,true)
	expected.save_png(folder.path_join("before.png")); reopened.save_png(folder.path_join("reopened.png"))
	var a := expected.get_data(); var b := reopened.get_data(); var different := 0; var total := 0
	for i in range(a.size()):
		var delta := absi(a[i]-b[i]); total += delta
		if delta > 0: different += 1
	print("HAS_REIMPORT changed=",different," mean=",float(total)/a.size())
	check(different<=384 and float(total)/a.size()<0.002, "packed project retains scene/camera/model/cel frame within existing bounded GLB reimport tolerance")
	check(app.audio_clip.source.sha256==FileAccess.get_sha256(moved.path_join("voice.wav")) and app.audio_clip.start_frame==24 and app.audio_clip.gain_db==-6, "packed audio retains source bytes, frame24 offset and gain")
	var original_hash := FileAccess.get_sha256(packed)
	var export_button := find_button(app,"Export movie")
	check(export_button != null and export_button.is_visible_in_tree() and not app.advanced_mode, "default movie export remains accessible in Simple")
	export_button.pressed.emit()
	check(app.exporting and directory_picker(app) == null and app.last_export_folder.get_base_dir() == folder, "saved HAS navbar Export starts beside project without destination dialog")
	while app.exporting: await process_frame
	var movie: String = app.last_export_folder.path_join("movie.mp4")
	var frame := Image.load_from_file(app.last_export_folder.path_join("frame_000025.png"))
	check(FileAccess.file_exists(movie) and frame.get_data()==reopened.get_data(), "reopened HAS exports synchronized MP4 with exact frame24 preview pixels")
	check(FileAccess.get_sha256(packed)==original_hash, "default export never changes manually saved HAS bytes")
	var first_render: String = app.last_export_folder
	var first_movie_hash := FileAccess.get_sha256(movie)
	var override_button := find_button(app,"Export to another folder…")
	check(override_button != null and not override_button.is_visible_in_tree(), "destination override stays behind Advanced")
	app.set_advanced(true); override_button.pressed.emit()
	var override_picker := directory_picker(app)
	check(override_picker != null and override_picker.current_dir.replace("\\","/") == folder.replace("\\","/"), "Advanced destination picker starts beside HAS")
	var other := folder.path_join("other exports"); DirAccess.make_dir_absolute(other)
	if override_picker: override_picker.dir_selected.emit(other)
	var picker_closed := override_picker != null and not override_picker.visible
	app.cancel_export = true
	while app.exporting: await process_frame
	check(app.last_export_folder.get_base_dir()==other and picker_closed and has.path==packed, "one-off override exports elsewhere and closes picker before rendering")
	app.set_advanced(false)
	app.export_dialog(); app.cancel_export = true
	while app.exporting: await process_frame
	check(app.last_export_folder.get_base_dir()==folder and app.last_export_folder!=first_render and FileAccess.get_sha256(movie)==first_movie_hash, "next default export returns beside HAS in fresh folder and preserves previous movie")
	var prior_folder: String = app.last_export_folder
	var unavailable: String = await app.export_movie(folder.path_join("missing parent"))
	check(not unavailable.is_empty() and not app.exporting and app.last_export_folder==prior_folder and not DirAccess.dir_exists_absolute(folder.path_join("missing parent")), "missing output parent gives actionable error without recreating directories or altering project")
	DirAccess.rename_absolute(moved,input)
	app.source = source; Support.rig(app).data.source = rig; app.audio_clip.source.path = audio
	for instance in app.renderer.world_runtime.instances.values():
		if instance.data.kind=="environment":instance.data.source=source
	var linked := folder.path_join("linked.has")
	has.save_file(linked,"linked"); await wait_job(has)
	check(has.path==linked and has.storage_mode=="linked", "linked HAS uses the same project with external standardized assets")
	DirAccess.rename_absolute(input,moved)
	var before: String = app.source
	has.open_file(linked); await wait_job(has)
	var missing := Recovery.read_json(has.result_path)
	check(not missing.get("ok",true) and missing.has("missing") and app.source==before, "missing linked assets preserve current live project and offer relinking")
	var relinks := 0
	while missing.has("missing") and relinks < 4:
		var confirm: ConfirmationDialog
		for child in app.get_children():
			if child is ConfirmationDialog and child.visible: confirm = child
		if confirm == null: check(false,"matching-asset prompt available"); break
		confirm.confirmed.emit(); await process_frame
		var picker: FileDialog
		for child in app.get_children():
			if child is FileDialog and child.visible: picker = child
		if picker == null: check(false,"relink file picker available"); break
		var replacement: String = str(missing.missing[0].reference).replace("\\","/").replace("/inputs/","/moved-inputs/")
		picker.file_selected.emit(replacement); await wait_job(has)
		missing = Recovery.read_json(has.result_path); relinks += 1
	check(missing.get("ok",false) and relinks==3 and has.path==linked, "three matching 3D/audio assets relink through actual prompts and file pickers")
	has.save_current(); await wait_job(has)
	check(FileAccess.file_exists(linked+".backup") and not app.dirty, "linked Save remembers relocated originals and preserves prior HAS backup")
	var old_hash := FileAccess.get_sha256(linked)
	has.save_current(); has.cancel(); await wait_job(has)
	check(FileAccess.get_sha256(linked)==old_hash, "cancelled HAS save leaves last complete file intact")
	var bad := folder.path_join("broken.has"); var bad_file := FileAccess.open(bad,FileAccess.WRITE); bad_file.store_string("not a project");bad_file.close()
	before = app.source; has.open_file(bad); await wait_job(has)
	check(app.source==before and has.path==linked, "corrupt HAS open leaves existing project and save identity intact")
	app.changed(); app.autosave_tick(true)
	var recovered := Recovery.read_json(app.recovery_root.path_join(app.recovery_session).path_join("project.json"))
	check(recovered.editor.recovery.origin==linked, "recovery records HAS filename rather than temporary cache folder")
	var restored: bool = app.restore_checkpoint({"folder":app.recovery_root.path_join(app.recovery_session),"manifest":"project.json"})
	check(restored and has.path.is_empty() and app.dirty, "recovery becomes an unsaved copy instead of overwriting HAS")
	app.save()
	var save_picker: FileDialog
	for child in app.get_children():
		if child is FileDialog and child.visible: save_picker = child
	check(save_picker != null and save_picker.file_mode==FileDialog.FILE_MODE_SAVE_FILE and save_picker.filters[0].contains("*.has"), "new/recovered Save uses actual HAS file picker")
	await process_frame; await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(folder.path_join("has-save-dialog.png"))
	if save_picker: save_picker.canceled.emit()
	await process_frame
	has.open_file(packed); await wait_job(has); has.save_current(); await wait_job(has)
	has.open_file(packed+".backup"); await wait_job(has)
	check(has.path.is_empty() and app.dirty and app.project_folder.is_empty(), "HAS backup opens as an unsaved editable copy")
	var native := []
	for sample in ["source-smoke/source-project","sfm-smoke/project","pose-smoke/miku-project"]:
		var project := ProjectSettings.globalize_path("res://output/"+sample)
		if not FileAccess.file_exists(project.path_join("project.json")): continue
		check(app.open_project(project), "existing native-prepared project loads: "+sample)
		var hash: String = Support.rig(app).data.sha256
		var pose_keys := JSON.stringify(Support.rig(app).authored_keys())
		var metadata := JSON.stringify(Support.rig(app).data.metadata)
		var file := folder.path_join(str(native.size())+"-native.has")
		has.save_file(file,"packed");await wait_job(has)
		has.open_file(file);await wait_job(has)
		check(has.path==file and Support.rig(app).data.sha256==hash and JSON.stringify(Support.rig(app).authored_keys())==pose_keys and JSON.stringify(Support.rig(app).data.metadata)==metadata,"native GMod/SFM/MMD data survives same HAS contract: "+sample)
		native.append(sample)
	var output := {"checks":checks,"failures":failures,"folder":folder,"movie":movie,"native_projects":native}
	var file := FileAccess.open(ProjectSettings.globalize_path("res://output/has-result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(output));file.close()
	print("HAS_SMOKE "+JSON.stringify(output));quit(0 if failures==0 else 1)
