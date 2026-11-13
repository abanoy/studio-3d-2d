extends RefCounted
# Hidden imports and paused-frame transfer only. The caller owns admission,
# generation/lifecycle, display, simulation, and disposal of a returned model.
const SceneIO=preload("res://src/scene3d.gd")
const Model=preload("res://src/model.gd")
const Shape=preload("res://src/source_shape.gd")
const Groups=preload("res://src/wind_review_groups.gd")

static func error(message: String) -> Dictionary:
	return {"error":message}

static func whole(value,limit: int=100000) -> bool:
	return (value is int or value is float) and is_finite(value) and value==floor(value) and value>=0 and value<limit

static func document(path: String) -> Dictionary:
	var file:=FileAccess.open(path,FileAccess.READ)
	if not file:return error("Cannot read the reviewed model.")
	var size:=file.get_length()
	if size<20 or size>512*1024*1024:file.close();return error("The reviewed model is outside the preview size limit.")
	var header:=file.get_buffer(20)
	if header.decode_u32(0)!=0x46546c67 or header.decode_u32(4)!=2 or header.decode_u32(8)!=size or header.decode_u32(16)!=0x4e4f534a or header.decode_u32(12)>size-20:file.close();return error("The reviewed model has an invalid GLB header.")
	var parsed=JSON.parse_string(file.get_buffer(header.decode_u32(12)).get_string_from_utf8());file.close()
	return {"document":parsed} if parsed is Dictionary else error("The reviewed model has invalid source declarations.")

static func inventory(doc: Dictionary) -> Dictionary:
	var nodes=doc.get("nodes");var scenes=doc.get("scenes");var scene=doc.get("scene",0)
	if not nodes is Array or nodes.is_empty() or nodes.size()>100000 or not scenes is Array or not whole(scene,scenes.size()):return error("The model's source-node inventory is incomplete.")
	var parents:={};var active:={};var declared:={};var skin_joints:={}
	for i in nodes.size():
		if not nodes[i] is Dictionary or not nodes[i].get("children",[]) is Array:return error("Invalid source-node declarations.")
		for child in nodes[i].get("children",[]):
			if not whole(child,nodes.size()) or parents.has(int(child)) or int(child)==i:return error("Ambiguous source-node parents.")
			parents[int(child)]=i
	var walks:=0
	for i in nodes.size():
		var at: int=i;var seen:={}
		while at>=0:
			walks+=1
			if walks>1000000:return error("The source-node hierarchy exceeds the preview review budget.")
			if seen.has(at):return error("Cyclic source-node parents.")
			seen[at]=true;at=int(parents.get(at,-1))
	var pending=scenes[int(scene)].get("nodes",[]) if scenes[int(scene)] is Dictionary else null
	if not pending is Array:return error("Invalid active model scene.")
	pending=pending.duplicate()
	while not pending.is_empty():
		var value=pending.pop_back()
		if not whole(value,nodes.size()) or active.has(int(value)):return error("Ambiguous active model scene.")
		active[int(value)]=true;pending.append_array(nodes[int(value)].get("children",[]))
	var skins=doc.get("skins",[])
	if not skins is Array:return error("Invalid source skin table.")
	for skin in skins:
		if not skin is Dictionary or not skin.get("joints") is Array:return error("Invalid source skin.")
		for joint in skin.joints:
			if not whole(joint,nodes.size()):return error("Invalid source skin joint.")
			declared[int(joint)]=true;skin_joints[int(joint)]=true
		if skin.has("skeleton"):
			if not whole(skin.skeleton,nodes.size()):return error("Invalid source skin root.")
			declared[int(skin.skeleton)]=true
	var ex=doc.get("extensions",{});var extras=doc.get("extras",{})
	if not ex is Dictionary or not extras is Dictionary:return error("Invalid model extension declarations.")
	var vrm=ex.get("VRM",{})
	if not vrm is Dictionary:return error("Invalid original motion declarations.")
	var old=vrm.get("secondaryAnimation",{})
	if not old is Dictionary:return error("Invalid original motion declarations.")
	var refs: Array=[]
	for definition in [ex.get("VRMC_springBone",{}),extras.get("has_secondary_helpers_1",{})]:
		if not definition is Dictionary or not definition.get("springs",[]) is Array or not definition.get("colliders",[]) is Array:return error("Invalid motion declarations.")
		for chain in definition.get("springs",[]):
			if not chain is Dictionary or not chain.get("joints",[]) is Array:return error("Invalid motion chain.")
			for joint in chain.get("joints",[]):
				if not joint is Dictionary:return error("Invalid motion joint.")
				refs.append(joint.get("node"))
			if chain.get("center",-1)!=-1:refs.append(chain.center)
		for collider in definition.get("colliders",[]):
			if not collider is Dictionary:return error("Invalid motion collider.")
			refs.append(collider.get("node"))
	if not old.get("boneGroups",[]) is Array or not old.get("colliderGroups",[]) is Array:return error("Invalid original motion tables.")
	for group in old.get("boneGroups",[]):
		if not group is Dictionary or not group.get("bones",[]) is Array:return error("Invalid original motion group.")
		refs.append_array(group.get("bones",[]))
		if group.get("center",-1)!=-1:refs.append(group.center)
	for group in old.get("colliderGroups",[]):
		if not group is Dictionary:return error("Invalid original collider group.")
		refs.append(group.get("node"))
	for ref in refs:
		if not whole(ref,nodes.size()):return error("Invalid declared motion reference.")
		declared[int(ref)]=true
	var required:=active.duplicate();required.merge(declared,true)
	return {"nodes":nodes,"parents":parents,"active":active,"declared":declared,"skin_joints":skin_joints,"required":required}

