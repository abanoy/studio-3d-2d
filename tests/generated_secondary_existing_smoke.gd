extends SceneTree
# Optional protected input remains local; only scalar measurements are printed.
const Spring=preload("res://src/secondary_spring.gd")
const Motion=preload("res://src/generated_secondary_motion.gd")
const Definition=preload("res://src/secondary_rig.gd")
const Bounds=preload("res://src/pose_bounds.gd")
const Shape=preload("res://src/source_shape.gd")
var app
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(135).timeout.connect(func():push_error("Existing hair settling watchdog");quit(2))
	call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;if not ok:failures+=1
	print(("PASS " if ok else "FAIL ")+label)
func settle() -> void:
	for i in range(4):await process_frame
func worker(helper: Node) -> void:
	while helper.pid>0:await process_frame
	await settle()
func affected_centroid(actor: RefCounted,ids: Array) -> Dictionary:
	var center:=Vector3.ZERO;var count:=0;var loose_center:=Vector3.ZERO;var loose_count:=0;var context:={"error":"","palettes":{},"updated":{}}
	for item in actor.root.find_children("*","MeshInstance3D",true,false):
		var mesh: MeshInstance3D=item
		if mesh.mesh==null or mesh.skin==null:continue
		var sk=mesh.get_node_or_null(mesh.skeleton)
		if not sk is Skeleton3D:continue
		var palette: Array=Bounds.palette(mesh,context)
		if not context.error.is_empty():return {"error":context.error}
		var slots: Dictionary={}
		for slot in range(mesh.skin.get_bind_count()):
			var name: String=mesh.skin.get_bind_name(slot);var bone: int=sk.find_bone(name) if not name.is_empty() else mesh.skin.get_bind_bone(slot)
			if bone>=0 and str(actor.root.get_path_to(sk))+"::"+str(sk.get_bone_name(bone)) in ids:slots[slot]=true
		if slots.is_empty():continue
		for surface in range(mesh.mesh.get_surface_count()):
			var arrays: Array=mesh.mesh.surface_get_arrays(surface)
			var vertices: PackedVector3Array=Shape.vertices(mesh,surface,arrays[Mesh.ARRAY_VERTEX]);var bones: PackedInt32Array=arrays[Mesh.ARRAY_BONES];var weights: PackedFloat32Array=arrays[Mesh.ARRAY_WEIGHTS]
			if vertices.is_empty() or bones.is_empty():continue
			var stride: int=bones.size()/vertices.size()
			for v in range(vertices.size()):
				var influenced:=false;var point:=Vector3.ZERO;var loose_weight:=0.
				for slot in range(stride):
					var bind: int=bones[v*stride+slot];var weight: float=weights[v*stride+slot]
					influenced=influenced or weight>0. and slots.has(bind)
					if slots.has(bind):loose_weight+=weight
					point+=(palette[bind]*vertices[v])*weight
				if influenced:center+=mesh.global_transform*point;count+=1
				# Independently identify lengths mainly driven by the loose chain,
				# rather than averaging them together with mostly pinned roots.
				if loose_weight>=.5:loose_center+=mesh.global_transform*point;loose_count+=1
	return {"error":"","count":count,"center":center/maxi(1,count),"loose_count":loose_count,"loose_center":loose_center/maxi(1,loose_count)}
func evaluate(actor: RefCounted,without_contacts:=false,without_skin:=false) -> Dictionary:
	actor.live_pose=null;actor.apply(0,true)
	var definition: Dictionary={}
	if without_contacts:
		definition=actor.root.get_meta("has_secondary_rig").duplicate(true)
		for source_chain in definition.chains:
			for joint in range(source_chain.joints.size()):source_chain.joints[joint]=Motion.values(source_chain.joints[joint],true,joint)
	var made: Dictionary=Spring.construct(actor,definition)
	if made.has("error"):return made
	var runner: RefCounted=made.runner;var chain: Dictionary=runner.chains[0]
	if without_contacts:chain.natural_gravity=true
	if without_skin and runner.skin_contact:runner.skin_contact.dispose();runner.skin_contact=null
	var first: String=chain.ids[0];var end_binding: Dictionary=chain.source.joints[-1].binding
	var before: Vector3=Definition.binding_transform(actor,end_binding).origin;var anchor: Vector3=actor.bone_transform(first).origin
	var vertices_before: Dictionary=affected_centroid(actor,chain.ids)
	var core_frames: Dictionary={}
	for id in actor.order:
		if Motion.core(actor.data,actor.bones[id].name):core_frames[id]=actor.bone_transform(id)
	var issue:="";var pose: Dictionary={};var minimum_gap:=0.;var maximum_remaining:=0
	await settle()
	var started: int=Time.get_ticks_usec()
	for tick in range(720):
		actor.live_pose={};actor.apply_current(0,true)
		var step: Dictionary=runner.step(1./120.,Vector3.ZERO)
		if step.has("error"):issue=step.error;break
		pose=step.pose;actor.live_pose=pose;actor.apply_current(0,true)
		if runner.skin_contact:
			minimum_gap=minf(minimum_gap,runner.skin_contact.stats.minimum_gap)
			maximum_remaining=maxi(maximum_remaining,int(runner.skin_contact.stats.remaining_pairs))
	var final: Vector3=Definition.binding_transform(actor,end_binding).origin
	var vertices_after: Dictionary=affected_centroid(actor,chain.ids)
	var fixed: bool=actor.bone_transform(first).origin.is_equal_approx(anchor)
	var cores_held:=true
	for id in core_frames:cores_held=cores_held and actor.bone_transform(id).is_equal_approx(core_frames[id])
	var scalar: Dictionary={"error":issue,"tip_drop":before.y-final.y,"tip_travel":before.distance_to(final),"root_fixed":fixed,"core_joints_held":cores_held,"checked_core_joints":core_frames.size(),"rotating_joints":chain.ids.size(),"sampled_weighted_vertices":vertices_after.get("count",0),"centroid_drop":vertices_before.center.y-vertices_after.center.y,"majority_weighted_vertices":vertices_after.loose_count,"majority_weighted_centroid_drop":vertices_before.loose_center.y-vertices_after.loose_center.y,"average_tick_usec":float(Time.get_ticks_usec()-started)/720.,"minimum_contact_gap":minimum_gap,"maximum_remaining_contact_pairs":maximum_remaining,"final_remaining_contact_pairs":runner.skin_contact.stats.remaining_pairs if runner.skin_contact else 0}
	runner.dispose();actor.live_pose=null;actor.apply(0,true)
	scalar.restored=Definition.binding_transform(actor,end_binding).origin.is_equal_approx(before)
	return scalar
