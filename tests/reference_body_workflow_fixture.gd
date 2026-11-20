extends RefCounted
# Original public geometry: a small weighted figure and one separate loose strand.
# The source stays small so all requested artist sizes exercise nonunit world bones.
const Writer=preload("res://tests/secondary_fixture.gd")

static func create(path: String) -> Error:
	var root:=Node3D.new();root.name="ReferenceBodyWorkflow"
	var sk:=Skeleton3D.new();sk.name="Rig";root.add_child(sk);sk.owner=root
	var names: Array=["hips","head","thigh.L","shin.L","foot.L","thigh.R","shin.R","foot.R","Hair.A","Hair.B","Hair.End"]
	var points: Array=[Vector3(0,.41,0),Vector3(0,.68,0),Vector3(-.085,.41,0),Vector3(-.085,.255,0),Vector3(-.085,.1,0),Vector3(.085,.41,0),Vector3(.085,.255,0),Vector3(.085,.1,0),Vector3(0,.73,.13),Vector3(0,.63,.13),Vector3(0,.53,.13)]
	var parents: Array=[-1,0,0,2,3,0,5,6,1,8,9]
	for i in range(names.size()):
		sk.add_bone(names[i]);sk.set_bone_parent(i,parents[i]);sk.set_bone_rest(i,Transform3D(Basis.IDENTITY,points[i]-(points[parents[i]] if parents[i]>=0 else Vector3.ZERO)))
	sk.reset_bone_poses()
	for bone in range(names.size()-1):
		var box:=BoxMesh.new()
		box.size=Vector3(.19,.2,.15) if bone==1 else Vector3(.12,.12,.18) if bone in [4,7] else Vector3(.09,.155,.09) if bone in [2,3,5,6] else Vector3(.27,.27,.15) if bone==0 else Vector3(.05,.1,.025)
		var center: Vector3=points[bone]
		if bone in [2,3,5,6]:center.y-=.0775
		elif bone==0:center.y+=.135
		elif bone in [8,9]:center.y-=.05
		var arrays:=box.surface_get_arrays(0);var vertices: PackedVector3Array=arrays[Mesh.ARRAY_VERTEX]
		for v in range(vertices.size()):vertices[v]+=center
		arrays[Mesh.ARRAY_VERTEX]=vertices
		var bones:=PackedInt32Array();var weights:=PackedFloat32Array();bones.resize(vertices.size()*4);weights.resize(vertices.size()*4)
		for v in range(vertices.size()):bones[v*4]=bone;weights[v*4]=1.
		arrays[Mesh.ARRAY_BONES]=bones;arrays[Mesh.ARRAY_WEIGHTS]=weights
		var mesh:=ArrayMesh.new();mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)
		var instance:=MeshInstance3D.new();instance.mesh=mesh;root.add_child(instance);instance.owner=root;instance.skeleton=instance.get_path_to(sk);instance.skin=sk.create_skin_from_rest_transforms()
		var material:=StandardMaterial3D.new();material.albedo_color=Color("66bde3") if bone<8 else Color("efb45d");instance.material_override=material
	var doc:=GLTFDocument.new();var state:=GLTFState.new();var error:=doc.append_from_scene(root,state)
	if error==OK:
		var raw:=doc.generate_buffer(state);var json_size:=raw.decode_u32(12)
		var data: Dictionary=JSON.parse_string(raw.slice(20,20+json_size).get_string_from_utf8());var indices:={}
		for i in range(data.nodes.size()):indices[data.nodes[i].get("name","")]=i
		var joints:=[]
		for name in ["Hair_A","Hair_B","Hair_End"]:
			if not indices.has(name):root.free();return ERR_INVALID_DATA
			joints.append({"node":indices[name],"stiffness":1.2,"dragForce":.4,"hitRadius":.005,"gravityPower":.15,"gravityDir":[1.,0.,0.]})
		if not data.has("extensions"):data.extensions={}
		data.extensions["VRMC_springBone"]={"specVersion":"1.0","springs":[{"name":"Separate loose hair","joints":joints}],"colliders":[],"colliderGroups":[]}
		if not data.has("extensionsUsed"):data.extensionsUsed=[]
		if not "VRMC_springBone" in data.extensionsUsed:data.extensionsUsed.append("VRMC_springBone")
		error=Writer.write_glb(path,data,raw.slice(28+json_size))
	root.free();return error
