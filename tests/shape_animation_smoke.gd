extends SceneTree
const Model=preload("res://src/model.gd")
const A=Model.ShapeAnimation
const Shape=Model.Shape
const Timeline=Model.Timeline
const Drawing=preload("res://src/drawing.gd")
const Channels=preload("res://src/animated_channels.gd")
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(180).timeout.connect(func():push_error("Animated shapes watchdog");quit(2));call_deferred("run")
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func settled() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func wait_job(job) -> void:
	while job.pid>0:await process_frame
	await settled()
func value(actor,index:=0) -> float:return float(actor.root.get_meta(Shape.META).rows[0].mesh.get_blend_shape_value(index))
func close_value(a: float,b: float) -> bool:return absf(a-b)<.00001
func choose(editor,index: int) -> void:
	for i in range(editor.shapes.item_count):
		if int(editor.shapes.get_item_metadata(i))==index:editor.shapes.select(i);editor.shapes.item_selected.emit(i);return
func edit(app,amount: float,index:=0) -> void:
	var editor=app.pose_editor.animated_shapes;choose(editor,index);editor.amount.value=amount;editor.apply_button.pressed.emit()
func cache_error(actor) -> float:
	var error:=0.0
	for row in actor.root.get_meta(Shape.META).rows:
		var baked: ArrayMesh=row.mesh.bake_mesh_from_current_blend_shape_mix()
		for surface in range(baked.get_surface_count()):
			var positions: PackedVector3Array=baked.surface_get_arrays(surface)[Mesh.ARRAY_VERTEX]
			var cpu:=Shape.vertices(row.mesh,surface,row.mesh.mesh.surface_get_arrays(surface)[Mesh.ARRAY_VERTEX])
			for v in range(positions.size()):error=maxf(error,positions[v].distance_to(cpu[v]))
	return error
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0];var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled()
	app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	app.pose_editor.add_model(folder.path_join("shape.glb"));var actor: RefCounted=app.renderer.active_model();var id: String=actor.data.id
	var original: Dictionary=actor.data.duplicate(true);var native_ids: Array=actor.order.duplicate();var camera_keys: Array=app.keys.duplicate(true)
	app.pose_editor.shape_button.pressed.emit();await settled()
	check(not app.advanced_mode and app.pose_editor.shape_window.visible and app.pose_editor.animated_shapes.panel.is_visible_in_tree(),"shape animation is available from Simple")
	check(Rect2(Vector2.ZERO,Vector2(app.pose_editor.shape_window.size)).encloses(app.pose_editor.shape_close.get_global_rect()),"shape window keeps its Close action inside the visible window")
	app.pose_editor.interpolation.select(1)
	var history: int=app.history.size();edit(app,.2);await settled()
	check(actor.data.format==A.FORMAT and close_value(value(actor),.2) and app.history.size()==history+1,"Simple Apply creates one version5 shape edit and one Undo")
	check(actor.authored_keys().is_empty() and actor.authored_shape_keys().size()==1 and actor.authored_shape_keys()[0].frame==0 and actor.data.pose==original.pose and app.keys==camera_keys,"shape auto-key preserves bones and explicit camera keys")
	app.undo();await settled();check(actor.data==original and close_value(value(actor),.6),"Undo removes the first expression and restores original defaults")
	app.redo();await settled();check(close_value(value(actor),.2),"Redo restores the expression")
	app.set_frame(24);edit(app,.8);await settled();app.set_frame(12);await settled()
	check(close_value(value(actor),.5),"actual GPU interpolates a shape at the master frame")
	var geometry_error:=cache_error(actor);check(geometry_error<.00001,"on-demand collision vertices match actual animated GPU geometry")
	app.pose_editor.frame_model();app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,55)]
	var middle: Image=await app.renderer.capture(app.keys,app.layers,12,true)
	app.set_frame(0);var start: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	app.set_frame(24);var end: Image=await app.renderer.capture(app.keys,app.layers,24,true)
	check(start.get_data()!=middle.get_data() and middle.get_data()!=end.get_data(),"three timeline samples show actual expression motion")
	var motion: Dictionary=actor.data.duplicate(true)
	app.set_frame(12);app.pose_editor.begin_draft();app.pose_editor.commit(actor.data.duplicate(true),true)
	check(close_value(value(actor),.5),"bone draft preparation retains the sampled expression")
	var split:=Model.Clips.split(actor.data,12);check(not split.has("error"),"expression take can split")
	app.pose_editor.restore_state(split.data);var moved:=Model.Clips.move(actor.data,split.right_id,24,48);app.pose_editor.restore_state(moved.data);app.set_frame(30);await settled()
	check(close_value(value(actor),float(A.sample(motion,18)["3"]["0"])),"actual moved split keeps original expression time")
	app.undo();app.undo();app.pose_editor.restore_state(motion);app.set_frame(24)
	app.pose_editor.set_visibility_key(false);check(actor.data.format==A.FORMAT and actor.data.has("visibility_keys"),"visibility edits retain version5 expressions")
	app.undo();app.set_frame(12);await settled()
	var rows:=Channels.describe(actor.data);check(rows.any(func(row):return row.id=="@shape/3/0"),"animated shape appears as an expandable timeline channel")
	app.select_timeline_channel(id,"@shape/3/0",24);await settled();check(app.pose_editor.animated_shapes.shape_index==0 and app.frame==24,"timeline channel opens its real shape control at the clicked frame")
	app.pose_editor.shape_window.hide()
	var list_signature: String=app.pose_editor.animated_shapes.signature
	app.set_frame(0);var hidden_unchanged: bool=app.pose_editor.animated_shapes.signature==list_signature;app.set_frame(24);await settled()
	check(hidden_unchanged,"closed expression window does not rebuild its list while scrubbing")
	var before: Dictionary=actor.data.duplicate(true)
	var bad:=before.duplicate(true);bad.shape_base["999"]={"0":0.}
	check(not app.pose_editor.restore_state(bad).is_empty() and actor.data==before,"missing animated part refuses before replacing live state")
	bad=before.duplicate(true);bad.animation_clips[0].shape_keys[0].shapes["3"]["0"]=NAN
	check(not app.pose_editor.restore_state(bad).is_empty() and actor.data==before,"invalid animated amount leaves active data intact")
	check(actor.order==native_ids and cache_error(actor)<.00001,"failed edits preserve original rig and active animated geometry")
	var source_split:=Model.Clips.split(actor.data,12);app.pose_editor.restore_state(source_split.data)
	app.clip_editor.request("copy",id,source_split.right_id,12)
	app.pose_editor.add_model(folder.path_join("shape.glb"));var peer: RefCounted=app.renderer.active_model();var peer_id: String=peer.data.id
	var peer_data: Dictionary=peer.data.duplicate(true);peer_data.position=[4,0,0];peer_data.metadata.source_shape={"format":"studio_source_shape_2","enabled":true,"overrides":{"3":{"0":.1}}};app.pose_editor.restore_state(peer_data)
	app.clip_editor.request("paste",peer_id,"",24);app.set_frame(30);await settled()
	check(peer.data.format==A.FORMAT and close_value(value(peer),.65),"copied shape source time survives paste onto another instance")
	app.set_frame(0);await settled();check(close_value(value(peer),.1),"pasted expressions do not replace the destination's own base outside the piece")
	app.world_selection.select_entity(id);actor=app.renderer.world_runtime.instance(id);app.pose_editor.restore_state(motion)
	app.set_frame(12);app.pose_editor.auto_key.button_pressed=false;app.pose_editor.open_shapes();edit(app,.7);await settled()
	var draft_keys: int=actor.authored_shape_keys().size()
	check(close_value(value(actor),.7) and draft_keys==2,"Advanced auto-key opt-out retains an unrecorded shape draft")
	app.pose_editor.record_key();await settled();check(actor.authored_shape_keys().size()==3 and actor.authored_keys().size()==1 and close_value(float(A.sample(actor.data,12)["3"]["0"]),.7),"explicit Record includes the shape draft in its own controls")
	var body_before: Array=actor.authored_keys().duplicate(true)
	app.pose_editor.animated_shapes.remove_button.pressed.emit();await settled()
	check(actor.authored_shape_keys().size()==2 and actor.authored_keys()==body_before and close_value(value(actor),.5),"Simple removes only the selected expression key and resamples its curve")
	app.undo();await settled();check(actor.authored_shape_keys().size()==3 and close_value(value(actor),.7),"Undo restores the removed expression independently")
	app.pose_editor.restore_state(motion);app.pose_editor.auto_key.button_pressed=true;app.pose_editor.shape_window.hide()
	app.set_frame(0);app.pose_editor.record_key()
	check(actor.data.format==Model.BODY_FORMAT and close_value(float(A.sample(actor.data,12)["3"]["0"]),.5),"normal body Record retains independent expression timing in model6")
	app.set_frame(12);await settled();var helper=app.physics_editor.helper_editor;helper.open();await wait_job(helper)
	check(close_value(helper.request.morph_weights["3"][0],.5),"loose-part review snapshots the current animated expression")
	for i in range(helper.assessment.regions.size()):
		var region: Dictionary=helper.assessment.regions[i]
		if int(region.node)==3 and int(region.primitive)==1 and int(region.component)==0:helper.select_part(i);break
	await wait_job(helper);helper.apply();await wait_job(helper);actor=app.renderer.world_runtime.instance(id)
	check(actor.order.size()==native_ids.size()+4 and actor.data.format==Model.BODY_FORMAT and close_value(float(A.sample(actor.data,12)["3"]["0"]),.5),"weighted helper revision retains independent body and expression bindings and source curves")
	app.set_frame(0);app.physics_editor.fan_editor.add_fan();var fan: RefCounted=app.renderer.active_model();fan.data.position=[.4,1.15,-1.5];fan.data.rotation_xyzw=[0,0,0,1];fan.data.metadata.airflow.speed=10;fan.apply(0)
	app.world_selection.select_entity(id,false);actor=app.renderer.world_runtime.instance(id);app.mode.select(2);app.change_mode(2)
	var physics=app.physics_editor;physics.hair_toggle.button_pressed=true
	while physics.pending.has(id):await process_frame
	await settled();check(physics.active(id),"generated helper and animated expression can run together")
	if physics.active(id):
		var record=physics.recording;record.scope.select(0);record.button.pressed.emit()
		while record.active:await process_frame
		actor=app.renderer.world_runtime.instance(id)
		check(record.last_error.is_empty() and actor.authored_keys().size()==49 and close_value(float(A.sample(actor.data,12)["3"]["0"]),.5),"normal Local Record preserves the timed expression in49 real samples")
		var sway:=0.0
		for key in actor.authored_keys():
			for bone in key.pose:
				if not bone in native_ids:sway=maxf(sway,Timeline.quaternion(key.pose[bone].rotation_xyzw).angle_to(Quaternion.IDENTITY))
		check(sway>.005,"recorded helper bones actually move alongside the expression")
	Drawing.insert(app.layers[1],0,48,Drawing.blank(1920,1080));Drawing.cel_at(app.layers[1],0).image.set_pixel(80,80,Color.CYAN)
	for mode in ["packed","linked"]:
		var path:=folder.path_join("animated-"+mode+".has");app.has_project.save_file(path,mode);await wait_job(app.has_project)
		app.new_project();app.has_project.open_file(path);await wait_job(app.has_project);actor=app.renderer.world_runtime.instance(id)
		app.set_frame(12);await settled();check(actor!=null and close_value(value(actor),.5) and Drawing.cel_at(app.layers[1],12).image.get_pixel(80,80)==Color.CYAN,"animated shapes and independent cels survive "+mode+" HAS")
	app.changed();app.autosave_tick(true);var checkpoint: String=app.recovery_root.path_join(app.recovery_session)
	check(FileAccess.file_exists(checkpoint.path_join("project.json")),"silent checkpoint writes version5 expressions")
	app.new_project();check(app.restore_checkpoint({"folder":checkpoint}),"normal recovery accepts complete animated-shape world")
	actor=app.renderer.world_runtime.instance(id);app.set_frame(12);await settled()
	check(close_value(value(actor),.5) and Drawing.cel_at(app.layers[1],12).image.get_pixel(80,80)==Color.CYAN and app.dirty,"recovery restores expression and editable drawing as unsaved copy")
	var preview: Image=await app.renderer.capture(app.keys,app.layers,12,true);preview.save_png(folder.path_join("middle.png"))
	var error: String=await app.export_movie(folder);var movie: String=app.last_export_folder.path_join("movie.mp4")
	check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000013.png")).get_data()==preview.get_data(),"animated shape export equals reopened preview at frame12")
	app.new_project();app.pose_editor.add_model(folder.path_join("shape.glb"));actor=app.renderer.active_model()
	var body_data: Dictionary=actor.data.duplicate(true)
	for frame in [0,24]:
		body_data.pose_keys.append({"frame":frame,"pose":{},"transform":{"position":[0 if frame==0 else 2,0,0],"rotation_xyzw":[0,0,0,1],"scale":1.},"interpolation":"ease"})
	app.pose_editor.restore_state(body_data);var body_samples:=[]
	for half in range(49):body_samples.append(actor.sample_transform(float(half)/2))
	app.pose_editor.frame_model();app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,55)]
	app.set_frame(12);app.pose_editor.open_shapes();edit(app,.2);await settled()
	var exact_motion:=true
	for half in range(49):exact_motion=exact_motion and actor.sample_transform(float(half)/2)==body_samples[half]
	check(exact_motion and JSON.stringify(actor.authored_keys())==JSON.stringify(body_data.pose_keys),"real Simple expression edit preserves all eased body samples and exact control values")
	var expression_rows:=Channels.describe(actor.data)
	check(expression_rows.any(func(row):return row.id=="@shape/3/0" and row.frames==[12]) and expression_rows.any(func(row):return row.id=="@root" and row.frames==[0,24]),"timeline shows independent body and expression control frames")
	var eased_id: String=actor.data.id;var eased_path:=folder.path_join("independent-eased.has");app.pose_editor.shape_window.hide()
	app.has_project.save_file(eased_path,"packed");await wait_job(app.has_project);app.new_project();app.has_project.open_file(eased_path);await wait_job(app.has_project);actor=app.renderer.world_runtime.instance(eased_id)
	exact_motion=actor!=null
	if actor:
		for half in range(49):exact_motion=exact_motion and actor.sample_transform(float(half)/2)==body_samples[half]
	check(exact_motion,"packed HAS reopen preserves independent eased body motion at every half-frame")
	var legacy_tested:=false
	var legacy_plan: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("legacy-project.json")))
	if legacy_plan.path is String:
		app.new_project();app.has_project.open_file(legacy_plan.path);await wait_job(app.has_project)
		for legacy_actor in app.renderer.world_runtime.instances.values():
			if legacy_actor.data.format!=A.LEGACY_FORMAT:continue
			legacy_tested=true;app.world_selection.select_entity(legacy_actor.data.id);actor=legacy_actor
			check(actor.data.format==A.LEGACY_FORMAT,"normal Open preserves an actual previously saved model4 document")
			var old_actor:=Model.new();old_actor.data=actor.data.duplicate(true)
			var promoted:=A.promote(actor.data);var promoted_actor:=Model.new();promoted_actor.data=promoted;var preserved:=true
			for half in range(97):
				var at:=float(half)/2
				preserved=preserved and old_actor.sample_transform(at)==promoted_actor.sample_transform(at) and old_actor.sample(at)==promoted_actor.sample(at) and old_actor.sample_shapes(at)==promoted_actor.sample_shapes(at)
			check(preserved,"actual model4 promotion preserves body, bone and expression motion at every half-frame")
			app.set_frame(12);app.pose_editor.open_shapes();edit(app,.37);await settled();preserved=true
			for half in range(97):
				var at:=float(half)/2;preserved=preserved and old_actor.sample_transform(at)==actor.sample_transform(at) and old_actor.sample(at)==actor.sample(at)
			check(actor.data.format==A.FORMAT and preserved,"editing an actual legacy expression upgrades it without changing body or bone motion")
			app.pose_editor.shape_window.hide();break
	else:print("SKIP actual model4 package absent; authored model4 sampling remains covered by domain tests")
	var native_metrics:={}
	var plans: Array=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("native-plans.json")))
	for plan in plans:
		app.new_project();app.pose_editor.add_model(plan.source);actor=app.renderer.active_model()
		for name in plan.metadata:
			if name!="source_shape":actor.data.metadata[name]=plan.metadata[name]
		var metadata: Dictionary=actor.data.metadata.duplicate(true);var bone_ids: Array=actor.order.duplicate()
		var best: Dictionary={}
		for row in actor.root.get_meta(Shape.META).rows:
			if best.is_empty() or row.weights.size()>best.weights.size():best=row
		check(not best.is_empty(),"native asset exposes animated shape bindings: "+plan.label)
		if best.is_empty():continue
		var target:=-1;var surface_index:=-1
		for surface in range(best.mesh.mesh.get_surface_count()):
			var base: PackedVector3Array=best.mesh.mesh.surface_get_arrays(surface)[Mesh.ARRAY_VERTEX]
			var targets: Array=best.mesh.mesh.surface_get_blend_shape_arrays(surface)
			for index in range(mini(32,targets.size())):
				var positions: PackedVector3Array=targets[index][Mesh.ARRAY_VERTEX]
				for v in range(base.size()):
					if positions[v].distance_to(base[v])>.000001:target=index;surface_index=surface;break
				if target>=0:break
			if target>=0:break
		check(target>=0,"native channel has real positional deformation: "+plan.label)
		if target<0:continue
		app.pose_editor.open_shapes();var editor=app.pose_editor.animated_shapes
		for i in range(editor.parts.item_count):
			if int(editor.parts.get_item_metadata(i))==int(best.node):editor.parts.select(i);editor.parts.item_selected.emit(i)
		editor.search.clear();editor.rebuild();app.pose_editor.interpolation.select(1)
		edit(app,.1,target);app.set_frame(24);edit(app,.8,target);app.set_frame(12);await settled()
		if plan.label=="MMD":app.pose_editor.shape_window.get_texture().get_image().save_png(folder.path_join("mmd-shape-controls.png"))
		check(close_value(best.mesh.get_blend_shape_value(target),.45) and actor.order==bone_ids,"actual native GPU expression interpolates without changing bones: "+plan.label)
		var native_error:=cache_error(actor);check(native_error<.00001,"native animated CPU/GPU geometry agrees: "+plan.label)
		var began:=Time.get_ticks_usec();var peak:=0
		for i in range(50):
			var tick:=Time.get_ticks_usec();actor.apply(i%25);peak=maxi(peak,Time.get_ticks_usec()-tick)
		var average:=float(Time.get_ticks_usec()-began)/50.
		check(average<40000,"warm native expression evaluation avoids full target rebuild per frame: "+plan.label)
		app.set_frame(12);var native_id: String=actor.data.id;app.pose_editor.shape_window.hide()
		var native_path:=folder.path_join("animated-"+plan.label+".has");app.has_project.save_file(native_path,"packed");await wait_job(app.has_project)
		app.new_project();app.has_project.open_file(native_path);await wait_job(app.has_project);actor=app.renderer.world_runtime.instance(native_id);app.set_frame(12);await settled()
		check(actor!=null and actor.data.metadata==JSON.parse_string(JSON.stringify(metadata,"",true,true)) and actor.order==bone_ids and close_value(Shape.snapshot(actor.root)[str(best.node)][target],.45),"native animated values, metadata and bindings survive packed HAS: "+plan.label)
		native_metrics[plan.label]={"channels":best.weights.size(),"target":target,"geometry_error":native_error,"average_evaluation_usec":average,"peak_evaluation_usec":peak}
	var result:={"checks":checks,"failures":failures,"gpu_geometry_error":geometry_error,"movie":movie}
	result["native"]=native_metrics;result["actual_model4_tested"]=legacy_tested
	var file:=FileAccess.open(folder.path_join("animated-result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close();print("SHAPE_ANIMATION "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
