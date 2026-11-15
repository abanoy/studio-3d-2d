extends Node
# Editor live state is separate from authored animation; Record explicitly commits it.
const Rig=preload("res://src/physics_rig.gd")
const Prop=preload("res://src/physics_prop.gd")
const Model=preload("res://src/model.gd")
const Placement=preload("res://src/import_placement.gd")
const Recording=preload("res://src/physics_recording.gd")
const Secondary=preload("res://src/secondary_live.gd")
const Airflow=preload("res://src/airflow.gd")
const FanEditor=preload("res://src/fan_editor.gd")
const HelperEditor=preload("res://src/secondary_helper_editor.gd")
const WindReview=preload("res://src/wind_review.gd")
const ContactRanges=preload("res://src/contact_ranges.gd")
var recording
var app
var toggle: CheckButton
var hair_toggle: CheckButton
var fan_editor: RefCounted
var helper_editor: Node
var pending: Dictionary={}
var import_starts: Dictionary={}
var generation:=0
var simulations:={}
var colliders: Node3D
var collider_triangles:=0
var skipped_surfaces:=0
var grabbed: PhysicsBody3D
var grab_anchor: AnimatableBody3D
var grab_joint: PinJoint3D
var grab_depth:=1.0
var grab_point:=Vector2.ZERO

func setup(parent: Node) -> void:
	process_physics_priority=-10
	toggle=CheckButton.new();toggle.text="Physics";parent.add_child(toggle)
	toggle.tooltip_text="Selected model: simulate a ragdoll or a solid prop. Off freezes its current pose and position without recording animation. A real imported floor/map is needed; the grid is only a guide."
	toggle.toggled.connect(change)
	hair_toggle=CheckButton.new();hair_toggle.text="Hair & clothes";parent.add_child(hair_toggle);hair_toggle.toggled.connect(change_hair)
	recording=Recording.new();recording.editor=self;add_child(recording);recording.setup(parent)
	fan_editor=FanEditor.new();fan_editor.app=app;fan_editor.setup(parent)
	helper_editor=HelperEditor.new();helper_editor.app=app;add_child(helper_editor);helper_editor.setup(parent)
	app.local_wind_review=WindReview.new();app.local_wind_review.app=app;add_child(app.local_wind_review);app.local_wind_review.setup(parent)
	app.renderer.assets_changed.connect(clear)

func active(id: String) -> bool:return simulations.has(id)
func is_running() -> bool:return not simulations.is_empty()
func body_active(id: String) -> bool:return active(id) and (not simulations[id] is Secondary or simulations[id].primary!=null)
func grabbing() -> bool:return is_instance_valid(grabbed)

func pointer(event: InputEvent, point: Vector2) -> bool:
	if not is_running() or app.mode.selected==0:return false
	if event is InputEventMouseButton:
		if event.button_index==MOUSE_BUTTON_LEFT:
			if not event.pressed:
				var held:=grabbing();release_grab();return held
			if event.ctrl_pressed:return false
			var camera: Camera3D=app.renderer.camera
			var origin:=camera.project_ray_origin(point)
			var query:=PhysicsRayQueryParameters3D.create(origin,origin+camera.project_ray_normal(point)*2000,3)
			var hit: Dictionary=app.renderer.viewport.find_world_3d().direct_space_state.intersect_ray(query)
			if hit.is_empty() or not (hit.collider is PhysicalBone3D or hit.collider is RigidBody3D):return false
			return begin_grab(hit.collider,hit.position)
		if event.button_index==MOUSE_BUTTON_RIGHT and event.pressed:release_grab();return false
		if grabbing() and event.pressed and event.button_index in [MOUSE_BUTTON_WHEEL_UP,MOUSE_BUTTON_WHEEL_DOWN]:
			grab_depth=clampf(grab_depth*(0.9 if event.button_index==MOUSE_BUTTON_WHEEL_UP else 1.1),0.2,100);return true
	if event is InputEventMouseMotion and grabbing():grab_point=point;return true
	return false

