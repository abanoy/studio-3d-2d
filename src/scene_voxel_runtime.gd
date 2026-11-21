extends RefCounted
# One bounded probe. Persist its editable recipe, regenerate bake data in memory.
var renderer_ref: WeakRef
var probe: VoxelGI
var dirty:=true
var baking:=false
var enabled:=false
var generation:=0
var stamp:=""
var settings: Dictionary={}
var error:=""
var status:="Room VoxelGI is off."
var bake_count:=0
var bake_ms:=0

func invalidate() -> void:
	dirty=true;generation+=1;baking=false

func disable() -> void:
	enabled=false
	if is_instance_valid(probe):probe.hide()
	if baking:invalidate()

func sync(renderer: Node,config: Dictionary) -> void:
	renderer_ref=weakref(renderer);enabled=true;settings=config.duplicate(true)
	var room: Dictionary=config.get("voxel",{"position":[0,2,0],"size":[10,6,10],"subdiv":0})
	var signature:=JSON.stringify(room)
	if not is_instance_valid(probe):
		probe=VoxelGI.new();probe.name="AuthoredRoomVoxelGI";renderer.world.add_child(probe);dirty=true
	if signature!=stamp:
		probe.position=Vector3(room.position[0],room.position[1],room.position[2])
		probe.size=Vector3(room.size[0],room.size[1],room.size[2]);probe.subdiv=int(room.subdiv)
		stamp=signature;invalidate()
	probe.visible=not dirty and probe.data!=null
	if probe.data:probe.data.energy=config.energy
	if dirty and not baking:
		baking=true;error="";status="Baking room VoxelGI… This can pause Studio for several seconds."
		# Imported nodes, transforms and materials must be ready before bake().
		call_deferred("bake_room",generation)

func bake_probe(from_node: Node) -> void:
	# One native boundary, also used by the deterministic failed-rebake control.
	probe.bake(from_node)

func bake_room(ticket: int) -> void:
	var renderer=renderer_ref.get_ref() if renderer_ref else null
	if ticket!=generation or not enabled:return
	if not is_instance_valid(renderer) or not renderer.is_inside_tree() or not is_instance_valid(probe):baking=false;return
	var bounds:=AABB(probe.position-probe.size*.5,probe.size)
	var contributors:=0
	for entry in renderer.scene_lighting.indirect.originals:
		var mesh=entry.node.get_ref()
		if is_instance_valid(mesh) and mesh.gi_mode==GeometryInstance3D.GI_MODE_STATIC and mesh.is_visible_in_tree() and bounds.intersects(mesh.global_transform*mesh.get_aabb()):contributors+=1
	if contributors==0:
		error="No static environment meshes inside the room. Import an environment, fit the room bounds, then Rebuild."
	else:
		var start:=Time.get_ticks_msec()
		# Native bake() returns void and can leave previous data intact on failure.
		# Only data produced by this attempt may qualify as a successful rebuild.
		probe.data=null
		bake_probe(renderer.world)
		bake_ms=Time.get_ticks_msec()-start
		if probe.data==null:error="VoxelGI bake produced no data. Check room bounds and supported environment materials, then Rebuild."
		else:
			probe.data.interior=true;probe.data.use_two_bounces=false;probe.data.energy=settings.energy
			bake_count+=1
	baking=false;dirty=false;probe.visible=error.is_empty() and enabled
	status=error if not error.is_empty() else "Room VoxelGI ready (%d environment meshes; bake %.2f s). Models use dynamic GI. Rebuild after changing static geometry; reopening regenerates the bake."%[contributors,bake_ms/1000.]
