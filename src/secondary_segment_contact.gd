extends RefCounted
# Bounded rotational contact guard for runtime-generated arm envelopes.
# Moves no attachment/local position and never changes authored spring settings.
const Timeline=preload("res://src/timeline.gd")
const Definition=preload("res://src/secondary_rig.gd")
static func ordered(actor: RefCounted,chains: Array) -> Dictionary:
	var owners: Dictionary={};var dependencies: Array=[]
	for i in range(chains.size()):
		for id in chains[i].ids:owners[id]=i
	for i in range(chains.size()):
		var wanted: Dictionary={}
		for id in chains[i].ids:
			var at: String=actor.parent_id(id)
			while at!="@root":
				if owners.has(at) and owners[at]!=i:wanted[owners[at]]=true
				at=actor.parent_id(at)
		dependencies.append(wanted)
	var indices: Array=[];var pending: Array=range(chains.size())
	while not pending.is_empty():
		var progressed:=false
		for i in range(pending.size()-1,-1,-1):
			var index: int=pending[i];var ready:=true
			for parent in dependencies[index]:
				if not parent in indices:ready=false;break
			if ready:indices.append(index);pending.remove_at(i);progressed=true
		if not progressed:return {"error":"Interleaved generated chains need independent joint ownership before body contact."}
	var result: Array=[]
	for index in indices:result.append(chains[index])
	return {"chains":result}
static func distance(a: Vector3,b: Vector3,c: Vector3,d: Vector3) -> float:
	var pair:=Geometry3D.get_closest_points_between_segments(a,b,c,d)
	return pair[0].distance_to(pair[1])
static func deflect(start: Vector3,finish: Vector3,a: Vector3,b: Vector3,radius: float,pole: Vector3) -> Dictionary:
	var direction:=finish-start;var length:=direction.length()
	if length<.000001 or distance(start,finish,a,b)>=radius:return {"rotation":Quaternion.IDENTITY,"changed":false,"blocked":false}
	var axis:=b-a;var nearest: Vector3=a+axis*clampf((start-a).dot(axis)/axis.length_squared(),0.,1.) if axis.length_squared()>0 else a
	var outward:=start-nearest
	if outward.length()<=radius:return {"rotation":Quaternion.IDENTITY,"changed":false,"blocked":true}
	direction/=length;outward=outward.normalized()
	var turn:=direction.cross(outward);var angle:=acos(clampf(direction.dot(outward),-1.,1.))
	if turn.length_squared()<.0000000001:
		turn=pole-direction*pole.dot(direction)
		if turn.length_squared()<.0000000001:turn=direction.cross(Vector3.UP if absf(direction.y)<.9 else Vector3.RIGHT)
	turn=turn.normalized()
	var lo:=0.;var hi:=angle
	# The away ray clears a convex capsule when the fixed attachment is outside.
	# Retain a known-clear upper bracket, never accept an enlarged tolerance.
	if distance(start,start+Quaternion(turn,hi)*direction*length,a,b)<radius:return {"rotation":Quaternion.IDENTITY,"changed":false,"blocked":true}
	for i in range(16):
		var middle: float=(lo+hi)*.5
		var endpoint: Vector3=start+Quaternion(turn,middle)*direction*length
		if distance(start,endpoint,a,b)>=radius:hi=middle
		else:lo=middle
	return {"rotation":Quaternion(turn,hi),"changed":true,"blocked":false}
static func world(actor: RefCounted,id: String,pose: Dictionary,context: Dictionary) -> Transform3D:
	if context.cache.has(id):return context.cache[id]
	if context.visiting.has(id) or not actor.bones.has(id):context.error="Invalid secondary contact hierarchy.";return Transform3D.IDENTITY
	context.visiting[id]=true
	var info: Dictionary=actor.bones[id];var index: int=info.index;var sk: Skeleton3D=info.skeleton
	var parent: int=sk.get_bone_parent(index);var ancestor: Transform3D=sk.global_transform
	if parent>=0:ancestor=world(actor,str(info.path)+"::"+str(sk.get_bone_name(parent)),pose,context)
	var local: Transform3D=sk.get_bone_pose(index)
	if pose.has(id):
		var value: Dictionary=pose[id];var base: Transform3D=info.base
		local=Transform3D(Basis(base.basis.get_rotation_quaternion()*Timeline.quaternion(value.rotation_xyzw)).scaled(base.basis.get_scale()),base.origin+Timeline.vector(value.position))
	var result: Transform3D=ancestor*local
	context.visiting.erase(id);context.cache[id]=result;return result
