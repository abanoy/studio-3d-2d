extends SceneTree
const Selection=preload("res://src/world_selection.gd")
var checks:=0
var failures:=0
func _initialize() -> void:call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func make_mesh(eight: bool) -> ArrayMesh:
	var mesh:=ArrayMesh.new();mesh.add_blend_shape("Authored expression");mesh.blend_shape_mode=Mesh.BLEND_SHAPE_MODE_RELATIVE
	var arrays: Array=[];arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX]=PackedVector3Array([Vector3.ZERO,Vector3.RIGHT,Vector3.UP])
	arrays[Mesh.ARRAY_INDEX]=PackedInt32Array([0,1,2])
	var bones:=PackedInt32Array();var weights:=PackedFloat32Array();var slots:=8 if eight else 4
	for vertex in range(3):
		for slot in range(slots):bones.append(slot);weights.append(1. if slot==0 else 0.)
	arrays[Mesh.ARRAY_BONES]=bones;arrays[Mesh.ARRAY_WEIGHTS]=weights
	var shape: Array=[];shape.resize(Mesh.ARRAY_MAX)
	shape[Mesh.ARRAY_VERTEX]=PackedVector3Array([Vector3(.1,0,0),Vector3(.1,0,0),Vector3(.1,0,0)])
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays,[shape],{},Mesh.ARRAY_FLAG_USE_8_BONE_WEIGHTS if eight else 0)
	return mesh
func run() -> void:
	var rest:=make_mesh(false);var flex:=make_mesh(true)
	var source:=MeshInstance3D.new();var proxy:=MeshInstance3D.new();var skin:=Skin.new()
	for i in range(8):skin.add_bind(i,Transform3D.IDENTITY)
	source.mesh=rest;source.skin=skin;proxy.mesh=rest;proxy.skin=skin
	proxy.layers=1<<19;proxy.gi_mode=GeometryInstance3D.GI_MODE_DISABLED;proxy.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var id_material:=ShaderMaterial.new();id_material.shader=preload("res://src/selection_id.gdshader")
	var ghost_material:=ShaderMaterial.new();ghost_material.shader=preload("res://src/selection_ghost.gdshader")
	proxy.set_surface_override_material(0,id_material)
	var row:={"original":source,"copy":proxy,"materials":[id_material],"ghost_materials":[ghost_material],"ghost":false}
	check(not Selection.sync_mesh_view(row),"unchanged selection geometry is a no-op")
	source.mesh=flex;source.set_blend_shape_value(0,.625)
	check(Selection.sync_mesh_view(row) and proxy.mesh==flex,"ID and outline proxy follows the flexible weight resource")
	check(proxy.get_surface_override_material(0)==id_material,"ID shader survives the mesh resource change")
	check(proxy.get_blend_shape_value(0)==.625,"selection geometry retains current expression amount")
	check(proxy.skin==skin and proxy.layers==1<<19 and proxy.gi_mode==GeometryInstance3D.GI_MODE_DISABLED and proxy.cast_shadow==GeometryInstance3D.SHADOW_CASTING_SETTING_OFF,"mesh changes preserve skin, isolated layer and GI/shadow exclusion")
	row.ghost=true;source.mesh=rest;source.set_blend_shape_value(0,.25)
	check(Selection.sync_mesh_view(row) and proxy.mesh==rest,"selection proxy returns to original rest weights")
	check(proxy.get_surface_override_material(0)==ghost_material and proxy.get_blend_shape_value(0)==.25,"hidden-selection ghost shader and expression survive restoration")
	check(source.get_surface_override_material(0)==null and rest.surface_get_material(0)==null and flex.surface_get_material(0)==null,"proxy updates never change original model materials")
	source.free();proxy.free()
	print("SELECTION_MESH_VIEW "+JSON.stringify({"checks":checks,"failures":failures,"user_profile":OS.get_user_data_dir(),"graphics_used":false}))
	quit(0 if failures==0 else 1)
