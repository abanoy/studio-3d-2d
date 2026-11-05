extends SceneTree
const P=preload("res://src/expression_presets.gd")
const Model=preload("res://src/model.gd")
const Drawing=preload("res://src/drawing.gd")
var checks:=0
var failures:=0
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func _initialize() -> void:
	create_timer(175).timeout.connect(func():push_error("Expression pose watchdog");quit(2));call_deferred("run")
func settled() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func wait_job(job) -> void:
	while job.pid>0:await process_frame
	await settled()
func choose(ui,id: String) -> bool:
	for i in range(ui.catalogue.entries.size()):
		if ui.catalogue.entries[i].id==id:ui.choices.select(i);ui.choices.item_selected.emit(i);return true
	return false
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0]
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("has-cache")
	if args.size()>1:
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
		app.has_project.open_file(folder.path_join("expressions-packed.has"));await wait_job(app.has_project)
		var actor: RefCounted=app.renderer.world_runtime.instance(expected.id)
		check(actor!=null,"cold Open restores expression-pose model")
		if actor:
			check(actor.root.get_meta(P.META).entries.size()==expected.count,"cold Open reconstructs embedded groups from managed source")
			check(JSON.parse_string(JSON.stringify(actor.authored_shape_keys(),"",true,true))==expected.keys and actor.data.metadata==expected.metadata,"cold Open retains exact deform keys and native metadata")
			check(Drawing.cel_at(app.layers[1],12).image.get_pixel(80,80)==Color.CYAN,"cold Open keeps drawing editable and independent")
			var image: Image=await app.renderer.capture(app.keys,app.layers,12,true);image.save_png(folder.path_join("cold.png"));var a:=image.get_data();var b:=Image.load_from_file(folder.path_join("middle.png")).get_data();var changed:=0;var total:=0
			for i in range(a.size()):
				var d:=absi(int(a[i])-int(b[i]));total+=d;changed+=int(d>0)
			check(a.size()==b.size() and changed<=384 and float(total)/a.size()<.002,"cold native render stays within existing mesh-edge rebuild bound")
		var result:={"checks":checks,"failures":failures};print("EXPRESSION_PRESETS_READER "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1);return
	var plans: Array=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("plans.json")))
	var material_error: String=app.pose_editor.add_model(folder.path_join("material-only.glb"));app.pose_editor.open_shapes();await settled()
	var material_ui=app.pose_editor.animated_shapes.presets
	check(material_error.is_empty() and app.pose_editor.shape_button.visible and material_ui.panel.is_visible_in_tree() and material_ui.apply_button.disabled and "unsupported material" in material_ui.info.text,"material-only expressions remain visible with explicit unsupported guidance")
	var final_id:=""
	for plan in plans:
		app.new_project();app.set_advanced(false);var error: String=app.pose_editor.add_model(plan.source);var actor: RefCounted=app.renderer.active_model()
		check(error.is_empty() and actor!=null,"expression model imports: "+plan.label)
		if not actor:continue
		app.pose_editor.frame_model();app.keys=[Model.Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,55)];app.set_frame(0)
		app.pose_editor.set_shape_amounts({plan.node:{plan.index:.23}});app.set_frame(12);app.pose_editor.open_shapes();await settled()
		var editor=app.pose_editor.animated_shapes;var ui=editor.presets
		check(ui.panel.visible and ui.choices.item_count==int(plan.expected),"embedded groups are separate from raw deform list: "+plan.label)
		check(app.pose_editor.shape_window.position.x>app.canvas.image_rect().get_center().x and app.pose_editor.shape_window.position.x+app.pose_editor.shape_window.size.x<=app.get_viewport_rect().size.x,"Shapes opens beside the framed subject within the actual app: "+plan.label)
		check(choose(ui,plan.id),"native group identity resolves: "+plan.label)
		var before: Dictionary=actor.data.duplicate(true);var keys: Array=app.keys.duplicate(true);var view: Dictionary=app.renderer.view_state();var history: int=app.history.size();var body: Dictionary=actor.sample_body(12)
		var image_before: Image=await app.renderer.capture(app.keys,app.layers,12,true);view=app.renderer.view_state()
		ui.amount.value=.6;var expected:=P.evaluate(ui.catalogue,{plan.id:.6});ui.apply_button.pressed.emit();await settled()
		var values: Dictionary=actor.sample_shapes(12)
		var matches:=true
		for row in editor.rows():
			var effective:=Model.Shape.effective(row,Model.ShapeAnimation.configuration(Model.Shape.setting(actor.data),values))
			for index in expected.values.get(str(row.node),{}):matches=matches and is_equal_approx(effective[int(index)],expected.values[str(row.node)][index])
		check(matches and values[plan.node][plan.index]==.23,"all declared grouped amounts apply while unrelated deform survives: "+plan.label)
		check(app.history.size()==history+1 and actor.sample_body(12)==body and app.keys==keys and actor.data.metadata==before.metadata and app.renderer.view_state()==view,"one Undo preserves body, camera, view and native data: "+plan.label)
		var image_after: Image=await app.renderer.capture(app.keys,app.layers,12,true);check(image_before.get_data()!=image_after.get_data(),"native expression pose visibly changes actual geometry: "+plan.label)
		app.undo();await settled();check(actor.data==before,"Undo restores exact original model: "+plan.label);app.redo();await settled()
		var after: Dictionary=actor.data.duplicate(true);history=app.history.size();ui.apply_button.pressed.emit();await settled();check(actor.data==after and app.history.size()==history,"identical expression pose is a no-op: "+plan.label)
		editor.amount.value+=.123;ui.apply_pose();check(editor.dirty and actor.data==after and app.history.size()==history,"pending raw amount is not consumed by an expression: "+plan.label);editor.load_amount()
		app.physics_editor.queue_import_start(actor.data.id,true,false);var ticket: Dictionary=app.physics_editor.import_starts.duplicate(true);var generation: int=app.physics_editor.generation;ui.apply_pose()
		check(app.physics_editor.import_starts==ticket and app.physics_editor.generation==generation and actor.data==after,"queued physics defers expression without freezing or cancelling: "+plan.label);app.physics_editor.clear()
		app.set_advanced(true);await settled();check(str(ui.entry().native_name) in ui.info.text and "bindings" in ui.info.text,"Advanced exposes original group and bindings: "+plan.label)
		if plan.label=="Authored compound":
			choose(ui,"custom:Material expression");ui.apply_pose();check(ui.apply_button.disabled and actor.data==after and app.history.size()==history,"unsupported native effects cannot apply a partial expression")
			choose(ui,plan.id);app.set_frame(20);app.pose_editor.auto_key.button_pressed=false;ui.amount.value=.25;var old_keys: Array=actor.authored_shape_keys().duplicate(true);ui.apply_pose();await settled()
			check(actor.authored_shape_keys()==old_keys and not Model.ShapeAnimation.has_control(actor.data,20,"3","0") and actor.data.shape_pose["3"]["0"]==.125,"Auto-key off creates only an ordinary expression draft")
			app.pose_editor.record_key();check(Model.ShapeAnimation.has_control(actor.data,20,"3","0"),"explicit Record keys the grouped draft through ordinary controls");app.pose_editor.auto_key.button_pressed=true
			# Exact baseline fits; adding grouped controls must refuse full-world overflow.
			app.set_frame(24);var padding: int=1024*1024-app.pose_editor.contacts.metadata_bytes(app.current_world())-4;actor.data.metadata["budget_test"]="x".repeat(maxi(padding-20,0));var budget_before: Dictionary=actor.data.duplicate(true);history=app.history.size();ui.amount.value=.9
			check(app.pose_editor.contacts.metadata_bytes(app.current_world())<=1024*1024,"near-limit expression fixture starts inside metadata budget")
			ui.apply_pose();check(actor.data==budget_before and app.history.size()==history and "metadata limit" in app.status.text,"oversized grouped keys refuse before data or history mutation");actor.data.metadata.erase("budget_test")
		app.set_frame(12);app.set_advanced(false);await settled();root.get_texture().get_image().save_png(folder.path_join(plan.label.replace(" ","_")+"-simple.png"));final_id=actor.data.id
	var actor: RefCounted=app.renderer.active_model();Drawing.insert(app.layers[1],0,48,Drawing.blank(1920,1080));Drawing.cel_at(app.layers[1],12).image.set_pixel(80,80,Color.CYAN)
	var expected:={"id":final_id,"count":actor.root.get_meta(P.META).entries.size(),"keys":actor.authored_shape_keys(),"metadata":actor.data.metadata};FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify(expected,"",true,true))
	app.pose_editor.shape_window.hide()
	for mode in ["packed","linked"]:
		app.has_project.save_file(folder.path_join("expressions-"+mode+".has"),mode);await wait_job(app.has_project);app.new_project();app.has_project.open_file(folder.path_join("expressions-"+mode+".has"));await wait_job(app.has_project);actor=app.renderer.world_runtime.instance(final_id)
		check(actor!=null and JSON.parse_string(JSON.stringify(actor.authored_shape_keys(),"",true,true))==JSON.parse_string(JSON.stringify(expected.keys,"",true,true)) and actor.root.get_meta(P.META).entries.size()==int(expected.count),"ordinary "+mode+" HAS retains embedded groups and exact editable deform keys")
	var preview: Image=await app.renderer.capture(app.keys,app.layers,12,true);preview.save_png(folder.path_join("middle.png"));var export_error: String=await app.export_movie(folder)
	check(export_error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000013.png")).get_data()==preview.get_data(),"normal MP4 uses exact expression-pose frame and independent cyan drawing")
	var result:={"checks":checks,"failures":failures,"models":plans.size(),"movie":app.last_export_folder.path_join("movie.mp4")};print("EXPRESSION_PRESETS_APP "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
