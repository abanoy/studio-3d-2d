extends SceneTree
const Motion=preload("res://src/mmd_motion_candidate.gd")
var ticks:=0
func _initialize() -> void:
	create_timer(130).timeout.connect(func():quit(2));call_deferred("run")
func settle() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func wait_build(importer) -> void:
	while importer.busy() and importer.candidate_job.is_empty():await process_frame
	assert(not importer.candidate_job.is_empty(),"No candidate phase: "+importer.app.status.text)
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0]
	var request: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("request.json")))
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settle()
	app.home.hide();app.autosave_enabled.button_pressed=false;app.video.duration_frames=300
	assert(app.pose_editor.add_model(request.source).is_empty())
	var rig: RefCounted=app.renderer.active_model();var before: Dictionary=rig.data.duplicate(true);var history: int=app.history.size()
	var importer=app.mmd_pose_importer
	process_frame.connect(func():ticks+=1)
	# The source worker and the editor-side candidate are separate cancellable phases.
	importer.begin(request.motion,{"source_start":0,"count":241});await wait_build(importer)
	await process_frame
	assert(importer.busy() and importer.motion_button.disabled and importer.candidate_job.next>0)
	assert(importer.candidate_job.next<241 and rig.data==before and app.history.size()==history)
	var cancelled_at: int=importer.candidate_job.next
	importer.progress.confirmed.emit()
	while importer.busy():await process_frame
	await settle()
	assert("cancelled" in app.status.text and rig.data==before and app.history.size()==history and not importer.motion_button.disabled)
	# A nonexclusive progress dialog permits seeking; this invalidates rather than commits.
	importer.begin(request.motion,{"source_start":0,"count":241});await wait_build(importer)
	app.set_frame(1)
	while importer.busy():await process_frame
	await settle()
	assert("scene changed" in app.status.text.to_lower() and rig.data==before and app.history.size()==history)
	app.set_frame(0)
	importer.begin(request.motion,{"source_start":0,"count":241});await wait_build(importer)
	var start_tick:=ticks;var batches:=0;var peak_usec:=0;var previous:=Time.get_ticks_usec()
	while importer.busy():
		await process_frame
		peak_usec=maxi(peak_usec,Time.get_ticks_usec()-previous);previous=Time.get_ticks_usec();batches+=1
		if batches==8:
			await RenderingServer.frame_post_draw
			app.get_viewport().get_texture().get_image().save_png(folder.path_join("motion-progress.png"))
	await settle()
	assert(is_instance_valid(importer.review) and importer.review.visible,app.status.text)
	assert(batches>1 and ticks-start_tick>1 and rig.data==before and app.history.size()==history)
	var converted: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(importer.request.result)).converted
	var sync:=Motion.candidate(rig,converted,0,300,24)
	assert(not sync.has("error"))
	# Both APIs must describe the same motion; generated clip IDs are transaction-local.
	var parallel: Dictionary=importer.proposed.data.duplicate(true)
	assert(parallel.animation_clips.size()==sync.data.animation_clips.size())
	for index in range(parallel.animation_clips.size()):parallel.animation_clips[index].id=sync.data.animation_clips[index].id
	assert(parallel==sync.data)
	importer.review.confirmed.emit();await settle()
	assert(app.history.size()==history+1 and rig.authored_keys().size()==241)
	app.undo();assert(rig.data==before)
	var result:={"frames":241,"batches":batches,"ui_ticks":ticks-start_tick,"peak_frame_usec":peak_usec,"cancelled_after_frames":cancelled_at,"cancel_preserved":true,"stale_preserved":true,"sync_samples_exact":true,"one_step_undo":true}
	FileAccess.open(folder.path_join("app-result.json"),FileAccess.WRITE).store_string(JSON.stringify(result))
	print("MMD_MOTION_PROGRESS ",JSON.stringify(result));app.free();quit(0)
