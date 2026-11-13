extends SceneTree
const SceneIO=preload("res://src/scene3d.gd")
const Model=preload("res://src/model.gd")
const Shape=preload("res://src/source_shape.gd")
var problems: Array=[]
func need(ok: bool,text: String) -> bool:
	if not ok:problems.append(text)
	return ok
func mat(t: Transform3D) -> Array:
	return [t.basis.x.x,t.basis.x.y,t.basis.x.z,0.,t.basis.y.x,t.basis.y.y,t.basis.y.z,0.,t.basis.z.x,t.basis.z.y,t.basis.z.z,0.,t.origin.x,t.origin.y,t.origin.z,1.]
func _initialize() -> void:call_deferred("run")
func source_audit(data: Dictionary) -> Array:
	var nodes: Array=data.nodes;var parents:={};var active:={};var declared:={};var joints:={}
	for i in range(nodes.size()):
		for child in nodes[i].get("children",[]):
			need(not parents.has(int(child)),"multiple source parents");parents[int(child)]=i
	var pending: Array=data.scenes[int(data.get("scene",0))].nodes.duplicate()
	while not pending.is_empty():
		var i:=int(pending.pop_back())
		if not need(not active.has(i),"cyclic or duplicate active traversal"):continue
		active[i]=true;pending.append_array(nodes[i].get("children",[]))
	for skin in data.get("skins",[]):
		for node in skin.get("joints",[]):declared[int(node)]=true;joints[int(node)]=true
		if skin.has("skeleton"):declared[int(skin.skeleton)]=true
	var ex: Dictionary=data.get("extensions",{});var old: Dictionary=ex.get("VRM",{}).get("secondaryAnimation",{})
	for declaration in [ex.get("VRMC_springBone",{}),data.get("extras",{}).get("has_secondary_helpers_1",{})]:
		for spring in declaration.get("springs",[]):
			for joint in spring.get("joints",[]):declared[int(joint.node)]=true
			if spring.get("center")!=null and spring.get("center")!=-1:declared[int(spring.center)]=true
		for collider in declaration.get("colliders",[]):declared[int(collider.node)]=true
	for group in old.get("boneGroups",[]):
		for node in group.get("bones",[]):declared[int(node)]=true
		if group.get("center")!=null and group.get("center")!=-1:declared[int(group.center)]=true
	for group in old.get("colliderGroups",[]):declared[int(group.node)]=true
	var rows: Array=[]
	for i in range(nodes.size()):rows.append({"source_node":i,"parent":int(parents.get(i,-1)),"children":nodes[i].get("children",[]),"mesh":int(nodes[i].get("mesh",-1)),"skin":int(nodes[i].get("skin",-1)),"active":active.has(i),"declared_reference":declared.has(i),"skin_joint":joints.has(i)})
	return rows