static func import_actor(path: String,shape: Dictionary,holder: Node3D) -> Dictionary:
	var result:=SceneIO.load_glb(path)
	if result.has("error"):return result
	var model:=Model.new();model.root=result.scene;model.base_root=model.root.transform;model.data=Model.definition(path)
	quiesce(model.root)
	model.root.visible=false;holder.add_child(model.root);model.inventory(model.root)
	var problem:=Shape.check(model.root,shape)
	if not problem.is_empty():model.root.free();return error(problem)
	Shape.apply(model.root,shape)
	return {"model":model}

static func quiesce(node: Node) -> void:
	if node is Camera3D:node.current=false
	if node is AnimationPlayer:node.stop();node.autoplay="";node.process_mode=Node.PROCESS_MODE_DISABLED
	for child in node.get_children():quiesce(child)

static func shape_matches(actor: RefCounted,shape: Dictionary) -> bool:
	if not Shape.validate(shape).is_empty() or shape.get("enabled",true):return false
	var descriptor: Dictionary=actor.root.get_meta(Shape.META,{"error":"","rows":[]})
	if not descriptor.get("error","").is_empty():return false
	var rows:={}
	for row in descriptor.rows:
		if rows.has(str(row.node)) or not is_instance_valid(row.mesh) or not row.mesh.mesh or row.mesh.mesh.get_blend_shape_count()!=row.weights.size():return false
		rows[str(row.node)]=row
	for node in shape.get("overrides",{}):
		if not rows.has(node):return false
		for target in shape.overrides[node]:
			if int(target)>=rows[node].weights.size():return false
	for row in rows.values():
		var expected:=Shape.effective(row,shape)
		for i in expected.size():
			if row.mesh.get_blend_shape_value(i)!=PackedFloat32Array([expected[i]])[0]:return false
	return true

static func live_state(actor: RefCounted) -> Dictionary:
	if not actor or not is_instance_valid(actor.root) or not actor.root.is_inside_tree():return {}
	var pose:={}
	for id in actor.order:
		var info: Dictionary=actor.bones[id]
		if not is_instance_valid(info.skeleton):return {}
		pose[id]=info.skeleton.get_bone_pose(info.index)
	return {"root":actor.root.get_instance_id(),"transform":actor.root.global_transform,"data":actor.data.duplicate(true),"order":actor.order.duplicate(),"pose":pose,"shape":Shape.snapshot(actor.root)}

static func foreign_roots(actor: RefCounted) -> Array:
	var result: Array=[];var runtime: RefCounted=actor.world_context.get_ref() if actor.world_context else null
	if not runtime:return result
	var instances=runtime.get("instances")
	if instances is Dictionary:
		for current in instances.values():
			if current!=actor and current and is_instance_valid(current.root):result.append(current.root)
	var effects=runtime.get("effects")
	if effects is Dictionary:
		for effect in effects.values():
			if effect and is_instance_valid(effect.root):result.append(effect.root)
	return result

