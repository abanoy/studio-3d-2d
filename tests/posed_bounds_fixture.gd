extends RefCounted
# Synthetic green skinned panel; no owner/native file is read.
static func scene(shared: ArrayMesh=null,shape:=false) -> Node3D:
	var node:=Node3D.new();node.name="BoundsFixture"
	var skeleton:=Skeleton3D.new();skeleton.name="Rig";skeleton.set_animate_physical_bones(false)
	node.add_child(skeleton);skeleton.owner=node;skeleton.add_bone("head");skeleton.set_bone_rest(0,Transform3D.IDENTITY);skeleton.reset_bone_poses()
	var resource: ArrayMesh=shared
	if resource==null:
		var box:=BoxMesh.new();box.size=Vector3(.5,.5,.05)
		var arrays: Array=box.surface_get_arrays(0);var vertices: PackedVector3Array=arrays[Mesh.ARRAY_VERTEX]
		var joints:=PackedInt32Array();var weights:=PackedFloat32Array();joints.resize(vertices.size()*4);weights.resize(vertices.size()*4)
		for i in range(vertices.size()):weights[i*4]=1.
		arrays[Mesh.ARRAY_BONES]=joints;arrays[Mesh.ARRAY_WEIGHTS]=weights
		resource=ArrayMesh.new();var targets: Array[Array]=[]
		if shape:
			resource.add_blend_shape("wider");resource.blend_shape_mode=Mesh.BLEND_SHAPE_MODE_RELATIVE
			var target: Array=[];target.resize(Mesh.ARRAY_MAX)
			var offsets:=PackedVector3Array();var normals:=PackedVector3Array();var tangents:=PackedFloat32Array()
			for point in vertices:offsets.append(Vector3(point.x,0,0));normals.append(Vector3.ZERO)
			tangents.resize(vertices.size()*4);target[Mesh.ARRAY_VERTEX]=offsets;target[Mesh.ARRAY_NORMAL]=normals;target[Mesh.ARRAY_TANGENT]=tangents;targets.append(target)
		resource.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays,targets)
	var mesh:=MeshInstance3D.new();mesh.name="Panel";mesh.mesh=resource;node.add_child(mesh);mesh.owner=node
	mesh.skin=skeleton.create_skin_from_rest_transforms();mesh.skeleton=mesh.get_path_to(skeleton)
	var material:=StandardMaterial3D.new();material.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED;material.albedo_color=Color.GREEN;mesh.material_override=material
	return node

static func write(path: String) -> Error:
	var node:=scene(null,true);var document:=GLTFDocument.new();var state:=GLTFState.new();var code: Error=document.append_from_scene(node,state)
	if code==OK:code=document.write_to_filesystem(state,path)
	node.free();return code
