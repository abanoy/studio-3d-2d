extends RefCounted
# Importer identities, never original display-name guesses. All state is per scene.
const META:="has_source_shape_1"
const NODE_META:="has_shape_source_node"

static func enabled(data: Dictionary) -> bool:
	return data.get("metadata",{}).get("source_shape",{}).get("enabled",false)

static func setting(data: Dictionary) -> Dictionary:
	return data.get("metadata",{}).get("source_shape",{"format":"studio_source_shape_1","enabled":false})

static func index_key(key,limit: int) -> bool:
	return key is String and key.is_valid_int() and str(key.to_int())==key and key.to_int()>=0 and key.to_int()<limit

static func validate(value) -> String:
	if not value is Dictionary or not value.get("format") in ["studio_source_shape_1","studio_source_shape_2"] or not value.get("enabled") is bool:return "Invalid imported shape setting."
	var overrides=value.get("overrides",{})
	if not overrides is Dictionary or overrides.size()>2048 or value.format=="studio_source_shape_1" and not overrides.is_empty():return "Invalid base shape adjustments."
	var total:=0
	for node in overrides:
		if not index_key(node,100000) or not overrides[node] is Dictionary:return "Invalid adjusted shape part."
		for index in overrides[node]:
			var weight=overrides[node][index];total+=1
			if total>2048 or not index_key(index,2048) or not (weight is int or weight is float) or not is_finite(float(weight)) or absf(float(weight))>100:return "Invalid or excessive base shape amount."
	return ""

static func mark(state: GLTFState) -> void:
	var nodes:=state.get_nodes()
	for i in range(nodes.size()):
		# Retain the exact source identity on surviving generated nodes as well as
		# meshes. GLTFState's scene-node table may contain discarded placeholders.
		nodes[i].set_meta(NODE_META,i)

static func capture(data: Dictionary,state: GLTFState,scene: Node) -> Dictionary:
	var result:={"rows":[],"error":"","applied":null}
	var nodes:=state.get_nodes();var resources:=state.get_meshes()
	var meshes: Array=scene.find_children("*","MeshInstance3D",true,false)
	if scene is MeshInstance3D:meshes.push_front(scene)
	var active:={};var scenes: Array=data.get("scenes",[]);var pending: Array=[]
	if not scenes.is_empty():pending=scenes[int(data.get("scene",0))].get("nodes",[]).duplicate()
	while not pending.is_empty():
		var i:=int(pending.pop_back())
		if active.has(i):continue
		active[i]=true
		for child in data.nodes[i].get("children",[]):pending.append(child)
	var claimed:={}
	for i in range(nodes.size()):
		var source: GLTFNode=nodes[i]
		if source.mesh<0 or not active.has(i):continue
		var resource: GLTFMesh=resources[source.mesh]
		var count: int=resource.mesh.get_blend_shape_count()
		if count==0:continue
		if count>2048:result.error="Imported shapes exceed2048 targets per mesh.";return result
		var expected: ArrayMesh=resource.mesh.get_mesh();var candidates: Array=[]
		for mesh in meshes:
			if mesh.mesh==expected and mesh.get_meta(NODE_META,-1)==i:candidates.append(mesh)
		# A skinned source node with children has a placeholder plus a reparented
		# mesh. The importer gives the mesh its unique GLTFNode resource_name.
		if candidates.is_empty():
			for mesh in meshes:
				if mesh.mesh==expected and str(mesh.name)==source.resource_name:candidates.append(mesh)
		if candidates.size()!=1 or claimed.has(candidates[0]):
			result.error="Cannot identify an imported shape's mesh instance. Its neutral appearance is still available.";return result
		var mesh: MeshInstance3D=candidates[0];claimed[mesh]=true
		var raw: Dictionary=data.meshes[source.mesh]
		var weights=data.nodes[i].get("weights",raw.get("weights",[]))
		if not data.nodes[i].has("weights") and not raw.has("weights"):weights=[];weights.resize(count);weights.fill(0.)
		if not weights is Array or weights.size()!=count:
			result.error="Imported shape weights do not match the mesh.";return result
		for primitive in raw.primitives:
			if primitive.get("targets",[]).size()!=count:result.error="Imported shape target counts are inconsistent.";return result
		for weight in weights:
			if not (weight is float or weight is int) or not is_finite(float(weight)) or absf(float(weight))>100:
				result.error="Imported shape weight is invalid or outside the supported range.";return result
		var names:=[]
		for index in range(count):names.append(str(mesh.mesh.get_blend_shape_name(index)))
		result.rows.append({"node":i,"name":str(data.nodes[i].get("name","Part "+str(i))).left(200),"names":names,"mesh":mesh,"weights":weights.duplicate(),"original_aabb":mesh.custom_aabb})
	return result

