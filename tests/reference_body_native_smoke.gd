extends SceneTree
# Actual prepared VRM geometry through import review, live Body Physics and HAS.
# This tests the common runtime path, not native-renderer or native-solver fidelity.
const Model = preload("res://src/model.gd")
const Height = preload("res://src/character_height.gd")
const Timeline = preload("res://src/timeline.gd")
const Drawing = preload("res://src/drawing.gd")
const Storage = preload("res://src/storage.gd")
var app
var request: Dictionary = {}
var folder: String
var checks: int = 0
var failures: int = 0
var metrics: Dictionary = {}
var reader: bool = false

func _initialize() -> void:
	create_timer(300).timeout.connect(func():push_error("Reference native body watchdog expired");quit(2))
	call_deferred("run")

func check(value: bool,label: String) -> void:
	checks += 1
	print(("PASS " if value else "FAIL ")+label)
	if not value:failures += 1

func settled() -> void:
	for index in range(4):await process_frame
	await RenderingServer.frame_post_draw

func wait_job() -> void:
	while app.has_project.pid > 0:await process_frame
	await settled()

func portable(value):
	return JSON.parse_string(JSON.stringify(value,"",true,true))

func digest(value) -> String:
	var hashing: HashingContext = HashingContext.new()
	hashing.start(HashingContext.HASH_SHA256);hashing.update(var_to_bytes(value))
	return hashing.finish().hex_encode()

func inventory(actor: RefCounted) -> Dictionary:
	var bones: Array = []
	for id in actor.order:
		var info: Dictionary = actor.bones[id]
		bones.append({"id":id,"base":info.base,"rest":info.skeleton.get_bone_rest(info.index)})
	var meshes: Array = []
	for node: MeshInstance3D in actor.root.find_children("*","MeshInstance3D",true,false):
		if node.mesh == null:continue
		var surfaces: Array = []
		for index in range(node.mesh.get_surface_count()):surfaces.append(digest(node.mesh.surface_get_arrays(index)))
		var binds: Array = []
		if node.skin:
			for index in range(node.skin.get_bind_count()):binds.append([node.skin.get_bind_bone(index),node.skin.get_bind_name(index),node.skin.get_bind_pose(index)])
		var shapes: Array = []
		for index in range(node.mesh.get_blend_shape_count()):shapes.append(node.mesh.get_blend_shape_name(index))
		meshes.append({"path":str(actor.root.get_path_to(node)),"surfaces":surfaces,"binds":digest(binds),"shapes":shapes})
	return {"order":actor.order.duplicate(),"bones":digest(bones),"meshes":meshes,"raw_root":digest(actor.raw_import_root),"base_root":digest(actor.base_root)}

func binding_error(simulation: RefCounted) -> Dictionary:
	# Rebuild source FK independently from the public ordinary pose. The
	# expectation is the actual physical frame, never the geometry planner.
	var actor: RefCounted = simulation.rig
	var captured: Dictionary = simulation.capture_pose()
	var globals: Dictionary = {}
	var position_error: float = 0.0
	var basis_error: float = 0.0
	var finite: bool = true
	for id in actor.order:
		var delta: Dictionary = captured.get(id,Model.identity())
		var base: Transform3D = actor.bones[id].base
		var local: Transform3D = Transform3D(base.basis*Basis(Timeline.quaternion(delta.rotation_xyzw)),base.origin+Timeline.vector(delta.position))
		var parent: String = actor.parent_id(id)
		globals[id] = globals[parent]*local if globals.has(parent) else local
	for id in simulation.bodies:
		var physical: PhysicalBone3D = simulation.bodies[id]
		var expected: Transform3D = physical.global_transform*physical.body_offset.affine_inverse()
		var actual: Transform3D = actor.bones[id].skeleton.global_transform*globals[id]
		finite = finite and actual.origin.is_finite() and actual.basis.x.is_finite() and actual.basis.y.is_finite() and actual.basis.z.is_finite()
		position_error = maxf(position_error,actual.origin.distance_to(expected.origin))
		basis_error = maxf(basis_error,maxf(actual.basis.x.distance_to(expected.basis.x),maxf(actual.basis.y.distance_to(expected.basis.y),actual.basis.z.distance_to(expected.basis.z))))
	return {"position":position_error,"basis":basis_error,"finite":finite}

func finish() -> void:
	if is_instance_valid(app):app.free();await settled()
	var result: Dictionary = {"checks":checks,"failures":failures,"role":request.role,"scale":request.scale,"mode":"reader" if reader else "writer","metrics":metrics,"native_fidelity_claimed":false}
	FileAccess.open(folder.path_join("reader-result.json" if reader else "writer-result.json"),FileAccess.WRITE).store_string(JSON.stringify(result,"",true,true))
	print("REFERENCE_BODY_NATIVE "+JSON.stringify(result,"",true,true))
	quit(0 if failures == 0 else 1)

