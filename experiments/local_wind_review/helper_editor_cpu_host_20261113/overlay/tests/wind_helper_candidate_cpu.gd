extends SceneTree
const Candidate=preload("res://src/wind_helper_candidate.gd")
const Model=preload("res://src/model.gd")
const Shape=preload("res://src/source_shape.gd")
const Groups=preload("res://src/wind_review_groups.gd")
var checks: Array=[]
var failures: Array=[]
var video: Dictionary={"fps_num":24,"fps_den":1,"duration_frames":48,"width":1920,"height":1080,"lighting_mode":"studio"}
class TestWorld extends RefCounted:
	var instances: Dictionary={}
	var effects: Dictionary={}
func need(value: bool,label: String) -> void:
	checks.append(label)
	if not value:failures.append(label);printerr("FAIL "+label)
func _initialize() -> void:call_deferred("run")
func source_for(row: Dictionary) -> RefCounted:
	var imported:=Candidate.import_actor(row.source,row.shape,root.get_node("FixtureHolder"))
	if imported.has("error"):need(false,"source fixture imports: "+str(imported.error));return null
	var source: RefCounted=imported.model
	var id: String=source.root.get_meta("has_source_bones",{}).get(int(row.get("head_node",2)),"")
	need(not id.is_empty(),row.label+" actual Head source-node binding")
	var first:=Model.identity();var second: Dictionary={"position":[.06,-.02,.03],"rotation_xyzw":[0.,sin(.22),0.,cos(.22)]}
	source.data.pose_keys=[{"frame":0,"interpolation":"linear","pose":{id:first},"transform":{"position":[1.,.2,-.4],"rotation_xyzw":[0.,sin(.1),0.,cos(.1)],"scale":1.4}},{"frame":10,"interpolation":"linear","pose":{id:second},"transform":{"position":[1.3,.2,-.4],"rotation_xyzw":[0.,sin(.2),0.,cos(.2)],"scale":1.4}}]
	source.data.metadata={"source_shape":row.shape.duplicate(true)}
	source.apply(5,false,false,video)
	return source
func alter_during_wait(source: RefCounted) -> void:
	if is_instance_valid(source.root):source.data.name="New edit during preparation"
func free_during_wait(source: RefCounted) -> void:
	if is_instance_valid(source.root):source.root.free()
