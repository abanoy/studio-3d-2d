extends RefCounted
# Isolated synthetic Model/Skeleton controller. No app hook or native admission.
const Math=preload("res://src/part_pose_follow_math.gd")
const Timeline=preload("res://src/timeline.gd")
const Model=preload("res://src/model.gd")
const PHASE:="authored_fk_ready_before_secondary"
const EPS:=0.00002
var master: RefCounted
var target: RefCounted
var bundle: Node3D
var master_rig: Dictionary={}
var target_rig: Dictionary={}
var links: Dictionary={}
var master_rest: Array=[]
var master_rest_frame:=Transform3D.IDENTITY
var captured: Dictionary={}
var owned: Dictionary={}
var channels: Dictionary={}
var last_epoch:=-1
var disposed:=false
var stats:={"captures":0,"applications":0,"pose_writes":0,"restores":0,"repeated_noops":0}

static func create_native(_master,_target,_bundle,_source_bindings) -> Dictionary:
	return {"error":"Native follow requires an independently qualified source-index/GLTF/runtime binding adapter. This controller only admits marked synthetic fixtures."}

static func same_frame(a: Transform3D,b: Transform3D) -> bool:
	return a.origin.distance_to(b.origin)<=EPS and a.basis.x.distance_to(b.basis.x)<=EPS and a.basis.y.distance_to(b.basis.y)<=EPS and a.basis.z.distance_to(b.basis.z)<=EPS

static func fixture_actor(actor: RefCounted) -> bool:
	if actor==null or actor.get_script()!=Model:return false
	var metadata=actor.data.get("metadata",{})
	return metadata is Dictionary and actor.data.get("format")=="studio_model_1" and metadata.get("part_follow_synthetic_fixture") is bool and metadata.part_follow_synthetic_fixture and not metadata.has("native_parameters")

static func inventory(actor: RefCounted) -> Dictionary:
	if not fixture_actor(actor):return {"error":"Only an actual marked synthetic Model script is supported."}
	if actor==null or not is_instance_valid(actor.root) or not actor.root.is_inside_tree():return {"error":"A live Model root is required."}
	if actor.order.is_empty() or actor.order.size()>512 or actor.order.size()!=actor.bones.size():return {"error":"A bounded complete Model bone inventory is required."}
	var sk: Skeleton3D
	for id in actor.order:
		if not actor.bones.has(id):return {"error":"Model bone inventory changed."}
		var row: Dictionary=actor.bones[id]
		if not is_instance_valid(row.get("skeleton")) or not row.skeleton is Skeleton3D:return {"error":"Model binding must identify an actual Skeleton3D."}
		if sk==null:sk=row.skeleton
		elif sk!=row.skeleton:return {"error":"This fixture profile supports one Skeleton per Model."}
	if not sk.is_inside_tree() or not actor.root.is_ancestor_of(sk) or sk.get_bone_count()!=actor.order.size():return {"error":"Model must own its complete independent Skeleton."}
	var ids: Array=[];var names: Array=[];var parents: Array=[];var bases: Array=[]
	ids.resize(sk.get_bone_count());names.resize(ids.size());parents.resize(ids.size());bases.resize(ids.size())
	for id in actor.order:
		var info: Dictionary=actor.bones[id];var index=info.get("index")
		if not index is int or index<0 or index>=ids.size() or ids[index]!=null:return {"error":"Model indices must identify unique actual bones."}
		if info.get("name")!=str(sk.get_bone_name(index)) or info.get("path")!=str(actor.root.get_path_to(sk)) or not info.get("base") is Transform3D:return {"error":"Model index/name/path/base binding changed."}
		if not Math.finite_frame(info.base):return {"error":"Imported Model base pose must be finite and nonsingular."}
		ids[index]=id;names[index]=info.name;parents[index]=sk.get_bone_parent(index);bases[index]=info.base
	var pending: Array=range(ids.size());var sorted: Array=[]
	while not pending.is_empty():
		var progressed:=false
		for at in range(pending.size()-1,-1,-1):
			var index: int=pending[at];var parent: int=parents[index]
			if parent< -1 or parent>=ids.size() or parent==index:return {"error":"Invalid target parent identity."}
			if parent>=0 and not parent in sorted:continue
			sorted.append(index);pending.remove_at(at);progressed=true
		if not progressed:return {"error":"Bone parents must be acyclic."}
	return {"skeleton":sk,"skeleton_id":sk.get_instance_id(),"root_id":actor.root.get_instance_id(),"ids":ids,"names":names,"parents":parents,"bases":bases,"order":sorted,"source":actor.data.get("source"),"sha256":actor.data.get("sha256")}

