extends SceneTree
# Focused recorded-time boundary: a held world body under an authored moving,
# rotating and uniformly scaling parent must replay that same world root.
const Fixture=preload("res://tests/reference_body_workflow_fixture.gd")
const Model=preload("res://src/model.gd")
const Timeline=preload("res://src/timeline.gd")
const Height=preload("res://src/character_height.gd")
var app
var folder: String
var checks:=0
var failures:=0
var metrics: Dictionary={}
var cold:=false

func _initialize() -> void:
	create_timer(150).timeout.connect(func():push_error("Reference body parent watchdog expired");quit(2))
	call_deferred("run")

func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1

func settled() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw

func wait_job() -> void:
	while app.has_project.pid>0:await process_frame
	await settled()

func transform(value: Dictionary) -> Transform3D:
	return Transform3D(Basis(Timeline.quaternion(value.rotation_xyzw)).scaled(Vector3.ONE*value.scale),Timeline.vector(value.position))

func difference(a: Transform3D,b: Transform3D) -> float:
	return maxf(a.origin.distance_to(b.origin),maxf(a.basis.x.distance_to(b.basis.x),maxf(a.basis.y.distance_to(b.basis.y),a.basis.z.distance_to(b.basis.z))))

func portable_data(data: Dictionary) -> Dictionary:
	# Packed projects legitimately resolve source to their verified extraction.
	# Every other authored field must match; source bytes are checked separately.
	var value: Dictionary=JSON.parse_string(JSON.stringify(data,"",true,true));value.erase("source");value.erase("path");return value

func encoded(value: Transform3D) -> Dictionary:
	return {"position":[value.origin.x,value.origin.y,value.origin.z],"x":[value.basis.x.x,value.basis.x.y,value.basis.x.z],"y":[value.basis.y.x,value.basis.y.y,value.basis.y.z],"z":[value.basis.z.x,value.basis.z.y,value.basis.z.z]}

func decoded(value: Dictionary) -> Transform3D:
	return Transform3D(Basis(Timeline.vector(value.x),Timeline.vector(value.y),Timeline.vector(value.z)),Timeline.vector(value.position))

func replay_error(child,parent,held: Transform3D) -> float:
	var error:=0.
	for frame in range(13):
		# Independent frame algebra uses stored parent/child authoring samples;
		# it does not call PhysicsRig.root_transform or the live solver.
		var parent_world: Transform3D=parent.root.get_parent().global_transform*transform(parent.sample_transform(frame))*parent.base_root
		var child_world: Transform3D=parent_world*transform(child.sample_transform(frame))*child.base_root
		error=maxf(error,difference(child_world,held))
	return error

func finish() -> void:
	var result:={"checks":checks,"failures":failures,"metrics":metrics}
	FileAccess.open(folder.path_join("result-reader.json" if cold else "result.json"),FileAccess.WRITE).store_string(JSON.stringify(result,"",true,true))
	print("REFERENCE_BODY_PARENT "+JSON.stringify(result,"",true,true));app.free();quit(0 if failures==0 else 1)

func read_project() -> void:
	var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
	app.has_project.open_file(folder.path_join("parented-reference.has"));await wait_job()
	var child=app.renderer.world_runtime.instance(expected.id) if app.renderer.world_runtime else null
	var parent=app.renderer.world_runtime.instance(expected.parent_id) if app.renderer.world_runtime else null
	check(child!=null and parent!=null and app.open_project_error.is_empty() and not app.physics_editor.is_running(),"independent cold process restores the recorded parent/reference world without simulation")
	if child==null or parent==null:finish();return
	check(child.data.asset_basis==expected.basis and JSON.parse_string(JSON.stringify(child.authored_keys(),"",true,true))==expected.keys and child.authored_keys().size()==13,"cold reader retains exact reference facts and13 ordinary editable samples")
	check(portable_data(parent.data)==expected.parent and parent.data.sha256==expected.source_sha and FileAccess.get_sha256(parent.data.source)==expected.source_sha and FileAccess.get_sha256(child.data.source)==expected.source_sha,"cold reader keeps all parent authoring and verified source bytes across legitimate cache paths")
	var held:=decoded(expected.held);var error:=replay_error(child,parent,held);metrics["cold_recorded_world_root_error"]=error
	check(error<.0002,"cold reader independently reconstructs the held world root at all13 recorded frames")
	app.set_frame(6);await settled()
	check(difference(child.root.global_transform,held)<.0002,"actual cold playback evaluates the frame6 world root without doubled intrinsic scale")
	check(Height.queries==0 and not app.height_review.pending and app.physics_editor.import_starts.is_empty() and not child.bones[child.order[0]].skeleton.has_meta("has_live_frame_pose_1"),"cold parented playback does not fit, rearm or retain live solver metadata")
	finish()

