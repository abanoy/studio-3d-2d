extends RefCounted
# Local fan fields on ordinary standard-model objects. No ecosystem branches.
const Timeline=preload("res://src/timeline.gd")
const FORMAT="studio_airflow_1"
static func defaults() -> Dictionary:return {"format":FORMAT,"enabled":true,"speed":3.0,"radius":1.0,"reach":6.0}
static func is_fan(data: Dictionary) -> bool:return data.get("metadata",{}).has("airflow")
static func validate(value) -> String:
	if not value is Dictionary or value.get("format")!=FORMAT or not value.get("enabled") is bool:return "Invalid fan settings."
	for key in ["speed","radius","reach"]:
		var n=value.get(key)
		if not (n is int or n is float) or not is_finite(float(n)) or n<0 or n>(50 if key=="speed" else 1000) or key!="speed" and n<0.05:return "Invalid fan "+key+"."
	return ""
static func field(transform: Transform3D,settings: Dictionary,point: Vector3) -> Vector3:
	if not validate(settings).is_empty() or not settings.enabled or not point.is_finite():return Vector3.ZERO
	var scale:=transform.basis.get_scale()
	if transform.basis.determinant()<=0 or minf(scale.x,minf(scale.y,scale.z))<0.00001 or absf(scale.x-scale.y)>scale.x*0.001 or absf(scale.x-scale.z)>scale.x*0.001:return Vector3.ZERO
	var direction:=transform.basis.z.normalized();var offset:=point-transform*Vector3(0,0.85,0)
	var along:=offset.dot(direction);var reach: float=settings.reach*scale.x
	if along<0 or along>=reach:return Vector3.ZERO
	var radius: float=settings.radius*scale.x+along*0.15
	var radial: float=(offset-direction*along).length()/radius
	if radial>=1:return Vector3.ZERO
	var falloff: float=(1.0-radial*radial)*(1.0-radial*radial)*(1.0-smoothstep(reach*0.7,reach,along))
	return direction*float(settings.speed)*falloff
static func world_transform(actor: RefCounted,runtime: RefCounted,frame: float) -> Transform3D:
	var value: Dictionary=actor.sample_transform(frame)
	var local: Transform3D=Transform3D(Basis(Timeline.quaternion(value.rotation_xyzw)).scaled(Vector3.ONE*value.scale),Timeline.vector(value.position))*actor.base_root
	var parent: String=actor.data.get("parent_id","")
	if runtime and not parent.is_empty():return world_transform(runtime.instance(parent),runtime,frame)*local
	return (runtime.root.global_transform if runtime else actor.root.get_parent().global_transform)*local
static func collect(renderer,frame: float,live: Dictionary) -> Array:
	var result: Array=[]
	if not renderer.world_runtime:return result
	for actor in renderer.world_runtime.instances.values():
		if not is_fan(actor.data) or frame<float(actor.data.start_frame) or not actor.visible_at(int(frame)):continue
		var settings: Dictionary=actor.data.metadata.airflow
		if not validate(settings).is_empty() or not settings.enabled:continue
		var visible:=true;var parent: String=actor.data.parent_id
		while not parent.is_empty():
			var node: RefCounted=renderer.world_runtime.instance(parent)
			visible=visible and frame>=float(node.data.start_frame) and node.visible_at(int(frame));parent=node.data.parent_id
		if not visible:continue
		result.append({"transform":actor.root.global_transform if live.has(actor.data.id) else world_transform(actor,renderer.world_runtime,frame),"settings":settings})
	return result
static func force(fields: Array,point: Vector3) -> Vector3:
	var result:=Vector3.ZERO
	for fan in fields:result+=field(fan.transform,fan.settings,point)*0.03
	return result.limit_length(3.0)
static func unsteady_force(fields: Array,point: Vector3,seconds: float) -> Vector3:
	# Fixed simulation time and spatial phase keep recording/replay deterministic.
	# A fan has a mean direction with small gusts and cross-flow, not a static bend.
	if not is_finite(seconds) or not point.is_finite():return Vector3.ZERO
	var result:=Vector3.ZERO;var time:=fmod(maxf(seconds,0),3600.)
	for fan in fields:
		var mean:=field(fan.transform,fan.settings,point)*.03
		if mean.length_squared()<.0000000001:continue
		var direction:=mean.normalized();var side:=direction.cross(Vector3.UP)
		if side.length_squared()<.001:side=direction.cross(Vector3.RIGHT)
		side=side.normalized();var lift:=side.cross(direction).normalized()
		var phase: float=point.dot(Vector3(13.1,7.7,11.3))+fan.transform.origin.dot(Vector3(.4,.7,1.1))
		var rate:=1.+float(fan.settings.speed)*.02;var clock:=time*TAU*rate
		var flutter:=clampf(float(fan.settings.speed)/6.,.1,1.5)
		var pulse:=.18*sin(clock*.95+phase)+.08*sin(clock*2.7+phase*.71)
		var lateral:=.16*sin(clock*2.+phase*.83)+.08*sin(clock*4.3+phase*1.27)
		var vertical:=.12*sin(clock*1.7+phase*1.13)
		result+=mean*(1.+pulse*flutter)+(side*lateral+lift*vertical)*mean.length()*flutter*(.8+float(fan.settings.speed)*.02)
	return result.limit_length(3.)
static func create_asset(path: String) -> Error:
	var SceneIO=load("res://src/scene3d.gd")
	var root:=Node3D.new();root.name="HASOriginalFan"
	SceneIO.box(root,"Foot",Vector3(0,0.06,0),Vector3(0.5,0.12,0.4),Color("668aa0"))
	SceneIO.box(root,"Stand",Vector3(0,0.4,0),Vector3(0.08,0.65,0.08),Color("9daeb8"))
	var disc:=MeshInstance3D.new();disc.name="FanBody";var cylinder:=CylinderMesh.new();cylinder.top_radius=0.32;cylinder.bottom_radius=0.32;cylinder.height=0.09;cylinder.radial_segments=24;disc.mesh=cylinder;root.add_child(disc);disc.owner=root;disc.position=Vector3(0,0.85,0);disc.rotation.x=PI/2
	var material:=StandardMaterial3D.new();material.albedo_color=Color("8fb0c5");disc.material_override=material
	for i in range(4):
		var angle:=i*PI/2+PI/4
		SceneIO.box(root,"Blade"+str(i),Vector3(cos(angle)*0.15,0.85+sin(angle)*0.15,0.06),Vector3(0.13,0.27,0.04),Color("dae5ea"));root.get_child(-1).rotation.z=angle-PI/2
	SceneIO.box(root,"Hub",Vector3(0,0.85,0.09),Vector3(0.09,0.09,0.07),Color("5b7c94"))
	# Permanent original arrow geometry marks the blowing (+Z) direction.
	SceneIO.box(root,"AirArrow",Vector3(0,0.85,0.32),Vector3(0.025,0.025,0.3),Color("66b9d9"))
	for side in [-1,1]:
		SceneIO.box(root,"ArrowTip",Vector3(side*0.04,0.85,0.44),Vector3(0.025,0.025,0.13),Color("66b9d9"));root.get_child(-1).rotation.y=side*PI/4
	var doc:=GLTFDocument.new();var state:=GLTFState.new();var error:=doc.append_from_scene(root,state)
	if error==OK:error=doc.write_to_filesystem(state,path)
	root.free();return error