func read_project() -> void:
	var expected: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
	app.has_project.open_file(folder.path_join("recorded.has"));await wait_job()
	var actor: RefCounted = app.renderer.world_runtime.instance(expected.id) if app.renderer.world_runtime else null
	check(actor != null and app.open_project_error.is_empty(),"cold packed HAS reconstructs the native reference")
	if actor == null:await finish();return
	app.world_selection.select_entity(expected.id);app.set_frame(6);await settled()
	check(actor.data.asset_basis == expected.asset_basis and is_equal_approx(float(actor.data.scale),float(request.scale)),"cold reader retains exact intrinsic reference and artist scale")
	check(portable(actor.data.metadata.native_parameters) == expected.native_parameters and actor.data.sha256 == request.source_sha256,"cold reader retains prepared/raw source provenance")
	check(portable(actor.authored_keys()) == expected.keys and actor.authored_keys().size() == 13,"cold reader restores all ordinary editable recording samples")
	check(portable(inventory(actor)) == expected.inventory,"cold reader retains source bones, rests, mesh, skin, shapes and captured roots")
	check(not app.physics_editor.is_running() and not app.height_review.pending,"cold playback neither simulates nor fits again")
	var image: Image = await app.renderer.capture(app.keys,app.layers,6,true)
	check(Storage.image_hash(image) == expected.pixels,"cold recorded frame matches ordinary preview pixels exactly")
	check(Drawing.image(Drawing.cel_at(app.layers[1],6)).get_pixel(80,80) == Color.CYAN,"cold reference retains the independent editable drawing")
	image.save_png(folder.path_join("cold.png"))
	await finish()

