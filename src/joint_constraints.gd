extends RefCounted
# Source-independent authoring only. Results are ordinary editable FK deltas.
const META:="has_joint_constraints_1"
const FORMAT:="studio_ik_constraints_1"
const T=preload("res://src/timeline.gd")
const Model=preload("res://src/model.gd")
var rig: RefCounted
var pose:={}
var cache:={}
var parents:={}

static func whole(value,low: int,high: int) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and value==floor(value) and value>=low and value<=high

static func ancestor(parent: String,child: String,table: Dictionary) -> bool:
	var seen:={}
	while child!="@root":
		if child==parent:return true
		if seen.has(child) or seen.size()>256 or not table.has(child):return false
		seen[child]=true;child=table[child]
	return false

static func valid_parents(child: String,table: Dictionary) -> bool:
	var seen:={}
	while child!="@root":
		if seen.has(child) or seen.size()>=256 or not table.has(child):return false
		seen[child]=true;child=table[child]
	return true

static func plan(model: RefCounted,selected: String) -> Dictionary:
	if not model or not model.root or not model.bones.has(selected):return {}
	var descriptor=model.root.get_meta(META,{})
	if not descriptor is Dictionary or descriptor.is_empty():return {}
	if descriptor.get("format")!=FORMAT or not descriptor.get("chains") is Array or descriptor.chains.size()>64:return {"error":"This model has unsupported joint declarations. Use direct bone posing."}
	var bindings: Dictionary=model.root.get_meta("has_source_bones",{})
	var controllers: Array=[]
	for row in descriptor.chains:
		if row is Dictionary and whole(row.get("controller"),0,100000) and bindings.get(int(row.controller),"")==selected:controllers.append(row)
	if controllers.is_empty():
		if descriptor.get("skipped") is Array:
			for row in descriptor.skipped:
				if row is Dictionary and row.get("name")==model.bones[selected].name:return {"error":"This joint control is unsupported: "+str(row.get("reason","Use direct bone posing.")).left(200)}
		return {}
	var table:={}
	for id in model.order:table[id]=model.parent_id(id)
	var rows: Array=[];var work:=0;var names:={}
	for row in descriptor.chains:
		if not row is Dictionary or not row.get("name") is String or row.name.is_empty() or names.has(row.name) or not whole(row.get("iterations"),1,256) or not (row.get("angle_limit") is int or row.get("angle_limit") is float) or not is_finite(float(row.angle_limit)) or row.angle_limit<=0 or row.angle_limit>TAU or not row.get("links") is Array or row.links.is_empty() or row.links.size()>32:return {"error":"Invalid joint-chain settings. Use direct bone posing."}
		names[row.name]=true
		var bound:={"name":row.name,"iterations":int(row.iterations),"angle_limit":float(row.angle_limit),"links":[]}
		for field in ["controller","effector"]:
			if not whole(row.get(field),0,100000) or not bindings.has(int(row[field])) or not model.bones.has(bindings[int(row[field])]):return {"error":"A declared joint has no exact imported bone binding."}
			bound[field]=bindings[int(row[field])]
			if not valid_parents(bound[field],table):return {"error":"Joint hierarchy is cyclic or exceeds256parents."}
		var previous: String=bound.effector;var seen:={}
		for link in row.links:
			if not link is Dictionary or not whole(link.get("node"),0,100000) or not bindings.has(int(link.node)):return {"error":"Invalid joint link binding."}
			var id: String=bindings[int(link.node)]
			if not model.bones.has(id) or seen.has(id) or id==previous or not ancestor(id,previous,table) or ancestor(id,bound.controller,table):return {"error":"Joint links have unsupported dependencies."}
			if model.bones[id].skeleton!=model.bones[bound.controller].skeleton or model.bones[id].skeleton!=model.bones[bound.effector].skeleton:return {"error":"Joint links must share one imported skeleton."}
			var entry:={"id":id,"free":[0,1,2]}
			if link.has("minimum") or link.has("maximum"):
				for field in ["minimum","maximum"]:
					if not link.get(field) is Array or link[field].size()!=3:return {"error":"Incomplete joint angle limits."}
					for value in link[field]:
						if not (value is int or value is float) or not is_finite(float(value)) or absf(value)>TAU*2:return {"error":"Invalid joint angle limits."}
				entry["minimum"]=T.vector(link.minimum);entry["maximum"]=T.vector(link.maximum);entry.free=[]
				for axis in range(3):
					if entry.minimum[axis]>entry.maximum[axis]:return {"error":"Reversed joint angle limits."}
					if entry.maximum[axis]-entry.minimum[axis]>1e-8:entry.free.append(axis)
			bound.links.append(entry);seen[id]=true;previous=id
		work+=bound.iterations*bound.links.size()
		if work>32768:return {"error":"Joint declarations exceed the authoring work budget."}
		if selected==bound.controller or ancestor(selected,bound.effector,table)!=ancestor(selected,bound.controller,table):rows.append(bound)
	return {"chains":rows,"parents":table,"root_id":model.root.get_instance_id(),"model_id":model.data.id,"selected":selected}

static func solve(model: RefCounted,binding: Dictionary,values: Dictionary) -> Dictionary:
	var worker: RefCounted=load("res://src/joint_constraints.gd").new()
	return worker.run(model,binding,values)

func global_bone(id: String) -> Transform3D:
	if cache.has(id):return cache[id]
	var info: Dictionary=rig.bones[id];var base: Transform3D=info.base
	var value: Dictionary=pose.get(id,Model.identity())
	var local:=Transform3D(base.basis*Basis(T.quaternion(value.rotation_xyzw)),base.origin+T.vector(value.position))
	var parent: String=parents[id]
	cache[id]=(info.skeleton.global_transform if parent=="@root" else global_bone(parent))*local
	return cache[id]

