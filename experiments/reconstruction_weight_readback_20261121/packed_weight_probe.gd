extends SceneTree
var checks:=0
var failures:=0
func _initialize() -> void:call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1
	print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func run() -> void:
	var args:=OS.get_cmdline_user_args()
	var folder: String=args[0]
	var recipe: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(args[2]))
	var version:=Engine.get_version_info()
	check(DisplayServer.get_name()=="headless" and version.hash=="89cea143987d564363e15d207438530651d943ac","actual pinned headless engine")
	var document:=GLTFDocument.new()
	var state:=GLTFState.new()
	var error:=document.append_from_file(args[1],state)
	check(error==OK,"actual authored four/eight-slot GLTF import")
	if error!=OK:quit(1);return
	var model:=document.generate_scene(state)
	root.add_child(model)
	var meshes:={}
	for item in model.find_children("*","MeshInstance3D",true,false):meshes[str(item.name)]=item
	check(meshes.size()==recipe.cases.size(),"every authored case imports as a unique skinned mesh")
	var actual:={}
	for row in recipe.cases:
		var mesh: MeshInstance3D=meshes.get(row.name)
		if mesh==null:
			check(false,"missing "+row.name)
			continue
		var arrays: Array=mesh.mesh.surface_get_arrays(0)
		var weights: PackedFloat32Array=arrays[Mesh.ARRAY_WEIGHTS]
		var bones: PackedInt32Array=arrays[Mesh.ARRAY_BONES]
		var count: int=arrays[Mesh.ARRAY_VERTEX].size()
		var slots: int=weights.size()/count
		check(count==3 and slots==int(row.slots) and bones.size()==weights.size(),row.name+" actual slot count and topology")
		var skeleton: Skeleton3D=mesh.get_node(mesh.skeleton)
		var names: Array=[]
		var identities:=true
		var readback: Array=[]
		for slot in range(slots):
			var bind: int=bones[slot]
			var name: String=mesh.skin.get_bind_name(bind)
			if name.is_empty():name=str(skeleton.get_bone_name(mesh.skin.get_bind_bone(bind)))
			names.append(name)
			readback.append(float(weights[slot]))
			if weights[slot]>0. and name!="FixtureJ"+str(int(row.joints[slot])):identities=false
		check(identities,row.name+" positive weights retain actual bone identities")
		var exact: bool=readback.size()==row.prediction.readback_bits.size()
		var bits:=PackedByteArray()
		bits.resize(4)
		for slot in range(mini(readback.size(),row.prediction.readback_bits.size())):
			bits.encode_u32(0,int(row.prediction.readback_bits[slot]))
			if readback[slot]!=bits.decode_float(0):exact=false
		check(exact,row.name+" exact predicted normalized UNORM16 readback")
		var repeated:=true
		for v in range(count):
			for slot in range(slots):
				if weights[v*slots+slot]!=weights[slot] or bones[v*slots+slot]!=bones[slot]:repeated=false
		check(repeated,row.name+" all authored vertices share the measured row")
		actual[row.name]={"weights":readback,"bone_names":names,"slots":slots,"mesh_format":mesh.mesh.surface_get_format(0)}
	var original: Array=actual["source_0"].weights
	var halves: Array=actual["naive_0_1"].weights
	check(original[0]==1. and halves[0]+halves[1]<original[0],"actual half split loses imported weight mass")
	var result:={"checks":checks,"failures":failures,"user_profile":OS.get_user_data_dir(),"cases":recipe.cases.size(),"actual":actual,"graphics":false}
	FileAccess.open(folder.path_join("actual.json"),FileAccess.WRITE).store_string(JSON.stringify(result,"",true,true))
	print("PACKED_WEIGHT_PROBE "+JSON.stringify({"checks":checks,"failures":failures,"user_profile":OS.get_user_data_dir(),"cases":recipe.cases.size(),"graphics":false}))
	model.queue_free()
	await process_frame
	quit(0 if failures==0 else 1)
