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
# Test-only JSON-wire oracle. Existing adjacent-double ceiling follows
# tests/rotation_gizmo_smoke.gd:15-29. Structure, booleans and integral values
# remain exact; pose inputs must additionally reconstruct exactly in the engine.
const ColdModel=preload("res://src/model.gd")
func cold_same_json_state(a,b) -> bool:
	if a is Dictionary and b is Dictionary:
		if a.size()!=b.size():return false
		for key in a:
			if not b.has(key) or not cold_same_json_state(a[key],b[key]):return false
		return true
	if a is Array and b is Array:
		if a.size()!=b.size():return false
		for index in range(a.size()):
			if not cold_same_json_state(a[index],b[index]):return false
		return true
	if (a is float or a is int) and (b is float or b is int):
		if not is_finite(float(a)) or not is_finite(float(b)):return false
		# Counts/indices and zero cannot become fractional under this oracle.
		if float(a)==floor(float(a)) or float(b)==floor(float(b)):return float(a)==float(b)
		return absf(float(a)-float(b))<=0.000000000001
	if typeof(a)!=typeof(b):return false
	return a==b
func cold_engine_pose_same(a,b) -> bool:
	if not ColdModel.pose_valid(a) or not ColdModel.pose_valid(b) or a.size()!=b.size():return false
	for id in a:
		if not b.has(id):return false
		if Timeline.vector(a[id].position)!=Timeline.vector(b[id].position):return false
		if Timeline.quaternion(a[id].rotation_xyzw)!=Timeline.quaternion(b[id].rotation_xyzw):return false
	return true
func cold_saved_fields_same(actual: Dictionary,expected_wire: Dictionary,original_pose: Dictionary) -> bool:
	for field in ["sha256","pose","pose_keys","metadata"]:
		if not actual.has(field) or not expected_wire.has(field):return false
	return actual.sha256==expected_wire.sha256 and cold_same_json_state(actual.pose,expected_wire.pose) and cold_engine_pose_same(original_pose,actual.pose) and actual.pose_keys==expected_wire.pose_keys and cold_same_json_state(actual.metadata,expected_wire.metadata)
func cold_control(ok: bool,label: String,state: Dictionary) -> void:
	state.checks+=1
	if not ok:state.failures+=1;state.failed_labels.append(label)
