extends RefCounted
# Two immutable imported mesh views, one live MeshInstance. Original weights are
# used only at exact guide rest; derived FK/contact always uses the flexible view.
const KEY:="has_secondary_rest_views_1"
const FORMAT:="studio_secondary_rest_views_1"
const PAIR:="has_reconstructed_rest_pair_1"
const Bounds=preload("res://src/pose_bounds.gd")
const SKIN_ATTRIBUTES=["JOINTS_0","WEIGHTS_0","JOINTS_1","WEIGHTS_1"]
var _actor: WeakRef
var _root_id:=0
var _rows: Array=[]
var _connections: Array=[]
var _leases: Dictionary={}
var _next_token:=0
var _disposed:=false
var _invalidated:=false
var stats:={"inventory_array_reads":0,"guide_checks":0,"transitions":0,"rest_meshes":0,"flex_meshes":0}

static func whole(value,limit: int) -> bool:
	return (value is int or value is float) and is_finite(value) and value==floor(value) and value>=0 and value<limit

static func instance(state: GLTFState,scene: Node3D,node_index: int) -> MeshInstance3D:
	var nodes:=state.get_nodes();var source: GLTFNode=nodes[node_index]
	if source.mesh<0 or source.mesh>=state.get_meshes().size():return null
	var expected: ArrayMesh=state.get_meshes()[source.mesh].mesh.get_mesh();var matches: Array=[]
	for value in scene.find_children("*","MeshInstance3D",true,false):
		var mesh: MeshInstance3D=value
		if mesh.mesh==expected and (mesh.get_meta("has_shape_source_node",-1)==node_index or str(mesh.name)==source.resource_name):matches.append(mesh)
	return matches[0] if matches.size()==1 else null

static func compatible(a: MeshInstance3D,b: MeshInstance3D) -> String:
	if not a.mesh is ArrayMesh or not b.mesh is ArrayMesh or a.skin==null or b.skin==null:return "Reconstructed rest view needs explicit ArrayMesh and Skin resources."
	if a.skin.get_bind_count()!=b.skin.get_bind_count():return "Reconstructed rest view changed skin slots."
	for i in range(a.skin.get_bind_count()):
		if a.skin.get_bind_name(i)!=b.skin.get_bind_name(i) or a.skin.get_bind_bone(i)!=b.skin.get_bind_bone(i) or a.skin.get_bind_pose(i)!=b.skin.get_bind_pose(i):return "Reconstructed rest view changed a skin binding."
	if a.mesh.get_surface_count()!=b.mesh.get_surface_count() or a.mesh.get_blend_shape_count()!=b.mesh.get_blend_shape_count() or a.mesh.blend_shape_mode!=b.mesh.blend_shape_mode:return "Reconstructed rest view changed surface or expression layout."
	for i in range(a.mesh.get_blend_shape_count()):
		if a.mesh.get_blend_shape_name(i)!=b.mesh.get_blend_shape_name(i):return "Reconstructed rest view changed expression identity."
	for s in range(a.mesh.get_surface_count()):
		if a.mesh.surface_get_primitive_type(s)!=b.mesh.surface_get_primitive_type(s):return "Reconstructed rest view changed primitive topology."
		var aa: Array=a.mesh.surface_get_arrays(s);var bb: Array=b.mesh.surface_get_arrays(s)
		for slot in range(Mesh.ARRAY_MAX):
			if slot in [Mesh.ARRAY_BONES,Mesh.ARRAY_WEIGHTS]:continue
			if aa[slot]!=bb[slot]:return "Reconstructed rest view changed non-skin geometry."
		if a.mesh.surface_get_blend_shape_arrays(s)!=b.mesh.surface_get_blend_shape_arrays(s):return "Reconstructed rest view changed expression geometry."
	return ""

static func repack(bytes: PackedByteArray,data: Dictionary) -> Dictionary:
	var offset: int=20+int(bytes.decode_u32(12))
	if offset+8>bytes.size() or bytes.decode_u32(offset+4)!=0x004e4942 or int(bytes.decode_u32(offset))+offset+8!=bytes.size():return {"error":"Reconstructed rest view needs one embedded BIN chunk."}
	var encoded:=JSON.stringify(data,"",true,true).to_utf8_buffer()
	if encoded.size()>16*1024*1024:return {"error":"Reconstructed rest metadata exceeds its import budget."}
	while encoded.size()%4:encoded.append(32)
	var binary:=bytes.slice(offset+8);var result:=PackedByteArray();result.resize(20)
	result.encode_u32(0,0x46546c67);result.encode_u32(4,2);result.encode_u32(8,28+encoded.size()+binary.size());result.encode_u32(12,encoded.size());result.encode_u32(16,0x4e4f534a);result.append_array(encoded)
	var header:=PackedByteArray();header.resize(8);header.encode_u32(0,binary.size());header.encode_u32(4,0x004e4942);result.append_array(header);result.append_array(binary)
	return {"bytes":result}

