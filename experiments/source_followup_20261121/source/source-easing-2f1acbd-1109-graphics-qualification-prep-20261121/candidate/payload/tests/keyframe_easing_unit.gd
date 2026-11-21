extends SceneTree
# Source-only transaction controls. No camera render/export/native asset is used.
const Editor=preload("res://src/camera_easing_editor.gd")
const Timeline=preload("res://src/timeline.gd")
var checks:=0
var failures:=0
class Physics extends RefCounted:
	var recording: Dictionary={"active":false}
	var running:=false
	func is_running() -> bool: return running
class CameraDraft extends RefCounted:
	var draft:=false
	func has_draft() -> bool: return draft
class RendererSpy extends RefCounted:
	var calls:=0
	var last_frame:=-1
	var last_keys: Array=[]
	func evaluate(keys: Array,frame: int) -> void:
		calls+=1;last_frame=frame;last_keys=keys.duplicate(true)
class App extends RefCounted:
	var keys: Array=[]
	var video: Dictionary={"duration_frames":20,"fps_num":24,"fps_den":1}
	var frame:=2
	var recovery_session:="test-session"
	var recovery_revision:=0
	var mode: Dictionary={"selected":1}
	var exporting:=false
	var playing:=false
	var navigating:=false
	var drawing:=false
	var dialog:=false
	var source_import: Dictionary={"pid":0}
	var has_project: Dictionary={"pid":0}
	var pose_editor: Dictionary={"dragging":false}
	var physics_editor: RefCounted=Physics.new()
	var camera_transform_editor: RefCounted=CameraDraft.new()
	var sequence_editor: Dictionary={"active_owner":""}
	var renderer: RefCounted=RendererSpy.new()
	var history: Array=[]
	var messages: Array=[]
	var changed_count:=0
	var set_frame_count:=0
	var unrelated: Dictionary={"paint":[1,2,3],"world":{"poses":"unchanged"},"physics":"off"}
	func has_dialog(_owner) -> bool: return dialog
	func message(value: String) -> void: messages.append(value)
	func push_history(value: Dictionary) -> void: history.append(value.duplicate(true))
	func changed() -> void: changed_count+=1;recovery_revision+=1
	func set_frame(value: int) -> void: frame=value;set_frame_count+=1;renderer.evaluate(keys,value)
func check(value: bool,label: String) -> void:
	checks+=1
	if not value: failures+=1
	print(("PASS " if value else "FAIL ")+"easing_editor."+label)
func key(frame: int,x: float,mode: String="linear") -> Dictionary:
	var row: Dictionary=Timeline.key(frame,Vector3(x,1,3),Quaternion.IDENTITY,55.,mode)
	row["near"]=0.05;row["far"]=2000.
	return row
func fixture(duration:=20) -> Dictionary:
	var app:=App.new();app.video.duration_frames=duration
	app.keys=[key(0,0),key(int(duration/2),10),key(duration,20)]
	var editor:=Editor.new();editor.app=app;editor.open()
	return {"app":app,"editor":editor,"before":app.keys.duplicate(true),"other":app.unrelated.duplicate(true)}
func close(f: Dictionary) -> void:
	f.editor.app=null;f.editor.free()
func ready(f: Dictionary) -> bool:
	return f.editor.set_controls_at(0,0.,1.).is_empty() and f.editor.preview().is_empty() and f.editor.preview_active()
func _initialize() -> void:
	create_timer(15).timeout.connect(func():push_error("Easing editor controls watchdog");quit(2))
	call_deferred("run")