func begin_grab(body: PhysicsBody3D, point: Vector3) -> bool:
	var owner:=""
	for id in simulations:
		if body in simulations[id].bodies.values():owner=id;break
	if owner.is_empty():return false
	var camera: Camera3D=app.renderer.camera
	if camera.is_position_behind(point):return false
	grab_point=camera.unproject_position(point)
	grab_depth=camera.project_ray_origin(grab_point).distance_to(point)
	release_grab();grabbed=body
	app.world_selection.select_entity(owner,false)
	grab_anchor=AnimatableBody3D.new();grab_anchor.name="PhysicsGrabAnchor";grab_anchor.sync_to_physics=false
	grab_anchor.collision_layer=0;grab_anchor.collision_mask=0
	var anchor_position: Vector3=app.renderer.world.to_local(point)
	grab_anchor.position=anchor_position
	app.renderer.world.add_child(grab_anchor)
	grab_joint=PinJoint3D.new();grab_joint.position=anchor_position
	app.renderer.world.add_child(grab_joint)
	grab_joint.node_a=grab_joint.get_path_to(grab_anchor);grab_joint.node_b=grab_joint.get_path_to(body)
	var message:=" Motion is unrecorded."
	if recording and recording.active:message=" This body's motion is being recorded." if recording.targets.has(owner) else " This body's motion is outside the locked Local recording scope."
	app.message("Hold left mouse to grab; move to lift, wheel for distance, release to throw. Ctrl + left still moves the camera."+message)
	return true

func _physics_process(delta: float) -> void:
	var time:=float(app.frame)
	if recording and recording.active:
		time=float(recording.start_frame)+float(recording.ticks+(1 if recording.armed else 0))*recording.fps_num/(recording.fps_den*Engine.physics_ticks_per_second)
	var has_secondary:=false
	for simulation in simulations.values():
		if simulation.has_method("sync_visual"):simulation.sync_visual()
		has_secondary=has_secondary or simulation is Secondary
	if has_secondary:
		var fields:=Airflow.collect(app.renderer,time,simulations)
		for id in simulations.keys():
			var simulation: RefCounted=simulations[id]
			if not simulation is Secondary:continue
			var error: String=simulation.advance(delta,app.frame,time,recording.active,fields,app.renderer.world_runtime)
			if not error.is_empty():freeze(id);app.message(error);break
	if fan_editor:fan_editor.update_status()
	if not grabbing():return
	if not is_instance_valid(grab_anchor):release_grab();return
	var camera: Camera3D=app.renderer.camera
	var target:=camera.project_ray_origin(grab_point)+camera.project_ray_normal(grab_point)*grab_depth
	# Bound target speed rather than teleporting a constrained body through the map.
	grab_anchor.global_position=grab_anchor.global_position.move_toward(target,10*delta)

func release_grab() -> void:
	if is_instance_valid(grab_joint):grab_joint.free()
	if is_instance_valid(grab_anchor):grab_anchor.free()
	grab_joint=null;grab_anchor=null;grabbed=null