func parent_drift_cases(original: Dictionary,child_id: String,parent_id: String) -> void:
	for immediate in [false,true]:
		app.set_frame(0);app.restore_world(original);app.world_selection.select_entity(child_id);await settled()
		var child=app.renderer.world_runtime.instance(child_id);var parent=app.renderer.world_runtime.instance(parent_id)
		var child_before: Dictionary=child.data.duplicate(true);var history: int=app.history.size()
		app.physics_editor.toggle.button_pressed=true;var record=app.physics_editor.recording;record.scope.select(0);record.button.pressed.emit()
		var label:="immediate Stop" if immediate else "next fixed tick"
		check(record.active and record.reference_parent_data.has(parent_id),label+": actual parented body capture snapshots the authored ancestor")
		if not record.active:continue
		while record.active and record.last_frame<2:await process_frame
		parent.data.metadata["reference_parent_drift"]="keep this independent edit";app.changed()
		var edited: Dictionary=parent.data.duplicate(true);var finished:=false
		if immediate:finished=record.finish("explicit stop")
		else:
			for i in range(4):await physics_frame
		check(not record.active and not app.physics_editor.is_running() and (not immediate or not finished) and child.data==child_before and parent.data==edited and app.history.size()==history and record.reference_world_roots.is_empty() and record.reference_parent_data.is_empty(),label+": changed parent cancels the take, preserves the independent edit and clears ownership")