func run() -> void:
	var args:=OS.get_cmdline_user_args()
	if args.size()!=1 or not str(args[0]).is_absolute_path() or not FileAccess.file_exists(args[0]):printerr("BINDING_GATE invalid manifest argument");quit(2);return
	var plan=JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	if not plan is Dictionary or not plan.has_all(["input","output","sha256","nonce","shape"]):printerr("BINDING_GATE invalid plan");quit(2);return
	if FileAccess.file_exists(plan.output) or FileAccess.get_sha256(plan.input)!=plan.sha256:printerr("BINDING_GATE nonfresh output or changed input");quit(2);return
	var file:=FileAccess.open(plan.input,FileAccess.READ);var raw:=file.get_buffer(file.get_length());file.close()
	var parsed=JSON.parse_string(raw.slice(20,20+raw.decode_u32(12)).get_string_from_utf8())
	if not parsed is Dictionary:printerr("BINDING_GATE source JSON");quit(2);return
	var data: Dictionary=parsed;var audit:=source_audit(data)
	var imported: Dictionary=SceneIO.load_glb(plan.input)
	if imported.has("error"):printerr("BINDING_GATE import: "+str(imported.error));quit(2);return
	var scene: Node3D=imported.scene;root.add_child(scene)
	await process_frame;await process_frame
	var shape_error:=Shape.check(scene,plan.shape);need(shape_error.is_empty(),"shape setting: "+shape_error)
	if shape_error.is_empty():Shape.apply(scene,plan.shape)
	var actor:=Model.new();actor.root=scene;actor.inventory(scene)
	var bones: Dictionary=scene.get_meta("has_source_bones",{});var live:={};var pending: Array=[scene];var runtime_nodes:={}
	for source in bones:
		if not need(actor.bones.has(bones[source]),"bone map entry exists in actual inventory"):continue
		var info: Dictionary=actor.bones[bones[source]]
		var identity:=str(scene.get_path_to(info.skeleton))+"#"+str(info.index)
		need(not runtime_nodes.has(identity),"source nodes alias an actual bone");runtime_nodes[identity]=int(source)
	while not pending.is_empty():
		var node: Node=pending.pop_back();pending.append_array(node.get_children())
		if not node is Node3D or node is Skeleton3D:continue
		var index=node.get_meta("has_shape_source_node",-1)
		if not index is int or index<0:continue
		need(index<audit.size(),"live tag out of source inventory")
		if not live.has(index):live[index]=[]
		live[index].append(node)
	var table:={};var coverage: Array=[]
	for row in audit:
		var index: int=row.source_node;var binding: Dictionary={}
		if bones.has(index):
			var id: String=bones[index]
			if need(actor.bones.has(id),"source bone map has no actual Model.inventory binding: "+str(index)):
				var info: Dictionary=actor.bones[id];var sk: Skeleton3D=info.skeleton
				var parent_index:=sk.get_bone_parent(info.index)
				var actual_parent: int=-1 if parent_index<0 else int(runtime_nodes.get(str(scene.get_path_to(sk))+"#"+str(parent_index),-2))
				need(actual_parent>=-1,"actual bone parent has no source-node join "+str(index))
				binding={"runtime_parent_source_node":actual_parent,"kind":"bone","id":id,"base":mat(info.base),"global_base":mat(sk.global_transform*sk.get_bone_global_pose(info.index)),"runtime_identity":"bone:"+str(scene.get_path_to(sk))+"::"+str(info.index),"bone_index":info.index,"generated_bone_name":info.name}
		else:
			var candidates: Array=live.get(index,[])
			if candidates.size()==1:
				var node: Node3D=candidates[0];var path:=str(scene.get_path_to(node))
				binding={"kind":"node","id":path,"base":mat(node.transform),"global_base":mat(node.global_transform),"runtime_identity":"node:"+path,"live_source_tag":index}
			elif candidates.size()>1:need(false,"ambiguous actual source-node tag: "+str(index))
		if not binding.is_empty():
			binding.source_node=index;binding.source_parent=row.parent;table[str(index)]=binding
		coverage.append({"source_node":index,"status":"unmapped" if binding.is_empty() else "mapped","bone_map_present":bones.has(index),"live_tagged_nodes":live.get(index,[]).size()})
	for key in table:
		var binding: Dictionary=table[key];var parent: Dictionary=table.get(str(binding.source_parent),{})
		if binding.kind=="node" and parent.get("kind","")=="bone":
			binding.kind="offset";binding["live_path"]=binding.id;binding.id=parent.id
			var node: Node3D=scene.get_node(NodePath(binding.live_path));var attachment:=node.get_parent()
			binding["observed_node_local"]=mat(node.transform)
			var info: Dictionary=actor.bones[parent.id];var sk: Skeleton3D=info.skeleton
			binding["offset_composed_global"]=mat(sk.global_transform*sk.get_bone_global_pose(info.index)*node.transform)
			need(binding.offset_composed_global==binding.global_base,"offset live global equals parent-bone/local composition "+key)
			var attachment_source: int=-2
			if attachment is BoneAttachment3D:
				var attached: Skeleton3D=attachment.get_skeleton()
				if attached!=null:attachment_source=int(runtime_nodes.get(str(scene.get_path_to(attached))+"#"+str(attachment.get_bone_idx()),-2))
				need(not attachment.get_override_pose(),"offset attachment is observation-only "+key)
			need(attachment_source==int(binding.source_parent),"offset actual BoneAttachment source parent "+key)
			binding["runtime_attachment_parent_source_node"]=attachment_source
	var rig: Dictionary=scene.get_meta("has_secondary_rig",{})
	var refs: Array=[]
	for chain in rig.get("chains",[]):
		for joint in chain.joints:refs.append(joint.binding)
		if not chain.center.is_empty():refs.append(chain.center)
	for collider in rig.get("colliders",[]):refs.append(collider.binding)
	for ref in refs:
		var key:=str(ref.source_node)
		if not need(table.has(key),"declared secondary ref lacks actual source-node binding "+key):continue
		var observed: Dictionary=table[key]
		need(observed.kind==ref.kind,"declared secondary binding kind differs "+key)
		need(observed.id==str(ref.get("id",ref.get("path",""))),"declared secondary explicit runtime ID differs "+key)
		if ref.kind=="offset":
			var p: Array=ref.position;var q: Array=ref.rotation_xyzw;var scale: Array=ref.scale
			var local:=Transform3D(Basis(Quaternion(q[0],q[1],q[2],q[3])).scaled(Vector3(scale[0],scale[1],scale[2])),Vector3(p[0],p[1],p[2]))
			observed["secondary_offset_matrix"]=mat(local)
			need(observed.secondary_offset_matrix==observed.base,"secondary offset descriptor equals actual node local base "+key)
	var shapes: Array=[]
	for row in scene.get_meta(Shape.META,{"rows":[]}).rows:shapes.append({"source_node":row.node,"effective_weights":Shape.effective(row,plan.shape),"actual_weights":Array(range(row.mesh.mesh.get_blend_shape_count())).map(func(i):return row.mesh.get_blend_shape_value(i))})
	var result:={"format":"has_actual_imported_bindings_1","nonce":plan.nonce,"glb_sha256":FileAccess.get_sha256(plan.input),"node_count":audit.size(),"source_node_audit":audit,"bindings":table,"coverage":coverage,"secondary_error":str(rig.get("error","")),"secondary_chains":rig.get("chains",[]).size(),"secondary_colliders":rig.get("colliders",[]).size(),"shape":plan.shape,"shapes":shapes,"problems":problems,"scope":"headless actual import only; no GPU/physics/UI/live-body interop"}
	actor=null;scene.free();await process_frame
	var out:=FileAccess.open(plan.output,FileAccess.WRITE);out.store_string(JSON.stringify(result,"",true,true)+"\n");out.close()
	print("BINDING_GATE "+JSON.stringify({"problems":problems,"nodes":audit.size(),"bindings":table.size(),"nonce":plan.nonce}))
	quit(0 if problems.is_empty() else 1)
