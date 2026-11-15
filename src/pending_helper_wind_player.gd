extends Node
# Only the disposable derived model is simulated. Original actor/peers are
# borrowed inputs; visibility and pointer state are restored by ownership.
signal phase_changed(value: String)
signal failed(reason: String)
const Groups=preload("res://src/wind_review_groups.gd")
const Spring=preload("res://src/secondary_spring.gd")
const Secondary=preload("res://src/secondary_live.gd")
const Definition=preload("res://src/secondary_rig.gd")
const Airflow=preload("res://src/airflow.gd")
var app
var phase:="stopped"
var source: RefCounted
var candidate: RefCounted
var simulation: RefCounted
var private_space: SubViewport
var hidden: Dictionary={}
var previous_pointer:=Callable()
var pointer_pending:=false
var guard:=Callable()
var baseline: Dictionary={}
var wind_direction:=Vector3.LEFT
var strength:=6.
var settling:=0

func valid() -> bool:
	return guard.is_valid() and guard.call() and source!=null and candidate!=null and is_instance_valid(source.root) and is_instance_valid(candidate.root)

func other_roots() -> Array:
	var result: Array=[]
	if app.renderer.world_runtime:
		for current in app.renderer.world_runtime.instances.values():
			if current!=source and is_instance_valid(current.root):result.append(current.root)
		for current in app.renderer.world_runtime.effects.values():
			if is_instance_valid(current.root):result.append(current.root)
	return result

func start(actor: RefCounted,prepared: Dictionary,context_guard: Callable,speed: float,direction: int) -> String:
	stop("Restarting",false)
	if DisplayServer.get_name()=="headless":return "Visible wind needs a graphical review."
	if not is_finite(speed) or speed<0 or speed>50 or direction<0 or direction>3:return "Invalid local wind settings."
	if not prepared.has("model") or not prepared.has("catalog") or not prepared.get("selected_group_ids") is Array:return "The checked setup is incomplete."
	source=actor;candidate=prepared.model;guard=context_guard;strength=speed
	if not valid():stop("Review changed",false);return "The reviewed model changed before wind could start."
	if FileAccess.get_sha256(candidate.data.source)!=prepared.catalog.get("source_sha256",""):stop("Candidate changed",false);return "The checked setup changed."
	# The first bounded display path handles model geometry. Scene light/camera/
	# environment payloads need a separate admission policy before duplication.
	for node in [candidate.root]+candidate.root.find_children("*","Node",true,false):
		if node is Light3D or node is Camera3D or node is WorldEnvironment:stop("Scene payload needs review",false);return "This model includes scene lights or cameras that need a separate preview review."
	var filtered:=Groups.filter(prepared.catalog,prepared.selected_group_ids)
	if not filtered.get("error","").is_empty() or filtered.get("chains",[]).is_empty():stop("No checked groups",false);return "Choose at least one motion group to try."
	baseline=candidate.data.pose.duplicate(true)
	if candidate.root.get_parent():candidate.root.get_parent().remove_child(candidate.root)
	candidate.root.visible=false;app.renderer.world.add_child(candidate.root);app.renderer.disable_cameras(candidate.root)
	candidate.live_pose=baseline.duplicate(true);candidate.live_world_transform=source.root.global_transform;candidate.apply(app.frame,false,false,app.video,source.evaluated_opacity)
	private_space=SubViewport.new();private_space.name="PendingHelperWindPhysics";private_space.own_world_3d=true;private_space.render_target_update_mode=SubViewport.UPDATE_DISABLED;private_space.size=Vector2i(1,1);add_child(private_space)
	var result:=Spring.construct(candidate,filtered,private_space)
	if result.has("error"):stop(result.error,false);return result.error
	simulation=Secondary.new();simulation.rig=candidate;simulation.runner=result.runner;simulation.initial_pose=baseline.duplicate(true);simulation.latest=baseline.duplicate(true);simulation.initial_world=source.root.global_transform
	var camera: Camera3D=app.renderer.camera
	wind_direction=([-camera.global_basis.x,camera.global_basis.x,-camera.global_basis.z,camera.global_basis.z][direction] as Vector3).normalized()
	for mesh in Groups.mesh_nodes(source.root,other_roots()):hidden[mesh]=mesh.visible;mesh.visible=false
	previous_pointer=app.canvas.review_pointer;app.canvas.review_pointer=Callable(self,"pointer")
	app.canvas.pose_lines=[];app.canvas.pose_joints=[];app.canvas.review_lines=PackedVector2Array();app.canvas.review_chain=PackedVector2Array();app.canvas.queue_redraw()
	phase="warming";settling=2;schedule_warmup();phase_changed.emit(phase)
	return ""

