extends RefCounted
# Source adapters end here. Consumers use stable HAS bone/path references, not
# ecosystem names or source node indices. No simulation or model edits on load.
const FORMAT="studio_secondary_rig_1"
var error:=""
var nodes: Array=[]
var parents:={}
var bindings:={}
var chains: Array=[]
var colliders: Array=[]
var groups: Array=[]
var owned:={}

func fail(message: String) -> void:
	if error.is_empty():error=message

func array(value,limit: int) -> Array:
	if not value is Array or value.size()>limit:fail("Invalid or excessive secondary rig list.");return []
	return value

func object(value) -> Dictionary:
	if not value is Dictionary:fail("Invalid secondary rig object.");return {}
	return value

func number(value,lo: float,hi: float) -> float:
	if not (value is int or value is float) or not is_finite(float(value)) or value<lo or value>hi:fail("Invalid secondary rig number.");return lo
	return float(value)

func index(value,limit: int) -> int:
	var n:=number(value,0,maxi(0,limit-1))
	if n!=floor(n) or limit==0:fail("Invalid secondary rig index.")
	return int(n)

func vector(value,legacy:=false,flip_z:=false) -> Array:
	var values: Array=[]
	if legacy:
		var d:=object(value);values=[d.get("x",0),d.get("y",0),d.get("z",0)]
	else:
		values=array(value,3)
		if values.size()!=3:fail("Invalid secondary rig vector.");return [0,0,0]
	var result: Array=[]
	for v in values:result.append(number(v,-100000,100000))
	if flip_z:result[2]=-result[2]
	return result

func ref(value) -> Dictionary:
	var i:=index(value,nodes.size())
	if not bindings.has(i):fail("Secondary rig node has no validated runtime binding: "+str(i));return {}
	return bindings[i].duplicate(true)

func settings(value: Dictionary,legacy:=false) -> Dictionary:
	return {"stiffness":number(value.get("stiffiness" if legacy else "stiffness",1.0),0,10000),
		"drag":number(value.get("dragForce",0.4),0,1),"gravity":number(value.get("gravityPower",0.0),0,10000),
		"gravity_direction":vector(value.get("gravityDir",{"x":0,"y":-1,"z":0} if legacy else [0,-1,0]),legacy),
		"radius":number(value.get("hitRadius",0.0),0,1000)}

func selected_colliders(value) -> Array:
	var result: Array=[]
	for entry in array(value,256):
		var i:=index(entry,groups.size())
		if i>=groups.size():continue
		for c in groups[i]:
			if not c in result:result.append(c)
	return result

func add_chain(joints: Array,name: String,center,collision_ids: Array,extension:=0.0) -> void:
	if joints.is_empty() or chains.size()>=128:fail("Invalid or excessive secondary chains.");return
	var seen:={};var last:=-1
	for joint in joints:
		var n: int=joint.source_node
		if seen.has(n):fail("Repeated joint in secondary chain.")
		seen[n]=true
		if last>=0:
			var at: int=parents.get(n,-1);var visited:={}
			while at!=last and at>=0 and not visited.has(at):visited[at]=true;at=parents.get(at,-1)
			if at!=last:fail("Secondary joints do not follow the source hierarchy.")
		last=n
	# VRM1's last joint is a tail only. VRM0 has an extra virtual tail.
	for i in range(joints.size() if extension>0 else joints.size()-1):
		var n: int=joints[i].source_node
		if owned.has(n):fail("Secondary chains share a rotating joint.")
		owned[n]=true
	if owned.size()>512:fail("Secondary rig exceeds512 rotating joints.")
	var anchor: Dictionary={}
	if center!=null and center!=-1:
		anchor=ref(center)
		var first: int=joints[0].source_node;var at:=first;var visited:={}
		while at>=0 and at!=int(center) and not visited.has(at):visited[at]=true;at=parents.get(at,-1)
		if at!=int(center):fail("Secondary center must be an ancestor of its chain.")
	chains.append({"name":name.left(256),"joints":joints,"center":anchor,"colliders":collision_ids,"end_extension":extension})

