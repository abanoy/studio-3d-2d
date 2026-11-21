extends SceneTree
# Authored/unrun state-only controls; no native files or asset/job execution.
const State=preload("res://src/loading_progress_state.gd")
const View=preload("res://src/loading_progress_ui.gd")
const Job=preload("res://src/loading_asset_job.gd")
var checks:=0
var failures:=0
func check(value: bool,label: String) -> void:
	checks+=1
	if not value:failures+=1
	print(("PASS " if value else "FAIL ")+label)
func packet(token: String,seq: int,phase: String,done: Variant=null,total: Variant=null,unit: String="") -> Dictionary:
	return {"format":State.FORMAT,"token":token,"sequence":seq,"phase":phase,"label":"Preparing this stage","completed":done,"total":total,"unit":unit}
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var s: RefCounted=State.new()
	check(s.begin("op_1","Loading model"),"begin.instant_unknown_stage")
	check(s.busy and s.total==null and s.sequence==-1,"begin.no_invented_percentage")
	check(not s.begin("op_2","Other operation"),"begin_active_replacement_refused")
	check(s.update(packet("op_1",0,"opening")),"unknown_phase_accepted")
	check(s.total==null and s.completed==null and s.unit=="","unknown_count_stays_indeterminate")
	check(s.update(packet("op_1",1,"reading",0,20,"bytes")),"known_real_byte_total_accepted")
	check(s.update(packet("op_1",2,"reading",10,20,"bytes")) and s.completed==10 and s.total==20,"known_real_byte_count_advances")
	var before: PackedByteArray=var_to_bytes(s.snapshot())
	check(not s.update(packet("stale",3,"reading",20,20,"bytes")) and var_to_bytes(s.snapshot())==before,"foreign_token_unchanged")
	check(not s.update(packet("op_1",2,"reading",20,20,"bytes")),"repeated_sequence_refused")
	check(not s.update(packet("op_1",1,"reading",20,20,"bytes")),"old_sequence_refused")
	check(not s.update(packet("op_1",3,"reading",9,20,"bytes")),"same_stage_regression_refused")
	check(not s.update(packet("op_1",3,"reading",10,21,"bytes")),"changing_known_denominator_refused")
	check(not s.update(packet("op_1",3,"reading",null,null,"")),"known_stage_cannot_become_unknown")
	check(not s.update(packet("op_1",3,"reading",21,20,"bytes")),"over_total_refused")
	check(not s.update(packet("op_1",3,"reading",true,20,"bytes")),"boolean_count_refused")
	check(not s.update(packet("op_1",3,"reading",1.5,20,"bytes")),"fractional_count_refused")
	check(not s.update(packet("op_1",3,"reading",10,20,"percent")),"invented_percentage_unit_refused")
	check(s.update(packet("op_1",3,"reading",20,20,"bytes")),"completed_byte_stage_accepted")
	check(s.update(packet("op_1",4,"decoding")),"next_unknown_stage_does_not_aggregate_fake_percent")
	check(not s.update(packet("op_1",5,"reading",20,20,"bytes")),"return_to_closed_phase_refused")
	check(not s.finish("stale",true) and s.busy,"stale_completion_cannot_clear_active_operation")
	check(s.request_cancel("op_1") and s.cancelling and s.busy,"cancel_stays_visible_until_owner_finishes")
	check(not s.request_cancel("op_1"),"cancel_callback_requested_only_once")
	check(s.update(packet("op_1",5,"ready",1,1,"items")) and s.cancelling,"late_worker_progress_does_not_uncancel")
	check(s.finish("op_1",true) and s.terminal=="cancelled" and not s.busy,"late_success_does_not_overrule_user_cancel")
	check(not s.begin("op_1","Reuse"),"operation_token_reuse_refused")
	check(s.begin("op_2","Opening project") and not s.cancelling and s.total==null,"fresh_operation_has_fresh_state")
	check(not s.finish("op_1",false) and s.busy,"old_failure_cannot_clear_new_operation")
	check(s.finish("op_2",false) and s.terminal=="failed" and not s.busy,"failure_releases_busy_state")
	check(s.begin("op_3","Preparing loose parts") and s.finish("op_3",true) and s.terminal=="succeeded","owner_success_releases_busy_state")
	check(not s.update(packet("op_3",99,"ready",1,1,"items")),"late_progress_after_completion_refused")
	check(not State.identifier("bad/token") and not State.identifier("x".repeat(97)),"operation_identifier_is_bounded")
	check(Job.CHUNK==1048576 and Job.MAX_BYTES==128*1024*1024,"asset_reader_existing128MiB_cap_and_real_chunk_units")
	print("Loading progress authored checks: "+str(checks)+"; failures: "+str(failures))
	quit(0 if failures==0 else 1)
