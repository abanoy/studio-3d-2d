extends SceneTree
const Hold=preload("res://src/foot_hold.gd")
const Support=preload("res://tests/world_test_support.gd")
const World=preload("res://src/world_document.gd")
const Storage=preload("res://src/storage.gd")
const Timeline=preload("res://src/timeline.gd")
const Drawing=preload("res://src/drawing.gd")
var checks:=0
var failures:=0
var app
var editor
var folder: String

func _initialize() -> void:
	create_timer(130).timeout.connect(func():push_error("Foot hold watchdog");quit(2))
	call_deferred("run")
func check(ok: bool, message: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+message)
	if not ok:failures+=1
func settled() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func wait_job() -> void:
	while app.has_project.pid>0:await process_frame
	await settled()
func error_of(rig, captured: Dictionary) -> float:
	var error:=0.
	for foot in captured.feet:error=maxf(error,rig.bone_transform(foot.limb.ids[2]).origin.distance_to(foot.position))
	return error
func move(axis: int, amount: float, cancel:=false) -> void:
	editor.update_gizmo();var handle: Dictionary=editor.handles[axis]
	var point: Vector2=handle.points[0].lerp(handle.points[-1],.7)
	var press:=InputEventMouseButton.new();press.button_index=MOUSE_BUTTON_LEFT;press.pressed=true;editor.input(press,point)
	check(editor.dragging,"body gizmo begins an actual drag")
	var motion:=InputEventMouseMotion.new();editor.input(motion,point+editor.drag_screen_axis.normalized()*amount/editor.drag_units*editor.drag_pixels)
	editor.finish_drag(cancel);await settled()
func numeric(axis: int, amount: float) -> void:
	editor.refresh_values();editor.fields[axis].value+=amount;editor.apply_numeric()

