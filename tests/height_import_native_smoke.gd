extends SceneTree
const Height=preload("res://src/character_height.gd")
var checks:=0
var failures:=0
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func _initialize() -> void:
	create_timer(90).timeout.connect(func():push_error("Native height review watchdog");quit(2));call_deferred("run")
func settled() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0];var input: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("raw-vrm.json")))
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("native-recovery");root.add_child(app);await settled();app.autosave_enabled.button_pressed=false;app.import_actions.offer_height=true
	var context: Dictionary=app.import_actions.placement();var keys: Array=app.keys.duplicate(true);var view: Dictionary=app.renderer.view_state()
	app.source_import.start(input.source,true,0,context)
	while app.source_import.pid>0:await process_frame
	while app.height_review.pending and not app.height_review.prepared:await process_frame
	await settled();var review=app.height_review
	check(review.pending and review.prepared and review.assessment.get("complete",false),"actual raw VRM worker passes its import context into completed height review")
	if not review.pending:app.free();quit(1);return
	check(app.renderer.active_model()==null and not app.physics_editor.is_running() and app.history.is_empty(),"native review precedes world mutation and automatic physics")
	check(app.keys==keys and app.renderer.view_state()==view,"native preparation/review leaves shot and temporary camera exact")
	app.source_import.start(input.source,true,0,context);check(app.source_import.pid<0 and review.pending,"another native start defers without replacing the pending review")
	# Close only the owned adapter limitations message before using the review.
	for child in app.get_children():
		if child is AcceptDialog and child.visible:child.hide();child.queue_free()
	var pending: Dictionary=review.data.duplicate(true);var id: String=pending.id;review.fit.button_pressed=true;review.apply();await settled()
	var deadline:=Time.get_ticks_msec()+10000
	while not app.physics_editor.pending.is_empty() and Time.get_ticks_msec()<deadline:await process_frame
	await settled();var actor: RefCounted=app.renderer.world_runtime.instance(id)
	check(actor!=null and actor.data.scale>1 and actor.data.metadata.import_height.source_sha256==pending.sha256,"fitted native model installs once with retained source provenance")
	check(actor!=null and app.physics_editor.active(id) and actor.authored_keys().is_empty(),"default body physics starts only after accepting the fitted import, without recording keys")
	if actor:
		var scale: float=actor.data.scale;app.physics_editor.freeze_all();await settled();check(actor.data.scale==scale,"physics stop keeps chosen standardized root scale")
	# A stale source file cannot be accepted after review. Only owned fixture bytes change.
	app.new_project();context.physics_on_import=false
	var path:=folder.path_join("mutable.glb");var original:=FileAccess.get_file_as_bytes("res://examples/tutorials/Practice figure.glb");FileAccess.open(path,FileAccess.WRITE).store_buffer(original)
	app.pose_editor.add_model(path,0,context)
	while app.height_review.pending and not app.height_review.prepared:await process_frame
	var changed:=original.duplicate();changed[changed.size()-1]^=1;FileAccess.open(path,FileAccess.WRITE).store_buffer(changed);app.height_review.apply()
	check(app.height_review.pending and app.renderer.active_model()==null and "source changed" in app.height_review.info.text,"changed source refuses before installation or cached fit reuse")
	FileAccess.open(path,FileAccess.WRITE).store_buffer(original);app.height_review.cancel()
	# Teardown before a deferred load must not leave owned render/window resources.
	app.pose_editor.add_model(path,0,context);var weak: WeakRef=weakref(app.height_review);app.free();await settled()
	check(weak.get_ref()==null,"application teardown releases a pending height review cleanly")
	var result:={"checks":checks,"failures":failures};print("HEIGHT_IMPORT_NATIVE "+JSON.stringify(result));quit(0 if failures==0 else 1)
