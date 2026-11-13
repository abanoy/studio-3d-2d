extends Node
signal assets_changed
signal view_changed
class NativeFrameNotification extends RefCounted:
	signal ready
var native_frame_notification:=NativeFrameNotification.new()
var native_frame_ready: Signal:
	get:return native_frame_notification.ready
const SceneIO = preload("res://src/scene3d.gd")
const Timeline = preload("res://src/timeline.gd")
const Drawing = preload("res://src/drawing.gd")
const Model = preload("res://src/model.gd")
const WorldRuntime = preload("res://src/world_runtime.gd")
const Lighting=preload("res://src/lighting.gd")
const PoseBounds=preload("res://src/pose_bounds.gd")
const GUIDE_LAYER:=1<<18
var viewport: SubViewport
var world: Node3D
var camera: Camera3D
var environment_scene: Node3D
var model: RefCounted
var world_runtime: RefCounted
var active_instance_id := ""
var editor_grid: MeshInstance3D
var empty_environment := true
var capturing_final := false
var native_readbacks:=0
var native_view_closing:=false
var world_environment: WorldEnvironment
var video_settings: Dictionary={}
var studio_light: DirectionalLight3D
var legacy_materials: RefCounted
var last_lighting:=""
var last_framing: Dictionary={}
var last_capture_error:=""
var sequence_instance:=false
var sequence_runtime: Node
var sequence_owner:=""
var before_final_capture:=Callable()
var before_asset_replace:=Callable()

func setup(width := 1920, height := 1080) -> void:
	viewport = SubViewport.new()
	viewport.size = Vector2i(width, height)
	viewport.own_world_3d = true
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(viewport)
	world = Node3D.new()
	viewport.add_child(world)
	var env := WorldEnvironment.new()
	world_environment = env
	env.environment = Environment.new()
	env.environment.background_mode = Environment.BG_COLOR
	env.environment.background_color = Color("263646")
	env.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.environment.ambient_light_color = Color("d2e2f2")
	env.environment.ambient_light_energy = 0.7
	world.add_child(env)
	var light := DirectionalLight3D.new()
	studio_light=light
	light.rotation_degrees = Vector3(-40, -30, 0)
	light.light_energy = 1.2
	world.add_child(light)
	camera = Camera3D.new()
	camera.far = 2000
	world.add_child(camera)
	camera.current = true
	editor_grid = MeshInstance3D.new()
	editor_grid.name = "EditorOnlyGrid"
	editor_grid.layers=GUIDE_LAYER
	var plane := PlaneMesh.new()
	plane.size = Vector2(256, 256)
	editor_grid.mesh = plane
	var grid_material := ShaderMaterial.new()
	grid_material.shader = preload("res://src/editor_grid.gdshader")
	editor_grid.material_override = grid_material
	editor_grid.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	world.add_child(editor_grid)

func set_background(kind: String) -> void:
	world_environment.environment.background_color = Color.BLACK if kind == "black" else Color("263646")

func _process(_delta: float) -> void:
	apply_lighting()
	if editor_grid:
		editor_grid.position = Vector3(floorf(camera.position.x), 0, floorf(camera.position.z))
		editor_grid.visible = empty_environment and not capturing_final and not sequence_instance

func apply_lighting() -> void:
	var kind:=Lighting.mode(video_settings)
	if kind!=last_lighting:
		last_lighting=kind
		studio_light.visible=kind=="studio"
		world_environment.environment.ambient_light_energy=0.7 if kind=="studio" else 0.
		world_environment.environment.ambient_light_sky_contribution=1. if kind=="studio" else 0.
	if environment_scene:
		if not legacy_materials:
			legacy_materials=Model.Opacity.new();legacy_materials.inventory(environment_scene)
		legacy_materials.set_appearance(1.,kind=="unshaded")

func import_scene(path: String) -> String:
	if world_runtime:return "A multi-object world is installed. Use the world import workflow."
	var result := SceneIO.load_glb(path)
	if result.has("error"):
		return result.error
	if before_asset_replace.is_valid():before_asset_replace.call()
	if environment_scene != null:
		world.remove_child(environment_scene)
		environment_scene.queue_free()
	environment_scene = result.scene
	legacy_materials=null
	world.add_child(environment_scene)
	# Imported cameras must not take over the independently animated shot.
	disable_cameras(environment_scene)
	camera.current = true
	empty_environment = scene_bounds().size.length_squared() == 0
	editor_grid.visible = empty_environment and not sequence_instance
	assets_changed.emit()
	return ""

func prepare_legacy(path: String, data: Dictionary = {},incoming_video: Dictionary={}) -> Dictionary:
	var scene:=SceneIO.load_glb(path)
	if scene.has("error"):return scene
	var actor:=prepare_model(data,incoming_video)
	if actor.has("error"):scene.scene.free();return actor
	return {"scene":scene.scene,"model":actor.model}