static func attach(data: Dictionary,bytes: PackedByteArray,state: GLTFState,scene: Node3D) -> Dictionary:
	var extras=data.get("extras",{})
	if not extras is Dictionary or not extras.has(KEY):return {"meshes":0}
	var declaration=extras[KEY]
	if not declaration is Dictionary or declaration.get("format")!=FORMAT or not declaration.get("surfaces") is Array or declaration.surfaces.is_empty() or declaration.surfaces.size()>128:return {"error":"Invalid reconstructed rest-view declaration."}
	var patched: Dictionary=data.duplicate(true);var meshes=data.get("meshes",[]);var nodes=data.get("nodes",[]);var accessors=data.get("accessors",[]);var affected: Dictionary={};var seen: Dictionary={}
	for entry in declaration.surfaces:
		if not entry is Dictionary or not whole(entry.get("node"),nodes.size()) or not whole(entry.get("mesh"),meshes.size()):return {"error":"Invalid reconstructed rest surface identity."}
		var ni:=int(entry.node);var mi:=int(entry.mesh)
		if nodes[ni].get("mesh",-1)!=mi or not whole(nodes[ni].get("skin"),data.get("skins",[]).size()) or not whole(entry.get("primitive"),meshes[mi].get("primitives",[]).size()):return {"error":"Reconstructed rest surface lost its mesh or skin."}
		var users:=0
		for node in nodes:
			if node.get("mesh",-1)==mi:users+=1
		if users!=1:return {"error":"Shared reconstructed meshes need separate instance ownership."}
		var pi:=int(entry.primitive);var key: String=str(mi)+":"+str(pi)
		if seen.has(key):return {"error":"Repeated reconstructed rest surface."}
		seen[key]=true
		var attrs=entry.get("attributes");var guides=entry.get("helper_nodes")
		if not attrs is Dictionary or not attrs.has("JOINTS_0") or not attrs.has("WEIGHTS_0") or attrs.has("JOINTS_1")!=attrs.has("WEIGHTS_1") or not guides is Array or guides.is_empty() or guides.size()>512:return {"error":"Invalid reconstructed rest attributes or guides."}
		var primitive: Dictionary=patched.meshes[mi].primitives[pi]
		for name in SKIN_ATTRIBUTES:primitive.attributes.erase(name)
		for name in attrs:
			if not name in SKIN_ATTRIBUTES or not whole(attrs[name],accessors.size()):return {"error":"Invalid original reconstructed weight accessor."}
			var accessor: Dictionary=accessors[int(attrs[name])]
			if accessor.get("type")!="VEC4" or accessor.get("count")!=accessors[int(primitive.attributes.POSITION)].get("count"):return {"error":"Original reconstructed weights do not match the surface."}
			primitive.attributes[name]=int(attrs[name])
		if not affected.has(ni):affected[ni]={"guides":{}}
		var skin: Dictionary=data.skins[int(nodes[ni].skin)]
		for guide in guides:
			if not whole(guide,nodes.size()) or not guide in skin.get("joints",[]):return {"error":"Reconstructed guide lost its original skin identity."}
			affected[ni].guides[int(guide)]=true
	patched.extras.erase(KEY)
	var packed:=repack(bytes,patched)
	if packed.has("error"):return packed
	var document:=GLTFDocument.new();var auxiliary:=GLTFState.new();var issue:=document.append_from_buffer(packed.bytes,"",auxiliary)
	if issue!=OK:return {"error":"Original rest-weight import failed: "+error_string(issue)}
	preload("res://src/source_shape.gd").mark(auxiliary)
	var hidden: Node3D=document.generate_scene(auxiliary)
	if hidden==null:return {"error":"Original rest-weight import produced no scene."}
	var prepared: Array=[];var error:=""
	for ni in affected:
		var live: MeshInstance3D=instance(state,scene,int(ni));var rest: MeshInstance3D=instance(auxiliary,hidden,int(ni))
		if live==null or rest==null:error="Cannot uniquely bind the reconstructed rest mesh.";break
		error=compatible(live,rest)
		if not error.is_empty():break
		# Keep exactly the already-corrected source material resources/order. The
		# auxiliary import supplies geometry only, never its duplicate materials.
		for s in range(live.mesh.get_surface_count()):rest.mesh.surface_set_material(s,live.mesh.surface_get_material(s))
		prepared.append({"mesh":live,"pair":{"format":FORMAT,"flex":live.mesh,"rest":rest.mesh,"guide_nodes":affected[ni].guides.keys()}})
	hidden.free()
	if not error.is_empty():return {"error":error}
	for row in prepared:row.mesh.set_meta(PAIR,row.pair)
	return {"meshes":prepared.size()}

