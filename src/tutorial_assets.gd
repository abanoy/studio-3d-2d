extends RefCounted
# Original procedural sample geometry. Not a user-facing model exporter.
const SceneIO=preload("res://src/scene3d.gd")
const Storage=preload("res://src/storage.gd")
const World=preload("res://src/world_document.gd")
const Timeline=preload("res://src/timeline.gd")
const FIGURE_ID:="tutorial-figure-v1"
const ROOM_ID:="tutorial-room-v1"

static func figure(path: String) -> Error:
	var root:=Node3D.new();root.name="OriginalPracticeFigure"
	var rig:=Skeleton3D.new();rig.name="PracticeRig";root.add_child(rig);rig.owner=root
	var names:=["hips","spine","chest","neck","head","upper_arm.L","forearm.L","hand.L","upper_arm.R","forearm.R","hand.R","thigh.L","shin.L","foot.L","thigh.R","shin.R","foot.R"]
	var parents:=[-1,0,1,2,3,2,5,6,2,8,9,0,11,12,0,14,15]
	var offsets:=[Vector3(0,.96,0),Vector3(0,.25,0),Vector3(0,.22,0),Vector3(0,.17,0),Vector3(0,.16,0),Vector3(.24,.04,0),Vector3(.32,-.025,.025),Vector3(.29,.025,-.025),Vector3(-.24,.04,0),Vector3(-.32,-.025,.025),Vector3(-.29,.025,-.025),Vector3(.13,-.04,0),Vector3(0,-.42,.025),Vector3(0,-.4,-.025),Vector3(-.13,-.04,0),Vector3(0,-.42,.025),Vector3(0,-.4,-.025)]
	var ends:=[1,2,3,4,-1,6,7,-1,9,10,-1,12,13,-1,15,16,-1]
	for i in range(names.size()):
		rig.add_bone(names[i]);rig.set_bone_rest(i,Transform3D(Basis.IDENTITY,offsets[i]))
		if parents[i]>=0:rig.set_bone_parent(i,parents[i])
	rig.reset_bone_poses()
	for i in range(names.size()):
		var start:=rig.get_bone_global_rest(i).origin
		var finish: Vector3=rig.get_bone_global_rest(ends[i]).origin if ends[i]>=0 else start+Vector3(0,.02,0)
		var shape: PrimitiveMesh;var basis:=Basis.IDENTITY;var center:=(start+finish)*.5
		if i==4:
			var sphere:=SphereMesh.new();sphere.radius=.14;sphere.height=.28;sphere.radial_segments=12;sphere.rings=6;shape=sphere;center=start+Vector3(0,.06,0)
		elif ends[i]<0:
			var box:=BoxMesh.new();box.size=Vector3(.13,.1,.23) if "foot" in names[i] else Vector3(.16,.1,.12);shape=box;center=start+Vector3(0,0,.04) if "foot" in names[i] else start+Vector3(.06 if i==7 else -.06,0,0)
		else:
			var capsule:=CapsuleMesh.new();capsule.height=start.distance_to(finish)*.95;capsule.radius=minf(.12 if i<3 else .065,capsule.height*.34);capsule.radial_segments=12;capsule.rings=4;shape=capsule;basis=Basis(Quaternion(Vector3.UP,(finish-start).normalized()))
		var arrays:=shape.surface_get_arrays(0);var vertices: PackedVector3Array=arrays[Mesh.ARRAY_VERTEX];var normals: PackedVector3Array=arrays[Mesh.ARRAY_NORMAL]
		for j in range(vertices.size()):vertices[j]=basis*vertices[j]+center;normals[j]=(basis*normals[j]).normalized()
		arrays[Mesh.ARRAY_VERTEX]=vertices;arrays[Mesh.ARRAY_NORMAL]=normals
		var bones:=PackedInt32Array();var weights:=PackedFloat32Array();bones.resize(vertices.size()*4);weights.resize(vertices.size()*4)
		for j in range(vertices.size()):bones[j*4]=i;weights[j*4]=1.
		arrays[Mesh.ARRAY_BONES]=bones;arrays[Mesh.ARRAY_WEIGHTS]=weights
		var mesh:=ArrayMesh.new();mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)
		var part:=MeshInstance3D.new();part.name="Part_%02d" % i;part.mesh=mesh;root.add_child(part);part.owner=root;part.skeleton=part.get_path_to(rig);part.skin=rig.create_skin_from_rest_transforms()
		var material:=StandardMaterial3D.new();material.albedo_color=Color("e9bc7f") if i>=5 and i<=10 else Color("81c5ca") if i<3 else Color("e8d3ad");material.roughness=.8;part.material_override=material
	var doc:=GLTFDocument.new();var state:=GLTFState.new();var error:=doc.append_from_scene(root,state)
	if error==OK:error=doc.write_to_filesystem(state,path)
	root.free();return error

static func build(folder: String) -> String:
	if DirAccess.make_dir_recursive_absolute(folder)!=OK:return "Cannot create practice assets."
	var room:=folder.path_join("Practice room.glb");var actor:=folder.path_join("Practice figure.glb")
	if SceneIO.make_fixture(room)!=OK or figure(actor)!=OK:return "Cannot build original practice geometry."
	var world:=World.empty();var map:=World.object(room,"environment","Practice room");map.id=ROOM_ID
	var model:=World.object(actor,"model","Practice figure");model.id=FIGURE_ID
	model.metadata={"tutorial_asset":"original-practice-figure-v1","provenance":{"source":"Original procedural geometry authored for this project","license":"Owner decision pending"}}
	model.pose_keys=[{"frame":0,"pose":{},"transform":{"position":[0,0,0],"rotation_xyzw":[0,0,0,1],"scale":1.},"interpolation":"ease"}]
	world.objects=[map,model]
	var position:=Vector3(2.8,2.2,5)
	var keys: Array=[Timeline.key(0,position,Basis.looking_at(Vector3(0,1,0)-position,Vector3.UP).get_rotation_quaternion(),55)]
	var video:={"width":1920,"height":1080,"fps_num":24,"fps_den":1,"duration_frames":48,"world_background":"black","lighting_mode":"unshaded","visibility_fade_ms":300}
	var layers: Array=[{"id":"practice-rough","name":"Rough","visible":true,"cels":[]},{"id":"practice-ink","name":"Ink","visible":true,"cels":[]}]
	var error:=Storage.save_project(folder.path_join("project"),video,keys,layers,"",0,{}, {},{},false,world)
	if not error.is_empty():return error
	return Storage.save_project(folder.path_join("first-movie"),video,keys,layers,"",0,{}, {},{},false,World.empty())
