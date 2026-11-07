extends SceneTree
# Real review controls plus derived weighted geometry/fan/Record/HAS/movie path.
const Model=preload("res://src/model.gd")
const Timeline=preload("res://src/timeline.gd")
const Drawing=preload("res://src/drawing.gd")
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(120).timeout.connect(func():push_error("Helper smoke watchdog expired");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settled() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func wait_job(job) -> void:
	while job.pid>0:await process_frame
	await settled()
func pixels(a: Image,b: Image) -> Dictionary:
	var aa:=a.get_data();var bb:=b.get_data();var changed:=0;var total:=0
	for i in range(aa.size()):
		if aa[i]!=bb[i]:changed+=1;total+=absi(int(aa[i])-int(bb[i]))
	return {"changed":changed,"mean":float(total)/aa.size()}
func wait_review(editor) -> void:
	while editor.pid>0:await process_frame
	await settled()
func review(app,folder: String) -> bool:
	var helper=app.physics_editor.helper_editor;var actor: RefCounted=app.renderer.active_model();var before: Dictionary=actor.data.duplicate(true);var history: int=app.history.size()
	helper.button.pressed.emit();var worker: int=helper.pid;helper.close();await settled()
	check(worker>0 and not OS.is_process_running(worker) and actor.data==before and app.history.size()==history,"Cancel stops the owned inspection worker without editing the model")
	helper.button.pressed.emit();await wait_review(helper)
	check(not helper.preview.is_empty() and helper.parts.item_count==3 and not helper.apply_button.disabled,"normal loose-part action offers connected regions and a usable preview")
	if helper.preview.is_empty():return false
	check(int(helper.preview.region.primitive)==1 and int(helper.preview.region.component)==0 and int(helper.request.anchor_node)==2,"suggested strand uses geometry/weights and avoids the existing body-joint region")
	check(int(helper.preview.region.attachment_vertices)==2 and helper.anchors.is_item_disabled(0) and not helper.anchors.is_item_disabled(1),"review reports the pinned attachment seam and disables unweighted attachments")
	check(app.canvas.review_lines.size()>0 and app.canvas.review_chain.size()==4 and actor.data==before and app.history.size()==history,"review draws the selected skinned region and proposed joints without edits or keys")
	var a: Image=await app.renderer.capture(app.keys,app.layers,app.frame,true);helper.clear_preview();var b: Image=await app.renderer.capture(app.keys,app.layers,app.frame,true)
	check(a.get_data()==b.get_data(),"review wires and joints are editor-only and absent from final capture")
	helper.draw_preview();app.set_advanced(true);await settled();var old: Array=helper.request.points_in_anchor.duplicate(true)
	helper.point_choice.select(1);helper.point_values();helper.fields[0].value+=0.05;await settled()
	check(helper.details.visible and helper.request.points_in_anchor!=old and actor.data==before,"Advanced joint correction changes the preview while retaining original model data")
	helper.scroll.ensure_control_visible(helper.fields[0]);await settled()
	check(helper.apply_button.get_global_rect().end.y<=helper.window.size.y and helper.fields[0].get_global_rect().end.y<=helper.scroll.get_global_rect().end.y+1,"review Apply stays accessible and precision fields scroll into view")
	helper.window.get_texture().get_image().save_png(folder.path_join("review-window.png"));root.get_texture().get_image().save_png(folder.path_join("review-editor.png"))
	app.set_advanced(false);await settled();check(not helper.details.visible and helper.request.points_in_anchor!=old,"Simple hides precision fields while retaining reviewed joint corrections")
	helper.apply_button.pressed.emit();await wait_review(helper)
	actor=app.renderer.active_model()
	check(not is_instance_valid(helper.window) and actor.order.size()==6 and actor.data.metadata.has("generated_helpers") and app.history.size()==history+1,"Apply installs one immutable weighted asset revision as one Undo step")
	check(actor.data.pose_keys==before.pose_keys and actor.data.pose==before.pose and actor.data.id==before.id,"reviewed generation preserves existing identity, pose keys and manual pose")
	return actor.order.size()==6
func lifecycle(app,original: String) -> void:
	app.new_project();app.append_object(Model.definition(original),"model");var helper=app.physics_editor.helper_editor
	helper.button.pressed.emit();await wait_review(helper)
	var actor: RefCounted=app.renderer.active_model();var sha: String=actor.data.sha256;var history: int=app.history.size()
	helper.apply_button.pressed.emit();actor.data.metadata["owner_edit"]="keep this edit";app.changed();await wait_review(helper)
	check(not is_instance_valid(helper.window) and actor.data.sha256==sha and actor.data.metadata.owner_edit=="keep this edit" and app.history.size()==history,"edits made during preparation cancel installation without losing current work")
	helper.button.pressed.emit();var worker: int=helper.pid;app.new_project();await settled()
	check(worker>0 and not OS.is_process_running(worker) and not is_instance_valid(helper.window) and app.renderer.world_runtime.order.is_empty() and app.canvas.review_lines.is_empty(),"New cancels an owned helper worker and clears its preview safely")
func mixed_weights(app,source: String,derived: String) -> void:
	app.new_project();app.append_object(Model.definition(source),"model");var id: String=app.last_import_id
	app.renderer.camera.position=Vector3(0,1.2,4);app.renderer.camera.look_at(Vector3(0,1.1,0));app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,48)]
	var reference: Image=await app.renderer.capture(app.keys,app.layers,0,true);var world: Dictionary=app.renderer.world_state();world.objects[0].source=derived;world.objects[0].sha256=FileAccess.get_sha256(derived)
	var error: String=app.restore_world(world);check(error.is_empty(),"mixed-weight generated rig loads through the ordinary model contract")
	if not error.is_empty():return
	var actor: RefCounted=app.renderer.world_runtime.instance(id);var neutral: Image=await app.renderer.capture(app.keys,app.layers,0,true);var delta:=pixels(reference,neutral)
	check(delta.changed<=384 and delta.mean<0.002,"actual eight-weight shader retains the mixed original bind appearance")
	var definition: Dictionary=actor.root.get_meta("has_secondary_rig");var bone: String=definition.chains[0].joints[1].binding.id;var q:=Quaternion(Vector3.BACK,.4)
	actor.data.pose[bone]={"position":[0,0,0],"rotation_xyzw":[q.x,q.y,q.z,q.w]}
	check(pixels(neutral,await app.renderer.capture(app.keys,app.layers,0,true)).changed>100,"actual eight-weight skin deforms under a generated joint")
