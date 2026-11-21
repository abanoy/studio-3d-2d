extends SceneTree
const RenderControl=preload("res://src/posed_render_bounds.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func _initialize() -> void:call_deferred("run")
func fixture() -> Dictionary:
	var owner:=Node3D.new();root.add_child(owner)
	var sk:=Skeleton3D.new();sk.name="Rig";owner.add_child(sk)
	sk.add_bone("head");sk.set_bone_rest(0,Transform3D.IDENTITY)
	var arrays:=[];arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX]=PackedVector3Array([Vector3(10,1,0),Vector3(11,1,0),Vector3(10,2,0)])
	arrays[Mesh.ARRAY_BONES]=PackedInt32Array([0,0,0,0,0,0,0,0,0,0,0,0])
	arrays[Mesh.ARRAY_WEIGHTS]=PackedFloat32Array([1,0,0,0,1,0,0,0,1,0,0,0])
	var resource:=ArrayMesh.new();resource.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)
	var mesh:=MeshInstance3D.new();mesh.mesh=resource;owner.add_child(mesh)
	mesh.skin=sk.create_skin_from_rest_transforms();mesh.skeleton=mesh.get_path_to(sk);mesh.extra_cull_margin=.25
	sk.set_bone_pose_position(0,Vector3(5,0,0));sk.force_update_all_bone_transforms()
	return {"owner":owner,"sk":sk,"mesh":mesh,"resource":resource}
func run() -> void:
	var f:=fixture();var original_custom: AABB=f.mesh.custom_aabb
	var built:=RenderControl.create([f.mesh]);check(built.has("control"),"explicit synthetic weighted mesh prepares without native assets")
	if not built.has("control"):print("POSED_RENDER_BOUNDS "+JSON.stringify({"checks":checks,"failures":failures}));quit(1);return
	var control: RefCounted=built.control
	check(f.mesh.extra_cull_margin==.25 and f.mesh.custom_aabb==original_custom,"preparation writes no engine properties")
	var first: Dictionary=control.refresh()
	check(not first.has("error") and first.updated==1 and f.mesh.extra_cull_margin>4.9,"posed palette derives a finite local margin")
	check(f.mesh.custom_aabb==original_custom and not f.mesh.has_meta("has_shape_bounds"),"control never writes SourceShape custom bounds or metadata")
	var writes: int=control.stats.margin_writes;var arrays: int=control.stats.inventory_array_reads
	for i in range(50):control.refresh()
	check(control.stats.margin_writes==writes and control.stats.cache_hits==50,"fifty unchanged evaluations do not write or enlarge margins")
	check(control.stats.inventory_array_reads==arrays and control.stats.hot_array_reads==0,"warm refreshes perform no surface array or vertex scans")
	f.owner.transform=Transform3D(Basis(Vector3.UP,.5).scaled(Vector3.ONE*2),Vector3(7,9,-4))
	var after_parent: Dictionary=control.refresh()
	check(not after_parent.has("error") and after_parent.updated==0,"parent transform changes do not inflate mesh-local padding")
	f.sk.set_bone_pose_position(0,Vector3.ZERO);f.sk.force_update_all_bone_transforms();var smaller: Dictionary=control.refresh()
	check(not smaller.has("error") and smaller.updated==1 and f.mesh.extra_cull_margin==.25,"returning to rest shrinks to original margin")
	var morph:=AABB(Vector3(10,1,0),Vector3(2,3,1));f.mesh.set_meta("has_shape_bounds",morph);f.mesh.custom_aabb=morph
	f.sk.set_bone_pose_position(0,Vector3(2,0,0));f.sk.force_update_all_bone_transforms();var shaped: Dictionary=control.refresh()
	check(not shaped.has("error") and f.mesh.custom_aabb==morph and f.mesh.get_meta("has_shape_bounds")==morph,"morph-bound ownership survives a current-pose refresh")
	f.mesh.remove_meta("has_shape_bounds");f.mesh.custom_aabb=original_custom;control.refresh()
	check(f.mesh.custom_aabb==original_custom and not f.mesh.has_meta("has_shape_bounds"),"removing a morph returns to immutable intrinsic input without recursive custom bounds")
	f.owner.remove_child(f.mesh);var detached: Dictionary=control.refresh()
	check(detached.has("error"),"detached mesh refuses before skeleton or viewport work")
	f.owner.add_child(f.mesh);var attached: Dictionary=control.refresh();check(not attached.has("error"),"same mesh reattaches without replacing the control")
	f.mesh.extra_cull_margin=99.;check(control.refresh().has("error"),"external margin edits are detected")
	control.dispose();check(f.mesh.extra_cull_margin==99.,"disposal preserves an external margin edit")
	check(control.refresh().has("error"),"disposed control cannot refresh")
	f.owner.free()
	var a:=fixture();var b:=fixture();var pair:=RenderControl.create([a.mesh,b.mesh]);var peer: RefCounted=pair.control;peer.refresh()
	var preserved: float=a.mesh.extra_cull_margin;a.sk.set_bone_pose_position(0,Vector3(20,0,0));a.sk.force_update_all_bone_transforms();b.owner.remove_child(b.mesh)
	check(peer.refresh().has("error") and a.mesh.extra_cull_margin==preserved,"peer refusal leaves every prepared margin uncommitted")
	b.owner.add_child(b.mesh);peer.refresh();peer.dispose()
	check(a.mesh.extra_cull_margin==.25 and b.mesh.extra_cull_margin==.25,"ordinary disposal restores only the two helper-owned margins")
	a.owner.free();b.owner.free()
	var changed:=fixture();var changing:=RenderControl.create([changed.mesh]);var guard: RefCounted=changing.control;guard.refresh();changed.resource.emit_changed()
	check(guard.refresh().has("error"),"immutable resource changes invalidate cached weight admission")
	guard.dispose();changed.owner.free()
	var freed:=fixture();var freed_control:=RenderControl.create([freed.mesh]);var lifecycle: RefCounted=freed_control.control;lifecycle.refresh();freed.owner.free()
	check(lifecycle.refresh().has("error"),"freed node identities refuse without dereferencing skeletons")
	lifecycle.dispose();check(true,"freed control disposal completes without a scene-tree query")
	check(RenderControl.create([null]).has("error") and RenderControl.create([]).has("control"),"invalid mesh refuses while an explicitly empty selection is inert")
	print("POSED_RENDER_BOUNDS "+JSON.stringify({"checks":checks,"failures":failures,"graphics_or_native_assets_used":false}))
	quit(0 if failures==0 else 1)