func parse_v1(native: Dictionary) -> void:
	if native.get("specVersion")!="1.0":fail("Unsupported spring specification version.");return
	for value in array(native.get("colliders",[]),256):
		var c:=object(value);var shape:=object(c.get("shape"));var kind: String="sphere" if shape.has("sphere") else "capsule" if shape.has("capsule") else ""
		if kind.is_empty() or shape.size()!=1:fail("Unsupported secondary collider shape.");continue
		var params:=object(shape[kind]);var row:={"binding":ref(c.get("node")),"shape":kind,"offset":vector(params.get("offset",[0,0,0])),"radius":number(params.get("radius",0),0,1000)}
		if kind=="capsule":row.tail=vector(params.get("tail",[0,0,0]))
		colliders.append(row)
	for value in array(native.get("colliderGroups",[]),256):
		var group: Array=[]
		for entry in array(object(value).get("colliders",[]),256):group.append(index(entry,colliders.size()))
		groups.append(group)
	for value in array(native.get("springs",[]),128):
		var spring:=object(value);var joints: Array=[]
		for item in array(spring.get("joints",[]),512):
			var j:=object(item);var row:=settings(j);row.binding=ref(j.get("node"));row.source_node=index(j.get("node"),nodes.size());joints.append(row)
		if joints.size()<2:fail("A spring chain needs at least two joints.");continue
		add_chain(joints,str(spring.get("name","Spring")),spring.get("center"),selected_colliders(spring.get("colliderGroups",[])))

func parse_v0(native: Dictionary) -> void:
	for value in array(native.get("colliderGroups",[]),256):
		var c:=object(value);var group: Array=[]
		for item in array(c.get("colliders",[]),256):
			if colliders.size()>=256:fail("Secondary rig exceeds256 colliders.");break
			var params:=object(item);group.append(colliders.size())
			# VRM0 collider offsets use the legacy left-handed Z convention.
			colliders.append({"binding":ref(c.get("node")),"shape":"sphere","offset":vector(params.get("offset",{}),true,true),"radius":number(params.get("radius",0),0,1000)})
		groups.append(group)
	for value in array(native.get("boneGroups",[]),128):
		var spring:=object(value);var config:=settings(spring,true)
		for root in array(spring.get("bones",[]),128):
			if not error.is_empty():return
			var joints: Array=[];var at:=index(root,nodes.size());var seen:={}
			while not seen.has(at) and joints.size()<512:
				seen[at]=true;var row:=config.duplicate(true);row.binding=ref(at);row.source_node=at;joints.append(row)
				var children:=array(object(nodes[at]).get("children",[]),512)
				if children.is_empty():break
				if joints.size()>=512:fail("Secondary chain exceeds512 joints.");break
				if children.size()!=1:fail("Branched legacy springs need explicit chain review.");break
				at=index(children[0],nodes.size())
				if seen.has(at):fail("Cyclic legacy spring hierarchy.")
			add_chain(joints,str(spring.get("comment","Spring")),spring.get("center"),selected_colliders(spring.get("colliderGroups",[])),0.07)

