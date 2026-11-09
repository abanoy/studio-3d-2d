extends SceneTree
const Timeline=preload("res://src/timeline.gd")
const World=preload("res://src/world_document.gd")
const Storage=preload("res://src/storage.gd")
var app
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(210).timeout.connect(func():push_error("Scenario A watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settle() -> void:
	for i in range(5):await process_frame
	await RenderingServer.frame_post_draw
func jobs() -> void:
	while app.has_project.pid>0 or app.source_import.pid>0:await process_frame
	await settle()
func pointer(point: Vector2,pressed: bool) -> void:
	var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.pressed=pressed
	var rect: Rect2=app.canvas.image_rect();event.position=rect.position+point/Vector2(1920,1080)*rect.size
	app.canvas._gui_input(event)
func normalized(value):return JSON.parse_string(JSON.stringify(value,"",true,true))
func drag(editor,delta: Vector2) -> void:
	editor.update_gizmo();var start: Vector2=editor.handles[2].points[6]
	pointer(start,true);check(editor.dragging,"projected rotation gizmo accepts actual canvas press")
	var motion:=InputEventMouseMotion.new();var rect: Rect2=app.canvas.image_rect();motion.position=rect.position+(start+delta)/Vector2(1920,1080)*rect.size
	app.canvas._gui_input(motion);pointer(start+delta,false);await settle()
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0];var packed:=folder.path_join("Freeform animation.has")
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settle();app.autosave_enabled.button_pressed=false
	app.has_project.cache_root=folder.path_join("reader-cache" if "--read" in args else "writer-cache")
	if "--read" in args:
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
		app.has_project.open_file(packed);await jobs()
		check(app.has_project.path==packed and not app.dirty and app.world_selection.selected.is_empty(),"fresh packed Open restores scene without missing-file prompts or selection")
		# Both actual and oracle have each crossed one JSON parse, not two vs one.
		check(World.portable(app.renderer.world_state())==expected.world and app.keys==expected.camera,"fresh packed Open preserves exact native scene, both poses, camera and provenance")
		var rig=app.renderer.world_runtime.instance(expected.actor_id)
		check(rig!=null and rig.authored_keys().any(func(k):return int(k.frame)==0) and rig.authored_keys().any(func(k):return int(k.frame)==4),"both automatically authored frame0/frame4 poses survive a new process")
		for frame in [0,2,4]:
			var image: Image=await app.renderer.capture(app.keys,[],frame,true);image.save_png(folder.path_join("cold-%d.png" % frame))
			check(Storage.image_hash(image)==expected.pixels[str(frame)],"fresh packed frame%d exactly matches saved preview" % frame)
		var result:={"checks":checks,"failures":failures,"mode":"reader"};FileAccess.open(folder.path_join("reader.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("SCENARIO_A "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1);return
	# Script-driven app instances intentionally suppress normal startup recovery/Home.
	# Exercise its production Home entry; normal startup has a separate observer suite.
	app.home.open_home();await settle()
	check(app.home.visible and app.home.new_button.is_visible_in_tree() and app.home.tutorials_button.is_visible_in_tree(),"step1 Home exposes New and Tutorials with a bounded Recent area")
	app.home.new_button.pressed.emit();await settle()
	check(not app.home.visible and not app.advanced_mode and app.renderer.world_runtime.instances.is_empty() and app.world_selection.selected.is_empty() and app.video.world_background=="black" and app.renderer.editor_grid.visible and app.timeline.is_visible_in_tree(),"step2 Simple New opens black empty world with editor floor grid and timeline")
	var source: String=args[1];var original:=FileAccess.get_sha256(source)
	app.import_actions.drop(PackedStringArray([source]),app.canvas.get_global_rect().get_center());check(app.source_import.pid>0,"step3 native VRM drop starts ordinary asynchronous importer")
	await jobs()
	for child in app.get_children():
		if child is AcceptDialog and child.title=="Imported with limitations":child.confirmed.emit();child.hide()
	await settle()
	check(app.current_world().objects.size()==1,"step3 native worker adds exactly one model to the empty scene")
	if app.current_world().objects.size()!=1:app.free();quit(1);return
	var actor_id: String=app.current_world().objects[0].id;var rig=app.renderer.world_runtime.instance(actor_id)
	if app.physics_editor.active(actor_id):app.physics_editor.toggle.button_pressed=false;await settle()
	app.world_selection.select_entity(actor_id);app.world_selection.context_action(1);await settle();rig=app.renderer.world_runtime.instance(actor_id)
	var bounds: AABB=app.renderer.scene_bounds(rig.root);var center: Vector2=app.renderer.camera.unproject_position(bounds.get_center())
	print("SPAWN ",bounds," center=",center," placement=",rig.data.metadata.initial_placement)
	check(Rect2(0,0,1920,1080).has_point(center) and absf(bounds.position.y)<0.025,"step3 imported humanoid is visible near camera and grounded before manual framing")
	app.world_selection.clear();app.mode.select(1);app.change_mode(1);pointer(center,true);pointer(center,false);await settle()
	check(app.world_selection.selected==actor_id and app.world_selection.outline.visible,"step4 actual model click selects native actor and enables editor outline")
	app.world_selection.frame_selected();await settle()
	app.mode.select(2);app.change_mode(2);app.get_viewport().gui_release_focus();await settle()
	var alt:=InputEventKey.new();alt.keycode=KEY_ALT;alt.pressed=true;app._input(alt);await settle()
	check(app.pose_editor.reveal_bones and app.canvas.pose_joints.size()>20,"step4 actual Alt reveals native skeleton in Pose")
	var editor=app.pose_editor;var arm:="";var suffix: String=rig.data.metadata.native_parameters.humanoid.leftUpperArm.node_name
	for id in rig.order:
		if id.ends_with("::"+suffix):arm=id;break
	check(not arm.is_empty(),"step4 native humanoid upper-arm binding is available")
	if arm.is_empty():app.free();quit(1);return
	var joint: Vector2=app.renderer.camera.unproject_position(rig.bone_transform(arm).origin)
	editor.selected="@root";editor.update_gizmo();pointer(joint,true);pointer(joint,false);await settle()
	check(editor.selected==arm,"step4 viewport bone click selects exact native upper arm")
	alt.pressed=false;app._input(alt);editor.operation.select(0);editor.refresh_values();editor.update_gizmo()
	var camera_before: Array=app.keys.duplicate(true);var history: int=app.history.size()
	app.set_frame(0);await drag(editor,Vector2(35,-20));rig=app.renderer.world_runtime.instance(actor_id)
	check(rig.authored_keys().any(func(k):return int(k.frame)==0) and app.history.size()==history+1,"step5 first gizmo pose auto-keys frame0 in one edit without Record")
	app.set_frame(4);await drag(editor,Vector2(-50,20));rig=app.renderer.world_runtime.instance(actor_id)
	check(rig.authored_keys().any(func(k):return int(k.frame)==4) and app.history.size()==history+2 and app.keys==camera_before,"step5 second gizmo pose auto-keys frame4 without editing camera")
	var q0:=Timeline.quaternion(rig.sample(0)[arm].rotation_xyzw);var q2:=Timeline.quaternion(rig.sample(2)[arm].rotation_xyzw);var q4:=Timeline.quaternion(rig.sample(4)[arm].rotation_xyzw)
	print("POSE_ANGLES ",[q0.angle_to(q4),q2.angle_to(q0),q2.angle_to(q4)]," selected=",editor.selected," expected=",arm)
	check(q0.angle_to(q4)>0.05 and q2.angle_to(q0)>0.01 and q2.angle_to(q4)>0.01,"step6 intermediate native pose transitions between distinct authored endpoints")
	app.set_frame(0);app.toggle_play();await settle();check(app.playing,"step6 normal Play previews the authored animation");app.stop()
	var pixels:={}
	for frame in [0,2,4]:
		var image: Image=await app.renderer.capture(app.keys,[],frame,true);image.save_png(folder.path_join("preview-%d.png" % frame));pixels[str(frame)]=Storage.image_hash(image)
	check(pixels["0"]!=pixels["2"] and pixels["2"]!=pixels["4"],"step6 actual preview images show intermediate motion")
	app.has_project.save_file(packed,"packed");await jobs()
	check(app.has_project.path==packed and not app.dirty,"step7 normal baked HAS Save commits native model and animation")
	var expected:={"actor_id":actor_id,"world":World.portable(app.renderer.world_state()),"camera":app.keys,"pixels":pixels};FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify(expected,"",true,true))
	app.new_project();app.has_project.open_file(packed);await jobs()
	FileAccess.open(folder.path_join("actual-reopened.json"),FileAccess.WRITE).store_string(JSON.stringify({"world":World.portable(app.renderer.world_state()),"camera":app.keys},"",true,true))
	check(app.has_project.path==packed and World.portable(app.renderer.world_state())==normalized(expected.world) and app.keys==normalized(expected.camera),"step7 closing and reopening packed project preserves exact poses and native assets")
	app.video.duration_frames=24;app.set_frame(0);var error: String=await app.export_movie(folder)
	check(error.is_empty() and app.last_export_folder.get_base_dir()==folder and FileAccess.file_exists(app.last_finished_movie),"step8 normal MP4 export succeeds next to the packed project")
	check(Image.load_from_file(app.last_export_folder.path_join("frame_000003.png")).get_data()==Image.load_from_file(folder.path_join("preview-2.png")).get_data(),"step8 movie render input matches exact interpolated preview")
	check(FileAccess.get_sha256(source)==original,"all eight software steps preserve the native original")
	var result:={"checks":checks,"failures":failures,"mode":"writer","movie":app.last_finished_movie,"conversion_folder":app.source_import.folder,"source_sha256":original};FileAccess.open(folder.path_join("writer.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("SCENARIO_A "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