func schedule_warmup() -> void:
	if RenderingServer.frame_post_draw.is_connected(warm_frame):RenderingServer.frame_post_draw.disconnect(warm_frame)
	RenderingServer.frame_post_draw.connect(warm_frame,CONNECT_ONE_SHOT)

func warm_frame() -> void:
	if RenderingServer.frame_post_draw.is_connected(warm_frame):RenderingServer.frame_post_draw.disconnect(warm_frame)
	if not valid():fail("The reviewed setup changed.");return
	settling-=1
	if settling>0:schedule_warmup();return
	phase="running";simulation.start();phase_changed.emit(phase)

func local_field() -> Dictionary:
	var center:=Vector3.ZERO;var count:=0;var radius:=.5
	for chain in simulation.runner.chains:center+=Definition.binding_transform(candidate,chain.source.joints[0].binding).origin;count+=1
	center/=maxi(count,1)
	for chain in simulation.runner.chains:radius=maxf(radius,center.distance_to(Definition.binding_transform(candidate,chain.source.joints[0].binding).origin)+.5)
	return {"transform":Transform3D(Basis(Quaternion(Vector3.BACK,wind_direction)),center-wind_direction*1.5-Vector3(0,.85,0)),"settings":{"format":Airflow.FORMAT,"enabled":true,"speed":strength,"radius":minf(radius,1000.),"reach":6.}}

func _physics_process(delta: float) -> void:
	if phase!="running":return
	if not valid():fail("The reviewed setup changed.");return
	simulation.initial_pose=baseline.duplicate(true);simulation.initial_world=source.root.global_transform
	var error: String=simulation.advance(minf(delta,1./60.),app.frame,float(app.frame),false,[local_field()],null)
	if not error.is_empty():fail(error)

func pointer(event: InputEventMouse,point: Vector2) -> bool:
	if phase not in ["warming","running"]:return false
	if not pointer_pending and not app.canvas.scene_contains(point):return false
	if event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_LEFT and (not event.ctrl_pressed or pointer_pending):
		if event.pressed:pointer_pending=true;app.canvas.grab_focus();app.world_selection.input(event,point)
		elif pointer_pending:
			pointer_pending=false
			if app.navigating:app.world_selection.input(event,point)
			else:app.world_selection.cancel_gesture(true)
		return true
	if pointer_pending:app.world_selection.input(event,point);return true
	return false

func global_event(event: InputEvent) -> bool:
	if not pointer_pending or not event is InputEventMouse:return false
	var local: Vector2=app.canvas.get_global_transform_with_canvas().affine_inverse()*event.position;var rect: Rect2=app.canvas.image_rect()
	return pointer(event,(local-rect.position)/rect.size*Vector2(app.video.width,app.video.height))

func fail(reason: String) -> void:
	stop(reason,false);failed.emit(reason)

func stop(_reason: String="Stopped",dispose:=true) -> void:
	if RenderingServer.frame_post_draw.is_connected(warm_frame):RenderingServer.frame_post_draw.disconnect(warm_frame)
	phase="stopped";settling=0
	if pointer_pending and is_instance_valid(app) and is_instance_valid(app.world_selection):app.world_selection.cancel_gesture(true)
	pointer_pending=false
	if is_instance_valid(app) and is_instance_valid(app.canvas) and app.canvas.review_pointer==Callable(self,"pointer"):app.canvas.review_pointer=previous_pointer
	previous_pointer=Callable()
	if simulation:simulation.dispose();simulation=null
	if candidate and is_instance_valid(candidate.root):
		candidate.root.visible=false
		if candidate.root.get_parent():candidate.root.get_parent().remove_child(candidate.root)
		if dispose:candidate.root.free()
	candidate=null;source=null;guard=Callable();baseline={}
	if is_instance_valid(private_space):private_space.free()
	private_space=null
	for mesh in hidden:
		if is_instance_valid(mesh):mesh.visible=hidden[mesh]
	hidden.clear()
	if is_instance_valid(app) and app.is_inside_tree() and is_instance_valid(app.canvas) and is_instance_valid(app.pose_editor):app.pose_editor.update_gizmo()

func _exit_tree() -> void:stop("Closed")