func _source_changed() -> void:_invalidated=true

static func create(actor: RefCounted) -> Dictionary:
	var result=new();result._actor=weakref(actor);result._root_id=actor.root.get_instance_id();var bindings: Dictionary=actor.root.get_meta("has_source_bones",{})
	for item in actor.root.find_children("*","MeshInstance3D",true,false):
		var mesh: MeshInstance3D=item
		if not mesh.has_meta(PAIR):continue
		var pair=mesh.get_meta(PAIR)
		if not pair is Dictionary or pair.get("format")!=FORMAT or not pair.get("rest") is ArrayMesh or not pair.get("flex") is ArrayMesh or not pair.get("guide_nodes") is Array or mesh.mesh not in [pair.rest,pair.flex]:result.dispose();return {"error":"Reconstructed mesh pair changed before model inventory."}
		var sk: Skeleton3D=mesh.get_node_or_null(mesh.skeleton)
		if sk==null or mesh.skin==null:result.dispose();return {"error":"Reconstructed mesh lost its registered skeleton."}
		var wanted: Dictionary={};var positive: Dictionary={}
		for node in pair.guide_nodes:
			var id: String=bindings.get(int(node),"")
			if not actor.bones.has(id):result.dispose();return {"error":"Reconstructed guide is not a model bone."}
			wanted[id]=true
		for s in range(pair.flex.get_surface_count()):
			var arrays: Array=pair.flex.surface_get_arrays(s);result.stats.inventory_array_reads+=1
			var bones: PackedInt32Array=arrays[Mesh.ARRAY_BONES];var weights: PackedFloat32Array=arrays[Mesh.ARRAY_WEIGHTS]
			if bones.size()!=weights.size():result.dispose();return {"error":"Reconstructed flexible skin arrays are inconsistent."}
			for slot in range(bones.size()):
				if weights[slot]<=0.:continue
				var bind: int=bones[slot]
				if bind<0 or bind>=mesh.skin.get_bind_count():result.dispose();return {"error":"Reconstructed flexible skin bind is missing."}
				var name: String=mesh.skin.get_bind_name(bind);var bone: int=sk.find_bone(name) if not name.is_empty() else mesh.skin.get_bind_bone(bind)
				if bone<0:result.dispose();return {"error":"Reconstructed flexible bone is missing."}
				var id: String=str(actor.root.get_path_to(sk))+"::"+str(sk.get_bone_name(bone))
				if wanted.has(id):positive[id]=true
		# A guide can drive weighted descendants without owning direct weights.
		# Ignore only unused terminal branches, never a generated ancestor.
		for id in positive.keys():
			var parent: String=actor.parent_id(id);var visited: Dictionary={}
			while wanted.has(parent) and not visited.has(parent):
				visited[parent]=true;positive[parent]=true;parent=actor.parent_id(parent)
		var guides: Array=[]
		for id in positive:
			var info: Dictionary=actor.bones[id];var base: Transform3D=info.base
			guides.append({"id":id,"skeleton":weakref(info.skeleton),"index":info.index,"position":base.origin,"rotation":base.basis.get_rotation_quaternion(),"scale":base.basis.get_scale()})
		result._rows.append({"mesh":weakref(mesh),"rest":pair.rest,"flex":pair.flex,"skin":mesh.skin,"skeleton":weakref(sk),"guides":guides})
		for resource in [pair.rest,pair.flex]:
			var watched:=false
			for connection in result._connections:
				if connection.resource.get_ref()==resource:watched=true;break
			if not watched:
				var callback: Callable=result._source_changed;resource.changed.connect(callback);result._connections.append({"resource":weakref(resource),"callback":callback})
	if result._rows.is_empty():result.dispose();return {"control":null}
	return {"control":result}