func sync() -> void:
	if not is_instance_valid(toggle) or not is_instance_valid(app) or not is_instance_valid(app.renderer):return
	var rig: RefCounted=app.renderer.active_model()
	toggle.disabled=app.exporting or rig==null or rig.data.get("kind","model")!="model"
	toggle.set_pressed_no_signal(rig!=null and body_active(rig.data.id))
	var definition: Dictionary=rig.root.get_meta("has_secondary_rig",{}) if rig else {}
	var missing_chains: bool=definition.get("chains",[]).is_empty()
	var can_setup: bool=rig!=null and rig.data.get("kind","model")=="model" and not rig.order.is_empty() and helper_editor!=null and definition.get("error","").is_empty()
	var reviewing: bool=helper_editor!=null and is_instance_valid(helper_editor.window)
	hair_toggle.disabled=app.exporting or rig==null or rig.data.get("kind","model")!="model" or not definition.get("error","").is_empty() or missing_chains and (not can_setup or reviewing) or pending.has(rig.data.id)
	hair_toggle.set_pressed_no_signal(rig!=null and (pending.has(rig.data.id) or active(rig.data.id) and simulations[rig.data.id] is Secondary))
	hair_toggle.tooltip_text="Simulate hair/clothing joints while posed or with Physics. Off restores their authored pose; body Physics keeps running. Record explicitly keeps motion."
	if missing_chains:hair_toggle.tooltip_text=definition.get("error","") if not definition.get("error","").is_empty() else "This model needs hair/clothing joints. Turn on to review a loose part and add weighted helpers; the original is kept." if can_setup else "Select a skinned model to review and add hair/clothing joints."
	if fan_editor:fan_editor.sync()
	if recording:recording.sync()

func _process(_delta: float) -> void:
	for simulation in simulations.values():
		if simulation.has_method("sync_visual"):simulation.sync_visual()
	process_import_starts()
	sync()

func change(enabled: bool) -> void:
	var actor: RefCounted=app.renderer.active_model()
	if not actor or app.exporting:return
	import_starts.erase(actor.data.id)
	if not enabled:freeze(actor.data.id);return
	enable_body(actor)
	sync()

func enable_body(actor: RefCounted) -> void:
	helper_editor.stop_pending_for_actor(actor.data.id)
	if pending.has(actor.data.id):sync();app.message("Hair/clothing setup is finishing. Try the body toggle when it is ready.");return
	if body_active(actor.data.id):sync();return
	if recording and recording.active:sync();app.message("Stop recording before enabling another physics object.");return
	if actor.data.get("kind","model")!="model":sync();app.message("Maps remain collision surfaces. Enable Physics on a model or prop.");return
	if not actor.root.is_visible_in_tree():sync();app.message("Show this model at the current frame before enabling Physics.");return
	for simulation in simulations.values():
		if simulation.rig.root.is_ancestor_of(actor.root) or actor.root.is_ancestor_of(simulation.rig.root):
			sync();app.message("Freeze the simulated parent or child first. Simulate independent models together; nested live bodies are not supported yet.");return
	app.stop();app.pose_editor.finish_drag();app.finish_stroke()
	var result: Dictionary=Prop.create(actor,app.renderer.world,app.frame) if actor.order.size()<=1 else Rig.create(actor,app.frame)
	if result.has("error"):toggle.set_pressed_no_signal(false);app.message(result.error);return
	if active(actor.data.id) and simulations[actor.data.id] is Secondary:
		for chain in simulations[actor.data.id].runner.chains:
			for id in chain.ids:
				if result.physics.bodies.has(id):
					result.physics.dispose();simulations[actor.data.id].start();sync();app.message("A secondary chain also drives a body joint. Review that rig before combining both simulations.");return
	if not is_instance_valid(colliders):build_colliders()
	if active(actor.data.id) and simulations[actor.data.id] is Secondary:
		var combined: RefCounted=simulations[actor.data.id];combined.primary=result.physics;combined.bodies=result.physics.bodies;result.physics.initial_pose=combined.initial_pose.duplicate(true)
	else:simulations[actor.data.id]=result.physics
	result.physics.start()
	app.message(("Physics on: rigid prop with approximate convex collision." if actor.order.size()<=1 else "Physics on: approximate ragdoll.")+" Switch off to freeze. Motion is not recorded."+(" No map collider: the grid is not a floor." if collider_triangles==0 else "")+(" Some map surfaces exceed the collision budget." if skipped_surfaces>0 else "")+(" Dense prop meshes use fitted boxes." if result.physics is Prop and result.physics.box_fallbacks>0 else ""))