static func parent_identity(node: Node,actor: RefCounted,live: Dictionary,physical: Dictionary) -> Dictionary:
	if node==actor.root:return {"identity":[{"actor_boundary":true}]}
	var current:=node.get_parent();var chain: Array=[];var steps:=0
	while current!=null and steps<512:
		steps+=1
		if current==actor.root:chain.append({"actor_boundary":true});return {"identity":chain}
		var tag=current.get_meta(Shape.NODE_META,-1)
		if tag is int and tag>=0 and live.get(tag,[]).size()==1 and live[tag][0]==current:
			chain.append({"source_node":tag});return {"identity":chain}
		if current is Skeleton3D:
			var roots: Array=[]
			for index in current.get_bone_count():
				if current.get_bone_parent(index)<0:
					var key: String=str(current.get_instance_id())+":"+str(index)
					if not physical.has(key):return error("A skeleton wrapper has an unjoined root joint.")
					roots.append(physical[key])
			roots.sort();chain.append({"wrapper":"Skeleton3D","roots":roots,"local":current.transform})
		elif current is BoneAttachment3D:
			var skeleton: Skeleton3D=current.get_skeleton()
			var key: String=str(skeleton.get_instance_id())+":"+str(current.get_bone_idx()) if skeleton else ""
			if not physical.has(key) or current.get_override_pose():return error("An ancestor attachment has no exact source-joint join.")
			chain.append({"wrapper":"BoneAttachment3D","bone":physical[key],"local":current.transform})
		elif current is Node3D:chain.append({"wrapper":str(current.get_class()),"local":current.transform})
		else:return error("An imported ancestor has an unsupported runtime wrapper.")
		current=current.get_parent()
	return error("An imported parent does not remain inside its actor.")

