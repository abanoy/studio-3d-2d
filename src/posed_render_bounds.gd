extends RefCounted
# Cached per-instance render bounds refreshed by Model and final-pose writers.
# SourceShape retains sole ownership of custom_aabb and morph-bound metadata.
const Bounds=preload("res://src/pose_bounds.gd")
const Envelope=preload("res://src/posed_render_envelope.gd")
const MAX_MESHES:=256
const MAX_VERTICES:=200000
const MAX_BINDS:=512
var _rows: Array=[]
var _connections: Array=[]
var _invalidated:=false
var _disposed:=false
var stats:={"inventory_array_reads":0,"inventory_vertices":0,"refreshes":0,"cache_hits":0,"computed_meshes":0,"margin_writes":0,"palette_entries":0,"hot_array_reads":0}

func _source_changed() -> void:_invalidated=true

static func create(meshes: Array) -> Dictionary:
	if meshes.size()>MAX_MESHES:return {"error":"Render bounds exceed the mesh inventory limit."}
	var result=new();var seen:={};var pending:=[]
	for value in meshes:
		if not is_instance_valid(value) or not value is MeshInstance3D or value.mesh==null:return {"error":"Render bounds need valid mesh instances."}
		var mesh: MeshInstance3D=value
		if seen.has(mesh):return {"error":"Render bounds contain a repeated mesh instance."}
		seen[mesh]=true
		var row: Dictionary=result._inspect(mesh)
		if row.has("error"):return row
		pending.append(row)
	# No margin/property writes occur until every selected mesh has passed.
	for row in pending:
		result._rows.append(row)
		for resource in [row.resource,row.skin]:
			if resource==null:continue
			var already:=false
			for connection in result._connections:
				if connection.resource.get_ref()==resource:already=true;break
			if already:continue
			var callback: Callable=result._source_changed
			resource.changed.connect(callback)
			result._connections.append({"resource":weakref(resource),"callback":callback})
	return {"control":result}

func _inspect(mesh: MeshInstance3D) -> Dictionary:
	var intrinsic: AABB=mesh.mesh.get_aabb()
	var engine_intrinsic: AABB=intrinsic
	if not Envelope.finite(intrinsic) or not Envelope.finite(mesh.custom_aabb) or not is_finite(mesh.extra_cull_margin) or mesh.extra_cull_margin<0:return {"error":"Invalid original render bounds or margin."}
	var used:={};var sum_min:=INF;var sum_max:=0.;var unskinned:=false
	var surfaces: int=mesh.mesh.get_surface_count()
	for surface in range(surfaces):
		var arrays: Array=mesh.mesh.surface_get_arrays(surface);stats.inventory_array_reads+=1
		if arrays.size()!=Mesh.ARRAY_MAX or not arrays[Mesh.ARRAY_VERTEX] is PackedVector3Array:return {"error":"Render bounds need readable immutable vertices."}
		var count: int=arrays[Mesh.ARRAY_VERTEX].size();stats.inventory_vertices+=count
		if stats.inventory_vertices>MAX_VERTICES:return {"error":"Render bounds exceed the inventory vertex budget."}
		if count==0:continue
		for point in arrays[Mesh.ARRAY_VERTEX]:
			if not point.is_finite():return {"error":"Render geometry contains a non-finite vertex."}
			intrinsic=intrinsic.expand(point)
		var joints=arrays[Mesh.ARRAY_BONES];var weights=arrays[Mesh.ARRAY_WEIGHTS]
		if not joints is PackedInt32Array or joints.is_empty():
			if weights is PackedFloat32Array and not weights.is_empty():return {"error":"Render weights have no matching joints."}
			unskinned=true;continue
		var stride:=int(joints.size()/count)
		if stride not in [4,8] or joints.size()!=count*stride or not weights is PackedFloat32Array or weights.size()!=joints.size():return {"error":"Invalid render skin weight layout."}
		for vertex in range(count):
			var total:=0.
			for slot in range(stride):
				var weight: float=weights[vertex*stride+slot];var bind: int=joints[vertex*stride+slot]
				if not is_finite(weight) or weight<0:return {"error":"Invalid render skin weight."}
				if weight==0:continue
				if bind<0 or bind>=MAX_BINDS:return {"error":"Invalid render skin bind."}
				total+=weight;used[bind]=true
			if not is_finite(total) or absf(total-1.)>.001:return {"error":"Render skin weights are outside the existing normalized profile."}
			sum_min=minf(sum_min,total);sum_max=maxf(sum_max,total)
	var sk=mesh.get_node_or_null(mesh.skeleton)
	if not used.is_empty() and (not sk is Skeleton3D or mesh.skin==null):return {"error":"Render bounds require an explicit registered skin and skeleton."}
	if mesh.skin!=null:
		if mesh.skin.get_bind_count()>MAX_BINDS:return {"error":"Render bounds exceed the skin bind limit."}
		for bind in used:
			if bind>=mesh.skin.get_bind_count():return {"error":"Render geometry refers to a missing skin bind."}
	var used_binds: Array=used.keys();used_binds.sort()
	return {"mesh":weakref(mesh),"resource":mesh.mesh,"skin":mesh.skin,"skeleton":weakref(sk) if sk is Skeleton3D else null,"skeleton_path":mesh.skeleton,"surface_count":surfaces,"intrinsic":intrinsic,"engine_intrinsic":engine_intrinsic,"original_custom":mesh.custom_aabb,"original_margin":mesh.extra_cull_margin,"used_binds":used_binds,"sum_min":sum_min if not used.is_empty() else 1.,"sum_max":sum_max if not used.is_empty() else 1.,"unskinned":unskinned,"last_signature":[],"published":false,"last_margin":mesh.extra_cull_margin}