func run() -> void:
	folder=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder)
	var asset:=folder.path_join("figure.glb");check(preload("res://src/tutorial_assets.gd").figure(asset)==OK,"original two-leg skin fixture created")
	var digest:=FileAccess.get_sha256(asset)
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled()
	app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache");app.home.hide();editor=app.pose_editor
	editor.add_model(asset);var rig: RefCounted=editor.active_rig();var id: String=rig.data.id
	check(not editor.hold_feet.button_pressed and not app.advanced_mode,"Simple exposes opt-in hold feet, initially off")
	editor.frame_model();app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,60)]
	editor.record_key();app.set_frame(12);editor.selected="@root";editor.operation.select(1);editor.space.select(1);editor.refresh_values()
	var pins:=Hold.capture(rig,"@root");check(not pins.has("error") and pins.feet.size()==2,"both validated leg endpoints captured")
	var before: Dictionary=rig.data.duplicate(true);var shots: Array=app.keys.duplicate(true);var view: Dictionary=app.renderer.view_state();var count: int=app.history.size()
	editor.hold_feet.button_pressed=true;await move(1,-.2)
	check(absf(rig.sample_transform(12).position[1]+.2)<.001 and error_of(rig,pins)<.0002,"crouch moves body while both feet stay at original world positions")
	check(rig.authored_keys().size()==2 and app.history.size()==count+1,"one completed crouch auto-keys body and legs in one Undo")
	var crouched: Dictionary=rig.data.duplicate(true)
	root.get_texture().get_image().save_png(folder.path_join("crouched-editor.png"))
	var old_size:=root.size;root.size=Vector2i(1200,800);await settled()
	check(root.size.x==1200 and editor.hold_feet.get_global_rect().end.x<=app.size.x and app.canvas.size.x>=500,"hold-feet control fits Simple workspace at 1200 pixels")
	root.get_texture().get_image().save_png(folder.path_join("crouched-1200.png"));root.size=old_size;await settled()
	app.undo();check(rig.data==before,"Undo restores exact pre-crouch data")
	app.redo();check(rig.data==crouched and error_of(rig,pins)<.0002,"Redo replays saved FK without live solving")
	await move(0,.06,true);check(rig.data==crouched and app.history.size()==count+1,"cancelled body drag restores all leg/body keys")
	numeric(1,10);check(rig.data==crouched and app.history.size()==count+1 and "reach" in app.status.text,"unreachable numeric body move rejects atomically")
	numeric(0,.04);check(error_of(rig,pins)<.0002 and rig.data!=crouched,"numeric body edit also holds both feet")
	app.undo();check(rig.data==crouched,"numeric held move is one Undo")
	var hips: String=rig.order[0];editor.tree_items[hips].select(0);editor.refresh_values();numeric(1,-.1)
	check(error_of(rig,pins)<.0002 and rig.data!=crouched,"common pelvis ancestor can move without translating feet")
	app.undo();editor.tree_items["@root"].select(0);editor.refresh_values()
	await move(0,0);check(rig.data==crouched,"zero-distance gesture creates no draft/key/history change")
	var skeleton: Skeleton3D=rig.bones[pins.feet[0].limb.ids[0]].skeleton;var scale_before:=skeleton.scale;skeleton.scale=Vector3(1.1,1,1)
	numeric(1,-.1);check(rig.data==crouched and "uniform" in app.status.text,"unsupported bone scale keeps the whole body/leg edit unchanged")
	skeleton.scale=scale_before;editor.apply_frame()
	app.physics_editor.toggle.button_pressed=true;await settled();var live_before: Dictionary=rig.data.duplicate(true)
	numeric(1,-.1);check(app.physics_editor.is_running() and rig.data==live_before and "off" in app.status.text,"holding feet refuses live simulation without freezing it or adding keys")
	app.physics_editor.clear();rig.data=crouched.duplicate(true);editor.apply_frame();await settled()
	check(app.keys==shots and app.renderer.view_state()==view,"foot authoring preserves shot keys and temporary view")
	# Sparse solved FK endpoints do not imply a continuous world-space contact lock.
	app.set_frame(6);var midpoint_error:=error_of(rig,pins)
	check(midpoint_error>.0005,"explicit negative evidence: sparse FK interpolation can still slide between held endpoints")
	app.set_frame(12);editor.hold_feet.button_pressed=false;numeric(0,.1)
	check(error_of(rig,pins)>.05,"turning hold off restores direct root movement")
	app.undo();editor.hold_feet.button_pressed=true
	app.mode.select(0);app.change_mode(0);app.create_cel(false);Drawing.stroke(Drawing.image(Drawing.cel_at(app.layers[1],12)),Vector2(70,70),Vector2(170,70),4,Color.CYAN,false);app.changed()
	var paint: PackedByteArray=Drawing.image(Drawing.cel_at(app.layers[1],12)).get_data()
	var packed:=folder.path_join("held-feet.has");app.has_project.save_file(packed,"packed");await wait_job()
	app.new_project();app.has_project.open_file(packed);await wait_job();rig=app.renderer.world_runtime.instance(id)
	check(rig!=null and error_of(rig,pins)<.0002 and Drawing.image(Drawing.cel_at(app.layers[1],12)).get_data()==paint,"ordinary packed HAS restores solved keys and independent editable paint")
	app.set_frame(12);var preview: Image=await app.renderer.capture(app.keys,app.layers,12,true)
	var export_error: String=await app.export_movie(folder)
	check(export_error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000013.png")).get_data()==preview.get_data(),"MP4 frame matches reopened posed scene and drawing exactly")
	var movie: String=app.last_export_folder.path_join("movie.mp4")
	# A rotated, uniformly scaled parent is not the foot contact coordinate system.
	var empty:=folder.path_join("empty.glb");preload("res://src/scene3d.gd").make_empty(empty)
	var group:=World.object(empty,"group","Parent");group.id="parent";group.scale=1.5
	var q:=Quaternion.from_euler(Vector3(.1,.6,.15));group.rotation_xyzw=[q.x,q.y,q.z,q.w]
	var child:=World.object(asset);child.id="child";child.parent_id=group.id;child.scale=.8
	var grouped:=World.empty();grouped.objects=[group,child];app.new_project();app.restore_world(grouped);app.world_selection.select_entity(child.id);rig=editor.active_rig();editor.selected="@root";editor.operation.select(1);editor.space.select(1);editor.hold_feet.button_pressed=true;editor.frame_model();await settled()
	var grouped_pins:=Hold.capture(rig,"@root");var parent_before: Dictionary=app.renderer.world_runtime.instance(group.id).data.duplicate(true)
	await move(1,-.1);check(error_of(rig,grouped_pins)<.0002 and app.renderer.world_runtime.instance(group.id).data==parent_before,"world-space held feet work through rotated/scaled parent without editing the group")
	# Native imports share the same authoring path, including Source's root correction.
	var natives:=[];var errors:={}
	for sample in ["pose-smoke/miku-project","source-smoke/source-project","sfm-smoke/project"]:
		var path:=ProjectSettings.globalize_path("res://output/"+sample)
		if not FileAccess.file_exists(path.path_join("project.json")):print("SKIP private native "+sample);continue
		var loaded:=Storage.load_project(path);var row:=Support.legacy_model(World.from_project(loaded).objects[-1]);row.id="held-native";row.parent_id="";row.start_frame=0;row.pose_keys=[];row.pose={};row.draft_frame=0
		var world:=World.empty();world.objects=[row];app.new_project();app.restore_world(world);app.world_selection.select_entity(row.id);rig=editor.active_rig()
		var original:=FileAccess.get_sha256(row.source);var metadata: Dictionary=rig.data.metadata.duplicate(true)
		editor.frame_model();editor.record_key();app.set_frame(12);editor.selected="@root";editor.operation.select(1);editor.refresh_values();editor.hold_feet.button_pressed=true
		var captured:=Hold.capture(rig,"@root");check(not captured.has("error"),"native legs recognized: "+sample)
		if captured.has("error"):continue
		var a: Vector3=rig.bone_transform(captured.feet[0].limb.ids[0]).origin;var b: Vector3=captured.feet[0].position
		var down: Vector3=(b-a).normalized()*.03
		var local: Vector3=rig.root.get_parent().global_basis.inverse()*down
		var prior: Dictionary=rig.data.duplicate(true)
		editor.refresh_values()
		for i in range(3):editor.fields[i].value+=local[i]
		editor.apply_numeric();errors[sample]=error_of(rig,captured)
		check(rig.data!=prior and error_of(rig,captured)<.0002,"native body edit holds both feet: "+sample)
		app.undo();check(rig.data==prior and rig.data.metadata==metadata and FileAccess.get_sha256(row.source)==original,"native exact Undo, metadata and source preservation: "+sample)
		natives.append(sample)
	var vrms:=[]
	for name in ["AvatarSample_A.vrm","AvatarSample_Avrm0.vrm"]:
		var path: String=preload("res://tests/native_sample_paths.gd").vrm(name)
		if not FileAccess.file_exists(path):print("SKIP private VRM "+name);continue
		var sha:=FileAccess.get_sha256(path);app.new_project();editor.add_model(path)
		while app.source_import.pid>0:await process_frame
		for child_node in app.get_children():
			if child_node is AcceptDialog and child_node.title=="Imported with limitations":child_node.hide();child_node.queue_free()
		await settled();rig=editor.active_rig();check(rig!=null,"native VRM worker completes: "+name)
		if not rig:continue
		editor.record_key();app.set_frame(12);editor.selected="@root";editor.operation.select(1);editor.refresh_values();editor.hold_feet.button_pressed=true
		var captured:=Hold.capture(rig,"@root");check(not captured.has("error") and captured.feet[0].limb.declared,"declared humanoid feet recognized: "+name)
		if captured.has("error"):continue
		var prior: Dictionary=rig.data.duplicate(true);numeric(1,-.03)
		check(rig.data!=prior and error_of(rig,captured)<.0002 and FileAccess.get_sha256(path)==sha,"VRM body crouch holds both feet with original bytes intact: "+name)
		app.undo();check(rig.data==prior,"VRM held pose Undo restores complete original data: "+name)
		vrms.append(name)
	check(FileAccess.get_sha256(asset)==digest,"original skin source bytes stay unchanged")
	root.get_texture().get_image().save_png(folder.path_join("foot-hold.png"))
	app.free();await settled()
	print("FOOT_HOLD_SMOKE "+JSON.stringify({"checks":checks,"failures":failures,"folder":folder,"movie":movie,"native_projects":natives,"native_errors":errors,"vrm_samples":vrms,"midpoint_sliding":midpoint_error}));quit(0 if failures==0 else 1)
