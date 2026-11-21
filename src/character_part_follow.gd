extends RefCounted
# Opt-in correspondence between actual prepared rigs. No skeleton/skin merge,
# native reconstruction, Model.data pose writes or automatic recording.
const Model=preload("res://src/model.gd")
const Math=preload("res://src/part_pose_follow_math.gd")
const PoseBounds=preload("res://src/pose_bounds.gd")
const EPS:=.00002
var plans: Dictionary={}
var reports: Dictionary={}
var frame_applications:=0

static func ownership_inputs(actor: RefCounted) -> Dictionary:
	# Snapshot only the declarations used to exclude procedural owners. Mutable
	# solver positions, collider geometry and unrelated importer data are omitted.
	var report=actor.data.get("metadata",{}).get("native_parameters",{})
	if not report is Dictionary:return {"error":"Native procedural ownership metadata must be an object."}
	var native=report.get("native_parameters",{})
	if not native is Dictionary:return {"error":"Native procedural declarations must be an object."}
	var catalogue=native.get("bones",[])
	if not catalogue is Array or catalogue.size()>4096:return {"error":"Native procedural bone identities are invalid or too large."}
	var names: Array=[]
	for bone in catalogue:
		if not bone is Dictionary or not bone.get("name") is String:return {"error":"Native procedural bone identity is incomplete."}
		names.append(bone.name)
	var secondary=actor.root.get_meta("has_secondary_rig",{})
	if not secondary is Dictionary:return {"error":"Secondary-joint ownership must be an object."}
	var chains=secondary.get("chains",[])
	if not chains is Array or chains.size()>512:return {"error":"Secondary-joint ownership chains are invalid."}
	var bindings: Array=[];var joint_count:=0
	for chain in chains:
		if not chain is Dictionary or not chain.get("joints",[]) is Array:return {"error":"Secondary-joint ownership chain is incomplete."}
		var group: Array=[]
		for joint in chain.get("joints",[]):
			joint_count+=1
			if joint_count>4096 or not joint is Dictionary or not joint.get("binding",{}) is Dictionary:return {"error":"Secondary-joint ownership binding is invalid."}
			group.append(joint.get("binding",{}))
		bindings.append(group)
	return {"native":native,"secondary":secondary,"signature":{"native_bones_present":native.has("bones"),"native_bone_names":names,"jiggle_present":native.has("source_jiggle"),"jiggle":native.get("source_jiggle"),"secondary_error":secondary.get("error",""),"secondary_bindings":bindings}}

static func same(a: Transform3D,b: Transform3D) -> bool:
	return a.origin.distance_to(b.origin)<=EPS and a.basis.x.distance_to(b.basis.x)<=EPS and a.basis.y.distance_to(b.basis.y)<=EPS and a.basis.z.distance_to(b.basis.z)<=EPS

static func relative_to(ancestor: Node3D,node: Node3D) -> Transform3D:
	# Compose local frames, avoiding subtracting distant scene/world coordinates.
	var result:=Transform3D.IDENTITY
	var current: Node=node
	while current!=ancestor and current!=null:
		if current is Node3D:result=current.transform*result
		current=current.get_parent()
	return result

