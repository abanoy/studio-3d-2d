extends SceneTree
const Renderer=preload("res://src/renderer.gd")
const Timeline=preload("res://src/timeline.gd")
class PreviewProbe extends RefCounted:
	var starts:=0
	var dimensions:=Vector2i.ZERO
	var marker: String
	func busy() -> bool:return false
	func poll() -> Dictionary:return {}
	func finish() -> Dictionary:return {}
	func start(_folder: String,_digest: String,image: Image,_overlays: Array) -> String:
		starts+=1;dimensions=image.get_size()
		var file:=FileAccess.open(marker,FileAccess.WRITE);file.store_string("preview reached writer");file.close()
		return ""
var checks:=0
var failures:=0
var folder: String
var cases: Array=[]
var selected_cases:=PackedStringArray()
func _initialize() -> void:
	create_timer(90).timeout.connect(func():push_error("Native readback lifecycle watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settled() -> void:
	for i in range(5):await process_frame
	await RenderingServer.frame_post_draw
func connections() -> int:return RenderingServer.get_signal_connection_list("frame_post_draw").size()
func fresh_app(label: String,setup_view: bool):
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join(label+"-recovery");app.recent_path=folder.path_join(label+"-recent.json");app.display_prefs_path=folder.path_join(label+"-display.cfg")
	root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false
	app.mode.select(1);app.change_mode(1);app.scene_view.set_setup(setup_view,false);await settled()
	return app
func start_preview(app,probe: PreviewProbe) -> void:
	app.recovery_preview=probe
	app.finish_recovery_preview(app.recovery_root.path_join(app.recovery_session),"a".repeat(64),app.frame,app.recovery_revision,app.renderer.view_state())
func observe_capture(renderer,result: Dictionary) -> void:
	var image: Image=await renderer.capture([Timeline.key(0,Vector3(0,1,4),Quaternion.IDENTITY,60)],[],0,true)
	result["completed"]=true;result["no_image"]=image==null
func capture_then_close(app,result: Dictionary) -> void:
	var image: Image=await app.renderer.capture(app.keys,app.layers,app.frame,true)
	result["native_image"]=image!=null and image.get_size()==Vector2i(1920,1080)
	# No settle/deferred free here: the real caller may close as capture returns.
	app.free()
	result["completed"]=true
func run() -> void:
	folder=OS.get_cmdline_user_args()[0]
	for value in OS.get_cmdline_user_args().slice(1):selected_cases.append(value)
	# Positive control executes the shipped caller and real GPU image read before
	# the probe's detached writer boundary. No application method is replaced.
	var control=await fresh_app("control",true);var control_probe:=PreviewProbe.new();control_probe.marker=folder.path_join("control.marker")
	start_preview(control,control_probe)
	check(control.renderer.native_readbacks==1,"positive recovery enters the real pending native readback")
	await settled()
	check(control_probe.starts==1 and control_probe.dimensions==Vector2i(1920,1080) and control.renderer.native_readbacks==0,"positive control receives actual native GPU pixels and releases the readback counter")
	control.free();await settled()
	var nodes_before:=int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT))
	var orphans_before:=int(Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT))
	for setup_view in [false,true]:
		for closure in ["free","queue_free","remove_from_tree"]:
			var label: String=("setup-" if setup_view else "focus-")+closure
			if not selected_cases.is_empty() and label not in selected_cases:continue
			var app=await fresh_app(label,setup_view);var probe:=PreviewProbe.new();probe.marker=folder.path_join(label+".marker")
			var app_ref: WeakRef=weakref(app);var renderer_ref: WeakRef=weakref(app.renderer);var viewport_ref: WeakRef=weakref(app.renderer.viewport);var camera_ref: WeakRef=weakref(app.renderer.camera);var setup_ref: WeakRef=weakref(app.scene_view.viewport)
			var connected:=connections();start_preview(app,probe)
			check(app.renderer.native_readbacks==1,"%s begins before frame_post_draw rather than after a completed capture"%label)
			if closure=="free":app.free()
			elif closure=="queue_free":app.queue_free()
			else:root.remove_child(app)
			await settled()
			if closure=="remove_from_tree":
				check(is_instance_valid(app) and not app.is_inside_tree() and app.renderer.native_readbacks==0,"%s drains its readback while its live owner remains outside the tree"%label)
				app.free();await settled()
			check(app_ref.get_ref()==null and renderer_ref.get_ref()==null and viewport_ref.get_ref()==null and camera_ref.get_ref()==null and setup_ref.get_ref()==null,"%s releases application, both viewports, renderer and camera"%label)
			check(probe.starts==0 and not FileAccess.file_exists(probe.marker),"%s cannot hand obsolete pixels to the recovery writer"%label)
			check(connections()<=connected,"%s leaves no pending frame_post_draw connection"%label)
			check(int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT))==nodes_before and int(Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT))==orphans_before,"%s leaves no orphan or retained scene nodes"%label)
			cases.append({"case":label,"obsolete_writer_calls":probe.starts,"nodes":int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT)),"orphans":int(Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT)),"signal_connections":connections()})
	# Standalone renderer ownership uses the exact same shipped readback method,
	# without leaving a running application that would access a deleted renderer.
	for closure in ["free","queue_free"]:
		if not selected_cases.is_empty() and "renderer-"+closure not in selected_cases:continue
		var renderer:=Renderer.new();root.add_child(renderer);renderer.setup(320,180);await settled()
		var renderer_ref: WeakRef=weakref(renderer);var viewport_ref: WeakRef=weakref(renderer.viewport);var connected:=connections()
		if renderer.has_method("begin_native_readback"):renderer.call("begin_native_readback")
		else:renderer.call("readback_native")
		check(renderer.native_readbacks==1,"standalone %s renderer has a truly pending readback"%closure)
		if closure=="free":renderer.free()
		else:renderer.queue_free()
		await settled()
		check(renderer_ref.get_ref()==null and viewport_ref.get_ref()==null and connections()<=connected,"standalone %s releases its renderer, counter owner, viewport and pending await"%closure)
		check(int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT))==nodes_before and int(Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT))==orphans_before,"standalone %s leaves no orphan or retained scene nodes"%closure)
		cases.append({"case":"renderer-"+closure,"nodes":int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT)),"orphans":int(Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT)),"signal_connections":connections()})
	for closure in ["free","queue_free","remove_from_tree"]:
		if not selected_cases.is_empty() and "capture-"+closure not in selected_cases:continue
		var renderer:=Renderer.new();root.add_child(renderer);renderer.setup(320,180);await settled()
		var renderer_ref: WeakRef=weakref(renderer);var viewport_ref: WeakRef=weakref(renderer.viewport);var connected:=connections()
		var result:={"completed":false,"no_image":false}
		if closure=="remove_from_tree":observe_capture(renderer,result)
		else:renderer.capture([Timeline.key(0,Vector3(0,1,4),Quaternion.IDENTITY,60)],[],0,true)
		check(renderer.native_readbacks==1 and renderer.capturing_final,"capture %s starts an actual final capture before frame_post_draw"%closure)
		if closure=="free":renderer.free()
		elif closure=="queue_free":renderer.queue_free()
		else:root.remove_child(renderer)
		await settled()
		if closure=="remove_from_tree":
			check(result.completed and result.no_image and renderer.native_readbacks==0 and not renderer.capturing_final and not renderer.last_capture_error.is_empty(),"detached live renderer completes an aborted capture with no image and no retained scope")
			renderer.free();await settled()
		check(renderer_ref.get_ref()==null and viewport_ref.get_ref()==null and connections()<=connected,"capture %s releases its renderer, counter owner, viewport and pending await"%closure)
		check(int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT))==nodes_before and int(Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT))==orphans_before,"capture %s leaves no orphan or retained scene nodes"%closure)
		cases.append({"case":"capture-"+closure,"nodes":int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT)),"orphans":int(Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT)),"signal_connections":connections()})
	for setup_view in [false,true]:
		var label: String="capture-close-app-"+("setup" if setup_view else "focus")
		if not selected_cases.is_empty() and label not in selected_cases:continue
		var app=await fresh_app(label,setup_view);var app_ref: WeakRef=weakref(app);var renderer_ref: WeakRef=weakref(app.renderer);var viewport_ref: WeakRef=weakref(app.renderer.viewport);var connected:=connections()
		var result:={"completed":false,"native_image":false}
		capture_then_close(app,result)
		check(app.renderer.native_readbacks==1,"%s begins an actual pending final capture"%label)
		await settled()
		check(result.completed and result.native_image,"%s returns native pixels and frees the application immediately without a settle"%label)
		check(app_ref.get_ref()==null and renderer_ref.get_ref()==null and viewport_ref.get_ref()==null and connections()<=connected,"%s releases the application, renderer, viewport and notification"%label)
		check(int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT))==nodes_before and int(Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT))==orphans_before,"%s leaves no orphan or retained scene nodes"%label)
		cases.append({"case":label,"nodes":int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT)),"orphans":int(Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT)),"signal_connections":connections()})
	var report:={"checks":checks,"failures":failures,"cases":cases,"positive_native_size":str(control_probe.dimensions),"initial_nodes":nodes_before,"initial_orphans":orphans_before}
	var file:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(report,"",true,true));file.close()
	print("NATIVE_READBACK_LIFECYCLE "+JSON.stringify(report));quit(0 if failures==0 else 1)
