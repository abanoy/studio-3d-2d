extends SceneTree
const Model=preload("res://src/model.gd")
const Shape=Model.Shape
const Timeline=preload("res://src/timeline.gd")
const Drawing=preload("res://src/drawing.gd")
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(180).timeout.connect(func():push_error("Base shape watchdog");quit(2));call_deferred("run")
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func settled() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func wait_job(job) -> void:
	while job.pid>0:await process_frame
	await settled()
func close_value(a: float,b: float) -> bool:return absf(a-b)<.000001
func choose(editor,index: int) -> void:
	for i in range(editor.shapes.item_count):
		if int(editor.shapes.get_item_metadata(i))==index:editor.shapes.select(i);editor.shapes.item_selected.emit(i);return
func weights(actor,a: float,b: float) -> bool:
	var mesh: MeshInstance3D=actor.root.get_meta(Shape.META).rows[0].mesh
	return close_value(mesh.get_blend_shape_value(0),a) and close_value(mesh.get_blend_shape_value(1),b)
func cache_error(actor) -> float:
	var maximum:=0.0
	for row in actor.root.get_meta(Shape.META).rows:
		var baked: ArrayMesh=row.mesh.bake_mesh_from_current_blend_shape_mix()
		for surface in range(baked.get_surface_count()):
			var gpu: PackedVector3Array=baked.surface_get_arrays(surface)[Mesh.ARRAY_VERTEX]
			var cached:=Shape.vertices(row.mesh,surface,row.mesh.mesh.surface_get_arrays(surface)[Mesh.ARRAY_VERTEX])
			for i in range(gpu.size()):maximum=maxf(maximum,gpu[i].distance_to(cached[i]))
	return maximum
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0];var app=load("res://main.tscn").instantiate()
	app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	app.pose_editor.add_model(folder.path_join("shape.glb"));var actor: RefCounted=app.renderer.active_model();var id: String=actor.data.id
	var editor=app.pose_editor.base_shapes
	check(not editor.panel.is_visible_in_tree(),"base setup stays out of the default Simple workspace")
	app.set_advanced(true);await settled();check(editor.panel.is_visible_in_tree() and editor.shapes.item_count==2,"Advanced shows actual named imported shape channels")
	app.pose_editor.frame_model();app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,55)]
	var original: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	var keys: Array=actor.data.pose_keys.duplicate(true);var cameras: Array=app.keys.duplicate(true);var count: int=app.history.size()
	choose(editor,0);editor.amount.value=.2;editor.apply_button.pressed.emit();await settled()
	check(weights(actor,.2,.2) and app.history.size()==count+1,"Apply changes one base amount with one Undo")
	check(actor.data.pose_keys==keys and app.keys==cameras and actor.data.metadata.source_shape.format=="studio_source_shape_2","base setup preserves pose/camera keys and stores a versioned adjustment")
	var edited: Image=await app.renderer.capture(app.keys,app.layers,0,true);check(edited.get_data()!=original.get_data(),"base amount visibly deforms the model")
	app.set_advanced(false);await settled();app.set_advanced(true);await settled()
	check((await app.renderer.capture(app.keys,app.layers,0,true)).get_data()==edited.get_data() and app.history.size()==count+1,"Simple/Advanced switching preserves adjusted pixels and Undo")
	var saved_history: int=app.history.size();editor.apply_button.pressed.emit();check(app.history.size()==saved_history,"untouched amount does not create a false edit")
	app.undo();await settled();check((await app.renderer.capture(app.keys,app.layers,0,true)).get_data()==original.get_data(),"Undo restores exact original default pixels")
	app.redo();await settled();check((await app.renderer.capture(app.keys,app.layers,0,true)).get_data()==edited.get_data(),"Redo restores exact adjusted pixels")
	editor.search.text="second";editor.search.text_changed.emit(editor.search.text)
	check(editor.shapes.item_count==1 and editor.shape_index==1,"shape search selects the original numeric channel without renaming it")
	editor.amount.value=.8;editor.apply_button.pressed.emit();await settled();check(weights(actor,.2,.8),"editing a second shape keeps the first adjustment")
	app.pose_editor.source_shape.button_pressed=false;await settled();check(weights(actor,.2,.8),"turning imported defaults off retains explicit adjustments")
	editor.reset_button.pressed.emit();await settled();check(weights(actor,.2,0),"reset removes only the selected adjustment and inherits neutral base")
	app.undo();app.undo();await settled();check(weights(actor,.2,.8) and Shape.enabled(actor.data),"Undo restores the adjustment and imported base choice")
	editor.reset_all.pressed.emit();await settled();check(weights(actor,.6,.2),"reset all restores declared defaults rather than deleting source morphs")
	app.undo();await settled();check(weights(actor,.2,.8),"reset all is one reversible model edit")
	var error:=cache_error(actor);check(error<.00001,"collision/framing vertices agree with actual adjusted GPU geometry")
	for frame in [0,24,47]:app.set_frame(frame);check(weights(actor,.2,.8),"base shape remains consistent across project time: "+str(frame))
	app.set_frame(0);var before: Dictionary=actor.data.duplicate(true);var history: int=app.history.size()
	for bad in [{"03":{"0":1.}}, {"999":{"0":1.}}, {"3":{"999":1.}}, {"3":{"0":NAN}}, {"3":{"0":101.}}, {"3":{"0":true}}]:
		var data:=before.duplicate(true);data.metadata.source_shape.overrides=bad
		check(not app.pose_editor.restore_state(data).is_empty() and actor.data==before and app.history.size()==history,"invalid adjustment refuses without changing the model or Undo")
	check(weights(actor,.2,.8) and cache_error(actor)<.00001,"failed adjustments leave active GPU and geometry caches intact")
	editor.search.clear();editor.rebuild();var helper=app.physics_editor.helper_editor;helper.open();await wait_job(helper)
	check(close_value(helper.request.morph_weights["3"][0],.2) and close_value(helper.request.morph_weights["3"][1],.8),"normal loose-part review receives edited base amounts")
	for i in range(helper.assessment.regions.size()):
		var row: Dictionary=helper.assessment.regions[i]
		if int(row.node)==3 and int(row.primitive)==1 and int(row.component)==0:helper.select_part(i);break
	await wait_job(helper);helper.apply();await wait_job(helper);actor=app.renderer.world_runtime.instance(id)
	check(weights(actor,.2,.8) and actor.order.size()==6 and actor.data.metadata.source_shape==before.metadata.source_shape,"weighted helper revision retains explicit base adjustments and original channels")
	Drawing.insert(app.layers[1],0,48,Drawing.blank(1920,1080));Drawing.edit_image(Drawing.cel_at(app.layers[1],0)).image.set_pixel(80,80,Color.CYAN)
	for mode in ["packed","linked"]:
		var path:=folder.path_join("base-"+mode+".has");app.has_project.save_file(path,mode);await wait_job(app.has_project)
		app.new_project();app.has_project.open_file(path);await wait_job(app.has_project);actor=app.renderer.world_runtime.instance(id)
		check(actor!=null and weights(actor,.2,.8) and Drawing.image(Drawing.cel_at(app.layers[1],0)).get_pixel(80,80)==Color.CYAN,"base adjustments and independent drawing survive "+mode+" HAS")
	var image: Image=await app.renderer.capture(app.keys,app.layers,0,true);image.save_png(folder.path_join("adjusted.png"))
	var export_error: String=await app.export_movie(folder);var movie: String=app.last_export_folder.path_join("movie.mp4")
	check(export_error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000001.png")).get_data()==image.get_data(),"adjusted base exports with exact reopened preview pixels")
	# A valid first part followed by a coordinate-overflowing part must not poison
	# the complete prepared cache when validation fails late.
	app.new_project();app.append_object(Model.definition(folder.path_join("late-failure.glb")),"model");actor=app.renderer.active_model()
	var valid: Dictionary=actor.data.duplicate(true);valid.metadata.source_shape={"format":"studio_source_shape_2","enabled":false,"overrides":{"3":{"0":.01}}}
	check(app.pose_editor.restore_state(valid).is_empty(),"valid adjusted geometry prepares before the late-failure probe")
	var bad_data: Dictionary=actor.data.duplicate(true);bad_data.metadata.source_shape.overrides={"3":{"0":.02},"5":{"0":100.}}
	check(not app.pose_editor.restore_state(bad_data).is_empty() and close_value(Shape.snapshot(actor.root)["3"][0],.01),"late second-part geometry failure preserves the previously applied shape")
	valid=actor.data.duplicate(true);valid.metadata.source_shape.overrides["3"]["0"] = .03
	check(app.pose_editor.restore_state(valid).is_empty(),"valid adjustment still works after a failed preparation")
	app.undo();await settled();check(close_value(Shape.snapshot(actor.root)["3"][0],.01),"Undo after a failed preparation restores the correct earlier geometry")
	var native_metrics:={}
	var plans: Array=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("native-plans.json")))
	for plan in plans:
		app.new_project();app.pose_editor.add_model(plan.source);actor=app.renderer.active_model();app.set_advanced(true)
		for key in plan.metadata:
			if key!="source_shape":actor.data.metadata[key]=plan.metadata[key]
		var original_ids: Array=actor.order.duplicate();var native_metadata: Dictionary=actor.data.metadata.duplicate(true)
		var best: Dictionary={}
		for row in actor.root.get_meta(Shape.META).rows:
			if best.is_empty() or row.weights.size()>best.weights.size():best=row
		check(not best.is_empty(),"native model exposes real shape channels: "+plan.label)
		if best.is_empty():continue
		editor=app.pose_editor.base_shapes;editor.search.clear();editor.search.text_changed.emit("")
		for i in range(editor.parts.item_count):
			if int(editor.parts.get_item_metadata(i))==int(best.node):editor.parts.select(i);editor.parts.item_selected.emit(i)
		var target:=-1;var surface_index:=-1
		for surface in range(best.mesh.mesh.get_surface_count()):
			var positions: PackedVector3Array=best.mesh.mesh.surface_get_arrays(surface)[Mesh.ARRAY_VERTEX]
			var targets: Array=best.mesh.mesh.surface_get_blend_shape_arrays(surface)
			for index in range(mini(32,targets.size())):
				var vertices: PackedVector3Array=targets[index][Mesh.ARRAY_VERTEX]
				for v in range(positions.size()):
					if vertices[v].distance_to(positions[v])>.000001:target=index;surface_index=surface;break
				if target>=0:break
			if target>=0:break
		check(target>=0,"native fixture has a nonzero positional shape for actual deformation: "+plan.label)
		if target<0:continue
		choose(editor,target)
		var original_mesh: ArrayMesh=best.mesh.bake_mesh_from_current_blend_shape_mix()
		editor.amount.value=.35;var started:=Time.get_ticks_usec();editor.apply_button.pressed.emit();var elapsed:=Time.get_ticks_usec()-started;await settled()
		var new_mesh: ArrayMesh=best.mesh.bake_mesh_from_current_blend_shape_mix()
		var original_positions: PackedVector3Array=original_mesh.surface_get_arrays(surface_index)[Mesh.ARRAY_VERTEX]
		var new_positions: PackedVector3Array=new_mesh.surface_get_arrays(surface_index)[Mesh.ARRAY_VERTEX];var deformation:=0.0
		for i in range(new_positions.size()):deformation=maxf(deformation,new_positions[i].distance_to(original_positions[i]))
		check(deformation>.000001 and actor.order==original_ids and close_value(best.mesh.get_blend_shape_value(target),.35),"native amount changes actual GPU geometry without changing bone identities: "+plan.label)
		if plan.label=="SFM":
			check(editor.shapes.item_count==520,"all520 actual Scout channels remain selectable")
			var last: String=best.names[519];editor.search.text=last;editor.search.text_changed.emit(last)
			choose(editor,519)
			check(editor.shapes.item_count>=1 and editor.shape_index==519,"native large-list search selects original channel519")
			editor.amount.value=.15;editor.apply_button.pressed.emit();await settled()
			check(close_value(best.mesh.get_blend_shape_value(519),.15) and close_value(best.mesh.get_blend_shape_value(target),.35),"editing native channel519 preserves the earlier adjustment")
		var native_id: String=actor.data.id;var native_path:=folder.path_join("base-"+plan.label+".has")
		app.has_project.save_file(native_path,"packed");await wait_job(app.has_project);app.new_project();app.has_project.open_file(native_path);await wait_job(app.has_project);actor=app.renderer.world_runtime.instance(native_id)
		var metadata: Dictionary=actor.data.metadata.duplicate(true);metadata.erase("source_shape");native_metadata.erase("source_shape")
		check(close_value(Shape.snapshot(actor.root)[str(best.node)][target],.35) and actor.order==original_ids and metadata==JSON.parse_string(JSON.stringify(native_metadata,"",true,true)),"native shape, full imported metadata and stable bindings survive packed HAS: "+plan.label)
		if plan.label=="SFM":check(close_value(Shape.snapshot(actor.root)[str(best.node)][519],.15),"native channel519 adjustment survives packed HAS")
		app.world_selection.select_entity(actor.data.id)
		native_metrics[plan.label]={"channels":best.weights.size(),"target":target,"deformation":deformation,"apply_usec":elapsed}
	app.get_window().size=Vector2i(1200,900);await settled();check(app.pose_editor.base_shapes.panel.is_visible_in_tree() and app.canvas.size.x>500,"visible Advanced shape controls leave a usable viewport at1200pixels")
	app.pose_editor.frame_model();app.inspector_scroll.ensure_control_visible(app.pose_editor.base_shapes.panel);await settled()
	check(app.inspector_scroll.get_global_rect().encloses(app.pose_editor.base_shapes.apply_button.get_global_rect()),"base Apply action is reachable within the scrolling inspector")
	app.get_viewport().get_texture().get_image().save_png(folder.path_join("base-controls.png"))
	var result:={"checks":checks,"failures":failures,"gpu_geometry_error":error,"movie":movie}
	result["native"]=native_metrics
	var f:=FileAccess.open(folder.path_join("base-result.json"),FileAccess.WRITE);f.store_string(JSON.stringify(result));f.close();print("BASE_SHAPES "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
