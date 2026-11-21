extends SceneTree
# Authored UNRUN. All model/transform/image data stays inside mandatory-new output.
const Renderer=preload("res://src/renderer.gd")
const RenderBounds=preload("res://src/posed_render_bounds.gd")
const ARCHIVE_SHA:="d304744dea70a05e7176b668bc10b0058b8cb4e6b1ffe5fc9fab05303da60efb"
const ASSET_SHA:="e3e233004f2ce1aed3c2f221f7d92d9218c0de1f133cad88557f8181644e6e8c"
var renderer: Node
var actor: RefCounted
var head: MeshInstance3D
var control: RefCounted
var folder:=""
var archive:=""
var project: Dictionary
var checks:=0
var failures:=0
var rows: Array=[]

func _initialize() -> void:
	create_timer(150).timeout.connect(func():push_error("Private posed-head controls watchdog");quit(2))
	call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func require_ok(ok: bool,label: String) -> bool:
	if not ok:push_error(label);failures+=1
	return ok
func digest(value) -> String:
	var hashing:=HashingContext.new();hashing.start(HashingContext.HASH_SHA256);hashing.update(var_to_bytes(value));return hashing.finish().hex_encode()
func raw_image_hash(image: Image) -> String:
	var hashing:=HashingContext.new();hashing.start(HashingContext.HASH_SHA256);hashing.update(image.get_data());return hashing.finish().hex_encode()
func weights() -> Array:
	var result:=[]
	for i in range(head.get_blend_shape_count()):result.append(head.get_blend_shape_value(i))
	return result
func morph_state() -> Array:
	return [head.custom_aabb,head.has_meta("has_shape_bounds"),head.get_meta("has_shape_bounds",AABB()),weights()]
func actor_state() -> String:
	return JSON.stringify(actor.data,"",true,true)
func pose_token(frame: int,editing: bool) -> String:
	return digest([actor.sample_body(frame,editing),actor.sample_transform(frame,editing),morph_state()])
func resolve_head(root_node: Node) -> Dictionary:
	var meshes: Array=root_node.find_children("*","MeshInstance3D",true,false)
	if root_node is MeshInstance3D:meshes.push_front(root_node)
	var matches:=[]
	for mesh in meshes:
		for surface in range(mesh.mesh.get_surface_count()):
			var material: Material=mesh.get_active_material(surface)
			if material is BaseMaterial3D and material.resource_name=="face":matches.append({"mesh":mesh,"surface":surface})
	return matches[0] if matches.size()==1 else {}

# Independent current-array skin evaluation. It does not call the envelope or
# PoseBounds palette/vertex helpers. This proves CPU containment/source binding;
# actual renderer skinning/order and visible-face restoration remain separate.
func cpu_geometry() -> Dictionary:
	var sk=head.get_node_or_null(head.skeleton)
	if not sk is Skeleton3D or head.skin==null:return {"error":"Explicit native skin unavailable."}
	sk.force_update_all_bone_transforms()
	var palette:=[];var binding_tokens:=[]
	for slot in range(head.skin.get_bind_count()):
		var name: StringName=head.skin.get_bind_name(slot)
		var bone: int=sk.find_bone(name) if not name.is_empty() else head.skin.get_bind_bone(slot)
		if bone<0 or bone>=sk.get_bone_count():return {"error":"Native CPU bind unavailable."}
		var posed: Transform3D=sk.get_bone_global_pose(bone)*head.skin.get_bind_pose(slot)
		palette.append(posed);binding_tokens.append([str(name),bone,head.skin.get_bind_pose(slot),sk.get_bone_global_pose(bone)])
	var points:=PackedVector3Array();var source_tokens:=[]
	for surface in range(head.mesh.get_surface_count()):
		var arrays: Array=head.mesh.surface_get_arrays(surface)
		var positions: PackedVector3Array=arrays[Mesh.ARRAY_VERTEX]
		var joints=arrays[Mesh.ARRAY_BONES];var amounts=arrays[Mesh.ARRAY_WEIGHTS]
		if not joints is PackedInt32Array or not amounts is PackedFloat32Array:return {"error":"Native CPU weights unavailable."}
		var stride:=int(joints.size()/positions.size()) if not positions.is_empty() else 0
		if stride not in [4,8] or joints.size()!=positions.size()*stride or amounts.size()!=joints.size():return {"error":"Native CPU weight layout differs."}
		source_tokens.append([positions,joints,amounts])
		for v in range(positions.size()):
			var point:=Vector3.ZERO;var total:=0.
			for influence in range(stride):
				var amount: float=amounts[v*stride+influence];var bind: int=joints[v*stride+influence]
				if not is_finite(amount) or amount<0:return {"error":"Invalid native CPU amount."}
				if amount==0:continue
				if bind<0 or bind>=palette.size():return {"error":"Invalid native CPU bind."}
				point+=(palette[bind]*positions[v])*amount;total+=amount
			if not point.is_finite() or absf(total-1.)>.001:return {"error":"Native CPU amount profile differs."}
			points.append(point)
	return {"points":points,"binding_sha256":digest([source_tokens,binding_tokens]),"vertices":points.size()}
