extends RefCounted
# Original deliberately overlapping skin-fit torso, not vendor geometry.
static func create(path: String,loose:=false) -> Error:
	var root:=Node3D.new();root.name="OriginalTorsoContactFixture"
	var sk:=Skeleton3D.new();sk.name="Rig";root.add_child(sk);sk.owner=root
	var names: Array=["hips","spine","spine_mid","spine_top","upper_arm.L","forearm.L","hand.L"]
	var offsets: Array=[Vector3(0,1,0),Vector3(0,0.18,0),Vector3(0,0.18,0),Vector3(0,0.18,0),Vector3(0.35,0.18,0),Vector3(0.6,0,0),Vector3(0.6,0,0)]
	var parents: Array=[-1,0,1,2,3,4,5]
	if loose:
		names.append_array(["head","spring_tip","index.L","hlp_sleeve"])
		offsets.append_array([Vector3(0,0.4,0),Vector3(0,-0.2,0),Vector3(0.6,0,0),Vector3(0.2,0,0)]);parents.append_array([3,7,6,4])
	for i in range(names.size()):
		sk.add_bone(names[i]);sk.set_bone_rest(i,Transform3D(Basis.IDENTITY,offsets[i]))
		if i>0:sk.set_bone_parent(i,parents[i])
	sk.reset_bone_poses()
	for i in range(names.size()):
		var center:=sk.get_bone_global_rest(i).origin+ (Vector3(0,0.1,0) if i<4 else Vector3(0.28,0,0))
		var shape:=BoxMesh.new();shape.size=Vector3(0.55,0.62,0.32) if i<4 else Vector3(0.55,0.18,0.18)
		if i==7:center=sk.get_bone_global_rest(i).origin+Vector3(0,0.12,0);shape.size=Vector3.ONE*0.3
		if i==8:center=sk.get_bone_global_rest(i).origin+Vector3(0,-0.8,0);shape.size=Vector3(0.25,1.5,0.1)
		if i==9:center=sk.get_bone_global_rest(i).origin+Vector3(0.12,0,0);shape.size=Vector3(0.25,0.08,0.08)
		if i==10:center=sk.get_bone_global_rest(i).origin+Vector3(0.1,0,0);shape.size=Vector3(0.5,0.6,0.6)
		var arrays:=shape.surface_get_arrays(0);var vertices: PackedVector3Array=arrays[Mesh.ARRAY_VERTEX]
		for j in range(vertices.size()):vertices[j]+=center
		arrays[Mesh.ARRAY_VERTEX]=vertices
		var indices:=PackedInt32Array();var weights:=PackedFloat32Array();indices.resize(vertices.size()*4);weights.resize(vertices.size()*4)
		for j in range(vertices.size()):indices[j*4]=i;weights[j*4]=1.0
		arrays[Mesh.ARRAY_BONES]=indices;arrays[Mesh.ARRAY_WEIGHTS]=weights
		var mesh:=ArrayMesh.new();mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)
		var instance:=MeshInstance3D.new();instance.mesh=mesh;root.add_child(instance);instance.owner=root;instance.skeleton=instance.get_path_to(sk);instance.skin=sk.create_skin_from_rest_transforms()
		var material:=StandardMaterial3D.new();material.albedo_color=Color.from_hsv(float(i)/names.size(),0.4,0.8);instance.material_override=material
	var document:=GLTFDocument.new();var state:=GLTFState.new();var error:=document.append_from_scene(root,state)
	if error==OK:error=document.write_to_filesystem(state,path)
	root.free();return error
