extends SceneTree
const Model=preload("res://src/model.gd")
const T=preload("res://src/timeline.gd")
func _initialize() -> void:
	create_timer(90).timeout.connect(func():quit(2))
	call_deferred("run")
func settle() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func job(app) -> void:
	while app.has_project.pid>0:await process_frame
	await settle()
func run() -> void:
	var folder:=ProjectSettings.globalize_path("res://output/mmd-pose-tests/app-roundtrip-%d" % Time.get_ticks_usec())
	DirAccess.make_dir_recursive_absolute(folder)
	var app=load("res://main.tscn").instantiate()
	app.recovery_root=folder.path_join("recovery");root.add_child(app);await settle()
	app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	var manifest: Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://output/native-import-verification.json"))
	var source: String=manifest.bundles[0].path_join("scene.glb")
	var import_error: String=app.pose_editor.add_model(source)
	if not import_error.is_empty():print(import_error);app.free();quit(1);return
	var rig: RefCounted=app.renderer.active_model()
	var id: String=rig.data.id
	var row: Dictionary=rig.root.get_meta(Model.Shape.META).rows[0]
	var node:=str(row.node)
	var blink:=str(row.names.find("まばたき"));var mouth:=str(row.names.find("あ"))
	assert(blink!="-1" and mouth!="-1")
	assert(app.pose_editor.set_shape_amounts({node:{mouth:.2}}).is_empty())
	app.pose_editor.record_key()
	app.set_frame(12)
	app.pose_editor.frame_model();await settle()
	var before: Dictionary=rig.data.duplicate(true)
	var history: int=app.history.size()
	var importer=app.mmd_pose_importer
	var pose_path:=ProjectSettings.globalize_path("res://output/mmd-pose-tests/generated.vpd")
	importer.import_button.pressed.emit()
	var picker: FileDialog
	for child in app.get_children():
		if child is FileDialog:picker=child
	assert(is_instance_valid(picker) and picker.visible)
	picker.file_selected.emit(pose_path)
	assert(importer.pid>0 and importer.import_button.disabled)
	importer.cancel()
	while importer.busy():await process_frame
	await settle()
	assert(rig.data==before and app.history.size()==history and not importer.import_button.disabled)
	assert("cancelled" in app.status.text and not is_instance_valid(importer.review))
	importer.begin(folder.path_join("missing.vpd"))
	while importer.busy():await process_frame
	await settle()
	assert(rig.data==before and app.history.size()==history and not importer.import_button.disabled)
	assert(not is_instance_valid(importer.review))
	importer.begin(pose_path)
	while importer.busy():await process_frame
	await settle()
	assert(is_instance_valid(importer.review) and importer.review.visible,app.status.text)
	assert("2 matched bones at frame 12" in importer.review.dialog_text and rig.data==before)
	assert("Shape controls matched: 1" in importer.review.dialog_text and "Shape controls skipped: 1" in importer.review.dialog_text and "not a real shape" in importer.review.dialog_text)
	app.get_viewport().get_texture().get_image().save_png(folder.path_join("pose-review.png"))
	app.set_frame(13)
	importer.review.confirmed.emit();await settle()
	assert(rig.data==before and app.history.size()==history and "scene changed" in app.status.text.to_lower())
	app.set_frame(12)
	importer.begin(pose_path)
	while importer.busy():await process_frame
	await settle()
	assert(is_instance_valid(importer.review) and importer.review.visible)
	importer.review.confirmed.emit();await settle()
	var imported: Dictionary=rig.data.duplicate(true)
	assert(app.history.size()==history+1 and rig.authored_keys().size()==2)
	assert(is_equal_approx(rig.sample_shapes(12)[node][blink],.75))
	assert(is_equal_approx(rig.sample_shapes(12)[node][mouth],.2))
	assert(Model.ShapeAnimation.has_control(rig.data,12,node,blink) and not Model.ShapeAnimation.has_control(rig.data,12,node,mouth))
	app.undo();assert(rig.data==before)
	app.redo();assert(rig.data==imported)
	app.pose_editor.frame_model()
	app.keys=[T.from_camera(0,app.renderer.camera,"ease")]
	app.mode.select(0);app.change_mode(0);await settle()
	var expected: Image=await app.renderer.capture(app.keys,app.layers,12,true)
	expected.save_png(folder.path_join("posed-frame.png"))
	var without_blink: Dictionary=rig.data.duplicate(true)
	for piece in without_blink.animation_clips:
		for key in piece.get("shape_keys",[]):
			if key.shapes.get(node,{}).has(blink):key.shapes[node][blink]=0.
	rig.data=without_blink
	var neutral: Image=await app.renderer.capture(app.keys,app.layers,12,true)
	assert(neutral.get_data()!=expected.get_data())
	rig.data=imported
	app.set_frame(18)
	var body_before: Array=rig.authored_keys().duplicate(true)
	var shape_before: Dictionary=rig.data.duplicate(true)
	var shape_history: int=app.history.size()
	importer.begin(ProjectSettings.globalize_path("res://output/mmd-pose-tests/shapes-only.vpd"))
	while importer.busy():await process_frame
	await settle()
	assert(is_instance_valid(importer.review) and importer.review.visible and "0 matched bones at frame 18" in importer.review.dialog_text,app.status.text)
	importer.review.confirmed.emit();await settle()
	assert(rig.authored_keys()==body_before and is_zero_approx(rig.sample_shapes(18)[node][blink]) and is_equal_approx(rig.sample_shapes(18)[node][mouth],.2))
	assert(app.history.size()==shape_history+1)
	var shape_after: Dictionary=rig.data.duplicate(true)
	app.undo();assert(rig.data==shape_before)
	app.redo();assert(rig.data==shape_after)
	app.set_frame(12)
	var path:=folder.path_join("pose.has")
	app.has_project.save_file(path,"packed");await job(app)
	assert(app.has_project.path==path)
	app.new_project();app.has_project.open_file(path);await job(app)
	rig=app.renderer.world_runtime.instance(id)
	assert(rig.authored_keys().size()==2 and rig.authored_keys()[1].frame==12)
	assert(is_equal_approx(rig.sample_shapes(12)[node][blink],.75) and is_zero_approx(rig.sample_shapes(18)[node][blink]))
	var actual: Image=await app.renderer.capture(app.keys,app.layers,12,true)
	assert(actual.get_data()==expected.get_data())
	var error: String=await app.export_movie(folder)
	assert(error.is_empty(),error)
	assert(Image.load_from_file(app.last_export_folder.path_join("frame_000013.png")).get_data()==actual.get_data())
	var result:={"project":path,"movie":app.last_export_folder.path_join("movie.mp4"),"keys":2,"undo_restored":true,"pixels_exact":true,"cancellation_preserved":true,"missing_pose_preserved":true,"stale_review_rejected":true,"shapes_keyed":true,"shape_only_preserved_body":true,"shape_pixels_changed":true}
	var file:=FileAccess.open("res://output/mmd-pose-result.json",FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close()
	print("VPD_APP_ROUNDTRIP ",JSON.stringify(result))
	app.free();quit(0)
