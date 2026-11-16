extends SceneTree
const SceneIO=preload("res://src/scene3d.gd")
const Support=preload("res://tests/world_test_support.gd")
const Timeline=preload("res://src/timeline.gd")
var checks:=0
var failures:=0
var folder: String
var cases: Array=[]
var requested:=PackedStringArray()
var reentrant_app: WeakRef
var reentrant_point:=Vector2.ZERO
var reentrant_observed: Dictionary={}

func _initialize() -> void:
	create_timer(90).timeout.connect(func():push_error("World selection teardown watchdog");quit(2))
	call_deferred("run")

func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1

func settled() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw

func connections() -> int:
	return RenderingServer.get_signal_connection_list("frame_post_draw").size()

func fresh_app(label: String,setup_view: bool):
	var app=load("res://main.tscn").instantiate()
	app.recovery_root=folder.path_join(label+"-recovery")
	app.recent_path=folder.path_join(label+"-recent.json")
	app.display_prefs_path=folder.path_join(label+"-display.cfg")
	root.add_child(app);await settled()
	app.home.hide();app.autosave_enabled.button_pressed=false
	app.mode.select(1);app.change_mode(1);app.scene_view.set_setup(setup_view,false)
	await settled()
	return app

func enqueue_reentrant_pick() -> void:
	var app=reentrant_app.get_ref()
	if app:app.world_selection.choose_at(reentrant_point)

func observe_reentrant_pick() -> void:
	var app=reentrant_app.get_ref()
	if app:
		reentrant_observed={"picking":app.world_selection.picking,"selected":app.world_selection.selected}

func controls() -> void:
	var app=await fresh_app("controls",false)
	var selection=app.world_selection
	var fixture:=folder.path_join("selection-control.glb")
	check(SceneIO.make_pose_fixture(fixture)==OK,"control creates its own deterministic pose fixture")
	app.pose_editor.add_model(fixture);await settled();app.pose_editor.frame_model()
	var model_id: String=Support.key(app,Support.rig(app))
	app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,app.renderer.camera.fov)]
	app.mode.select(1);app.change_mode(1);selection.select_entity("",false);await settled()
	var point: Vector2=app.renderer.camera.unproject_position(Vector3(.8,1,0))
	var empty:=Vector2(10,10)
	var connected:=connections()
	var source_hash:=FileAccess.get_sha256(fixture)
	var camera_before:=var_to_str(app.renderer.camera.transform)
	var keys_before:=JSON.stringify(app.keys)
	selection.choose_at(point)
	check(selection.picking>0 and connections()>connected,"control enters a genuine pending GPU pick before a draw")
	await settled()
	check(selection.selected==model_id and selection.picking==0 and connections()==connected,"real draw selects the independently known fixture and releases its pending pick")
	check(var_to_str(app.renderer.camera.transform)==camera_before and JSON.stringify(app.keys)==keys_before,"completed pick preserves the camera and authored keys")
	selection.choose_at(point);selection.choose_at(empty)
	check(selection.picking>0,"multiple same-frame requests really remain pending")
	await settled()
	check(selection.selected.is_empty() and selection.picking==0 and connections()==connected,"last same-frame request wins without retaining earlier requests")
	selection.select_entity(model_id,false);selection.choose_at(empty);selection.cancel_gesture(true)
	await settled()
	check(selection.selected==model_id and selection.picking==0 and connections()==connected,"canceling a pending request preserves the previous selection")
	# This listener precedes the old request in the draw signal's snapshot. A
	# request it creates must wait for the next draw, not the old request's draw.
	reentrant_app=weakref(app);reentrant_point=empty;reentrant_observed={}
	RenderingServer.frame_post_draw.connect(enqueue_reentrant_pick,CONNECT_ONE_SHOT)
	selection.choose_at(point)
	RenderingServer.frame_post_draw.connect(observe_reentrant_pick,CONNECT_ONE_SHOT)
	await RenderingServer.frame_post_draw
	check(reentrant_observed.get("picking",0)==1 and reentrant_observed.get("selected","")==model_id,"pick enqueued by an earlier draw listener waits beyond that same draw")
	await RenderingServer.frame_post_draw
	check(selection.picking==0 and selection.selected.is_empty() and connections()==connected,"reentrant request completes on the next draw and releases its frame wait")
	reentrant_app=null;reentrant_observed={}
	selection.choose_at(point)
	check(selection.picking>0,"document replacement begins with an actual pending old-world pick")
	check(app.new_project(),"normal New replaces the old world while its pick is pending")
	var new_world:=JSON.stringify(app.current_world())
	var new_keys:=JSON.stringify(app.keys)
	var new_camera:=var_to_str(app.renderer.camera.transform)
	var new_history: int=app.history.size();var new_dirty: bool=app.dirty
	await settled()
	check(selection.selected.is_empty() and selection.picking==0 and JSON.stringify(app.current_world())==new_world and JSON.stringify(app.keys)==new_keys and var_to_str(app.renderer.camera.transform)==new_camera and app.history.size()==new_history and app.dirty==new_dirty,"obsolete pick cannot select old geometry or alter the new document")
	check(FileAccess.get_sha256(fixture)==source_hash,"picking and document replacement leave original fixture bytes unchanged")
	var app_ref: WeakRef=weakref(app);var selection_ref: WeakRef=weakref(selection);var viewport_ref: WeakRef=weakref(selection.viewport)
	for i in range(3):selection.choose_at(Vector2(960,540))
	check(selection.picking>0 and connections()>connected,"queued close starts with multiple genuinely pending picks")
	app.queue_free()
	await settled()
	check(app_ref.get_ref()==null and selection_ref.get_ref()==null and viewport_ref.get_ref()==null and connections()==connected,"queued close releases its application, selection viewport and all frame waits")
	cases.append({"case":"controls-queue-free","signal_connections":connections(),"reentrant_pending_after_first_draw":1})

