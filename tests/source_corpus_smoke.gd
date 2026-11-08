extends SceneTree
const Timeline=preload("res://src/timeline.gd")
const Storage=preload("res://src/storage.gd")
var app
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(600).timeout.connect(func():push_error("Native corpus ingress watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settle() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func visible_pixels(image: Image) -> bool:
	if image==null or image.get_size()!=Vector2i(1920,1080):return false
	var blank:=Image.create(1920,1080,false,Image.FORMAT_RGBA8);blank.fill(image.get_pixel(0,0))
	return image.get_data()!=blank.get_data()
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0]
	var plans: Array=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("plans.json")))
	if "--images" in OS.get_cmdline_user_args():
		for plan in plans:check(visible_pixels(Image.load_from_file(folder.path_join(plan.name+".png"))),plan.name+" has nonuniform actual full-resolution pixels")
		var result:={"checks":checks,"failures":failures,"mode":"captured-images"}
		FileAccess.open(folder.path_join("image-checks.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("SOURCE_CORPUS_IMAGES "+JSON.stringify(result));quit(0 if failures==0 else 1);return
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.display_prefs_path=folder.path_join("prefs.cfg");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false
	var observations:=[]
	for plan in plans:
		app.new_project();await settle()
		var why: String=app.pose_editor.add_model(plan.glb)
		check(why.is_empty(),plan.name+" imports through ordinary Add model")
		await settle();var rig=app.renderer.active_model()
		check(rig!=null and rig.order.size()==int(plan.bones),plan.name+" preserves converted native bones")
		if rig==null:continue
		check(rig.data.metadata.native_parameters.source_profile=="standalone" and not app.physics_editor.is_running(),plan.name+" preserves standalone provenance and manual pose mode")
		app.pose_editor.frame_model();await settle()
		app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,app.renderer.camera.fov)]
		var image: Image=await app.renderer.capture(app.keys,[],0,true)
		var small: Image=image.duplicate();small.resize(64,36,Image.INTERPOLATE_NEAREST)
		var colors:={}
		for y in range(36):
			for x in range(64):colors[small.get_pixel(x,y).to_rgba32()]=true
		check(visible_pixels(image),plan.name+" produces nonuniform actual full HD pixels")
		image.save_png(folder.path_join(plan.name+".png"))
		observations.append({"name":plan.name,"bones":rig.order.size(),"sample_colors":colors.size(),"used_rect":str(image.get_used_rect()),"render_sha256":Storage.image_hash(image)})
	var result:={"checks":checks,"failures":failures,"models":observations}
	FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("SOURCE_CORPUS "+JSON.stringify({"checks":checks,"failures":failures,"models":observations.size()}));app.free();quit(0 if failures==0 else 1)