func evaluate_context(frame: int,editing: bool) -> void:
	renderer.evaluate(project.camera_keys,frame)
	renderer.world_runtime.evaluate(frame,false,actor.data.id if editing else "",renderer.video_settings)
func original_margin_restored(before_margin: float,before_morph: Array,before_data: String) -> bool:
	return head.extra_cull_margin==before_margin and morph_state()==before_morph and actor_state()==before_data
func cpu_context(frame: int,editing: bool) -> Dictionary:
	evaluate_context(frame,editing)
	var before_data:=actor_state();var before_morph:=morph_state();var before_margin:=head.extra_cull_margin
	var created:=RenderBounds.create([head]);check(created.has("control"),"native explicit head control prepares")
	if not created.has("control"):return {}
	control=created.control
	var refreshed: Dictionary=control.refresh()
	check(not refreshed.has("error") and refreshed.updated==1 and is_finite(head.extra_cull_margin),"native current palette derives finite padding")
	var geometry:=cpu_geometry();var contained:=not geometry.has("error")
	var native_box: AABB=head.custom_aabb if head.custom_aabb.size.length_squared()>0 else head.mesh.get_aabb()
	if contained:
		for point in geometry.points:contained=contained and native_box.grow(head.extra_cull_margin).encloses(AABB(point,Vector3.ZERO))
	check(contained and geometry.get("vertices")==5361,"all5361 independent current-array skinned vertices are enclosed")
	var margin: float=head.extra_cull_margin;var array_reads: int=control.stats.inventory_array_reads
	var warm_ok:=true
	for i in range(50):
		var warm: Dictionary=control.refresh();warm_ok=warm_ok and not warm.has("error") and warm.updated==0 and head.extra_cull_margin==margin
	check(warm_ok and control.stats.inventory_array_reads==array_reads and control.stats.hot_array_reads==0,"native warm50 has no growth writes or hot vertex scans")
	check(morph_state()==before_morph,"native85neutral morphs and custom bounds remain unchanged")
	check(actor_state()==before_data,"native authored pose and root data remain unchanged")
	var token:=pose_token(frame,editing);control.dispose();control=null
	check(original_margin_restored(before_margin,before_morph,before_data),"native disposal restores only derived margin")
	var again:=RenderBounds.create([head]);var deterministic:=again.has("control")
	if deterministic:
		control=again.control;var second: Dictionary=control.refresh();deterministic=not second.has("error") and head.extra_cull_margin==margin
		control.dispose();control=null
	check(deterministic and original_margin_restored(before_margin,before_morph,before_data),"native fresh control is deterministic and restores state")
	return {"frame":frame,"editing":editing,"pose_sha256":token,"binding_sha256":geometry.get("binding_sha256",""),"vertices":geometry.get("vertices",0),"contained":contained,"warm50_unchanged":warm_ok,"derived_margin":margin,"native_box":str(native_box)}
