extends RefCounted
# Runtime-only arm envelopes for generated HAS chains with no source colliders.
# Skin resources, source declarations, joint settings and saved models stay intact.
const IK=preload("res://src/limb_ik.gd")
const Bounds=preload("res://src/pose_bounds.gd")
const Shape=preload("res://src/source_shape.gd")
const MAX_VERTICES:=200000
static func point_segment(point: Vector3,a: Vector3,b: Vector3) -> float:
	var axis:=b-a
	return point.distance_to(a+axis*clampf((point-a).dot(axis)/axis.length_squared(),0.,1.))
static func build(actor: RefCounted) -> Dictionary:
	var segments: Dictionary={};var skeletons: Dictionary={}
	for id in actor.order:
		var limb: Dictionary=IK.chain(actor,id)
		if not limb.get("role","") in ["leftHand","rightHand"]:continue
		for i in range(2):
			var start: String=limb.ids[i];var finish: String=limb.ids[i+1]
			var t: Transform3D=actor.bone_transform(start);var end: Vector3=actor.bone_transform(finish).origin
			if not IK.regular(t.basis) or not t.origin.is_finite() or not end.is_finite() or t.origin.distance_to(end)<.00001:continue
			segments[start]={"transform":t,"start":t.origin,"finish":end,"finish_id":finish,"radius":0.,"vertices":0}
			skeletons[actor.bones[start].skeleton]=true
	if segments.is_empty():return {"colliders":[],"reason":"No unambiguous supported arm chains."}
	var inspected:=0;var matched:=0;var context:={"palettes":{},"updated":{},"error":""}
	var candidates: Array=actor.root.find_children("*","MeshInstance3D",true,false)
	for item in candidates:
		var mesh: MeshInstance3D=item
		var sk=mesh.get_node_or_null(mesh.skeleton)
		if not sk is Skeleton3D or not skeletons.has(sk) or mesh.mesh==null or mesh.skin==null:continue
		if not mesh.global_transform.is_equal_approx(sk.global_transform):return {"colliders":[],"reason":"Generated arm contact needs matching mesh and skeleton frames."}
		if not IK.regular(mesh.global_basis):return {"colliders":[],"reason":"Arm collision fitting needs positive uniform mesh scale."}
		var palette: Array=Bounds.palette(mesh,context)
		if not context.error.is_empty():return {"colliders":[],"reason":context.error}
		var ids: Array=[]
		for bind in range(mesh.skin.get_bind_count()):
			var name: String=mesh.skin.get_bind_name(bind)
			var index: int=sk.find_bone(name) if not name.is_empty() else mesh.skin.get_bind_bone(bind)
			if index<0 or index>=sk.get_bone_count():return {"colliders":[],"reason":"Arm skin binding changed."}
			ids.append(str(actor.root.get_path_to(sk))+"::"+str(sk.get_bone_name(index)))
		for surface in range(mesh.mesh.get_surface_count()):
			var arrays: Array=mesh.mesh.surface_get_arrays(surface)
			if arrays.size()!=Mesh.ARRAY_MAX or not arrays[Mesh.ARRAY_VERTEX] is PackedVector3Array:continue
			var vertices: PackedVector3Array=Shape.vertices(mesh,surface,arrays[Mesh.ARRAY_VERTEX]);inspected+=vertices.size()
			if inspected>MAX_VERTICES:return {"colliders":[],"reason":"Arm collision fitting exceeds the bounded vertex budget."}
			var joints=arrays[Mesh.ARRAY_BONES];var weights=arrays[Mesh.ARRAY_WEIGHTS]
			if not joints is PackedInt32Array or joints.is_empty() or vertices.is_empty():continue
			var stride: int=joints.size()/vertices.size()
			if stride not in [4,8] or joints.size()!=vertices.size()*stride or not weights is PackedFloat32Array or weights.size()!=joints.size():return {"colliders":[],"reason":"Unsupported arm skin weight layout."}
			for v in range(vertices.size()):
				var dominant:=-1;var maximum:=-1.;var sum:=0.;var point:=Vector3.ZERO
				for slot in range(stride):
					var bind: int=joints[v*stride+slot];var weight: float=weights[v*stride+slot]
					if not is_finite(weight) or weight<0 or bind<0 or bind>=palette.size():return {"colliders":[],"reason":"Invalid arm skin row."}
					if weight>maximum:maximum=weight;dominant=bind
					sum+=weight;point+=(palette[bind]*vertices[v])*weight
				if absf(sum-1.)>.001:return {"colliders":[],"reason":"Arm skin weights exceed the supported normalized profile."}
				point=mesh.global_transform*point
				if not point.is_finite():return {"colliders":[],"reason":"Invalid arm skin position."}
				if dominant<0 or dominant>=ids.size() or not segments.has(ids[dominant]):continue
				var segment: Dictionary=segments[ids[dominant]]
				segment.radius=maxf(segment.radius,point_segment(point,segment.start,segment.finish));segment.vertices+=1;matched+=1
	var colliders: Array=[]
	for id in segments:
		var row: Dictionary=segments[id];var length: float=row.start.distance_to(row.finish)
		# Refuse ambiguous clouds instead of clamping a radius to hide an error.
		if row.vertices<3 or row.radius<=0 or row.radius>length*.75:continue
		var t: Transform3D=row.transform;var local: Vector3=t.affine_inverse()*row.finish
		colliders.append({"binding":{"kind":"bone","id":id},"tail_binding":{"kind":"bone","id":row.finish_id},"shape":"capsule","offset":[0,0,0],"tail":[local.x,local.y,local.z],"radius":row.radius/t.basis.get_scale().x})
	return {"colliders":colliders,"reason":"","inspected_vertices":inspected,"matched_vertices":matched,"runtime_generated":true}
