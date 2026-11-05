extends RefCounted
# Two independent skin branches make accidental cross-part motion measurable.
static func create(path: String) -> Error:
	var root:=Node3D.new();root.name="BodyCurveFixture"
	var skeleton:=Skeleton3D.new();skeleton.name="Rig";root.add_child(skeleton);skeleton.owner=root
	for i in range(2):
		skeleton.add_bone("left" if i==0 else "right")
		skeleton.set_bone_rest(i,Transform3D(Basis.IDENTITY,Vector3(-.6 if i==0 else .6,0,0)))
	skeleton.reset_bone_poses()
	for i in range(2):
		var box:=BoxMesh.new();box.size=Vector3(.35,1.,.3)
		var arrays:=box.surface_get_arrays(0);var vertices: PackedVector3Array=arrays[Mesh.ARRAY_VERTEX]
		for j in range(vertices.size()):vertices[j]+=skeleton.get_bone_global_rest(i).origin+Vector3(0,.4,0)
		arrays[Mesh.ARRAY_VERTEX]=vertices
		var bones:=PackedInt32Array();var weights:=PackedFloat32Array();bones.resize(vertices.size()*4);weights.resize(vertices.size()*4)
		for j in range(vertices.size()):bones[j*4]=i;weights[j*4]=1.
		arrays[Mesh.ARRAY_BONES]=bones;arrays[Mesh.ARRAY_WEIGHTS]=weights
		var mesh:=ArrayMesh.new();mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)
		var instance:=MeshInstance3D.new();instance.name="LeftMesh" if i==0 else "RightMesh";instance.mesh=mesh;root.add_child(instance);instance.owner=root
		instance.skeleton=instance.get_path_to(skeleton);instance.skin=skeleton.create_skin_from_rest_transforms()
		var material:=StandardMaterial3D.new();material.albedo_color=Color("81bddd") if i==0 else Color("eeab77");instance.material_override=material
	var document:=GLTFDocument.new();var state:=GLTFState.new();var error:=document.append_from_scene(root,state)
	if error==OK:error=document.write_to_filesystem(state,path)
	root.free();return error
