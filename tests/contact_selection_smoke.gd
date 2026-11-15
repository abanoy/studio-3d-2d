extends SceneTree
const Model=preload("res://src/model.gd")
const World=preload("res://src/world_document.gd")
const Bounds=preload("res://src/pose_bounds.gd")
var app
var folder: String
var checks:=0
var failures:=0
var reference_view: SubViewport
var reference_camera: Camera3D
var reference_root: Node3D
var compatibility:=false
func _initialize() -> void:
	create_timer(180).timeout.connect(func():push_error("Contact selection watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settled() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func sync_reference_view() -> void:
	# The oracle is independently baked static geometry, viewed through the
	# current displayed projection. Setup's mask no longer has a fixed native size.
	var shown: Camera3D=app.scene_view.display_camera()
	reference_view.size=app.world_selection.viewport.size
	reference_camera.global_transform=shown.global_transform
	reference_camera.projection=shown.projection;reference_camera.keep_aspect=shown.keep_aspect
	reference_camera.fov=shown.fov;reference_camera.size=shown.size
	reference_camera.near=shown.near;reference_camera.far=shown.far
	reference_camera.h_offset=shown.h_offset;reference_camera.v_offset=shown.v_offset;reference_camera.frustum_offset=shown.frustum_offset
func job() -> void:
	while app.has_project.pid>0:await process_frame
	await settled()
func actor(id: String) -> RefCounted:return app.renderer.world_runtime.instance(id)
func same(a,b) -> bool:return JSON.parse_string(JSON.stringify(a,"",true,true))==JSON.parse_string(JSON.stringify(b,"",true,true))
func fits(points: PackedVector3Array) -> bool:
	var camera: Camera3D=app.renderer.camera
	for point in points:
		var depth: float=-camera.to_local(point).z;var pixel:=camera.unproject_position(point)
		if camera.is_position_behind(point) or depth<camera.near or depth>camera.far or pixel.x<0 or pixel.x>1920 or pixel.y<0 or pixel.y>1080:return false
	return true
func bake(rig: RefCounted) -> Dictionary:
	if is_instance_valid(reference_root):reference_root.free()
	reference_root=Node3D.new();app.renderer.world.add_child(reference_root)
	var points:=PackedVector3Array();var bounds:=AABB();var first:=true
	for mesh in rig.opacity_materials.meshes:
		# CPU baking remains the independent posed-vertex/bounds reference.
		# Raster silhouette uses original asset geometry with its own frozen pose;
		# CPU baking and GPU skinning can round a subpixel edge differently.
		var source: MeshInstance3D=mesh;var temporary: MeshInstance3D
		if mesh.get_blend_shape_count()>0:
			temporary=MeshInstance3D.new();temporary.mesh=mesh.bake_mesh_from_current_blend_shape_mix();temporary.skin=mesh.skin;temporary.transform=mesh.transform;temporary.visible=false;mesh.get_parent().add_child(temporary)
			var skeleton=mesh.get_node_or_null(mesh.skeleton)
			if skeleton is Skeleton3D:temporary.skeleton=temporary.get_path_to(skeleton);skeleton.force_update_all_bone_transforms()
			source=temporary
		var geometry: Mesh=source.bake_mesh_from_current_skeleton_pose() if source.get_skin_reference()!=null else source.mesh
		var copy:=MeshInstance3D.new();copy.mesh=mesh.mesh;copy.skin=mesh.skin;copy.layers=1<<17;reference_root.add_child(copy);copy.global_transform=mesh.global_transform;copy.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		var source_skeleton=mesh.get_node_or_null(mesh.skeleton)
		if source_skeleton is Skeleton3D:
			var frozen:=frozen_reference_skeleton(source_skeleton,reference_root)
			copy.skeleton=copy.get_path_to(frozen)
		for shape in range(mesh.get_blend_shape_count()):copy.set_blend_shape_value(shape,mesh.get_blend_shape_value(shape))
		for surface in range(geometry.get_surface_count()):
			var material:=ShaderMaterial.new();material.shader=preload("res://src/selection_id.gdshader");material.set_shader_parameter("object_color",app.world_selection.color_for(rig.data.id))
			# Native authored material lives on the imported Mesh resource; runtime
			# fade/Unshaded overrides must not enter this independent reference.
			var authored: Material=mesh.mesh.surface_get_material(surface)
			if authored is BaseMaterial3D and authored.transparency!=BaseMaterial3D.TRANSPARENCY_DISABLED:
				material.set_shader_parameter("use_alpha",true);material.set_shader_parameter("opacity",authored.albedo_color.a)
				if authored.albedo_texture:material.set_shader_parameter("alpha_texture",authored.albedo_texture)
			copy.set_surface_override_material(surface,material)
			for vertex in geometry.surface_get_arrays(surface)[Mesh.ARRAY_VERTEX]:
				var point: Vector3=mesh.global_transform*vertex;points.append(point)
				if first:bounds=AABB(point,Vector3.ZERO);first=false
				else:bounds=bounds.expand(point)
		if temporary:temporary.free()
	return {"points":points,"bounds":bounds}

func frozen_reference_skeleton(source: Skeleton3D,owner_node: Node3D) -> Skeleton3D:
	# Mesh/Skin/texture resources are immutable source inputs. Pose state belongs
	# to this separate skeleton; no selection-copy geometry or skeleton is read.
	var cache: Dictionary=owner_node.get_meta("frozen_reference_skeletons",{})
	var key:=str(source.get_instance_id())
	if cache.has(key):return cache[key]
	var frozen:=Skeleton3D.new();owner_node.add_child(frozen);frozen.global_transform=source.global_transform
	frozen.modifier_callback_mode_process=Skeleton3D.MODIFIER_CALLBACK_MODE_PROCESS_MANUAL
	for i in range(source.get_bone_count()):frozen.add_bone(source.get_bone_name(i))
	for i in range(source.get_bone_count()):
		frozen.set_bone_parent(i,source.get_bone_parent(i));frozen.set_bone_rest(i,source.get_bone_rest(i));frozen.set_bone_enabled(i,source.is_bone_enabled(i))
		frozen.set_bone_pose_position(i,source.get_bone_pose_position(i));frozen.set_bone_pose_rotation(i,source.get_bone_pose_rotation(i));frozen.set_bone_pose_scale(i,source.get_bone_pose_scale(i))
	frozen.force_update_all_bone_transforms()
	cache[key]=frozen;owner_node.set_meta("frozen_reference_skeletons",cache)
	return frozen
func neighbour(mask: PackedByteArray,index: int,width: int,height: int) -> bool:
	var x:=index%width;var y:=int(index/width)
	for dy in range(-1,2):
		for dx in range(-1,2):
			if x+dx>=0 and x+dx<width and y+dy>=0 and y+dy<height and mask[(y+dy)*width+x+dx]:return true
	return false
func compare(a: Image,b: Image) -> Dictionary:
	if a.get_size()!=b.get_size():return {"reference_pixels":0,"different_pixels":0,"outside_one_pixel":-1,"dimensions_equal":false}
	a.convert(Image.FORMAT_RGBA8);b.convert(Image.FORMAT_RGBA8);var aa:=a.get_data();var bb:=b.get_data();var count:=a.get_width()*a.get_height();var am:=PackedByteArray();var bm:=PackedByteArray();am.resize(count);bm.resize(count);var pixels:=0;var different:=0;var outside:=0
	for i in range(count):am[i]=1 if aa[i*4]+aa[i*4+1]+aa[i*4+2]>15 else 0;bm[i]=1 if bb[i*4]+bb[i*4+1]+bb[i*4+2]>15 else 0;pixels+=bm[i]
	for i in range(count):
		if am[i]==bm[i]:continue
		different+=1
		if not neighbour(bm if am[i] else am,i,a.get_width(),a.get_height()):outside+=1
	return {"reference_pixels":pixels,"different_pixels":different,"outside_one_pixel":outside}
func green_added(a: Image,b: Image) -> int:
	a.convert(Image.FORMAT_RGBA8);b.convert(Image.FORMAT_RGBA8);var aa:=a.get_data();var bb:=b.get_data();var count:=0
	for i in range(0,aa.size(),4):
		if aa[i]<95 and aa[i+1]>180 and aa[i+2]<160 and not (bb[i]<95 and bb[i+1]>180 and bb[i+2]<160):count+=1
	return count
func case_for(data: Dictionary,parent: Dictionary) -> Dictionary:
	app.new_project();var world:=World.empty();data=data.duplicate(true);data.visible=false;data.visibility_keys=[{"frame":0,"visible":true},{"frame":36,"visible":false}];world.objects=[data,parent.duplicate(true)];app.restore_world(world);app.video.visibility_fade_ms=300
	var rig:=actor(data.id);app.set_frame(1);await settled()
	# Rebuild while alpha=1/7.2: collecting temporary faded materials previously
	# made even fully opaque native surfaces disappear from the selection mask.
	app.world_selection.signature="";app.world_selection.refresh();app.world_selection.select_entity(data.id);app.world_selection.frame_selected();await settled()
	var view: Dictionary=app.renderer.view_state();var before: Dictionary=app.current_world();var shots: Array=app.keys.duplicate(true);var history: int=app.history.size();var dirty: bool=app.dirty;var metrics:=[];var baseline_mask: PackedByteArray;var first_mask: PackedByteArray;var reversed:=false;var deformed:=false
	for at in [1,12,24,44,6,12]:
		app.set_frame(at);app.renderer.restore_view(view);await settled();var actual:=bake(rig);app.world_selection._process(0)
		sync_reference_view()
		reference_view.render_target_update_mode=SubViewport.UPDATE_ONCE;await settled()
		var mask: Image=app.world_selection.viewport.get_texture().get_image();var expected: Image=reference_view.get_texture().get_image();var comparison:=compare(mask,expected)
		check(comparison.reference_pixels>100 and comparison.outside_one_pixel==0 and (compatibility or rig.evaluation_error.is_empty()),"selection silhouette matches an independent frozen source pose at frame%d: %s" % [at,data.name])
		if at==1:first_mask=mask.get_data()
		if at==12:
			if baseline_mask.is_empty():baseline_mask=mask.get_data();deformed=first_mask!=baseline_mask
			else:reversed=baseline_mask==mask.get_data()
		if at==44:
			check(not rig.root.visible and app.world_selection.outline_material.get_shader_parameter("ghost"),"hidden native model retains an actual pose-matching ghost: "+data.name)
			app.world_selection.frame_selected();var query: Dictionary=app.renderer.last_framing;var error: float=query.bounds.position.distance_to(actual.bounds.position)+query.bounds.size.distance_to(actual.bounds.size)
			check(query.error.is_empty() and error<.001 and fits(actual.points),"hidden Frame selected encloses every independent posed vertex: "+data.name)
			await settled();var green: Image=root.get_texture().get_image();app.world_selection.outline.modulate.a=0;await settled();var plain: Image=root.get_texture().get_image();app.world_selection.outline.modulate.a=1
			var added:=green_added(green,plain);check(added>20,"hidden native ghost produces actual green editor pixels: "+data.name);green.save_png(folder.path_join(data.id+"-hidden-editor.png"))
			mask.save_png(folder.path_join(data.id+"-hidden-mask.png"));expected.save_png(folder.path_join(data.id+"-source-reference-mask.png"));comparison["green_added"]=added;comparison["bound_error"]=error
		metrics.append({"frame":at,"comparison":comparison})
	check(deformed and reversed and same(app.current_world(),before) and app.keys==shots and app.history.size()==history and app.dirty==dirty,"reverse seek/hidden framing preserve deformed mask, native data, history and explicit camera keys: "+data.name)
	# The same appearance owner must work when opacity comes from an animated
	# parent and the selected item is the whole group, not the model itself.
	var inherited: Dictionary=rig.data.duplicate(true);inherited.visible=true;inherited.visibility_keys=[];parent=actor(parent.id).data.duplicate(true);parent.visible=false;parent.visibility_keys=[{"frame":0,"visible":true},{"frame":36,"visible":false}]
	app.renderer.world_runtime.restore_instances({data.id:inherited,parent.id:parent});app.set_frame(1);await settled();app.world_selection.signature="";app.world_selection.refresh();app.world_selection.select_entity(parent.id)
	var group_before: Dictionary=app.current_world();var group_metrics:=[]
	for at in [1,44]:
		app.set_frame(at);app.world_selection.frame_selected();await settled();var actual:=bake(rig);sync_reference_view();reference_view.render_target_update_mode=SubViewport.UPDATE_ONCE;await settled()
		var comparison:=compare(app.world_selection.viewport.get_texture().get_image(),reference_view.get_texture().get_image());var query: Dictionary=app.renderer.last_framing;var error: float=query.bounds.position.distance_to(actual.bounds.position)+query.bounds.size.distance_to(actual.bounds.size)
		check(comparison.reference_pixels>100 and comparison.outside_one_pixel==0 and error<.001 and fits(actual.points) and (at!=44 or not actor(parent.id).root.visible and not rig.root.is_visible_in_tree() and app.world_selection.outline_material.get_shader_parameter("ghost")),"selected group retains inherited fade/hidden native geometry and framing at frame%d: %s" % [at,data.name]);comparison["bound_error"]=error;group_metrics.append({"frame":at,"comparison":comparison})
	check(same(app.current_world(),group_before) and app.keys==shots and app.history.size()==history and app.dirty==dirty,"inherited group framing and selection preserve authored state: "+data.name)
	return {"id":data.id,"name":data.name,"bones":rig.order.size(),"samples":metrics,"group_samples":group_metrics}
func run() -> void:
	var args:=OS.get_cmdline_user_args();folder=args[0];compatibility=args.size()>2 and args[2]=="compatibility";DirAccess.make_dir_recursive_absolute(folder);app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.display_prefs_path=folder.path_join("display.cfg");app.recent_path=folder.path_join("recent.json");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	if compatibility:app.restore_world(JSON.parse_string(FileAccess.get_file_as_string(args[1])));await settled()
	else:app.has_project.open_file(args[1]);await job()
	var world: Dictionary=app.current_world();var parent: Dictionary={};var plans:=[]
	for row in world.objects:
		if row.id=="contact-group":parent=row
		elif row.kind=="model" and row.get("format") in ["studio_model_6","studio_model_7"]:plans.append(row)
	check(plans.size()==5 and not parent.is_empty(),"five actual native models and animated parent available")
	if plans.size()!=5 or parent.is_empty():app.free();quit(1);return
	reference_view=SubViewport.new();reference_view.size=app.world_selection.viewport.size;reference_view.world_3d=app.renderer.viewport.find_world_3d();reference_view.render_target_update_mode=SubViewport.UPDATE_DISABLED;root.add_child(reference_view);reference_camera=Camera3D.new();reference_camera.cull_mask=1<<17;reference_camera.environment=Environment.new();reference_camera.environment.background_mode=Environment.BG_COLOR;reference_camera.environment.background_color=Color.BLACK;reference_view.add_child(reference_camera);reference_camera.current=true;app.renderer.camera.set_cull_mask_value(18,false)
	var reports:=[]
	for plan in plans:reports.append(await case_for(plan,parent))
	if is_instance_valid(reference_root):reference_root.free()
	app.set_frame(44);var before: Dictionary=app.current_world();var hidden: Image=await app.renderer.capture(app.keys,app.layers,44,true);app.world_selection.clear();var clear: Image=await app.renderer.capture(app.keys,app.layers,44,true)
	check(hidden.get_data()==clear.get_data() and same(app.current_world(),before),"hidden selection is excluded from actual final frames without changing visibility or native contacts")
	var result:={"checks":checks,"failures":failures,"folder":folder,"contacts":not compatibility,"native_reports":reports,"audio_driver":AudioServer.get_driver_name(),"scope":"Native geometric selection; hardware audio is checked separately"};var file:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close();reference_view.free();app.free();await settled();print("CONTACT_SELECTION "+JSON.stringify(result));quit(0 if failures==0 else 1)
