extends RefCounted
# Bounded initial placement only. No simulation, source changes or implicit pose keys.
const SceneIO=preload("res://src/scene3d.gd")
const TRIANGLE_BUDGET:=50000

static func local_bounds(node: Node, parent:=Transform3D.IDENTITY) -> AABB:
	var transform: Transform3D=parent*node.transform if node is Node3D else parent
	var bounds: AABB=transform*preload("res://src/source_shape.gd").mesh_bounds(node) if node is MeshInstance3D and node.mesh else AABB()
	for child in node.get_children():
		var other:=local_bounds(child,transform)
		if other.size.length_squared()>0:bounds=other if bounds.size.length_squared()==0 else bounds.merge(other)
	return bounds

static func collect(node: Node, output: Array, stops: Dictionary, start:=true) -> void:
	if not start and stops.has(node):return
	if node is MeshInstance3D and node.mesh and node.is_visible_in_tree():output.append(node)
	for child in node.get_children():collect(child,output,stops,false)

static func in_view(bounds: AABB, context: Dictionary) -> bool:
	var inverse: Transform3D=context.camera.affine_inverse()
	var tangent:=tan(deg_to_rad(float(context.fov)*0.5))*0.95
	for x in [0,1]:
		for y in [0,1]:
			for z in [0,1]:
				var point:=inverse*(bounds.position+bounds.size*Vector3(x,y,z))
				if -point.z<float(context.get("near",0.1)) or -point.z>float(context.get("far",INF)) or absf(point.y)>-point.z*tangent or absf(point.x)>-point.z*tangent*context.aspect:return false
	return true

