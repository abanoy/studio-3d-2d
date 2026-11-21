extends SceneTree
# SOURCE ONLY / UNPARSED / UNRUN. Root runs in an owned private GPU project.
# Arguments: -- <protected stuff.has> <new private output directory>
const Renderer = preload("res://src/renderer.gd")
const World = preload("res://src/world_document.gd")
const Bounds = preload("res://src/pose_bounds.gd")
const ZIP_SHA := "d304744dea70a05e7176b668bc10b0058b8cb4e6b1ffe5fc9fab05303da60efb"
const ASSET_SHA := "e3e233004f2ce1aed3c2f221f7d92d9218c0de1f133cad88557f8181644e6e8c"
var renderer: Node
var folder := ""
var records: Array = []
var failed := false

func _initialize() -> void:
	create_timer(180).timeout.connect(func(): push_error("Private face diagnostic watchdog"); quit(2))
	call_deferred("run")

func require_ok(ok: bool, reason: String) -> bool:
	if not ok:
		push_error(reason); failed = true
	return ok

func image_hash(image: Image) -> String:
	var context := HashingContext.new()
	if context.start(HashingContext.HASH_SHA256)!=OK: return ""
	context.update(image.get_data())
	return context.finish().hex_encode()

func meshes_below(node: Node, found: Array) -> void:
	if node is MeshInstance3D and node.mesh: found.append(node)
	for child in node.get_children(): meshes_below(child, found)

func face_surface(actor: Node3D) -> Dictionary:
	var meshes: Array = []; meshes_below(actor, meshes)
	var matches: Array = []
	for mesh in meshes:
		for surface in range(mesh.mesh.get_surface_count()):
			var material: Material = mesh.get_active_material(surface)
			if material is BaseMaterial3D and material.resource_name == "face":
				matches.append({"mesh":mesh,"surface":surface,"material":material})
	return matches[0] if matches.size() == 1 else {}

func depth_interval(bounds: AABB) -> Array:
	var low := INF; var high := -INF
	for x in [0,1]:
		for y in [0,1]:
			for z in [0,1]:
				var point: Vector3 = bounds.position + bounds.size * Vector3(x,y,z)
				var depth: float = -renderer.camera.to_local(point).z
				low = minf(low,depth); high = maxf(high,depth)
	return [low,high]

func render_cell(label: String, frame: int, editing: bool, backoff: float, control: String, camera_view: Dictionary, face: Dictionary) -> bool:
	var runtime: RefCounted = renderer.world_runtime
	var id: String = runtime.order[0]
	runtime.evaluate(frame,false,id if editing else "",renderer.video_settings)
	if not require_ok(runtime.evaluation_error.is_empty(),"World evaluation failed"): return false
	renderer.restore_view(camera_view)
	renderer.camera.global_position += renderer.camera.global_basis.z.normalized() * backoff
	var mesh: MeshInstance3D = face.mesh
	# Resolve the current effective material after evaluation; only our private
	# override is changed. No imported shared resource is mutated.
	var active: BaseMaterial3D = mesh.get_active_material(face.surface)
	var previous_override: Material = mesh.get_surface_override_material(face.surface)
	var previous_margin: float = mesh.extra_cull_margin
	var previous_bounds: AABB = mesh.custom_aabb
	if control in ["double_sided","opaque_face"]:
		var diagnostic_material: BaseMaterial3D = active.duplicate()
		if control == "double_sided": diagnostic_material.cull_mode = BaseMaterial3D.CULL_DISABLED
		if control == "opaque_face": diagnostic_material.transparency = BaseMaterial3D.TRANSPARENCY_DISABLED
		mesh.set_surface_override_material(face.surface,diagnostic_material)
	elif control == "near_tenth": renderer.camera.near = camera_view.near * 0.1
	elif control == "bounds_margin": mesh.extra_cull_margin = maxf(10.,mesh.get_aabb().size.length()*10.)
	# Bounds query observes the current skin/morph pose, without changing poses.
	var posed: Dictionary = Bounds.query(mesh)
	var row := {"label":label,"frame":frame,"editing_draft_context":editing,"backoff":backoff,"control":control,"camera_fov":renderer.camera.fov,"camera_near":renderer.camera.near,"camera_far":renderer.camera.far,"camera_transform":str(renderer.camera.global_transform),"face_material_name":active.resource_name,"baseline_transparency":active.transparency,"baseline_cull_mode":active.cull_mode,"mesh_aabb":str(mesh.get_aabb()),"custom_aabb":str(previous_bounds),"posed_bounds_error":posed.error,"pose_vertices_examined":posed.vertices,"pose_bounds_conservative_count":posed.conservative}
	if posed.error.is_empty(): row["posed_face_mesh_depth_interval"] = depth_interval(posed.bounds)
	# Two frame boundaries avoid diagnosing a stale first frame. Neither capture
	# calls renderer.capture(), which would re-evaluate away the editing context.
	var image: Image = null
	for tick in range(2):
		if not renderer.begin_native_readback(): failed=true; break
		await renderer.native_frame_ready
		image = renderer.finish_native_readback()
	if image != null and not image.is_empty():
		var name := label+".png"
		row["image"] = name
		row["save_error"] = image.save_png(folder.path_join(name))
		if not require_ok(row.save_error==OK,"Diagnostic image could not be saved"): failed=true
		row["image_dimensions"] = [image.get_width(),image.get_height()]
		row["image_raw_sha256"] = image_hash(image)
	else:
		row["error"] = "No native image"; failed=true
	mesh.set_surface_override_material(face.surface,previous_override)
	mesh.extra_cull_margin = previous_margin; mesh.custom_aabb = previous_bounds
	renderer.restore_view(camera_view)
	records.append(row)
	return not failed