func cold_oracle_controls() -> bool:
	var original: Dictionary={"sha256":"a".repeat(64),"pose":{"joint":{"position":[0.125,0.00001,-0.25],"rotation_xyzw":[0.0,0.0,0.0,1.0]}},"pose_keys":[],"metadata":{"count":3,"enabled":false,"unknown":{"word":"kept","fraction":0.125}}}
	var original_bytes:=var_to_bytes(original)
	var expected: Dictionary=JSON.parse_string(JSON.stringify(original,"",true,true))
	var tally: Dictionary={"checks":0,"failures":0,"failed_labels":[]}
	var candidate: Dictionary=expected.duplicate(true)
	cold_control(cold_saved_fields_same(candidate,expected,original.pose),"full_precision_wire_expected_is_accepted",tally)
	cold_control(cold_engine_pose_same(original.pose,expected.pose),"same_wire_has_exact_engine_pose_inputs",tally)
	candidate.metadata.count=3.0
	cold_control(cold_saved_fields_same(candidate,expected,original.pose),"integral_json_float_count_retains_value",tally)
	candidate=expected.duplicate(true);candidate.metadata.erase("unknown")
	cold_control(not cold_saved_fields_same(candidate,expected,original.pose),"unknown_metadata_cannot_disappear",tally)
	candidate=expected.duplicate(true);candidate.metadata.unknown.extra="foreign"
	cold_control(not cold_saved_fields_same(candidate,expected,original.pose),"unknown_metadata_cannot_be_added",tally)
	candidate=expected.duplicate(true);candidate.metadata.enabled=0
	cold_control(not cold_saved_fields_same(candidate,expected,original.pose),"boolean_is_not_a_number",tally)
	candidate=expected.duplicate(true);candidate.metadata.count=3.0000000000005
	cold_control(not cold_saved_fields_same(candidate,expected,original.pose),"count_cannot_become_fractional_inside_scalar_ceiling",tally)
	candidate=expected.duplicate(true);candidate.metadata.count=4
	cold_control(not cold_saved_fields_same(candidate,expected,original.pose),"changed_count_refused",tally)
	candidate=expected.duplicate(true);candidate.sha256="b".repeat(64)
	cold_control(not cold_saved_fields_same(candidate,expected,original.pose),"changed_source_hash_refused",tally)
	candidate=expected.duplicate(true);candidate.metadata.unknown.word="changed"
	cold_control(not cold_saved_fields_same(candidate,expected,original.pose),"changed_string_refused",tally)
	candidate=expected.duplicate(true);candidate.pose.joint.position[0]+=0.001
	cold_control(not cold_saved_fields_same(candidate,expected,original.pose),"meaningful_translation_drift_refused",tally)
	candidate=expected.duplicate(true);candidate.pose.joint.position[1]+=0.00000000000075
	cold_control(cold_same_json_state(candidate.pose,expected.pose) and not cold_engine_pose_same(original.pose,candidate.pose) and not cold_saved_fields_same(candidate,expected,original.pose),"engine_visible_drift_below_scalar_ceiling_refused",tally)
	candidate=expected.duplicate(true);candidate.pose.joint.rotation_xyzw=[0.0,0.0,0.001,1.0]
	cold_control(not cold_saved_fields_same(candidate,expected,original.pose),"meaningful_rotation_drift_refused",tally)
	candidate=expected.duplicate(true);candidate.pose.joint.rotation_xyzw[3]=2.0
	cold_control(not cold_saved_fields_same(candidate,expected,original.pose),"quaternion_value_change_not_hidden_by_engine_normalization",tally)
	candidate=expected.duplicate(true);candidate.pose.joint.position.pop_back()
	cold_control(not cold_saved_fields_same(candidate,expected,original.pose),"changed_array_shape_refused",tally)
	candidate=expected.duplicate(true);candidate.pose.erase("joint")
	cold_control(not cold_saved_fields_same(candidate,expected,original.pose),"missing_pose_channel_refused",tally)
	candidate=expected.duplicate(true);candidate.pose_keys.append({"frame":0})
	cold_control(not cold_saved_fields_same(candidate,expected,original.pose),"unsolicited_pose_key_refused",tally)
	candidate=expected.duplicate(true);candidate.metadata.unknown.fraction=NAN
	cold_control(not cold_saved_fields_same(candidate,expected,original.pose),"nonfinite_scalar_refused",tally)
	candidate=expected.duplicate(true);candidate.erase("metadata")
	cold_control(not cold_saved_fields_same(candidate,expected,original.pose),"missing_whole_metadata_refused",tally)
	cold_control(var_to_bytes(original)==original_bytes,"expected_wire_does_not_mutate_authored_input",tally)
	print("IMPORT_OFF_COLD_ORACLE_CONTROLS "+JSON.stringify({"format":"has_off_import_cold_wire_controls_1","checks":tally.checks,"failures":tally.failures,"failed_labels":tally.failed_labels,"actual_native_asset_tested":false,"application_adopted":false}))
	if tally.checks!=20 or tally.failures>0:push_error("Cold import wire oracle controls failed.");return false
	return true
