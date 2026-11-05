extends SceneTree
const Model=preload("res://src/model.gd")
const T=preload("res://src/timeline.gd")
const Drawing=preload("res://src/drawing.gd")
func _initialize() -> void:
	create_timer(150).timeout.connect(func():quit(2));call_deferred("run")
func settle() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func wait_import(importer) -> void:
	while importer.busy():await process_frame
	await settle()
func job(app) -> void:
	while app.has_project.pid>0:await process_frame
	await settle()
func bone(rig,native: String) -> String:
	for id in rig.order:
		if rig.bones[id].name==native:return id
	return ""
func error_distance(rig) -> float:
	return rig.bone_transform(bone(rig,"左足首")).origin.distance_to(rig.bone_transform(bone(rig,"左足ＩＫ")).origin)
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0]
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settle()
	app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	var source:=folder.path_join("native/scene.glb")
	assert(app.pose_editor.add_model(source).is_empty())
	var rig: RefCounted=app.renderer.active_model();var id: String=rig.data.id
	assert(rig.data.metadata.native_parameters.ik_constraints.chains.size()==7)
	var right_knee:=bone(rig,"右ひざ");var right_arm:=bone(rig,"右腕")
	var manual: Dictionary=rig.data.duplicate(true)
	var rotation:=Quaternion(Vector3.RIGHT,.2)
	manual.pose[right_knee]={"position":[0,0,0],"rotation_xyzw":[rotation.x,rotation.y,rotation.z,rotation.w]}
	manual.pose[right_arm]=manual.pose[right_knee].duplicate(true)
	assert(app.pose_editor.restore_state(manual).is_empty())
	app.set_frame(12)
	var before: Dictionary=rig.data.duplicate(true);var body_before: Dictionary=rig.sample_body(12,true);var history: int=app.history.size()
	var importer=app.mmd_pose_importer
	importer.begin(folder.path_join("foot.vpd"));await wait_import(importer)
	assert(is_instance_valid(importer.review) and importer.review.visible,app.status.text)
	assert("Joint chains solved: 2" in importer.review.dialog_text)
	app.get_viewport().get_texture().get_image().save_png(folder.path_join("ik-review.png"))
	importer.review.confirmed.emit();await settle()
	assert(app.history.size()==history+1 and error_distance(rig)<.001)
	assert(rig.sample_body(12)[right_knee]==body_before[right_knee] and rig.sample_body(12)[right_arm]==body_before[right_arm])
	var posed: Dictionary=rig.data.duplicate(true)
	app.undo();assert(rig.data==before)
	app.redo();assert(rig.data==posed)
	app.pose_editor.frame_model();app.keys=[T.from_camera(0,app.renderer.camera,"linear")]
	Drawing.insert(app.layers[1],0,48,Drawing.blank(1920,1080));Drawing.cel_at(app.layers[1],12).image.set_pixel(80,80,Color.CYAN)
	var expected: Image=await app.renderer.capture(app.keys,app.layers,12,true)
	expected.save_png(folder.path_join("ik-pose.png"))
	var path:=folder.path_join("ik-pose.has");app.has_project.save_file(path,"packed");await job(app)
	assert(app.has_project.path==path)
	app.new_project();app.has_project.open_file(path);await job(app)
	rig=app.renderer.world_runtime.instance(id)
	assert(error_distance(rig)<.001)
	assert((await app.renderer.capture(app.keys,app.layers,12,true)).get_data()==expected.get_data())
	# A fresh model makes the off-switch's FK baseline unambiguous.
	app.new_project();assert(app.pose_editor.add_model(source).is_empty())
	rig=app.renderer.active_model();id=rig.data.id
	before=rig.data.duplicate(true);history=app.history.size()
	importer.begin(folder.path_join("foot.vmd"),{"source_start":0,"count":25});await wait_import(importer)
	assert(is_instance_valid(importer.review) and importer.review.visible,app.status.text)
	importer.review.confirmed.emit();await settle()
	assert(app.history.size()==history+1)
	app.set_frame(8);await settle();assert(error_distance(rig)<.001)
	app.set_frame(12);await settle();assert(error_distance(rig)>.03)
	var knee:=bone(rig,"左ひざ")
	assert(absf(T.quaternion(rig.sample_body(12)[knee].rotation_xyzw).dot(Quaternion.IDENTITY))>1.-1e-6)
	app.set_frame(20);await settle();assert(error_distance(rig)<.001)
	var animated: Dictionary=rig.data.duplicate(true)
	app.undo();assert(rig.data==before)
	app.redo();assert(rig.data==animated)
	app.pose_editor.frame_model();app.keys=[T.from_camera(0,app.renderer.camera,"linear")]
	Drawing.insert(app.layers[1],0,48,Drawing.blank(1920,1080));Drawing.cel_at(app.layers[1],20).image.set_pixel(80,80,Color.CYAN)
	expected=await app.renderer.capture(app.keys,app.layers,20,true)
	path=folder.path_join("ik-motion.has");app.has_project.save_file(path,"packed");await job(app)
	assert(app.has_project.path==path)
	app.new_project();app.has_project.open_file(path);await job(app)
	rig=app.renderer.world_runtime.instance(id)
	assert((await app.renderer.capture(app.keys,app.layers,20,true)).get_data()==expected.get_data())
	app.set_frame(12);await settle();assert(error_distance(rig)>.03)
	app.set_frame(20);await settle();assert(error_distance(rig)<.001)
	assert(await app.export_movie(folder)=="")
	assert(Image.load_from_file(app.last_export_folder.path_join("frame_000021.png")).get_data()==expected.get_data())
	var foot_reach:=error_distance(rig);var movie: String=app.last_export_folder.path_join("movie.mp4")
	assert(app.pose_editor.add_model(folder.path_join("pmx/scene.glb")).is_empty())
	var hinge: RefCounted=app.renderer.active_model()
	assert(hinge.data.metadata.native_parameters.ik_constraints.chains.size()==1)
	importer.begin(folder.path_join("hinge.vpd"));await wait_import(importer)
	assert(is_instance_valid(importer.review) and importer.review.visible,app.status.text)
	importer.review.confirmed.emit();await settle()
	var hinge_reach: float=hinge.bone_transform(bone(hinge,"Tip")).origin.distance_to(hinge.bone_transform(bone(hinge,"Foot target")).origin)
	assert(hinge_reach<.001)
	var result:={"movie":movie,"project":path,"native_chains":7,"foot_reach":foot_reach,"pmx_hinge_reach":hinge_reach,"unrelated_fk_preserved":true,"switches_baked":true,"undo_restored":true,"pixels_exact":true,"raw_pmx_tested":true}
	FileAccess.open(folder.path_join("app-result.json"),FileAccess.WRITE).store_string(JSON.stringify(result))
	print("MMD_IK_SMOKE ",JSON.stringify(result));app.free();quit(0)