func change_hair(enabled: bool) -> void:
	var actor: RefCounted=app.renderer.active_model()
	if not actor or app.exporting:return
	helper_editor.stop_pending_for_actor(actor.data.id)
	import_starts.erase(actor.data.id)
	if not enabled:
		generation+=1;pending.erase(actor.data.id);disable_hair(actor.data.id);sync();return
	enable_hair(actor)

func disable_hair(id: String) -> void:
	if recording and recording.active:
		recording.finish("hair/clothes off");return
	if not simulations.has(id) or not simulations[id] is Secondary:return
	var simulation: RefCounted=simulations[id];var actor: RefCounted=simulation.rig
	var body: RefCounted=simulation.detach_primary();var world: Transform3D=actor.root.global_transform
	# Keep the live body's solver and shared body dictionary. Disposing secondary
	# offsets must neither freeze the body nor author a simulated hair draft.
	simulation.dispose();simulations.erase(id)
	actor.preview_frame=-1;actor.preview_pose={};actor.preview_transform={}
	if body:
		simulations[id]=body;actor.live_pose=body.initial_pose;actor.live_world_transform=world
	app.pose_editor.apply_frame()
	if not is_running():clear_colliders()
	app.message("Hair & clothes off: authored pose restored. Recorded animation is kept."+(" Body Physics is still on." if body else ""))

func enable_hair(actor: RefCounted) -> void:
	helper_editor.stop_pending_for_actor(actor.data.id)
	if pending.has(actor.data.id) or active(actor.data.id) and simulations[actor.data.id] is Secondary:return
	if recording.active:sync();app.message("Stop recording before enabling another simulation.");return
	if actor.data.get("kind","model")!="model" or not actor.root.is_visible_in_tree():sync();app.message("Select a visible model with declared hair/clothing joints.");return
	var definition: Dictionary=actor.root.get_meta("has_secondary_rig",{})
	if definition.get("chains",[]).is_empty():
		hair_toggle.set_pressed_no_signal(false)
		if definition.get("error","").is_empty() and not actor.order.is_empty() and helper_editor:
			helper_editor.open(true)
		else:app.message(definition.get("error","") if not definition.get("error","").is_empty() else "Select a skinned model to set up loose parts.")
		sync();return
	for simulation in simulations.values():
		if simulation.rig!=actor and (simulation.rig.root.is_ancestor_of(actor.root) or actor.root.is_ancestor_of(simulation.rig.root)):
			sync();app.message("Freeze the live parent or child before enabling this simulation.");return
	app.stop();app.pose_editor.finish_drag();app.finish_stroke()
	var id: String=actor.data.id;var before: Dictionary=actor.data.duplicate(true);var token:=generation+1;generation=token;pending[id]=token;sync()
	var result: Dictionary=await Secondary.create(actor,simulations.get(id),app.frame,app.mode.selected==2)
	var valid: bool=is_inside_tree() and pending.get(id,-1)==token and is_instance_valid(actor.root) and actor.data==before
	if pending.get(id,-1)==token:pending.erase(id)
	if not valid:
		if result.has("physics"):
			var cancelled: RefCounted=result.physics;var keep: RefCounted=null
			var world:=Transform3D.IDENTITY
			# An unfinished secondary wrapper borrows its primary. Cancelling that
			# wrapper cannot dispose a body still owned by the live editor.
			if cancelled.primary!=null and simulations.get(id)==cancelled.primary and is_instance_valid(actor.root):
				world=actor.root.global_transform;keep=cancelled.detach_primary()
			cancelled.dispose()
			if keep:actor.live_pose=keep.initial_pose;actor.live_world_transform=world
		if is_inside_tree():app.pose_editor.apply_frame();sync()
		return
	if result.has("error"):app.pose_editor.apply_frame();sync();app.message(result.error);return
	simulations[id]=result.physics;result.physics.start();sync()
	app.message("Hair & clothes on. The body stays posed unless Physics is on. Move a fan or adjust its blowing speed; Record keeps the motion.")

