extends SceneTree
# Owned review entry. Product source remains the exact committed snapshot.
const Height=preload("res://src/character_height.gd")
const BodyPhysics=preload("res://src/physics_rig.gd")
const INPUT="res://review-input/vrm0/scene.glb"
const PARAMETERS="res://review-input/vrm0/parameters.json"
const INPUT_SHA="3caa50b76d0f481bb7ee66daeb6ebe7485aefb966140321b599ca60d9d464b56"
const PARAMETERS_SHA="0f8f746ca68a821acaf9e502b6895a2f2798d8d1d2bd62569d78deea652fc0ef"
var app
var folder: String
var verifying:=false
var verify_body_guard:=false
var checks: Array=[]
var failures: Array=[]
var input_time:=0
var parameters_time:=0
var reference_id:=""

func check(ok: bool,label: String) -> void:
	checks.append(label)
	print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures.append(label)

func _initialize() -> void:
	call_deferred("run")

func settled() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw

func actor():return app.renderer.active_model()

func linked_ancestor(path: String) -> bool:
	# The Python launchers additionally check Windows reparse attributes. A direct
	# entry still refuses every ancestor link visible to the engine filesystem.
	var filesystem:=DirAccess.open(ProjectSettings.globalize_path("res://"))
	if filesystem==null:return true
	var current:=path
	while not current.is_empty():
		if filesystem.is_link(current):return true
		var parent:=current.get_base_dir()
		if parent==current:break
		current=parent
	return false

func wait_review() -> void:
	while app.height_review.pending and not app.height_review.prepared:await process_frame
	await settled()

func wait_job() -> void:
	while app.has_project.pid>0:await process_frame
	await settled()

func unchanged() -> bool:
	return FileAccess.get_sha256(INPUT)==INPUT_SHA and FileAccess.get_sha256(PARAMETERS)==PARAMETERS_SHA and FileAccess.get_modified_time(INPUT)==input_time and FileAccess.get_modified_time(PARAMETERS)==parameters_time

func retained_model_state(subject: RefCounted) -> Dictionary:
	var topology: Array=[];var pending: Array=[subject.root]
	while not pending.is_empty():
		var node: Node=pending.pop_back();topology.append(node.get_instance_id());pending.append_array(node.get_children(true))
	var poses: Array=[]
	for id in subject.order:
		var info: Dictionary=subject.bones[id];poses.append(info.skeleton.get_bone_pose(info.index))
	return {"data":var_to_bytes(subject.data),"live_pose":var_to_bytes(subject.live_pose),"live_world":subject.live_world_transform,"root":subject.root.transform,"raw":subject.raw_import_root,"base":subject.base_root,"order":subject.order.duplicate(),"poses":poses,"topology":topology,"secondary":subject.root.get_meta("has_secondary_rig",{}).duplicate(true)}

func body_guard() -> void:
	# Explicit opt-in for guarded revisions. The original23-check run is retained
	# separately; this authored extension has no inherited execution claim.
	var before:=retained_model_state(actor())
	var result: Dictionary=BodyPhysics.create(actor())
	check(result.get("error","")=="Body Physics is not ready for this reference size. Posing and Hair & clothes are still available." and not result.has("physics"),"Body Physics clearly refuses the unsupported nonunit reference size before allocation")
	if result.has("physics"):result.physics.dispose()
	check(retained_model_state(actor())==before,"Body Physics refusal preserves model data, authored and live poses, reference roots, secondary metadata and topology")

func screenshot() -> String:
	var path:=folder.path_join("human-reference.png")
	check(root.get_texture().get_image().save_png(path)==OK,"Visible studio screenshot was saved inside this review")
	return path

func finish(status: String) -> void:
	check(unchanged(),"Prepared source and parameter bytes and modification times remain unchanged")
	var picture:=screenshot()
	var result:={"format":"has_native_human_reference_result_1","mode":"verify" if verifying else "owner","body_guard_requested":verify_body_guard,"status":status,"checks":checks.size(),"failures":failures.size(),"failed_checks":failures,"source_sha256":INPUT_SHA,"parameters_sha256":PARAMETERS_SHA,"reference_id":reference_id,"screenshot":picture,"scope":"Existing prepared VRM0 size-reference workflow; no native fidelity certification and no owner acceptance implied."}
	FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE).store_string(JSON.stringify(result,"\t",true,true))
	print("NATIVE_HUMAN_REFERENCE "+JSON.stringify(result))
	if verifying:
		app.free();quit(0 if failures.is_empty() else 1)
	else:
		app.message("Six-foot reference is ready. Scale 1 is the visible neutral reference; try Scale 0.5 or 2 in Human reference." if failures.is_empty() else "The review could not prepare the reference. See this review's result.json; the original source is unchanged.")