func rotation(id: String) -> Quaternion:
	return T.quaternion(pose.get(id,Model.identity()).rotation_xyzw)

func limited(value: Quaternion,link: Dictionary) -> Quaternion:
	if not link.has("minimum"):return value.normalized()
	# Blender-style XYZ deltas compose Rz*Ry*Rx, Godot's ZYX basis convention.
	var angles:=Basis(value.normalized()).get_euler(EULER_ORDER_ZYX)
	for axis in range(3):angles[axis]=clampf(angles[axis],link.minimum[axis],link.maximum[axis])
	return Basis.from_euler(angles,EULER_ORDER_ZYX).get_rotation_quaternion().normalized()

func set_rotation(id: String,value: Quaternion,link: Dictionary) -> void:
	var q:=limited(value,link);var current: Dictionary=pose.get(id,Model.identity()).duplicate(true)
	current.rotation_xyzw=[q.x,q.y,q.z,q.w];pose[id]=current;cache.clear()

func run(model: RefCounted,binding: Dictionary,values: Dictionary) -> Dictionary:
	if binding.get("root_id",-1)!=model.root.get_instance_id() or binding.get("model_id","")!=model.data.id:return {"error":"The model changed. Start the joint edit again."}
	rig=model;pose=values.duplicate(true);parents=binding.parents
	for id in pose:
		if not rig.bones.has(id) or not Model.transform_valid(pose[id]):return {"error":"Invalid authored pose for joint solving."}
	var reports: Array=[]
	for chain in binding.chains:
		for id in [chain.controller,chain.effector]:
			if not preload("res://src/limb_ik.gd").regular(global_bone(id).basis):return {"error":"Joint posing needs positive uniform scale. Use direct bone posing."}
		for link in chain.links:
			if not preload("res://src/limb_ik.gd").regular(global_bone(link.id).basis):return {"error":"Joint posing needs positive uniform bone scale."}
		var goal:=global_bone(chain.controller).origin
		for link in chain.links:set_rotation(link.id,rotation(link.id),link)
		var steps:=0;var warm:=false
		if chain.links.size()==2 and chain.links[0].has("minimum") and chain.links[0].free.size()==1:
			var knee: Dictionary=chain.links[0];var hip: Dictionary=chain.links[1];var axis_index: int=knee.free[0]
			var h:=global_bone(hip.id).origin;var k:=global_bone(knee.id).origin;var f:=global_bone(chain.effector).origin
			var a:=h.distance_to(k);var b:=k.distance_to(f);var distance:=h.distance_to(goal)
			if minf(a,b)>1e-8:
				var bend:=PI-acos(clampf((a*a+b*b-distance*distance)/(2*a*b),-1,1))
				var current:=acos(clampf((k-h).normalized().dot((f-k).normalized()),-1,1))
				var sign_value: int=-1 if knee.maximum[axis_index]<=0 else 1
				var axis:=Vector3.ZERO;axis[axis_index]=1
				var angle: float=clampf(sign_value*(bend-current),-chain.angle_limit,chain.angle_limit)
				set_rotation(knee.id,rotation(knee.id)*Quaternion(axis,angle),knee);steps+=1
				var inverse:=global_bone(hip.id).basis.orthonormalized().inverse()
				var source: Vector3=inverse*(global_bone(chain.effector).origin-h);var target: Vector3=inverse*(goal-h)
				if minf(source.length(),target.length())>1e-8:
					var delta:=Quaternion(source.normalized(),target.normalized());angle=minf(delta.get_angle(),chain.angle_limit)
					if angle>1e-9:set_rotation(hip.id,rotation(hip.id)*Quaternion(delta.get_axis(),angle),hip)
					steps+=1;warm=true
		for iteration in range(chain.iterations-int(warm)):
			if global_bone(chain.effector).origin.distance_to(goal)<1e-6:break
			for link in chain.links:
				var world:=global_bone(link.id);var inverse:=world.basis.orthonormalized().inverse()
				var a: Vector3=inverse*(global_bone(chain.effector).origin-world.origin);var b: Vector3=inverse*(goal-world.origin)
				if minf(a.length(),b.length())<1e-9:continue
				a=a.normalized();b=b.normalized();var axis:=Vector3.ZERO;var angle:=0.
				if link.free.size()==1:
					axis[link.free[0]]=1;a-=axis*a.dot(axis);b-=axis*b.dot(axis)
					if minf(a.length(),b.length())<1e-9:continue
					a=a.normalized();b=b.normalized();angle=atan2(axis.dot(a.cross(b)),clampf(a.dot(b),-1,1))
				else:
					axis=a.cross(b);angle=atan2(axis.length(),clampf(a.dot(b),-1,1))
					if angle<1e-9:continue
					if axis.length()<1e-9:axis=a.cross(Vector3.RIGHT if absf(a.x)<.9 else Vector3.UP)
					axis=axis.normalized()
				angle=clampf(angle,-chain.angle_limit,chain.angle_limit);set_rotation(link.id,rotation(link.id)*Quaternion(axis,angle),link);steps+=1
		var residual:=global_bone(chain.effector).origin.distance_to(goal)
		if not is_finite(residual):return {"error":"Joint solving produced a nonfinite pose."}
		reports.append({"name":chain.name,"residual":residual,"steps":steps})
	return {"pose":pose,"chains":reports}
