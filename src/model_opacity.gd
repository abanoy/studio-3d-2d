extends RefCounted
# Compatibility/OpenGL ignores GeometryInstance3D.transparency. Only temporary,
# instance-local copies compose fades and Unshaded; authored materials stay intact.
var meshes: Array=[]
var active:=false
var last_alpha:=-1.0
var unshaded:=false
var controlled:=false

func inventory(node: Node) -> void:
	if node is MeshInstance3D and node.mesh:meshes.append(node)
	for child in node.get_children():inventory(child)

var originals: Array=[]
var copies: Array=[]

func authored_material(mesh: MeshInstance3D,surface: int) -> Material:
	# Selection needs native cutouts, independent of temporary scene fades and
	# lighting copies. An absent surface override inherits the Mesh material.
	for entry in originals:
		if entry.mesh!=mesh:continue
		if entry.surface<0:return entry.material
		if entry.surface==surface:return entry.material if entry.material else mesh.mesh.surface_get_material(surface)
	return mesh.get_active_material(surface)

func set_alpha(alpha: float) -> void:
	set_appearance(alpha,unshaded)

func set_appearance(alpha: float,flat: bool) -> void:
	if alpha==last_alpha and flat==unshaded:return
	var fading:=alpha>0 and alpha<1
	if flat!=unshaded or fading!=active:
		for entry in originals:
			if not is_instance_valid(entry.mesh):continue
			if entry.surface<0:entry.mesh.material_override=entry.material
			else:entry.mesh.set_surface_override_material(entry.surface,entry.material)
		originals.clear();copies.clear();controlled=false
	last_alpha=alpha;unshaded=flat;active=fading
	if not fading and not flat:return
	if not controlled:
		for mesh in meshes:
			if not is_instance_valid(mesh):continue
			if mesh.material_override:
				duplicate_material(mesh,-1,mesh.material_override)
			else:
				for surface in range(mesh.mesh.get_surface_count()):duplicate_material(mesh,surface,mesh.get_active_material(surface))
		controlled=true
	for entry in copies:
		var color: Color=entry.color
		if fading:
			if entry.opaque:color.a=1
			color.a*=alpha
		entry.material.albedo_color=color

func duplicate_material(mesh: MeshInstance3D, surface: int, source: Material) -> void:
	# Runtime GLB imports supply BaseMaterial3D. Do not silently replace arbitrary shaders.
	if source and not source is BaseMaterial3D:return
	var material: BaseMaterial3D=source.duplicate() if source else StandardMaterial3D.new()
	var original: Material=mesh.material_override if surface<0 else mesh.get_surface_override_material(surface)
	originals.append({"mesh":mesh,"surface":surface,"material":original})
	var color:=material.albedo_color
	copies.append({"material":material,"color":color,"opaque":material.transparency==BaseMaterial3D.TRANSPARENCY_DISABLED})
	if active:material.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA
	if unshaded:
		material.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
		material.emission_enabled=false
	if surface<0:mesh.material_override=material
	else:mesh.set_surface_override_material(surface,material)