static func create_fixture(master_actor: RefCounted,target_actor: RefCounted,root_node: Node3D,pairs: Array,procedural: Dictionary={}) -> Dictionary:
	if master_actor==target_actor or not is_instance_valid(root_node) or not root_node.is_inside_tree():return {"error":"Use two independent actors under a live bundle root."}
	var a:=inventory(master_actor);var b:=inventory(target_actor)
	if a.has("error"):return a
	if b.has("error"):return b
	if a.skeleton==b.skeleton or a.skeleton.is_ancestor_of(b.skeleton) or b.skeleton.is_ancestor_of(a.skeleton) or master_actor.root.is_ancestor_of(target_actor.root) or target_actor.root.is_ancestor_of(master_actor.root):return {"error":"Follow cannot alias or nest the two Skeleton owners."}
	if not root_node.is_ancestor_of(master_actor.root) or not root_node.is_ancestor_of(target_actor.root):return {"error":"Both actors must be descendants of the same explicit bundle."}
	if pairs.is_empty() or pairs.size()>512:return {"error":"Choose explicit bounded runtime binding pairs."}
	for role in procedural:
		if not role in ["master","target"]:return {"error":"Unknown procedural owner collection."}
		var rig: Dictionary=a if role=="master" else b
		if not procedural[role] is Array:return {"error":"Procedural owners must be explicit runtime IDs."}
		var seen:={}
		for id in procedural[role]:
			if not id is String or not id in rig.ids or seen.has(id):return {"error":"Procedural runtime owner is missing or duplicated."}
			seen[id]=true
	var value=new();value.master=master_actor;value.target=target_actor;value.bundle=root_node;value.master_rig=a;value.target_rig=b
	for pair in pairs:
		if not pair is Dictionary or pair.size()!=2 or not pair.get("master_id") is String or not pair.get("target_id") is String:return {"error":"Pairs must contain explicit master and target Model bone IDs."}
		var ai: int=a.ids.find(pair.master_id);var bi: int=b.ids.find(pair.target_id)
		if ai<0 or bi<0 or value.links.has(bi):return {"error":"A target runtime binding is missing or duplicated."}
		if pair.master_id in procedural.get("master",[]) or pair.target_id in procedural.get("target",[]):return {"error":"Procedural-owned source or target channels cannot be followed."}
		value.links[bi]=ai
	var why: String=value.binding_error()
	if not why.is_empty():return {"error":why}
	value.master_rest_frame=value.to_bundle(a.skeleton)
	var canonical: Array=[]
	for base in a.bases:canonical.append(Transform3D(Basis(base.basis.get_rotation_quaternion())*Basis.from_scale(base.basis.get_scale()),base.origin))
	value.master_rest=value.fk(canonical,a)
	for i in range(value.master_rest.size()):value.master_rest[i]=value.master_rest_frame*value.master_rest[i]
	return {"controller":value,"native_qualified":false,"synthetic_only":true}

func modifiers_supported(sk: Skeleton3D) -> bool:
	# Stock Godot adds an internal compatibility simulator even without bones.
	# Only an empty inactive scriptless internal stub can be inert in this profile.
	var visible: Array=sk.get_children()
	for child in sk.find_children("*","SkeletonModifier3D",false,false):
		var simulator:=child as PhysicalBoneSimulator3D
		if child in visible or simulator==null:return false
		if simulator.get_script()!=null or simulator.is_active() or simulator.is_simulating_physics() or simulator.get_child_count(true)!=0:return false
	return true

