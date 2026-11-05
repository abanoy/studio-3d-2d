extends SceneTree
const Measure=preload("res://src/map_measure.gd")
const Scene=preload("res://src/scene3d.gd")
const Model=preload("res://src/model.gd")
const Drawing=preload("res://src/drawing.gd")
var checks:=0
var failures:=0
func check(value: bool,text: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+text)
	if not value:failures+=1
func _initialize() -> void:
	create_timer(160).timeout.connect(func():push_error("Map calibration watchdog");quit(2));call_deferred("run")
func settle() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func job(operation) -> void:
	while operation.pid>0:await process_frame
	await settle()
func click(review,world: Vector3) -> void:
	var point: Vector2=review.scratch.camera.unproject_position(world);var rect: Rect2=review.image_rect()
	var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.pressed=true;event.position=rect.position+point/Vector2(960,540)*rect.size
	review.preview.gui_input.emit(event)
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0]
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settle();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("has-cache")
	var review=app.map_calibration
	if OS.get_cmdline_user_args().size()>1:
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
		app.has_project.open_file(folder.path_join("map-packed.has"));await job(app.has_project)
		var rig: RefCounted=app.renderer.world_runtime.instance(expected.id)
		check(rig!=null and JSON.parse_string(JSON.stringify(rig.data.metadata,"",true,true))==expected.metadata,"cold Open preserves exact map calibration provenance")
		check(rig!=null and PackedFloat32Array([rig.data.scale]).to_byte_array().hex_encode()==expected.scale_bits,"cold Open keeps exact engine scale without applying a second fit")
		check(not review.pending and Drawing.cel_at(app.layers[1],0).image.get_pixel(70,70)==Color.CYAN,"cold Open keeps editable screen drawing and no measurement session")
		print("MAP_CALIBRATION_READER "+JSON.stringify({"checks":checks,"failures":failures}));app.free();quit(0 if failures==0 else 1);return
	review.open();check(not review.pending,"map tool refuses empty selection")
	var path:=folder.path_join("authored-map.glb");var node:=Node3D.new();node.name="OriginalMeasuredMap"
	Scene.box(node,"DoorReference",Vector3(0,2,0),Vector3(3,4,.2),Color("b6b09a"));Scene.box(node,"Floor",Vector3(0,-.1,1),Vector3(8,.2,6),Color("525c6b"))
	var doc:=GLTFDocument.new();var state:=GLTFState.new();var error: int=doc.append_from_scene(node,state)
	if error==OK:error=doc.write_to_filesystem(state,path)
	node.free();check(error==OK,"original static doorway/reference fixture exports as standard GLB")
	var data:=Model.definition(path);data.position=[2,0,0]
	check(app.append_object(data,"environment").is_empty(),"map installs through the shared standard world path")
	var map_id: String=app.last_import_id
	var peer:=Model.definition("res://examples/tutorials/Practice figure.glb");peer.position=[-3,0,0];app.append_object(peer,"model")
	var peer_id: String=app.last_import_id;var peer_before: Dictionary=app.renderer.world_runtime.instance(peer_id).data.duplicate(true)
	app.world_selection.select_entity(map_id);app.renderer.camera.position=Vector3(2,2,8);app.renderer.camera.look_at(Vector3(2,2,0),Vector3.UP)
	var before: Dictionary=app.current_world();var keys: Array=app.keys.duplicate(true);var view: Dictionary=app.renderer.view_state();var history: int=app.history.size()
	var initial: Image=await app.renderer.capture(app.keys,app.layers,0,true);app.renderer.restore_view(view)
	review.open();await settle()
	check(review.pending and review.triangles.size()==24,"review owns a separate exact-triangle standard map copy")
	if not review.pending or review.triangles.is_empty():print(review.note.text);app.free();quit(1);return
	check(app.current_world()==before and app.keys==keys and app.history.size()==history and app.renderer.view_state()==view,"opening review preserves world, shot, camera, history and peers")
	var first:=Vector3(2,.2,.1);var second:=Vector3(2,3.8,.1)
	click(review,first);click(review,second);await settle()
	check(review.points.size()==2 and review.points[0].distance_to(first)<.00002 and review.points[1].distance_to(second)<.00002,"actual preview clicks choose exact nearest map surfaces")
	check(not review.apply_button.disabled and review.guide.mesh.get_surface_count()==1,"two measured points enable Apply with a separate reference guide")
	var raw_transform: Transform3D=review.scratch.model.root.global_transform
	review.fit_preview.button_pressed=true;await settle()
	check(review.scratch.model.root.global_transform!=raw_transform and app.current_world()==before and app.history.size()==history,"Preview size changes only the disposable map, with no world edit or key")
	check(absf(review.scratch.model.root.global_transform.basis.get_scale().x-2.032/3.6)<.00001,"proposed map preview uses the actual planned uniform scale")
	root.get_texture().get_image().save_png(folder.path_join("map-review.png"));review.scratch.viewport.get_texture().get_image().save_png(folder.path_join("reference-preview.png"))
	click(review,first);check(review.points.size()==2,"preview mode cannot accidentally pick old unscaled triangles")
	review.fit_preview.button_pressed=false;await settle();check(review.scratch.model.root.global_transform==raw_transform,"turning Preview size off restores exact neutral measuring geometry")
	var during: Image=await app.renderer.capture(app.keys,app.layers,0,true);app.renderer.restore_view(view)
	check(during.get_data()==initial.get_data(),"measurement and cyan reference never enter the live final renderer")
	var plan:=Measure.fit(data,review.points,2.032);check(plan.error.is_empty() and absf(plan.factor-2.032/3.6)<.00001,"known doorway distance computes a uniform fit, independent of overall map bounds")
	var measured: Array=review.points.duplicate();review.apply();await settle()
	var rig: RefCounted=app.renderer.world_runtime.instance(map_id)
	var old_transform:=Transform3D(Basis.IDENTITY,Vector3(2,0,0));var local_a: Vector3=old_transform.affine_inverse()*measured[0];var local_b: Vector3=old_transform.affine_inverse()*measured[1]
	check(not review.pending and app.history.size()==history+1,"Apply is one ordinary world Undo and closes the temporary review")
	check((rig.root.global_transform*local_a).distance_to(first)<.00002 and absf((rig.root.global_transform*local_a).distance_to(rig.root.global_transform*local_b)-2.032)<.00002,"fitted geometry keeps first anchor and reaches the known distance")
	check(app.renderer.world_runtime.instance(peer_id).data==peer_before and app.keys==keys and app.renderer.view_state()==view,"map resizing preserves peer model, shot and working camera")
	check(rig.authored_keys().is_empty() and FileAccess.get_sha256(path)==data.sha256,"map fit creates no animation keys and preserves original geometry bytes")
	var fitted: Dictionary=app.current_world();app.undo();await settle();check(app.current_world()==before,"Undo restores original full world exactly");app.redo();await settle();check(app.current_world()==fitted,"Redo restores the calibrated world exactly")
	app.world_selection.select_entity(map_id);review.open();await settle();review.close();await settle();check(app.current_world()==fitted,"Cancel leaves calibration and scene unchanged")
	review.open();app.new_project();await settle();check(not review.pending and app.renderer.world_runtime.instances.is_empty(),"New invalidates a pending map review before late installation")
	app.restore_world(fitted);app.world_selection.select_entity(map_id);review.open();await settle();app.set_frame(1);await settle();check(not review.pending,"changing frame closes a stale map review")
	app.set_frame(0);app.world_selection.select_entity(map_id)
	var animated: Dictionary=app.renderer.active_model().data.duplicate(true);var saved: Dictionary=animated.duplicate(true);animated.pose_keys=[{"frame":0,"pose":{},"transform":{"position":animated.position,"rotation_xyzw":animated.rotation_xyzw,"scale":animated.scale},"interpolation":"ease"}]
	app.renderer.active_model().data=animated;check(not review.eligibility(app.renderer.active_model()).is_empty(),"animated maps require their animation workflow instead of silent static scaling");app.renderer.active_model().data=saved
	check(not Measure.fit(data,[Vector3.ZERO,Vector3.ZERO],2).error.is_empty() and not Measure.fit(data,[Vector3.ZERO,Vector3.UP],NAN).error.is_empty(),"zero spans and nonfinite target distances refuse without mutation")
	var rotated:=data.duplicate(true);var rotation:=Quaternion(Vector3.UP,.7);rotated.rotation_xyzw=[rotation.x,rotation.y,rotation.z,rotation.w];rotated.scale=1.7
	var transform:=Transform3D(Basis(rotation).scaled(Vector3.ONE*1.7),Vector3(2,0,0));var a:=transform*Vector3(1,0,0);var b:=transform*Vector3(1,3,0)
	var rotated_plan:=Measure.fit(rotated,[a,b],2.032);var after_transform:=Transform3D(Basis(rotation).scaled(Vector3.ONE*rotated_plan.data.scale),Model.Timeline.vector(rotated_plan.data.position))
	check((after_transform*Vector3(1,0,0)).distance_to(a)<.00002 and absf((after_transform*Vector3(1,0,0)).distance_to(after_transform*Vector3(1,3,0))-2.032)<.00002,"existing root rotation and scale retain the anchor and calibrated span")
	app.world_selection.select_entity(peer_id);review.open();check(not review.pending,"character selection cannot be calibrated as an environment")
	app.world_selection.select_entity(map_id)
	var linked: Dictionary=app.renderer.active_model().data.duplicate(true);linked.parent_id=peer_id;var unchanged_data: Dictionary=app.renderer.active_model().data.duplicate(true);app.renderer.active_model().data=linked
	check(not review.eligibility(app.renderer.active_model()).is_empty(),"attached map refuses before any transform edit");app.renderer.active_model().data=unchanged_data
	review.open();await settle();app.world_selection.select_entity(peer_id);await settle();check(not review.pending,"selection changes invalidate the pending measuring session")
	app.world_selection.select_entity(map_id);review.open();review.close();review.open();await settle();check(review.pending and review.triangles.size()==24,"cancel/reopen discards the old deferred map preparation");review.close()
	Drawing.insert(app.layers[1],0,48,Drawing.blank(1920,1080));Drawing.cel_at(app.layers[1],0).image.set_pixel(70,70,Color.CYAN)
	app.keys=[Model.Timeline.key(0,Vector3(2,2,8),Quaternion.IDENTITY,55)]
	rig=app.renderer.world_runtime.instance(map_id);var metadata: Dictionary=JSON.parse_string(JSON.stringify(rig.data.metadata,"",true,true));var bits:=PackedFloat32Array([rig.data.scale]).to_byte_array().hex_encode()
	for storage in ["packed","linked"]:
		app.has_project.save_file(folder.path_join("map-"+storage+".has"),storage);await job(app.has_project);app.new_project();app.has_project.open_file(folder.path_join("map-"+storage+".has"));await job(app.has_project);rig=app.renderer.world_runtime.instance(map_id)
		check(rig!=null and JSON.parse_string(JSON.stringify(rig.data.metadata,"",true,true))==metadata and PackedFloat32Array([rig.data.scale]).to_byte_array().hex_encode()==bits,"ordinary "+storage+" HAS preserves calibrated scale/provenance")
	var preview: Image=await app.renderer.capture(app.keys,app.layers,0,true);error=OK if (await app.export_movie(folder)).is_empty() else FAILED
	check(error==OK and Image.load_from_file(app.last_export_folder.path_join("frame_000001.png")).get_data()==preview.get_data(),"ordinary MP4 exactly matches calibrated scene with independent cyan drawing")
	var movie: String=app.last_export_folder.path_join("movie.mp4")
	# Actual prepared Source map uses this same static triangle path; no converter rerun.
	var native_path: String=FileAccess.get_file_as_string(folder.path_join("native-map.txt")).strip_edges()
	var native_triangles:=0
	if not native_path.is_empty():
		app.new_project();app.load_scene(native_path);app.world_selection.select_entity(app.last_import_id);review.open();await settle();native_triangles=review.triangles.size();check(review.pending and native_triangles>100,"actual prepared gm_construct opens the same exact map-measuring path")
		if review.pending and not review.triangles.is_empty():
			var triangle: Array=review.triangles[0];var center: Vector3=(triangle[0]+triangle[1]+triangle[2])/3.;var normal: Vector3=(triangle[1]-triangle[0]).cross(triangle[2]-triangle[0]).normalized()
			var span: float=maxf(triangle[0].distance_to(triangle[1]),.1);review.scratch.camera.position=center+normal*span*.3;review.scratch.camera.near=.001
			review.scratch.camera.look_at(center,Vector3.FORWARD if absf(normal.y)>.9 else Vector3.UP)
			click(review,center*.8+triangle[0]*.2);click(review,center*.8+triangle[1]*.2);await settle()
			check(review.points.size()==2,"actual Source map accepts two surface points through the same preview input")
			if review.points.size()==2:
				var source_before: String=app.renderer.active_model().data.sha256;var source_points: Array=review.points.duplicate();var source_transform: Transform3D=app.renderer.active_model().root.global_transform;var source_a: Vector3=source_transform.affine_inverse()*source_points[0];var source_b: Vector3=source_transform.affine_inverse()*source_points[1]
				review.apply();await settle();var native_rig: RefCounted=app.renderer.active_model()
				check(not review.pending and absf((native_rig.root.global_transform*source_a).distance_to(native_rig.root.global_transform*source_b)-2.032)<.0001 and native_rig.data.sha256==source_before,"actual gm_construct calibration reaches the requested distance and retains native source identity")
			review.close()
	app.new_project();app.load_scene(path);review.open();var weak: WeakRef=weakref(review);app.free();await settle();check(weak.get_ref()==null,"teardown before deferred preparation releases map view without late callbacks")
	FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify({"id":map_id,"metadata":metadata,"scale_bits":bits},"",true,true))
	print("MAP_CALIBRATION_APP "+JSON.stringify({"checks":checks,"failures":failures,"native_triangles":native_triangles,"movie":movie}));quit(0 if failures==0 else 1)
