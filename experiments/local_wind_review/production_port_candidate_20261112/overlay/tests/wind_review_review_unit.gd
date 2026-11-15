extends "res://tests/wind_review_unit.gd"
# Additional review oracles. The old prototype runs these same assertions first.
const App=preload("res://src/app.gd")
class AuditApp extends "res://src/app.gd":
	var last_message:=""
	func _ready() -> void:pass
	func _process(_delta: float) -> void:pass
	func _physics_process(_delta: float) -> void:pass
	func _exit_tree() -> void:pass
	func message(value: String) -> void:last_message=value
class AuditHelper extends Node:
	var window: Window
	func cancel_patch_drag() -> void:pass
class AuditOps extends Node:
	var simulations: Dictionary={}
	var recording: Dictionary={"active":false}
	var helper_editor:=AuditHelper.new()
	var pid:=-1
	var releases:=0
	func _init() -> void:add_child(helper_editor)
	func release_grab() -> void:releases+=1
	func is_running() -> bool:return false
class AuditPose extends Node:
	var dragging:=false
	var reveal_bones:=false
	func finish_drag(_cancel:=false) -> void:pass
	func update_gizmo() -> void:pass
class AuditRenderer extends "res://src/renderer.gd":
	var reads: Array=[]
	var factory:=Callable()
	func _process(_delta: float) -> void:pass
	func native_view_available() -> bool:return true
	func view_state() -> Dictionary:return {}
	func begin_native_readback() -> bool:native_readbacks+=1;return true
	func finish_native_readback(read_pixels:=true) -> Image:
		native_readbacks-=1;reads.append(read_pixels);return null
	func prepare_model(data: Dictionary,_video: Dictionary={}) -> Dictionary:return {"model":factory.call(data)}
func _initialize() -> void:
	create_timer(60).timeout.connect(func():push_error("Wind review audit watchdog");quit(2))
	call_deferred("review_audit_run")
func long_chain(count: int,prefix: String) -> Dictionary:
	var ids: Array=[]
	for i in range(count):ids.append(prefix+str(i))
	return chain("Long declared chain",ids,.1)
func make_candidate(data: Dictionary) -> RefCounted:
	var actor:=fixture();actor.root.get_parent().remove_child(actor.root);actor.data=data
	return actor
