extends RefCounted
# Owns temporary GI flags on live instances, never imported resources/model data.
var renderer_ref: WeakRef
var originals: Array=[]
var dirty:=true
var active:=false
var reset_draw:=-1
var started_draw:=0
var stamp:=""
var contributor_count:=0
var receiver_count:=0
var status:="Indirect light is off."

static func supported() -> bool:
	return DisplayServer.get_name()=="headless" or RenderingServer.get_current_rendering_method()=="forward_plus"

func setup(renderer: Node) -> void:
	renderer_ref=weakref(renderer)
	renderer.assets_changed.connect(invalidate)

func invalidate() -> void:
	dirty=true
	if active:reset_draw=Engine.get_frames_drawn()

func rebuild() -> void:
	dirty=true;reset_draw=Engine.get_frames_drawn()

func restore() -> void:
	for entry in originals:
		var mesh=entry.node.get_ref()
		if is_instance_valid(mesh):mesh.gi_mode=entry.mode
	originals.clear();contributor_count=0;receiver_count=0

func collect(node: Node,mode: int,desired: Dictionary) -> void:
	if node is MeshInstance3D and node.mesh:desired[node.get_instance_id()]={"node":node,"mode":mode}
	for child in node.get_children():collect(child,mode,desired)

func inventory(renderer: Node) -> void:
	restore()
	var desired:={}
	# Unknown helpers (grid, outlines, picking copies) do not contribute to GI.
	collect(renderer.world,GeometryInstance3D.GI_MODE_DISABLED,desired)
	if renderer.world_runtime:
		for actor in renderer.world_runtime.instances.values():
			if not actor.opacity_materials:continue
			var mode:=GeometryInstance3D.GI_MODE_STATIC if actor.data.kind=="environment" else GeometryInstance3D.GI_MODE_DYNAMIC
			for mesh in actor.opacity_materials.meshes:
				if is_instance_valid(mesh):desired[mesh.get_instance_id()]={"node":mesh,"mode":mode}
	else:
		if renderer.environment_scene:collect(renderer.environment_scene,GeometryInstance3D.GI_MODE_STATIC,desired)
		if renderer.model:collect(renderer.model.root,GeometryInstance3D.GI_MODE_DYNAMIC,desired)
	for entry in desired.values():
		var mesh: MeshInstance3D=entry.node
		originals.append({"node":weakref(mesh),"mode":mesh.gi_mode})
		mesh.gi_mode=entry.mode
		if entry.mode==GeometryInstance3D.GI_MODE_STATIC:contributor_count+=1
		elif entry.mode==GeometryInstance3D.GI_MODE_DYNAMIC:receiver_count+=1
	dirty=false

func sync(video: Dictionary,environment: Environment) -> void:
	var settings: Dictionary=video.get("scene_lighting",{}).get("indirect",{})
	var desired: bool=settings.get("enabled",false) and video.get("lighting_mode","studio")=="lit"
	if not desired or not supported():
		environment.sdfgi_enabled=false
		if active or not originals.is_empty():restore()
		active=false;dirty=true;stamp="";reset_draw=-1
		status="Indirect light requires Lit and Forward+ (python run.py --forward-plus)." if desired else "Indirect light is off."
		return
	var renderer=renderer_ref.get_ref() if renderer_ref else null
	if not is_instance_valid(renderer):return
	if dirty:inventory(renderer)
	if Engine.get_frames_drawn()<=reset_draw:
		environment.sdfgi_enabled=false;active=false;stamp="";status="Rebuilding indirect lighting from the current environment…";return
	var signature:=JSON.stringify(settings)
	if not active or signature!=stamp:
		environment.sdfgi_cascades=4
		environment.sdfgi_min_cell_size=settings.cell_size
		environment.sdfgi_energy=settings.energy
		environment.sdfgi_bounce_feedback=0.
		environment.sdfgi_use_occlusion=true
		environment.sdfgi_read_sky_light=false
		# Headless checks cover transactions/flags, not an unavailable GPU backend.
		environment.sdfgi_enabled=DisplayServer.get_name()!="headless"
		started_draw=Engine.get_frames_drawn();stamp=signature;active=true
	status="SDFGI warming up…" if Engine.get_frames_drawn()-started_draw<int(settings.settle_frames) else "SDFGI: %d environment meshes contribute; %d model meshes receive. Rebuild after moving environment geometry."%[contributor_count,receiver_count]

func capture_frames(video: Dictionary) -> int:
	var settings: Dictionary=video.get("scene_lighting",{}).get("indirect",{})
	if not supported() or video.get("lighting_mode","studio")!="lit" or not settings.get("enabled",false):return 0
	return int(settings.get("settle_frames",32))
