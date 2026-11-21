extends SceneTree
const Model=preload("res://src/model.gd")
const SceneIO=preload("res://src/scene3d.gd")
const Views=preload("res://src/reconstructed_rest_view.gd")
const Bounds=preload("res://src/pose_bounds.gd")
const Spring=preload("res://src/secondary_spring.gd")
var checks:=0
var failures:=0
func _initialize() -> void:call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func make(path: String) -> Dictionary:
	var loaded:=SceneIO.load_glb(path)
	if loaded.has("error"):return loaded
	var actor:=Model.new();actor.root=loaded.scene;actor.data=Model.definition(path);root.add_child(actor.root)
	var problem: String=actor.capture_import_root(actor.root.transform)
	if not problem.is_empty():actor.root.free();return {"error":problem}
	actor.inventory(actor.root);actor.apply(0,true);return {"actor":actor}
func mesh_of(actor: RefCounted) -> MeshInstance3D:
	for value in actor.root.find_children("*","MeshInstance3D",true,false):
		if value.has_meta(Views.PAIR):return value
	return null
func point_at(mesh: MeshInstance3D,surface: int,index: int) -> Vector3:
	var arrays: Array=mesh.mesh.surface_get_arrays(surface);var vertices: PackedVector3Array=arrays[Mesh.ARRAY_VERTEX];var bones: PackedInt32Array=arrays[Mesh.ARRAY_BONES];var weights: PackedFloat32Array=arrays[Mesh.ARRAY_WEIGHTS]
	var context:={"error":"","palettes":{},"updated":{}};var palette: Array=Bounds.palette(mesh,context);var stride: int=bones.size()/vertices.size();var p:=Vector3.ZERO
	for j in range(stride):p+=(palette[bones[index*stride+j]]*vertices[index])*weights[index*stride+j]
	return mesh.global_transform*p
