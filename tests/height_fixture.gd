extends RefCounted
# Original weighted boxes distinguish proportion/mesh coverage from bone inventory.
static func create(path: String,leg: float,torso: float,head_only:=false) -> Error:
	var root:=Node3D.new();root.name="HeightFixture";var sk:=Skeleton3D.new();sk.name="Rig";root.add_child(sk);sk.owner=root
	var names: Array=["hips","head","thigh.L","shin.L","foot.L","thigh.R","shin.R","foot.R"]
	var points: Array=[Vector3(0,leg+.1,0),Vector3(0,leg+.1+torso,0),Vector3(-.12,leg+.1,0),Vector3(-.12,leg*.5+.1,0),Vector3(-.12,.1,0),Vector3(.12,leg+.1,0),Vector3(.12,leg*.5+.1,0),Vector3(.12,.1,0)]
	var parents: Array=[-1,0,0,2,3,0,5,6]
	for i in range(names.size()):
		sk.add_bone(names[i]);sk.set_bone_parent(i,parents[i]);sk.set_bone_rest(i,Transform3D(Basis.IDENTITY,points[i]-(points[parents[i]] if parents[i]>=0 else Vector3.ZERO)))
	sk.reset_bone_poses()
	for i in range(names.size()):
		if head_only and i!=1:continue
		var shape:=BoxMesh.new();shape.size=Vector3(.25,.2,.2) if i==1 or i==4 or i==7 else Vector3(.2,leg*.5,.2) if i in [2,3,5,6] else Vector3(.4,torso,.2)
		var center: Vector3=points[i]
		if i in [2,3,5,6]:center.y-=leg*.25
		elif i==0:center.y+=torso*.5
		var arrays:=shape.surface_get_arrays(0);var vertices: PackedVector3Array=arrays[Mesh.ARRAY_VERTEX]
		for v in range(vertices.size()):vertices[v]+=center
		arrays[Mesh.ARRAY_VERTEX]=vertices;var bones:=PackedInt32Array();var weights:=PackedFloat32Array();bones.resize(vertices.size()*4);weights.resize(vertices.size()*4)
		for v in range(vertices.size()):bones[v*4]=i;weights[v*4]=1.
		arrays[Mesh.ARRAY_BONES]=bones;arrays[Mesh.ARRAY_WEIGHTS]=weights
		var mesh:=ArrayMesh.new();mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays);var instance:=MeshInstance3D.new();instance.mesh=mesh;root.add_child(instance);instance.owner=root;instance.skeleton=instance.get_path_to(sk);instance.skin=sk.create_skin_from_rest_transforms()
		var material:=StandardMaterial3D.new();material.albedo_color=Color.CORNFLOWER_BLUE;instance.material_override=material
	var gltf:=GLTFDocument.new();var state:=GLTFState.new();var error:=gltf.append_from_scene(root,state)
	if error==OK:error=gltf.write_to_filesystem(state,path)
	root.free();return error
