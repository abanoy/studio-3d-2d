extends SceneTree
const Model=preload("res://src/model.gd")
const Drawing=preload("res://src/drawing.gd")
const Timeline=preload("res://src/timeline.gd")
var app
var helper
var folder: String
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(160).timeout.connect(func():push_error("Batch helper watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settle() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func ready(job=null) -> void:
	if job:
		while job.pid>0:await process_frame
	else:
		while helper.pid>0 or helper.point_review_after>0:await process_frame
	await settle()
func index_for(node: int,primitive: int,component: int) -> int:
	for i in range(helper.assessment.get("regions",[]).size()):
		var row: Dictionary=helper.assessment.regions[i]
		if int(row.node)==node and int(row.primitive)==primitive and int(row.component)==component:return i
	return -1
func choose(index: int) -> void:
	helper.parts.select(index);helper.parts.item_selected.emit(index);await ready()
func corrected(values: Array) -> void:
	helper.point_choice.select(1);helper.point_values()
	for axis in range(3):helper.fields[axis].value=values[axis]
	await ready()
func lower_patch() -> void:
	helper.patch_toggle.button_pressed=true;helper.draw_preview();var lower:=Vector2(INF,INF);var upper:=Vector2(-INF,-INF)
	for i in range(8,20):lower=lower.min(helper.projected_vertices[i]);upper=upper.max(helper.projected_vertices[i])
	helper.box_start=lower-Vector2(3,3);helper.box_end=upper+Vector2(3,3);helper.box_dragging=true;helper.finish_patch_box()
	check(helper.apply_button.disabled and helper.include_status.text.contains("needs review"),"a checked patch edit invalidates only that saved item during review")
	await ready()
func close_pixels(a: Image,b: Image) -> bool:
	var aa:=a.get_data();var bb:=b.get_data();var changed:=0;var total:=0
	for i in range(aa.size()):
		if aa[i]!=bb[i]:changed+=1;total+=absi(int(aa[i])-int(bb[i]))
	return changed<=384 and float(total)/aa.size()<.002
func worker_running(pid: int) -> bool:
	return FileAccess.file_exists("/proc/%d/stat"%pid) if OS.get_name()=="Linux" else OS.is_process_running(pid)
func run() -> void:
	var args:=OS.get_cmdline_user_args();folder=args[0];var source: String=args[1];var shared: String=args[2];var bad: String=args[3];var wav: String=args[4]
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recent.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	app.append_object(Model.definition(source),"model");await settle();var actor: RefCounted=app.renderer.active_model();var id: String=actor.data.id
	var head: String=actor.root.get_meta("has_source_bones",{}).get(2,"");var q:=Quaternion(Vector3.UP,.17)
	actor.data.pose[head]={"position":[0,0,0],"rotation_xyzw":[q.x,q.y,q.z,q.w]};app.pose_editor.apply_frame()
	app.renderer.camera.position=Vector3(0,1.2,4);app.renderer.camera.look_at(Vector3(0,1.1,0));app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,48)]
	Drawing.insert(app.layers[1],0,48,Drawing.blank(1920,1080));Drawing.edit_image(Drawing.cel_at(app.layers[1],0)).image.set_pixel(80,80,Color.CYAN)
	check(app.import_audio(wav).is_empty(),"batch scene keeps ordinary independent audio")
	app.audio_start.value=24;app.apply_audio_settings();app.changed();await settle()
	var original: Dictionary=actor.data.duplicate(true);var world: Dictionary=app.current_world().duplicate(true);var history: int=app.history.size();var shots: Array=app.keys.duplicate(true);var paint:=Drawing.image(Drawing.cel_at(app.layers[1],0)).get_data();var sha:=FileAccess.get_sha256(source)
	var before: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	helper=app.physics_editor.helper_editor;helper.open();await ready()
	var first:=index_for(3,1,0);var second:=index_for(3,1,1)
	check(first>=0 and second>=0 and helper.included.is_empty() and not helper.include_toggle.button_pressed and not helper.apply_button.disabled,"opening preserves the original single-part workflow without checking anything")
	await choose(first);helper.include_toggle.button_pressed=true;await ready()
	check(helper.included.size()==1 and helper.include_toggle.button_pressed and helper.include_status.text.contains("reviewed"),"visible Include in setup checks one reviewed part")
	app.set_advanced(true);helper.point_choice.select(1);helper.point_values()
	var original_x: float=helper.fields[0].value;var original_step: float=helper.fields[0].step;var precise_x:=98765.43210987654
	var old_transport: float=JSON.parse_string(JSON.stringify({"x":precise_x})).x
	helper.fields[0].step=0.;helper.fields[0].value=precise_x;await ready()
	var precision_transport:={"expected":precise_x,"old_default":old_transport,"actual":helper.request.points_in_anchor[1][0],"old_absolute_loss":absf(precise_x-old_transport)}
	check(absf(precise_x-old_transport)>1e-12 and helper.request.points_in_anchor[1][0]==precise_x and helper.included.values()[0].request.points_in_anchor[1][0]==precise_x,"a deliberate high-precision correction keeps digits that default JSON transport loses")
	helper.fields[0].value=original_x;helper.fields[0].step=original_step;await ready();helper.fields[0].value+=.025
	check(helper.apply_button.disabled and helper.include_status.text.contains("needs review"),"editing a checked point invalidates its saved plan immediately")
	await ready();var first_points: Array=helper.request.points_in_anchor.duplicate(true)
	check(not helper.apply_button.disabled and helper.include_status.text.contains("reviewed"),"matching corrected-point review restores a usable checked plan")
	await choose(second)
	check(helper.included.size()==1 and not helper.include_toggle.button_pressed,"focusing another part preserves the first check and keeps the new focus separate")
	helper.point_choice.select(1);helper.point_values();helper.fields[0].value-=.035;var second_points: Array=helper.request.points_in_anchor.duplicate(true)
	helper.include_toggle.button_pressed=true;await ready()
	check(helper.included.size()==2 and helper.apply_button.text=="Set up 2 checked parts" and not helper.apply_button.disabled,"two independent checks produce an explicit two-part Apply")
	await choose(first)
	check(helper.request.points_in_anchor==first_points and helper.included.size()==2,"revisiting a checked part restores its own corrected joint points")
	await lower_patch();helper.point_choice.select(1);helper.point_values();helper.fields[0].value+=.02;await ready();first_points=helper.request.points_in_anchor.duplicate(true)
	await choose(second);await choose(first)
	check(helper.request.vertex_mask==range(8,20) and helper.patch_toggle.button_pressed and helper.request.points_in_anchor==first_points,"a checked part restores both its precise patch and its revised joint correction")
	var folded: Array=first_points[0].duplicate();await corrected(folded)
	check(helper.apply_button.disabled and helper.include_status.text.contains("needs review") and helper.included.size()==2,"a refused folded chain keeps both checks and blocks the whole batch")
	await corrected(first_points[1]);check(not helper.apply_button.disabled,"correcting the invalid checked item recovers without losing the other plan")
	await choose(second)
	if helper.request.points_in_anchor!=second_points:print("POINTS_EXPECTED_ACTUAL "+JSON.stringify({"expected":second_points,"actual":helper.request.points_in_anchor},"",true,true))
	check(helper.request.points_in_anchor==second_points,"a different part retains its separate correction after another part fails review")
	var space:=InputEventKey.new();space.keycode=KEY_SPACE;space.physical_keycode=KEY_SPACE;space.pressed=true;helper.parts.grab_focus();helper.window.push_input(space,true);await ready()
	check(helper.included.size()==1 and not helper.include_toggle.button_pressed and not app.playing,"routed Space on the focused list row unchecks membership without starting playback")
	helper.parts.grab_focus();helper.window.push_input(space,true);await ready();app.navigating=true;helper.window.push_input(space,true);app.navigating=false
	check(helper.included.size()==2 and helper.include_toggle.button_pressed and not app.playing,"routed Space rechecks the row and remains inactive during camera navigation")
	check(app.current_world()==world and app.history.size()==history and app.keys==shots and actor.data==original,"all checking, refinement and recovery author no scene, pose, keys or history")
	# Exercise the actual ordinary import preflight with a complete but broken
	# private candidate. No installed runtime or Undo entry may be replaced.
	var runtime=app.renderer.world_runtime
	var report:={"format":"studio_generated_helpers_1","source_sha256":sha,"changed_vertices":1}
	helper.install({"glb":bad,"report":report,"reports":[report,report],"batch":{"source_sha256":sha,"source_stamp_ns":helper.assessment.source_stamp_ns,"final_sha256":FileAccess.get_sha256(bad)}})
	await settle()
	check(app.renderer.world_runtime==runtime and app.current_world()==world and app.history.size()==history and helper.included.size()==2 and helper.info.text.contains("could not preserve"),"candidate import failure leaves the installed world, checked plans and history intact")
	helper.window.get_texture().get_image().save_png(folder.path_join("review.png"))
	helper.apply_button.pressed.emit();await ready();actor=app.renderer.world_runtime.instance(id)
	check(not is_instance_valid(helper.window) and actor.root.get_meta("has_secondary_rig",{}).get("chains",[]).size()==2 and app.history.size()==history+1,"one batch Apply installs both usable chains as exactly one Undo edit")
	var derived: Dictionary=actor.data.duplicate(true)
	check(actor.data.pose==original.pose and actor.data.pose_keys==original.pose_keys and actor.data.metadata.generated_helper_history.size()==2,"batch setup preserves the authored pose and appends both individual reports")
	check(actor.data.metadata.generated_helpers==actor.data.metadata.generated_helper_history[-1] and actor.data.metadata.generated_helper_history[0].source_sha256==sha and actor.data.metadata.generated_helper_history[1].source_sha256!=sha,"single-report compatibility and actual intermediate provenance are retained")
	check(close_pixels(before,await app.renderer.capture(app.keys,app.layers,0,true)),"combined helpers preserve the original non-rest rendered appearance")
	app.undo();await settle();check(app.renderer.world_runtime.instance(id).data==original,"one Undo removes the whole multi-part setup")
	app.redo();await settle();actor=app.renderer.world_runtime.instance(id);check(actor.data==derived,"one Redo restores both reviewed parts and their individual history")
	app.world_selection.select_entity(id,false);app.physics_editor.hair_toggle.button_pressed=true
	while app.physics_editor.pending.has(id):await process_frame
	var definition: Dictionary=actor.root.get_meta("has_secondary_rig");var expected: Array=definition.chains.map(func(chain):return chain.joints.slice(0,chain.joints.size()-1).map(func(joint):return joint.binding.id))
	var actual: Array=app.physics_editor.simulations[id].runner.chains.map(func(chain):return chain.ids) if app.physics_editor.active(id) else []
	check(expected.size()==2 and actual==expected,"both expected generated joint chains start through ordinary Hair & clothes")
	for i in range(30):await physics_frame
	app.physics_editor.hair_toggle.button_pressed=false;await settle()
	check(not app.physics_editor.active(id) and actor.data==derived,"previewing both chains and switching off keeps authored data exact")
	app.has_project.save_file(folder.path_join("two-parts.has"),"packed");await ready(app.has_project)
	check(not app.has_project.path.is_empty() and not app.dirty,"normal Save packs the complete combined setup")
	app.new_project();app.has_project.open_file(folder.path_join("two-parts.has"));await ready(app.has_project);actor=app.renderer.world_runtime.instance(id)
	check(actor!=null and actor.root.get_meta("has_secondary_rig").chains.size()==2 and actor.data.metadata.generated_helper_history.size()==2,"packed reopening retains both chains and both provenance reports")
	var saved_keys: Array=JSON.parse_string(JSON.stringify(shots,"",true,true))
	check(JSON.stringify(app.keys)==JSON.stringify(saved_keys) and Drawing.image(Drawing.cel_at(app.layers[1],0)).get_data()==paint and app.audio_clips.size()==1,"combined setup reopening retains camera keys through their existing JSON contract, independent drawing and audio")
	var error: String=await app.export_movie(folder);check(error.is_empty(),"combined setup produces a real encoded movie")
	var movie: String=app.last_finished_movie
	# A real second-item backend refusal after one private step has succeeded.
	app.new_project();app.append_object(Model.definition(shared),"model");await settle();actor=app.renderer.active_model();var shared_world: Dictionary=app.current_world().duplicate(true);var shared_history: int=app.history.size()
	helper.open();await ready();await choose(index_for(3,1,0));helper.include_toggle.button_pressed=true;await ready();await choose(index_for(4,0,0));helper.include_toggle.button_pressed=true;await ready()
	check(helper.included.size()==2 and not helper.apply_button.disabled,"both individually reviewed items remain selected before the shared-instance build guard")
	helper.apply_button.pressed.emit();await ready()
	check(helper.info.text.contains("shared by multiple source nodes") and app.current_world()==shared_world and app.history.size()==shared_history and helper.included.size()==2,"real later-item failure installs neither part and retains the checked plans")
	helper.apply_button.pressed.emit();var owned: int=helper.pid;helper.close();await settle()
	check(owned>0 and not worker_running(owned) and app.current_world()==shared_world and app.history.size()==shared_history,"Cancel stops an owned batch worker without authoring a partial setup")
	check(FileAccess.get_sha256(source)==sha,"the original source is unchanged through checking, failure, Undo, Save and movie export")
	var result:={"checks":checks,"failures":failures,"movie":movie,"source_sha256":sha,"derived_sha256":derived.sha256,"precision_transport":precision_transport}
	FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE).store_string(JSON.stringify(result,"",true,true));print("SECONDARY_BATCH "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