func run() -> void:
	var args:=OS.get_cmdline_user_args()
	if args.size()<2 or args.size()>3 or not args[0] in ["--owner","--verify"]:
		push_error("Use the owned review launcher or its private verifier.");quit(2);return
	verifying=args[0]=="--verify"
	if args.size()==3 and (not verifying or args[2]!="--body-guard"):
		push_error("The body guard check requires explicit private --verify mode.");quit(2);return
	verify_body_guard=args.size()==3
	folder=str(args[1]).replace("\\","/").simplify_path()
	var boundary:=ProjectSettings.globalize_path("res://output").replace("\\","/").simplify_path()+"/"
	if not folder.begins_with(boundary) or linked_ancestor(folder) or not DirAccess.dir_exists_absolute(folder) or FileAccess.file_exists(folder.path_join("result.json")):
		push_error("A fresh owned review output folder is required.");quit(2);return
	if verifying:create_timer(180).timeout.connect(func():push_error("Native human-reference review watchdog");quit(2))
	input_time=FileAccess.get_modified_time(INPUT);parameters_time=FileAccess.get_modified_time(PARAMETERS)
	if FileAccess.get_sha256(INPUT)!=INPUT_SHA or FileAccess.get_sha256(PARAMETERS)!=PARAMETERS_SHA:
		push_error("Prepared review input checksum differs.");quit(2);return
	app=load("res://main.tscn").instantiate()
	app.recovery_root=folder.path_join("recovery");app.display_prefs_path=folder.path_join("display.cfg")
	root.add_child(app);await settled()
	app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("has-cache")
	app.new_project();app.set_advanced(false);app.import_actions.offer_height=true;await settled()
	var context: Dictionary=app.import_actions.placement();context.physics_on_import=false
	var history: int=app.history.size()
	var why: String=app.pose_editor.add_model(ProjectSettings.globalize_path(INPUT),0,context)
	await wait_review()
	var eligible: bool=why.is_empty() and app.height_review.pending and app.height_review.assessment.get("complete",false) and app.height_review.assessment.get("error","").is_empty() and not app.height_review.reference.disabled
	check(eligible,"Existing prepared VRM0 is eligible for the explicit complete-human reference")
	check(actor()==null and app.history.size()==history,"Neutral review does not install a model or create an Undo entry")
	if not eligible:
		if app.height_review.pending:app.height_review.cancel()
		finish("eligibility_failed");return
	app.height_review.reference.button_pressed=true
	check(app.height_review.fit.button_pressed and not app.height_review.target.editable and app.height_review.target.get_line_edit().text=="1.8288","Six-foot reference selects and displays the exact target")
	app.height_review.apply();await settled()
	check(actor()!=null and app.history.size()==history+1,"Reference imports as one ordinary world Undo entry")
	if not actor():finish("import_failed");return
	reference_id=actor().data.id
	check(actor().data.scale==1. and actor().data.has("asset_basis"),"Imported artist scale is 1 with a separate intrinsic reference")
	check(actor().data.sha256==INPUT_SHA and actor().data.metadata.has("native_parameters"),"Imported reference retains the exact prepared source identity and native parameter report")
	check(absf(Height.query(actor()).height-Height.SIX_FEET)<.00002,"Visible neutral height equals six feet within 0.00002 scene units")
	app.pose_editor.frame_model();app.set_advanced(false);await settled()
	check(app.pose_editor.human_size_row.is_visible_in_tree() and app.pose_editor.human_reference_note.is_visible_in_tree(),"Simple mode displays Human reference size controls")
	if not verifying:finish("owner_ready" if failures.is_empty() else "failed");return
	if verify_body_guard:body_guard()
	var reference: Dictionary=actor().data.asset_basis.duplicate(true)
	for size in [.5,2.]:
		app.pose_editor.human_size_field.value=size;app.pose_editor.human_size_apply.pressed.emit();await settled()
		check(absf(Height.query(actor()).height-Height.SIX_FEET*size)<.00002,"Artist scale "+str(size)+" changes the actual geometry height")
		check(actor().data.asset_basis==reference,"Artist size edits preserve the intrinsic reference")
		app.undo();await settled()
		check(absf(Height.query(actor()).height-Height.SIX_FEET)<.00002,"Undo restores reference height after scale "+str(size))
		app.redo();await settled()
		check(absf(Height.query(actor()).height-Height.SIX_FEET*size)<.00002,"Redo restores relative height at scale "+str(size))
		app.undo();await settled()
	var project:=folder.path_join("native-reference.has")
	var queries:=Height.queries
	app.has_project.save_file(project,"packed");await wait_job()
	check(FileAccess.file_exists(project),"Ordinary packed HAS save creates the review project")
	if not FileAccess.file_exists(project):finish("save_failed");return
	app.new_project();app.has_project.open_file(project);await wait_job()
	app.world_selection.select_entity(reference_id);await settled()
	check(actor()!=null and app.open_project_error.is_empty(),"Packed reopen explicitly reselects the imported model")
	check(Height.queries==queries and not app.height_review.pending,"Saving and reopening do not remeasure or open a height review")
	if actor():
		check(actor().data.scale==1. and actor().data.asset_basis==reference,"Packed reopen retains exact reference facts and artist scale 1")
		check(absf(Height.query(actor()).height-Height.SIX_FEET)<.00002,"Packed reopen applies the intrinsic reference exactly once")
		app.pose_editor.frame_model();app.set_advanced(false);await settled()
	finish("passed" if failures.is_empty() else "failed")
