extends SceneTree
const Fixture=preload("res://tests/limb_fixture.gd")
const SecondaryFixture=preload("res://tests/secondary_fixture.gd")
const SceneIO=preload("res://src/scene3d.gd")
const Drawing=preload("res://src/drawing.gd")
const Timeline=preload("res://src/timeline.gd")
const Secondary=preload("res://src/secondary_live.gd")
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(180).timeout.connect(func():push_error("Import physics watchdog");quit(2));call_deferred("run")
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func settled() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func wait_job(job) -> void:
	while job.pid>0:await process_frame
	await settled()
func wait_hair(physics) -> void:
	var deadline:=Time.get_ticks_msec()+10000
	while not physics.pending.is_empty() and Time.get_ticks_msec()<deadline:await process_frame
	await settled()
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0]
	var asset:=folder.path_join("limb.glb");Fixture.create(asset)
	var unsupported:=folder.path_join("unsupported.glb");SceneIO.make_pose_fixture(unsupported)
	var hair_asset:=folder.path_join("hair.glb");SecondaryFixture.create(hair_asset)
	var hash:=FileAccess.get_sha256(asset)
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled()
	app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	var physics=app.physics_editor
	check(not app.advanced_mode and not physics.is_running(),"empty Simple startup contains no spontaneous simulation")
	app.pose_editor.add_model(asset);await settled()
	check(not physics.is_running(),"low-level asset setup does not invent an interactive import request")
	app.new_project();app.load_demo_room()
	# Grounded placement can already support this short arm. Use the normal
	# aerial fallback to prove gravity, rather than demand that a grounded rig falls.
	app.renderer.camera.position=Vector3(300,10,305);app.renderer.camera.quaternion=Quaternion.IDENTITY
	app.pose_editor.import_dialog();await settled()
	var picker: FileDialog=null
	for child in app.get_children():
		if child is FileDialog and child.visible:picker=child;break
	check(picker!=null,"normal Add model opens the real file picker")
	if picker:picker.file_selected.emit(asset)
	var id: String=app.last_import_id;var actor: RefCounted=app.renderer.active_model()
	var before: Dictionary=actor.data.duplicate(true);var shots: Array=app.keys.duplicate(true);var history: int=app.history.size()
	await settled()
	check(physics.active(id) and physics.toggle.button_pressed and physics.toggle.is_visible_in_tree() and physics.collider_triangles>0,"interactive compatible import starts real Physics in Simple against the map")
	check(actor.data.metadata.initial_placement.support=="view" and actor.root.global_position.y>5,"normal aerial import starts above the floor for the gravity probe")
	if not physics.active(id):app.free();quit(1);return
	var simulation: RefCounted=physics.simulations[id];var initial:={}
	for part in simulation.bodies:initial[part]=simulation.bodies[part].global_position
	for i in range(120):await physics_frame
	var fall:=0.
	for part in initial:fall=maxf(fall,initial[part].y-simulation.bodies[part].global_position.y)
	check(fall>0.01,"automatically enabled ragdoll actually falls under gravity")
	check(actor.data==before and actor.data.pose_keys.is_empty() and app.history.size()==history and app.keys==shots,"default live motion creates no pose keys, history or camera changes")
	physics.toggle.button_pressed=false;await settled()
	var frozen: Dictionary=actor.data.duplicate(true)
	check(not physics.is_running() and actor.data.pose_keys.is_empty() and frozen.pose!=before.pose,"immediate Physics off freezes the fallen pose without recording")
	app.undo();app.redo();await settled()
	check(not physics.is_running() and actor.data==frozen,"Undo/Redo of frozen pose never rearms import physics")
	physics.change(true);await settled();var view: Transform3D=app.renderer.camera.transform
	app.import_actions.add(asset,true,0);var second: String=app.last_import_id;await settled()
	check(physics.active(id) and physics.active(second) and physics.simulations.size()==2,"adding a second ragdoll resumes the existing body as well as the new one")
	check(app.world_selection.selected==second and app.renderer.camera.transform==view,"peer restart retains new selection and the inspection camera")
	var map:=folder.path_join("map.glb");SceneIO.make_fixture(map);app.load_scene(map);var map_id: String=app.last_import_id;await settled()
	check(physics.active(id) and physics.active(second) and not physics.active(map_id) and physics.toggle.disabled,"adding an environment rebuilds collision and resumes bodies without simulating the map")
	check(app.world_selection.selected==map_id,"starting unselected peers never steals map selection")
	app.import_actions.add(unsupported,true,0);var unsupported_id: String=app.last_import_id;await settled()
	check(not physics.active(unsupported_id) and physics.active(id) and physics.active(second) and "validated" in app.status.text,"unsupported rigs stay poseable with a reason while valid peers resume")
	app.import_actions.add(map,true,0);var solid: String=app.last_import_id;await settled()
	check(not physics.active(solid) and physics.active(id) and physics.active(second),"unrigged props are not forced into automatic ragdolls")
	physics.freeze_all()
	# A real warning/modal holds the start until its owner dismisses it.
	app.import_actions.add(asset,true,0);var delayed: String=app.last_import_id
	var dialog:=AcceptDialog.new();app.add_child(dialog);dialog.dialog_text="Owned import warning";dialog.popup_centered();await settled()
	check(not physics.active(delayed) and physics.import_starts.has(delayed),"automatic activation waits for import warning dialogs")
	dialog.hide();dialog.queue_free();await settled()
	check(physics.active(delayed),"dismissal starts the queued ragdoll once")
	physics.freeze_all();app.import_actions.add(asset,true,0);var cancelled: String=app.last_import_id;physics.change(false);await settled()
	check(not physics.active(cancelled) and not physics.import_starts.has(cancelled),"Physics off can cancel a queued start immediately")
	app.import_actions.add(asset,true,0);var stale: String=app.last_import_id;app.set_frame(1);await settled()
	check(not physics.active(stale) and physics.import_starts.is_empty(),"seeking cancels pending starts instead of unexpectedly simulating playback")
	app.new_project();app.load_demo_room();app.pose_editor.add_model(hair_asset);var hair: String=app.last_import_id
	physics.change_hair(true);await wait_hair(physics)
	check(physics.active(hair) and physics.simulations[hair] is Secondary,"authored secondary-only motion is active before structural import")
	app.import_actions.add(asset,true,0);var beside_hair: String=app.last_import_id;await settled();await wait_hair(physics)
	check(physics.active(hair) and physics.simulations[hair] is Secondary and physics.simulations[hair].primary==null and physics.active(beside_hair),"new body import preserves a peer's secondary-only mode")
	physics.freeze_all();app.new_project();app.load_demo_room()
	app.import_actions.add(asset,true,0);await settled();id=app.last_import_id;actor=app.renderer.active_model()
	app.physics_editor.recording.scope.select(0);check(physics.recording.start(),"automatically live import can immediately use explicit Local Record")
	for i in range(90):await physics_frame
	check(physics.recording.finish() and actor.has_animation() and not physics.is_running(),"explicit Record alone creates an editable take from default live physics")
	app.mode.select(0);app.change_mode(0);app.set_frame(0);app.create_cel(false)
	Drawing.edit_image(Drawing.cel_at(app.layers[1],0)).image.set_pixel(80,80,Color.CYAN);var paint: PackedByteArray=Drawing.image(Drawing.cel_at(app.layers[1],0)).get_data()
	var project:=folder.path_join("import-physics.has");app.has_project.save_file(project,"packed");await wait_job(app.has_project)
	app.new_project();app.has_project.open_file(project);await wait_job(app.has_project)
	check(not physics.is_running() and physics.import_starts.is_empty() and app.renderer.world_runtime.instance(id).has_animation() and Drawing.image(Drawing.cel_at(app.layers[1],0)).get_data()==paint,"HAS reopens the authored take and exact drawing without fresh simulation")
	var preview: Image=await app.renderer.capture(app.keys,app.layers,0,true);var error: String=await app.export_movie(folder)
	check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000001.png")).get_data()==preview.get_data(),"MP4 uses saved authored motion and overlay rather than new live physics")
	var movie: String=app.last_export_folder.path_join("movie.mp4")
	var plans: Array=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("native-plans.json")))
	for plan in plans:
		app.new_project();app.load_demo_room();app.import_actions.add(plan.source,true,0)
		actor=app.renderer.active_model();id=actor.data.id;before=actor.data.duplicate(true);await settled()
		check(physics.active(id) and physics.simulations[id].bodies.size()>=3 and actor.data==before and actor.data.pose_keys.is_empty(),"native standard rig automatically simulates without recording: "+plan.label)
		physics.change(false);await settled()
		check(not physics.active(id) and actor.data.metadata==before.metadata and actor.data.pose_keys.is_empty(),"native import freezes with exact provenance and no generated keys: "+plan.label)
		if str(plan.label).begins_with("VRM1"):
			physics.change(true);physics.change_hair(true);await wait_hair(physics)
			check(physics.active(id) and physics.simulations[id] is Secondary and physics.simulations[id].primary!=null,"native body and hair are combined before another import")
			app.import_actions.add(asset,true,0);var peer: String=app.last_import_id;await settled();await wait_hair(physics)
			check(physics.active(id) and physics.simulations[id] is Secondary and physics.simulations[id].primary!=null and physics.active(peer),"structural import restores native combined body/hair mode alongside its new ragdoll")
	app.new_project();app.import_actions.pick(24,true);await settled()
	picker=null
	for child in app.get_children():
		if child is FileDialog and child.visible:picker=child;break
	if picker:picker.file_selected.emit(asset)
	await settled();id=app.last_import_id
	check(app.frame==24 and app.renderer.active_model().data.start_frame==24 and physics.active(id),"timeline import at its chosen frame also defaults to live ragdoll physics")
	app.new_project();app.import_actions.add(asset,true,0);var pending_id: String=app.last_import_id
	var pending_project:=folder.path_join("saved-before-start.has");app.has_project.save_file(pending_project,"packed");await wait_job(app.has_project)
	check(not physics.active(pending_id) and physics.import_starts.is_empty(),"Save before the next UI frame cancels its pending live start")
	app.new_project();app.import_actions.add(asset,true,0);app.new_project();await settled()
	check(not physics.is_running() and physics.import_starts.is_empty() and app.renderer.world_runtime.instances.is_empty(),"New cancels late automatic starts and leaves an empty world")
	check(FileAccess.get_sha256(asset)==hash,"interactive simulation never modifies its original GLB")
	var result:={"checks":checks,"failures":failures,"folder":folder,"movie":movie,"fall":fall,"native_models":plans.size()}
	var file:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close()
	print("IMPORT_PHYSICS "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