static func inventory(actor: RefCounted) -> Dictionary:
	if actor==null or actor.get_script()!=Model or not is_instance_valid(actor.root) or not actor.root.is_inside_tree():return {"error":"A live prepared model is required."}
	if actor.order.is_empty() or actor.order.size()>512:return {"error":"This part needs a bounded bone rig."}
	var skeleton: Skeleton3D
	var source_ids:={}
	var source_map=actor.root.get_meta("has_source_bones",{})
	if not source_map is Dictionary:return {"error":"Prepared source-node identities are missing."}
	for node in source_map:
		var id: String=str(source_map[node])
		if source_ids.has(id):return {"error":"A prepared bone has ambiguous source-node identities."}
		source_ids[id]=node
	for id in actor.order:
		if not actor.bones.has(id) or not source_ids.has(id):return {"error":"A bone has no unique prepared source-node identity."}
		var item: Dictionary=actor.bones[id]
		if not is_instance_valid(item.get("skeleton")) or not item.skeleton is Skeleton3D:return {"error":"A bone's actual skeleton is missing."}
		if skeleton==null:skeleton=item.skeleton
		elif skeleton!=item.skeleton:return {"error":"Multiple skeletons in one part are ambiguous for this following mode."}
	if not actor.root.is_ancestor_of(skeleton) or skeleton.get_bone_count()!=actor.order.size():return {"error":"The model must own its complete independent skeleton."}
	var count: int=skeleton.get_bone_count()
	var ids: Array=[];var names: Array=[];var parents: Array=[];var rests: Array=[];var source_nodes: Array=[]
	ids.resize(count);names.resize(count);parents.resize(count);rests.resize(count);source_nodes.resize(count)
	var by_name:={};var ambiguous:={}
	for id in actor.order:
		var item: Dictionary=actor.bones[id];var index: int=item.index
		if index<0 or index>=count or ids[index]!=null or str(skeleton.get_bone_name(index))!=item.name:return {"error":"Prepared bone identity changed."}
		ids[index]=id;names[index]=item.name;parents[index]=skeleton.get_bone_parent(index);rests[index]=skeleton.get_bone_rest(index);source_nodes[index]=source_ids[id]
		if by_name.has(item.name):ambiguous[item.name]=true
		else:by_name[item.name]=index
	var pending: Array=range(count);var order: Array=[]
	while not pending.is_empty():
		var progressed:=false
		for at in range(pending.size()-1,-1,-1):
			var index: int=pending[at];var parent: int=parents[index]
			if parent< -1 or parent>=count or parent==index:return {"error":"Invalid prepared bone parent."}
			if parent>=0 and not parent in order:continue
			order.append(index);pending.remove_at(at);progressed=true
		if not progressed:return {"error":"Cyclic bone parents cannot follow."}
	var forbidden:={}
	var ownership:=ownership_inputs(actor)
	if ownership.has("error"):return ownership
	var native: Dictionary=ownership.native
	if native is Dictionary and native.get("bones") is Array:
		# Retained names/parents are used only to exclude declared procedural
		# owners and their descendants. Rule values/fidelity are never certified.
		if not native.has("source_jiggle"):return {"error":"Native procedural ownership is unavailable; keep this part independent."}
		var catalogue: Array=native.bones;var jiggle=native.get("source_jiggle",{})
		if not jiggle is Dictionary:return {"error":"Procedural ownership metadata is incomplete."}
		var rules=jiggle.get("rules",[])
		var unsupported=jiggle.get("unsupported",[])
		if not rules is Array or rules.size()>4096 or not unsupported is Array or not unsupported.is_empty():return {"error":"Procedural ownership is incomplete; keep this part independent."}
		var declared=jiggle.get("declared_jiggle_rule_count",0)
		if not (declared is int or declared is float) or not is_finite(float(declared)) or declared!=floor(declared) or declared<0 or declared>4096:return {"error":"The declared procedural joint count is invalid."}
		if int(declared)!=rules.size():return {"error":"Some declared procedural joints are unresolved."}
		for rule in rules:
			if not rule is Dictionary:return {"error":"Invalid retained procedural owner."}
			var raw_index=rule.get("native_bone_index",-1)
			if not (raw_index is int or raw_index is float) or not is_finite(float(raw_index)) or raw_index!=floor(raw_index):return {"error":"Invalid retained procedural bone index."}
			var native_index: int=int(raw_index)
			if native_index<0 or native_index>=catalogue.size() or not catalogue[native_index] is Dictionary or catalogue[native_index].get("name")!=rule.get("native_bone_name"):return {"error":"A declared procedural owner is ambiguous."}
			var name: String=str(rule.native_bone_name)
			if not by_name.has(name) or ambiguous.has(name):return {"error":"A procedural owner cannot be identified in the prepared rig."}
			forbidden[by_name[name]]=true
	var secondary: Dictionary=ownership.secondary
	if secondary is Dictionary:
		if not str(secondary.get("error","")).is_empty():return {"error":"Declared secondary-joint bindings are invalid."}
		for chain in secondary.get("chains",[]):
			for joint in chain.get("joints",[]):
				var binding=joint.get("binding",{})
				if binding.get("kind")=="bone":
					var index: int=ids.find(str(binding.get("id","")))
					if index<0:return {"error":"A secondary joint has no owned prepared bone."}
					forbidden[index]=true
	for index in order:
		if parents[index]>=0 and forbidden.has(parents[index]):forbidden[index]=true
	var relative: Transform3D=relative_to(actor.root,skeleton)
	var imported: Array=[]
	for index in range(count):imported.append(actor.base_root*relative*skeleton.get_bone_global_rest(index))
	return {"actor":actor,"skeleton":skeleton,"root_id":actor.root.get_instance_id(),"skeleton_id":skeleton.get_instance_id(),"sha256":actor.data.sha256,"ids":ids,"names":names,"parents":parents,"rests":rests,"source_nodes":source_nodes,"source_map":source_map.duplicate(),"ownership":ownership.signature.duplicate(true),"by_name":by_name,"ambiguous":ambiguous,"forbidden":forbidden,"order":order,"imported":imported,"relative":relative}

