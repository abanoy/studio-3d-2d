extends SceneTree
const Height=preload("res://src/character_height.gd")
const Model=preload("res://src/model.gd")
const Fixture=preload("res://tests/height_fixture.gd")
const Drawing=preload("res://src/drawing.gd")
var checks:=0
var failures:=0
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func _initialize() -> void:
	create_timer(215).timeout.connect(func():push_error("Height review watchdog");quit(2));call_deferred("run")
func settled() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func wait_review(review) -> void:
	while review.pending and not review.prepared:await process_frame
	await settled()
func wait_job(job) -> void:
	while job.pid>0:await process_frame
	await settled()
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0];var plans: Array=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("plans.json")))
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled();app.autosave_enabled.button_pressed=false
	app.has_project.cache_root=folder.path_join("has-cache")
	if args.size()>1:
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")));app.has_project.open_file(folder.path_join("height-packed.has"));await wait_job(app.has_project)
		var actor: RefCounted=app.renderer.world_runtime.instance(expected.id);check(actor!=null,"cold Open restores fitted standard model")
		if actor:
			check(actor.data.metadata==expected.metadata and PackedFloat32Array([actor.data.scale]).to_byte_array().hex_encode()==expected.scale_bits and Height.queries==0,"cold Open preserves exact engine scale and measurement provenance without re-analysis")
			app.set_frame(12);var measured:=Height.query(actor);check(absf(measured.height-Height.SIX_FEET)<.00002,"cold fitted geometry keeps its target height")
			check(Drawing.image(Drawing.cel_at(app.layers[1],12)).get_pixel(80,80)==Color.CYAN,"cold fitted scene keeps independent editable drawing")
		var result:={"checks":checks,"failures":failures};print("CHARACTER_HEIGHT_READER "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1);return
	var context: Dictionary=app.import_actions.placement();context.physics_on_import=false
	var queries:=Height.queries;var error: String=app.pose_editor.add_model(plans[0].source,0,context)
	check(error.is_empty() and not app.height_review.pending and Height.queries==queries and app.renderer.active_model().data.scale==1.,"default unchecked imports without extra height analysis or fitting")
	app.new_project();app.show_project_options();app.height_choice.button_pressed=true;app.project_options.hide()
	check(app.import_actions.offer_height and app.import_actions.placement().review_height,"Options carries explicit per-session choice into import context")
	for entry in [["Short legs",.35,.9],["Long legs",2.5,.25],["Head with full rig",.9,.75]]:
		var path:=folder.path_join(str(entry[0])+".glb");check(Fixture.create(path,entry[1],entry[2],entry[0]=="Head with full rig")==OK,"authored proportion/coverage fixture exports")
		plans.append({"label":entry[0],"source":path,"metadata":{},"rotation":[0,0,0,1]})
	var last_fit:={}
	var results:=[]
	for plan in plans:
		app.new_project();context=app.import_actions.placement();context.physics_on_import=false
		var data: Dictionary=app.pose_editor.definition(plan.source).data;data.rotation_xyzw=plan.rotation
		if not plan.metadata.is_empty():data.metadata=plan.metadata.duplicate(true)
		var original: Dictionary=data.duplicate(true);var keys: Array=app.keys.duplicate(true);var view: Dictionary=app.renderer.view_state();var history: int=app.history.size()
		error=app.append_object(data,"model",12,context);var review=app.height_review;await wait_review(review)
		check(error.is_empty() and review.pending and review.prepared and app.renderer.active_model()==null,"review happens before world installation: "+plan.label)
		check(app.history.size()==history and app.keys==keys and app.renderer.view_state()==view and data==original,"measurement leaves scene/history/camera/source definition untouched: "+plan.label)
		print("HEIGHT_RESULT "+str(plan.label)+" "+JSON.stringify(review.assessment))
		if review.assessment.is_empty():check(false,"height assessment produced a result");review.cancel();continue
		var measured: Dictionary=review.assessment.duplicate(true)
		if plan.label in ["Supplied Mima","Head with full rig"]:
			check(not measured.complete and review.fit.disabled and not review.fit.button_pressed,"separate head cannot be normalized as a whole person: "+plan.label)
		else:check(measured.complete and measured.height>0 and not review.fit.disabled,"actual full character has head and both-leg skin coverage: "+plan.label)
		if plan.label in ["Short legs","Long legs"]:check(not measured.suggest_fit and not review.fit.button_pressed,"nonstandard proportions stay unchecked until explicit choice: "+plan.label)
		if plan.label in ["Authored figure","VRM1.0"]:
			root.get_texture().get_image().save_png(folder.path_join("height-ui.png"));last_fit={"data":data.duplicate(true),"context":context.duplicate(true)}
		if plan.label=="VRM1.0":
			queries=Height.queries;var was_fit: bool=review.fit.button_pressed;app.set_advanced(true);await settled()
			check(review.advanced_info.visible and review.pending and review.fit.button_pressed==was_fit and Height.queries==queries,"Advanced reveals measurement provenance without resetting the pending choice")
			root.get_texture().get_image().save_png(folder.path_join("height-advanced-ui.png"));app.set_advanced(false);await settled()
			check(not review.advanced_info.visible and review.pending,"Simple hides diagnostics while retaining the same measurement and choice")
			check(review.accept.get_global_rect().end.y<=review.window.size.y,"height Add action stays pinned inside the actual review window")
		if measured.complete:review.fit.button_pressed=true
		review.accept.pressed.emit();await settled();var actor: RefCounted=app.renderer.active_model()
		check(actor!=null and not review.pending and app.history.size()==history+1,"Add commits one ordinary world Undo: "+plan.label)
		if not actor:continue
		check(actor.data.get("start_frame")==12 and actor.authored_keys().is_empty() and app.keys==keys,"fit preserves import timing without implicit pose or camera keys: "+plan.label)
		if measured.complete:
			check(not actor.root.visible,"future import remains absent before its introduction: "+plan.label)
			app.set_frame(12);await settled()
			var now:=Height.query(actor)
			print("HEIGHT_AFTER "+str(plan.label)+" "+JSON.stringify(now))
			check(absf(float(now.height)-Height.SIX_FEET)<.00002 and actor.data.metadata.import_height.source_sha256==data.sha256,"fitted neutral geometry reaches target using shared root scale: "+plan.label)
			check(actor.data.sha256==data.sha256 and actor.data.metadata.import_height.original_root_scale.to_float()==1.,"source hash and original root scale provenance survive: "+plan.label)
		else:check(actor.data.scale==1. and not actor.data.metadata.has("import_height"),"declined/ineligible part remains at original size")
		results.append({"label":plan.label,"assessment":measured,"scale":actor.data.scale})
		app.undo();await settled();check(app.renderer.world_runtime.instances.is_empty(),"Undo removes the fitted import as a whole: "+plan.label);app.redo();await settled()
	# Cancellation and New revoke pending work before the deferred load installs it.
	app.new_project();context=app.import_actions.placement();context.physics_on_import=false;app.pose_editor.add_model(plans[0].source,0,context);app.height_review.cancel();await settled()
	check(not app.height_review.pending and app.renderer.world_runtime.instances.is_empty(),"Cancel before deferred measurement adds nothing")
	app.pose_editor.add_model(plans[0].source,0,context);app.new_project();await settled()
	check(not app.height_review.pending and app.renderer.world_runtime.instances.is_empty(),"New invalidates pending review without late replacement")
	queries=Height.queries;app.pose_editor.add_model(plans[0].source,0,context);app.height_review.cancel();app.pose_editor.add_model(plans[0].source,0,context);await wait_review(app.height_review)
	check(Height.queries==queries+1,"cancel/reopen cannot run a stale deferred measurement on the replacement request");app.height_review.cancel()
	# Explicit decline leaves a complete figure at its source scale.
	app.pose_editor.add_model(plans[0].source,0,context);await wait_review(app.height_review);app.height_review.fit.button_pressed=false;app.height_review.apply();await settled()
	check(app.renderer.active_model().data.scale==1. and not app.renderer.active_model().data.metadata.has("import_height"),"unchecked review preserves original root scale without fit metadata")
	app.new_project();queries=Height.queries;error=app.append_object(Model.definition("res://examples/tutorials/Practice room.glb"),"environment",0,context)
	check(error.is_empty() and not app.height_review.pending and Height.queries==queries,"maps never enter human-height normalization")
	# Save/Open does not reapply a fit. Standard scale/metadata needs no new schema.
	app.new_project();app.append_object(last_fit.data,"model",12,last_fit.context);await wait_review(app.height_review);app.height_review.fit.button_pressed=true;app.height_review.apply();app.set_frame(12);await settled()
	var actor: RefCounted=app.renderer.active_model();var id: String=actor.data.id
	Drawing.insert(app.layers[1],0,48,Drawing.blank(1920,1080));Drawing.edit_image(Drawing.cel_at(app.layers[1],12)).image.set_pixel(80,80,Color.CYAN)
	app.pose_editor.frame_model();app.keys=[Model.Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,55)];app.set_frame(12)
	var metadata: Dictionary=JSON.parse_string(JSON.stringify(actor.data.metadata,"",true,true));var chosen_scale: float=actor.data.scale
	for mode in ["packed","linked"]:
		app.has_project.save_file(folder.path_join("height-"+mode+".has"),mode);await wait_job(app.has_project);app.new_project();queries=Height.queries;app.has_project.open_file(folder.path_join("height-"+mode+".has"));await wait_job(app.has_project);actor=app.renderer.world_runtime.instance(id)
		var same_metadata: bool=actor!=null and JSON.parse_string(JSON.stringify(actor.data.metadata,"",true,true))==metadata
		print("HEIGHT_PERSIST "+JSON.stringify({"mode":mode,"metadata_equal":same_metadata,"scale_equal":Vector3.ONE*actor.data.scale==Vector3.ONE*chosen_scale,"queries_before":queries,"queries_after":Height.queries}))
		check(actor!=null and same_metadata and Vector3.ONE*actor.data.scale==Vector3.ONE*chosen_scale and Height.queries==queries,"ordinary "+mode+" HAS preserves exact engine scale/provenance without double normalization")
	var preview: Image=await app.renderer.capture(app.keys,app.layers,12,true);preview.save_png(folder.path_join("middle.png"));var export_error: String=await app.export_movie(folder)
	check(export_error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000013.png")).get_data()==preview.get_data(),"ordinary MP4 keeps exact fitted frame and independent drawing")
	FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify({"id":id,"metadata":metadata,"scale":chosen_scale,"scale_bits":PackedFloat32Array([chosen_scale]).to_byte_array().hex_encode()},"",true,true))
	var result:={"checks":checks,"failures":failures,"models":results,"movie":app.last_export_folder.path_join("movie.mp4")};FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("CHARACTER_HEIGHT_APP "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