func run() -> void:
	var args:=OS.get_cmdline_user_args()
	if args.size()!=4 or DisplayServer.get_name()!="headless":quit(2);return
	var source_sha:=FileAccess.get_sha256(args[1]);var candidate_sha:=FileAccess.get_sha256(args[2]);var made:=make(args[2])
	check(not made.has("error"),"metadata-bearing candidate imports original-weight auxiliary mesh")
	if made.has("error"):print(str(made.error));quit(1);return
	var actor: RefCounted=made.actor;var mesh: MeshInstance3D=mesh_of(actor)
	check(mesh!=null and actor.reconstruction_view_error.is_empty() and actor.reconstruction_view_diagnostics().active,"ordinary inventory owns the reconstructed mesh pair")
	if mesh==null:actor.root.free();quit(1);return
	var pair: Dictionary=mesh.get_meta(Views.PAIR);var source:=make(args[1]);var original_mesh: MeshInstance3D=source.actor.root.find_children("*","MeshInstance3D",true,false)[0]
	check(mesh.mesh==pair.rest,"exact authored guide rest selects original-weight mesh")
	var original_arrays_match:=true
	for s in range(mesh.mesh.get_surface_count()):original_arrays_match=original_arrays_match and mesh.mesh.surface_get_arrays(s)==original_mesh.mesh.surface_get_arrays(s)
	check(original_arrays_match,"rest view arrays exactly match original four-influence imported mesh")
	var shared:=true
	for s in range(mesh.mesh.get_surface_count()):shared=shared and pair.rest.surface_get_material(s)==pair.flex.surface_get_material(s)
	check(shared,"rest and flexible views share exact canonical material resources")
	var row: Dictionary=actor._rest_views._rows[0];var guide: String=row.guides[0].id;var base_data: Dictionary=actor.data.duplicate(true)
	var q:=Quaternion(Vector3.FORWARD,.2);var posed: Dictionary={guide:{"position":[0,0,0],"rotation_xyzw":[q.x,q.y,q.z,q.w]}}
	actor.data.pose=posed.duplicate(true);actor.apply(0,true)
	check(mesh.mesh==pair.flex,"manual guide FK selects flexible view while Hair is off")
	actor.data.pose={};actor.apply(0,true)
	check(mesh.mesh==pair.rest,"clearing guide FK restores original-weight view")
	var native: String=actor.root.get_meta("has_source_bones",{}).get(1,"");actor.data.pose={native:{"position":[0,0,0],"rotation_xyzw":[q.x,q.y,q.z,q.w]}};actor.apply(0,true)
	check(mesh.mesh==pair.rest,"original native ancestor FK retains original-weight view")
	actor.data.pose={};actor.apply(0,true)
	var material:=StandardMaterial3D.new();material.albedo_color=Color.BLUE;mesh.material_override=material;mesh.set_surface_override_material(0,material);mesh.set_blend_shape_value(0,.42);var shape_value:=mesh.get_blend_shape_value(0);var box: AABB=mesh.custom_aabb
	var owner:=RefCounted.new();var lease: Dictionary=actor.acquire_reconstruction_flex(owner)
	check(not lease.has("error") and int(lease.get("token",0))>0 and mesh.mesh==pair.flex,"force-flex lease switches before any contact-cache construction")
	check(mesh.material_override==material and mesh.get_surface_override_material(0)==material and mesh.get_blend_shape_value(0)==shape_value and mesh.custom_aabb==box,"switch preserves per-instance materials expressions and SourceShape bounds")
	actor.apply(0,false,true);check(mesh.mesh==pair.flex,"live cache owner retains flexible resource during a final authored-rest evaluation")
	actor.release_reconstruction_flex(int(lease.token));check(mesh.mesh==pair.rest,"last live owner release restores exact authored-rest resource")
	var transform: Dictionary={"position":[0,0,0],"rotation_xyzw":[0,0,0,1],"scale":1.}
	actor.data.pose_keys=[{"frame":0,"pose":{},"transform":transform,"interpolation":"hold"},{"frame":4,"pose":posed,"transform":transform,"interpolation":"hold"}];actor.apply(4,false,true)
	check(mesh.mesh==pair.flex,"recorded guide key uses flexible geometry in final evaluation with Hair off")
	actor.apply(0,false,true);check(mesh.mesh==pair.rest,"recorded rest key uses original geometry without a live owner")
	actor.data.pose_keys=[];actor.preview_frame=2;actor.preview_pose=posed.duplicate(true);actor.apply(2,true)
	check(mesh.mesh==pair.flex,"manual pose preview uses flexible geometry")
	actor.preview_frame=-1;actor.preview_pose={};actor.live_pose=posed.duplicate(true);actor.apply(0,true)
	check(mesh.mesh==pair.flex,"live guide pose uses flexible geometry")
	actor.live_pose=null;actor.apply(0,true)
	var skeleton: Skeleton3D=row.guides[0].skeleton.get_ref();var global_poses: Array=[]
	for i in range(skeleton.get_bone_count()):global_poses.append(skeleton.get_bone_global_pose(i))
	skeleton.set_meta(Bounds.FINAL_META,{"owner":weakref(owner),"poses":global_poses});actor.refresh_render_bounds();check(mesh.mesh==pair.flex,"authoritative final-pose owner conservatively selects flexible geometry")
	skeleton.remove_meta(Bounds.FINAL_META);actor.refresh_render_bounds();check(mesh.mesh==pair.rest,"clearing final-pose owner restores ordinary rest selection")
	var runner_result: Dictionary=Spring.construct(actor)
	check(not runner_result.has("error") and mesh.mesh==pair.flex,"ordinary Spring construction holds flexible mesh while caches exist")
	if not runner_result.has("error"):runner_result.runner.dispose()
	check(mesh.mesh==pair.rest,"ordinary Spring disposal releases the mesh lease after caches")
	var clone: Node3D=actor.root.duplicate();root.add_child(clone);var cloned_mesh: MeshInstance3D=clone.find_children("*","MeshInstance3D",true,false)[0];var info: Dictionary=actor.bones[guide];var cloned_sk: Skeleton3D=clone.get_node(NodePath(info.path));cloned_sk.set_bone_pose_rotation(info.index,info.base.basis.get_rotation_quaternion()*q)
	check(Views.select_clone(actor,clone).is_empty() and cloned_mesh.mesh==pair.flex and mesh.mesh==pair.rest,"thumbnail-style clone selects its requested flexible pose without borrowing original state")
	clone.free();check(actor._rest_views!=null and mesh.mesh==pair.rest,"freeing clone preserves original controller and rest view")
	var parked:=Node3D.new();root.add_child(parked);var old_controller: int=actor.reconstruction_view_diagnostics().controller
	root.remove_child(actor.root);parked.add_child(actor.root);actor.apply(0,true)
	check(actor.reconstruction_view_diagnostics().active and actor.reconstruction_view_diagnostics().controller!=old_controller and mesh.mesh==pair.rest,"hidden-candidate reparenting rebinds its owned rest controller")
	var renewed: Dictionary=actor.acquire_reconstruction_flex(owner);actor.release_reconstruction_flex(int(lease.token),old_controller)
	check(mesh.mesh==pair.flex,"stale lease cannot release a newly bound controller's contact resource")
	actor.release_reconstruction_flex(int(renewed.token),int(renewed.controller))
	var ancestor_made:=make(args[3]);var ancestor_ok: bool=not ancestor_made.has("error")
	if ancestor_ok:
		var ancestor_actor: RefCounted=ancestor_made.actor;var ancestor_mesh: MeshInstance3D=mesh_of(ancestor_actor);var ancestor_pair: Dictionary=ancestor_mesh.get_meta(Views.PAIR)
		var ancestor_id: String=ancestor_actor.root.get_meta("has_source_bones",{}).get(int(ancestor_pair.guide_nodes[0]),"");var ancestor_info: Dictionary=ancestor_actor.bones[ancestor_id];var direct:=false
		for s in range(ancestor_pair.flex.get_surface_count()):
			var arrays: Array=ancestor_pair.flex.surface_get_arrays(s);var bones: PackedInt32Array=arrays[Mesh.ARRAY_BONES];var weights: PackedFloat32Array=arrays[Mesh.ARRAY_WEIGHTS]
			for j in range(bones.size()):
				var bind: int=bones[j]
				if weights[j]>0. and ancestor_mesh.skin.get_bind_name(bind)==ancestor_info.name:direct=true
		var before_point:=point_at(ancestor_mesh,1,2);ancestor_actor.data.pose={ancestor_id:{"position":[0,0,0],"rotation_xyzw":[q.x,q.y,q.z,q.w]}};ancestor_actor.apply(0,true)
		var descendant_locals_rest:=true
		for tracked in ancestor_actor._rest_views._rows[0].guides:
			if tracked.id==ancestor_id:continue
			var sk: Skeleton3D=tracked.skeleton.get_ref()
			descendant_locals_rest=descendant_locals_rest and sk.get_bone_pose_rotation(tracked.index)==tracked.rotation and sk.get_bone_pose_position(tracked.index)==tracked.position
		ancestor_ok=not direct and descendant_locals_rest and ancestor_mesh.mesh==ancestor_pair.flex and point_at(ancestor_mesh,1,2).distance_to(before_point)>.01
		ancestor_actor.root.free()
	check(ancestor_ok,"unweighted generated parent preserves authored weighted-descendant deformation while descendant locals stay at rest")
	var array_reads: int=actor.reconstruction_view_diagnostics().stats.inventory_array_reads
	for i in range(30):actor.apply(0,true)
	check(actor.reconstruction_view_diagnostics().stats.inventory_array_reads==array_reads and actor.render_bounds_error.is_empty(),"steady rest evaluation avoids geometry rescans and bounds ownership failure")
	check(actor.data==base_data,"mesh selection and physics ownership do not author model data")
	check(FileAccess.get_sha256(args[1])==source_sha and FileAccess.get_sha256(args[2])==candidate_sha,"original source and derived candidate stay read-only")
	var result:={"checks":checks,"failures":failures,"user_profile":OS.get_user_data_dir(),"rest_view":actor.reconstruction_view_diagnostics(),"graphics_used":false,"source_arrays_published":false}
	print("RECONSTRUCTED_REST_VIEW "+JSON.stringify(result));FileAccess.open(args[0].path_join("result.json"),FileAccess.WRITE).store_string(JSON.stringify(result,"",true,true));source.actor.root.free();actor.root.free();parked.free();quit(0 if failures==0 else 1)