static func plan(master: RefCounted,target: RefCounted,bundle: Node3D) -> Dictionary:
	var a:=inventory(master);var b:=inventory(target)
	if a.has("error"):return a
	if b.has("error"):return b
	if master==target or a.skeleton==b.skeleton or master.root.get_parent()!=bundle or target.root.get_parent()!=bundle:return {"error":"Body and part need separate sibling rigs under the same character."}
	var links:={};var ambiguous:=0;var unmatched:=0;var procedural:=0
	for index in b.order:
		var name: String=b.names[index]
		if a.ambiguous.has(name) or b.ambiguous.has(name):ambiguous+=1;continue
		if not a.by_name.has(name):unmatched+=1;continue
		var source: int=a.by_name[name]
		if a.forbidden.has(source) or b.forbidden.has(index):procedural+=1;continue
		var ap: int=a.parents[source];var bp: int=b.parents[index]
		if (ap<0)!=(bp<0) or (ap>=0 and a.names[ap]!=b.names[bp]) or not same(a.imported[source],b.imported[index]):unmatched+=1;continue
		if bp>=0 and not links.has(bp):unmatched+=1;continue
		links[index]=source
	return {"master":a,"target":b,"bundle":bundle,"links":links,"matched":links.size(),"unmatched":unmatched,"ambiguous":ambiguous,"procedural":procedural,"native_fidelity_qualified":false}

static func phase_error(rig: Dictionary) -> String:
	var actor: RefCounted=rig.actor;var skeleton: Skeleton3D=rig.skeleton
	if not is_instance_valid(actor.root) or not actor.root.is_inside_tree() or not is_instance_valid(skeleton):return "The part is detached or freed."
	if actor.get_script()!=Model or actor.root.get_instance_id()!=rig.root_id or skeleton.get_instance_id()!=rig.skeleton_id or actor.data.sha256!=rig.sha256:return "The prepared rig changed; reload the part."
	if actor.live_pose!=null or actor.live_world_transform!=null:return "Following pauses while live hair, clothes or body physics owns either rig."
	if not actor.evaluation_error.is_empty():return "Following pauses because a model's authored pose could not be evaluated."
	var ownership:=ownership_inputs(actor)
	if ownership.has("error"):return ownership.error
	if ownership.signature!=rig.ownership:return "Procedural joint ownership changed; reload the part before following."
	if not PoseBounds.final_pose(skeleton).is_empty():return "Following pauses while a final simulation pose is active."
	if not same(relative_to(actor.root,skeleton),rig.relative):return "The imported skeleton frame changed; reload the part."
	var visible: Array=skeleton.get_children()
	for child in skeleton.find_children("*","SkeletonModifier3D",false,false):
		var simulator:=child as PhysicalBoneSimulator3D
		# Imported Godot4.6 rigs contain an internal compatibility simulator with
		# active=true, but no physical bones. It cannot write any joint. Explicit
		# user modifiers, scripts, children or actual simulation remain excluded.
		if child in visible or simulator==null or simulator.get_class()!="PhysicalBoneSimulator3D" or simulator.get_script()!=null or simulator.is_simulating_physics() or simulator.get_child_count(true)!=0:return "An external skeleton modifier owns this rig."
	if skeleton.get_bone_count()!=rig.ids.size() or actor.order.size()!=rig.ids.size():return "The prepared bone inventory changed."
	var source_map=actor.root.get_meta("has_source_bones",{})
	if not source_map is Dictionary or source_map!=rig.source_map:return "Prepared source-node identities changed."
	for index in range(rig.ids.size()):
		if not actor.bones.has(rig.ids[index]) or actor.bones[rig.ids[index]].skeleton!=skeleton or actor.bones[rig.ids[index]].index!=index or str(skeleton.get_bone_name(index))!=rig.names[index] or skeleton.get_bone_parent(index)!=rig.parents[index] or skeleton.get_bone_rest(index)!=rig.rests[index] or source_map.get(rig.source_nodes[index])!=rig.ids[index]:return "A prepared bone binding or rest changed."
	return ""

static func snapshot(rig: Dictionary) -> Dictionary:
	var why:=phase_error(rig)
	if not why.is_empty():return {"error":why}
	var skeleton: Skeleton3D=rig.skeleton;skeleton.force_update_all_bone_transforms()
	var locals: Array=[];var globals: Array=[];globals.resize(rig.ids.size())
	for index in range(rig.ids.size()):
		var value: Transform3D=skeleton.get_bone_pose(index)
		if not Math.finite_frame(value):return {"error":"A pose contains an unsupported transform."}
		locals.append(value)
	for index in rig.order:
		var parent: int=rig.parents[index]
		globals[index]=globals[parent]*locals[index] if parent>=0 else locals[index]
		if not same(globals[index],skeleton.get_bone_global_pose(index)):return {"error":"An external bone override prevents safe following."}
	return {"locals":locals,"globals":globals}