func review_audit_run() -> void:
	for count in [257,512]:
		var value:=Groups.build(definition([long_chain(count,"a")]),SHA)
		check(value.error.is_empty() and value.groups.size()==1 and value.groups[0].rotating_ids.size()==count,"existing contract accepts a declared "+str(count)+"-rotator chain")
	check(not Groups.build(definition([long_chain(513,"a")]),SHA).error.is_empty(),"a chain above the existing512 limit is refused")
	check(Groups.build(definition([long_chain(200,"a"),long_chain(200,"b"),long_chain(112,"c")]),SHA).error.is_empty(),"multiple chains can reach exactly512 total rotators")
	check(not Groups.build(definition([long_chain(200,"a"),long_chain(200,"b"),long_chain(113,"c")]),SHA).error.is_empty(),"combined independent chains cannot exceed512 total rotators")
	var many: Array=[]
	for i in range(128):many.append(long_chain(1,"chain"+str(i)+"_"))
	check(Groups.build(definition(many),SHA).error.is_empty(),"the existing128-chain boundary is accepted")
	many.append(long_chain(1,"too_many_"))
	check(not Groups.build(definition(many),SHA).error.is_empty(),"more than128 chains remains refused")
	var app:=AuditApp.new();root.add_child(app)
	var renderer:=AuditRenderer.new();app.renderer=renderer;app.add_child(renderer)
	renderer.world=Node3D.new();renderer.add_child(renderer.world);renderer.camera=Camera3D.new();renderer.world.add_child(renderer.camera);renderer.factory=make_candidate
	var operations:=AuditOps.new();app.physics_editor=operations;app.source_import=operations;app.has_project=operations;app.add_child(operations)
	app.pose_editor=AuditPose.new();app.add_child(app.pose_editor)
	app.canvas=App.CanvasView.new();app.add_child(app.canvas)
	app.world_selection=App.WorldSelection.new();app.world_selection.app=app;app.add_child(app.world_selection)
	app.mode=OptionButton.new();app.mode.add_item("Draw");app.mode.add_item("Camera");app.mode.add_item("Pose");app.mode.select(2);app.add_child(app.mode)
	var source:=fixture();source.root.reparent(renderer.world);source.data.source="res://tests/wind_review_review_unit.gd";source.data.sha256=FileAccess.get_sha256(source.data.source);renderer.model=source
	var review:=Review.new();review.app=app;app.local_wind_review=review;app.add_child(review)
	review.target_id=source.data.id;review.root_id=source.root.get_instance_id();review.source_sha=source.data.sha256;review.source_modified=FileAccess.get_modified_time(source.data.source);review.revision=app.recovery_revision;review.opened_frame=app.frame;review.original_data=source.data.duplicate(true);review.catalog=Groups.build(source.root.get_meta("has_secondary_rig"),source.data.sha256,Groups.parents(source))
	review.window=Window.new();app.add_child(review.window);review.window.visible=true
	review.parts=ItemList.new();review.wind_check=CheckButton.new();review.master=CheckButton.new();review.status=Label.new();review.detail=Label.new();review.direction=OptionButton.new();review.direction.add_item("From right");review.strength=SpinBox.new();review.strength.value=6
	for control in [review.parts,review.wind_check,review.master,review.status,review.detail,review.direction,review.strength]:review.window.add_child(control)
	for group in review.catalog.groups:review.parts.add_item(str(group.names[0]))
	review.focus_group(0);review.wind_ids[review.catalog.groups[0].id]=true
	var source_before: Dictionary=source.data.duplicate(true);var peer:=FakeBody.new();operations.simulations["unrelated"]=peer
	var returned: Array=[];app.camera_cursor_return_requested.connect(func(point: Vector2):returned.append(point))
	var escape:=InputEventKey.new();escape.keycode=KEY_ESCAPE;escape.pressed=true
	for item in [{"name":"LMB","button":MOUSE_BUTTON_LEFT,"ctrl":false},{"name":"Ctrl LMB","button":MOUSE_BUTTON_LEFT,"ctrl":true},{"name":"RMB","button":MOUSE_BUTTON_RIGHT,"ctrl":false},{"name":"middle/orbit","button":MOUSE_BUTTON_MIDDLE,"ctrl":false},{"name":"stopped open window","button":MOUSE_BUTTON_LEFT,"ctrl":false}]:
		review.phase="stopped" if item.name=="stopped open window" else "warming"
		app.canvas.middle_pending="test";app.canvas.middle_motion=Vector2(9,0);app.canvas.panning=true
		app.camera_button(item.button,true,item.ctrl,Vector2(23,37))
		if item.name=="middle/orbit":app.orbit_control.active=true
		var prior:=returned.size();app._input(escape)
		check(not app.navigating and app.camera_buttons==0 and not app.camera_free and not app.orbit_control.active,"routed Escape ends "+str(item.name)+" navigation")
		check(not app.canvas.panning and app.canvas.middle_pending.is_empty() and app.canvas.middle_motion==Vector2.ZERO,"routed Escape clears "+str(item.name)+" canvas middle state")
		check(not app.camera_cursor_restore_pending and returned.size()==prior+1 and returned[-1]==Vector2(23,37),"routed Escape requests the original cursor once for "+str(item.name))
		# Retain old-oracle failures without leaking its captured state into another case.
		app.release_mouse()
	# Rebuild the lightweight review UI after the stopped-window case closed it.
	review.close();await process_frame
	review.window=Window.new();app.add_child(review.window);review.window.visible=true
	review.parts=ItemList.new();review.wind_check=CheckButton.new();review.master=CheckButton.new();review.status=Label.new();review.detail=Label.new();review.direction=OptionButton.new();review.direction.add_item("From right");review.strength=SpinBox.new();review.strength.value=6
	for control in [review.parts,review.wind_check,review.master,review.status,review.detail,review.direction,review.strength]:review.window.add_child(control)
	review.catalog=Groups.build(source.root.get_meta("has_secondary_rig"),source.data.sha256,Groups.parents(source));review.focused=0
	for group in review.catalog.groups:review.parts.add_item(str(group.names[0]))
	review.wind_ids[review.catalog.groups[0].id]=true
	renderer.capturing_final=true
	check(not review.available() and not review.context_valid(),"pending final capture rejects both opening and restarting a try-out")
	review.begin_preview()
	check(review.phase=="stopped" and review.candidate==null,"an already open review cannot insert a candidate during final capture")
	review.stop_preview();renderer.capturing_final=false
	app.recovery_root="res://output/wind-audit";app.recovery_session="audit"
	app.finish_recovery_preview(app.recovery_root.path_join(app.recovery_session),"test",app.frame,app.recovery_revision,{})
	check(renderer.native_readbacks==1 and app.recovery_native_requests.size()==1,"recovery request is genuinely pending before the try-out starts")
	review.begin_preview()
	check(review.phase=="warming" and review.candidate!=null,"actual synchronous preview construction enters warming")
	review.stop_preview("stop before readback dispatch")
	app.complete_recovery_previews()
	check(renderer.reads==[false] and renderer.native_readbacks==0 and app.recovery_native_requests.is_empty(),"start then stop still invalidates queued recovery pixels and releases its scope")
	app.finish_recovery_preview(app.recovery_root.path_join(app.recovery_session),"fresh",app.frame,app.recovery_revision,{})
	app.complete_recovery_previews()
	check(renderer.reads[-1]==true and renderer.native_readbacks==0 and app.recovery_native_requests.is_empty(),"fresh recovery after the stopped try-out remains eligible at the new epoch")
	check(source.data==source_before and operations.simulations["unrelated"]==peer and not peer.disposed,"all cancellation and capture guards preserve source state and peer simulation identity")
	review.close();app.free();await process_frame
	print("WIND_REVIEW_AUDIT_UNIT "+JSON.stringify({"checks":checks,"failures":failures}))
	quit(0 if failures==0 else 1)
