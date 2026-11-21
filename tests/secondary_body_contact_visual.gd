extends "res://tests/secondary_body_contact_smoke.gd"
const SkinBinding=preload("res://tests/miku_contact_support/miku_skin_binding.gd")
# Root-run private GPU check: ordinary saved Open and Hair & clothes On/Off.
# Args: owned data, protected stuff2.has, original collider input, alignment input.
var skin_cache: Dictionary={}
func skin_clearance(actor: RefCounted,runner: RefCounted) -> Dictionary:
	var actual: Dictionary=SkinBinding.points(actor,skin_cache)
	if actual.has("error"):return actual
	var minimum:=INF;var penetrating:=0
	for chain in runner.chains:
		for collider in chain.colliders:
			var c: Dictionary=collider.definition;var a: Transform3D=Definition.binding_transform(actor,c.binding);var b: Vector3=Definition.binding_transform(actor,c.tail_binding).origin
			var radius: float=c.radius*a.basis.get_scale().x
			for vertex in actual.vertices:
				var gap: float=Fit.point_segment(vertex,a.origin,b)-radius;minimum=minf(minimum,gap)
				if gap<-.00005:penetrating+=1
	return {"vertices":actual.vertices.size(),"minimum_skin_clearance":minimum,"penetrating_skin_vertex_pairs":penetrating,"maximum_palette_disagreement":actual.maximum_palette_disagreement}
func shot(folder: String,name: String) -> bool:
	if not app.renderer.begin_native_readback():return false
	var notification: RefCounted=app.renderer.native_frame_notification
	await notification.ready
	var image: Image=app.renderer.finish_native_readback()
	return image!=null and image.get_size()==Vector2i(1920,1080) and image.save_png(folder.path_join(name+".png"))==OK and app.renderer.native_readbacks==0