static func select_clone(source: RefCounted,clone: Node3D) -> String:
	# Thumbnails write clone skeletons directly. Preserve the SOURCE base frames,
	# not the clone's already-requested pose, when deciding exact guide rest.
	var actor: RefCounted=source.get_script().new();actor.root=clone;actor.data=source.data.duplicate(true);actor.order=source.order.duplicate()
	for id in source.order:
		var info: Dictionary=source.bones[id].duplicate();var skeleton=clone.get_node_or_null(NodePath(info.path))
		if not skeleton is Skeleton3D:return "Cannot bind reconstructed thumbnail guides to their clone."
		info.skeleton=skeleton;actor.bones[id]=info
	var made:=create(actor)
	if made.has("error"):return str(made.error)
	if made.control==null:return ""
	var control: RefCounted=made.control;var proposal: Dictionary=control.plan();var error: String=str(proposal.error) if proposal.has("error") else control.commit(proposal)
	control.dispose();return error

func acquire(owner: RefCounted) -> int:
	_next_token+=1;_leases[_next_token]=weakref(owner);return _next_token
func release(token: int) -> void:_leases.erase(token)

func plan() -> Dictionary:
	if _disposed or _invalidated:return {"error":"Reconstructed mesh source changed; reopen the model."}
	var actor: RefCounted=_actor.get_ref()
	if actor==null or not is_instance_valid(actor.root) or actor.root.get_instance_id()!=_root_id:return {"error":"Reconstructed mesh owner changed."}
	for token in _leases.keys():
		if _leases[token].get_ref()==null:_leases.erase(token)
	var changes: Array=[]
	for row in _rows:
		var mesh: MeshInstance3D=row.mesh.get_ref();var skeleton: Skeleton3D=row.skeleton.get_ref()
		if not is_instance_valid(mesh) or not actor.root.is_ancestor_of(mesh) or not is_instance_valid(skeleton) or mesh.skin!=row.skin or mesh.get_node_or_null(mesh.skeleton)!=skeleton or mesh.mesh not in [row.rest,row.flex]:return {"error":"Reconstructed mesh binding changed outside its owner."}
		var rest: bool=_leases.is_empty() and Bounds.final_pose(skeleton).is_empty()
		for guide in row.guides:
			var sk: Skeleton3D=guide.skeleton.get_ref();stats.guide_checks+=1
			if not is_instance_valid(sk) or not actor.bones.has(guide.id) or actor.bones[guide.id].skeleton!=sk or actor.bones[guide.id].index!=guide.index:return {"error":"Reconstructed guide ownership changed."}
			if not Bounds.final_pose(sk).is_empty() or sk.get_bone_pose_position(guide.index)!=guide.position or sk.get_bone_pose_rotation(guide.index)!=guide.rotation or sk.get_bone_pose_scale(guide.index)!=guide.scale:rest=false
		var desired: ArrayMesh=row.rest if rest else row.flex
		if mesh.mesh!=desired:changes.append({"mesh":mesh,"before":mesh.mesh,"after":desired})
	return {"changes":changes}

func commit(proposal: Dictionary) -> String:
	for row in proposal.changes:
		if not is_instance_valid(row.mesh) or row.mesh.mesh!=row.before:return "Reconstructed mesh changed during profile selection."
	for row in proposal.changes:
		var mesh: MeshInstance3D=row.mesh;var blends: Array=[];var overrides: Array=[]
		for i in range(mesh.mesh.get_blend_shape_count()):blends.append(mesh.get_blend_shape_value(i))
		for i in range(mesh.mesh.get_surface_count()):overrides.append(mesh.get_surface_override_material(i))
		var material: Material=mesh.material_override;var overlay: Material=mesh.material_overlay
		mesh.mesh=row.after;mesh.material_override=material;mesh.material_overlay=overlay
		for i in range(overrides.size()):mesh.set_surface_override_material(i,overrides[i])
		for i in range(blends.size()):mesh.set_blend_shape_value(i,float(blends[i]))
		stats.transitions+=1
	stats.rest_meshes=0;stats.flex_meshes=0
	for row in _rows:
		var mesh: MeshInstance3D=row.mesh.get_ref()
		if mesh.mesh==row.rest:stats.rest_meshes+=1
		else:stats.flex_meshes+=1
	return ""

func dispose() -> void:
	if _disposed:return
	_disposed=true;_leases.clear()
	for connection in _connections:
		var resource=connection.resource.get_ref()
		if is_instance_valid(resource) and resource.changed.is_connected(connection.callback):resource.changed.disconnect(connection.callback)
	_connections.clear();_rows.clear()