func build_colliders() -> void:
	clear_colliders();colliders=Node3D.new();colliders.name="StudioPhysicsColliders";app.renderer.world.add_child(colliders)
	var meshes: Array=[];var stops:={}
	if app.renderer.world_runtime:
		for actor in app.renderer.world_runtime.instances.values():stops[actor.root]=true
		for actor in app.renderer.world_runtime.instances.values():
			if actor.data.kind=="environment":Placement.collect(actor.root,meshes,stops)
	elif app.renderer.environment_scene:Placement.collect(app.renderer.environment_scene,meshes,{})
	for mesh in meshes:
		for surface in range(mesh.mesh.get_surface_count()):
			if mesh.mesh.surface_get_primitive_type(surface)!=Mesh.PRIMITIVE_TRIANGLES:continue
			var count: int=mesh.mesh.surface_get_array_index_len(surface)
			if count==0:count=mesh.mesh.surface_get_array_len(surface)
			if count/3>100000-collider_triangles:skipped_surfaces+=1;continue
			var arrays: Array=mesh.mesh.surface_get_arrays(surface)
			var vertices: PackedVector3Array=preload("res://src/source_shape.gd").vertices(mesh,surface,arrays[Mesh.ARRAY_VERTEX])
			var indices: PackedInt32Array=arrays[Mesh.ARRAY_INDEX] if arrays[Mesh.ARRAY_INDEX] is PackedInt32Array else PackedInt32Array()
			var faces:=PackedVector3Array()
			for i in range(count):faces.append(mesh.global_transform*vertices[indices[i] if not indices.is_empty() else i])
			if faces.is_empty():continue
			var shape:=ConcavePolygonShape3D.new();shape.set_faces(faces);shape.backface_collision=true
			var collision:=CollisionShape3D.new();collision.shape=shape
			var body:=StaticBody3D.new();body.collision_layer=1;body.collision_mask=2;body.add_child(collision);colliders.add_child(body)
			collider_triangles+=count/3

func freeze(id: String, history:=true) -> bool:
	if recording and recording.active:return recording.finish("physics off")
	if not simulations.has(id):return true
	var simulation: RefCounted=simulations[id];var actor: RefCounted=simulation.rig
	var before: Dictionary=actor.data.duplicate(true)
	var candidate: Dictionary=before.duplicate(true)
	var released:=false
	if Model.is_contact(before) and body_active(id):
		# A live body owns its fallen pose, not the authored foot targets. Release
		# this draft frame atomically; seeking elsewhere still uses authored pins.
		var result:=ContactRanges.edit(before,app.frame,app.frame+1,{},int(app.video.duration_frames))
		if result.has("error"):
			sync();app.message("Physics is still on: cannot freeze this planted frame. "+result.error);return false
		candidate=result.data;released=result.changed
	var transform: Dictionary=simulation.root_transform(app.frame,app.mode.selected==2)
	var pose: Dictionary=simulation.pose()
	candidate.pose=pose;candidate.position=transform.position;candidate.rotation_xyzw=transform.rotation_xyzw;candidate.scale=transform.scale;candidate.draft_frame=app.frame
	if before.get("format")==Model.ShapeAnimation.LEGACY_FORMAT:candidate.shape_pose=actor.sample_shapes(app.frame,true)
	var error:=Model.validate(candidate,int(app.video.duration_frames))
	if Model.is_contact(before):
		if not error.is_empty():sync();app.message("Physics is still on: cannot freeze this pose. "+error);return false
		var world: Dictionary=app.current_world()
		for i in range(world.objects.size()):
			if world.objects[i].id==id:world.objects[i]=candidate
		if app.pose_editor.contacts.metadata_bytes(world)>1024*1024:
			sync();app.message("Physics is still on: the frozen pose exceeds the1MiB project metadata limit.");return false
	release_grab();simulation.stop();simulation.dispose();simulations.erase(id);sync()
	if not error.is_empty():
		if not is_running():clear_colliders()
		app.pose_editor.apply_frame();app.message("Physics pose exceeded supported limits. The authored state was kept; nothing was recorded. "+error)
		return false
	actor.data=candidate
	actor.preview_pose=pose.duplicate(true);actor.preview_transform=transform.duplicate(true);actor.preview_frame=app.frame
	if history:app.pose_editor.commit(before,false)
	else:app.pose_editor.apply_frame()
	if not is_running():clear_colliders()
	app.message("Physics off: current pose frozen. No simulation keys were added. Pose drafts resume their authored track when scrubbing."+(" Feet released at this frame; surrounding contact ranges were kept." if released else ""))
	return true

