extends RefCounted
# Original skinned hanging strips: hair and skirt; no owner/vendor artwork.
static func create(path: String) -> Error:
	var root:=Node3D.new();root.name="OriginalSecondaryFixture"
	var sk:=Skeleton3D.new();sk.name="Rig";root.add_child(sk);sk.owner=root
	var names: Array=["Body","Hair.A","Hair.B","Hair.C","Hair.End","Skirt.A","Skirt.B","Skirt.End"]
	var parents: Array=[-1,0,1,2,3,0,5,6]
	var positions: Array=[Vector3.ZERO,Vector3(0,2,0),Vector3(0,-0.3,0),Vector3(0,-0.3,0),Vector3(0,-0.3,0),Vector3(0.35,1.2,0),Vector3(0,-0.35,0),Vector3(0,-0.35,0)]
	for i in range(names.size()):
		sk.add_bone(names[i]);sk.set_bone_rest(i,Transform3D(Basis.IDENTITY,positions[i]))
		if i>0:sk.set_bone_parent(i,parents[i])
	sk.reset_bone_poses()
	for bone in [0,1,2,3,5,6]:
		var box:=BoxMesh.new();box.size=Vector3(0.35,0.9,0.22) if bone==0 else Vector3(0.18,0.3,0.05)
		var arrays:=box.surface_get_arrays(0);var vertices: PackedVector3Array=arrays[Mesh.ARRAY_VERTEX]
		var center:=Vector3(0,1.45,-0.3) if bone==0 else sk.get_bone_global_rest(bone).origin+Vector3(0,-0.15,0)
		for i in range(vertices.size()):vertices[i]+=center
		arrays[Mesh.ARRAY_VERTEX]=vertices
		var bones:=PackedInt32Array();var weights:=PackedFloat32Array();bones.resize(vertices.size()*4);weights.resize(vertices.size()*4)
		for i in range(vertices.size()):bones[4*i]=bone;weights[4*i]=1
		arrays[Mesh.ARRAY_BONES]=bones;arrays[Mesh.ARRAY_WEIGHTS]=weights
		var mesh:=ArrayMesh.new();mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)
		var instance:=MeshInstance3D.new();instance.mesh=mesh;root.add_child(instance);instance.owner=root;instance.skeleton=instance.get_path_to(sk);instance.skin=sk.create_skin_from_rest_transforms()
		var material:=StandardMaterial3D.new();material.albedo_color=Color("79c6bd") if bone==0 else Color("eab26f") if bone<5 else Color("d990b1");instance.material_override=material
	var doc:=GLTFDocument.new();var state:=GLTFState.new();var result:=doc.append_from_scene(root,state)
	if result==OK:
		var data: Dictionary=state.json;var nodes:=state.get_nodes();var indices:={}
		for i in range(nodes.size()):indices[nodes[i].resource_name]=i
		# Export JSON is serialized by generate_buffer, so resolve actual source
		# node indices from that buffer rather than assuming bone_index==node_index.
		var raw:=doc.generate_buffer(state);var json_size:=raw.decode_u32(12);data=JSON.parse_string(raw.slice(20,20+json_size).get_string_from_utf8());indices={}
		for i in range(data.nodes.size()):indices[data.nodes[i].get("name","")]=i
		var chains: Array=[]
		for spec in [["Hair.A","Hair.B","Hair.C","Hair.End"],["Skirt.A","Skirt.B","Skirt.End"]]:
			var joints: Array=[]
			for name in spec:joints.append({"node":indices[name.replace(".","_")],"stiffness":1.0,"dragForce":0.4,"hitRadius":0.01})
			chains.append({"name":spec[0],"joints":joints,"center":indices.Body,"colliderGroups":[0]})
		data["extensions"]={"VRMC_springBone":{"specVersion":"1.0","springs":chains,"colliders":[{"node":indices.Body,"shape":{"sphere":{"offset":[-0.15,1.74,0],"radius":0.08}}},{"node":indices.Body,"shape":{"capsule":{"offset":[0.3,0.7,-0.25],"tail":[0.3,1.2,-0.25],"radius":0.06}}}],"colliderGroups":[{"colliders":[0,1]}]}}
		data["extensionsUsed"]=["VRMC_springBone"]
		result=write_glb(path,data,raw.slice(28+json_size))
	root.free();return result

static func write_glb(path: String,data: Dictionary,binary: PackedByteArray) -> Error:
	var json:=JSON.stringify(data).to_utf8_buffer()
	while json.size()%4:json.append(32)
	var file:=FileAccess.open(path,FileAccess.WRITE)
	if file==null:return FileAccess.get_open_error()
	for n in [0x46546c67,2,28+json.size()+binary.size(),json.size(),0x4e4f534a]:file.store_32(n)
	file.store_buffer(json);file.store_32(binary.size());file.store_32(0x004e4942);file.store_buffer(binary);file.close();return OK