func run() -> void:
	var args:=OS.get_cmdline_user_args()
	if args.size()!=2:printerr("CANDIDATE_CPU arguments");quit(2);return
	var plan=JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	if not plan is Dictionary or not plan.get("cases") is Array:printerr("CANDIDATE_CPU plan");quit(2);return
	var holder:=Node3D.new();holder.name="FixtureHolder";holder.visible=false;root.add_child(holder)
	need(Candidate.inventory({}).has("error"),"missing inventory refuses")
	need(Candidate.inventory({"nodes":[{"children":[0]}],"scenes":[{"nodes":[0]}]}).has("error"),"source-node cycle refuses")
	need(Candidate.inventory({"nodes":[{}],"scenes":[{"nodes":[0]}],"extensions":[]}).has("error"),"malformed extension table refuses")
	for row in plan.cases:
		var source:=source_for(row)
		if not source:continue
		await process_frame;await process_frame
		var before:=Candidate.live_state(source);var count:=root.get_child_count();var pose: Dictionary=source.sample(5,false)
		var unknown_shape: Dictionary={"format":"studio_source_shape_2","enabled":false,"overrides":{"99999":{"0":.5}}}
		need(not Candidate.shape_matches(source,unknown_shape),row.label+" unknown morph node refuses safely")
		if not row.shape.get("overrides",{}).is_empty():
			var invalid_shape: Dictionary=row.shape.duplicate(true);var first_node: String=invalid_shape.overrides.keys()[0];invalid_shape.overrides[first_node]["2047"]=.5
			need(not Candidate.shape_matches(source,invalid_shape),row.label+" out-of-range actual morph target refuses before evaluation")
		var prepared: Dictionary=await Candidate.prepare(source,row.candidate,row.shape,pose,video,row.operations,row.candidate_sha256)
		need(not prepared.has("error"),row.label+" actual hidden candidate prepares: "+str(prepared.get("error","")))
		need(Candidate.live_state(source)==before,row.label+" original exact state unchanged")
		need(root.get_child_count()==count,row.label+" hidden import holder disposed")
		if not prepared.has("error"):
			var model: RefCounted=prepared.model
			need(model.root.get_parent()==null and not model.root.visible,row.label+" returned candidate detached and hidden")
			need(prepared.bone_id_map.size()==source.order.size(),row.label+" all original bone IDs joined")
			need(Candidate.shape_matches(model,row.shape),row.label+" frozen effective morph weights retained")
			need(prepared.operation_group_ids.size()==row.operations.size() and not prepared.selected_group_ids.is_empty(),row.label+" actual operation chain joins checked group")
			var selected:=Groups.filter(prepared.catalog,prepared.selected_group_ids)
			need(selected.get("error","").is_empty() and not selected.chains.is_empty(),row.label+" checked catalogue filters actual candidate")
			var original_head: String=source.root.get_meta("has_source_bones")[int(row.get("head_node",2))]
			var mapped: String=prepared.bone_id_map[original_head]
			need(model.data.pose[mapped]==pose[original_head],row.label+" recorded paused-frame channel remapped exactly")
			need(model.live_world_transform==source.root.global_transform,row.label+" original actor world transform retained separately")
			model.root.free()
		var bad_sha: Dictionary=await Candidate.prepare(source,row.candidate,row.shape,pose,video,row.operations,"0".repeat(64))
		need(bad_sha.has("error"),row.label+" candidate completion SHA mismatch refuses")
		var wrong: Dictionary=pose.duplicate(true);wrong["unmapped::Bone"]=Model.identity()
		var missing: Dictionary=await Candidate.prepare(source,row.candidate,row.shape,wrong,video,row.operations,row.candidate_sha256)
		need(missing.has("error"),row.label+" unknown paused pose channel refuses")
		var stale: Dictionary=pose.duplicate(true);var head: String=source.root.get_meta("has_source_bones")[int(row.get("head_node",2))];stale[head]=Model.identity()
		var outdated: Dictionary=await Candidate.prepare(source,row.candidate,row.shape,stale,video,row.operations,row.candidate_sha256)
		need(outdated.has("error"),row.label+" stale paused pose refuses")
		var changed: Array=row.operations.duplicate(true);changed[0].candidate_helper_nodes=[99999]
		var bad_group: Dictionary=await Candidate.prepare(source,row.candidate,row.shape,pose,video,changed,row.candidate_sha256)
		need(bad_group.has("error"),row.label+" wrong operation source-node chain refuses")
		need(root.get_child_count()==count and Candidate.live_state(source)==before,row.label+" all refusal routes retain source and release own imports")
		var doc:=Candidate.document(row.source);var inv:=Candidate.inventory(doc.document);var good:=Candidate.bindings(source,inv)
		need(not good.has("error"),row.label+" live posed source has complete actual bindings")
		if not good.has("error"):
			var map: Dictionary=source.root.get_meta("has_source_bones").duplicate();source.root.set_meta("has_source_bones",{})
			need(Candidate.bindings(source,inv).has("error"),row.label+" missing source bone tags cannot fake completeness")
			source.root.set_meta("has_source_bones",map)
			var first: String=source.order[0];var second: String=source.order[1];var saved: Dictionary=source.bones[second].duplicate()
			source.bones[second].skeleton=source.bones[first].skeleton;source.bones[second].index=source.bones[first].index
			need(Candidate.bindings(source,inv).has("error"),row.label+" distinct dictionary IDs cannot alias one physical bone")
			source.bones[second]=saved
			if row.has("ordinary_reparent"):
				var child: Node3D=source.root.get_node(NodePath(good.rows[int(row.ordinary_reparent.node)].id))
				var parent: Node3D=source.root.get_node(NodePath(good.rows[int(row.ordinary_reparent.parent)].id));var old_parent:=child.get_parent();var old_transform:=child.global_transform
				child.reparent(parent,false)
				need(child.global_transform==old_transform,"ordinary reparent control keeps neutral-equivalent global transform")
				var reparented: Dictionary=await Candidate.prepare(source,row.candidate,row.shape,pose,video,row.operations,row.candidate_sha256)
				need(reparented.has("error"),"actual ordinary-node parent change refuses despite equal transforms")
				child.reparent(old_parent,false)
		var peer:=source_for(plan.cases[0]);await process_frame;await process_frame
		peer.root.reparent(source.root)
		var world:=TestWorld.new();world.instances={source.data.id:source,peer.data.id:peer};source.world_context=weakref(world)
		var peer_before:=Candidate.live_state(peer)
		var with_child: Dictionary=await Candidate.prepare(source,row.candidate,row.shape,pose,video,row.operations,row.candidate_sha256)
		need(not with_child.has("error"),row.label+" separately owned child root excluded from source binding inventory: "+str(with_child.get("error","")))
		need(Candidate.live_state(peer)==peer_before and peer.root.get_parent()==source.root,row.label+" separate child exact state and parenting untouched")
		if not with_child.has("error"):with_child.model.root.free()
		source.world_context=null;world.instances.clear();peer.root.free()
		source.root.free()
	var last: Dictionary=plan.cases[-1]
	var edited:=source_for(last);await process_frame;await process_frame
	var pose: Dictionary=edited.sample(5,false);call_deferred("alter_during_wait",edited)
	var refused: Dictionary=await Candidate.prepare(edited,last.candidate,last.shape,pose,video,last.operations,last.candidate_sha256)
	need(refused.has("error") and edited.data.name=="New edit during preparation","late edit is kept and late candidate refused")
	edited.root.free()
	var freed:=source_for(last);await process_frame;await process_frame
	pose=freed.sample(5,false);call_deferred("free_during_wait",freed)
	refused=await Candidate.prepare(freed,last.candidate,last.shape,pose,video,last.operations,last.candidate_sha256)
	need(refused.has("error") and not is_instance_valid(freed.root),"source freed during import is safely refused")
	holder.free();await process_frame
	var out:=FileAccess.open(args[1],FileAccess.WRITE)
	out.store_string(JSON.stringify({"format":"has_wind_helper_candidate_cpu_1","checks":checks,"failures":failures,"headless":true,"gpu":false},"\t",true,true)+"\n");out.close()
	print("CANDIDATE_CPU "+JSON.stringify({"checks":checks.size(),"failures":failures.size()}))
	quit(0 if failures.is_empty() else 1)