func capture_image(name: String) -> Dictionary:
	var image: Image
	for i in range(2):
		if not renderer.begin_native_readback():return {"error":"Native readback unavailable."}
		await renderer.native_frame_ready
		image=renderer.finish_native_readback()
	if image==null or image.is_empty():return {"error":"Native readback empty."}
	if image.save_png(folder.path_join(name))!=OK:return {"error":"Native PNG save failed."}
	return {"image":name,"dimensions":[image.get_width(),image.get_height()],"image_raw_sha256":raw_image_hash(image)}
func capture_group(frame: int,editing: bool,backoff: float,admission: Dictionary) -> void:
	evaluate_context(frame,editing)
	var geometry:=cpu_geometry()
	check(not geometry.has("error") and geometry.get("vertices")==5361 and geometry.get("binding_sha256")==admission.binding_sha256 and pose_token(frame,editing)==admission.pose_sha256 and admission.contained,"graphical pose and source weights match qualified native CPU geometry")
	var view: Dictionary=renderer.view_state();renderer.camera.global_position+=renderer.camera.global_basis.z.normalized()*backoff
	var before_data:=actor_state();var before_morph:=morph_state();var before_margin:=head.extra_cull_margin
	var label:="frame%d_%s_backoff%.2f" % [frame,"draft" if editing else "playback",backoff]
	var baseline: Dictionary=await capture_image(label+"_baseline.png")
	check(not baseline.has("error") and baseline.dimensions==[1920,1080],"private baseline image captured")
	var created:=RenderBounds.create([head]);var derived_ok:=created.has("control")
	if derived_ok:
		control=created.control;var refreshed: Dictionary=control.refresh();derived_ok=not refreshed.has("error") and is_finite(head.extra_cull_margin)
	check(derived_ok and morph_state()==before_morph and actor_state()==before_data,"opt-in derived padding preserves native source pose and morphs")
	var margin: float=head.extra_cull_margin
	var derived: Dictionary=await capture_image(label+"_derived.png")
	check(not derived.has("error") and derived.dimensions==[1920,1080],"private derived-control image captured")
	if control:control.dispose();control=null
	renderer.restore_view(view)
	check(original_margin_restored(before_margin,before_morph,before_data) and renderer.view_state()==view,"group disposal restores margin shot and all authored state")
	rows.append({"frame":frame,"editing":editing,"backoff":backoff,"baseline":baseline,"derived":derived,"derived_margin":margin,"pose_sha256":admission.pose_sha256,"binding_sha256":admission.binding_sha256,"camera_transform":str(view.transform),"native_cpu_geometry_admitted":true})
func finish(mode: String) -> void:
	if control:control.dispose();control=null
	var private_result:={"format":"has_private_posed_head_1102_controls_1","mode":mode,"private_do_not_publish":true,"checks":checks,"failures":failures,"source_archive_sha256":ARCHIVE_SHA,"source_asset_sha256":ASSET_SHA,"head_vertices":5361,"face_surface_vertices":1489,"neutral_imported_morph_targets":85,"rows":rows,"application_adopted":false,"visual_face_restoration_qualified":false,"nonuniform_renderer_order_qualified":false,"export_or_cold_qualified":false}
	var file:=FileAccess.open(folder.path_join("PRIVATE_RESULT.json"),FileAccess.WRITE)
	if file:file.store_string(JSON.stringify(private_result,"\t",true,true)+"\n");file.close()
	else:failures+=1
	print("POSED_HEAD_NATIVE_"+("CPU" if mode=="cpu" else "CAPTURES")+" "+JSON.stringify({"checks":checks,"failures":failures,"context_count":2,"capture_count":0 if mode=="cpu" else rows.size()*2,"source_archive_sha256":ARCHIVE_SHA,"source_asset_sha256":ASSET_SHA,"head_vertices":5361,"face_surface_vertices":1489,"neutral_imported_morph_targets":85,"application_adopted":false,"visual_face_restoration_qualified":false}))
	if renderer:renderer.queue_free()
	await process_frame;await process_frame
	quit(0 if failures==0 else 1)
