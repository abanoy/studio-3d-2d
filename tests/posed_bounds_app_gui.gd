extends "res://tests/posed_bounds_app_headless.gd"
# Generated fixture only. Future Root host must isolate writer/cache/user source
# before a separate copied-source reader; no owner art or native source is used.
func green(image: Image) -> int:
	if image==null:return 0
	var bytes:=image.get_data();var total:=0
	for i in range(0,bytes.size(),4):
		if bytes[i]<30 and bytes[i+1]>200 and bytes[i+2]<30:total+=1
	return total
func aabb_bits(box: AABB) -> String:
	return PackedFloat64Array([box.position.x,box.position.y,box.position.z,box.size.x,box.size.y,box.size.z]).to_byte_array().hex_encode()
func margin_bits(mesh: MeshInstance3D) -> String:
	return PackedFloat64Array([mesh.extra_cull_margin]).to_byte_array().hex_encode()
func aim_at_deformed(actor: RefCounted) -> void:
	var result: Dictionary=app.renderer.PoseBounds.query(actor.root)
	if not result.error.is_empty():push_error(result.error);return
	var bounds: AABB=result.bounds;var center: Vector3=bounds.get_center();var distance: float=maxf(.1,bounds.size.length()*1.3)
	var key: Dictionary=app.keys[0].duplicate(true);key.position=[center.x,center.y,center.z+distance];key.rotation_xyzw=[0,0,0,1];key.fov=45.;key.near=.001;key.far=100.
	app.keys=[key];app.renderer.evaluate(app.keys,app.frame)
func pick_panel(actor: RefCounted) -> bool:
	app.mode.select(2);app.change_mode(2);app.world_selection.select_entity("",false)
	app.world_selection.choose_at(Vector2(app.video.width,app.video.height)/2.)
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
	return app.world_selection.selected==actor.data.id and app.world_selection.pick_requests.is_empty()
