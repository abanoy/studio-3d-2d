extends SceneTree
# Candidate only. This file is copied into a fresh exact-commit private project.
const SceneIO=preload("res://src/scene3d.gd")
const Shape=preload("res://src/source_shape.gd")
const AppProbe=preload("res://tests/sfm_probe_app_probe.gd")
const TOLERANCE:=0.0002
var checks:=0
var failures:=0
var viewport: SubViewport
var stage: Node3D
var camera: Camera3D
var captures:=[]
var material_observations:=[]
var geometry_observations:=[]

func _initialize() -> void:
	create_timer(180).timeout.connect(func():push_error("SFM derived probe watchdog");quit(2))
	call_deferred("run")

func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1

func digest(bytes: PackedByteArray) -> String:
	var hash:=HashingContext.new();hash.start(HashingContext.HASH_SHA256);hash.update(bytes)
	return hash.finish().hex_encode()

func settled() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw

func material_rows(scene: Node) -> Array:
	var result:=[]
	var meshes:=scene.find_children("*","MeshInstance3D",true,false)
	if scene is MeshInstance3D:meshes.push_front(scene)
	for mesh in meshes:
		for surface in range(mesh.mesh.get_surface_count()):
			var material: Material=mesh.get_active_material(surface)
			result.append({"mesh":mesh,"surface":surface,"material":material,"name":material.resource_name if material else ""})
	return result

func material_record(row: Dictionary) -> Dictionary:
	var material=row.material
	if not material is BaseMaterial3D:return {"name":row.name,"unsupported_class":material.get_class() if material else "null"}
	var texture: Texture2D=material.albedo_texture
	var image: Image=texture.get_image() if texture else null
	if image and image.is_compressed():image.decompress()
	if image:image.convert(Image.FORMAT_RGBA8)
	return {"name":row.name,"render_priority":material.render_priority,"transparency":material.transparency,
		"metallic":material.metallic,"roughness":material.roughness,"emission_enabled":material.emission_enabled,
		"albedo_color":[material.albedo_color.r,material.albedo_color.g,material.albedo_color.b,material.albedo_color.a],
		"width":image.get_width() if image else 0,"height":image.get_height() if image else 0,
		"rgba8_sha256":digest(image.get_data()) if image else ""}

func inspect(scene: Node,plan: Dictionary) -> bool:
	var start:=failures
	var rows:=material_rows(scene);var records:=[]
	check(rows.size()==plan.primitives.size(),plan.key+" keeps every as-supplied primitive including glow")
	var names:={}
	for expected in plan.materials:names[expected.name]=expected
	for row in rows:
		var record:=material_record(row);records.append(record)
		check(names.has(row.name),plan.key+" runtime material has exact declared identity: "+row.name)
		if not names.has(row.name):continue
		var expected: Dictionary=names[row.name]
		check(record.get("rgba8_sha256","")==expected.image.rgba8_sha256 and record.get("width",0)==int(expected.image.width) and record.get("height",0)==int(expected.image.height),plan.key+" decoded runtime texture pixels match independent embedded PNG: "+row.name)
	var skeletons:=scene.find_children("*","Skeleton3D",true,false)
	var count:=0;var bound_names:={}
	for skeleton in skeletons:
		count+=skeleton.get_bone_count()
		for index in range(skeleton.get_bone_count()):
			var name: String=skeleton.get_bone_name(index);bound_names[name]=int(bound_names.get(name,0))+1
	var bindings:=true
	for bone in plan.parameters.native_parameters.bones:bindings=bindings and int(bound_names.get(bone.name,0))==1
	check(bindings,plan.key+" retains every exact native bone name once")
	material_observations.append({"case":plan.key,"materials":records,"native_bone_count":plan.bones,"runtime_bone_count":count,"scope":"Actual runtime derived PBR materials and embedded image pixels; no native shader equivalence"})
	return failures==start