func run() -> void:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	request = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	folder = request.folder
	reader = args.size() > 1 and args[1] == "reader"
	var actual_root: String = ProjectSettings.globalize_path("res://").replace("\\","/").simplify_path().trim_suffix("/")
	metrics["project_root"] = actual_root
	check(actual_root.to_lower() == str(request.project_root).replace("\\","/").simplify_path().trim_suffix("/").to_lower(),"private job binds the requested checkout")
	app = load("res://main.tscn").instantiate()
	app.recovery_root = folder.path_join("reader-recovery" if reader else "writer-recovery")
	app.display_prefs_path = folder.path_join("display.cfg")
	app.recent_path = folder.path_join("recents.json")
	root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed = false
	app.has_project.cache_root = folder.path_join("reader-cache" if reader else "writer-cache")
	app.workspace_layout.path = folder.path_join("layout.json")
	if reader:await read_project();return
	app.new_project();app.load_demo_room();app.video.duration_frames = 12
	app.import_actions.offer_height = true
	var context: Dictionary = app.import_actions.placement();context.physics_on_import = false
	var error: String = app.pose_editor.add_model(request.source,0,context)
	while app.height_review.pending and not app.height_review.prepared:await process_frame
	await settled()
	check(error.is_empty() and app.height_review.pending and app.height_review.prepared and not app.height_review.reference.disabled,"actual native import review offers a complete six-foot reference")
	if not app.height_review.pending or app.height_review.reference.disabled:await finish();return
	app.height_review.reference.button_pressed = true
	app.height_review.apply();await settled()
	var actor: RefCounted = app.renderer.active_model()
	check(actor != null and actor.data.has("asset_basis") and actor.data.scale == 1.0,"review installs the intrinsic reference with artist Scale1")
	if actor == null:await finish();return
	check(absf(Height.query(actor).height-Height.SIX_FEET) < 0.0002,"native neutral mesh reaches six-foot visible height")
	check(FileAccess.get_sha256(request.source) == request.source_sha256 and FileAccess.get_sha256(request.parameters) == request.parameters_sha256,"staged prepared GLB and report retain separate checksums")
	check(actor.data.metadata.native_parameters.source_sha256 == request.raw_original_sha256_from_report,"native metadata retains the separately identified raw-original hash")
	app.pose_editor.auto_key.button_pressed = false
	app.pose_editor.human_size_field.value = request.scale
	app.pose_editor.human_size_apply.pressed.emit();await settled()
	check(is_equal_approx(float(actor.data.scale),float(request.scale)) and absf(Height.query(actor).height-Height.SIX_FEET*float(request.scale)) < 0.0003,"native relative size .5/1/2 uses the same immutable reference")
	actor.data.position = [0,2.5,0];actor.apply(0,false,true)
	app.world_selection.select_entity(actor.data.id);app.mode.select(1);app.change_mode(1)
	app.pose_editor.frame_model();app.keys = [Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,app.renderer.camera.fov)]
	Drawing.insert(app.layers[1],0,12,Drawing.blank(1920,1080));Drawing.edit_image(Drawing.cel_at(app.layers[1],0)).image.set_pixel(80,80,Color.CYAN)
	var id: String = actor.data.id
	var source_inventory: Dictionary = inventory(actor)
	var before: Dictionary = actor.data.duplicate(true)
	var history: int = app.history.size()
	app.physics_editor.toggle.button_pressed = true
	check(app.physics_editor.body_active(id),"connected Body Physics toggle starts the native reference")
	if not app.physics_editor.body_active(id):await finish();return
	var simulation: RefCounted = app.physics_editor.simulations[id]
	check(simulation.rig == actor and simulation.bodies.size() >= 3 and simulation.bodies.size() <= 48,"native body solver retains the original actor and bounded canonical bodies")
	var initial_error: Dictionary = binding_error(simulation)
	check(initial_error.finite and initial_error.position < 0.002 and initial_error.basis < 0.002,"native tick-zero physical frames reconstruct source FK")
	var start_y: float = 0.0
	for body in simulation.bodies.values():start_y += body.global_position.y
	start_y /= simulation.bodies.size()
	for index in range(60):await physics_frame
	var end_y: float = 0.0
	for body in simulation.bodies.values():end_y += body.global_position.y
	end_y /= simulation.bodies.size()
	var live_error: Dictionary = binding_error(simulation)
	metrics["initial_binding_error"] = initial_error
	metrics["live_binding_error"] = live_error
	metrics["physical_bodies"] = simulation.bodies.size()
	metrics["source_bones"] = actor.order.size()
	metrics["start_mean_y"] = start_y;metrics["end_mean_y"] = end_y
	check(live_error.finite and live_error.position < 0.002 and live_error.basis < 0.002 and end_y < start_y-0.05,"real fixed ticks move native bodies and preserve source-space readback")
	check(actor.data == before and app.history.size() == history and inventory(actor) == source_inventory,"native live body leaves authored data and original rig/skin/shape inventory intact")
	var frozen_pose: Dictionary = simulation.pose()
	app.physics_editor.toggle.button_pressed = false
	check(not app.physics_editor.body_active(id) and actor.data.pose == frozen_pose and app.history.size() == history+1,"native Physics off freezes the last ordinary source pose in one Undo")
	check(actor.data.asset_basis == before.asset_basis and is_equal_approx(float(actor.data.scale),float(request.scale)) and actor.data.metadata == before.metadata and inventory(actor) == source_inventory,"native freeze retains source identity, scale and inventory")
	var frozen: Dictionary = actor.data.duplicate(true)
	app.undo();actor = app.renderer.world_runtime.instance(id)
	check(actor.data == before,"native freeze Undo restores the exact authored reference")
	app.redo();actor = app.renderer.world_runtime.instance(id)
	check(actor.data == frozen,"native freeze Redo restores the exact source-space pose")
	app.undo();app.set_frame(0);actor = app.renderer.world_runtime.instance(id)
	app.world_selection.select_entity(id);app.physics_editor.toggle.button_pressed = true
	var record = app.physics_editor.recording
	record.scope.select(0);record.scope.item_selected.emit(0);record.button.pressed.emit()
	check(record.active and record.targets.has(id),"connected Local Record starts on the native reference")
	if not record.active:await finish();return
	while record.active:await process_frame
	await settled();actor = app.renderer.world_runtime.instance(id)
	check(record.last_error.is_empty() and app.frame == 12 and not app.physics_editor.is_running(),"native Local Record completes the exact short project boundary")
	check(actor.authored_keys().size() == 13 and app.history.size() == history+1,"native take stores thirteen editable samples as one Undo")
	check(actor.data.asset_basis == before.asset_basis and actor.data.metadata == before.metadata and inventory(actor) == source_inventory,"native recording retains reference facts and all source structure")
	app.set_frame(6);await settled()
	var image: Image = await app.renderer.capture(app.keys,app.layers,6,true)
	check(image != null and image.get_size() == Vector2i(1920,1080),"native recorded source renders through the ordinary preview")
	image.save_png(folder.path_join("preview.png"))
	var expected: Dictionary = {"id":id,"asset_basis":actor.data.asset_basis,"native_parameters":portable(actor.data.metadata.native_parameters),"keys":portable(actor.authored_keys()),"inventory":portable(source_inventory),"pixels":Storage.image_hash(image)}
	FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify(expected,"",true,true))
	app.has_project.save_file(folder.path_join("recorded.has"),"packed");await wait_job()
	check(FileAccess.file_exists(folder.path_join("recorded.has")) and not app.dirty,"native reference take saves as an ordinary packed HAS")
	check(FileAccess.get_sha256(request.source) == request.source_sha256 and FileAccess.get_sha256(request.parameters) == request.parameters_sha256,"native workflow keeps staged source/report bytes unchanged")
	await finish()