func run() -> void:
	var args:=OS.get_cmdline_user_args()
	if not require_ok(args.size()==4,"Need archive new-output cpu|captures CPU-admission"):quit(2);return
	archive=args[0];folder=args[1];var mode: String=args[2]
	if not require_ok(mode in ["cpu","captures"] and FileAccess.get_sha256(archive)==ARCHIVE_SHA,"Protected archive or mode differs"):quit(2);return
	if not require_ok(not DirAccess.dir_exists_absolute(folder) and not FileAccess.file_exists(folder) and DirAccess.make_dir_recursive_absolute(folder)==OK,"Private output must be new"):quit(2);return
	var zip:=ZIPReader.new()
	if not require_ok(zip.open(archive)==OK,"Protected archive unavailable"):quit(2);return
	project=JSON.parse_string(zip.read_file("project.json").get_string_from_utf8())
	var bytes:=zip.read_file("assets/"+ASSET_SHA+".glb");zip.close()
	if not require_ok(project is Dictionary and project.world.objects.size()==1 and project.video.width==1920 and project.video.height==1080,"Protected project context differs"):quit(2);return
	var path:=folder.path_join("private-model.glb");var file:=FileAccess.open(path,FileAccess.WRITE)
	if not require_ok(file!=null,"Private working GLB unavailable"):quit(2);return
	file.store_buffer(bytes);file.close()
	if not require_ok(FileAccess.get_sha256(path)==ASSET_SHA,"Protected asset differs"):quit(2);return
	var document: Dictionary=project.world.duplicate(true);document.objects[0].source=path
	renderer=Renderer.new();root.add_child(renderer);renderer.setup(1920,1080);renderer.video_settings=project.video.duplicate(true);renderer.set_background("black");renderer.editor_grid.visible=false
	var prepared: Dictionary=renderer.prepare_world(document,int(project.video.duration_frames),project.video)
	if not require_ok(not prepared.has("error") and renderer.install_world(prepared),"Protected world unavailable"):await finish(mode);return
	actor=renderer.world_runtime.instance(renderer.world_runtime.order[0]);var resolved:=resolve_head(actor.root)
	if not require_ok(not resolved.is_empty(),"Unique protected face surface unavailable"):await finish(mode);return
	head=resolved.mesh
	if mode=="cpu":
		var vertices:=0
		for surface in range(head.mesh.get_surface_count()):vertices+=head.mesh.surface_get_array_len(surface)
		check(vertices==5361 and head.mesh.surface_get_array_len(resolved.surface)==1489 and head.get_blend_shape_count()==85,"protected head face-surface and85target inventory matches")
		check(weights().all(func(value):return value==0.),"all imported target amounts remain neutral")
		check(actor.data.get("shape_pose",{}).is_empty() and actor.data.get("shape_base",{}).is_empty(),"saved project has no authored active expression amounts")
		check(head.skin!=null and head.get_node_or_null(head.skeleton) is Skeleton3D and head.skin.get_bind_count()<=512,"protected explicit skin context is bounded")
		for context in [{"frame":0,"editing":false},{"frame":43,"editing":true}]:rows.append(cpu_context(context.frame,context.editing))
	else:
		var admission=JSON.parse_string(FileAccess.get_file_as_string(args[3]))
		if not require_ok(admission is Dictionary and admission.get("mode")=="cpu" and admission.get("checks")==20 and admission.get("failures")==0 and admission.get("source_archive_sha256")==ARCHIVE_SHA and admission.get("source_asset_sha256")==ASSET_SHA and admission.get("rows",[]).size()==2,"Qualified source-bound CPU admission required"):await finish(mode);return
		for index in range(2):
			var context: Dictionary=admission.rows[index]
			if not require_ok(context.get("frame")==[0,43][index] and context.get("editing")==[false,true][index] and context.get("contained") is bool and context.contained,"Exact independent CPU contexts required"):break
			for backoff in [0.,.1,.3,1.]:await capture_group(context.frame,context.editing,backoff,context)
		check(rows.size()==8 and FileAccess.get_sha256(archive)==ARCHIVE_SHA and FileAccess.get_sha256(path)==ASSET_SHA,"all16 private captures complete with original archive and GLB unchanged")
	await finish(mode)