func binding_error(target_only:=false) -> String:
	if disposed:return "Controller is disposed."
	if not is_instance_valid(bundle) or not bundle.is_inside_tree() or not Math.finite_frame(bundle.global_transform):return "Bundle is detached, freed or singular."
	var entries: Array=[[target,target_rig]] if target_only else [[master,master_rig],[target,target_rig]]
	for entry in entries:
		var actor: RefCounted=entry[0];var saved: Dictionary=entry[1]
		if not fixture_actor(actor):return "Model script or fixture-only admission changed."
		if actor==null or not is_instance_valid(actor.root) or not actor.root.is_inside_tree() or actor.root.get_instance_id()!=saved.root_id:return "Model root ownership changed."
		var sk: Skeleton3D=saved.skeleton
		if not is_instance_valid(sk) or not sk.is_inside_tree() or sk.get_instance_id()!=saved.skeleton_id or not actor.root.is_ancestor_of(sk) or not bundle.is_ancestor_of(actor.root):return "Skeleton ownership changed."
		if sk.get_bone_count()!=saved.ids.size() or actor.order.size()!=saved.ids.size() or actor.bones.size()!=saved.ids.size():return "Skeleton topology changed."
		if actor.data.get("source")!=saved.source or actor.data.get("sha256")!=saved.sha256:return "Model asset identity changed."
		if actor.preview_frame>=0:return "Preview overrides require an integration adapter and are unsupported here."
		if actor.live_pose!=null or actor.live_world_transform!=null:return "Live secondary/body pose phases are explicitly unsupported. Release before those writers run."
		if not Math.finite_frame(sk.global_transform):return "Skeleton frame is singular."
		if not modifiers_supported(sk):return "User/active/nonempty Skeleton modifiers are outside this isolated fixture profile."
		for i in range(saved.ids.size()):
			if not actor.bones.has(saved.ids[i]):return "Model runtime bone ID disappeared."
			var info: Dictionary=actor.bones[saved.ids[i]]
			if info.get("skeleton")!=sk or info.get("index")!=i or info.get("name")!=saved.names[i] or info.get("base")!=saved.bases[i] or info.get("path")!=str(actor.root.get_path_to(sk)):return "Captured Model binding/base changed."
			if str(sk.get_bone_name(i))!=saved.names[i] or sk.get_bone_parent(i)!=saved.parents[i] or not sk.is_bone_enabled(i):return "Actual Skeleton parent/name/enabled state changed."
	return ""

func to_bundle(sk: Skeleton3D) -> Transform3D:return bundle.global_transform.affine_inverse()*sk.global_transform

func poses(sk: Skeleton3D) -> Array:
	var result:=[]
	for i in range(sk.get_bone_count()):result.append({"position":sk.get_bone_pose_position(i),"rotation":sk.get_bone_pose_rotation(i),"scale":sk.get_bone_pose_scale(i),"local":sk.get_bone_pose(i)})
	return result

func fk(locals: Array,rig: Dictionary) -> Array:
	var result: Array=[];result.resize(locals.size())
	for i in rig.order:
		var parent: int=rig.parents[i];result[i]=locals[i] if parent<0 else result[parent]*locals[i]
	return result

func fk_matches(sk: Skeleton3D,rows: Array,rig: Dictionary) -> bool:
	sk.force_update_all_bone_transforms()
	var locals:=[]
	for row in rows:locals.append(row.local)
	var expected: Array=fk(locals,rig)
	for i in range(expected.size()):
		if not same_frame(sk.get_bone_global_pose(i),expected[i]):return false
	return true

func data_token(actor: RefCounted) -> String:return JSON.stringify(actor.data,"",true,true)

func authored_matches(actor: RefCounted,rig: Dictionary,rows: Array,frame: int,editing: bool) -> bool:
	var pose: Dictionary=actor.sample(frame,editing)
	var transform: Dictionary=actor.sample_transform(frame,editing)
	var wanted: Transform3D=Transform3D(Basis(Timeline.quaternion(transform.rotation_xyzw)).scaled(Vector3.ONE*transform.scale),Timeline.vector(transform.position))*actor.base_root
	if not same_frame(actor.root.transform,wanted):return false
	for i in range(rig.ids.size()):
		var delta: Dictionary=pose.get(rig.ids[i],{"position":[0,0,0],"rotation_xyzw":[0,0,0,1]})
		var base: Transform3D=rig.bases[i]
		var expected:=Transform3D(Basis(base.basis.get_rotation_quaternion()*Timeline.quaternion(delta.rotation_xyzw))*Basis.from_scale(base.basis.get_scale()),base.origin+Timeline.vector(delta.position))
		if not same_frame(rows[i].local,expected):return false
	return actor.evaluation_error.is_empty()