static func bindings(actor: RefCounted,inv: Dictionary) -> Dictionary:
	var rows:={};var live:={};var runtime:={};var physical:={};var covered:={};var bones: Dictionary=actor.root.get_meta("has_source_bones",{})
	for node in bones:
		if not whole(node,inv.nodes.size()) or not actor.bones.has(bones[node]):return error("A source joint has no imported binding.")
		var id: String=bones[node];var info: Dictionary=actor.bones[id]
		if not info.get("skeleton") is Skeleton3D or not is_instance_valid(info.skeleton) or not whole(info.get("index"),info.skeleton.get_bone_count()) or not actor.root.is_ancestor_of(info.skeleton) and actor.root!=info.skeleton:return error("An imported joint's actual skeleton or index changed.")
		var name: String=str(info.skeleton.get_bone_name(info.index));var path: String=str(actor.root.get_path_to(info.skeleton));var key: String=str(info.skeleton.get_instance_id())+":"+str(info.index)
		if id!=path+"::"+name or info.get("name")!=name or info.get("path")!=path:return error("An imported joint's canonical identity changed.")
		if runtime.has(id) or physical.has(key):return error("Source joints share an actual imported bone.")
		runtime[id]=int(node);physical[key]=int(node);covered[id]=true
	if covered.size()!=actor.order.size():return error("An imported joint has no source-node identity.")
	var pending: Array=[actor.root];var excluded:=foreign_roots(actor)
	while not pending.is_empty():
		var node: Node=pending.pop_back()
		if node!=actor.root and node in excluded:continue
		pending.append_array(node.get_children())
		if not node is Node3D or node is Skeleton3D:continue
		var tag=node.get_meta(Shape.NODE_META,-1)
		if tag is int and tag>=0:
			if tag>=inv.nodes.size():return error("An imported source-node tag is outside its source.")
			if not live.has(tag):live[tag]=[]
			live[tag].append(node)
	for index in inv.nodes.size():
		var row: Dictionary={};var parent: int=inv.parents.get(index,-1)
		if bones.has(index):
			var id: String=bones[index];var info: Dictionary=actor.bones[id];var sk: Skeleton3D=info.skeleton
			var actual_parent: String=actor.parent_id(id);var expected_parent:=parent
			while expected_parent>=0 and not bones.has(expected_parent):expected_parent=int(inv.parents.get(expected_parent,-1))
			if int(runtime.get(actual_parent,-1 if actual_parent=="@root" else -2))!=expected_parent:return error("A joint's actual parent differs from its source-node join.")
			var observed_parent:=parent_identity(sk,actor,live,physical)
			if observed_parent.has("error"):return observed_parent
			row={"kind":"bone","id":id,"base":info.base,"global_base":sk.global_transform*sk.get_bone_global_pose(info.index),"parent":parent,"bone_parent":expected_parent,"skeleton_local":sk.transform,"runtime_parent":observed_parent.identity}
		else:
			var choices: Array=live.get(index,[])
			if choices.size()>1:return error("An imported source-node tag is ambiguous.")
			if choices.size()==1:
				var node: Node3D=choices[0]
				var observed_parent:=parent_identity(node,actor,live,physical)
				if observed_parent.has("error"):return observed_parent
				row={"kind":"node","id":str(actor.root.get_path_to(node)),"base":node.transform,"global_base":node.global_transform,"parent":parent,"runtime_parent":observed_parent.identity}
		if row.is_empty():
			if inv.required.has(index):return error("A required source node has no actual imported binding.")
			continue
		if inv.skin_joints.has(index) and row.kind!="bone":return error("A source skin joint is not an imported bone.")
		rows[index]=row
	for index in rows:
		var row: Dictionary=rows[index];var parent: Dictionary=rows.get(row.parent,{})
		if row.kind=="node" and parent.get("kind")=="bone":
			var node: Node3D=actor.root.get_node(NodePath(row.id));var attachment:=node.get_parent();var info: Dictionary=actor.bones[parent.id]
			if not attachment is BoneAttachment3D or attachment.get_skeleton()!=info.skeleton or attachment.get_bone_idx()!=info.index or attachment.get_override_pose():return error("A motion endpoint has an invalid bone attachment.")
			row.kind="offset";row["path"]=row.id;row.id=parent.id
			if row.global_base!=parent.global_base*row.base:return error("A motion endpoint differs from its parent-bone composition.")
	var definition: Dictionary=actor.root.get_meta("has_secondary_rig",{})
	if not definition.get("error","").is_empty():return error("Imported motion declarations need review.")
	var refs: Array=[]
	for chain in definition.get("chains",[]):
		for joint in chain.joints:refs.append(joint.binding)
		if not chain.center.is_empty():refs.append(chain.center)
	for collider in definition.get("colliders",[]):refs.append(collider.binding)
	for ref in refs:
		var row: Dictionary=rows.get(int(ref.source_node),{})
		if row.is_empty() or row.kind!=ref.kind or row.id!=str(ref.get("id",ref.get("path",""))):return error("A motion declaration has no exact imported source-node binding.")
		if ref.kind=="offset":
			var p: Array=ref.position;var q: Array=ref.rotation_xyzw;var s: Array=ref.scale
			if row.base!=Transform3D(Basis(Quaternion(q[0],q[1],q[2],q[3])).scaled(Vector3(s[0],s[1],s[2])),Vector3(p[0],p[1],p[2])):return error("A motion endpoint's descriptor differs from its actual local base.")
	return {"rows":rows}

static func transfer(original: Dictionary,derived: Dictionary,live: Dictionary,old_inv: Dictionary,new_inv: Dictionary,pose: Dictionary) -> Dictionary:
	if new_inv.nodes.size()<old_inv.nodes.size() or not Model.pose_valid(pose):return error("The paused pose or retained source-node inventory is invalid.")
	var map:={};var remapped:={}
	for index in old_inv.nodes.size():
		for field in ["mesh","skin"]:
			if old_inv.nodes[index].get(field,-1)!=new_inv.nodes[index].get(field,-1):return error("A retained source node changed ownership.")
		if old_inv.parents.get(index,-1)!=new_inv.parents.get(index,-1) or old_inv.active.has(index)!=new_inv.active.has(index) or old_inv.skin_joints.has(index)!=new_inv.skin_joints.has(index):return error("A retained source-node hierarchy changed.")
		var before: Dictionary=original.get(index,{});var after: Dictionary=derived.get(index,{});var current: Dictionary=live.get(index,{})
		if before.is_empty():
			if not after.is_empty() or not current.is_empty():return error("A retained source-node mapping changed.")
			continue
		if after.is_empty() or current.is_empty():return error("A retained source-node binding disappeared.")
		for key in ["kind","base","parent","runtime_parent"]:
			if before[key]!=after[key] or before[key]!=current[key]:return error("A retained imported binding or local base changed.")
		if before.global_base!=after.global_base:return error("A retained imported global base changed.")
		if before.kind=="bone":
			if before.bone_parent!=after.bone_parent or before.bone_parent!=current.bone_parent or before.skeleton_local!=current.skeleton_local:return error("A retained actual joint hierarchy changed.")
			map[current.id]=after.id
	for id in pose:
		if not map.has(id):return error("A paused pose channel has no explicit source-node join.")
		remapped[map[id]]=pose[id].duplicate(true)
	return {"bone_id_map":map,"pose":remapped}

