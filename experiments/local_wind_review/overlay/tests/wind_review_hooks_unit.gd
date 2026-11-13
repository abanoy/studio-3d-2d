extends SceneTree
const Review=preload("res://src/wind_review.gd")
const Renderer=preload("res://src/renderer.gd")
const HasProject=preload("res://src/has_project.gd")
const Recording=preload("res://src/physics_recording.gd")
const Fixtures=preload("res://tests/wind_review_unit.gd")
class Harness extends "res://src/app.gd":
	var last_message:=""
	func _ready() -> void:pass
	func _process(_delta: float) -> void:pass
	func _physics_process(_delta: float) -> void:pass
	func _exit_tree() -> void:pass
	func finish_stroke() -> void:pass
	func release_mouse(_restore:=false) -> void:pass
	func refresh_layer() -> void:pass
	func refresh_timeline() -> void:pass
	func selected_output_size() -> String:return "intentionally-unavailable-profile"
	func message(value: String) -> void:last_message=value
class Operations extends Node:
	var app
	var pid:=-1
	var observed_stopped:=false
	var recording: Dictionary={"active":false,"advancing":false}
	func freeze_all() -> bool:observed_stopped=not app.local_wind_active();return false
	func clear_previews() -> void:pass
	func is_running() -> bool:return false
class Pose extends Node:
	var dragging:=false
	func finish_drag() -> void:pass
	func apply_frame() -> void:pass
	func refresh_values() -> void:pass
class CaptureRenderer extends Renderer:
	var readback_started:=0
	var reads: Array=[]
	func begin_native_readback() -> bool:readback_started+=1;return false
	func finish_native_readback(read_pixels:=true) -> Image:reads.append(read_pixels);return null
	func native_view_available() -> bool:return true
	func view_state() -> Dictionary:return {}
	func apply_lighting() -> void:pass
	func prepare_world(_document: Dictionary,_duration: int,_video: Dictionary={}) -> Dictionary:return {"error":"unit preflight stops here"}
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func arm(review: Node) -> void:review.phase="warming";review.schedule_warmup()
func stopped(review: Node) -> bool:return review.phase=="stopped" and not RenderingServer.frame_post_draw.is_connected(review.warm_frame)
func _initialize() -> void:run.call_deferred()
func run() -> void:
	# The real endpoint implementations are called; unavailable downstream work
	# deliberately exits after their first boundary, without a worker or GPU.
	var source_app:=Fixtures.FakeApp.new();root.add_child(source_app)
	var review:=Review.new();review.app=source_app;source_app.add_child(review)
	var app:=Harness.new();app.local_wind_review=review
	var operations:=Operations.new();operations.app=app;app.physics_editor=operations;app.source_import=operations
	var renderer:=CaptureRenderer.new();app.renderer=renderer
	var pose:=Pose.new();app.pose_editor=pose
	app.mode=OptionButton.new();app.mode.add_item("Drawing");app.mode.add_item("Camera");app.mode.select(1)
	app.frame_box=SpinBox.new();app.transport_info=Label.new()
	arm(review);app.save()
	check(stopped(review) and operations.observed_stopped,"Save stops the owned try-out before the first physics/snapshot boundary")
	var project:=HasProject.new();project.app=app
	arm(review);operations.observed_stopped=false;project.save_file("res://output/never-written.has","packed")
	check(stopped(review) and operations.observed_stopped and project.pid==-1,"package Save cannot freeze or launch while the temporary candidate remains")
	arm(review);operations.observed_stopped=false;project.save_asset("res://output/never-written-asset.has")
	check(stopped(review) and operations.observed_stopped and project.pid==-1,"Save asset stops before its captured world snapshot")
	var recording:=Recording.new();recording.editor=operations
	arm(review);var recorded:=recording.start()
	check(stopped(review) and not recorded and recording.targets.is_empty(),"Record stops the preview before selecting any real simulation targets")
	arm(review);var export_error: String=await app.export_frames("res://output/never-written",true,false)
	check(stopped(review) and not export_error.is_empty() and not app.exporting,"Export stops before delivery checks, frame snapshots, or writer launch")
	arm(review);app.playing=true;operations.observed_stopped=false;app.toggle_play()
	check(stopped(review) and operations.observed_stopped and not app.playing,"Playback stops the temporary candidate before freezing original physics")
	arm(review);operations.observed_stopped=false;app.set_frame(1)
	check(stopped(review) and operations.observed_stopped and app.frame==1,"frame changes stop before resampling or freezing the source")
	arm(review);app.restore_world({})
	check(stopped(review),"world restore stops even when a later world preflight refuses the change")
	arm(review);app.reset_document("")
	check(stopped(review),"new/open document stops before preparing a replacement world")
	var actual_renderer:=Renderer.new();actual_renderer.before_asset_replace=Callable(review,"stop_for_asset")
	arm(review);actual_renderer.clear_assets()
	check(stopped(review),"renderer asset replacement has its own synchronous stop boundary")
	actual_renderer.before_final_capture=Callable(review,"stop_for_capture")
	arm(review);var final_image: Image=await actual_renderer.capture([],[],0,true)
	check(stopped(review) and final_image==null,"native final capture stops even when its native viewport is unavailable")
	arm(review);app.finish_recovery_preview("unused","digest",app.frame,0,{})
	check(renderer.readback_started==0 and app.recovery_native_requests.is_empty(),"recovery never begins a pixel readback while local wind is visible")
	app.recovery_root="res://output/unit";app.recovery_session="unit";app.recovery_revision=0
	root.add_child(app);app.complete_recovery_preview(app.recovery_root.path_join(app.recovery_session),"digest",app.frame,0,{})
	check(renderer.reads==[false],"a recovery request queued before wind starts releases its scope without temporary pixels")
	review.stop_preview();app.finish_recovery_preview("unused","digest",app.frame,0,{})
	check(renderer.readback_started==1,"recovery pixel requests remain available after the try-out stops")
	actual_renderer.before_asset_replace=Callable();actual_renderer.before_final_capture=Callable();actual_renderer.free()
	app.frame_box.free();app.transport_info.free();app.mode.free();app.free()
	operations.free();pose.free();renderer.free();recording.free();project.free();source_app.free()
	await process_frame
	print("WIND_REVIEW_HOOKS_UNIT "+JSON.stringify({"checks":checks,"failures":failures}))
	quit(0 if failures==0 else 1)