static func configuration(value) -> Dictionary:
	return {"format":"studio_source_shape_1","enabled":value} if value is bool else value

static func effective(row: Dictionary,config: Dictionary) -> Array:
	var weights: Array=row.weights.duplicate()
	if not config.enabled:weights.fill(0.)
	for index in config.get("overrides",{}).get(str(row.node),{}):weights[int(index)]=float(config.overrides[str(row.node)][index])
	return weights

static func check(root: Node,value) -> String:
	var config:=configuration(value);var error:=validate(config)
	if not error.is_empty():return error
	var descriptor: Dictionary=root.get_meta(META,{"rows":[],"error":""})
	if descriptor.get("checked_setting")==config:return ""
	if (config.enabled or not config.get("overrides",{}).is_empty()) and not descriptor.error.is_empty():return descriptor.error
	var by_node:={}
	for row in descriptor.rows:by_node[str(row.node)]=row
	for node in config.get("overrides",{}):
		if not by_node.has(node):return "A base shape adjustment refers to a missing model part."
		for index in config.overrides[node]:
			if int(index)>=by_node[node].weights.size():return "A base shape adjustment refers to a missing shape."
	# Prepare the complete candidate before replacing cached geometry. Failed edits
	# must not invalidate the currently applied shape or a later Undo.
	var prepared:=[]
	var operations:=0
	for row in descriptor.rows:
		var weights:=effective(row,config)
		var candidate:={"row":row,"weights":weights,"surfaces":[],"bounds":row.original_aabb}
		prepared.append(candidate)
		if not weights.any(func(weight):return weight!=0.):continue
		var mesh: ArrayMesh=row.mesh.mesh;var bounds:=AABB();var started:=false
		for surface in range(mesh.get_surface_count()):
			var vertices: PackedVector3Array=mesh.surface_get_arrays(surface)[Mesh.ARRAY_VERTEX]
			var targets: Array=mesh.surface_get_blend_shape_arrays(surface);var active:=0
			for weight in weights:active+=int(weight!=0.)
			operations+=vertices.size()*active
			if vertices.size()*active>2000000 or operations>8000000:return "Imported shape bounds exceed the supported evaluation budget."
			if active==0:continue
			for index in range(weights.size()):
				var weight:=float(weights[index])
				if weight==0:continue
				var shape: PackedVector3Array=targets[index][Mesh.ARRAY_VERTEX]
				if shape.size()!=vertices.size():return "Imported shape vertices do not match the mesh."
				var base: PackedVector3Array=mesh.surface_get_arrays(surface)[Mesh.ARRAY_VERTEX]
				for v in range(vertices.size()):vertices[v]+=weight*(shape[v]-base[v]) if mesh.blend_shape_mode==Mesh.BLEND_SHAPE_MODE_NORMALIZED else weight*shape[v]
			for point in vertices:
				if not point.is_finite() or maxf(absf(point.x),maxf(absf(point.y),absf(point.z)))>100000:return "Imported shape produces invalid bounds."
				bounds=bounds.expand(point) if started else AABB(point,Vector3.ZERO);started=true
			candidate.surfaces.append(vertices)
		candidate.bounds=bounds.grow(.001) if started else row.original_aabb
	descriptor["prepared"]=prepared;descriptor["checked_setting"]=config.duplicate(true)
	return ""

