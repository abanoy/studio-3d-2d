extends RefCounted
# Isolated read-only clone: neither the live camera nor the source skeleton moves.
const Model=preload("res://src/model.gd")
const Timeline=preload("res://src/timeline.gd")
const Bounds=preload("res://src/pose_bounds.gd")
static func capture(rig: RefCounted,pose: Dictionary,parent: Node) -> Dictionary:
	var viewport:=SubViewport.new();viewport.size=Vector2i(96,54);viewport.own_world_3d=true;viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;viewport.gui_disable_input=true;parent.add_child(viewport)
	var clone: Node3D=rig.root.duplicate();clone.transform=rig.base_root;clone.visible=true;clone.process_mode=Node.PROCESS_MODE_DISABLED
	var pending: Array=[clone]
	while not pending.is_empty():
		var node: Node=pending.pop_back();pending.append_array(node.get_children())
		if node is AnimationPlayer:node.autoplay="";node.stop(true)
		if node is AnimationTree:node.active=false
		if node is Camera3D:node.current=false
		if node is RigidBody3D:node.freeze=true;node.sleeping=true
	viewport.add_child(clone)
	var skeletons:={}
	for id in rig.order:
		var info: Dictionary=rig.bones[id];var skeleton=clone.get_node_or_null(NodePath(info.path))
		if not skeleton is Skeleton3D:viewport.queue_free();return {"error":"Cannot make an independent pose thumbnail for this rig."}
		var base: Transform3D=info.base;var delta: Dictionary=pose.get(id,Model.identity())
		skeleton.set_bone_pose_position(info.index,base.origin+Timeline.vector(delta.position));skeleton.set_bone_pose_rotation(info.index,base.basis.get_rotation_quaternion()*Timeline.quaternion(delta.rotation_xyzw));skeleton.set_bone_pose_scale(info.index,base.basis.get_scale());skeletons[skeleton.get_instance_id()]=skeleton
	for skeleton in skeletons.values():skeleton.remove_meta(Bounds.FINAL_META);skeleton.force_update_all_bone_transforms()
	var queried:=Bounds.query(clone)
	if not queried.error.is_empty():viewport.queue_free();return {"error":queried.error}
	var bounds: AABB=queried.bounds;var radius:=bounds.size.length()*.5
	if not is_finite(radius) or radius<=0:viewport.queue_free();return {"error":"This model has no visible geometry for a body-pose thumbnail."}
	var environment:=WorldEnvironment.new();environment.environment=Environment.new();environment.environment.background_mode=Environment.BG_COLOR;environment.environment.background_color=Color("405567");environment.environment.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR;environment.environment.ambient_light_color=Color.WHITE;environment.environment.ambient_light_energy=.9;viewport.add_child(environment)
	var light:=DirectionalLight3D.new();light.rotation_degrees=Vector3(-35,-25,0);light.light_energy=1.1;viewport.add_child(light)
	var camera:=Camera3D.new();camera.fov=45;camera.near=maxf(.0001,radius/10000);var distance:=radius/sin(deg_to_rad(22.5))*1.12;camera.far=maxf(10,distance+radius*4);viewport.add_child(camera);camera.position=bounds.get_center()+Vector3(.35,.2,1).normalized()*distance;camera.look_at(bounds.get_center(),Vector3.UP);camera.current=true
	await parent.get_tree().process_frame;await RenderingServer.frame_post_draw
	var image:=viewport.get_texture().get_image();viewport.queue_free()
	if image==null:return {"error":"Cannot read the body-pose thumbnail."}
	image.convert(Image.FORMAT_RGBA8);return {"image":image}
