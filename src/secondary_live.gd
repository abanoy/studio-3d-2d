extends RefCounted
# Same live-simulation contract as body rigs/props, with an optional body solver.
# Fixed-tick output is ordinary native-ID FK, consumed by existing Record/Freeze.
const Spring=preload("res://src/secondary_spring.gd")
const Definition=preload("res://src/secondary_rig.gd")
const Model=preload("res://src/model.gd")
const Timeline=preload("res://src/timeline.gd")
const Airflow=preload("res://src/airflow.gd")
var rig: RefCounted
var primary: RefCounted
var runner: RefCounted
var bodies: Dictionary={}
var initial_pose: Dictionary={}
var initial_world:=Transform3D.IDENTITY
var latest: Dictionary={}
var dynamics: Dictionary={}
var forces: Array=[]
var age:=0.0
var running:=false

static func create(actor: RefCounted,body: RefCounted,frame: int,editing: bool) -> Dictionary:
	var candidate=new();candidate.rig=actor;candidate.primary=body
	candidate.initial_pose=body.capture_pose() if body and body.has_method("capture_pose") else body.pose() if body else actor.sample(frame,editing)
	candidate.latest=candidate.initial_pose.duplicate(true);candidate.initial_world=actor.root.global_transform
	actor.live_pose=candidate.latest;actor.apply_current(frame,editing)
	var result: Dictionary=await Spring.create(actor)
	if result.has("error"):
		actor.live_pose=null if not body else candidate.initial_pose
		return result
	candidate.runner=result.runner
	if body:candidate.bodies=body.bodies
	if body:
		for chain in candidate.runner.chains:
			for id in chain.ids:
				if body.bodies.has(id):candidate.runner.dispose();return {"error":"A declared hair/clothing chain also drives a body joint. Review that rig before combining both simulations."}
	return {"physics":candidate}

func start() -> void:
	running=true;rig.live_world_transform=initial_world;rig.live_pose=latest

func advance(delta: float,frame: int,time: float,recording: bool,fields: Array,runtime: RefCounted) -> String:
	if not running:return ""
	var base: Dictionary
	if primary:
		base=primary.capture_pose() if primary.has_method("capture_pose") else primary.pose()
		if primary.has_method("sync_visual"):primary.sync_visual()
	elif recording:
		base=rig.sample(time);rig.live_world_transform=Airflow.world_transform(rig,runtime,time)
	else:base=initial_pose.duplicate(true);rig.live_world_transform=initial_world
	rig.live_pose=base;rig.apply_current(frame)
	var wind: Array=[]
	for i in range(runner.chains.size()):
		var chain: Dictionary=runner.chains[i];var point:=Definition.binding_transform(rig,chain.source.joints[0].binding).origin
		var wanted:=Airflow.force(fields,point)
		if forces.size()<=i:forces.append(Vector3.ZERO)
		forces[i]=forces[i].lerp(wanted,1.0-exp(-delta/0.15));wind.append(forces[i])
	var result: Dictionary=runner.step(delta,Vector3.ZERO,wind)
	if result.has("error"):return result.error
	age+=delta;var blend:=smoothstep(0.0,0.35,age);latest=base.duplicate(true)
	for id in result.pose:
		var authored: Dictionary=base.get(id,Model.identity());var q:=Timeline.quaternion(authored.rotation_xyzw)
		var target: Quaternion=q.inverse()*Timeline.quaternion(result.pose[id].rotation_xyzw)
		target=Quaternion.IDENTITY.slerp(target,blend)
		var previous: Quaternion=dynamics.get(id,Quaternion.IDENTITY)
		var angle:=previous.angle_to(target);var maximum:=deg_to_rad(180)*delta
		var offset:=previous.slerp(target,minf(1.0,maximum/angle)) if angle>0.000001 else target
		dynamics[id]=offset;var rotation: Quaternion=(q*offset).normalized()
		latest[id]={"position":authored.position.duplicate(),"rotation_xyzw":[rotation.x,rotation.y,rotation.z,rotation.w]}
	rig.live_pose=latest;rig.apply_current(frame)
	return ""

func sync_visual() -> void:
	if not running:return
	if primary and primary.has_method("sync_visual"):primary.sync_visual()
	rig.live_pose=latest

func root_transform(_frame: int,_editing: bool) -> Dictionary:
	if primary:return primary.root_transform(_frame,_editing)
	var local: Transform3D=rig.root.get_parent().global_transform.affine_inverse()*rig.root.global_transform*rig.base_root.affine_inverse()
	var q:=local.basis.orthonormalized().get_rotation_quaternion().normalized()
	return {"position":[local.origin.x,local.origin.y,local.origin.z],"rotation_xyzw":[q.x,q.y,q.z,q.w],"scale":local.basis.get_scale().x}
func capture_pose() -> Dictionary:return latest.duplicate(true)
func pose() -> Dictionary:return latest.duplicate(true)
func stop() -> Dictionary:
	var result:=pose();running=false
	if primary:primary.stop()
	rig.live_pose=null;rig.live_world_transform=null
	return result
func dispose() -> void:
	running=false
	if primary:primary.dispose();primary=null
	if runner:runner.dispose();runner=null
	if is_instance_valid(rig.root):rig.live_pose=null;rig.live_world_transform=null
	bodies.clear();latest.clear()
