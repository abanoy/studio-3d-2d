extends SceneTree
const Height=preload("res://src/character_height.gd")
const Fixture=preload("res://tests/height_fixture.gd")
const Drawing=preload("res://src/drawing.gd")
var checks:=0
var failures:=0
var app
var folder: String

func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1

func _initialize() -> void:
	create_timer(180).timeout.connect(func():push_error("Human reference watchdog");quit(2))
	call_deferred("run")

func settled() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw

func wait_review() -> void:
	while app.height_review.pending and not app.height_review.prepared:await process_frame
	await settled()

func wait_job() -> void:
	while app.has_project.pid>0:await process_frame
	await settled()

func actor():return app.renderer.active_model()

func add_reference(path: String) -> void:
	var context: Dictionary=app.import_actions.placement();context.physics_on_import=false
	var history: int=app.history.size()
	var error: String=app.pose_editor.add_model(path,0,context)
	await wait_review()
	check(error.is_empty() and app.height_review.pending and not app.height_review.reference.disabled,"complete figure offers the distinct Scale1 reference choice")
	check(actor()==null and app.history.size()==history,"review and measurement do not install a model or create Undo")
	if not app.height_review.pending:return
	app.height_review.reference.button_pressed=true
	print("REFERENCE_CHOICE "+JSON.stringify({"fit":app.height_review.fit.button_pressed,"reference":app.height_review.reference.button_pressed,"target":app.height_review.target.value,"expected":Height.SIX_FEET,"text":app.height_review.target.get_line_edit().text,"editable":app.height_review.target.editable}))
	check(app.height_review.fit.button_pressed and app.height_review.target.get_line_edit().text=="1.8288" and not app.height_review.target.editable,"reference choice displays exactly1.8288metres and locks the target")
	app.height_review.fit.button_pressed=false
	check(not app.height_review.reference.button_pressed,"keeping original size clears a previously selected reference")
	app.height_review.reference.button_pressed=true
	app.height_review.apply();await settled()
	check(actor()!=null and app.history.size()==history+1,"reference imports as one ordinary world Undo")

