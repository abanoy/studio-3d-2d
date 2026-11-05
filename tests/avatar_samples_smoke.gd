extends SceneTree
const Support=preload("res://tests/world_test_support.gd")
# Optional owner-private prepared fixtures; this is not a native VRM/card importer.
const Drawing=preload("res://src/drawing.gd")
const Timeline=preload("res://src/timeline.gd")
var checks:=0
var failures:=0

func _initialize() -> void:
	create_timer(100).timeout.connect(func():push_error("Avatar sample watchdog expired");quit(2))
	call_deferred("run")

func check(ok: bool,text: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+text)
	if not ok:failures+=1

func settled() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw

func wait_job(job) -> void:
	while job.pid>0:await process_frame
	await settled()

func morph_count(node: Node) -> int:
	var count: int=node.mesh.get_blend_shape_count() if node is MeshInstance3D and node.mesh else 0
	for child in node.get_children():count+=morph_count(child)
	return count

func run() -> void:
	var request_path:=ProjectSettings.globalize_path("res://output/vrm-owner-test-request.json")
	if not FileAccess.file_exists(request_path):print("SKIP owner avatar fixtures absent");quit(0);return
	var request: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(request_path))
	var folder:=ProjectSettings.globalize_path("res://output/avatar-samples/run_%d" % Time.get_ticks_usec());DirAccess.make_dir_recursive_absolute(folder)
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled()
	app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	var identities: Array[String]=[]
	for row in request.models:
		var error: String=app.pose_editor.add_model(row.glb)
		check(error.is_empty(),"VRM%s container loads through standard GLB/model path" % row.version)
		if not error.is_empty():app.free();quit(1);return
		var rig: RefCounted=app.renderer.active_model();identities.append(rig.data.id)
		check(not rig.order.is_empty() and rig.order.size()<=512,"VRM%s retains poseable skeleton" % row.version)
		var arm: String=""
		for id in rig.order:
			if "UpperArm" in rig.bones[id].name and "_L_" in rig.bones[id].name:arm=id;break
		check(not arm.is_empty(),"VRM%s native left upper arm resolves" % row.version)
		if arm.is_empty():app.free();quit(1);return
		app.pose_editor.frame_model();app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,app.renderer.camera.fov)]
		app.mode.select(0);app.change_mode(0);app.set_frame(0)
		var before: Image=await app.renderer.capture(app.keys,app.layers,0,true)
		app.mode.select(2);app.change_mode(2);app.pose_editor.tree_items[arm].select(0);app.pose_editor.operation.select(0);app.pose_editor.refresh_values()
		app.pose_editor.fields[2].value=40;app.pose_editor.apply_numeric();await settled()
		var after: Image=await app.renderer.capture(app.keys,app.layers,0,true)
		check(before.get_data()!=after.get_data() and rig.authored_keys().size()==1,"VRM%s arm edit deforms skin and auto-keys" % row.version)
		app.undo();var undone: Image=await app.renderer.capture(app.keys,app.layers,0,true)
		check(before.get_data()==undone.get_data(),"VRM%s pose Undo restores exact pixels" % row.version)
		app.redo()
		var morphs:=morph_count(rig.root)
		check(morphs>0,"VRM%s retains native morph geometry (no expression UI claim)" % row.version)
		after.save_png(folder.path_join("vrm-"+str(row.version)+".png"))
		check(FileAccess.get_sha256(row.source)==row.sha256,"VRM%s original bytes unchanged" % row.version)
		app.pose_editor.set_flag("visible",false)
	check(app.renderer.world_runtime.instances.size()==request.models.size(),"both VRM versions coexist as independent standard instances")
	app.world_selection.select_entity(identities[0]);app.pose_editor.set_flag("visible",true);app.pose_editor.frame_model()
	app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,app.renderer.camera.fov)]
	app.mode.select(0);app.change_mode(0);app.create_cel(false);Drawing.stroke(Drawing.cel_at(app.layers[1],0).image,Vector2(100,100),Vector2(220,100),6,Color.RED,false);app.changed()
	var expected: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	var project:=folder.path_join("avatars.has");app.has_project.save_file(project,"packed");await wait_job(app.has_project)
	check(app.has_project.path==project and not app.dirty,"VRM geometry/poses and independent drawing save as packed HAS")
	app.new_project();app.has_project.open_file(project);await wait_job(app.has_project)
	check(app.renderer.world_runtime.instances.size()==request.models.size() and app.world_selection.selected.is_empty(),"normal HAS reopen restores both VRM instances without selection")
	var reopened: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	check(expected.get_data()==reopened.get_data(),"VRM packed reopen matches exact preview pixels")
	var export_error: String=await app.export_movie(folder)
	var exported:=Image.load_from_file(app.last_export_folder.path_join("frame_000001.png"))
	check(export_error.is_empty() and exported!=null and reopened.get_data()==exported.get_data(),"VRM camera/pose/RGBA MP4 frame matches reopened preview")
	var result:={"checks":checks,"failures":failures,"project":project,"folder":folder,"movie":app.last_export_folder.path_join("movie.mp4"),"scope":"VRM GLB geometry/FK/morph preservation test; native importer and VRM behavior pending"}
	var file:=FileAccess.open("res://output/avatar-samples-result.json",FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close()
	print("AVATAR_SAMPLES "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
