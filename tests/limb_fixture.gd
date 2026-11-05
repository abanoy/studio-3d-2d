extends RefCounted

static func create(path: String, leg:=false, anchor:=false) -> Error:
	var root:=Node3D.new();root.name="AuthoredLimb"
	var skeleton:=Skeleton3D.new();skeleton.name="Rig";root.add_child(skeleton);skeleton.owner=root
	var names: Array=["thigh.L","shin.L","foot.L"] if leg else ["upper_arm.L","forearm.L","hand.L"]
	var rest: Array=[Vector3(0,2,0),Vector3(0,-0.8,0.15),Vector3(0,-0.8,-0.15)] if leg else [Vector3(0,1,0),Vector3(0.8,0.15,0),Vector3(0.8,-0.15,0)]
	var first:=1 if anchor else 0
	if anchor:skeleton.add_bone("hips")
	for i in range(3):
		skeleton.add_bone(names[i]);skeleton.set_bone_rest(i+first,Transform3D(Basis.IDENTITY,rest[i]))
		if i+first>0:skeleton.set_bone_parent(i+first,i+first-1)
	skeleton.reset_bone_poses()
	for i in range(3):
		var start:=skeleton.get_bone_global_rest(i+first).origin
		var end:=skeleton.get_bone_global_rest(i+first+1).origin if i<2 else start+Vector3(0.2,0,0)
		var shape:=BoxMesh.new();shape.size=Vector3(0.2,0.75,0.2) if leg and i<2 else Vector3(0.75,0.2,0.2) if i<2 else Vector3(0.25,0.25,0.25)
		var arrays:=shape.surface_get_arrays(0);var vertices: PackedVector3Array=arrays[Mesh.ARRAY_VERTEX]
		for j in range(vertices.size()):vertices[j]+=(start+end)*0.5
		arrays[Mesh.ARRAY_VERTEX]=vertices
		var indices:=PackedInt32Array();var weights:=PackedFloat32Array();indices.resize(vertices.size()*4);weights.resize(vertices.size()*4)
		for j in range(vertices.size()):indices[j*4]=i+first;weights[j*4]=1
		arrays[Mesh.ARRAY_BONES]=indices;arrays[Mesh.ARRAY_WEIGHTS]=weights
		var mesh:=ArrayMesh.new();mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)
		var instance:=MeshInstance3D.new();instance.mesh=mesh;root.add_child(instance);instance.owner=root
		instance.skeleton=instance.get_path_to(skeleton);instance.skin=skeleton.create_skin_from_rest_transforms()
		var material:=StandardMaterial3D.new();material.albedo_color=[Color("79c6bd"),Color("eab26f"),Color("ed9275")][i];instance.material_override=material
	var document:=GLTFDocument.new();var state:=GLTFState.new();var error:=document.append_from_scene(root,state)
	if error==OK:error=document.write_to_filesystem(state,path)
	root.free();return error
