extends SceneTree
const Model=preload("res://src/model.gd")
const Timeline=preload("res://src/timeline.gd")
var checks:=0
var failures:=0
func check(value: bool, message: String) -> void:
	checks+=1
	if not value:failures+=1;push_error("FAIL "+message)
func _initialize() -> void:
	create_timer(90).timeout.connect(func():push_error("Morph render watchdog");quit(2))
	call_deferred("run")
func weights(actor: RefCounted, values: Array) -> Array:
	var meshes: Array=actor.root.find_children("*","MeshInstance3D",true,false)
	if actor.root is MeshInstance3D:meshes.push_front(actor.root)
	for mesh in meshes:
		for i in range(values.size()):mesh.set_blend_shape_value(i,float(values[i]))
	return meshes
func delta(a: Image,b: Image) -> Dictionary:
	var x:=a.get_data();var y:=b.get_data();var changed:=0;var total:=0
	for i in range(x.size()):
		if x[i]!=y[i]:changed+=1;total+=absi(int(x[i])-int(y[i]))
	return {"changed":changed,"mean":float(total)/x.size()}
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0]
	var plan: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("plan.json")))
	var app=load("res://main.tscn").instantiate();root.add_child(app)
	await process_frame;await process_frame
	var metrics:={}
	for case in plan.cases:
		app.new_project();app.append_object(Model.definition(case.source),"model")
		var actor: RefCounted=app.renderer.active_model()
		app.pose_editor.frame_model();app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,app.renderer.camera.fov)]
		var meshes:=weights(actor,case.weights)
		var shaped: Image=await app.renderer.capture(app.keys,app.layers,0,true)
		shaped.save_png(folder.path_join(case.name+"-shape.png"))
		var maximum:=0.0;var surfaces:=0
		for mesh in meshes:
			var baked: ArrayMesh=mesh.bake_mesh_from_current_blend_shape_mix()
			for surface in range(baked.get_surface_count()):
				var actual: PackedVector3Array=baked.surface_get_arrays(surface)[Mesh.ARRAY_VERTEX]
				var expected: Array=case.positions[surface];surfaces+=1
				check(actual.size()==expected.size(),case.name+" actual GPU bake vertex count")
				for i in range(mini(actual.size(),expected.size())):
					maximum=maxf(maximum,actual[i].distance_to(Vector3(expected[i][0],expected[i][1],expected[i][2])))
		check(surfaces==case.positions.size() and maximum<0.00001,case.name+" actual GPU morph mix agrees with bounded CPU preview")
		var zeros: Array=case.weights.duplicate();zeros.fill(0.);weights(actor,zeros);var neutral: Image=await app.renderer.capture(app.keys,app.layers,0,true)
		check(delta(neutral,shaped).changed>100,case.name+" morph causes visible GPU deformation")
		var world: Dictionary=app.current_world();world.objects[0].source=case.derived;world.objects[0].sha256=FileAccess.get_sha256(case.derived)
		check(app.restore_world(world).is_empty(),case.name+" derived helper revision loads")
		actor=app.renderer.active_model();weights(actor,case.weights)
		var derived: Image=await app.renderer.capture(app.keys,app.layers,0,true);var difference:=delta(shaped,derived)
		check(difference.changed<=384 and difference.mean<.002,case.name+" generated joints retain shaped pixels")
		var def: Dictionary=actor.root.get_meta("has_secondary_rig")
		check(def.error.is_empty() and def.chains.size()==1,case.name+" generated chain binds")
		var helper: String=def.chains[0].joints[0].binding.id;var rotation:=Quaternion(Vector3.BACK,.6)
		actor.data.pose[helper]={"position":[0,0,0],"rotation_xyzw":[rotation.x,rotation.y,rotation.z,rotation.w]}
		var bent: Image=await app.renderer.capture(app.keys,app.layers,0,true)
		bent.save_png(folder.path_join(case.name+"-bent.png"))
		check(delta(derived,bent).changed>100,case.name+" generated joint moves the actually morphed skin")
		metrics[case.name]={"gpu_geometry_error":maximum,"reimport":difference,"deformation":delta(derived,bent).changed}
	var result:={"checks":checks,"failures":failures,"metrics":metrics}
	var file:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close()
	print("HELPER_MORPHS "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