func closure_case(label: String,setup_view: bool,detach: bool) -> void:
	var nodes_before:=int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT))
	var orphans_before:=int(Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT))
	var app=await fresh_app(label,setup_view)
	var selection=app.world_selection
	var app_ref: WeakRef=weakref(app);var selection_ref: WeakRef=weakref(selection)
	var viewport_ref: WeakRef=weakref(selection.viewport);var camera_ref: WeakRef=weakref(selection.camera)
	var renderer_ref: WeakRef=weakref(app.renderer);var native_ref: WeakRef=weakref(app.renderer.viewport);var setup_ref: WeakRef=weakref(app.scene_view.viewport)
	var connected:=connections()
	selection.choose_at(Vector2(960,540))
	check(selection.picking>0 and connections()>connected,"%s begins a real pending pick before any draw"%label)
	# No await/deferred free between the pending request and this operation.
	if detach:
		root.remove_child(app)
		check(is_instance_valid(app) and not app.is_inside_tree() and selection.picking==0 and connections()==connected,"detaching a live owner immediately releases its pending pick and draw callback")
	else:
		app.free()
		check(app_ref.get_ref()==null and selection_ref.get_ref()==null and connections()==connected,"%s immediately releases receiver and callback without another frame"%label)
	await settled()
	if detach:
		check(selection.picking==0 and selection.selected.is_empty() and connections()==connected,"detached owner cannot apply a stale pick on a later draw")
		app.free();await settled()
	check(app_ref.get_ref()==null and selection_ref.get_ref()==null and viewport_ref.get_ref()==null and camera_ref.get_ref()==null and renderer_ref.get_ref()==null and native_ref.get_ref()==null and setup_ref.get_ref()==null,"%s releases selection, application and both scene views"%label)
	check(connections()==connected and int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT))==nodes_before and int(Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT))==orphans_before,"%s leaves no frame connection, retained Node or orphan"%label)
	cases.append({"case":label,"signal_connections":connections(),"nodes":int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT)),"orphans":int(Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT))})

func run() -> void:
	folder=OS.get_cmdline_user_args()[0]
	for name in OS.get_cmdline_user_args().slice(1):requested.append(name)
	if requested.is_empty() or "controls-queue-free" in requested:await controls()
	for config in [["focus-free",false,false],["setup-free",true,false],["focus-detach",false,true]]:
		if requested.is_empty() or config[0] in requested:await closure_case(config[0],config[1],config[2])
	var report:={"checks":checks,"failures":failures,"cases":cases}
	var file:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify(report,"",true,true));file.close()
	print("WORLD_SELECTION_TEARDOWN "+JSON.stringify(report))
	quit(0 if failures==0 else 1)