static func apply(root: Node,value) -> void:
	var config:=configuration(value)
	var descriptor: Dictionary=root.get_meta(META,{"rows":[],"applied":null})
	if descriptor.applied==config and not descriptor.get("dynamic",false):return
	var error:=check(root,config)
	if not error.is_empty():push_error(error);return
	for prepared in descriptor.get("prepared",[]):
		var row: Dictionary=prepared.row
		if row.mesh.has_meta("has_animated_shape_weights"):row.mesh.remove_meta("has_animated_shape_weights")
		for i in range(prepared.weights.size()):row.mesh.set_blend_shape_value(i,float(prepared.weights[i]))
		row.mesh.custom_aabb=prepared.bounds
		if prepared.bounds.size.length_squared()>0:row.mesh.set_meta("has_shape_bounds",prepared.bounds)
		elif row.mesh.has_meta("has_shape_bounds"):row.mesh.remove_meta("has_shape_bounds")
		if not prepared.surfaces.is_empty():row.mesh.set_meta("has_shape_vertices",prepared.surfaces)
		elif row.mesh.has_meta("has_shape_vertices"):row.mesh.remove_meta("has_shape_vertices")
	descriptor.applied=config.duplicate(true)
	descriptor["dynamic"]=false;descriptor["dynamic_setting"]=null

static func dynamic_surface(row: Dictionary,surface: int,weights: Array) -> Dictionary:
	if not row.has("raw_surfaces"):row["raw_surfaces"]={}
	var mesh: ArrayMesh=row.mesh.mesh
	if not row.raw_surfaces.has(surface):
		var base: PackedVector3Array=mesh.surface_get_arrays(surface)[Mesh.ARRAY_VERTEX]
		var bounds:=AABB();var started:=false
		for point in base:bounds=bounds.expand(point) if started else AABB(point,Vector3.ZERO);started=true
		row.raw_surfaces[surface]={"base":base,"bounds":bounds,"targets":{},"extents":{}}
	var raw: Dictionary=row.raw_surfaces[surface];var missing:=false
	for i in range(weights.size()):
		if weights[i]!=0 and not raw.targets.has(i):missing=true
	if missing:
		# Fetch the engine arrays only on first use of a channel. Keep only needed
		# channels, rather than duplicating hundreds of unused native targets.
		var targets: Array=mesh.surface_get_blend_shape_arrays(surface)
		for i in range(weights.size()):
			if weights[i]==0 or raw.targets.has(i):continue
			var positions: PackedVector3Array=targets[i][Mesh.ARRAY_VERTEX]
			if positions.size()!=raw.base.size():return {"error":"Animated shape vertices do not match the mesh."}
			var delta:=AABB();var started:=false
			for v in range(positions.size()):
				var point: Vector3=positions[v]-raw.base[v] if mesh.blend_shape_mode==Mesh.BLEND_SHAPE_MODE_NORMALIZED else positions[v]
				if not point.is_finite():return {"error":"Animated shape contains invalid geometry."}
				delta=delta.expand(point) if started else AABB(point,Vector3.ZERO);started=true
			raw.targets[i]=positions;raw.extents[i]=delta
	return raw

static func dynamic_plan(root: Node,config: Dictionary) -> Dictionary:
	var error:=validate(config)
	if not error.is_empty():return {"error":error}
	var descriptor: Dictionary=root.get_meta(META,{"rows":[],"error":""});var by_node:={};var prepared:=[];var operations:=0
	if not descriptor.error.is_empty():return {"error":descriptor.error}
	for row in descriptor.rows:by_node[str(row.node)]=row
	for node in config.get("overrides",{}):
		if not by_node.has(node):return {"error":"An animated shape refers to a missing part."}
		for index in config.overrides[node]:
			if int(index)>=by_node[node].weights.size():return {"error":"An animated shape refers to a missing channel."}
	for row in descriptor.rows:
		var weights:=effective(row,config);var active:=0
		for weight in weights:active+=int(weight!=0.)
		var bounds:=AABB();var started:=false
		if active==0:bounds=row.mesh.get_aabb()
		else:
			for surface in range(row.mesh.mesh.get_surface_count()):
				var raw:=dynamic_surface(row,surface,weights)
				if raw.has("error"):return raw
				operations+=raw.base.size()*active
				if raw.base.size()*active>2000000 or operations>8000000:return {"error":"Animated shape exceeds the supported evaluation budget."}
				var lower: Vector3=raw.bounds.position;var upper: Vector3=raw.bounds.end
				for i in range(weights.size()):
					var weight:=float(weights[i])
					if weight==0:continue
					var delta: AABB=raw.extents[i]
					lower+=(delta.position if weight>0 else delta.end)*weight
					upper+=(delta.end if weight>0 else delta.position)*weight
				if not lower.is_finite() or not upper.is_finite():return {"error":"Invalid animated shape bounds."}
				for point in [lower,upper]:
					if maxf(absf(point.x),maxf(absf(point.y),absf(point.z)))>100000:return {"error":"Animated shape exceeds supported bounds."}
				var box:=AABB(lower,upper-lower);bounds=bounds.merge(box) if started else box;started=true
		prepared.append({"row":row,"weights":weights,"bounds":bounds.grow(.001)})
	return {"rows":prepared}