func clear_assets() -> void:
	if before_asset_replace.is_valid():before_asset_replace.call()
	legacy_materials=null
	if world_runtime:world_runtime.dispose();world_runtime=null
	active_instance_id=""
	if model:
		model.root.get_parent().remove_child(model.root);model.root.queue_free();model=null
	if environment_scene:
		environment_scene.get_parent().remove_child(environment_scene);environment_scene.queue_free();environment_scene=null

func install_legacy(prepared: Dictionary) -> void:
	clear_assets()
	environment_scene=prepared.scene;world.add_child(environment_scene);disable_cameras(environment_scene)
	model=prepared.model
	if model:world.add_child(model.root);disable_cameras(model.root);model.apply(0)
	empty_environment=scene_bounds(environment_scene).size.length_squared()==0
	editor_grid.visible=empty_environment and not capturing_final and not sequence_instance;camera.current=true
	assets_changed.emit()

func environment_root() -> Node3D:
	if not world_runtime:return environment_scene
	var active: RefCounted=active_model()
	if active and active.data.kind=="environment":return active.root
	var rows: Array=world_runtime.snapshot().objects
	for i in range(rows.size()-1,-1,-1):
		if rows[i].kind=="environment":return world_runtime.instance(rows[i].id).root
	return world_runtime.root

func disable_cameras(node: Node) -> void:
	if node is Camera3D:
		node.current = false
	if node is AnimationPlayer: node.stop()
	for child in node.get_children():
		disable_cameras(child)

func evaluate(keys: Array, frame: int) -> void:
	apply_lighting()
	var value := Timeline.sample(keys, frame)
	camera.transform = Transform3D(Basis(value.rotation), value.position)
	camera.fov = value.fov
	camera.near=value.near;camera.far=value.far
	view_changed.emit()
	if world_runtime:world_runtime.evaluate(frame,false,"",video_settings)
	elif model: model.apply(frame,false,false,video_settings)

func prepare_world(document: Dictionary, duration: int,incoming_video: Dictionary={}) -> Dictionary:
	return WorldRuntime.prepare(document,duration,incoming_video if not incoming_video.is_empty() else video_settings)

func install_world(prepared: Dictionary, frame := 0) -> bool:
	if not prepared.get("runtime") is WorldRuntime:return false
	var incoming: RefCounted=prepared.runtime
	if not is_instance_valid(incoming.root) or incoming.root.get_parent()!=null:return false
	# All files/rigs were checked during preparation; one replacement, one notification.
	clear_assets()
	world_runtime=incoming;active_instance_id="";world.add_child(incoming.root)
	disable_cameras(incoming.root)
	incoming.evaluate(frame)
	empty_environment=scene_bounds(incoming.root).size.length_squared()==0
	editor_grid.visible=empty_environment and not capturing_final and not sequence_instance
	camera.current=true
	assets_changed.emit()
	return true

func world_state() -> Dictionary:
	return world_runtime.snapshot() if world_runtime else {}

func active_model() -> RefCounted:
	return world_runtime.instance(active_instance_id) if world_runtime else model

func select_instance(id: String) -> bool:
	if not world_runtime:return false
	if not id.is_empty() and not world_runtime.instances.has(id):return false
	active_instance_id=id
	return true

func prepare_model(data: Dictionary,incoming_video: Dictionary={}) -> Dictionary:
	if data.is_empty(): return {"model": null}
	var result := SceneIO.load_glb(data.source)
	if result.has("error"): return result
	var candidate := Model.new()
	candidate.root = result.scene
	candidate.base_root = candidate.root.transform
	candidate.data = data
	candidate.inventory(candidate.root)
	var timing: Dictionary=incoming_video if not incoming_video.is_empty() else video_settings
	if load("res://src/walking_animation.gd").active(data):candidate.motion_video=timing.duplicate(true)
	var error := candidate.check_bindings()
	if not error.is_empty():
		candidate.root.free()
		return {"error": error}
	error=load("res://src/walking_animation.gd").preflight_detached(candidate.root,[candidate],timing)
	if not error.is_empty():candidate.root.free();return {"error":error}
	return {"model": candidate}

func install_model(prepared: Dictionary) -> bool:
	if world_runtime:return false
	if before_asset_replace.is_valid():before_asset_replace.call()
	if model:
		world.remove_child(model.root)
		model.root.queue_free()
	model = prepared.model
	if model:
		world.add_child(model.root)
		disable_cameras(model.root)
		model.apply(0)
	camera.current = true
	assets_changed.emit()
	return true

func model_state() -> Dictionary:
	return model.data if model else {}

func scene_bounds(node: Node = environment_scene) -> AABB:
	var bounds := AABB()
	if node == null: return bounds
	if node is MeshInstance3D and node.mesh:
		bounds = node.global_transform * Model.Shape.mesh_bounds(node)
	for child in node.get_children():
		var child_bounds := scene_bounds(child)
		if child_bounds.size.length_squared() > 0:
			bounds = child_bounds if bounds.size.length_squared() == 0 else bounds.merge(child_bounds)
	return bounds

