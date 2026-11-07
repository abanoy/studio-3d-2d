extends SceneTree
const Model=preload("res://src/model.gd")
const Timeline=preload("res://src/timeline.gd")
const Drawing=preload("res://src/drawing.gd")
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(150).timeout.connect(func():push_error("Source shape watchdog");quit(2));call_deferred("run")
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func settled() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func wait_job(job) -> void:
	while job.pid>0:await process_frame
	await settled()
func close_pixels(a: Image,b: Image) -> bool:
	var aa:=a.get_data();var bb:=b.get_data();var changed:=0;var total:=0
	for i in range(aa.size()):
		if aa[i]!=bb[i]:changed+=1;total+=absi(int(aa[i])-int(bb[i]))
	return changed<=384 and float(total)/aa.size()<.002
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0]
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled()
	app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	var source:=folder.path_join("shape.glb")
	app.append_object(Model.definition(source),"model");var actor: RefCounted=app.renderer.active_model();var id: String=actor.data.id
	check(not Model.Shape.enabled(actor.data) and Model.Shape.snapshot(actor.root).is_empty(),"old records retain their neutral shape despite declared defaults")
	app.pose_editor.frame_model();app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,55)]
	var neutral: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	var history: int=app.history.size();var original_keys: Array=actor.data.pose_keys.duplicate(true);var cameras: Array=app.keys.duplicate(true)
	app.set_advanced(true);check(app.pose_editor.source_shape.visible and not app.pose_editor.source_shape.button_pressed,"Advanced exposes the saved compatibility choice")
	app.pose_editor.source_shape.button_pressed=true;await settled()
	check(Model.Shape.enabled(actor.data) and app.history.size()==history+1 and actor.data.pose_keys==original_keys and app.keys==cameras,"shape change is one Undo and creates no pose or camera key")
	check(Model.Shape.snapshot(actor.root)=={"3":[float(.6),float(.2)]} or absf(float(Model.Shape.snapshot(actor.root)["3"][0])-.6)<.000001,"node weights override mesh defaults in the actual rendered instance")
	var shaped: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	check(not neutral.get_data()==shaped.get_data(),"declared shape visibly changes the rendered model")
	var source_bounds: AABB=Model.Shape.mesh_bounds(actor.root.get_meta(Model.Shape.META).rows[0].mesh)
	var bounds_ok:=true
	for v in JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("positions.json"))):bounds_ok=bounds_ok and source_bounds.has_point(Vector3(v[0],v[1],v[2]))
	check(bounds_ok,"framing and placement bounds include evaluated shape positions")
	var source_mesh: MeshInstance3D=actor.root.get_meta(Model.Shape.META).rows[0].mesh
	var effective:=Model.Shape.vertices(source_mesh,1,source_mesh.mesh.surface_get_arrays(1)[Mesh.ARRAY_VERTEX])
	var cache_error:=0.0;var expected_shape: Array=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("positions.json")))
	for i in range(effective.size()):cache_error=maxf(cache_error,effective[i].distance_to(Vector3(expected_shape[i][0],expected_shape[i][1],expected_shape[i][2])))
	check(cache_error<.00001,"shared geometry queries use the visible imported shape")
	app.undo();await settled();check((await app.renderer.capture(app.keys,app.layers,0,true)).get_data()==neutral.get_data(),"shape Undo restores exact neutral pixels")
	app.redo();await settled();check((await app.renderer.capture(app.keys,app.layers,0,true)).get_data()==shaped.get_data(),"shape Redo restores exact imported pixels")
	app.set_advanced(false);await settled();check(not app.pose_editor.source_shape.visible and Model.Shape.enabled(actor.data),"Simple mode keeps imported shape active")
	var invalid: Dictionary=actor.data.duplicate(true);invalid.metadata.source_shape.enabled="yes"
	check(not app.pose_editor.restore_state(invalid).is_empty() and Model.Shape.enabled(actor.data),"malformed saved shape setting refuses without changing appearance")
	# Real helper window/worker now snapshots current morph weights.
	var helper=app.physics_editor.helper_editor;helper.open();await wait_job(helper)
	check(helper.assessment.skipped.is_empty() and helper.request.has("morph_weights"),"ordinary review worker receives actual nonzero morph snapshot")
	var selected:=-1
	for i in range(helper.assessment.regions.size()):
		var row: Dictionary=helper.assessment.regions[i]
		if int(row.node)==3 and int(row.primitive)==1 and int(row.component)==0:selected=i
	check(selected>=0,"shaped strand keeps its original component identity")
	if selected<0:helper.close();app.free();quit(1);return
	helper.select_part(selected);await wait_job(helper);helper.draw_preview()
	var bindings: Dictionary=actor.root.get_meta("has_source_bones");var maximum:=0.0
	var expected: Array=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("positions.json")))
	for i in range(helper.preview.source_vertices.size()):
		var p:=Vector3.ZERO
		for influence in helper.preview.vertices[i]:p+=(actor.bone_transform(bindings[int(influence[0])])*Vector3(influence[1],influence[2],influence[3]))*float(influence[4])
		var v: Array=expected[int(helper.preview.source_vertices[i])];maximum=maxf(maximum,p.distance_to(Vector3(v[0],v[1],v[2])))
	check(maximum<.00001 and not helper.projected_vertices.is_empty(),"visible review coordinates follow morphed skin and current skeleton")
	var bones: Array=actor.order.duplicate();helper.apply();await wait_job(helper);actor=app.renderer.world_runtime.instance(id)
	check(actor.order.size()==bones.size()+4 and Model.Shape.enabled(actor.data),"ordinary Apply adds weighted joints while keeping the imported shape")
	var after: Image=await app.renderer.capture(app.keys,app.layers,0,true);check(close_pixels(shaped,after),"derived revision keeps the actual shaped appearance within existing rebuild bound")
	Drawing.insert(app.layers[1],0,48,Drawing.blank(1920,1080));Drawing.edit_image(Drawing.cel_at(app.layers[1],0)).image.set_pixel(80,80,Color.CYAN)
	var paint: PackedByteArray=Drawing.image(Drawing.cel_at(app.layers[1],0)).get_data();var project:=folder.path_join("shaped.has")
	app.has_project.save_file(project,"packed");await wait_job(app.has_project);app.new_project();app.has_project.open_file(project);await wait_job(app.has_project)
	actor=app.renderer.world_runtime.instance(id)
	check(actor!=null and Model.Shape.enabled(actor.data) and actor.order.size()==bones.size()+4 and Drawing.image(Drawing.cel_at(app.layers[1],0)).get_data()==paint,"packed HAS reopens shape, weighted rig and independent drawing")
	var reopened: Image=await app.renderer.capture(app.keys,app.layers,0,true);reopened.save_png(folder.path_join("reopened.png"))
	var export_error: String=await app.export_movie(folder)
	var movie: String=app.last_export_folder.path_join("movie.mp4")
	check(export_error.is_empty() and FileAccess.file_exists(movie) and Image.load_from_file(app.last_export_folder.path_join("frame_000001.png")).get_data()==reopened.get_data(),"shaped model and independent overlay export with exact reopened preview pixels")
	for entry in [{"file":"mesh-default.glb","node":3,"values":[.75,-.3]}, {"file":"shared.glb","node":5,"values":[.3,.9]}, {"file":"root.glb","node":0,"values":[.2,.4]}]:
		app.new_project();var error: String=app.pose_editor.add_model(folder.path_join(entry.file));actor=app.renderer.active_model()
		check(error.is_empty() and actor!=null and Model.Shape.enabled(actor.data),"ordinary new import enables source shape: "+entry.file)
		if actor==null:continue
		var descriptor: Dictionary=actor.root.get_meta(Model.Shape.META);var row_found:=false
		for row in descriptor.rows:
			if int(row.node)!=entry.node:continue
			row_found=true
			check(absf(row.mesh.get_blend_shape_value(0)-entry.values[0])<.000001 and absf(row.mesh.get_blend_shape_value(1)-entry.values[1])<.000001,"exact mesh binding and per-instance defaults: "+entry.file)
		check(row_found and descriptor.error.is_empty(),"source identity survives node replacement/reparenting: "+entry.file)
		if entry.file=="root.glb":
			var fitted: Dictionary=preload("res://src/physics_prop.gd").create(actor,app.renderer.world,0)
			check(not fitted.has("error"),"shape-aware unskinned prop creates actual collision geometry")
			if not fitted.has("error"):
				var mesh: MeshInstance3D=descriptor.rows[0].mesh
				var points: PackedVector3Array=fitted.physics.body.get_child(0).shape.points
				var transform: Transform3D=fitted.physics.body.global_transform.affine_inverse()*mesh.global_transform
				var index:=0;var hull_error:=0.0
				for surface in range(mesh.mesh.get_surface_count()):
					for point in Model.Shape.vertices(mesh,surface,mesh.mesh.surface_get_arrays(surface)[Mesh.ARRAY_VERTEX]):
						hull_error=maxf(hull_error,points[index].distance_to(transform*point));index+=1
				check(index==points.size() and hull_error<.00001,"actual prop hull fits morphed vertices rather than the neutral mesh")
				fitted.physics.dispose()
	var before: Dictionary=app.current_world().duplicate(true)
	var bad_error: String=app.pose_editor.add_model(folder.path_join("bad-default.glb"))
	check(not bad_error.is_empty() and app.current_world()==before,"unsupported imported default refuses while preserving the complete current world")
	app.new_project();app.load_scene(folder.path_join("floor.glb"));var floor_id: String=app.last_import_id
	var camera: Camera3D=app.renderer.camera;camera.position=Vector3(100,6,105);camera.quaternion=Quaternion.IDENTITY
	app.world_selection.select_entity(floor_id);await settled()
	var bounds_match:=true;var copies:=0
	for entry in app.world_selection.entries:
		if entry.kind!=floor_id:continue
		copies+=1;bounds_match=bounds_match and entry.copy.custom_aabb==entry.original.custom_aabb and entry.copy.get_blend_shape_value(0)==1.
	check(copies==1 and bounds_match,"green selection copies shape weights and displaced culling bounds")
	app.import_actions.add(source,true,0);actor=app.renderer.active_model()
	check(actor.data.metadata.initial_placement.support=="mesh" and absf(app.renderer.scene_bounds(actor.root).position.y-4)<.01,"visible import grounds on a floor morphed far beyond its original bounds")
	app.physics_editor.build_colliders();var map_faces:=0;var contacts_match:=true
	for body in app.physics_editor.colliders.get_children():
		for point in body.get_child(0).shape.get_faces():map_faces+=1;contacts_match=contacts_match and absf(point.y-4)<.00001 and point.x>=89.99 and point.x<=110.01
	check(map_faces==6 and contacts_match,"actual static map collision uses displaced morph geometry")
	app.physics_editor.clear_colliders()
	var native_plans: Array=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("native-plans.json")))
	for plan in native_plans:
		app.new_project();var error: String=app.pose_editor.add_model(plan.source);actor=app.renderer.active_model()
		if not error.is_empty():print("NATIVE_SHAPE_ERROR ",plan.label," ",error)
		check(error.is_empty() and actor!=null,"ordinary native prepared import accepts its declared shape: "+plan.label)
		if actor==null:continue
		var descriptor: Dictionary=actor.root.get_meta(Model.Shape.META)
		check(descriptor.error.is_empty() and descriptor.rows.size()==plan.meshes and Model.Shape.enabled(actor.data) and Model.Shape.snapshot(actor.root).is_empty(),"all actual native morph mesh bindings resolve without inventing nonzero defaults: "+plan.label)
	var result:={"checks":checks,"failures":failures,"review_geometry_error":maximum,"movie":movie}
	var f:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);f.store_string(JSON.stringify(result));f.close();print("SOURCE_SHAPES "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
