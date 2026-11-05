extends RefCounted
# A world-space proxy drives the visual root without changing authored model data.
const IK=preload("res://src/limb_ik.gd")
var rig: RefCounted
var body: RigidBody3D
var bodies:={}
var initial_pose: Dictionary={}
var visual_offset:=Transform3D.IDENTITY
var running:=false
var box_fallbacks:=0

static func solid(points: PackedVector3Array) -> bool:
	if points.size()<4:return false
	var a:=points[0];var b:=a;var far:=0.0
	for point in points:
		var distance:=a.distance_squared_to(point)
		if distance>far:far=distance;b=point
	if far<0.000001:return false
	var normal:=Vector3.ZERO;far=0
	for point in points:
		var cross: Vector3=(b-a).cross(point-a)
		if cross.length_squared()>far:far=cross.length_squared();normal=cross
	if far<0.000000000001:return false
	normal=normal.normalized()
	for point in points:
		if absf(normal.dot(point-a))>0.0005:return true
	return false

static func create(actor: RefCounted, world: Node3D, frame:=0) -> Dictionary:
	if not actor or not is_instance_valid(actor.root) or actor.data.get("kind","model")!="model":return {"error":"Physics props must be models, not maps or groups."}
	if actor.order.size()>1:return {"error":"This rig needs a supported ragdoll; it cannot safely be treated as one rigid prop."}
	if not actor.root.is_visible_in_tree():return {"error":"Show this object at the current frame before enabling Physics."}
	if not IK.regular(actor.root.global_basis):return {"error":"Prop physics needs positive uniform scale, including its parents."}
	var meshes: Array=actor.opacity_materials.meshes if actor.opacity_materials else []
	var specs: Array=[];var used:=0;var fallbacks:=0
	var initial:=Transform3D(actor.root.global_basis.orthonormalized(),actor.root.global_position)
	for mesh in meshes:
		if not is_instance_valid(mesh) or not mesh.is_visible_in_tree() or not mesh.mesh:continue
		if not mesh.mesh is ArrayMesh:return {"error":"Prop physics needs standardized triangle meshes. Re-import this model first."}
		if specs.size()>=32:return {"error":"This prop exceeds32 collision meshes. Use a simpler model for live physics."}
		var points:=PackedVector3Array()
		for surface in range(mesh.mesh.get_surface_count()):
			if mesh.mesh.surface_get_primitive_type(surface)!=Mesh.PRIMITIVE_TRIANGLES:continue
			var arrays: Array=mesh.mesh.surface_get_arrays(surface)
			var vertices: PackedVector3Array=preload("res://src/source_shape.gd").vertices(mesh,surface,arrays[Mesh.ARRAY_VERTEX])
			used+=vertices.size()
			if used>100000:return {"error":"This prop exceeds100000 collision vertices. Use a simpler model for live physics."}
			var sk: Skeleton3D=mesh.get_node_or_null(mesh.skeleton) if mesh.skin else null
			var binds: Array=[]
			if sk:
				for i in range(mesh.skin.get_bind_count()):
					var bone: int=mesh.skin.get_bind_bone(i)
					if bone<0:bone=sk.find_bone(mesh.skin.get_bind_name(i))
					if bone<0:return {"error":"This prop has an unresolved skin binding."}
					binds.append(sk.get_bone_global_pose(bone)*mesh.skin.get_bind_pose(i))
			var bones=arrays[Mesh.ARRAY_BONES];var weights=arrays[Mesh.ARRAY_WEIGHTS]
			var stride: int=bones.size()/vertices.size() if bones is PackedInt32Array and not vertices.is_empty() else 0
			if sk and (stride not in [4,8] or not weights is PackedFloat32Array or weights.size()!=bones.size()):return {"error":"This prop has an unsupported skin layout."}
			for i in range(vertices.size()):
				var point: Vector3=mesh.global_transform*vertices[i]
				if sk:
					point=Vector3.ZERO
					for j in range(stride):
						var weight: float=weights[i*stride+j];var bind: int=bones[i*stride+j]
						if weight<=0:continue
						if bind<0 or bind>=binds.size():return {"error":"This prop has an invalid skin binding."}
						point+=(sk.global_transform*(binds[bind]*vertices[i]))*weight
				points.append(initial.affine_inverse()*point)
		if points.is_empty():continue
		var bounds:=AABB(points[0],Vector3.ZERO)
		for point in points:bounds=bounds.expand(point)
		if minf(bounds.size.x,minf(bounds.size.y,bounds.size.z))<0.001 or not solid(points):return {"error":"Prop collision needs a solid mesh with thickness, not a flat drawing plane."}
		if not bounds.position.is_finite() or not bounds.size.is_finite() or bounds.size.length()>1000:return {"error":"This prop has unsupported collision bounds."}
		var shape: Shape3D;var offset:=Transform3D.IDENTITY
		if points.size()<=4096:
			var convex:=ConvexPolygonShape3D.new();convex.points=points;shape=convex
		else:
			var box:=BoxShape3D.new();box.size=bounds.size;shape=box;offset.origin=bounds.get_center();fallbacks+=1
		shape.margin=minf(0.005,minf(bounds.size.x,minf(bounds.size.y,bounds.size.z))*0.025)
		specs.append({"shape":shape,"transform":offset})
	if specs.is_empty():return {"error":"This model has no visible solid mesh for prop physics."}
	var candidate=new();candidate.rig=actor;candidate.initial_pose=actor.sample(frame,true);candidate.box_fallbacks=fallbacks
	var proxy:=RigidBody3D.new();proxy.name="StudioPhysicsProp";candidate.body=proxy
	proxy.collision_layer=2;proxy.collision_mask=3;proxy.continuous_cd=true
	proxy.mass=1;proxy.linear_damp=0.15;proxy.angular_damp=1.5;proxy.freeze=true
	var material:=PhysicsMaterial.new();material.friction=0.8;material.bounce=0;proxy.physics_material_override=material
	for spec in specs:
		var collision:=CollisionShape3D.new();collision.shape=spec.shape;collision.transform=spec.transform;proxy.add_child(collision)
	world.add_child(proxy);proxy.global_transform=initial
	candidate.visual_offset=initial.affine_inverse()*actor.root.global_transform
	candidate.bodies={"@root":proxy}
	return {"physics":candidate}

func start() -> void:
	running=true;rig.live_pose=initial_pose;body.freeze=false;sync_visual()

func sync_visual() -> void:
	if not running or not is_instance_valid(body):return
	rig.live_world_transform=body.global_transform*visual_offset
	rig.root.global_transform=rig.live_world_transform

func root_transform(_frame: int, _editing: bool) -> Dictionary:
	sync_visual()
	var local: Transform3D=rig.root.get_parent().global_transform.affine_inverse()*rig.root.global_transform*rig.base_root.affine_inverse()
	var q:=local.basis.orthonormalized().get_rotation_quaternion().normalized()
	return {"position":[local.origin.x,local.origin.y,local.origin.z],"rotation_xyzw":[q.x,q.y,q.z,q.w],"scale":local.basis.get_scale().x}

func pose() -> Dictionary:return initial_pose.duplicate(true)

func stop() -> Dictionary:
	sync_visual();running=false;body.freeze=true;rig.live_world_transform=null;rig.live_pose=null
	return pose()

func dispose() -> void:
	running=false;rig.live_world_transform=null;rig.live_pose=null
	if is_instance_valid(body):body.free()
	body=null;bodies.clear()
