extends SceneTree
const Storage=preload("res://src/storage.gd")
const T=preload("res://src/timeline.gd")
var app
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(180).timeout.connect(func():push_error("Native motion watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settle() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func jobs() -> void:
	while app.has_project.pid>0:await process_frame
	await settle()
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0];var root_path: String=args[1]
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.display_prefs_path=folder.path_join("prefs.cfg");app.recent_path=folder.path_join("recent.json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	check(app.pose_editor.add_model(root_path.path_join("miku-final/scene.glb")).is_empty(),"native Miku is available for native pose/motion import")
	await settle();var rig=app.renderer.active_model();var id: String=rig.data.id
	app.pose_editor.frame_model();await settle();app.keys=[T.from_camera(0,app.renderer.camera,"linear")]
	var importer=app.mmd_pose_importer
	for kind in ["pose","motion"]:
		app.set_frame(0 if kind=="pose" else 12);await settle();rig=app.renderer.world_runtime.instance(id)
		var before: Dictionary=rig.data.duplicate(true);var history: int=app.history.size();var camera: Array=app.keys.duplicate(true)
		var path:=root_path.path_join("motion/Original arm pose.vpd" if kind=="pose" else "motion/Original arm motion.vmd");var identity:=FileAccess.get_sha256(path)
		importer.begin(path,{} if kind=="pose" else {"source_start":0,"count":11})
		while importer.busy():await process_frame
		await settle()
		check(is_instance_valid(importer.review) and importer.review.visible,kind+" native file produces actual review")
		if not is_instance_valid(importer.review):print(app.status.text);app.free();quit(1);return
		check(rig.data==before and app.history.size()==history and app.keys==camera,kind+" candidate preserves scene before Apply")
		importer.review.confirmed.emit();await settle();rig=app.renderer.world_runtime.instance(id)
		var after: Dictionary=rig.data.duplicate(true)
		check(after!=before and app.history.size()==history+1,kind+" Apply commits one editable animation change")
		app.undo();await settle();rig=app.renderer.world_runtime.instance(id);check(rig.data==before,kind+" Undo restores exact native model state")
		app.redo();await settle();rig=app.renderer.world_runtime.instance(id);check(rig.data==after and FileAccess.get_sha256(path)==identity,kind+" Redo restores animation and leaves native file unchanged")
	var first: Image=await app.renderer.capture(app.keys,app.layers,12,true);var last: Image=await app.renderer.capture(app.keys,app.layers,22,true)
	check(first.get_data()!=last.get_data(),"native VMD changes actual posed geometry across its sampled range")
	var packed:=folder.path_join("Native motion.has");app.has_project.save_file(packed,"packed");await jobs();check(app.has_project.path==packed,"native pose and motion save in canonical HAS")
	app.new_project();app.has_project.open_file(packed);await jobs()
	check(Storage.image_hash(await app.renderer.capture(app.keys,app.layers,22,true))==Storage.image_hash(last),"native motion exact pixels survive saved HAS reopening")
	var result:={"checks":checks,"failures":failures};print("MMD_NATIVE_MOTION "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