func engine_points(mesh: MeshInstance3D,surface: int) -> Array:
	# Independent engine bake, not product pose-bounds or source-shape cache output.
	var source: MeshInstance3D=mesh;var temporary: MeshInstance3D
	if mesh.get_blend_shape_count()>0:
		temporary=MeshInstance3D.new();temporary.mesh=mesh.bake_mesh_from_current_blend_shape_mix();temporary.skin=mesh.skin;temporary.transform=mesh.transform;temporary.visible=false
		mesh.get_parent().add_child(temporary)
		var skeleton=mesh.get_node_or_null(mesh.skeleton)
		if skeleton is Skeleton3D:temporary.skeleton=temporary.get_path_to(skeleton);skeleton.force_update_all_bone_transforms()
		source=temporary
	var baked: Mesh=source.bake_mesh_from_current_skeleton_pose() if source.get_skin_reference()!=null else source.mesh
	var arrays:=baked.surface_get_arrays(surface)
	var vertices: PackedVector3Array=arrays[Mesh.ARRAY_VERTEX]
	var used:={};var indices=arrays[Mesh.ARRAY_INDEX]
	if indices is PackedInt32Array and not indices.is_empty():
		for index in indices:used[index]=true
	else:
		for index in range(vertices.size()):used[index]=true
	var result:=[]
	for index in used:result.append(mesh.global_transform*vertices[index])
	if temporary:temporary.free()
	return result

func cell(point: Vector3) -> Vector3i:
	return Vector3i(floori(point.x/TOLERANCE),floori(point.y/TOLERANCE),floori(point.z/TOLERANCE))

func max_nearest(source: Array,target: Array) -> float:
	var grid:={}
	for point: Vector3 in target:
		var key:=cell(point)
		if not grid.has(key):grid[key]=[]
		grid[key].append(point)
	var maximum:=0.0
	for point: Vector3 in source:
		var key:=cell(point);var nearest:=INF
		for x in [-1,0,1]:
			for y in [-1,0,1]:
				for z in [-1,0,1]:
					for other in grid.get(key+Vector3i(x,y,z),[]):nearest=minf(nearest,point.distance_to(other))
		maximum=maxf(maximum,nearest)
	return maximum

func compare_geometry(scene: Node,references: Array,label: String) -> Dictionary:
	var rows:=material_rows(scene);var errors:=[];var by_name:={};var all_points:=[]
	for row in rows:
		check(not by_name.has(row.name),label+" has unambiguous material-to-primitive mapping")
		by_name[row.name]=row
	for reference in references:
		check(by_name.has(reference.material_name),label+" reference primitive exists: "+reference.material_name)
		if not by_name.has(reference.material_name):continue
		var row: Dictionary=by_name[reference.material_name]
		var actual:=engine_points(row.mesh,row.surface)
		var expected:=[]
		for p in reference.positions:expected.append(Vector3(float(p[0]),float(p[1]),float(p[2])))
		var distance:=maxf(max_nearest(actual,expected),max_nearest(expected,actual))
		check(not actual.is_empty() and is_finite(distance) and distance<TOLERANCE,label+" engine-baked world points match independent derived reference: "+row.name)
		var vectors:=PackedVector3Array(actual)
		errors.append({"material":row.name,"source_node":reference.source_node,"source_name":reference.source_name,"engine_used_vertex_records":actual.size(),"reference_used_vertex_records":expected.size(),"symmetric_max_nearest_error":distance if is_finite(distance) else -1,"engine_points_sha256":digest(vectors.to_byte_array())})
		all_points.append_array(actual)
	return {"case":label,"point_tolerance_world_units":TOLERANCE,"primitives":errors,"points":all_points}