func capture_authored(epoch,phase: String,frame: int,master_editing: bool,target_editing: bool) -> Dictionary:
	var why:=binding_error()
	if not why.is_empty():return {"error":why}
	if phase!=PHASE or not epoch is int or epoch<0 or epoch<=last_epoch:return {"error":"Capture requires a new explicit authored-before-secondary epoch."}
	if not owned.is_empty():return {"error":"Release owned derived channels BEFORE calling Model.apply or capturing another authored epoch."}
	var a: Skeleton3D=master_rig.skeleton;var b: Skeleton3D=target_rig.skeleton
	a.force_update_all_bone_transforms();b.force_update_all_bone_transforms()
	var ap:=poses(a);var bp:=poses(b);var ag:=[];var bg:=[]
	if not authored_matches(master,master_rig,ap,frame,master_editing) or not authored_matches(target,target_rig,bp,frame,target_editing):return {"error":"Both actual Models must apply the requested authored frame before capture; stale/dependency-order poses are unsupported."}
	for entry in [[a,ap,master_rig,ag],[b,bp,target_rig,bg]]:
		var locals:=[]
		for row in entry[1]:
			if not Math.finite_frame(row.local):return {"error":"Authored pose contains an unsupported frame."}
			locals.append(row.local)
		var expected: Array=fk(locals,entry[2]);var transform: Transform3D=to_bundle(entry[0])
		for i in range(locals.size()):
			var actual: Transform3D=entry[0].get_bone_global_pose(i)
			if not same_frame(actual,expected[i]):return {"error":"External overrides/rest-only/modifier FK is unsupported."}
			entry[3].append(transform*actual)
	captured={"epoch":epoch,"frame":frame,"master_editing":master_editing,"target_editing":target_editing,"a":ap,"b":bp,"ag":ag,"bg":bg,"af":to_bundle(a),"bf":to_bundle(b),"bundle":bundle.global_transform,"ad":data_token(master),"bd":data_token(target)}
	last_epoch=epoch;channels.clear();stats.captures+=1
	return {"captured":true,"epoch":epoch,"native_qualified":false}

static func model_delta(base: Transform3D,local: Transform3D) -> Dictionary:
	if not Math.finite_frame(base) or not Math.finite_frame(local):return {"error":"Model delta needs finite supported local/base frames."}
	var rotation: Quaternion=(base.basis.get_rotation_quaternion().inverse()*local.basis.get_rotation_quaternion()).normalized()
	var offset: Vector3=local.origin-base.origin
	var rebuilt:=Transform3D(Basis(base.basis.get_rotation_quaternion()*rotation)*Basis.from_scale(base.basis.get_scale()),base.origin+offset)
	if not same_frame(rebuilt,local):return {"error":"Follow would require a bone scale/shear change that Model pose channels cannot represent."}
	return {"position":[offset.x,offset.y,offset.z],"rotation_xyzw":[rotation.x,rotation.y,rotation.z,rotation.w]}

func write_pose(sk: Skeleton3D,index: int,row: Dictionary) -> void:
	sk.set_bone_pose_position(index,row.position);sk.set_bone_pose_rotation(index,row.rotation);sk.set_bone_pose_scale(index,row.scale)

