extends SceneTree
const Support=preload("res://tests/world_test_support.gd")
const IK=preload("res://src/limb_ik.gd")
const Fixture=preload("res://tests/limb_fixture.gd")
const Timeline=preload("res://src/timeline.gd")
const Storage=preload("res://src/storage.gd")
const World=preload("res://src/world_document.gd")
const Drawing=preload("res://src/drawing.gd")
const SceneIO=preload("res://src/scene3d.gd")
var checks:=0
var failures:=0

func _initialize() -> void:
	create_timer(110).timeout.connect(func():push_error("Limb IK watchdog expired");quit(2))
	call_deferred("run")

func check(ok: bool,text: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+text)
	if not ok:failures+=1

func settled() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw

func wait_job(job) -> void:
	while job.pid>0:await process_frame
	await settled()

func close_warnings(app) -> void:
	for child in app.get_children():
		if child is AcceptDialog and child.title=="Imported with limitations":child.hide();child.queue_free()

func move_handle(app, axis: int, amount: float, cancel:=false) -> Dictionary:
	var editor=app.pose_editor;editor.update_gizmo()
	var handle: Dictionary=editor.handles[axis]
	var start: Vector2=handle.points[0].lerp(handle.points[-1],0.7)
	var before: Dictionary=editor.active_rig().data.duplicate(true)
	var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.pressed=true;editor.input(event,start)
	var desired: Vector3=editor.drag_world.origin+editor.drag_axis*amount
	var motion:=InputEventMouseMotion.new()
	editor.input(motion,start+editor.drag_screen_axis.normalized()*amount/editor.drag_units*editor.drag_pixels)
	var during: Dictionary=editor.active_rig().data.duplicate(true)
	var endpoint: Vector3=editor.active_rig().bone_transform(editor.selected).origin
	var active: bool=editor.dragging;var chain: Dictionary=editor.drag_chain.duplicate(true)
	editor.finish_drag(cancel);await settled()
	return {"before":before,"during":during,"target":desired,"end":endpoint,"dragged":active,"chain":chain}