func freeze_all() -> bool:
	generation+=1;pending.clear();import_starts.clear()
	if recording and recording.active:return recording.finish("save/play/operation")
	var valid:=true;var error:=""
	for id in simulations.keys():
		if not freeze(id):
			valid=false
			if error.is_empty():error=app.status.text
	if not valid:app.message(error)
	return valid

func clear_previews() -> void:
	if app.renderer.world_runtime:
		for actor in app.renderer.world_runtime.instances.values():actor.preview_frame=-1;actor.preview_pose={};actor.preview_transform={}
	elif app.renderer.model:app.renderer.model.preview_frame=-1;app.renderer.model.preview_pose={};app.renderer.model.preview_transform={}

func clear_colliders() -> void:
	if is_instance_valid(colliders):colliders.free()
	colliders=null;collider_triangles=0;skipped_surfaces=0

func clear() -> void:
	generation+=1;pending.clear();import_starts.clear()
	if recording and recording.active:recording.cancel("Recording discarded because the world changed.",false)
	release_grab()
	for simulation in simulations.values():simulation.dispose()
	simulations.clear();clear_colliders()
	sync()

func _exit_tree() -> void:clear()

# Transient import intent only: never serialized or rearmed by HAS Open/Undo.
func import_intents() -> Dictionary:
	var result:={}
	for id in simulations:
		result[id]={"body":body_active(id),"hair":simulations[id] is Secondary,"ragdoll_only":false}
	for id in import_starts:
		var ticket: Dictionary=import_starts[id]
		result[id]={"body":ticket.body,"hair":ticket.hair,"ragdoll_only":ticket.ragdoll_only}
	return result

func restore_import_intents(values: Dictionary) -> void:
	for id in values:queue_import_start(id,values[id].body,values[id].hair,values[id].ragdoll_only)

func queue_import_start(id: String, body: bool, hair: bool, ragdoll_only:=false) -> void:
	if not app.renderer.world_runtime:return
	var actor: RefCounted=app.renderer.world_runtime.instance(id)
	if actor==null or actor.data.kind!="model":return
	# Solid props keep their explicit toggle; a static mesh is not a ragdoll.
	if ragdoll_only and actor.order.size()<=1:return
	import_starts[id]={"body":body,"hair":hair,"ragdoll_only":ragdoll_only,"root":actor.root,"data":actor.data.duplicate(true),"frame":app.frame}

func process_import_starts() -> void:
	if import_starts.is_empty() or app.exporting or app.playing or app.drawing or app.navigating or app.pose_editor.dragging:return
	if app.source_import.pid>0 or app.has_project.pid>0 or app.has_dialog(app):return
	if app.timeline and (not app.timeline.moving_id.is_empty() or app.timeline.audio_gesture_active()):return
	for id in import_starts.keys():
		var ticket: Dictionary=import_starts[id]
		var actor: RefCounted=app.renderer.world_runtime.instance(id) if app.renderer.world_runtime else null
		import_starts.erase(id)
		if actor==null or not is_instance_valid(ticket.root) or actor.root!=ticket.root or actor.data!=ticket.data or app.frame!=ticket.frame:continue
		if not actor.root.is_visible_in_tree():continue
		# A rebuilt peer must start at its frozen draft, even after selection changed.
		actor.apply_current(app.frame,true)
		if ticket.body:enable_body(actor)
		if ticket.hair:enable_hair(actor)