func apply_plan(value: Dictionary) -> String:
	var a: Dictionary=value.master;var b: Dictionary=value.target
	var source:=snapshot(a);var target:=snapshot(b)
	if source.has("error"):return source.error
	if target.has("error"):return target.error
	var bundle: Node3D=value.bundle
	if not is_instance_valid(bundle) or not bundle.is_inside_tree() or not Math.finite_frame(bundle.global_transform):return "The character root is unavailable."
	if a.actor.root.get_parent()!=bundle or b.actor.root.get_parent()!=bundle:return "A part left the character's sibling hierarchy."
	var source_frame: Transform3D=relative_to(bundle,a.skeleton)
	var target_frame: Transform3D=relative_to(bundle,b.skeleton)
	var solved: Array=[];solved.resize(b.ids.size());var prepared:={}
	for index in b.order:
		var parent: int=b.parents[index]
		var desired: Transform3D=solved[parent]*target.locals[index] if parent>=0 else target.locals[index]
		if value.links.has(index):
			var source_index: int=value.links[index]
			var goal:=Math.goal(a.imported[source_index],source_frame*source.globals[source_index],target_frame*target.globals[index])
			if goal.has("error"):return goal.error
			desired=target_frame.affine_inverse()*goal.world_goal
			var local:=Math.local_goal(solved[parent] if parent>=0 else Transform3D.IDENTITY,desired)
			if local.has("error"):return local.error
			var wanted: Transform3D=local.local_goal
			if wanted.basis.determinant()<=0:return "Reflected joint transforms are unsupported for following."
			var rotation: Quaternion=wanted.basis.orthonormalized().get_rotation_quaternion().normalized()
			var scale: Vector3=wanted.basis.get_scale()
			var canonical:=Transform3D(Basis(rotation).scaled(scale),wanted.origin)
			if not same(canonical,wanted):return "Following would introduce shear; keep this part independent."
			prepared[index]={"position":wanted.origin,"rotation":rotation,"scale":scale}
		solved[index]=desired
	# Every candidate local was checked before the first write. Authored Model.data
	# remains untouched; the next ordinary Model.apply replaces derived channels.
	for index in prepared:
		b.skeleton.set_bone_pose_position(index,prepared[index].position)
		b.skeleton.set_bone_pose_rotation(index,prepared[index].rotation)
		b.skeleton.set_bone_pose_scale(index,prepared[index].scale)
	b.skeleton.force_update_all_bone_transforms();b.actor.refresh_render_bounds();frame_applications+=1
	return ""

func inspect(runtime: RefCounted,target_id: String,reference_id: String="") -> Dictionary:
	var target: RefCounted=runtime.instance(target_id)
	if target==null:return {"error":"Select a character part."}
	if not target.data.get("metadata",{}).get("character_part",{}) is Dictionary:return {"error":"Character-part settings must be an object."}
	var group: RefCounted=runtime.instance(str(target.data.get("parent_id","")))
	if group==null:return {"error":"The part has no character root."}
	var metadata=group.data.get("metadata",{}).get("character_parts",{})
	if not metadata is Dictionary or metadata.get("format")!="studio_character_parts_1":return {"error":"The character's part settings are invalid."}
	var master_id: String=reference_id if not reference_id.is_empty() else str(metadata.get("follow_reference_id",metadata.get("height_reference_id","")))
	var master: RefCounted=runtime.instance(master_id)
	if master==null:return {"error":"The body's reference part is missing."}
	if master==target:return {"error":"This is the body reference itself."}
	if not is_instance_valid(master.root) or not is_instance_valid(target.root) or not is_instance_valid(group.root):return {"error":"A character part was freed."}
	if master.data.get("parent_id")!=group.data.id:return {"error":"The body reference must belong to the same character."}
	var key: String=str(master.root.get_instance_id())+":"+str(target.root.get_instance_id())
	if not plans.has(key):plans[key]=plan(master,target,group.root)
	var value: Dictionary=plans[key]
	if value.has("error"):return value.duplicate(true)
	return {"matched":value.matched,"unmatched":value.unmatched,"ambiguous":value.ambiguous,"procedural":value.procedural,"native_fidelity_qualified":false,"plan_key":key}

func evaluate(runtime: RefCounted) -> void:
	reports.clear()
	for id in runtime.order:
		var actor: RefCounted=runtime.instance(id)
		var settings=actor.data.get("metadata",{}).get("character_part",{})
		if not settings is Dictionary:
			reports[id]={"error":"Character-part settings must be an object."};continue
		if not settings.get("follow_body",false) is bool:
			reports[id]={"error":"Follow body must be On or Off."};continue
		if settings.get("follow_body",false)!=true:continue
		var status:=inspect(runtime,id)
		if not status.has("error"):
			if status.matched==0:status["error"]="No unambiguous compatible joints were found."
			else:
				var why: String=apply_plan(plans[status.plan_key])
				if not why.is_empty():status["error"]=why
		reports[id]=status

func dispose() -> void:
	plans.clear();reports.clear()