func run() -> void:
	var folder:=ProjectSettings.globalize_path("res://output/limb-ik/run_%d" % Time.get_ticks_usec());DirAccess.make_dir_recursive_absolute(folder)
	var asset:=folder.path_join("arm.glb");Fixture.create(asset)
	if not FileAccess.file_exists(asset):check(false,"authored limb fixture must be written before runtime testing");quit(1);return
	var digest:=FileAccess.get_sha256(asset)
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled()
	app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache");app.pose_editor.add_model(asset)
	var rig: RefCounted=app.renderer.active_model();var id: String=rig.data.id;var editor=app.pose_editor
	var hand: String=rig.order[2];var limb:=IK.chain(rig,hand)
	check(not app.advanced_mode and editor.limb_ik.button_pressed and not limb.is_empty(),"Simple defaults to natural movement for a validated hand chain")
	editor.record_key();editor.frame_model();app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,60)]
	var shots: Array=app.keys.duplicate(true);var original_root: Dictionary=rig.sample_transform(0)
	var neutral: Image=await app.renderer.capture(app.keys,[],0,true)
	app.set_frame(8);editor.tree_items[hand].select(0);editor.operation.select(1);editor.refresh_values();await settled()
	var orientation: Quaternion=rig.bone_transform(hand).basis.get_rotation_quaternion();var history: int=app.history.size()
	var moved: Dictionary=await move_handle(app,0,-0.35)
	check(moved.dragged and not moved.chain.is_empty() and Support.keys(moved.during).size()==1,"actual hand gizmo uses IK as an unkeyed draft until release")
	var error: float=moved.end.distance_to(moved.target)
	print("AUTHORED_HAND_ERROR ",error)
	check(error<0.0001 and rig.bone_transform(hand).origin.distance_to(moved.target)<0.0001,"hand reaches its gizmo target by bending the limb")
	check(absf(rig.bone_transform(hand).basis.get_rotation_quaternion().dot(orientation))>0.9999,"hand world orientation stays stable while its chain bends")
	check(rig.authored_keys().size()==2 and rig.authored_keys()[1].frame==8 and app.history.size()==history+1 and rig.authored_keys()[1].authored_channels.size()==3,"release auto-keys the three changed joints in one Undo step")
	check(rig.sample_transform(8)==original_root and app.keys==shots,"IK does not move the model root or create camera keys")
	var solved: Dictionary=rig.data.duplicate(true);var posed: Image=await app.renderer.capture(app.keys,[],8,true)
	check(posed.get_data()!=neutral.get_data(),"solved joint rotations actually deform the skinned mesh")
	posed.save_png(folder.path_join("posed-hand.png"));neutral.save_png(folder.path_join("neutral-hand.png"))
	await settled();root.get_texture().get_image().save_png(folder.path_join("limb-editor.png"))
	app.undo();check(rig.data==moved.before,"Undo restores the complete preceding FK pose and key list")
	app.redo();check(rig.data==solved and rig.bone_transform(hand).origin.distance_to(moved.target)<0.0001,"Redo restores the same solved pose without rerunning live IK")
	var elbow: Vector3=rig.bone_transform(limb.ids[1]).origin
	editor.reverse_limb_bend()
	check(rig.bone_transform(hand).origin.distance_to(moved.target)<0.0001 and rig.bone_transform(limb.ids[1]).origin.distance_to(elbow)>0.1,"Advanced reverse bend changes the elbow side while keeping the hand in place")
	app.undo();check(rig.data==solved,"reverse bend is one ordinary undoable pose edit")
	var cancelled: Dictionary=await move_handle(app,1,0.15,true)
	check(rig.data==solved and app.history.size()==history+1,"Escape/cancel restores the original hand pose without an extra key")
	var current: Dictionary=rig.data.duplicate(true);var far:=IK.solve(rig,limb,Vector3(10000,10000,10000))
	check(not far.has("error") and far.clamped and rig.data==current,"unreachable targets clamp to limb reach without mutating the live rig")
	var invalid:=IK.solve(rig,limb,Vector3(NAN,0,0))
	check(invalid.has("error") and rig.data==current,"nonfinite targets fail without replacing the pose")
	var skeleton: Skeleton3D=rig.bones[hand].skeleton;var old_scale:=skeleton.scale;skeleton.scale=Vector3(1.1,1,1)
	await move_handle(app,0,-0.1)
	check(rig.data==current and app.history.size()==history+1,"unsupported nonuniform scale reports direct-posing fallback without keys or Undo noise")
	skeleton.scale=old_scale;app.set_frame(8)
	var odd: Dictionary=rig.data.metadata.duplicate(true);rig.data.metadata={"native_parameters":"opaque old metadata"}
	check(not IK.chain(rig,hand).is_empty(),"opaque older metadata does not crash conservative name mapping")
	rig.data.metadata=odd
	app.set_frame(12);editor.limb_ik.button_pressed=false;editor.tree_items[hand].select(0);editor.operation.select(1);editor.refresh_values()
	var direct: Dictionary=await move_handle(app,0,0.1)
	check(direct.chain.is_empty() and rig.authored_keys()[-1].pose[hand].position!=Support.keys(solved)[-1].pose[hand].position,"visible opt-out retains direct per-bone movement")
	app.undo();editor.limb_ik.button_pressed=true;app.set_frame(8)
	app.mode.select(0);app.change_mode(0);app.set_frame(0);app.create_cel(false);Drawing.stroke(Drawing.cel_at(app.layers[1],0).image,Vector2(80,80),Vector2(180,80),5,Color.RED,false);app.changed()
	var wav:=ProjectSettings.globalize_path("res://output/fixtures/voice — тест.wav")
	if FileAccess.file_exists(wav):
		check(app.import_audio(wav).is_empty(),"IK fixture imports independent WAV audio")
		app.audio_clip.start_frame=24;app.audio_clip.gain_db=-6;app.rebuild_audio()
	app.set_frame(8);var expected: Image=await app.renderer.capture(app.keys,app.layers,8,true)
	var project:=folder.path_join("limb.has");app.has_project.save_file(project,"packed");await wait_job(app.has_project)
	app.new_project();app.has_project.open_file(project);await wait_job(app.has_project);rig=app.renderer.world_runtime.instance(id)
	check(rig.authored_keys().size()==2 and rig.bone_transform(hand).origin.distance_to(moved.target)<0.0001,"packed HAS replays solved ordinary pose keys without solver state")
	app.set_frame(8);var reopened: Image=await app.renderer.capture(app.keys,app.layers,8,true)
	var export_error: String=await app.export_movie(folder)
	check(export_error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000009.png")).get_data()==reopened.get_data(),"MP4 uses the same solved pose with independent camera/cel/audio")
	var movie: String=app.last_export_folder.path_join("movie.mp4")
	var leg:=folder.path_join("leg.glb");Fixture.create(leg,true);app.new_project();editor.add_model(leg);rig=app.renderer.active_model();var foot: String=rig.order[2]
	editor.record_key();editor.frame_model();app.set_frame(8);editor.tree_items[foot].select(0);editor.operation.select(1);editor.refresh_values();await settled()
	var foot_move: Dictionary=await move_handle(app,1,0.3)
	check(not foot_move.chain.is_empty() and foot_move.end.distance_to(foot_move.target)<0.0001,"foot gizmo bends its thigh and knee to reach a closer target")
	var fallback:=folder.path_join("unsupported.glb");SceneIO.make_pose_fixture(fallback);app.new_project();editor.add_model(fallback);rig=app.renderer.active_model();var last: String=rig.order[-1]
	editor.frame_model();editor.tree_items[last].select(0);editor.operation.select(1);editor.refresh_values();await settled()
	var free_move: Dictionary=await move_handle(app,0,0.1)
	check(free_move.chain.is_empty() and free_move.end.distance_to(free_move.target)<0.0001,"unrecognized or incomplete rigs retain normal direct bone movement")
	var empty:=folder.path_join("empty.glb");SceneIO.make_empty(empty)
	var parent:=World.object(empty,"group");parent.position=[3,1,-4];parent.scale=1.8
	var q:=Quaternion.from_euler(Vector3(0.2,0.7,0.1));parent.rotation_xyzw=[q.x,q.y,q.z,q.w]
	var child:=World.object(asset);child.id="scaled-child";child.parent_id=parent.id;child.position=[0.5,0.25,0.2];child.scale=0.75
	var grouped:=World.empty();grouped.objects=[parent,child];app.new_project();app.restore_world(grouped);app.world_selection.select_entity(child.id);rig=app.renderer.active_model();hand=rig.order[2]
	editor.frame_model();editor.tree_items[hand].select(0);editor.operation.select(1);editor.space.select(1);editor.refresh_values();await settled()
	var parent_before: Dictionary=app.renderer.world_runtime.instance(parent.id).data.duplicate(true)
	var transformed: Dictionary=await move_handle(app,0,-0.15)
	check(not transformed.chain.is_empty() and transformed.end.distance_to(transformed.target)<0.0001 and app.renderer.world_runtime.instance(parent.id).data==parent_before,"world-axis IK works through a rotated/scaled parent without changing the group")
	editor.space.select(0)
	var native_samples:=[];var native_errors:={}
	for sample in ["pose-smoke/miku-project","source-smoke/source-project","sfm-smoke/project"]:
		var path:=ProjectSettings.globalize_path("res://output/"+sample)
		if not FileAccess.file_exists(path.path_join("project.json")):print("SKIP optional native IK fixture: "+sample);continue
		var loaded: Dictionary=Storage.load_project(path);var row: Dictionary=World.from_project(loaded).objects[-1]
		row=Support.legacy_model(row)
		row.id="native-ik";row.parent_id="";row.start_frame=0;row.format="studio_model_1";row.pose_keys=[];row.pose={};row.draft_frame=0;row.visible=true;row.reference_only=false
		for field in ["animation_clips","visibility_keys","presence_offset"]:row.erase(field)
		app.new_project();var world:=World.empty();world.objects.append(row);app.restore_world(world);app.world_selection.select_entity(row.id);rig=app.renderer.active_model()
		var metadata: Dictionary=rig.data.metadata.duplicate(true);var native_sha:=FileAccess.get_sha256(row.source)
		var native_hand:=""
		for candidate in rig.order:
			var chain:=IK.chain(rig,candidate)
			if chain.get("role","")=="leftHand":native_hand=candidate
		check(not native_hand.is_empty(),"native left hand has a validated chain: "+sample)
		if native_hand.is_empty():continue
		editor.frame_model();app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,60)];editor.record_key();app.set_frame(8)
		editor.tree_items[native_hand].select(0);editor.operation.select(1);editor.refresh_values();await settled()
		var native_limb:=IK.chain(rig,native_hand)
		var root_point: Vector3=rig.bone_transform(native_limb.ids[0]).origin;var tip_point: Vector3=rig.bone_transform(native_hand).origin
		# Use a reachable inward target through the same public solver, then commit as an authored pose.
		var target: Vector3=root_point+(tip_point-root_point)*0.8
		var before_native: Dictionary=rig.data.duplicate(true);editor.begin_draft();editor.apply_frame()
		var result:=IK.solve(rig,native_limb,target)
		check(not result.has("error"),"native limb solver produces a result: "+sample)
		if result.has("error"):continue
		rig.data.pose=result.pose;editor.commit(before_native,true)
		var native_error: float=rig.bone_transform(native_hand).origin.distance_to(result.target);native_errors[sample]=native_error
		print("NATIVE_IK_ERROR ",sample," ",native_error)
		check(native_error<0.001 and rig.authored_keys().size()==2,"native hand reaches target and auto-keys: "+sample)
		app.undo();var undone: bool=rig.data==before_native;app.redo()
		check(undone and rig.data.metadata==metadata and FileAccess.get_sha256(row.source)==native_sha,"native IK Undo, metadata and source bytes stay intact: "+sample)
		var native_foot:=""
		for candidate in rig.order:
			if IK.chain(rig,candidate).get("role","")=="leftFoot":native_foot=candidate
		check(not native_foot.is_empty(),"native left foot has a validated chain: "+sample)
		check(editor.tree_items[native_hand].get_text(0)=="Left hand" and (native_foot.is_empty() or editor.tree_items[native_foot].get_text(0)=="Left foot"),"native hand and foot use Simple body names: "+sample)
		if not native_foot.is_empty():
			app.set_frame(16);var leg_chain:=IK.chain(rig,native_foot)
			var a: Vector3=rig.bone_transform(leg_chain.ids[0]).origin;var c: Vector3=rig.bone_transform(native_foot).origin
			var before_foot: Dictionary=rig.data.duplicate(true);var kept_hand: Vector3=rig.bone_transform(native_hand).origin
			editor.begin_draft();editor.apply_frame();var foot_result:=IK.solve(rig,leg_chain,a+(c-a)*0.8)
			if not foot_result.has("error"):rig.data.pose=foot_result.pose;editor.commit(before_foot,true)
			check(not foot_result.has("error") and rig.bone_transform(native_foot).origin.distance_to(foot_result.target)<0.001 and rig.bone_transform(native_hand).origin.distance_to(kept_hand)<0.0001,"native foot reaches target without changing the authored hand: "+sample)
		var native_pose: Dictionary=rig.data.duplicate(true);var native_hand_end: Vector3=rig.bone_transform(native_hand).origin
		var saved:=folder.path_join("native-%d.has" % native_samples.size());app.has_project.save_file(saved,"packed");await wait_job(app.has_project)
		app.new_project();app.has_project.open_file(saved);await wait_job(app.has_project);rig=app.renderer.world_runtime.instance(row.id)
		check(Support.same_keys(rig.data,native_pose) and rig.bone_transform(native_hand).origin.distance_to(native_hand_end)<0.001,"native solved keys and bindings survive packed HAS: "+sample)
		native_samples.append(sample)
	var vrm_samples:=[]
	for name in ["AvatarSample_A.vrm","AvatarSample_Avrm0.vrm"]:
		var path: String=preload("res://tests/native_sample_paths.gd").vrm(name)
		if not FileAccess.file_exists(path):print("SKIP optional VRM IK sample: "+name);continue
		var original:=FileAccess.get_sha256(path);close_warnings(app);app.new_project();editor.add_model(path);await wait_job(app.source_import);close_warnings(app);await settled();rig=app.renderer.active_model()
		check(rig!=null,"VRM imports through ordinary model preparation for IK: "+name)
		if not rig:continue
		var tip:=""
		for candidate in rig.order:
			var mapped:=IK.chain(rig,candidate)
			if mapped.get("role","")=="leftHand" and mapped.declared:tip=candidate
		check(not tip.is_empty(),"VRM declared humanoid map identifies its hand chain: "+name)
		if tip.is_empty():continue
		check(editor.tree_items[tip].get_text(0)=="Left hand","native VRM declared hand has a Simple body name: "+name)
		editor.record_key();app.set_frame(8);editor.begin_draft();editor.apply_frame()
		var mapped:=IK.chain(rig,tip);var a: Vector3=rig.bone_transform(mapped.ids[0]).origin;var c: Vector3=rig.bone_transform(tip).origin
		var vrm_before: Dictionary=rig.data.duplicate(true);var result:=IK.solve(rig,mapped,a+(c-a)*0.8)
		if not result.has("error"):rig.data.pose=result.pose;editor.commit(vrm_before,true)
		check(not result.has("error") and rig.bone_transform(tip).origin.distance_to(result.target)<0.001 and FileAccess.get_sha256(path)==original,"VRM hand reaches target and original source stays unchanged: "+name)
		var saved:=folder.path_join("vrm-%d.has" % vrm_samples.size());var actor_id: String=rig.data.id;var endpoint: Vector3=rig.bone_transform(tip).origin
		app.has_project.save_file(saved,"packed");await wait_job(app.has_project);app.new_project();app.has_project.open_file(saved);await wait_job(app.has_project);rig=app.renderer.world_runtime.instance(actor_id)
		check(rig.bone_transform(tip).origin.distance_to(endpoint)<0.001 and IK.chain(rig,tip).declared,"VRM declared mapping and solved pose survive packed reopen: "+name)
		vrm_samples.append(name)
	check(FileAccess.get_sha256(asset)==digest,"IK never rewrites the source GLB")
	var report:={"checks":checks,"failures":failures,"folder":folder,"project":project,"movie":movie,"hand_error":error,"native_samples":native_samples,"native_errors":native_errors,"vrm_samples":vrm_samples}
	var file:=FileAccess.open(ProjectSettings.globalize_path("res://output/limb-ik-result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(report));file.close()
	print("LIMB_IK "+JSON.stringify(report));app.queue_free();await process_frame;quit(0 if failures==0 else 1)
