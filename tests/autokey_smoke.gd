extends SceneTree
const Support = preload("res://tests/world_test_support.gd")
const SceneIO = preload("res://src/scene3d.gd")
const Timeline = preload("res://src/timeline.gd")
const Drawing = preload("res://src/drawing.gd")
var checks := 0
var failures := 0

func _initialize() -> void:
	create_timer(90).timeout.connect(func(): push_error("Auto-key watchdog expired"); quit(2))
	call_deferred("run")

func check(ok: bool, text: String) -> void:
	checks += 1; print(("PASS " if ok else "FAIL ") + text)
	if not ok: failures += 1

func rotate(editor, degrees: float) -> void:
	editor.operation.select(0); editor.refresh_values()
	editor.fields[2].value = degrees; editor.apply_numeric()

func run() -> void:
	var folder := ProjectSettings.globalize_path("res://output/autokey/run_%d" % Time.get_ticks_usec())
	DirAccess.make_dir_recursive_absolute(folder)
	var app = load("res://main.tscn").instantiate()
	app.recovery_root = folder.path_join("recovery")
	root.add_child(app); await process_frame
	var fixture := folder.path_join("rig.glb"); SceneIO.make_pose_fixture(fixture)
	var source_hash := FileAccess.get_sha256(fixture)
	app.pose_editor.add_model(fixture)
	var editor = app.pose_editor
	var rig = Support.rig(app)
	var id := ""
	for candidate in rig.order:
		if rig.bones[candidate].name == "arm": id = candidate
	check(editor.auto_key.button_pressed and not app.advanced_mode and rig.authored_keys().is_empty(), "Simple defaults to auto-key without creating import keys")
	editor.tree_items[id].select(0); editor.frame_model()
	var camera: Camera3D = app.renderer.camera
	app.keys = [Timeline.key(0,camera.position,camera.quaternion,camera.fov),Timeline.key(48,camera.position,camera.quaternion,camera.fov)]
	var camera_keys := JSON.stringify(app.keys)
	rotate(editor, 20)
	check(rig.authored_keys().size()==1 and rig.authored_keys()[0].frame==0 and rig.authored_keys()[0].interpolation=="ease", "manual bone edit automatically keys frame0 with smooth easing")
	var first: Dictionary = rig.data.duplicate(true)
	app.set_frame(4); rotate(editor,80)
	check(rig.authored_keys().size()==2 and rig.authored_keys()[1].frame==4, "manual edit at frame4 adds exact current-frame key")
	check(Timeline.quaternion(rig.sample(2)[id].rotation_xyzw).is_equal_approx(Quaternion(Vector3.BACK,deg_to_rad(50))), "auto-keyed poses interpolate at master frame2")
	app.undo()
	check(rig.data==first, "one Undo removes the edit and newly inserted key together")
	app.redo()
	var before_update: Dictionary = rig.data.duplicate(true)
	rotate(editor,65)
	check(rig.authored_keys().size()==2 and Timeline.quaternion(rig.sample(4)[id].rotation_xyzw).is_equal_approx(Quaternion(Vector3.BACK,deg_to_rad(65))), "editing existing frame updates one key without a replacement prompt")
	app.undo(); check(rig.data==before_update,"Undo restores previous value of an overwritten automatic key")
	app.redo()
	app.set_frame(0); editor.refresh_values(); editor.apply_numeric()
	check(rig.authored_keys().size()==2, "applying unchanged values does not create a key")
	app.set_frame(8); editor.operation.select(0); editor.refresh_values(); editor.update_gizmo()
	var handle: Dictionary = editor.handles[2]
	var start: Vector2 = handle.points[6]
	var press := InputEventMouseButton.new(); press.button_index=MOUSE_BUTTON_LEFT; press.pressed=true
	editor.input(press,start)
	var history: int = app.history.size()
	var motion := InputEventMouseMotion.new()
	editor.input(motion,start+Vector2(20,-10)); editor.input(motion,start+Vector2(40,-20))
	check(editor.dragging and rig.authored_keys().size()==2, "live gizmo motions remain a draft until gesture completes")
	press.pressed=false; editor.input(press,start+Vector2(40,-20))
	check(not editor.dragging and rig.authored_keys().size()==3 and rig.authored_keys()[2].frame==8 and app.history.size()==history+1, "gizmo release creates one key and one undo command")
	app.undo(); editor.update_gizmo()
	handle=editor.handles[2]; start=handle.points[6]
	var before_cancel: Dictionary=rig.data.duplicate(true)
	press.pressed=true; editor.input(press,start); editor.input(motion,start+Vector2(20,-10)); editor.finish_drag(true)
	check(rig.data==before_cancel,"cancelled gizmo restores pose and leaves no key")
	app.set_frame(12); editor.tree_items["@root"].select(0); editor.operation.select(1); editor.refresh_values()
	editor.fields[0].value=0.5; editor.apply_numeric()
	editor.scale_field.value=1.25; editor.scale_apply.pressed.emit()
	check(rig.authored_keys()[-1].frame==12 and is_equal_approx(rig.authored_keys()[-1].transform.scale,1.25) and is_equal_approx(rig.authored_keys()[-1].transform.position[0],0.5),"root translation and uniform scale auto-key through same contract")
	var keys_before := JSON.stringify(rig.authored_keys())
	editor.set_flag("visible",false); editor.set_flag("visible",true); editor.set_flag("reference_only",true); editor.set_flag("reference_only",false)
	app.set_frame(16); editor.tree_items[id].select(0); editor.refresh_values()
	check(JSON.stringify(rig.authored_keys())==keys_before and JSON.stringify(app.keys)==camera_keys and app.layers[1].cels.is_empty(),"selection, frame changes and flags do not key poses, cameras or paint")
	editor.auto_key.button_pressed=false; rotate(editor,35)
	check(JSON.stringify(rig.authored_keys())==keys_before,"Advanced Auto-key off preserves explicit draft workflow")
	editor.record_key(); check(rig.authored_keys()[-1].frame==16,"explicit Record remains usable with Auto-key off")
	editor.auto_key.button_pressed=true
	app.set_frame(20); editor.reset_selected()
	check(rig.authored_keys()[-1].frame==20,"manual Reset selected creates an undoable automatic key")
	app.set_frame(22); editor.tree_items["@root"].select(0); editor.operation.select(1); editor.refresh_values()
	editor.fields[0].value=90000; editor.apply_numeric()
	editor.fields[0].value=90000.05; editor.apply_numeric()
	check(absf(rig.authored_keys()[-1].transform.position[0]-90000.05)<0.01,"small authored move far from origin updates automatic key")
	app.undo(); app.undo()
	app.mode.select(0); app.change_mode(0); app.set_frame(4); app.create_cel(false)
	Drawing.stroke(Drawing.cel_at(app.layers[1],4).image,Vector2(100,100),Vector2(200,100),6,Color.RED,false)
	var has = app.has_project; has.cache_root=folder.path_join("cache")
	var saved_keys: Array = JSON.parse_string(JSON.stringify(rig.authored_keys(),"",true,true))
	var project := folder.path_join("auto-keyed.has")
	has.save_file(project,"packed")
	while has.pid>0: await process_frame
	has.open_file(project)
	while has.pid>0: await process_frame
	check(has.path==project and JSON.parse_string(JSON.stringify(Support.rig(app).authored_keys(),"",true,true))==saved_keys,"automatic independent controls round-trip through packed HAS")
	var expected: Image=await app.renderer.capture(app.keys,app.layers,4,true)
	var error: String=await app.export_movie(folder)
	var frame:=Image.load_from_file(app.last_export_folder.path_join("frame_000005.png"))
	check(error.is_empty() and frame.get_data()==expected.get_data(),"auto-keyed animation and independent cel export with identical frame4 pixels")
	check(JSON.parse_string(JSON.stringify(Support.rig(app).authored_keys(),"",true,true))==saved_keys and FileAccess.get_sha256(fixture)==source_hash,"export creates no keys and original model bytes stay unchanged")
	var native := []
	for sample in [{"project":"pose-smoke/miku-project","bone":"左腕"},{"project":"source-smoke/source-project","bone":"L_UpperArm"},{"project":"sfm-smoke/project","bone":"bip_upperArm_L"}]:
		var project_folder := ProjectSettings.globalize_path("res://output/"+str(sample.project))
		if not FileAccess.file_exists(project_folder.path_join("project.json")):
			print("SKIP private native auto-key fixture absent: "+str(sample.project)); continue
		check(app.open_project(project_folder),"native prepared fixture opens for auto-key: "+str(sample.project))
		rig=Support.select_rig(app); editor=app.pose_editor
		id=""
		for candidate in rig.order:
			if str(rig.bones[candidate].name).ends_with(str(sample.bone)): id=candidate
		if id.is_empty(): check(false,"required native arm: "+str(sample.project)); continue
		app.mode.select(2); app.change_mode(2); app.set_frame(0)
		editor.tree_items[id].select(0); editor.frame_model()
		camera=app.renderer.camera
		app.keys=[Timeline.key(0,camera.position,camera.quaternion,camera.fov)]
		var native_before: Dictionary=rig.data.duplicate(true)
		var native_hash:=FileAccess.get_sha256(rig.data.source)
		var before_image: Image=await app.renderer.capture(app.keys,[],0,true)
		editor.operation.select(0); editor.refresh_values(); editor.fields[2].value+=35; editor.apply_numeric()
		var after_image: Image=await app.renderer.capture(app.keys,[],0,true)
		check(rig.authored_keys()[0].frame==0 and rig.authored_keys()[0].pose==rig.sample(0,true) and before_image.get_data()!=after_image.get_data(),"native arm edit auto-keys and visibly deforms shared rig: "+str(sample.project))
		app.undo()
		check(rig.data==native_before and FileAccess.get_sha256(rig.data.source)==native_hash,"native auto-key Undo restores full data and source remains unchanged: "+str(sample.project))
		native.append(sample.project)
	var report:={"checks":checks,"failures":failures,"movie":app.last_export_folder.path_join("movie.mp4"),"folder":folder,"native_projects":native}
	var file:=FileAccess.open(ProjectSettings.globalize_path("res://output/autokey-result.json"),FileAccess.WRITE); file.store_string(JSON.stringify(report)); file.close()
	print("AUTOKEY_SMOKE "+JSON.stringify(report)); quit(0 if failures==0 else 1)