func run() -> void:
	var args:=OS.get_cmdline_user_args()
	if args.size()!=4 or DisplayServer.get_name()=="headless" or FileAccess.get_sha256(args[1])!=PROJECT_SHA:push_error("Use private graphical output, protected Miku case and original skin calibration inputs");quit(2);return
	if FileAccess.get_sha256(args[2])!="e3ada9ac313b21919c3a0d35617d8ec1dbd8cdf6abfe5dec0d8af4f7dd699971" or FileAccess.get_sha256(args[3])!=SkinBinding.ALIGNMENT_SHA:push_error("Original private calibration input differs");quit(2);return
	var folder: String=args[0];var archive: String=args[1]
	root.size=Vector2i(1600,1000);root.gui_embed_subwindows=true
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recent.json");root.add_child(app);await settle()
	app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache");app.has_project.open_file(archive)
	while app.has_project.pid>0:await process_frame
	await settle()
	var actor: RefCounted
	for value in app.renderer.world_runtime.instances.values():
		if value.data.sha256==MODEL_SHA:actor=value
	check(app.has_project.path==archive and actor!=null,"ordinary Open installs protected Miku in the saved multi-model scene")
	if actor==null:await app.quit_studio();quit(1);return
	app.world_selection.select_entity(actor.data.id,false);app.mode.select(2);app.change_mode(2);app.set_frame(0);await settle()
	var definition: Dictionary=actor.root.get_meta("has_secondary_rig");var before: PackedByteArray=var_to_bytes(actor.data);var settings: PackedByteArray=var_to_bytes(definition);var world: PackedByteArray=var_to_bytes(app.current_world());var keys: PackedByteArray=var_to_bytes(app.keys);var history: int=app.history.size()
	check(definition.source_family=="HAS" and definition.colliders.is_empty(),"protected generated rig retains original zero-collider declarations")
	var private_raw: PackedByteArray=FileAccess.get_file_as_bytes(args[2]);var alignment: PackedByteArray=FileAccess.get_file_as_bytes(args[3])
	var input: Dictionary=JSON.parse_string(private_raw.get_string_from_utf8())
	var prepared: Dictionary=SkinBinding.prepare(actor,input,alignment)
	check(not prepared.has("error") and prepared.cache.rows.size()==13111 and prepared.cache.hair.size()==989,"original source inverse binds and actual imported hair surface calibrate")
	if prepared.has("error"):push_error(str(prepared.error));await app.quit_studio();quit(1);return
	skin_cache=prepared.cache
	var original_view: Dictionary=app.renderer.view_state();var bounds: AABB=app.renderer.PoseBounds.query(actor.root).bounds;var center: Vector3=bounds.get_center();var extent: float=bounds.size.length()
	app.renderer.camera.global_position=center+actor.root.global_basis.z.normalized()*extent;app.renderer.camera.look_at(center,Vector3.UP)
	check(await shot(folder,"before"),"private original-pose image captures with balanced native readback")
	await app.physics_editor.enable_hair(actor)
	var live: RefCounted=app.physics_editor.simulations.get(actor.data.id)
	check(live!=null and live.runner.chains[0].colliders.size()==4 and app.physics_editor.hair_toggle.button_pressed,"ordinary Hair & clothes On includes four generated arm colliders")
	if live==null:await app.quit_studio();quit(1);return
	var active_minimum:=INF;var skin_minimum:=INF;var skin_pairs:=0;var palette_maximum:=0.
	while live.running and live.age<4.:
		await process_frame
		if live.age<=0:continue
		var measure: Dictionary=clearance(actor,live.runner);active_minimum=minf(active_minimum,measure.segment_clearance)
		var surface: Dictionary=skin_clearance(actor,live.runner)
		if surface.has("error"):push_error(str(surface.error));failures+=1;break
		skin_minimum=minf(skin_minimum,surface.minimum_skin_clearance);skin_pairs+=surface.penetrating_skin_vertex_pairs;palette_maximum=maxf(palette_maximum,surface.maximum_palette_disagreement)
	check(live.running and live.age>=4.,"ordinary live physics advances saved fan and hair for four seconds")
	check(is_finite(active_minimum) and active_minimum>=-.00005,"visible-frame samples meet the existing arm capsule clearance tolerance")
	check(is_finite(skin_minimum) and palette_maximum<=SkinBinding.CALIBRATION_TOLERANCE,"actual989-vertex skin surface remains independently measurable against original calibrated palettes")
	check(live.latest!=live.initial_pose,"saved fan changes the live hair pose")
	var processing: bool=app.physics_editor.is_physics_processing();var captured_age: float=live.age;var captured_pose: PackedByteArray=var_to_bytes(live.latest)
	app.physics_editor.set_physics_process(false)
	for view in [{"name":"after_front","axis":actor.root.global_basis.z},{"name":"after_right","axis":actor.root.global_basis.x},{"name":"after_back","axis":-actor.root.global_basis.z}]:
		app.renderer.camera.global_position=center+view.axis.normalized()*extent;app.renderer.camera.look_at(center,Vector3.UP)
		check(await shot(folder,view.name) and live.age==captured_age and var_to_bytes(live.latest)==captured_pose,"private same-pose live hair view captures with balanced readback: "+view.name)
	check(var_to_bytes(app.current_world())==world and var_to_bytes(app.keys)==keys and app.history.size()==history,"live hair and temporary view changes do not author scene shot keys or Undo")
	app.physics_editor.disable_hair(actor.data.id);app.physics_editor.set_physics_process(processing);await settle();app.renderer.restore_view(original_view)
	check(actor.live_pose==null and var_to_bytes(actor.data)==before and var_to_bytes(actor.root.get_meta("has_secondary_rig"))==settings,"ordinary Hair & clothes Off restores original authored pose and settings")
	check(FileAccess.get_sha256(archive)==PROJECT_SHA and FileAccess.get_sha256(actor.data.source)==MODEL_SHA,"original project and restored managed Miku GLB remain unchanged")
	print("SECONDARY_BODY_CONTACT_VISUAL "+JSON.stringify({"checks":checks,"failures":failures,"user_profile":OS.get_user_data_dir(),"active_minimum_segment_clearance":active_minimum,"actual_skin_vertices":989,"minimum_skin_clearance":skin_minimum,"penetrating_skin_vertex_pairs":skin_pairs,"maximum_palette_disagreement":palette_maximum,"skin_surface_capsule_clear":skin_pairs==0,"visual_skin_contact_review_required":true,"source_arrays_published":false,"readbacks_balanced":app.renderer.native_readbacks==0}));await app.quit_studio();quit(0 if failures==0 else 1)