static func from_gltf(data: Dictionary,state: GLTFState,scene: Node3D) -> Dictionary:
	var extensions=data.get("extensions",{})
	if not extensions is Dictionary:return {"format":FORMAT,"chains":[],"colliders":[],"error":"Invalid extension list."}
	var legacy=false;var native=extensions.get("VRMC_springBone")
	if native==null:
		var vrm=extensions.get("VRM",{})
		if vrm is Dictionary:native=vrm.get("secondaryAnimation");legacy=native!=null
	var extras=data.get("extras",{});var helpers=extras.get("has_secondary_helpers_1") if extras is Dictionary else null
	if native==null and helpers==null:return {"format":FORMAT,"chains":[],"colliders":[],"error":""}
	var adapter=new();adapter.nodes=adapter.array(data.get("nodes"),100000)
	# GLTFSkeleton.get_godot_bone_node() is export-only in4.6 (empty on import).
	# GLTFNode.resource_name is the engine-generated UNIQUE bone name for this
	# exact source node, after sanitization. Never search original display names.
	var generated:=state.get_nodes();var skeletons:=state.get_skeletons()
	var live_nodes:={};var pending: Array=[scene]
	while not pending.is_empty():
		var current: Node=pending.pop_back();pending.append_array(current.get_children())
		if not current is Node3D or current is Skeleton3D:continue
		var source_index=current.get_meta("has_shape_source_node",-1)
		if not source_index is int or source_index<0 or source_index>=generated.size():continue
		if not live_nodes.has(source_index):live_nodes[source_index]=[]
		live_nodes[source_index].append(current)
	for i in range(generated.size()):
		var g: GLTFNode=generated[i]
		if g.skeleton>=0 and g.skeleton<skeletons.size():
			var sk: Skeleton3D=skeletons[g.skeleton].get_godot_skeleton()
			var bone:=sk.find_bone(g.resource_name)
			if bone>=0:adapter.bindings[i]={"kind":"bone","id":str(scene.get_path_to(sk))+"::"+str(sk.get_bone_name(bone)),"source_node":i}
		else:
			# Never dereference the importer's stale scene-node table. Only live,
			# uniquely tagged scene nodes can provide a non-bone binding.
			var candidates: Array=live_nodes.get(i,[])
			if candidates.size()==1:adapter.bindings[i]={"kind":"node","path":str(scene.get_path_to(candidates[0])),"source_node":i}
	for i in range(adapter.nodes.size()):
		for child in adapter.array(adapter.object(adapter.nodes[i]).get("children",[]),100000):
			var c:=adapter.index(child,adapter.nodes.size())
			if adapter.parents.has(c):adapter.fail("Secondary source hierarchy has repeated parents.")
			adapter.parents[c]=i
	for i in adapter.bindings:
		var parent: int=adapter.parents.get(i,-1)
		if adapter.bindings[i].kind=="node" and adapter.bindings.has(parent) and adapter.bindings[parent].kind=="bone":
			var local: Transform3D=generated[i].xform
			var q:=local.basis.get_rotation_quaternion();var s:=local.basis.get_scale()
			adapter.bindings[i]={"kind":"offset","id":adapter.bindings[parent].id,"position":[local.origin.x,local.origin.y,local.origin.z],"rotation_xyzw":[q.x,q.y,q.z,q.w],"scale":[s.x,s.y,s.z],"source_node":i}
	if native!=null:
		if legacy:adapter.parse_v0(adapter.object(native))
		else:adapter.parse_v1(adapter.object(native))
	if helpers!=null:
		var addition: Dictionary=adapter.object(helpers)
		# Generated HAS additions cannot borrow native collision-group indices or
		# alter an imported collider configuration. Their joints use the same parser.
		if addition.has("colliders") or addition.has("colliderGroups"):adapter.fail("Invalid generated helper collider data.")
		for chain in adapter.array(addition.get("springs",[]),128):
			if not adapter.array(adapter.object(chain).get("colliderGroups",[]),256).is_empty():adapter.fail("Generated helper collision groups need explicit authoring.")
		adapter.parse_v1(addition)
	return {"format":FORMAT,"chains":adapter.chains if adapter.error.is_empty() else [],"colliders":adapter.colliders if adapter.error.is_empty() else [],"error":adapter.error,"source_family":"HAS" if native==null else "VRM0" if legacy else "VRM1"}

static func binding_transform(actor: RefCounted,binding: Dictionary) -> Transform3D:
	if binding.kind=="bone":return actor.bone_transform(binding.id)
	if binding.kind=="offset":
		var q: Array=binding.rotation_xyzw;var p: Array=binding.position;var s: Array=binding.scale
		return actor.bone_transform(binding.id)*Transform3D(Basis(Quaternion(q[0],q[1],q[2],q[3])).scaled(Vector3(s[0],s[1],s[2])),Vector3(p[0],p[1],p[2]))
	var node: Node3D=actor.root.get_node(NodePath(binding.path))
	return node.global_transform