static func binding(actor: RefCounted,value: Dictionary,pose: Dictionary,context: Dictionary) -> Transform3D:
	if value.kind=="bone":return world(actor,value.id,pose,context)
	if value.kind=="offset":return world(actor,value.id,pose,context)*Transform3D(Basis(Timeline.quaternion(value.rotation_xyzw)).scaled(Timeline.vector(value.scale)),Timeline.vector(value.position))
	return Definition.binding_transform(actor,value)
static func constrain(actor: RefCounted,chains: Array,pose: Dictionary) -> Dictionary:
	var result: Dictionary=pose.duplicate(true);var corrections:=0;var blocked:=0
	var order: Dictionary=ordered(actor,chains)
	if order.has("error"):return order
	for chain in order.chains:
		var context:={"cache":{},"visiting":{},"error":""};var original: Array[Transform3D]=[]
		for joint in chain.source.joints:original.append(binding(actor,joint.binding,result,context))
		if not context.error.is_empty():return {"error":context.error}
		var current: Array[Transform3D]=original.duplicate()
		var chain_changed:=false
		for pass_index in range(3):
			var changed:=false
			for i in range(chain.ids.size()):
				for collider in chain.colliders:
					var c: Dictionary=collider.definition
					if not c.has("tail_binding"):continue
					var a: Transform3D=binding(actor,c.binding,result,context);var b: Transform3D=binding(actor,c.tail_binding,result,context)
					var joint: Dictionary=chain.source.joints[i]
					var next_joint: Dictionary=chain.source.joints[i+1]
					var hair_radius: float=maxf(joint.radius*current[i].basis.get_scale().x,next_joint.radius*current[i+1].basis.get_scale().x)
					var radius: float=c.radius*a.basis.get_scale().x+hair_radius
					var solved: Dictionary=deflect(current[i].origin,current[i+1].origin,a.origin,b.origin,radius,current[i].basis.x)
					if solved.blocked:blocked+=1
					if not solved.changed:continue
					var rotation: Quaternion=solved.rotation;var basis:=Basis(rotation)
					var delta:=Transform3D(basis,current[i].origin-basis*current[i].origin)
					for j in range(i,current.size()):current[j]=delta*current[j]
					changed=true;chain_changed=true;corrections+=1
			if not changed:break
		if not chain_changed:continue
		var solved_bones: Dictionary={}
		for i in range(chain.ids.size()):solved_bones[chain.ids[i]]=current[i]
		for i in range(chain.ids.size()):
			var id: String=chain.ids[i];var info: Dictionary=actor.bones[id];var parent: String=actor.parent_id(id)
			var ancestor: Transform3D=info.skeleton.global_transform if parent=="@root" else world(actor,parent,result,context)
			var at: String=parent
			while at!="@root":
				if solved_bones.has(at):ancestor=solved_bones[at]*world(actor,at,result,context).affine_inverse()*ancestor;break
				at=actor.parent_id(at)
			var q: Quaternion=(info.base.basis.get_rotation_quaternion().inverse()*ancestor.basis.get_rotation_quaternion().inverse()*current[i].basis.get_rotation_quaternion()).normalized()
			var value: Dictionary=result.get(id,{"position":[0,0,0],"rotation_xyzw":[0,0,0,1]}).duplicate(true)
			value.rotation_xyzw=[q.x,q.y,q.z,q.w];result[id]=value
	return {"pose":result,"corrections":corrections,"blocked_attachments":blocked}