static func apply_dynamic(root: Node,base: Dictionary,values: Dictionary) -> void:
	var descriptor: Dictionary=root.get_meta(META)
	if descriptor.applied!=base:apply(root,base)
	var config:=base.duplicate(true);config.format="studio_source_shape_2";config["overrides"]=config.get("overrides",{}).duplicate(true)
	for node in values:
		if not config.overrides.has(node):config.overrides[node]={}
		for index in values[node]:config.overrides[node][index]=values[node][index]
	if descriptor.get("dynamic_setting")==config:return
	var plan:=dynamic_plan(root,config)
	if plan.has("error"):push_error(plan.error);return
	for candidate in plan.rows:
		var row: Dictionary=candidate.row
		for i in range(candidate.weights.size()):row.mesh.set_blend_shape_value(i,candidate.weights[i])
		row.mesh.custom_aabb=candidate.bounds;row.mesh.set_meta("has_shape_bounds",candidate.bounds)
		row.mesh.set_meta("has_animated_shape_weights",candidate.weights)
		row.mesh.set_meta("has_animated_shape_sources",row.get("raw_surfaces",{}))
		row.mesh.set_meta("has_animated_shape_relative",row.mesh.mesh.blend_shape_mode==Mesh.BLEND_SHAPE_MODE_RELATIVE)
		if row.mesh.has_meta("has_shape_vertices"):row.mesh.remove_meta("has_shape_vertices")
	descriptor["dynamic"]=true;descriptor["dynamic_setting"]=config.duplicate(true)

static func mesh_bounds(mesh: MeshInstance3D) -> AABB:
	return mesh.get_meta("has_shape_bounds",mesh.get_aabb())

static func vertices(mesh: MeshInstance3D,surface: int,fallback: PackedVector3Array) -> PackedVector3Array:
	if mesh.has_meta("has_animated_shape_weights"):
		var sources: Dictionary=mesh.get_meta("has_animated_shape_sources",{})
		if not sources.has(surface):return fallback
		var cached: Dictionary=mesh.get_meta("has_animated_shape_vertices",{})
		var weights: Array=mesh.get_meta("has_animated_shape_weights")
		if cached.get("weights")!=weights:cached={"weights":weights,"surfaces":{}};mesh.set_meta("has_animated_shape_vertices",cached)
		if not cached.surfaces.has(surface):
			var raw: Dictionary=sources[surface];var positions: PackedVector3Array=raw.base.duplicate()
			for i in range(weights.size()):
				if weights[i]==0:continue
				var target: PackedVector3Array=raw.targets[i]
				for v in range(positions.size()):positions[v]+=float(weights[i])*(target[v] if mesh.get_meta("has_animated_shape_relative") else target[v]-raw.base[v])
			cached.surfaces[surface]=positions
		return cached.surfaces[surface]
	var surfaces: Array=mesh.get_meta("has_shape_vertices",[])
	return surfaces[surface] if surface<surfaces.size() else fallback

static func snapshot(root: Node) -> Dictionary:
	var result:={}
	for row in root.get_meta(META,{"rows":[]}).rows:
		var values:=[];var nonzero:=false
		for i in range(row.weights.size()):
			var weight: float=row.mesh.get_blend_shape_value(i);values.append(weight);nonzero=nonzero or weight!=0.
		if nonzero:result[str(row.node)]=values
	return result
