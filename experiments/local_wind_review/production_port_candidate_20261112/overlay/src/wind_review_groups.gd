extends RefCounted
# Session identities use the source and actual bindings, never display names.
static func rotating(chain: Dictionary) -> Array:
	var joints: Array=chain.get("joints",[])
	return joints if float(chain.get("end_extension",0))>0 else joints.slice(0,maxi(0,joints.size()-1))

static func chain_id(chain: Dictionary,sha: String) -> String:
	var identity: Array=[]
	for joint in chain.get("joints",[]):
		var item: Dictionary=joint.duplicate(true);identity.append(item)
	return JSON.stringify({"source":sha,"joints":identity,"center":chain.get("center",{}),"end_extension":chain.get("end_extension",0)},"",true,true).sha256_text()

static func parents(actor: RefCounted) -> Dictionary:
	var result:={}
	for id in actor.order:result[id]=actor.parent_id(id)
	return result

static func mesh_nodes(root: Node,excluded: Array=[]) -> Array:
	var result: Array=[];var pending: Array=[root]
	while not pending.is_empty():
		var node: Node=pending.pop_back()
		if node!=root and node in excluded:continue
		if node is MeshInstance3D and node.mesh:result.append(node)
		pending.append_array(node.get_children())
	return result

static func influences(id: String,owner: Dictionary,parent_ids: Dictionary) -> Array:
	var found: Array=[];var seen:={};var at:=id
	while not at.is_empty() and at!="@root" and not seen.has(at) and seen.size()<512:
		seen[at]=true
		if owner.has(at) and not owner[at] in found:found.append(owner[at])
		at=parent_ids.get(at,"")
	return found

static func vertex_links(actor: RefCounted,chains: Array,parent_ids: Dictionary,excluded: Array=[]) -> Dictionary:
	var owner:={};var links:={};var total:=0
	for i in range(chains.size()):
		for joint in rotating(chains[i]):owner[str(joint.binding.id)]=i
	for mesh in mesh_nodes(actor.root,excluded):
		if not mesh.skin:continue
		var skeleton=mesh.get_node_or_null(mesh.skeleton)
		if not skeleton is Skeleton3D:return {"error":"A weighted surface has no live skeleton."}
		var ids: Array=[]
		for i in range(mesh.skin.get_bind_count()):
			var name: String=mesh.skin.get_bind_name(i);var bone: int=skeleton.find_bone(name) if not name.is_empty() else mesh.skin.get_bind_bone(i)
			if bone<0 or bone>=skeleton.get_bone_count():return {"error":"A weighted surface has an unresolved bone."}
			ids.append(str(actor.root.get_path_to(skeleton))+"::"+str(skeleton.get_bone_name(bone)))
		for surface in range(mesh.mesh.get_surface_count()):
			var arrays: Array=mesh.mesh.surface_get_arrays(surface)
			var points=arrays[Mesh.ARRAY_VERTEX];var bones=arrays[Mesh.ARRAY_BONES];var weights=arrays[Mesh.ARRAY_WEIGHTS]
			if points==null or bones==null or weights==null:continue
			total+=points.size()
			if total>500000:return {"error":"Weight review exceeds500kvertices."}
			if points.is_empty() or bones.size()!=weights.size() or bones.size() not in [points.size()*4,points.size()*8]:return {"error":"A weighted surface needs a narrower influence review."}
			var slots: int=bones.size()/points.size()
			for v in range(points.size()):
				var touched: Array=[]
				for slot in range(slots):
					var offset:=v*slots+slot
					if float(weights[offset])<=0:continue
					var bind:=int(bones[offset])
					if bind<0 or bind>=ids.size():return {"error":"A weighted surface has an invalid influence."}
					for index in influences(ids[bind],owner,parent_ids):
						if not index in touched:touched.append(index)
				for a in touched:
					for b in touched:
						if a<b:links["%d:%d"%[a,b]]=[a,b]
	return {"error":"","links":links.values(),"vertices":total}

static func root_of(tree: Array,index: int) -> int:
	while tree[index]!=index:index=tree[index]
	return index

static func join(tree: Array,a: int,b: int) -> void:
	var aa:=root_of(tree,a);var bb:=root_of(tree,b)
	tree[maxi(aa,bb)]=mini(aa,bb)

