extends SceneTree
const Model=preload("res://src/model.gd")
const Motion=preload("res://src/mmd_motion_candidate.gd")
const T=preload("res://src/timeline.gd")
const Drawing=preload("res://src/drawing.gd")
func _initialize() -> void:
	create_timer(100).timeout.connect(func():quit(2));call_deferred("run")
func settle() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func job(app) -> void:
	while app.has_project.pid>0:await process_frame
	await settle()
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0]
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settle()
	app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	var request: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("request.json")))
	var converted: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("converted.json")))
	assert(app.pose_editor.add_model(request.source).is_empty())
	var rig: RefCounted=app.renderer.active_model();var id: String=rig.data.id
	app.pose_editor.record_key();app.set_frame(12)
	var before: Dictionary=rig.data.duplicate(true);var history: int=app.history.size();var camera: Array=app.keys.duplicate(true)
	assert(Motion.candidate(rig,converted,12,20,24).has("error"))
	assert(Motion.candidate(rig,converted,12,48,30).has("error"))
	assert(rig.data==before and app.history.size()==history)
	var existing:=Model.new();existing.root=rig.root;existing.bones=rig.bones;existing.order=rig.order
	existing.data=rig.body_animation().promote(before,48)
	existing.data.animation_clips[0].length=40;existing.data.animation_clips[0].auto_extend=false;existing.data.animation_clips[0]["body_untrimmed"]=false
	var long_block: Dictionary=existing.data.duplicate(true)
	var sliced:=Motion.prepare_range(existing,12,25,48)
	assert(not sliced.has("error") and existing.data==long_block and sliced.data.animation_clips.size()==3)
	assert(sliced.data.animation_clips[1].start==12 and sliced.data.animation_clips[1].length==25)
	existing.data.animation_clips[0].length=10
	var second: Dictionary=existing.data.animation_clips[0].duplicate(true);second.id=str(ResourceUID.create_id());second.start=30
	existing.data.animation_clips.append(second)
	var two_blocks: Dictionary=existing.data.duplicate(true)
	assert(Motion.prepare_range(existing,5,30,48).has("error") and existing.data==two_blocks)
	existing.data=before.duplicate(true);existing.data.metadata["animation_imports"]="foreign metadata"
	assert(Motion.candidate(existing,converted,12,48,24).has("error"))
	var proposed:=Motion.candidate(rig,converted,12,48,24)
	assert(not proposed.has("error"),str(proposed))
	assert(rig.data==before and app.history.size()==history and app.keys==camera)
	var importer=app.mmd_pose_importer
	importer.motion_range(request.motion);await settle()
	app.set_frame(13);importer.range_dialog.confirmed.emit();await settle()
	assert(importer.pid<=0 and rig.data==before and app.history.size()==history and "scene changed" in app.status.text.to_lower())
	app.set_frame(12)
	importer.begin(request.motion,{"source_start":0,"count":25});importer.cancel()
	while importer.busy():await process_frame
	await settle()
	assert(rig.data==before and app.history.size()==history and not importer.motion_button.disabled and "cancelled" in app.status.text)
	importer.begin(folder.path_join("camera-only.vmd"),{"source_start":0,"count":25})
	while importer.busy():await process_frame
	await settle()
	assert(rig.data==before and app.history.size()==history and "no model motion" in app.status.text)
	importer.motion_button.pressed.emit()
	var picker: FileDialog
	for child in app.get_children():
		if child is FileDialog and child.visible:picker=child
	assert(is_instance_valid(picker))
	picker.file_selected.emit(request.motion);await settle()
	assert(is_instance_valid(importer.range_dialog) and importer.range_dialog.visible)
	importer.motion_count.value=25;importer.range_dialog.confirmed.emit()
	while importer.busy():await process_frame
	await settle()
	assert(is_instance_valid(importer.review) and importer.review.visible,app.status.text)
	assert("frames 12–36 (25 frames)" in importer.review.dialog_text and rig.data==before and app.history.size()==history)
	app.get_viewport().get_texture().get_image().save_png(folder.path_join("motion-review.png"))
	importer.review.confirmed.emit();await settle()
	var after: Dictionary=rig.data.duplicate(true)
	for value in rig.data.animation_clips:assert(not value.has("mmd_motion_reservation"))
	assert(app.history.size()==history+1 and rig.authored_keys().size()==26)
	var piece: Dictionary=rig.data.animation_clips[Model.Clips.index_at(rig.data,12)]
	if piece.start!=12 or piece.length!=25:
		var bounds: Array=[]
		for value in rig.data.animation_clips:bounds.append({"start":value.start,"length":value.length,"source_in":value.source_in})
		print("MOTION_PIECE_BOUNDS ",JSON.stringify(bounds));app.free();quit(1);return
	assert(rig.data.metadata.animation_imports[-1].source_sha256==converted.source_sha256)
	for i in range(converted.samples.size()):
		var pose: Dictionary=rig.sample_body(12+i)
		for control in converted.samples[i].bones:
			var bone_id:=""
			for value in rig.order:
				if rig.bones[value].name==control.name:bone_id=value
			assert(not bone_id.is_empty())
			var position: Vector3=rig.bones[bone_id].base.basis*T.vector(control.translation)
			assert(position.distance_to(T.vector(pose[bone_id].position))<1e-5)
			assert(absf(T.quaternion(pose[bone_id].rotation_xyzw).dot(T.quaternion(control.rotation_xyzw)))>1.-1e-6)
	var row: Dictionary=rig.root.get_meta(Model.Shape.META).rows[0]
	var node:=str(row.node);var blink:=str(row.names.find("まばたき"))
	assert(is_equal_approx(rig.sample_shapes(24)[node][blink],.5))
	app.clip_editor.move_piece(id,piece.id,20,after)
	assert(rig.data.animation_clips[Model.Clips.index_at(rig.data,20)].start==20 and is_equal_approx(rig.sample_shapes(32)[node][blink],.5))
	app.undo();assert(rig.data==after)
	app.undo();assert(rig.data==before)
	app.redo();assert(rig.data==after)
	app.set_frame(24);app.pose_editor.frame_model();app.keys=[T.from_camera(0,app.renderer.camera,"linear")]
	Drawing.insert(app.layers[1],0,48,Drawing.blank(1920,1080));Drawing.edit_image(Drawing.cel_at(app.layers[1],24)).image.set_pixel(80,80,Color.CYAN)
	var expected: Image=await app.renderer.capture(app.keys,app.layers,24,true)
	expected.save_png(folder.path_join("motion-frame.png"))
	var path:=folder.path_join("motion.has");app.has_project.save_file(path,"packed");await job(app)
	assert(app.has_project.path==path)
	app.new_project();app.has_project.open_file(path);await job(app)
	rig=app.renderer.world_runtime.instance(id)
	assert(rig.authored_keys().size()==26 and is_equal_approx(rig.sample_shapes(24)[node][blink],.5))
	var reopened: Image=await app.renderer.capture(app.keys,app.layers,24,true)
	assert(reopened.get_data()==expected.get_data())
	assert(await app.export_movie(folder)=="")
	assert(Image.load_from_file(app.last_export_folder.path_join("frame_000025.png")).get_data()==expected.get_data())
	var result:={"project":path,"movie":app.last_export_folder.path_join("movie.mp4"),"body_keys":26,"sampled_frames":25,"pixels_exact":true,"undo_restored":true,"frame_rate_guard":true,"range_guard":true,"picker_range_review":true,"movable_standard_piece":true,"source_provenance":true,"cancellation_preserved":true,"stale_range_rejected":true,"camera_only_preserved":true}
	FileAccess.open(folder.path_join("app-result.json"),FileAccess.WRITE).store_string(JSON.stringify(result))
	print("MMD_MOTION_SMOKE ",JSON.stringify(result));app.free();quit(0)