func frame_scene(node: Node = environment_scene) -> bool:
	last_framing=PoseBounds.query(node)
	if not last_framing.error.is_empty():return false
	var bounds: AABB=last_framing.bounds
	if bounds.size.length_squared() == 0: return false
	var distance := bounds.size.length() * 0.5 / sin(deg_to_rad(camera.fov * 0.5)) * 1.15
	distance=maxf(distance,camera.near*1.05+bounds.size.length()*0.5)
	camera.position = bounds.get_center() + Vector3(0.35, 0.2, 1).normalized() * distance
	camera.look_at(bounds.get_center(), Vector3.UP)
	camera.far = maxf(2000, distance * 4)
	view_changed.emit()
	return true

func view_state() -> Dictionary:
	return {"transform":camera.transform,"fov":camera.fov,"near":camera.near,"far":camera.far}

func restore_view(value: Dictionary) -> void:
	camera.transform=value.transform;camera.fov=value.fov;camera.near=value.near;camera.far=value.far
	view_changed.emit()

func _enter_tree() -> void:native_view_closing=false

func _exit_tree() -> void:
	native_view_closing=true
	if RenderingServer.frame_post_draw.is_connected(dispatch_native_frame):RenderingServer.frame_post_draw.disconnect(dispatch_native_frame)
	# Complete owner-bound waits while the renderer still exists. Cancellation
	# during destruction otherwise retains coroutine/signal-name references.
	var notification:=native_frame_notification
	var pending:=native_readbacks>0;native_readbacks=0
	if pending:notification.ready.emit()

func native_view_available() -> bool:
	return not native_view_closing and is_inside_tree() and is_instance_valid(viewport) and viewport.is_inside_tree()

func begin_native_readback() -> bool:
	# A caller owns one frame wait directly. Nesting cancelled coroutine waits
	# retains Godot FunctionState objects when both caller and renderer close.
	if not native_view_available():return false
	native_readbacks+=1;viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS
	if not RenderingServer.frame_post_draw.is_connected(dispatch_native_frame):RenderingServer.frame_post_draw.connect(dispatch_native_frame,CONNECT_ONE_SHOT)
	return true

func dispatch_native_frame() -> void:
	# Disconnect before notifying callers, so a callback may request a later frame.
	if RenderingServer.frame_post_draw.is_connected(dispatch_native_frame):RenderingServer.frame_post_draw.disconnect(dispatch_native_frame)
	# A resumed capture caller may free this renderer before emission returns.
	# Keep the RefCounted signal owner alive independently of that Node.
	var notification:=native_frame_notification
	notification.ready.emit()

func finish_native_readback(read_pixels:=true) -> Image:
	if native_readbacks<=0:return null
	native_readbacks-=1
	if not read_pixels or not native_view_available():return null
	var image:=viewport.get_texture().get_image()
	return null if image==null or image.is_empty() else image

func capture(keys: Array, layers: Array, frame: int, final := false) -> Image:
	if final and before_final_capture.is_valid():before_final_capture.call()
	last_capture_error=""
	if not native_view_available():last_capture_error="Native render view is unavailable.";return null
	evaluate(keys, frame)
	if world_runtime:world_runtime.evaluate(frame,final,"",video_settings)
	elif model: model.apply(frame, false, final,video_settings)
	if world_runtime and not world_runtime.evaluation_error.is_empty():
		last_capture_error=world_runtime.evaluation_error;return null
	var actors: Array=world_runtime.instances.values() if world_runtime else [model] if model else []
	for actor in actors:
		if actor.root.is_visible_in_tree() and not actor.evaluation_error.is_empty():
			last_capture_error="Frame %d · %s: %s" % [frame,actor.data.name,actor.evaluation_error]
			if world_runtime:world_runtime.evaluate(frame,false,"",video_settings)
			return null
	capturing_final = final
	editor_grid.visible = empty_environment and not final and not sequence_instance
	if not begin_native_readback():
		capturing_final=false;editor_grid.visible=empty_environment and not sequence_instance
		last_capture_error="Native render view is unavailable.";return null
	var notification:=native_frame_notification
	await notification.ready
	var image: Image=finish_native_readback()
	if native_view_available() and world_runtime:world_runtime.evaluate(frame,false,"",video_settings)
	capturing_final = false
	editor_grid.visible = empty_environment and not sequence_instance
	if image==null:last_capture_error="Native render view closed before this frame completed.";return null
	image.convert(Image.FORMAT_RGBA8)
	if sequence_instance:image=preload("res://src/sequence_pixels.gd").straight(image)
	if sequence_runtime:
		var nested: Image=await sequence_runtime.render(sequence_owner,frame,final)
		if nested==null:last_capture_error=sequence_runtime.last_error;return null
		image.blend_rect(nested,Rect2i(Vector2i.ZERO,viewport.size),Vector2i.ZERO)
	var overlay := Drawing.composite_result(layers, frame, image.get_width(), image.get_height())
	if overlay.has("error"):last_capture_error=overlay.error;return null
	image.blend_rect(overlay.image, Rect2i(Vector2i.ZERO, viewport.size), Vector2i.ZERO)
	return image