func run() -> void:
	var args := OS.get_cmdline_user_args()
	if not require_ok(args.size()==2,"Need protected archive and new private output directory"): quit(2); return
	var archive: String = args[0]; folder = args[1]
	if not require_ok(FileAccess.get_sha256(archive)==ZIP_SHA,"Protected fixture SHA mismatch"): quit(2); return
	if not require_ok(not DirAccess.dir_exists_absolute(folder) and not FileAccess.file_exists(folder),"Output directory must be new"): quit(2); return
	if not require_ok(DirAccess.make_dir_recursive_absolute(folder)==OK,"Cannot create owned private output"): quit(2); return
	var zip := ZIPReader.new()
	if not require_ok(zip.open(archive)==OK,"Cannot read protected archive"): quit(2); return
	var project = JSON.parse_string(zip.read_file("project.json").get_string_from_utf8())
	var asset := zip.read_file("assets/"+ASSET_SHA+".glb")
	zip.close()
	if not require_ok(project is Dictionary and project.world.objects.size()==1,"Expected one-actor saved world"): quit(2); return
	# A private GLB working copy is necessary for the production importer. It is
	# confined to this new diagnostic output; it must never enter a public packet.
	var asset_path := folder.path_join("private-model.glb")
	var file := FileAccess.open(asset_path,FileAccess.WRITE)
	if not require_ok(file!=null,"Cannot write private working asset"): quit(2); return
	file.store_buffer(asset); file.close()
	if not require_ok(FileAccess.get_sha256(asset_path)==ASSET_SHA,"Embedded GLB SHA mismatch"): quit(2); return
	var document: Dictionary = project.world.duplicate(true)
	document.objects[0]["source"] = asset_path
	var authored_snapshot := JSON.stringify(document,"",true,true)
	renderer = Renderer.new(); root.add_child(renderer)
	renderer.setup(int(project.video.width),int(project.video.height))
	renderer.video_settings = project.video.duplicate(true)
	renderer.set_background("black"); renderer.editor_grid.visible=false
	var prepared: Dictionary = renderer.prepare_world(document,int(project.video.duration_frames),project.video)
	if not require_ok(not prepared.has("error"),"Cannot prepare saved world"): renderer.queue_free(); quit(2); return
	if not require_ok(renderer.install_world(prepared),"Cannot install private saved world"): renderer.queue_free(); quit(2); return
	var actor: RefCounted = renderer.world_runtime.instance(renderer.world_runtime.order[0])
	var face: Dictionary = face_surface(actor.root)
	if not require_ok(not face.is_empty(),"Expected exactly one named face material surface"): renderer.queue_free(); quit(2); return
	# Two distinct saved contexts: playback at editor frame0, and selected-actor
	# editing at saved draft43. Neither rewrites keys, pose, FOV, or visibility.
	for context in [{"frame":0,"editing":false},{"frame":43,"editing":true}]:
		renderer.evaluate(project.camera_keys,context.frame)
		var camera_view: Dictionary = renderer.view_state()
		for backoff in [0.,0.1,0.3,1.]:
			for control in ["baseline","near_tenth","double_sided","opaque_face","bounds_margin"]:
				var label := "frame%d_%s_backoff%.2f_%s" % [context.frame,"draft" if context.editing else "playback",backoff,control]
				if not await render_cell(label,context.frame,context.editing,backoff,control,camera_view,face): break
			if failed: break
		if failed: break
	var unchanged: bool = JSON.stringify(renderer.world_runtime.data,"",true,true)==authored_snapshot
	var fixture_unchanged: bool = FileAccess.get_sha256(archive)==ZIP_SHA
	if not require_ok(records.size()==40,"Expected exactly forty diagnostic captures"): failed=true
	if not require_ok(fixture_unchanged,"Protected archive changed during diagnostic"): failed=true
	var summary := {"format":"has_private_close_face_diagnostic_1","status":"CAPTURED_FOR_REVIEW" if not failed and unchanged else "ERROR","diagnosis_proven":false,"fixture_sha256":ZIP_SHA,"saved_data_unchanged":unchanged,"fixture_sha256_unchanged":fixture_unchanged,"captures":records,"scope":"All images, working GLB, camera transforms and poses remain private. Controls are diagnostic only. Visual comparison required; a changed image does not establish a cause."}
	var result := FileAccess.open(folder.path_join("PRIVATE_RESULT.json"),FileAccess.WRITE)
	if result:
		result.store_string(JSON.stringify(summary,"\t",true,true)+"\n"); result.flush()
		if result.get_error()!=OK: failed=true
		result.close()
	else: failed=true
	renderer.queue_free(); await process_frame; await process_frame
	quit(0 if not failed and unchanged else 1)