func refresh() -> Dictionary:
	if _disposed:return {"error":"Render bounds control has been disposed."}
	if _invalidated:return {"error":"Render source geometry or skin changed; rebuild the control."}
	stats.refreshes+=1
	var context:={"palettes":{},"updated":{},"error":""};var prepared:=[]
	for row in _rows:
		var mesh=row.mesh.get_ref()
		if not is_instance_valid(mesh) or not mesh.is_inside_tree():return {"error":"Render mesh is freed or detached."}
		if mesh.mesh!=row.resource or mesh.skin!=row.skin or mesh.skeleton!=row.skeleton_path or mesh.mesh.get_surface_count()!=row.surface_count:return {"error":"Render mesh binding changed; rebuild the control."}
		if mesh.extra_cull_margin!=row.last_margin:return {"error":"Render margin was changed outside this control."}
		if row.skeleton!=null and (not is_instance_valid(row.skeleton.get_ref()) or mesh.get_node_or_null(mesh.skeleton)!=row.skeleton.get_ref()):return {"error":"Render skeleton identity changed."}
		var input: AABB=row.intrinsic
		if mesh.has_meta("has_shape_bounds"):
			var current=mesh.get_meta("has_shape_bounds")
			if not current is AABB or not Envelope.finite(current):return {"error":"Invalid current morph render bounds."}
			input=current
		var native_box: AABB=mesh.custom_aabb if mesh.custom_aabb.size.length_squared()>0 else row.engine_intrinsic
		if not Envelope.finite(native_box):return {"error":"Invalid current engine render bounds."}
		var palette: Array=Bounds.palette(mesh,context)
		if not context.error.is_empty():return {"error":context.error}
		var transforms: Array=[]
		for bind in row.used_binds:
			if bind>=palette.size():return {"error":"Render palette lost a used bind."}
			transforms.append(palette[bind]);stats.palette_entries+=1
		var signature: Array=[input,native_box,transforms]
		if row.last_signature==signature:stats.cache_hits+=1;continue
		var envelope:=Envelope.calculate(input,transforms,row.sum_min,row.sum_max,row.unskinned)
		if envelope.has("error"):return envelope
		var padding:=Envelope.padding(native_box,envelope.bounds)
		if padding.has("error"):return padding
		# Static/unskinned geometry needs no extra helper margin.
		var margin: float=maxf(row.original_margin,padding.margin) if not transforms.is_empty() else row.original_margin
		prepared.append({"row":row,"mesh":mesh,"signature":signature,"margin":margin,"bounds":envelope.bounds})
	# A failed peer mesh above cannot leave partial bound/property changes.
	for item in prepared:
		item.mesh.extra_cull_margin=item.margin
		item.row.last_margin=item.mesh.extra_cull_margin
		item.row.last_signature=item.signature.duplicate(true);item.row.published=true
		stats.computed_meshes+=1;stats.margin_writes+=1
	return {"updated":prepared.size(),"stats":stats.duplicate(true)}

func dispose() -> void:
	if _disposed:return
	_disposed=true
	for row in _rows:
		var mesh=row.mesh.get_ref()
		if is_instance_valid(mesh) and row.published and mesh.extra_cull_margin==row.last_margin:mesh.extra_cull_margin=row.original_margin
	_disconnect_sources();_rows.clear()

func _disconnect_sources() -> void:
	for connection in _connections:
		var resource=connection.resource.get_ref()
		if is_instance_valid(resource) and resource.changed.is_connected(connection.callback):resource.changed.disconnect(connection.callback)
	_connections.clear()