func run() -> void:
	folder=OS.get_cmdline_user_args()[0]
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.display_prefs_path=folder.path_join("display.cfg")
	root.add_child(app);await settled();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("has-cache");app.import_actions.offer_height=true
	if OS.get_cmdline_user_args().size()>1:
		app.has_project.open_file(folder.path_join("human-packed.has"));await wait_job()
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
		app.world_selection.select_entity(expected.id);await settled()
		check(actor()!=null and actor().data.scale==1. and actor().data.has("asset_basis"),"cold HAS reader restores intrinsic reference with artist Scale1")
		check(Height.queries==0 and not app.height_review.pending,"cold Open does not remeasure or show import review")
		if actor():check(absf(Height.query(actor()).height-Height.SIX_FEET)<.00002,"cold Open applies the six-foot basis exactly once")
		finish();return
	var paths:=[];var identities:={}
	var normalized_definition:={}
	for factor in [.25,3.]:
		var path:=folder.path_join("human-"+str(factor)+".glb")
		check(Fixture.create(path,.75*factor,.65*factor)==OK,"authored character fixture exports at independent source size")
		paths.append(path);identities[path]=FileAccess.get_sha256(path)
		app.new_project();await add_reference(path)
		if not actor():continue
		check(actor().data.scale==1. and actor().data.has("asset_basis"),"six-foot reference leaves artist Scale at1 instead of baking into it")
		check(absf(Height.query(actor()).height-Height.SIX_FEET)<.00002,"different source sizes reach the same six-foot visible reference")
		check(FileAccess.get_sha256(path)==identities[path] and actor().data.sha256==identities[path],"reference preserves original GLB bytes and source identity")
		normalized_definition=actor().data.duplicate(true);normalized_definition.source=path
	# Exercise the actual novice-facing size control and its ordinary Undo path.
	if actor():
		app.pose_editor.frame_model();app.set_advanced(false);await settled()
		check(app.pose_editor.human_size_row.is_visible_in_tree() and app.pose_editor.human_reference_note.is_visible_in_tree(),"Simple Pose exposes reference size without Advanced mode")
		root.get_texture().get_image().save_png(folder.path_join("reference-inspector.png"))
		var reference_record: Dictionary=actor().data.asset_basis.duplicate(true)
		var reference_id: String=actor().data.id
		var before_body_request:=var_to_bytes(actor().data)
		app.physics_editor.enable_body(actor())
		check(not app.physics_editor.body_active(reference_id) and app.status.text=="Body Physics is not ready for this reference size. Posing and Hair & clothes are still available." and var_to_bytes(actor().data)==before_body_request,"body toggle refuses unsupported reference scaling without changing the model")
		for scale in [.5,2.]:
			app.pose_editor.human_size_field.value=scale
			print("REFERENCE_SCALE_BEFORE "+JSON.stringify({"requested":scale,"simple":app.pose_editor.human_size_field.value,"advanced":app.pose_editor.scale_field.value,"frame":app.frame}))
			app.pose_editor.human_size_apply.pressed.emit();await settled()
			print("REFERENCE_SCALE_AFTER "+JSON.stringify({"requested":scale,"simple":app.pose_editor.human_size_field.value,"advanced":app.pose_editor.scale_field.value,"sample":actor().sample_transform(app.frame,true).scale,"data":actor().data.scale,"height":Height.query(actor()).height,"status":app.status.text,"history":app.history.size()}))
			check(absf(Height.query(actor()).height-Height.SIX_FEET*scale)<.00002,"relative artist scale changes measured height: "+str(scale))
			check(actor().data.asset_basis==reference_record,"artist scale edits never rewrite the asset reference")
			app.undo();await settled();check(absf(Height.query(actor()).height-Height.SIX_FEET)<.00002,"Undo restores Scale1 without compounding the basis")
			app.redo();await settled();check(absf(Height.query(actor()).height-Height.SIX_FEET*scale)<.00002,"Redo preserves reference and relative scale")
			app.undo();await settled()
		# Original independent drawing and preview/export agreement remain required.
		Drawing.insert(app.layers[1],0,48,Drawing.blank(1920,1080));Drawing.edit_image(Drawing.cel_at(app.layers[1],0)).image.set_pixel(80,80,Color.CYAN)
		app.pose_editor.frame_model();app.keys=[app.Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,55)]
		for mode in ["packed","linked"]:
			var queries:=Height.queries;app.has_project.save_file(folder.path_join("human-"+mode+".has"),mode);await wait_job()
			app.new_project();app.has_project.open_file(folder.path_join("human-"+mode+".has"));await wait_job()
			app.world_selection.select_entity(reference_id);await settled()
			print("REFERENCE_OPEN "+JSON.stringify({"mode":mode,"actor":actor()!=null,"error":app.open_project_error,"status":app.status.text,"worker":app.has_project.pending}))
			check(actor()!=null and actor().data.scale==1. and actor().data.asset_basis==reference_record,"ordinary "+mode+" HAS retains exact reference and Scale1")
			check(Height.queries==queries and not app.height_review.pending,"ordinary "+mode+" Open does not fit again")
			if actor():check(absf(Height.query(actor()).height-Height.SIX_FEET)<.00002,"ordinary "+mode+" HAS keeps the reference geometry")
		var preview: Image=await app.renderer.capture(app.keys,app.layers,0,true)
		var export_error: String=await app.export_movie(folder)
		check(export_error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000001.png")).get_data()==preview.get_data(),"reference preview and MP4 input frame agree exactly")
		check(Drawing.image(Drawing.cel_at(app.layers[1],0)).get_pixel(80,80)==Color.CYAN,"reference workflow keeps the independent editable drawing")
		preview.save_png(folder.path_join("preview.png"))
		FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify({"id":reference_id}))
	# A full skeleton with only a head remains a part, never a complete human.
	app.new_project();check(not app.pose_editor.human_size_row.visible and not app.pose_editor.human_reference_note.visible,"clearing the active model hides the reference controls")
	var part:=folder.path_join("head.glb");check(Fixture.create(part,.75,.65,true)==OK,"partial fixture retains full skeleton")
	var context: Dictionary=app.import_actions.placement();context.physics_on_import=false;app.pose_editor.add_model(part,0,context);await wait_review()
	check(app.height_review.reference.disabled and not app.height_review.assessment.complete,"head-only geometry cannot receive a six-foot human reference")
	app.height_review.fit.button_pressed=false;app.height_review.apply();await settled()
	check(actor()!=null and actor().data.scale==1. and not actor().data.has("asset_basis"),"partial model keeps source size and no active reference")
	# Legacy single-model editing must not strip a captured intrinsic basis while
	# keeping its already-scaled runtime node alive.
	app.new_project();app.renderer.clear_assets()
	var prepared: Dictionary=app.renderer.prepare_model(normalized_definition)
	check(not prepared.has("error"),"legacy single-model constructor accepts the supported reference")
	if not prepared.has("error"):
		app.renderer.install_model(prepared)
		var before: Dictionary=actor().data.duplicate(true);var before_root: Transform3D=actor().root.transform
		var stripped:=before.duplicate(true);stripped.erase("asset_basis")
		check(not app.pose_editor.restore_state(stripped,false).is_empty() and actor().data==before and actor().root.transform==before_root,"same-source legacy fast edit refuses reference stripping atomically")
	for path in paths:check(FileAccess.get_sha256(path)==identities[path],"all original authored fixtures remain byte-identical")
	finish()

func finish() -> void:
	var result:={"checks":checks,"failures":failures}
	FileAccess.open(folder.path_join("result-reader.json" if OS.get_cmdline_user_args().size()>1 else "result.json"),FileAccess.WRITE).store_string(JSON.stringify(result))
	print("HUMAN_REFERENCE "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
