extends Node
const Recovery=preload("res://src/recovery.gd")
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
var checks:=0
var failures:=0
var received:=false
func _ready() -> void:
	var isolated: String=str(OS.get_cmdline_user_args()[0]).path_join("recovery")
	if get_parent().recovery_root!=isolated:
		get_parent().recovery_root=isolated
		push_error("Reader scene recovery-root override failed");get_tree().quit(2);return
	get_parent().startup_recovery_finished.connect(on_recovered)
	get_tree().create_timer(100).timeout.connect(func():push_error("Startup recovery reader watchdog");get_tree().quit(2))
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func canonical(value):return JSON.parse_string(JSON.stringify(value,"",false,true))
func portable(data: Dictionary) -> Dictionary:
	var result: Dictionary=canonical(data)
	for row in result.objects:row.erase("source");row.erase("path")
	return result
func on_recovered(result: Dictionary) -> void:
	if received:return
	received=true
	var app=get_parent();app.autosave_enabled.button_pressed=false
	var args:=OS.get_cmdline_user_args();var folder: String=args[0];var label: String=args[1];var target:=int(args[2]);var attempts:=int(args[3])
	var expected:=Recovery.read_json(folder.path_join("expected.json"))
	app.has_project.cache_root=folder.path_join("reader-cache")
	for i in range(3):await get_tree().process_frame
	await RenderingServer.frame_post_draw
	check(not result.cancelled and result.attempts.size()==attempts,"normal startup dispatch completed with expected candidate attempts")
	check(not app.has_dialog(app),"startup recovery needs no confirmation or error dialog")
	check(app.home.visible!=bool(result.restored) and (result.restored or result.attempts.is_empty() or app.home.notice.text==app.status.text),"Home follows recovery priority and retains failure feedback")
	check(FileAccess.get_sha256(expected.manual)==expected.manual_sha256,"last explicit HAS remains byte-identical")
	var movie:=""
	if target>=0 and not result.restored:
		var failed:={"case":label,"startup":result,"checks":checks,"failures":failures+1}
		var diagnostic:=FileAccess.open(folder.path_join(label+"-result.json"),FileAccess.WRITE);diagnostic.store_string(JSON.stringify(failed));diagnostic.close()
		print("RECOVERY_STARTUP "+JSON.stringify(failed));get_tree().quit(1);return
	if target>=0:
		var state: Dictionary=expected.states[str(target)]
		check(result.restored and app.dirty and app.project_folder.is_empty() and app.has_project.path.is_empty() and app.recovered_from==expected.checkpoint,"automatic recovery is a dirty unsaved copy without manual-save identity")
		check(app.frame==target and canonical(app.keys)==state.keys and canonical(app.video)==state.video,"correct generation restores full camera range, video and playhead")
		check(portable(app.renderer.world_state())==state.world,"every authored world/native metadata field restores exactly")
		var bindings:=true;var transforms:=true
		for id in state.orders:
			var rig: RefCounted=app.renderer.world_runtime.instance(id)
			bindings=bindings and rig.order==state.orders[id]
			transforms=transforms and canonical(rig.sample_transform(target))==state.transforms[id]
		check(bindings and transforms,"all source-native bone identities and sampled transforms survive restart")
		check(Storage.image_hash(Drawing.cel_at(app.layers[1],target).image)==state.paint,"editable drawing pixels survive restart exactly")
		check(not app.audio_clip.is_empty() and app.audio_clip.start_frame==24 and app.audio_clip.gain_db==-6,"managed WAV and synchronization settings survive restart")
		var current: Image=await app.renderer.capture(app.keys,app.layers,target,true);var before:=Image.load_from_file(folder.path_join("frame%d.png" % target));var a:=current.get_data();var b:=before.get_data();var changed:=0;var total:=0
		for i in range(a.size()):
			if a[i]!=b[i]:changed+=1;total+=absi(int(a[i])-int(b[i]))
		check(changed<=384 and float(total)/a.size()<0.002,"fresh-process render stays within established mesh-edge rebuild bound")
		current.save_png(folder.path_join(label+".png"))
		# Confirm explicit stale startup work cannot overwrite an edited document.
		var world: Dictionary=app.renderer.world_state();var revision: int=app.recovery_revision;var session: String=app.recovery_session
		app.changed();app.recover_latest(session,revision)
		check(app.startup_recovery_result.cancelled and app.renderer.world_state()==world,"deferred recovery refuses to overwrite subsequent user edits")
		if label=="newest":
			var error: String=await app.export_movie(folder)
			movie=app.last_export_folder.path_join("movie.mp4")
			check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000025.png")).get_data()==current.get_data(),"recovered motion, camera, drawing and audio export with exact preview PNG")
		if label=="save":
			var chosen:=folder.path_join("chosen-recovered.has");app.has_project.save_file(chosen,"packed")
			while app.has_project.pid>0:await get_tree().process_frame
			check(FileAccess.file_exists(chosen) and not app.dirty and FileAccess.get_sha256(expected.manual)==expected.manual_sha256,"explicit Save writes chosen recovered HAS and preserves original")
	else:
		check(not result.restored and not app.dirty and app.renderer.world_runtime.instances.is_empty(),"no valid/available checkpoint leaves the clean empty startup world")
		check(app.keys.size()==1 and app.world_selection.selected.is_empty(),"failed candidates do not leak partial world, selection or camera keys")
		check(FileAccess.file_exists(str(expected.checkpoint).path_join("project.backup.json")),"older checkpoint files remain available without deletion")
	var report:={"checks":checks,"failures":failures,"case":label,"startup":result,"movie":movie}
	var file:=FileAccess.open(folder.path_join(label+"-result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(report,"",false,true));file.close()
	print("RECOVERY_STARTUP "+JSON.stringify(report));get_tree().quit(0 if failures==0 else 1)