func run() -> void:
	var args: PackedStringArray=OS.get_cmdline_user_args()
	if args.size()!=5 or DisplayServer.get_name()!="headless":quit(2);return
	var folder: String=args[0];var source: String=args[1];var source_sha: String=FileAccess.get_sha256(source)
	root.size=Vector2i(1400,900);root.gui_embed_subwindows=true
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recent.json")
	root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	check(app.pose_editor.add_model(source).is_empty(),"ordinary Add model loads protected existing-rig copy")
	var actor: RefCounted=app.renderer.active_model();var original_data: Dictionary=actor.data.duplicate(true);var bone_count: int=actor.order.size()
	check(actor.root.get_meta("has_secondary_rig",{}).get("chains",[]).is_empty(),"saved original has no configured helper chains")
	var helper: Node=app.physics_editor.helper_editor;helper.open(true);await worker(helper)
	var selected:=-1
	for i in range(helper.assessment.get("regions",[]).size()):
		var row: Dictionary=helper.assessment.regions[i]
		if int(row.node)==int(args[2]) and int(row.primitive)==int(args[3]) and int(row.component)==int(args[4]):selected=i;break
	check(selected>=0,"review finds the requested connected back-hair region")
	if selected<0:await app.quit_studio();quit(1);return
	helper.select_part(selected);await worker(helper)
	if helper.preview.get("mode","")!="existing_joints":helper.existing_mode(true);await worker(helper)
	check(helper.preview_ready and helper.preview.get("can_apply",false) and helper.preview.get("mode","")=="existing_joints","ordinary setup offers supported existing-joint chain")
	var history: int=app.history.size();helper.apply();await worker(helper)
	actor=app.renderer.active_model()
	check(app.history.size()==history+1 and actor.data.metadata.get("generated_helpers",{}).get("source_skin_preserved",false),"Apply installs one reversible setup preserving source skin")
	check(actor.data.metadata.generated_helpers.get("changed_vertices",-1)==0 and actor.order.size()==bone_count and actor.data.metadata.generated_helpers.helper_nodes.size()==1,"existing setup changes no weights or skin bones and adds one unweighted endpoint")
	var authored: Dictionary=actor.data.duplicate(true);var rig_before: PackedByteArray=var_to_bytes(actor.root.get_meta("has_secondary_rig"))
	var keep: Dictionary=await evaluate(actor)
	check(keep.get("error","").is_empty() and keep.get("restored",false),"Keep shape runs existing tuning and Off restores the original pose despite contact")
	var ui=app.physics_editor.generated_motion_editor;ui.sync();ui.change(1);await settle();actor=app.renderer.active_model()
	check(Motion.setting(actor.data).get("mode")=="natural","ordinary preset enables gravity on configured existing joints")
	var natural: Dictionary=await evaluate(actor)
	check(natural.get("error","").is_empty() and natural.get("tip_drop",0.)>.05 and natural.get("sampled_weighted_vertices",0)>0 and natural.get("centroid_drop",0.)>.01,"protected weighted back-hair geometry and terminal actually settle downward")
	check(natural.get("root_fixed",false) and natural.get("core_joints_held",false) and natural.get("checked_core_joints",0)>0 and natural.get("restored",false),"body attachment and core joints stay fixed and Off restores authored diagonal hair")
	var comparable: Dictionary=actor.data.duplicate(true);comparable.metadata.erase(Motion.KEY)
	check(comparable==authored and var_to_bytes(actor.root.get_meta("has_secondary_rig"))==rig_before,"gravity preview preserves authored state and original chain declaration")
	# Private convenience artifact for later graphical review; no baked pose,
	# source arrays or owner assets are added to the public repository.
	app.has_project.save_file(folder.path_join("prepared-junko-natural.has"),"packed")
	while app.has_project.pid>0:await process_frame
	await settle()
	app.undo();await settle();check(Motion.setting(app.renderer.active_model().data).mode=="keep_shape","Undo removes Natural override without removing setup")
	app.undo();await settle();actor=app.renderer.active_model()
	check(actor.data==original_data and actor.order.size()==bone_count,"Undo setup restores exact original model declaration and skeleton")
	check(FileAccess.get_sha256(source)==source_sha,"protected input bytes remain unchanged")
	print("GENERATED_SECONDARY_EXISTING "+JSON.stringify({"checks":checks,"failures":failures,"user_profile":OS.get_user_data_dir(),"metrics":natural,"keep_metrics":keep,"source_preserved":FileAccess.get_sha256(source)==source_sha}))
	await app.quit_studio();quit(0 if failures==0 else 1)