static func plan(renderer: Node, source: String, context: Dictionary, use_shape=false,root_transform:=Transform3D.IDENTITY) -> Dictionary:
	if not context.get("camera") is Transform3D or not context.camera.is_finite() or absf(context.camera.basis.determinant())<.000001:return {"error":"Import placement needs a valid camera view. Try adding the model again."}
	for field in ["fov","aspect"]:
		if not (context.get(field) is int or context.get(field) is float) or not is_finite(float(context[field])) or float(context[field])<=0:return {"error":"Import placement needs valid camera projection settings. Try adding the model again."}
	var decoded:=SceneIO.load_glb(source)
	if decoded.has("error"):return decoded
	var shape=preload("res://src/source_shape.gd")
	var shape_error: String=shape.check(decoded.scene,use_shape)
	if not shape_error.is_empty():decoded.scene.free();return {"error":shape_error}
	shape.apply(decoded.scene,use_shape)
	var bounds: AABB=root_transform*local_bounds(decoded.scene);decoded.scene.free()
	if not bounds.position.is_finite() or not bounds.size.is_finite() or bounds.size.length()<0.001:
		var near_distance: float=float(context.get("near",0.1));var far_distance: float=float(context.get("far",INF))
		return {"position":context.camera.origin-context.camera.basis.z*clampf(3,near_distance,far_distance),"support":"view","attempts":1,"overlap":false,"triangles":0}
	var camera: Transform3D=context.camera
	var distance:=maxf(4,bounds.size.length()*0.6/sin(deg_to_rad(float(context.fov)*0.4)))
	distance=minf(distance,1500)
	if context.has("near") or context.has("far"):
		var nearest: float=float(context.get("near",0.1));var farthest: float=float(context.get("far",INF))
		var margin:=minf(0.05,(farthest-nearest)*0.05);var lower:=0.;var upper:=INF
		var tangent:=tan(deg_to_rad(float(context.fov)*0.5))*0.95
		for x in [0,1]:
			for y in [0,1]:
				for z in [0,1]:
					var offset: Vector3=camera.basis.inverse()*(bounds.position+bounds.size*Vector3(x,y,z)-bounds.get_center())
					lower=maxf(lower,maxf(nearest+margin+offset.z,offset.z+maxf(absf(offset.y)/tangent,absf(offset.x)/(tangent*float(context.aspect)))))
					upper=minf(upper,farthest-margin+offset.z)
		if upper<lower:return {"error":"This model does not fit between the current view distances. Increase the far distance in Advanced, then import again."}
		distance=clampf(distance,lower,upper)
	var seed: Vector3=camera.origin-camera.basis.z.normalized()*distance
	var step:=maxf(0.5,maxf(bounds.size.x,bounds.size.z)+0.15)
	var radius:=step*3
	var drop:=maxf(8,bounds.size.y*4)
	var region:=AABB(seed-Vector3(radius,drop,radius),Vector3(radius*2,drop+bounds.size.y+1,radius*2))
	var meshes: Array=[];var obstacles: Array[AABB]=[];var stops:={}
	if renderer.world_runtime:
		for instance in renderer.world_runtime.instances.values():stops[instance.root]=true
		for instance in renderer.world_runtime.instances.values():
			if not instance.root.is_visible_in_tree():continue
			if instance.data.kind=="environment":collect(instance.root,meshes,stops)
			elif instance.data.kind=="model":obstacles.append(renderer.scene_bounds(instance.root))
	elif renderer.environment_scene:
		collect(renderer.environment_scene,meshes,{})
		if renderer.model:obstacles.append(renderer.scene_bounds(renderer.model.root))
	var triangles: Array=[];var used:=0;var skipped:=0
	for mesh in meshes:
		if not region.intersects(mesh.global_transform*preload("res://src/source_shape.gd").mesh_bounds(mesh)):continue
		for surface in range(mesh.mesh.get_surface_count()):
			if mesh.mesh.surface_get_primitive_type(surface)!=Mesh.PRIMITIVE_TRIANGLES:continue
			var count: int=mesh.mesh.surface_get_array_index_len(surface)
			if count==0:count=mesh.mesh.surface_get_array_len(surface)
			if count/3>TRIANGLE_BUDGET-used:skipped+=1;continue
			var arrays: Array=mesh.mesh.surface_get_arrays(surface)
			var vertices: PackedVector3Array=preload("res://src/source_shape.gd").vertices(mesh,surface,arrays[Mesh.ARRAY_VERTEX])
			var indices: PackedInt32Array=arrays[Mesh.ARRAY_INDEX] if arrays[Mesh.ARRAY_INDEX] is PackedInt32Array else PackedInt32Array()
			for i in range(0,count-2,3):
				var a: Vector3=mesh.global_transform*vertices[indices[i] if not indices.is_empty() else i]
				var b: Vector3=mesh.global_transform*vertices[indices[i+1] if not indices.is_empty() else i+1]
				var c: Vector3=mesh.global_transform*vertices[indices[i+2] if not indices.is_empty() else i+2]
				var box:=AABB(a,Vector3.ZERO).expand(b).expand(c)
				if region.intersects(box.grow(0.005)):triangles.append({"a":a,"b":b,"c":c,"box":box,"horizontal":absf((b-a).cross(c-a).normalized().y)>0.65})
			used+=count/3
	var right:=Vector3(camera.basis.x.x,0,camera.basis.x.z).normalized()
	if right.length()<0.1:right=Vector3.RIGHT
	var forward:=Vector3(-right.z,0,right.x)
	var offsets:=[Vector2.ZERO,Vector2(1,0),Vector2(-1,0),Vector2(0,1),Vector2(0,-1),Vector2(1,1),Vector2(-1,1),Vector2(1,-1),Vector2(-1,-1)]
	var fallback:={};var attempts:=0
	for offset in offsets:
		attempts+=1
		var center: Vector3=seed+(right*offset.x+forward*offset.y)*step
		var ground: Variant=null
		for triangle in triangles:
			if not triangle.horizontal:continue
			var hit: Variant=Geometry3D.ray_intersects_triangle(center+Vector3.UP*0.05,Vector3.DOWN,triangle.a,triangle.b,triangle.c)
			if hit!=null and center.y-hit.y<=drop and (ground==null or hit.y>ground):ground=hit.y
		var support:="mesh" if ground!=null else "grid"
		var position: Vector3=Vector3(center.x-bounds.get_center().x,(float(ground) if ground!=null else 0)-bounds.position.y,center.z-bounds.get_center().z)
		var placed:=AABB(bounds.position+position,bounds.size)
		if not in_view(placed,context):
			if offset!=Vector2.ZERO:continue
			position=seed-bounds.get_center();placed=AABB(bounds.position+position,bounds.size);support="view"
		var overlap:=false
		for obstacle in obstacles:
			if placed.grow(-0.01).intersects(obstacle):overlap=true;break
		if not overlap:
			for triangle in triangles:
				if not triangle.horizontal and placed.grow(-0.02).intersects(triangle.box.grow(0.005)):overlap=true;break
		var candidate:={"position":position,"support":support,"attempts":attempts,"overlap":overlap,"triangles":used,"skipped_surfaces":skipped}
		if fallback.is_empty():fallback=candidate
		# Keep searching nearby floor-supported positions before choosing the
		# center's visible floating fallback. A later candidate may fit on ground.
		if not overlap and support!="view":return candidate
	fallback["attempts"]=attempts
	return fallback
