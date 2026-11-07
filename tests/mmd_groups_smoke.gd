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
	create_timer(170).timeout.connect(func():push_error("MMD expression watchdog");quit(2));call_deferred("run")
func settle() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func job(operation) -> void:
	while operation.pid>0:await process_frame
	await settle()
func choose(ui,id: String) -> bool:
	for i in range(ui.catalogue.entries.size()):
		if ui.catalogue.entries[i].id==id:ui.choices.select(i);ui.choices.item_selected.emit(i);return true
	return false
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0]
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settle();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("has-cache")
	if OS.get_cmdline_user_args().size()>1:
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
		app.has_project.open_file(folder.path_join("mmd-packed.has"));await job(app.has_project);var actor: RefCounted=app.renderer.world_runtime.instance(expected.id)
		check(actor!=null and actor.root.get_meta(P.META).entries.size()==4,"cold Open reconstructs native PMX groups from embedded standard source")
		check(actor!=null and JSON.parse_string(JSON.stringify(actor.authored_shape_keys(),"",true,true))==expected.keys and actor.data.metadata==expected.metadata,"cold Open preserves exact ordinary deform keys/native provenance")
		check(Drawing.image(Drawing.cel_at(app.layers[1],12)).get_pixel(80,80)==Color.CYAN,"cold Open keeps the independent cyan drawing editable")
		print("MMD_GROUPS_READER "+JSON.stringify({"checks":checks,"failures":failures}));app.free();quit(0 if failures==0 else 1);return
	var keys: Array=app.keys.duplicate(true);var source:=folder.path_join("Original groups.pmx");var original:=FileAccess.get_sha256(source)
	var placement: Dictionary=app.import_actions.placement();placement.physics_on_import=false
	app.source_import.start(source,true,0,placement);await job(app.source_import)
	var actor: RefCounted=app.renderer.active_model()
	check(actor!=null,"raw original PMX imports through the in-app native worker")
	if actor==null:print(app.status.text);app.free();quit(1);return
	for child in app.get_children():
		if child is AcceptDialog and child.title=="Imported with limitations":child.hide();child.queue_free()
	var report_path: String=app.source_import.folder.path_join("parameters.json");var report: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(report_path))
	check(report.mmd_expression_groups.size()==4 and report.expression_presets.entries.size()==4,"native preparation retains exact group names and dependencies")
	check(app.keys==keys and not app.physics_editor.is_running(),"native group discovery invents no shot keys or live simulation")
	var catalogue: Dictionary=actor.root.get_meta(P.META);check(catalogue.error.is_empty() and catalogue.entries.size()==4,"native MMD groups use the same transient standard expression catalogue")
	app.pose_editor.frame_model();app.keys=[Model.Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,55)];app.set_frame(0)
	app.pose_editor.open_shapes();await settle();var ui=app.pose_editor.animated_shapes.presets
	check(ui.panel.is_visible_in_tree() and ui.choices.get_item_text(0)=="Friendly","Simple uses the source's declared English group name")
	var native: Dictionary=actor.data.metadata.duplicate(true);var body: Dictionary=actor.sample_body(0);var view: Dictionary=app.renderer.view_state();keys=app.keys.duplicate(true)
	var neutral: Image=await app.renderer.capture(app.keys,app.layers,0,true);var id: String=actor.data.id
	for i in range(3):
		app.set_frame(i*12);check(choose(ui,"mmd:group:"+str(i)),"exact native group identity resolves: "+str(i))
		var before: Dictionary=actor.data.duplicate(true);var history: int=app.history.size();ui.amount.value=.6;ui.apply_button.pressed.emit();await settle()
		var expected: Dictionary=P.evaluate(catalogue,{"mmd:group:"+str(i):.6}).values;var actual: Dictionary=actor.sample_shapes(app.frame);var matches:=true
		for node in expected:
			for index in expected[node]:matches=matches and is_equal_approx(float(actual.get(node,{}).get(index,0.)),float(expected[node][index]))
		check(matches and app.history.size()==history+1,"compound/nested/signed bindings create one ordinary deform edit: "+str(i))
		check(actor.sample_body(app.frame)==body and actor.data.metadata==native and app.keys==keys and app.renderer.view_state()==view,"MMD expression preserves independent body/native/shot/view: "+str(i))
		app.undo();await settle();check(actor.data==before,"native group Undo restores exact model: "+str(i));app.redo();await settle()
	var changed: Image=await app.renderer.capture(app.keys,app.layers,24,true);check(changed.get_data()!=neutral.get_data(),"signed native group changes real rendered geometry")
	var before: Dictionary=actor.data.duplicate(true);var history: int=app.history.size();choose(ui,"mmd:group:3");ui.apply_pose()
	check(ui.apply_button.disabled and "unsupported" in ui.info.text and actor.data==before and app.history.size()==history,"mixed UV group stays visible and refuses the entire pose")
	choose(ui,"mmd:group:1");app.set_advanced(true);await settle();check(str(ui.entry().native_name) in ui.info.text and "bindings" in ui.info.text,"Advanced exposes exact JP group identity and prepared vertex bindings")
	root.get_texture().get_image().save_png(folder.path_join("mmd-advanced.png"));app.set_advanced(false);await settle();root.get_texture().get_image().save_png(folder.path_join("mmd-simple.png"))
	app.pose_editor.shape_window.hide();Drawing.insert(app.layers[1],0,48,Drawing.blank(1920,1080));Drawing.edit_image(Drawing.cel_at(app.layers[1],12)).image.set_pixel(80,80,Color.CYAN);app.set_frame(12)
	var expected:={"id":id,"keys":actor.authored_shape_keys(),"metadata":actor.data.metadata};FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify(expected,"",true,true))
	for mode in ["packed","linked"]:
		app.has_project.save_file(folder.path_join("mmd-"+mode+".has"),mode);await job(app.has_project);app.new_project();app.has_project.open_file(folder.path_join("mmd-"+mode+".has"));await job(app.has_project);actor=app.renderer.world_runtime.instance(id)
		check(actor!=null and JSON.parse_string(JSON.stringify(actor.authored_shape_keys(),"",true,true))==JSON.parse_string(JSON.stringify(expected.keys,"",true,true)) and actor.root.get_meta(P.META).entries.size()==4,"ordinary "+mode+" HAS preserves groups and editable keys")
	var preview: Image=await app.renderer.capture(app.keys,app.layers,12,true);preview.save_png(folder.path_join("middle.png"));var error: String=await app.export_movie(folder)
	check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000013.png")).get_data()==preview.get_data(),"ordinary MP4 matches grouped native pose and independent drawing exactly")
	check(FileAccess.get_sha256(source)==original,"native PMX input stays byte-identical")
	var result:={"checks":checks,"failures":failures,"movie":app.last_export_folder.path_join("movie.mp4"),"bundle":report_path.get_base_dir()};print("MMD_GROUPS_APP "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