func run() -> void:
	var args:=OS.get_cmdline_user_args()
	if args.is_empty() or DisplayServer.get_name()=="headless":push_error("Owned private graphical data folder required");quit(2);return
	var folder: String=args[0];var reading: bool="--read" in args;await setup_app(folder)
	var packed: String=folder.path_join("Bounds.has");var expected_path: String=folder.path_join("expected.json")
	if reading:
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(expected_path))
		app.has_project.open_file(packed);await wait_project();var actor: RefCounted=first_actor();var mesh: MeshInstance3D=mesh_for(actor)
		check(app.has_project.path==packed and actor!=null,"separate reader opens copied packed fixture through ordinary Open")
		check(FileAccess.get_sha256(actor.data.source)==expected.source_sha and actor.data.source.simplify_path().begins_with(app.has_project.cache_root.simplify_path()+"/"),"cold managed source is checksum-identical and belongs to fresh reader cache")
		check(actor.render_bounds_diagnostics().active and actor.render_bounds_diagnostics().error.is_empty(),"cold ordinary Model evaluation independently creates its render cache")
		check(actor.data.pose==expected.pose and actor.data.get("shape_pose",{})==expected.shape_pose,"cold replay preserves authored bone and expression data")
		check(aabb_bits(mesh.custom_aabb)==expected.custom_aabb and mesh.get_meta("has_shape_bounds")==mesh.custom_aabb,"cold shape owner recreates exact custom bounds")
		check(margin_bits(mesh)==expected.margin,"cold ordinary pose recreates exact derived margin without saved cache")
		app.mode.select(2);app.change_mode(2);await settle()
		var data: PackedByteArray=var_to_bytes(actor.data);var shot: Array=app.keys.duplicate(true);var focus: bool=app.canvas.scene_setup
		var image: Image=await app.renderer.capture(app.keys,app.layers,app.frame,false)
		var picked: bool=await pick_panel(actor)
		check(image!=null and image.get_size()==Vector2i(1920,1080) and green(image)>100 and picked,"cold near-view deformed panel renders and ordinary ID-mask picking selects it")
		check(app.renderer.native_readbacks==0 and var_to_bytes(actor.data)==data and app.keys==shot and app.canvas.scene_setup==focus,"cold readback remains balanced and preserves authored view/focus state")
		if image!=null:image.save_png(folder.path_join("cold.png"))
		if checks!=8:push_error("Expected8 cold integration controls");quit(2);return
		print("POSED_BOUNDS_GUI_READ "+JSON.stringify({"checks":checks,"failures":failures,"user_profile":OS.get_user_data_dir(),"synthetic_only":true,"native_owner_face_qualified":false}));await shutdown();return
	var source: String=folder.path_join("synthetic.glb");var made: bool=Fixture.write(source)==OK
	if made:made=app.pose_editor.add_model(source).is_empty()
	check(made,"ordinary Add model loads generated weighted panel")
	var actor: RefCounted=first_actor();var mesh: MeshInstance3D=mesh_for(actor);var source_sha: String=FileAccess.get_sha256(source)
	check(actor.render_bounds_diagnostics().active,"ordinary graphical model initializes render cache without test helper calls")
	pose_actor(actor);check(mesh.extra_cull_margin>4.9 and mask_margin_matches(mesh),"ordinary posing updates both model and selection-mask instance bounds")
	var rows: Array=actor.root.get_meta(Model.Shape.META).rows
	check(rows.size()==1 and app.pose_editor.set_shape_amounts({str(rows[0].node):{"0":.5}}).is_empty(),"ordinary expression path changes the generated panel")
	check(mesh.custom_aabb==mesh.get_meta("has_shape_bounds") and actor.render_bounds_diagnostics().active,"expression custom bounds remain owned by SourceShape")
	aim_at_deformed(actor);var view: Dictionary=app.renderer.view_state();var shot: Array=app.keys.duplicate(true);var focus: bool=app.canvas.scene_setup
	var stats: Dictionary=actor.render_bounds_diagnostics().stats;var authored: PackedByteArray=var_to_bytes(actor.data)
	var preview: Image=await app.renderer.capture(app.keys,app.layers,app.frame,false)
	var picked: bool=await pick_panel(actor)
	check(preview!=null and preview.get_size()==Vector2i(1920,1080) and green(preview)>100 and app.renderer.native_readbacks==0 and picked,"ordinary near preview renders and ID-mask picking selects the posed panel")
	check(app.renderer.view_state()==view and app.keys==shot and app.canvas.scene_setup==focus,"preview leaves camera keys and focus/scene setup unchanged")
	var final_image: Image=await app.renderer.capture(app.keys,app.layers,app.frame,true)
	check(final_image!=null and final_image.get_size()==Vector2i(1920,1080) and green(final_image)>100 and app.renderer.native_readbacks==0,"ordinary final frame contains posed panel with balanced readback")
	check(var_to_bytes(actor.data)==authored and actor.render_bounds_diagnostics().stats.inventory_array_reads==stats.inventory_array_reads,"preview/final evaluation preserves authored data and avoids vertex rescans")
	app.has_project.save_file(packed,"packed");await wait_project()
	check(app.has_project.path==packed and FileAccess.file_exists(packed),"ordinary packed save succeeds after real preview/final evaluation")
	check(FileAccess.get_sha256(source)==source_sha,"generated original source remains unchanged")
	var expected:={"source_sha":FileAccess.get_sha256(actor.data.source),"pose":actor.data.pose,"shape_pose":actor.data.get("shape_pose",{}),"custom_aabb":aabb_bits(mesh.custom_aabb),"margin":margin_bits(mesh)}
	var file:=FileAccess.open(expected_path,FileAccess.WRITE)
	if file==null:push_error("Cannot write synthetic expectation");quit(2);return
	file.store_string(JSON.stringify(expected,"",true,true));file.flush();file.close()
	if preview!=null:preview.save_png(folder.path_join("preview.png"))
	if final_image!=null:final_image.save_png(folder.path_join("final.png"))
	app.new_project();await settle()
	check(not actor.render_bounds_diagnostics().active and app.renderer.native_readbacks==0,"graphical New releases model cache without outstanding native waits")
	if checks!=12:push_error("Expected12 writer integration controls");quit(2);return
	print("POSED_BOUNDS_GUI "+JSON.stringify({"checks":checks,"failures":failures,"user_profile":OS.get_user_data_dir(),"synthetic_only":true,"native_owner_face_qualified":false}));await shutdown()