func set_pose(scene: Node,source_node: int,quaternion: Array) -> void:
	var bindings: Dictionary=scene.get_meta("has_source_bones",{})
	check(bindings.has(source_node),"pose has exact source-node binding "+str(source_node))
	if not bindings.has(source_node):return
	var binding: String=bindings[source_node];var split:=binding.rfind("::")
	var skeleton: Skeleton3D=scene.get_node(binding.substr(0,split))
	var index:=skeleton.find_bone(binding.substr(split+2))
	check(index>=0,"pose retains exact source bone identifier")
	if index>=0:
		# Godot 4 poses are absolute local channels. Preserve imported base rotation.
		var base_rotation:=skeleton.get_bone_pose_rotation(index)
		var delta:=Quaternion(float(quaternion[0]),float(quaternion[1]),float(quaternion[2]),float(quaternion[3]))
		skeleton.set_bone_pose_rotation(index,(base_rotation*delta).normalized())
		skeleton.force_update_all_bone_transforms()

func setup_view() -> void:
	viewport=SubViewport.new();viewport.size=Vector2i(1920,1080);viewport.own_world_3d=true;viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS
	root.add_child(viewport);stage=Node3D.new();viewport.add_child(stage)
	var world_environment:=WorldEnvironment.new();var environment:=Environment.new()
	environment.background_mode=Environment.BG_COLOR;environment.background_color=Color(.13,.15,.18)
	environment.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR;environment.ambient_light_color=Color.WHITE;environment.ambient_light_energy=.5
	world_environment.environment=environment;stage.add_child(world_environment)
	var light:=DirectionalLight3D.new();light.rotation_degrees=Vector3(-35,-25,0);light.light_energy=1.;stage.add_child(light)
	camera=Camera3D.new();camera.fov=45;camera.near=.001;camera.far=100.;stage.add_child(camera);camera.current=true

func frame_union(manifest: Dictionary,group: String) -> void:
	var bounds:=AABB();var first:=true
	for capture in manifest.render_cases:
		if not str(capture.case).begins_with(group):continue
		var low: Array=capture.bounds[0];var high: Array=capture.bounds[1]
		var minimum:=Vector3(float(low[0]),float(low[1]),float(low[2]));var maximum:=Vector3(float(high[0]),float(high[1]),float(high[2]))
		var box:=AABB(minimum,maximum-minimum);bounds=box if first else bounds.merge(box);first=false
	var radius:=maxf(bounds.size.length()*.5,.01)
	var center:=bounds.get_center();var distance:=radius/sin(deg_to_rad(camera.fov*.5))*1.1
	camera.position=center+Vector3(0,0,distance);camera.look_at(center,Vector3.UP)

