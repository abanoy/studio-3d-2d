extends "res://tests/wind_review_gpu_common.gd"
class PreviewProbe extends RefCounted:
	var starts:=0
	var image: Image
	var overlays: Array=[]
	func busy() -> bool:return false
	func poll() -> Dictionary:return {}
	func finish() -> Dictionary:return {}
	func start(_folder: String,_digest: String,pixels: Image,layers: Array) -> String:
		starts+=1;image=pixels.duplicate();overlays=layers.duplicate();return ""

func prepare(label: String) -> bool:
	await fresh_app(label)
	var source: RefCounted=await add_source(source_path())
	if source==null:return false
	await add_media()
	return true

func capture_into(result: Dictionary) -> void:
	result.image=await native_image(true);result.done=true

func export_into(result: Dictionary) -> void:
	result.error=await app.export_frames(folder,true,false);result.done=true

func hidden_now(reference: WeakRef) -> bool:
	var node=reference.get_ref()
	return node==null or not node.visible and node.is_queued_for_deletion()

func endpoint_cases() -> void:
	for running in [false,true]:
		for action in ["save","record","export","play","seek","source","close"]:
			var label: String=("running-" if running else "warming-")+action
			if not await prepare(label):return
			var before:=document_state();var expected: Image=await native_image(true)
			if not await open_review() or not await begin_review(running):return
			var review=app.local_wind_review;var candidate: WeakRef=weakref(review.candidate.root)
			check(document_matches(before),label+" has not edited the document before its normal operation")
			var job:={"done":false,"error":""}
			match action:
				"save":app.has_project.save_file(folder.path_join(label+".has"),"packed")
				"record":check(not app.physics_editor.recording.start(),"no-physics Record retains its normal refusal after cancelling the try-out")
				"export":export_into(job)
				"play":app.toggle_play()
				"seek":app.set_frame(app.frame+1)
				"source":app.new_project()
				"close":review.window.close_requested.emit()
			check(review.phase=="stopped" and review.candidate==null and hidden_now(candidate),label+" hides and releases the candidate synchronously")
			check(not RenderingServer.frame_post_draw.is_connected(review.warm_frame),label+" removes its warm-up callback immediately")
			if action=="save":
				await wait_job(app.has_project)
				check(FileAccess.file_exists(folder.path_join(label+".has")) and app.has_project.path==folder.path_join(label+".has"),label+" completes a real packed save")
			elif action=="export":
				while not job.done:await process_frame
				var first:=Image.load_from_file(app.last_export_folder.path_join("frame_000001.png"))
				check(job.error.is_empty() and changed_bytes(first,expected)==0,label+" exports original native pixels without the temporary try-out")
				metrics[label+"-frames"]=app.last_export_folder
			elif action=="play":app.stop()
			await settled()
			if action!="source":check(document_matches(before,false),label+" preserves authored world, shot keys, paint, audio and history")
			else:check(app.current_world().objects.is_empty(),label+" retains the intended New-project result")
			check(app.renderer.native_readbacks==0 and not app.local_wind_active(),label+" leaves no preview or native-readback scope")
			app.free();app=null;await settled()

func mouse_button(index: int,pressed: bool,ctrl: bool,point: Vector2) -> void:
	var event:=InputEventMouseButton.new();event.button_index=index;event.pressed=pressed;event.ctrl_pressed=ctrl;event.position=point;event.global_position=point
	root.push_input(event,true)

func physical_key(code: int,pressed: bool) -> void:
	var event:=InputEventKey.new();event.keycode=code;event.physical_keycode=code;event.pressed=pressed
	Input.parse_input_event(event);Input.flush_buffered_events()