func run() -> void:
	var args:=OS.get_cmdline_user_args();var original: String=args[0];var derived: String=args[1];var folder: String=args[2];var wav: String=args[3]
	var sha:=FileAccess.get_sha256(original);var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled()
	app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	app.append_object(Model.definition(original),"model");var id: String=app.last_import_id;var actor: RefCounted=app.renderer.active_model();var original_ids: Array=actor.order.duplicate();var head:=""
	for bone in actor.order:
		if actor.bones[bone].name=="Head":head=bone
	check(not head.is_empty() and actor.order.size()==2,"authored original imports with its two existing joints")
	if head.is_empty():app.free();quit(1);return
	var q:=Quaternion(Vector3.FORWARD,0.15)
	actor.data.pose_keys=[{"frame":0,"pose":{},"transform":{"position":[0,0,0],"rotation_xyzw":[0,0,0,1],"scale":1},"interpolation":"ease"},{"frame":48,"pose":{head:{"position":[0,0,0],"rotation_xyzw":[q.x,q.y,q.z,q.w]}},"transform":{"position":[0,0,0],"rotation_xyzw":[0,0,0,1],"scale":1},"interpolation":"ease"}]
	app.renderer.camera.position=Vector3(0,1.2,4);app.renderer.camera.look_at(Vector3(0,1.1,0));app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,48)]
	app.set_frame(24);var before: Image=await app.renderer.capture(app.keys,app.layers,24,true)
	if not await review(app,folder):app.free();quit(1);return
	var error: String="";app.set_frame(24);actor=app.renderer.world_runtime.instance(id)
	check(actor.order.size()==6 and original_ids.all(func(bone):return actor.bones.has(bone)),"generated weighted joints append without renaming original bones")
	var same: Image=await app.renderer.capture(app.keys,app.layers,24,true);var delta:=pixels(before,same)
	check(delta.changed<=384 and delta.mean<0.002,"original animated bind appearance survives derived skin at the same frame")
	var definition: Dictionary=actor.root.get_meta("has_secondary_rig");check(definition.error.is_empty() and definition.chains.size()==1 and definition.chains[0].joints.size()==4,"generated helpers enter the same standard secondary-rig adapter")
	app.world_selection.select_entity(id,false);app.mode.select(2);app.change_mode(2);var editor=app.pose_editor
	editor.selected=definition.chains[0].joints[1].binding.id;editor.operation.select(0);editor.refresh_values();editor.fields[2].value=25;editor.apply_numeric();await settled()
	var bent: Image=await app.renderer.capture(app.keys,app.layers,24,true)
	check(pixels(same,bent).changed>100,"rotating an added helper visibly deforms actual textured geometry")
	var crop:=Rect2i(0,0,960,1080)
	check(same.get_region(crop).get_data()==bent.get_region(crop).get_data(),"unselected body and separate side patch retain their rendered pixels")
	app.undo();check((await app.renderer.capture(app.keys,app.layers,24,true)).get_data()==same.get_data(),"ordinary pose Undo restores weighted-helper deformation exactly")
	app.undo();actor=app.renderer.world_runtime.instance(id)
	check(actor.order==original_ids and actor.data.sha256==sha,"whole-world Undo restores the original asset and animation")
	app.redo();app.set_frame(0);actor=app.renderer.world_runtime.instance(id)
	check(actor.order.size()==6 and not actor.data.pose_keys.is_empty(),"whole-world Redo restores the derived native asset with prior animation")
	app.physics_editor.fan_editor.add_fan();var fan: RefCounted=app.renderer.active_model();fan.data.position=[0.4,1.15,-1.5];fan.data.rotation_xyzw=[0,0,0,1];fan.data.metadata.airflow.speed=10;fan.apply(0)
	app.world_selection.select_entity(id,false);actor=app.renderer.world_runtime.instance(id);app.mode.select(2);app.change_mode(2)
	var physics=app.physics_editor;physics.hair_toggle.button_pressed=true
	while physics.pending.has(id):await process_frame
	await settled();check(physics.active(id) and physics.hair_toggle.button_pressed,"normal Hair & clothes accepts the generated weighted chain")
	if not physics.active(id):app.free();quit(1);return
	for i in range(120):await physics_frame
	var live: Dictionary=physics.simulations[id].pose();var sway:=0.0
	for bone in live:
		if not bone in original_ids:sway=maxf(sway,Timeline.quaternion(live[bone].rotation_xyzw).angle_to(Quaternion.IDENTITY))
	check(sway>0.03,"generated weighted region responds to the ordinary local fan")
	var record=physics.recording;record.scope.select(0);record.button.pressed.emit()
	while record.active:await process_frame
	actor=app.renderer.world_runtime.instance(id)
	check(record.last_error.is_empty() and actor.authored_keys().size()==49,"normal Local Record captures an editable generated-helper take")
	Drawing.insert(app.layers[1],0,48,Drawing.blank(1920,1080));Drawing.edit_image(Drawing.cel_at(app.layers[1],0)).image.set_pixel(80,80,Color.CYAN)
	check(app.import_audio(wav).is_empty(),"independent audio remains usable with derived assets")
	app.audio_start.value=24;app.audio_gain.value=-6;app.apply_audio_settings();app.set_frame(24)
	var state: Dictionary=actor.sample(24);var project:=folder.path_join("helpers.has");app.has_project.save_file(project,"packed");await wait_job(app.has_project)
	app.new_project();app.has_project.open_file(project);await wait_job(app.has_project);actor=app.renderer.world_runtime.instance(id)
	check(actor!=null and actor.order.size()==6 and JSON.stringify(actor.sample(24))==JSON.stringify(state),"packed HAS reopens the actual weighted rig and recorded motion")
	definition=actor.root.get_meta("has_secondary_rig");check(definition.chains.size()==1,"packed geometry retains the generated chain descriptor")
	check(actor.data.metadata.generated_helpers.source_sha256==sha,"packed HAS retains derived-asset source provenance")
	app.world_selection.select_entity(id,false);await settled()
	check(not app.physics_editor.helper_editor.button.disabled,"models with existing chains can review other unrigged parts")
	var helper=app.physics_editor.helper_editor;helper.button.pressed.emit();await wait_review(helper)
	check(helper.parts.is_item_disabled(1) and not helper.parts.is_item_disabled(0),"existing weighted spring region is protected while other connected regions remain available")
	helper.close();await settled()
	var labeled:=false
	for bone in actor.order:
		if actor.bones[bone].name.begins_with("__HAS_Loose_"):labeled=labeled or app.pose_editor.tree_items[bone].get_text(0).begins_with("Loose joint")
	check(labeled,"Simple gives generated joints usable names while retaining internal binding IDs")
	var reference: Image=await app.renderer.capture(app.keys,app.layers,24,true);reference.save_png(folder.path_join("recorded-reference.png"))
	app.set_frame(3);app.set_frame(40);app.set_frame(24)
	check((await app.renderer.capture(app.keys,app.layers,24,true)).get_data()==reference.get_data(),"generated-helper recording seeks reproducibly without a live solver")
	app.world_selection.select_entity(id,false);await settled();root.get_texture().get_image().save_png(folder.path_join("derived-editor.png"))
	error=await app.export_movie(folder)
	check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000025.png")).get_data()==reference.get_data(),"derived weighted motion exports with exact reopened preview pixels")
	check(FileAccess.get_sha256(original)==sha,"original GLB stays unchanged through authoring, Undo, recording and export")
	var movie: String=app.last_export_folder.path_join("movie.mp4");var linked:=folder.path_join("helpers-linked.has");app.has_project.save_file(linked,"linked");await wait_job(app.has_project)
	app.new_project();app.has_project.open_file(linked);await wait_job(app.has_project);actor=app.renderer.world_runtime.instance(id)
	check(actor.order.size()==6 and actor.data.metadata.generated_helpers.source_sha256==sha and JSON.stringify(actor.sample(24))==JSON.stringify(state),"linked HAS retains weighted geometry, source provenance and the editable take")
	await lifecycle(app,original)
	await mixed_weights(app,args[4],args[5])
	var result:={"checks":checks,"failures":failures,"folder":folder,"movie":movie,"bind_difference":delta,"sway_radians":sway}
	var f:=FileAccess.open("res://output/secondary-helpers-result.json",FileAccess.WRITE);f.store_string(JSON.stringify(result));f.close();print("SECONDARY_HELPERS "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