func run() -> void:
	var args:=OS.get_cmdline_user_args();folder=args[0];cold=args.size()>1 and args[1]=="reader";DirAccess.make_dir_recursive_absolute(folder)
	metrics["project_root"]=ProjectSettings.globalize_path("res://").replace("\\","/").simplify_path().trim_suffix("/")
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recent.json");app.display_prefs_path=folder.path_join("display.cfg");root.add_child(app);await settled()
	app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	if cold:await read_project();return
	var source:=folder.path_join("public-parent-reference.glb")
	check(Fixture.create(source)==OK,"original public parent/reference source exports")
	var source_sha:=FileAccess.get_sha256(source)
	app.new_project();app.load_demo_room();app.video.fps_num=25;app.video.fps_den=2;app.video.duration_frames=12
	app.import_actions.offer_height=true;var context: Dictionary=app.import_actions.placement();context.physics_on_import=false
	var error: String=app.pose_editor.add_model(source,0,context)
	while app.height_review.pending and not app.height_review.prepared:await process_frame
	check(error.is_empty() and app.height_review.pending and not app.height_review.reference.disabled,"actual import review offers the explicit human reference")
	if not app.height_review.pending or app.height_review.reference.disabled:finish();return
	app.height_review.reference.button_pressed=true;app.height_review.apply();await settled()
	var child=app.renderer.active_model();var child_id: String=child.data.id;var basis: Dictionary=child.data.asset_basis.duplicate(true)
	check(child.data.scale==1. and child.data.has("asset_basis"),"reference import leaves artist Scale1 and retains its intrinsic factor")
	var world: Dictionary=app.renderer.world_state();var parent:=Model.definition(source)
	parent.id="animated-reference-parent";parent.kind="group";parent.parent_id="";parent.start_frame=0
	parent.position=[1.,.2,-.4];parent.rotation_xyzw=[0.,sin(.2),0.,cos(.2)];parent.scale=1.4
	var first:={"position":parent.position.duplicate(),"rotation_xyzw":parent.rotation_xyzw.duplicate(),"scale":1.4}
	var last:={"position":[3.,.6,-1.4],"rotation_xyzw":[0.,sin(.6),0.,cos(.6)],"scale":1.8}
	parent.pose_keys=[{"frame":0,"pose":{},"transform":first,"interpolation":"linear"},{"frame":12,"pose":{},"transform":last,"interpolation":"linear"}]
	world.objects.append(parent)
	for row in world.objects:
		if row.id==child_id:row.parent_id=parent.id;row.position=[.2,2.4,-.2];row.scale=.5
	error=app.restore_world(world);app.mode.select(1);app.change_mode(1);app.world_selection.select_entity(child_id);await settled()
	child=app.renderer.world_runtime.instance(child_id);var parent_actor=app.renderer.world_runtime.instance(parent.id)
	check(error.is_empty() and child.root.get_parent()==parent_actor.root,"actual world installs the reference beneath an animated positive-uniform parent")
	var before: Dictionary=app.renderer.world_state();var parent_before: Dictionary=parent_actor.data.duplicate(true);var history: int=app.history.size()
	var held: Transform3D=child.root.global_transform;var initial_parent: Transform3D=parent_actor.root.global_transform
	app.physics_editor.toggle.button_pressed=true
	check(app.physics_editor.body_active(child_id),"connected body toggle accepts the reference at its actual inherited size")
	if not app.physics_editor.body_active(child_id):finish();return
	var record=app.physics_editor.recording;record.scope.select(0);record.button.pressed.emit()
	check(record.active and record.targets.keys()==[child_id],"Local Record captures only the child reference under the authored parent")
	if not record.active:finish();return
	var live_drift:=0.;var parent_motion:=0.
	while record.active:
		await process_frame
		if record.active:
			live_drift=maxf(live_drift,difference(child.root.global_transform,held))
			parent_motion=maxf(parent_motion,difference(parent_actor.root.global_transform,initial_parent))
	await settled();child=app.renderer.world_runtime.instance(child_id);parent_actor=app.renderer.world_runtime.instance(parent.id)
	check(record.last_error.is_empty() and record.ticks==116 and child.authored_keys().size()==13 and app.history.size()==history+1 and not app.physics_editor.is_running(),"rational parented capture produces13 ordinary samples in one Undo")
	check(parent_motion>.5 and live_drift<.0002,"parent actually moves while the live child root stays fixed in world space")
	check(parent_actor.data==parent_before and child.data.asset_basis==basis and FileAccess.get_sha256(source)==source_sha,"recording leaves authored parent, intrinsic reference and original source intact")
	var error_replay:=replay_error(child,parent_actor,held);metrics.merge({"maximum_live_root_error":live_drift,"parent_motion":parent_motion,"maximum_recorded_world_root_error":error_replay,"ticks":record.ticks,"samples":child.authored_keys().size()})
	check(error_replay<.0002,"every stored child root compensates the parent at that exact recorded frame")
	var recorded: Dictionary=app.renderer.world_state();app.undo()
	check(app.renderer.world_state()==before,"Undo restores the exact parented pre-take world")
	app.redo();check(app.renderer.world_state()==recorded,"Redo restores both authoring and ordinary recorded compensation")
	var project:=folder.path_join("parented-reference.has");app.has_project.save_file(project,"packed");await wait_job()
	check(FileAccess.file_exists(project) and not app.physics_editor.is_running(),"parented reference recording saves without live simulation")
	var expected:={"id":child_id,"parent_id":parent.id,"basis":basis,"held":encoded(held),"parent":portable_data(parent_before),"source_sha":source_sha,"keys":JSON.parse_string(JSON.stringify(child.authored_keys(),"",true,true))}
	FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify(expected,"",true,true))
	app.new_project();app.has_project.open_file(project);await wait_job();app.set_frame(6)
	child=app.renderer.world_runtime.instance(child_id);parent_actor=app.renderer.world_runtime.instance(parent.id)
	var reopened:=replay_error(child,parent_actor,held);metrics["reopened_world_root_error"]=reopened
	var diagnostic:={"expected_parent":portable_data(parent_before),"actual_parent":portable_data(parent_actor.data),"basis_equal":child.data.asset_basis==basis,"source_hash":FileAccess.get_sha256(parent_actor.data.source),"original_hash":source_sha,"world_root_error":reopened}
	FileAccess.open(folder.path_join("packed-diagnostic.json"),FileAccess.WRITE).store_string(JSON.stringify(diagnostic,"",true,true))
	check(not app.physics_editor.is_running() and reopened<.0002 and child.data.asset_basis==basis and portable_data(parent_actor.data)==portable_data(parent_before) and parent_actor.data.sha256==source_sha and FileAccess.get_sha256(parent_actor.data.source)==source_sha,"packed reopen keeps exact parent motion, verified source bytes and frame-correct child world roots")
	await parent_drift_cases(before,child_id,parent.id)
	finish()
