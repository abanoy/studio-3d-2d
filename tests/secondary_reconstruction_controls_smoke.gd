extends SceneTree
const Motion=preload("res://src/generated_secondary_motion.gd")
const Timeline=preload("res://src/timeline.gd")
const StudioTheme=preload("res://src/studio_theme.gd")
const Bounds=preload("res://src/pose_bounds.gd")
const Shape=preload("res://src/source_shape.gd")
var app
var checks:=0
var failures:=0
func _initialize() -> void:call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settle() -> void:
	for i in range(5):await process_frame
	await RenderingServer.frame_post_draw
func ready(helper: Node) -> void:
	while helper.pid>0:await process_frame
	await settle()
func wait_for(predicate: Callable,seconds:=90.) -> bool:
	var limit:=Time.get_ticks_msec()+int(seconds*1000)
	while not predicate.call() and Time.get_ticks_msec()<limit:await process_frame
	return predicate.call()
func geometry(actor: RefCounted) -> Dictionary:
	var result:={};var context:={"error":"","palettes":{},"updated":{}}
	for item in actor.root.find_children("*","MeshInstance3D",true,false):
		var mesh: MeshInstance3D=item
		if mesh.mesh==null or mesh.skin==null:continue
		var palette: Array=Bounds.palette(mesh,context)
		if not context.error.is_empty():return {}
		for s in range(mesh.mesh.get_surface_count()):
			var arrays: Array=mesh.mesh.surface_get_arrays(s);var vertices: PackedVector3Array=Shape.vertices(mesh,s,arrays[Mesh.ARRAY_VERTEX]);var bones: PackedInt32Array=arrays[Mesh.ARRAY_BONES];var weights: PackedFloat32Array=arrays[Mesh.ARRAY_WEIGHTS]
			var points:=PackedVector3Array();var stride: int=bones.size()/vertices.size()
			for i in range(vertices.size()):
				var p:=Vector3.ZERO
				for j in range(stride):p+=(palette[bones[i*stride+j]]*vertices[i])*weights[i*stride+j]
				points.append(mesh.global_transform*p)
			var key:=str(mesh.name)+":"+str(s)
			if result.has(key):return {}
			result[key]=points
	return result
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0];var source: String=args[1];var source_sha:=FileAccess.get_sha256(source)
	root.size=Vector2i(1600,1000)
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recent.json");app.helper_preview_runtime_path="C:/Program Files/Python313/python.exe";app.helper_preview_work_root=folder.path_join("preview-work");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache");app.set_advanced("--advanced" in args)
	check(app.pose_editor.add_model(source).is_empty(),"ordinary Add model opens the original protected character")
	check(app.advanced_mode==("--advanced" in args) and StudioTheme.is_neon(),"actual requested workspace and Neon theme are active")
	var actor: RefCounted=app.renderer.active_model();var id: String=actor.data.id
	var head:=""
	for b in actor.order:
		if str(actor.bones[b].name).to_lower().ends_with("head1"):head=b;break
	check(not head.is_empty(),"actual native Head joint is found for nonzero authored FK preservation")
	if head.is_empty():await app.quit_studio();quit(1);return
	actor.data.pose[head]={"position":[0,0,0],"rotation_xyzw":[0,sin(.1),0,cos(.1)]}
	actor.data.pose_keys=[{"frame":0,"pose":actor.data.pose.duplicate(true),"transform":{"position":actor.data.position.duplicate(),"rotation_xyzw":actor.data.rotation_xyzw.duplicate(),"scale":actor.data.scale},"interpolation":"linear"}];app.pose_editor.apply_frame();app.changed()
	app.pose_editor.frame_model();app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,app.renderer.camera.fov)];await settle();var original: Dictionary=actor.data.duplicate(true);var history: int=app.history.size();var original_geometry:=geometry(actor)
	var before: Image=await app.renderer.capture(app.keys,app.layers,0,true);before.save_png(folder.path_join("before.png"))
	var helper: Node=app.physics_editor.helper_editor;helper.open(true);await ready(helper);var chosen:=-1
	for i in range(helper.assessment.regions.size()):
		var row: Dictionary=helper.assessment.regions[i]
		if int(row.node)==131 and int(row.primitive)==1 and int(row.component)==2:chosen=i;break
	check(chosen>=0,"ordinary review identifies the complete requested back-hair component")
	if chosen<0:await app.quit_studio();quit(1);return
	helper.select_part(chosen);await ready(helper)
	check(not helper.preview.can_apply and not helper.reconstruct_toggle.button_pressed,"mixed native weights keep the original refusal until explicit reconstruction")
	helper.request.segments=4;helper.reconstruct_toggle.button_pressed=true;await ready(helper)
	check(helper.preview.can_apply and helper.preview.mode=="reconstructed_weights" and helper.reconstruct_toggle.visible and helper.reconstruct_toggle.button_pressed,"explicit visible opt-in prepares owned multi-anchor guides")
	check(int(helper.preview.region.vertices)==1292 and helper.preview.added_chains==13 and app.canvas.review_lines.size()>0 and helper.info.text.contains("1292"),"review highlights all1292 vertices and discloses13 guide groups")
	helper.include_toggle.button_pressed=true;await ready(helper)
	check(helper.included.size()==1 and helper.include_toggle.button_pressed and not helper.apply_button.disabled,"reviewed section can be included without applying it")
	helper.try_wind.button_pressed=true
	var running: bool=await wait_for(func():return helper.pending_preview.phase=="running" or helper.pending_preview.phase=="failed")
	var player: Node=helper.pending_preview.player
	check(running and helper.pending_preview.phase=="running" and player.simulation!=null and player.simulation.runner.chains.size()==13,"Try a local blow runs all13 reconstructed guide groups before Apply")
	helper.try_wind.button_pressed=false;await settle()
	check(actor.data==original and app.history.size()==history and actor.root.visible,"temporary reconstruction preview restores the original without authored edits")
	helper.window.get_texture().get_image().save_png(folder.path_join("review.png"))
	helper.apply_button.pressed.emit();await ready(helper);actor=app.renderer.world_runtime.instance(id)
	var derived: Dictionary=actor.data.duplicate(true);var definition: Dictionary=actor.root.get_meta("has_secondary_rig",{})
	check(not is_instance_valid(helper.window) and definition.get("chains",[]).size()==13 and app.history.size()==history+1,"Apply adopts the new owned candidate as one reversible edit")
	check(actor.data.pose==original.pose and actor.data.pose_keys==original.pose_keys and actor.data.metadata.generated_helpers.mode=="reconstructed_weights","original native pose and keys survive owned reconstruction")
	var after: Image=await app.renderer.capture(app.keys,app.layers,0,true);after.save_png(folder.path_join("after-rest.png"))
	var a:=before.get_data();var b:=after.get_data();var changed:=0
	var max_channel:=0;var total_channel:=0;var changed_pixels: Dictionary={}
	if a.size()==b.size():
		for i in range(a.size()):
			if a[i]!=b[i]:changed+=1;max_channel=maxi(max_channel,absi(a[i]-b[i]));total_channel+=absi(a[i]-b[i]);changed_pixels[i/4]=true
	var after_geometry:=geometry(actor);var topology_held: bool=not original_geometry.is_empty() and original_geometry.size()==after_geometry.size();var maximum_vertex_error:=0.;var sampled_vertices:=0
	for key in original_geometry:
		if not after_geometry.has(key) or after_geometry[key].size()!=original_geometry[key].size():topology_held=false;continue
		for i in range(original_geometry[key].size()):maximum_vertex_error=maxf(maximum_vertex_error,original_geometry[key][i].distance_to(after_geometry[key][i]));sampled_vertices+=1
	check(topology_held,"actual imported surface topology and every posed source vertex remain addressable")
	check(a.size()==b.size() and changed==0,"owned guide rest exactly preserves the posed character's rendered surfaces")
	app.undo();await settle();check(app.renderer.world_runtime.instance(id).data==original,"one Undo restores the exact original asset and native edits")
	app.redo();await settle();actor=app.renderer.world_runtime.instance(id);check(actor.data==derived,"one Redo restores the reviewed owned candidate")
	app.world_selection.select_entity(id,false);await settle();app.physics_editor.generated_motion_editor.sync();app.physics_editor.generated_motion_editor.change(1);await settle();actor=app.renderer.world_runtime.instance(id)
	var frames: Dictionary={}
	for bone in actor.order:frames[bone]=actor.bone_transform(bone)
	app.physics_editor.hair_toggle.button_pressed=true;var live: bool=await wait_for(func():return app.physics_editor.active(id) or not app.physics_editor.pending.has(id),30.)
	check(live and app.physics_editor.active(id) and Motion.setting(actor.data).mode=="natural","Natural gravity starts through ordinary Hair and clothes controls")
	for i in range(120):await physics_frame
	var live_image: Image=await app.renderer.capture(app.keys,app.layers,0,false);live_image.save_png(folder.path_join("natural.png"))
	app.physics_editor.hair_toggle.button_pressed=false;await settle();var maximum:=0.
	for bone in frames:
		var now: Transform3D=actor.bone_transform(bone);var old: Transform3D=frames[bone];maximum=maxf(maximum,now.origin.distance_to(old.origin))
		for axis in range(3):maximum=maxf(maximum,now.basis[axis].distance_to(old.basis[axis]))
	check(not app.physics_editor.active(id) and maximum<.000001,"Hair and clothes Off restores every authored bone transform")
	check(FileAccess.get_sha256(source)==source_sha and app.renderer.native_readbacks==0,"original source stays unchanged and rendering readbacks are balanced")
	print("SECONDARY_RECONSTRUCTION_CONTROLS "+JSON.stringify({"checks":checks,"failures":failures,"user_profile":OS.get_user_data_dir(),"advanced":app.advanced_mode,"rest_pixel_bytes_changed":changed,"rest_pixels_changed":changed_pixels.size(),"maximum_channel_difference":max_channel,"total_channel_difference":total_channel,"sampled_posed_vertices":sampled_vertices,"maximum_posed_vertex_difference":maximum_vertex_error,"maximum_off_transform_error":maximum,"captures":4}));await app.quit_studio();quit(0 if failures==0 else 1)