func run() -> void:
	if not cold_oracle_controls():quit(1);return
	var folder: String=OS.get_cmdline_user_args()[0]
	var asset:=folder.path_join("limb.glb");Fixture.create(asset)
	var unsupported:=folder.path_join("unsupported.glb");SceneIO.make_pose_fixture(unsupported)
	var hair_asset:=folder.path_join("hair.glb");SecondaryFixture.create(hair_asset)
	var hash:=FileAccess.get_sha256(asset)
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settled();app.home.hide()
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
	check(not physics.is_running() and not physics.toggle.button_pressed and not physics.hair_toggle.button_pressed and physics.toggle.is_visible_in_tree() and physics.collider_triangles==0 and physics.import_starts.is_empty(),"interactive compatible import defaults both Physics and Hair & clothes off with no queued activation")
	physics.change(true);await settled()
	check(physics.active(id) and physics.toggle.button_pressed and physics.collider_triangles>0,"explicit Physics on starts the retained compatible rig against the map")
	check(actor.data.metadata.initial_placement.support=="view" and actor.root.global_position.y>5,"normal aerial import starts above the floor for the gravity probe")
	if not physics.active(id):app.free();quit(1);return
	var simulation: RefCounted=physics.simulations[id];var initial:={}
	for part in simulation.bodies:initial[part]=simulation.bodies[part].global_position
	for i in range(120):await physics_frame
	var fall:=0.
	for part in initial:fall=maxf(fall,initial[part].y-simulation.bodies[part].global_position.y)
	check(fall>0.01,"explicitly enabled imported ragdoll actually falls under gravity")
	check(actor.data==before and actor.data.pose_keys.is_empty() and app.history.size()==history and app.keys==shots,"explicit live motion creates no pose keys, history or camera changes")
	physics.toggle.button_pressed=false;await settled()
	var frozen: Dictionary=actor.data.duplicate(true)
	check(not physics.is_running() and actor.data.pose_keys.is_empty() and frozen.pose!=before.pose,"immediate Physics off freezes the fallen pose without recording")
	app.undo();app.redo();await settled()
	check(not physics.is_running() and actor.data==frozen,"Undo/Redo of frozen pose never rearms import physics")
	# Capture the expected JSON wire before Save; it never comes from reopened data.
	var frozen_wire: Dictionary=JSON.parse_string(JSON.stringify(frozen,"",true,true))
	var existing_project:=folder.path_join("existing-off-intent.has");app.has_project.save_file(existing_project,"packed");await wait_job(app.has_project)
	app.new_project();app.has_project.open_file(existing_project);await wait_job(app.has_project)
	actor=app.renderer.world_runtime.instance(id)
	check(actor!=null and not physics.is_running() and physics.import_starts.is_empty() and cold_saved_fields_same(actor.data,frozen_wire,frozen.pose),"existing project restores its frozen pose and retained setup without fresh simulation")
	app.world_selection.select_entity(id,false)
	physics.change(true);await settled();var view: Transform3D=app.renderer.camera.transform
	app.import_actions.add(asset,true,0);var second: String=app.last_import_id;await settled()
	check(physics.active(id) and not physics.active(second) and physics.simulations.size()==1 and not physics.import_starts.has(second),"adding a second model keeps it off and resumes the explicitly running peer")
	physics.change(true);await settled()
	check(physics.active(id) and physics.active(second) and physics.simulations.size()==2,"explicit activation of the second model leaves both independent bodies running")
	check(app.world_selection.selected==second and app.renderer.camera.transform==view,"peer restart retains new selection and the inspection camera")
	var map:=folder.path_join("map.glb");SceneIO.make_fixture(map);app.load_scene(map);var map_id: String=app.last_import_id;await settled()
	check(physics.active(id) and physics.active(second) and not physics.active(map_id) and physics.toggle.disabled,"adding an environment rebuilds collision and resumes bodies without simulating the map")
	check(app.world_selection.selected==map_id,"starting unselected peers never steals map selection")
	app.import_actions.add(unsupported,true,0);var unsupported_id: String=app.last_import_id;await settled()
	check(not physics.active(unsupported_id) and not physics.import_starts.has(unsupported_id) and physics.active(id) and physics.active(second),"unsupported import stays off while explicitly running peers resume")
	physics.change(true);await settled()
	check(not physics.active(unsupported_id) and physics.active(id) and physics.active(second) and "validated" in app.status.text,"explicit unsupported Physics retains its validation reason and valid peers")
	app.import_actions.add(map,true,0);var solid: String=app.last_import_id;await settled()
	check(not physics.active(solid) and physics.active(id) and physics.active(second),"unrigged props are not forced into automatic ragdolls")
	physics.freeze_all()
	# The new default never queues. Explicit restoration tickets still respect modal ownership.
	app.import_actions.add(asset,true,0);var delayed: String=app.last_import_id
	var dialog:=AcceptDialog.new();app.add_child(dialog);dialog.dialog_text="Owned import warning";dialog.popup_centered();await settled()
	check(not physics.active(delayed) and not physics.import_starts.has(delayed),"new import remains off even after a warning dialog is shown")
	physics.queue_import_start(delayed,true,false,true);await settled()
	check(not physics.active(delayed) and physics.import_starts.has(delayed),"explicit queued intent still waits for its warning dialog")
	dialog.hide();dialog.queue_free();await settled()
	check(physics.active(delayed),"dismissal starts the explicitly queued ragdoll once")
	physics.freeze_all();app.import_actions.add(asset,true,0);var cancelled: String=app.last_import_id;physics.queue_import_start(cancelled,true,false,true);physics.change(false);await settled()
	check(not physics.active(cancelled) and not physics.import_starts.has(cancelled),"Physics off can cancel a queued start immediately")
	app.import_actions.add(asset,true,0);var stale: String=app.last_import_id;physics.queue_import_start(stale,true,false,true);app.set_frame(1);await settled()
	check(not physics.active(stale) and physics.import_starts.is_empty(),"seeking cancels pending starts instead of unexpectedly simulating playback")
	app.new_project();app.load_demo_room();app.pose_editor.add_model(hair_asset);var hair: String=app.last_import_id
	physics.change_hair(true);await wait_hair(physics)
	check(physics.active(hair) and physics.simulations[hair] is Secondary,"authored secondary-only motion is active before structural import")
	app.import_actions.add(asset,true,0);var beside_hair: String=app.last_import_id;await settled();await wait_hair(physics)
	check(physics.active(hair) and physics.simulations[hair] is Secondary and physics.simulations[hair].primary==null and not physics.active(beside_hair) and not physics.import_starts.has(beside_hair),"new off-by-default model preserves a peer's explicit secondary-only mode")
	physics.freeze_all();app.new_project();app.load_demo_room()
	app.import_actions.add(asset,true,0);await settled();id=app.last_import_id;actor=app.renderer.active_model()
	app.physics_editor.recording.scope.select(0)
	check(not physics.recording.start() and not physics.is_running() and actor.data.pose_keys.is_empty(),"Record cannot implicitly enable physics on a new off-by-default import")
	physics.change(true);await settled()
	check(physics.recording.start(),"explicit Physics on can use explicit Local Record")
	for i in range(90):await physics_frame
	check(physics.recording.finish() and actor.has_animation() and not physics.is_running(),"explicit Record alone creates an editable take after explicit Physics on")
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
		check(not physics.active(id) and not physics.toggle.button_pressed and not physics.hair_toggle.button_pressed and physics.import_starts.is_empty() and actor.data==before and actor.data.pose_keys.is_empty(),"native standard rig defaults off with exact retained setup and provenance: "+plan.label)
		physics.change(true);await settled()
		check(physics.active(id) and physics.simulations[id].bodies.size()>=3 and actor.data==before and actor.data.pose_keys.is_empty(),"native standard rig explicitly simulates from retained setup without recording: "+plan.label)
		physics.change(false);await settled()
		check(not physics.active(id) and actor.data.metadata==before.metadata and actor.data.pose_keys.is_empty(),"native import freezes with exact provenance and no generated keys: "+plan.label)
		if str(plan.label).begins_with("VRM1"):
			physics.change(true);physics.change_hair(true);await wait_hair(physics)
			check(physics.active(id) and physics.simulations[id] is Secondary and physics.simulations[id].primary!=null,"native body and hair are combined before another import")
			app.import_actions.add(asset,true,0);var peer: String=app.last_import_id;await settled();await wait_hair(physics)
			check(physics.active(id) and physics.simulations[id] is Secondary and physics.simulations[id].primary!=null and not physics.active(peer) and not physics.import_starts.has(peer),"structural import restores explicit native combined body/hair while the new model stays off")
	app.new_project();app.import_actions.pick(24,true);await settled()
	picker=null
	for child in app.get_children():
		if child is FileDialog and child.visible:picker=child;break
	if picker:picker.file_selected.emit(asset)
	await settled();id=app.last_import_id
	check(app.frame==24 and app.renderer.active_model().data.start_frame==24 and not physics.active(id) and not physics.import_starts.has(id),"timeline import keeps its chosen frame and starts with both simulations off")
	physics.change(true);await settled()
	check(physics.active(id),"timeline model retains explicit Physics activation at its chosen frame")
	app.new_project();app.import_actions.add(asset,true,0);var pending_id: String=app.last_import_id
	check(not physics.active(pending_id) and not physics.import_starts.has(pending_id),"new import has no delayed start for Save to accidentally persist")
	physics.queue_import_start(pending_id,true,false,true)
	var pending_project:=folder.path_join("saved-before-start.has");app.has_project.save_file(pending_project,"packed");await wait_job(app.has_project)
	check(not physics.active(pending_id) and physics.import_starts.is_empty(),"Save before the next UI frame cancels its pending live start")
	app.new_project();app.import_actions.add(asset,true,0);physics.queue_import_start(app.last_import_id,true,false,true);app.new_project();await settled()
	check(not physics.is_running() and physics.import_starts.is_empty() and app.renderer.world_runtime.instances.is_empty(),"New cancels late explicit queued starts and leaves an empty world")
	check(FileAccess.get_sha256(asset)==hash,"interactive simulation never modifies its original GLB")
	var result:={"checks":checks,"failures":failures,"folder":folder,"movie":movie,"fall":fall,"native_models":plans.size()}
	var file:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close()
	print("IMPORT_PHYSICS "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