func navigation_cases() -> void:
	if not await prepare("navigation") or not await open_review():return
	var before:=document_state();var original_view: Dictionary=app.renderer.view_state();var review=app.local_wind_review
	var returned: Array=[];app.camera_cursor_return_requested.connect(func(point: Vector2):returned.append(point))
	for spec in [{"name":"LMB","button":MOUSE_BUTTON_LEFT,"ctrl":false,"scheme":"fly"},{"name":"Ctrl LMB","button":MOUSE_BUTTON_LEFT,"ctrl":true,"scheme":"fly"},{"name":"RMB","button":MOUSE_BUTTON_RIGHT,"ctrl":false,"scheme":"fly"},{"name":"middle","button":MOUSE_BUTTON_MIDDLE,"ctrl":false,"scheme":"fly"},{"name":"orbit","button":MOUSE_BUTTON_LEFT,"ctrl":true,"scheme":"orbit"}]:
		if not is_instance_valid(review.window):
			if not await open_review():return
		if not await begin_review():return
		app.navigation_scheme=spec.scheme;app.get_window().grab_focus();await settled()
		var point: Vector2=app.canvas.global_position+app.canvas.scene_rect().get_center()
		physical_key(KEY_CTRL,spec.ctrl);mouse_button(spec.button,true,spec.ctrl,point)
		var motion:=InputEventMouseMotion.new();motion.position=point+Vector2(12,7);motion.relative=Vector2(12,7);motion.button_mask=1<<(int(spec.button)-1);motion.ctrl_pressed=spec.ctrl;root.push_input(motion,true)
		check(app.navigating,"actual canvas input enters "+str(spec.name)+" navigation")
		var cursor: Vector2=app.camera_cursor_origin;var count:=returned.size()
		if spec.scheme=="fly":
			physical_key(KEY_W,true)
			physical_key(KEY_CTRL,false);var start: Vector3=app.renderer.camera.position;app._process(1./60.);var normal:=start.distance_to(app.renderer.camera.position)
			physical_key(KEY_CTRL,true);start=app.renderer.camera.position;app._process(1./60.);var slow:=start.distance_to(app.renderer.camera.position)
			physical_key(KEY_CTRL,false);start=app.renderer.camera.position;app._process(1./60.);var resumed:=start.distance_to(app.renderer.camera.position)
			check(normal>.04 and absf(slow*4-normal)<.001 and absf(resumed-normal)<.001,"physical WASD state uses Ctrl slow movement and resumes during "+str(spec.name))
		var escape:=InputEventKey.new();escape.keycode=KEY_ESCAPE;escape.pressed=true;root.push_input(escape,true)
		check(not app.navigating and app.camera_buttons==0 and not app.orbit_control.active and not app.canvas.panning and app.canvas.middle_pending.is_empty(),"routed Escape clears "+str(spec.name)+" navigation and middle state")
		check(returned.size()==count+1 and returned[-1]==cursor.clamp(Vector2.ZERO,app.get_viewport_rect().size-Vector2.ONE),"Escape requests the pre-navigation cursor exactly once for "+str(spec.name))
		var stopped: Vector3=app.renderer.camera.position;app._process(1./60.)
		check(app.renderer.camera.position==stopped,"still-held WASD cannot move after "+str(spec.name)+" Escape")
		physical_key(KEY_W,false);physical_key(KEY_CTRL,false);app.renderer.restore_view(original_view)
		if not is_instance_valid(review.window):
			if not await open_review():return
		if not await begin_review():return
		app.navigation_scheme="fly";mouse_button(spec.button,true,false,point)
		motion.position=point+Vector2(14,0);motion.relative=Vector2(14,0);motion.ctrl_pressed=false;root.push_input(motion,true)
		mouse_button(spec.button,false,false,Vector2(-80,-80))
		check(not app.navigating and not review.pointer_pending,"off-canvas release ends "+str(spec.name)+" capture")
		review.stop_preview();app.release_mouse();app.renderer.restore_view(original_view)
	# Escape must also release navigation when the window is already stopped.
	app.get_window().grab_focus();await settled();physical_key(KEY_CTRL,true)
	var point: Vector2=app.canvas.global_position+app.canvas.scene_rect().get_center()
	mouse_button(MOUSE_BUTTON_LEFT,true,true,point)
	var escape:=InputEventKey.new();escape.keycode=KEY_ESCAPE;escape.pressed=true;root.push_input(escape,true)
	check(not is_instance_valid(review.window) and not app.navigating and app.camera_buttons==0,"Escape closes the stopped review and releases a new camera gesture")
	physical_key(KEY_CTRL,false);app.renderer.restore_view(original_view)
	check(document_matches(before),"navigation tests preserve authored world, camera keys, paint, audio and history")
	app.free();app=null;await settled()