func apply_captured(epoch,phase: String) -> Dictionary:
	var why:=binding_error()
	if not why.is_empty():return {"error":why}
	if phase!=PHASE or not epoch is int or epoch<0 or captured.is_empty() or epoch!=captured.epoch:return {"error":"Apply requires the captured authored-before-secondary epoch."}
	var a: Skeleton3D=master_rig.skeleton;var b: Skeleton3D=target_rig.skeleton
	if captured.ad!=data_token(master) or captured.bd!=data_token(target) or captured.bundle!=bundle.global_transform or captured.af!=to_bundle(a) or captured.bf!=to_bundle(b):return {"error":"Authored data or object frames changed after capture."}
	if poses(a)!=captured.a:return {"error":"Master changed after the pre-follow snapshot."}
	var before:=poses(b)
	if not fk_matches(a,poses(a),master_rig) or not fk_matches(b,before,target_rig):return {"error":"External global-only pose writer changed FK after capture; no follow writes are permitted."}
	for i in range(before.size()):
		var expected: Dictionary=owned[i] if owned.has(i) else captured.b[i]
		if before[i]!=expected:return {"error":"Target writer changed a channel after capture. Release/re-evaluate under a new epoch."}
	if captured.get("applied",false):stats.repeated_noops+=1;return {"applied":true,"writes":0,"repeated":true,"native_qualified":false}
	# An exactly equal Model-zero-channel rest is an exact no-write operation.
	var at_rest: bool=captured.af==master_rest_frame
	for i in range(master_rest.size()):at_rest=at_rest and captured.ag[i]==master_rest[i]
	if at_rest:
		captured["applied"]=true;stats.applications+=1
		return {"applied":true,"writes":0,"repeated":false,"native_qualified":false,"synthetic_only":true}
	var solved: Array=[];solved.resize(before.size());var desired:={};var staged_channels:={}
	for i in target_rig.order:
		var parent: int=target_rig.parents[i];var parent_frame: Transform3D=captured.bf if parent<0 else solved[parent]
		if not links.has(i):solved[i]=parent_frame*captured.b[i].local;continue
		var ai: int=links[i];var goal: Dictionary=Math.goal(master_rest[ai],captured.ag[ai],captured.bg[i])
		if goal.has("error"):return goal
		var local: Dictionary=Math.local_goal(parent_frame,goal.world_goal)
		if local.has("error"):return local
		var delta: Dictionary=model_delta(target_rig.bases[i],local.local_goal)
		if delta.has("error"):return delta
		desired[i]={"position":local.local_goal.origin,"rotation":local.local_goal.basis.get_rotation_quaternion(),"scale":target_rig.bases[i].basis.get_scale(),"local":local.local_goal}
		staged_channels[target_rig.ids[i]]=delta;solved[i]=goal.world_goal
	# Every binding, frame, parent and representability check completes before writes.
	for i in target_rig.order:
		if desired.has(i):write_pose(b,i,desired[i])
	b.force_update_all_bone_transforms();var actual:=poses(b);var good:=true
	for i in range(actual.size()):
		if desired.has(i):good=good and same_frame(actual[i].local,desired[i].local) and same_frame(to_bundle(b)*b.get_bone_global_pose(i),solved[i])
		else:good=good and actual[i]==before[i]
	if not good:
		for i in desired:write_pose(b,i,before[i])
		b.force_update_all_bone_transforms();return {"error":"Derived write did not roundtrip; the pre-follow pose was restored."}
	for i in desired:owned[i]=actual[i]
	channels=staged_channels;captured["applied"]=true;stats.applications+=1;stats.pose_writes+=desired.size()
	return {"applied":true,"writes":desired.size(),"repeated":false,"native_qualified":false,"synthetic_only":true}

func release_owned() -> Dictionary:
	if disposed:return {"released":true,"writes":0}
	if owned.is_empty():captured.clear();channels.clear();return {"released":true,"writes":0}
	var why:=binding_error(true)
	if not why.is_empty():return {"error":why}
	if captured.bd!=data_token(target):return {"error":"Authored data changed while derived channels were owned; recovery must restore the actor explicitly."}
	var sk: Skeleton3D=target_rig.skeleton;var current:=poses(sk)
	for i in owned:
		if current[i]!=owned[i]:return {"error":"A linked channel has a new writer; no owned channel was restored."}
	var count:=owned.size()
	for i in owned:write_pose(sk,i,captured.b[i])
	sk.force_update_all_bone_transforms();owned.clear();captured.clear();channels.clear();stats.restores+=1
	return {"released":true,"writes":count}

func dispose() -> Dictionary:
	if disposed:return {"disposed":true}
	if not is_instance_valid(target.root):owned.clear();captured.clear();channels.clear()
	else:
		var released:=release_owned()
		if released.has("error"):return released
	disposed=true;return {"disposed":true,"native_qualified":false}