static func valid_chain(chain,collider_count: int) -> bool:
	if not chain is Dictionary or not chain.get("joints") is Array or chain.joints.is_empty() or chain.joints.size()>512 or not chain.get("center") is Dictionary or not chain.get("colliders") is Array:return false
	var extension=chain.get("end_extension")
	if not (extension is int or extension is float) or not is_finite(extension) or extension<0:return false
	for index in chain.colliders:
		if not index is int or index<0 or index>=collider_count:return false
	for joint in chain.joints:
		if not joint is Dictionary or not joint.get("binding") is Dictionary:return false
		var binding: Dictionary=joint.binding
		if not binding.get("kind") in ["bone","node","offset"]:return false
		if binding.kind in ["bone","offset"] and (not binding.get("id") is String or binding.id.is_empty()):return false
		if binding.kind=="node" and (not binding.get("path") is String or binding.path.is_empty()):return false
		for key in ["stiffness","drag","gravity","radius"]:
			var value=joint.get(key)
			if not (value is int or value is float) or not is_finite(value):return false
		if not joint.get("gravity_direction") is Array or joint.gravity_direction.size()!=3:return false
		for value in joint.gravity_direction:
			if not (value is int or value is float) or not is_finite(value):return false
	return true

static func build(definition: Dictionary,sha: String,parent_ids: Dictionary={},links: Array=[]) -> Dictionary:
	if sha.length()!=64 or not sha.is_valid_hex_number(false) or not definition.get("error","").is_empty() or not definition.get("chains") is Array or not definition.get("colliders") is Array or definition.chains.size()>128:return {"error":"No validated motion groups are available."}
	var chains: Array=definition.chains;var tree: Array=[];var ids: Array=[];var owner:={};var seen:={}
	for i in range(chains.size()):
		if not valid_chain(chains[i],definition.colliders.size()) or rotating(chains[i]).is_empty():return {"error":"A motion group has no valid rotating joints."}
		var id:=chain_id(chains[i],sha)
		if seen.has(id):return {"error":"Repeated motion group identity."}
		seen[id]=true;ids.append(id);tree.append(i)
		for joint in rotating(chains[i]):
			var binding=joint.get("binding",{})
			if binding.get("kind","")!="bone" or str(binding.get("id","")).is_empty() or owner.has(binding.id):return {"error":"Motion groups need unique validated rotating bones."}
			owner[binding.id]=i
			if owner.size()>512:return {"error":"Motion review exceeds512 rotating joints."}
	for i in range(chains.size()):
		for joint in rotating(chains[i]):
			for other in influences(str(joint.binding.id),owner,parent_ids):join(tree,i,int(other))
	for pair in links:
		if not pair is Array or pair.size()!=2 or not pair[0] is int or not pair[1] is int or pair[0]<0 or pair[0]>=chains.size() or pair[1]<0 or pair[1]>=chains.size():return {"error":"Invalid linked motion groups."}
		join(tree,pair[0],pair[1])
	var members:={}
	for i in range(chains.size()):
		var key:=root_of(tree,i)
		if not members.has(key):members[key]=[]
		members[key].append(i)
	var groups: Array=[]
	for indices in members.values():
		var keys: Array=[];var bones: Array=[];var names: Array=[]
		for index in indices:
			keys.append(ids[index]);names.append(str(chains[index].get("name","Spring")))
			for joint in rotating(chains[index]):bones.append(str(joint.binding.id))
		keys.sort()
		groups.append({"id":JSON.stringify(keys).sha256_text(),"chain_indices":indices,"chain_ids":keys,"rotating_ids":bones,"names":names,"linked":indices.size()>1})
	return {"error":"","source_sha256":sha,"groups":groups,"chain_ids":ids,"definition":definition.duplicate(true)}

static func filter(catalog: Dictionary,selected: Array) -> Dictionary:
	if not catalog.get("error","").is_empty() or not catalog.has("definition"):return {"error":"Motion review is unavailable."}
	if catalog.get("chain_ids",[]).size()!=catalog.definition.chains.size():return {"error":"Motion review changed."}
	for i in range(catalog.definition.chains.size()):
		if not valid_chain(catalog.definition.chains[i],catalog.definition.colliders.size()) or chain_id(catalog.definition.chains[i],catalog.source_sha256)!=catalog.chain_ids[i]:return {"error":"Motion review changed."}
	var available:={};var indices:={};var seen:={}
	for group in catalog.groups:available[group.id]=group
	for id in selected:
		if not id is String or not available.has(id) or seen.has(id):return {"error":"The checked motion groups no longer match this source."}
		seen[id]=true
		for index in available[id].chain_indices:indices[int(index)]=true
	var result: Dictionary=catalog.definition.duplicate(true);result.chains=[]
	for i in range(catalog.definition.chains.size()):
		if indices.has(i):result.chains.append(catalog.definition.chains[i].duplicate(true))
	return result