func run() -> void:
	var f: Dictionary=fixture()
	check(f.editor.valid_context() and not f.editor.preview_active() and f.app.history.is_empty(),"open_is_a_readonly_session")
	check(ready(f),"explicit_recipe_can_preview")
	check(f.app.keys==f.before and f.app.unrelated==f.other and f.app.history.is_empty() and f.app.changed_count==0,"preview_writes_no_keys_world_or_history")
	var sample: Dictionary=f.editor.sample_preview(f.app.keys,2)
	var plain: Dictionary=Timeline.sample(f.app.keys,2)
	check(not sample.is_empty() and sample.position.x<plain.position.x,"preview_sampler_uses_departure_control")
	check(f.editor.sample_preview(f.app.keys,0).position.is_equal_approx(Timeline.sample(f.app.keys,0).position) and f.editor.sample_preview(f.app.keys,10).position.is_equal_approx(Timeline.sample(f.app.keys,10).position),"preview_keeps_authored_key_endpoints")
	var saved_plan: PackedByteArray=var_to_bytes(f.editor.plan)
	f.editor.preview()
	check(saved_plan==var_to_bytes(f.editor.plan) and f.app.keys==f.before and f.app.history.is_empty(),"recalculate_is_deterministic_and_nonaccumulating")
	var changed_keys: Array=f.app.keys.duplicate(true);changed_keys[1].fov=60.
	check(f.editor.sample_preview(changed_keys,2).is_empty(),"foreign_key_stream_gets_original_sampler")
	f.app.exporting=true
	check(f.editor.sample_preview(f.app.keys,2).is_empty() and f.app.keys==f.before,"export_guard_bypasses_temporary_sampler")
	f.app.exporting=false;var evaluations: int=f.app.renderer.calls
	f.editor.discard()
	check(not f.editor.preview_active() and f.editor.context.is_empty() and f.editor.controls.is_empty() and f.app.keys==f.before and f.app.history.is_empty(),"discard_clears_only_session_recipe")
	check(f.app.renderer.calls==evaluations+1 and f.app.changed_count==0,"discard_restores_authored_evaluation_without_changed")
	close(f)

	f=fixture();ready(f);var old_controls: PackedByteArray=var_to_bytes(f.editor.controls);var old_plan: PackedByteArray=var_to_bytes(f.editor.plan)
	var error: String=f.editor.set_controls_at(0,0.,2.)
	check(not error.is_empty() and old_controls==var_to_bytes(f.editor.controls) and old_plan==var_to_bytes(f.editor.plan) and f.editor.preview_active(),"invalid_recipe_edit_keeps_previous_preview_atomic")
	var previous_calls: int=f.app.renderer.calls
	error=f.editor.set_controls_at(0,0.,0.5)
	check(error.is_empty() and not f.editor.preview_active() and f.app.renderer.calls==previous_calls+1 and f.app.keys==f.before,"valid_recipe_edit_returns_to_authored_until_recalculate")
	close(f)

	for kind in ["session","video","keys","child_scene"]:
		f=fixture();ready(f)
		match kind:
			"session": f.app.recovery_session="different-session"
			"video": f.app.video.fps_num=30
			"keys": f.app.keys[1].position[0]=123.
			"child_scene": f.app.sequence_editor.active_owner="nested-scene"
		var before: PackedByteArray=var_to_bytes(f.app.keys)
		check(not f.editor.preview_active() and f.editor.sample_preview(f.app.keys,2).is_empty() and f.app.history.is_empty() and var_to_bytes(f.app.keys)==before,"stale_context_rejects_without_undo_"+kind)
		f.editor._process(0.)
		check(f.editor.context.is_empty() and f.editor.controls.is_empty(),"stale_context_lifetime_clears_recipe_"+kind)
		close(f)

	f=fixture();ready(f);f.editor.plan.segments[0].leave=0.25
	check(f.editor.sample_preview(f.app.keys,2).is_empty() and not f.editor.preview_active() and f.app.keys==f.before and f.app.history.is_empty(),"tampered_plan_cannot_be_sampled_or_baked")
	close(f)

	for kind in ["export","playback","navigation","dialog","source_worker","project_worker","pose_mode","drawing","pose_drag","record","live_physics","camera_draft","nested_scene"]:
		f=fixture()
		match kind:
			"export": f.app.exporting=true
			"playback": f.app.playing=true
			"navigation": f.app.navigating=true
			"dialog": f.app.dialog=true
			"source_worker": f.app.source_import.pid=10
			"project_worker": f.app.has_project.pid=20
			"pose_mode": f.app.mode.selected=2
			"drawing": f.app.drawing=true
			"pose_drag": f.app.pose_editor.dragging=true
			"record": f.app.physics_editor.recording.active=true
			"live_physics": f.app.physics_editor.running=true
			"camera_draft": f.app.camera_transform_editor.draft=true
			"nested_scene": f.app.sequence_editor.active_owner="sequence-child"
		check(not f.editor.set_controls_at(0,0.,1.).is_empty() and not f.editor.preview().is_empty() and not f.editor.bake_preview().is_empty() and f.app.keys==f.before and f.app.history.is_empty(),"busy_admission_keeps_scene_"+kind)
		close(f)

	f=fixture();ready(f)
	var expected_frames: Dictionary={}
	for at in range(11):expected_frames[at]=f.editor.sample_preview(f.app.keys,at)
	error=f.editor.bake_preview()
	check(error.is_empty() and f.app.keys.size()==12 and f.app.history.size()==1 and f.app.changed_count==1 and f.app.set_frame_count==1,"bake_uses_one_existing_history_command")
	var command: Dictionary=f.app.history[0]
	check(command.type=="keys" and command.before==f.before and command.after==f.app.keys and command.bytes>0,"history_has_complete_before_after_camera_keys")
	var authored_preserved:=true
	for original in f.before:
		var found:=false
		for current in f.app.keys:
			if current.frame==original.frame:found=current==original
		authored_preserved=authored_preserved and found
	check(authored_preserved,"bake_preserves_every_authored_key_dictionary")
	var sampled_match:=true
	for at in range(11):
		var actual: Dictionary=Timeline.sample(f.app.keys,at);var expected: Dictionary=expected_frames[at]
		sampled_match=sampled_match and actual.position.distance_to(expected.position)<0.000001 and absf(actual.rotation.dot(expected.rotation))>0.999999 and absf(actual.fov-expected.fov)<0.000001
	check(sampled_match,"baked_integer_frames_match_prebake_preview_samples")
	check(not f.editor.preview_active() and f.editor.context.is_empty() and f.editor.controls.is_empty() and f.app.unrelated==f.other,"bake_closes_recipe_preserves_unrelated_state")
	var again: String=f.editor.bake_preview()
	check(not again.is_empty() and f.app.history.size()==1 and f.app.changed_count==1,"bake_cannot_replay_without_new_recipe")
	var recorded_after: Array=command.after.duplicate(true);f.app.keys[1].fov=77.
	check(command.after==recorded_after,"history_snapshot_not_aliased_to_mutable_installed_keys")
	# The command contract is ordinary before/after data; real app Undo is a
	# separate existing integration test, not claimed by this fake restoration.
	f.app.keys=command.before.duplicate(true)
	check(f.app.keys==f.before,"ordinary_before_payload_can_restore_authored_keys")
	f.app.keys=recorded_after.duplicate(true)
	check(f.app.keys==recorded_after,"ordinary_after_payload_retains_baked_keys")
	close(f)

	f=fixture(600);ready(f);var huge_before: PackedByteArray=var_to_bytes(f.app.keys)
	error=f.editor.bake_preview()
	check(not error.is_empty() and var_to_bytes(f.app.keys)==huge_before and f.app.history.is_empty() and f.editor.preview_active(),"existing_241_key_budget_refuses_bake_atomically")
	close(f)
	f=fixture();f.editor.preview()
	check(not f.editor.preview_active() and not f.editor.bake_preview().is_empty() and f.app.history.is_empty(),"zero_control_recipe_does_not_create_history")
	close(f)
	print("KEYFRAME_EASING_EDITOR_UNIT ",JSON.stringify({"checks":checks,"failures":failures,"native_asset_tested":false,"camera_render_or_export_tested":false,"real_app_undo_tested":false,"application_adopted":false}))
	quit(0 if failures==0 else 1)