static func catalogue(candidate: RefCounted,operations: Array,old_count: int,sha: String) -> Dictionary:
	if operations.is_empty() or operations.size()>128:return error("No reviewed helper setup is available.")
	var definition: Dictionary=candidate.root.get_meta("has_secondary_rig",{});var selected:={};var ids:={};var helper_ids:={};var chains_by_operation:={}
	for operation in operations:
		if not operation is Dictionary or not operation.get("operation_id") is String or operation.operation_id.length()!=64 or not operation.operation_id.is_valid_hex_number(false) or ids.has(operation.operation_id) or not operation.get("candidate_helper_nodes") is Array or operation.candidate_helper_nodes.is_empty() or not operation.get("configured_source_nodes") is Array:return error("Invalid reviewed helper identity.")
		ids[operation.operation_id]=true
		var nodes: Array=[];var configured:={}
		if not operation.get("mode") in ["existing_joints","weighted"]:return error("Invalid reviewed helper mode.")
		if operation.mode=="weighted" and not operation.configured_source_nodes.is_empty() or operation.mode=="existing_joints" and operation.configured_source_nodes.is_empty():return error("Invalid reviewed existing-joint identity.")
		for index in operation.configured_source_nodes:
			if not whole(index,old_count) or configured.has(int(index)):return error("Invalid or repeated original joint identity.")
			configured[int(index)]=true;nodes.append(int(index))
		for index in operation.candidate_helper_nodes:
			if not whole(index) or index<old_count or helper_ids.has(int(index)):return error("Invalid or repeated candidate helper identity.")
			helper_ids[int(index)]=true;nodes.append(int(index))
		var matching: Array=[]
		for i in definition.get("chains",[]).size():
			var actual: Array=[]
			for joint in definition.chains[i].joints:actual.append(int(joint.binding.source_node))
			if actual==nodes:matching.append(i)
		if matching.size()!=1 or selected.has(matching[0]):return error("A reviewed setup does not identify one actual candidate chain.")
		selected[matching[0]]=true;chains_by_operation[operation.operation_id]=matching[0]
	var parents:=Groups.parents(candidate);var linked:=Groups.vertex_links(candidate,definition.chains,parents)
	var links: Array=linked.get("links",[]);var notice:=""
	if not linked.get("error","").is_empty():
		for i in range(1,definition.chains.size()):links.append([0,i])
		notice="These joints are linked for this try-out because their weights could not be separated safely."
	var result:=Groups.build(definition,sha,parents,links)
	if result.has("error") and not result.error.is_empty():return result
	var checked: Array=[];var by_operation:={}
	for group in result.groups:
		for operation in chains_by_operation:
			if chains_by_operation[operation] in group.chain_indices:
				by_operation[operation]=group.id
				if not group.id in checked:checked.append(group.id)
	if by_operation.size()!=operations.size():return error("A checked helper setup has no actual motion group.")
	return {"catalog":result,"selected_group_ids":checked,"operation_group_ids":by_operation,"notice":notice}