func raw_cases(manifest: Dictionary,folder: String) -> void:
	setup_view()
	for plan in manifest.cases:
		check(FileAccess.get_sha256(plan.input_glb)==plan.glb_sha256,plan.key+" reads exact owned GLB bytes")
		var loaded: Dictionary=SceneIO.load_glb(plan.input_glb)
		check(not loaded.has("error"),plan.key+" loads its real derived GLB")
		if loaded.has("error"):continue
		stage.add_child(loaded.scene);Shape.apply(loaded.scene,true);await settled();inspect(loaded.scene,plan);loaded.scene.free()
	var references: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(manifest.derived_reference.path)).captures
	var pixel_hashes:={};var controls:={}
	for capture in manifest.render_cases:
		var plans: Array=manifest.cases.filter(func(value):return value.key==capture.case)
		var plan: Dictionary=plans[0];var loaded: Dictionary=SceneIO.load_glb(plan.input_glb)
		if loaded.has("error"):check(false,capture.key+" cannot load capture source");continue
		var scene: Node=loaded.scene;stage.add_child(scene);Shape.apply(scene,true)
		if capture.has("morph_weight"):
			var rows: Array=scene.get_meta(Shape.META,{"rows":[]}).rows
			var matched:=0
			for row in rows:
				if row.names==["Tools"]:row.mesh.set_blend_shape_value(0,float(capture.morph_weight));matched+=1
			check(matched==1,capture.key+" adjusts the one actual Tools channel")
		if capture.has("pose_node"):set_pose(scene,int(capture.pose_node),capture.pose_quaternion)
		frame_union(manifest,"nitori" if str(capture.case).begins_with("nitori") else "keiki");await settled()
		var observation:=compare_geometry(scene,references[capture.key],capture.key)
		var fits:=true
		for p: Vector3 in observation.points:
			var pixel:=camera.unproject_position(p)
			fits=fits and not camera.is_position_behind(p) and pixel.x>=0 and pixel.x<1920 and pixel.y>=0 and pixel.y<1080
		check(fits,capture.key+" fixed camera contains all actual posed points")
		observation.erase("points");geometry_observations.append(observation)
		var image:=viewport.get_texture().get_image();image.convert(Image.FORMAT_RGBA8)
		var pixels:=image.get_data();var changed:=0;var background:=image.get_pixel(0,0)
		for y in range(0,1080,4):
			for x in range(0,1920,4):changed+=int(image.get_pixel(x,y)!=background)
		check(changed>100,capture.key+" produces positively visible geometry")
		check(image.save_png(folder.path_join(capture.key+".png"))==OK,capture.key+" retains its actual as-supplied screenshot")
		pixel_hashes[capture.key]=digest(pixels);captures.append(capture.key)
		if capture.has("morph_weight"):
			for primitive in observation.primitives:
				if float(capture.morph_weight)==0:controls[primitive.material]=primitive.engine_points_sha256
				if primitive.source_name!="tools.dmx":
					check(controls[primitive.material]==primitive.engine_points_sha256,capture.key+" keeps unrelated box/flame geometry exact")
		if capture.has("pose_node") and capture.case=="keiki-000":
			for primitive in observation.primitives:
				if primitive.source_name!="box.smd":check(controls.get(primitive.material,"")==primitive.engine_points_sha256,"box pose keeps tools/flame geometry exact")
		scene.free()
	check(pixel_hashes.get("keiki-tools-0.0","")!=pixel_hashes.get("keiki-tools-0.5","") and pixel_hashes.get("keiki-tools-0.5","")!=pixel_hashes.get("keiki-tools-1.0",""),"actual Tools 0, .5 and 1 produce distinct derived pixels")
	check(pixel_hashes.get("keiki-000-pose","")!=pixel_hashes.get("keiki-tools-0.0",""),"actual box pose changes derived pixels")
	check(pixel_hashes.get("nitori-skin-0-pose","")!=pixel_hashes.get("nitori-skin-0-rest",""),"actual hand pose changes derived pixels")
	# The three skins may render alike behind their coincident opaque glow layer.
	# Record their pixels; never delete that layer to manufacture a color pass.
	material_observations.append({"capture_pixel_hashes":pixel_hashes,"native_shader_fidelity":"UNTESTED; native additive glow remains ordinary PBR"})
	viewport.free();viewport=null

func run() -> void:
	var args:=OS.get_cmdline_user_args();var manifest: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(args[0]));var folder: String=args[1];var mode: String=args[2]
	check(mode in ["writer","reader"],"candidate has an explicit writer/reader mode")
	if mode=="writer":await raw_cases(manifest,folder)
	var probe:=AppProbe.new();var app_result: Dictionary=await probe.run(self,manifest,folder,mode)
	checks+=int(app_result.checks);failures+=int(app_result.failures)
	var result:={"checks":checks,"failures":failures,"nonce":manifest.nonce,"mode":mode,"raw_captures":captures,"app_cases":app_result.get("app_cases",[]),"app":app_result,"materials":material_observations,"geometry":geometry_observations,"scope":{"structure":"derived GLB","render":"actual as-supplied PBR captures","app":"ordinary current contracts","native_fidelity":"UNTESTED"}}
	var file:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(result,"",true,true));file.close()
	print("SFM_DERIVED_PROBE "+JSON.stringify({"checks":checks,"failures":failures,"mode":mode,"nonce":manifest.nonce}))
	quit(0 if failures==0 else 1)