func readback_cases() -> void:
	for setup_view in [true,false]:
		if not await prepare("readback-"+str(setup_view)):return
		app.scene_view.set_setup(setup_view,false);await settled()
		var before:=document_state();var expected: Image=await native_image(true);var background: Image=await native_image(true,false)
		if not await open_review() or not await begin_review():return
		var review=app.local_wind_review;var result:={"done":false,"image":null}
		capture_into(result)
		check(app.renderer.capturing_final and app.renderer.native_readbacks==1 and review.phase=="stopped","real final capture cancels the try-out and owns a pending native frame")
		review.master.button_pressed=true
		check(review.phase=="stopped" and review.candidate==null,"actual open-window master cannot restart during pending final capture")
		while not result.done:await process_frame
		check(changed_bytes(result.image,expected)==0 and app.renderer.native_readbacks==0,"pending final capture returns original exact pixels and drains its scope")
		await settled()
		if not is_instance_valid(review.window):
			if not await open_review():return
		var probe:=PreviewProbe.new();app.recovery_preview=probe
		# This callback is deliberately connected before native-frame dispatch.
		RenderingServer.frame_post_draw.connect(func():review.stop_preview("post-draw stop"),CONNECT_ONE_SHOT)
		app.finish_recovery_preview(app.recovery_root.path_join(app.recovery_session),"obsolete",app.frame,app.recovery_revision,app.renderer.view_state())
		check(app.renderer.native_readbacks==1,"actual recovery request is pending before a new try-out starts")
		if not await begin_review(false):return
		await settled()
		check(probe.starts==0 and app.renderer.native_readbacks==0,"start then post-draw stop rejects obsolete GPU recovery pixels and releases the counter")
		app.finish_recovery_preview(app.recovery_root.path_join(app.recovery_session),"fresh",app.frame,app.recovery_revision,app.renderer.view_state());await settled()
		check(probe.starts==1 and changed_bytes(probe.image,background)==0 and app.renderer.native_readbacks==0,"fresh recovery after stop receives original exact native background pixels")
		check(document_matches(before),"capture and recovery interleavings leave the authored scene and media unchanged")
		app.free();app=null;await settled()

func immediate_close_cases() -> void:
	for running in [false,true]:
		for setup_view in [true,false]:
			var nodes:=int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT));var orphans:=int(Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT));var connections:=RenderingServer.get_signal_connection_list("frame_post_draw").size()
			if not await prepare("close-"+str(running)+"-"+str(setup_view)):return
			app.scene_view.set_setup(setup_view,false)
			if not await open_review() or not await begin_review(running):return
			var app_ref: WeakRef=weakref(app);var candidate_ref: WeakRef=weakref(app.local_wind_review.candidate.root);var space_ref: WeakRef=weakref(app.local_wind_review.private_space)
			app.free();app=null;await settled(8)
			check(app_ref.get_ref()==null and candidate_ref.get_ref()==null and space_ref.get_ref()==null,"immediate close reclaims application, temporary model and private space")
			check(RenderingServer.get_signal_connection_list("frame_post_draw").size()<=connections and int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT))==nodes and int(Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT))==orphans,"immediate warming/running close retains no frame callbacks or orphan nodes")

func dormant_canvas_close_case() -> void:
	var nodes:=int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT));var orphans:=int(Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT));var connections:=RenderingServer.get_signal_connection_list("frame_post_draw").size()
	await fresh_app("dormant-canvas-first")
	var app_ref: WeakRef=weakref(app);var review_ref: WeakRef=weakref(app.local_wind_review)
	check(app.local_wind_review.phase=="stopped" and app.local_wind_review.candidate==null and not is_instance_valid(app.local_wind_review.window),"canvas-first close starts with a dormant review and no temporary candidate")
	app.canvas.free();app.free();app=null;await settled(8)
	check(app_ref.get_ref()==null and review_ref.get_ref()==null,"canvas-first close reclaims the dormant review without redrawing disposed controls")
	check(RenderingServer.get_signal_connection_list("frame_post_draw").size()<=connections and int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT))==nodes and int(Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT))==orphans,"canvas-first close leaves no frame callbacks, retained nodes or orphans")

func run() -> void:
	setup_request()
	if "--dormant-canvas-close-only" in OS.get_cmdline_user_args():
		await dormant_canvas_close_case();await finish("WIND_REVIEW_GPU_LIFECYCLE");return
	await endpoint_cases()
	if failures>0:await finish("WIND_REVIEW_GPU_LIFECYCLE");return
	await navigation_cases()
	if failures>0:await finish("WIND_REVIEW_GPU_LIFECYCLE");return
	await readback_cases()
	if failures>0:await finish("WIND_REVIEW_GPU_LIFECYCLE");return
	await immediate_close_cases()
	await dormant_canvas_close_case()
	await finish("WIND_REVIEW_GPU_LIFECYCLE")