static func prepare(source: RefCounted,candidate_path: String,shape_snapshot: Dictionary,baseline_pose: Dictionary,video: Dictionary,operations: Array,candidate_sha256: String) -> Dictionary:
	shape_snapshot=shape_snapshot.duplicate(true);baseline_pose=baseline_pose.duplicate(true);video=video.duplicate(true);operations=operations.duplicate(true)
	var before:=live_state(source)
	if before.is_empty() or not shape_matches(source,shape_snapshot):return error("The paused model or its shapes changed. Review the part again.")
	var source_path: String=source.data.source;var source_sha: String=source.data.sha256
	if not candidate_path.is_absolute_path() or candidate_sha256.length()!=64 or FileAccess.get_sha256(source_path)!=source_sha or FileAccess.get_sha256(candidate_path)!=candidate_sha256:return error("The reviewed source or candidate changed.")
	var first:=document(source_path);var second:=document(candidate_path)
	if first.has("error"):return first
	if second.has("error"):return second
	var old_inv:=inventory(first.document);var new_inv:=inventory(second.document)
	if old_inv.has("error"):return old_inv
	if new_inv.has("error"):return new_inv
	# A separate nonrendering world also isolates embedded cameras, lights and
	# environments while actual BoneAttachments receive their normal updates.
	var space:=SubViewport.new();space.name="HiddenHelperImportSpace";space.own_world_3d=true;space.render_target_update_mode=SubViewport.UPDATE_DISABLED;space.size=Vector2i(1,1);source.root.get_tree().root.add_child(space)
	var holder:=Node3D.new();holder.name="HiddenHelperBindingReview";holder.visible=false;space.add_child(holder)
	var first_import:=import_actor(source_path,shape_snapshot,holder)
	if first_import.has("error"):space.free();return first_import
	var second_import:=import_actor(candidate_path,shape_snapshot,holder)
	if second_import.has("error"):space.free();return second_import
	var neutral: RefCounted=first_import.model;var candidate: RefCounted=second_import.model
	var tree:=holder.get_tree()
	await tree.process_frame
	await tree.process_frame
	if not is_instance_valid(holder):
		if is_instance_valid(space):space.free()
		return error("The preview owner closed during preparation.")
	var result: Dictionary={}
	if live_state(source)!=before or FileAccess.get_sha256(source_path)!=source_sha or FileAccess.get_sha256(candidate_path)!=candidate_sha256:result=error("The model changed while the try-out was preparing.")
	else:
		var original:=bindings(neutral,old_inv);var derived:=bindings(candidate,new_inv);var current:=bindings(source,old_inv)
		for item in [original,derived,current]:
			if item.has("error"):result=item;break
		if result.is_empty():result=transfer(original.rows,derived.rows,current.rows,old_inv,new_inv,baseline_pose)
		if not result.has("error"):
			candidate.data.pose=result.pose.duplicate(true);candidate.data.metadata={"source_shape":shape_snapshot.duplicate(true)}
			candidate.live_pose=result.pose.duplicate(true);candidate.live_world_transform=before.transform
			candidate.apply(0,false,false,video,source.evaluated_opacity)
			await tree.process_frame
			await tree.process_frame
			if not is_instance_valid(holder) or live_state(source)!=before or FileAccess.get_sha256(source_path)!=source_sha or FileAccess.get_sha256(candidate_path)!=candidate_sha256:result=error("The model changed while its paused pose was being checked.")
			if not result.has("error"):
				var posed_original:=bindings(source,old_inv);var posed_candidate:=bindings(candidate,new_inv)
				if posed_original.has("error"):result=posed_original
				elif posed_candidate.has("error"):result=posed_candidate
				else:
					var old_inverse: Transform3D=source.root.global_transform.affine_inverse();var new_inverse: Transform3D=candidate.root.global_transform.affine_inverse()
					for index in original.rows:
						var a: Transform3D=old_inverse*posed_original.rows[index].global_base;var b: Transform3D=new_inverse*posed_candidate.rows[index].global_base
						if not a.is_equal_approx(b):result=error("A retained source node moved differently in the paused pose.");break
			if not result.has("error"):
				for id in result.bone_id_map:
					var old: Dictionary=source.bones[id];var new: Dictionary=candidate.bones[result.bone_id_map[id]]
					var a: Transform3D=old.skeleton.get_bone_pose(old.index);var b: Transform3D=new.skeleton.get_bone_pose(new.index)
					if not a.is_equal_approx(b):result=error("The paused pose no longer matches the reviewed baseline.");break
			if not result.has("error") and not shape_matches(candidate,shape_snapshot):result=error("The prepared shapes differ from the paused model.")
			if not result.has("error"):
				var groups:=catalogue(candidate,operations,old_inv.nodes.size(),candidate_sha256)
				if groups.has("error"):result=groups
				else:result.merge(groups,true)
	if not result.has("error"):
		holder.remove_child(candidate.root);candidate.root.visible=false
		result["model"]=candidate;result["source_sha256"]=source_sha;result["candidate_sha256"]=candidate_sha256
	if is_instance_valid(space):space.free()
	return result
