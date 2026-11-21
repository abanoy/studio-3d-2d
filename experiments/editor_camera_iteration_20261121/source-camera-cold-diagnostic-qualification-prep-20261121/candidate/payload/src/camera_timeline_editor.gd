extends Node
# Session selection/ghost only. A completed edit uses the normal camera keys history.
const Edits=preload("res://src/camera_key_edits.gd")
const Timeline=preload("res://src/timeline.gd")
var app
var view: Control
var selected_frame:=-1
var context: Dictionary={}
var source_frame:=-1
var preview_frame:=-1
var press_screen:=Vector2.ZERO
var moved:=false
var preview_valid:=true
var session:=""
var scene_owner:=""
func setup(owner_app,owner_view: Control) -> void:
	app=owner_app;view=owner_view;view.camera_editor=self;session=app.recovery_session;scene_owner=owner_id()
func owner_id() -> String:
	return str(app.sequence_editor.active_owner) if app.sequence_editor else ""
func busy_error() -> String:
	if app.exporting or app.playing or app.navigating:return "Stop playback/navigation and wait for export before editing camera keys."
	if app.home and app.home.visible or app.has_dialog(app) or app.source_import.pid>0 or app.has_project.pid>0:return "Finish the open operation before editing camera keys."
	if app.drawing or app.pose_editor.dragging or app.physics_editor.recording.active or app.physics_editor.is_running():return "Finish the current edit and turn live Physics / Hair & clothes off before editing camera keys."
	if app.camera_transform_editor and app.camera_transform_editor.has_draft():return "Apply or reload the numeric camera draft first."
	return ""
func snapshot() -> Dictionary:
	return {"session":app.recovery_session,"owner":owner_id(),"video":app.video.duplicate(true),"keys":app.keys.duplicate(true),"keys_sha256":Edits.digest(app.keys)}
func matches(saved: Dictionary) -> bool:
	return not saved.is_empty() and app.recovery_session==saved.session and owner_id()==saved.owner and app.video==saved.video and app.keys==saved.keys and Edits.digest(app.keys)==saved.keys_sha256
func active() -> bool:return not context.is_empty()
func screen_transform() -> Transform2D:
	return view.get_viewport().get_screen_transform()*view.get_global_transform_with_canvas()
func camera_row(point: Vector2) -> bool:
	return not view.hide_header and point.x>=view.LEFT and point.x<=view.size.x-16 and point.y>=24. and point.y<52.
func hit_key(point: Vector2) -> int:
	if not camera_row(point):return -1
	var mapping:=screen_transform();var screen_point:=mapping*point
	var radius: float=maxf(10.,8.*maxf(mapping.x.length(),mapping.y.length()))
	var distance:=radius;var result:=-1
	for key in view.keys:
		var candidate:=mapping*Vector2(view.x(key.frame),38)
		var next: float=screen_point.distance_to(candidate)
		if next<distance:distance=next;result=int(key.frame)
	return result
func begin(at_frame: int,point: Vector2) -> String:
	var why:=busy_error()
	if not why.is_empty():report(why);return why
	why=Edits.error(app.keys,app.video.duration_frames)
	if not why.is_empty():report(why);return why
	if Edits.index_at(app.keys,at_frame)<0:return "That camera key changed."
	app.stop();app.set_frame(at_frame)
	context=snapshot();source_frame=at_frame;preview_frame=at_frame
	press_screen=screen_transform()*point;moved=false;preview_valid=true;selected_frame=at_frame
	view.dragging=false;view.grab_focus();view.queue_redraw()
	return ""
func motion(point: Vector2) -> void:
	if not active():return
	if not matches(context) or not busy_error().is_empty():cancel();return
	if not moved and (screen_transform()*point).distance_to(press_screen)<4.:return
	moved=true;preview_frame=view.frame_at(point)
	var occupied:=Edits.index_at(context.keys,preview_frame)
	preview_valid=occupied<0 or preview_frame==source_frame
	view.mouse_default_cursor_shape=Control.CURSOR_MOVE if preview_valid else Control.CURSOR_FORBIDDEN
	view.queue_redraw()
func finish() -> String:
	if not active():return ""
	var saved: Dictionary=context.duplicate(true);var was_moved:=moved;var previous:=source_frame;var target:=preview_frame
	var why:=busy_error()
	if why.is_empty() and not matches(saved):why="The camera track changed. Select the key again."
	cancel()
	if not why.is_empty():report(why);return why
	if not was_moved:return ""
	var planned:=Edits.retime(saved.keys,previous,target,int(saved.video.duration_frames))
	if planned.has("error"):report(planned.error);return planned.error
	return commit(saved,planned,target)
func toggle(at_frame: int) -> String:
	var why:=busy_error()
	if not why.is_empty():report(why);return why
	var saved:=snapshot();var captured: Dictionary={}
	if Edits.index_at(app.keys,at_frame)<0:
		captured=Timeline.from_camera(at_frame,app.renderer.camera,app.interpolation.get_item_text(app.interpolation.selected))
	var planned:=Edits.toggle(app.keys,at_frame,int(app.video.duration_frames),captured)
	if planned.has("error"):report(planned.error);return planned.error
	return commit(saved,planned,at_frame)
func commit(saved: Dictionary,planned: Dictionary,at_frame: int) -> String:
	if not matches(saved) or not busy_error().is_empty():return "The camera track changed. Start the edit again."
	if not planned.get("changed",false):return ""
	var before: Array=saved.keys.duplicate(true);var after: Array=planned.keys.duplicate(true)
	app.keys=after
	app.push_history({"type":"keys","before":before,"after":after.duplicate(true),"bytes":2*(var_to_bytes(before).size()+var_to_bytes(after).size())})
	selected_frame=int(planned.selected_frame)
	app.changed();app.set_frame(at_frame);view.queue_redraw()
	report("Camera keys updated. Undo restores the previous timing and views.")
	return ""
func cancel() -> void:
	context.clear();source_frame=-1;preview_frame=-1;moved=false;preview_valid=true
	if is_instance_valid(view):view.mouse_default_cursor_shape=Control.CURSOR_ARROW;view.queue_redraw()
func input(event: InputEvent) -> bool:
	if not event is InputEventMouseButton or event.button_index!=MOUSE_BUTTON_LEFT or not event.pressed or not camera_row(event.position):return false
	app.stop()
	var hit:=hit_key(event.position)
	if event.double_click:
		cancel();view.dragging=false;toggle(hit if hit>=0 else view.frame_at(event.position));return true
	if hit>=0:
		begin(hit,event.position);return true
	selected_frame=-1;view.queue_redraw()
	return false # Existing empty-lane and ruler scrubbing remains authoritative.
func global_event(event: InputEvent) -> bool:
	if not active():return false
	if not matches(context) or not busy_error().is_empty():cancel();return false
	if event is InputEventKey and event.pressed and event.keycode==KEY_ESCAPE or event is InputEventMouseButton and event.pressed and event.button_index==MOUSE_BUTTON_RIGHT:
		cancel();return true
	if event is InputEventMouseMotion:
		if not (event.button_mask&MOUSE_BUTTON_MASK_LEFT):cancel();return false
		motion(view.get_global_transform_with_canvas().affine_inverse()*event.position);return true
	if event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_LEFT and not event.pressed:
		finish();return true
	return false
func hover(point: Vector2) -> void:
	if camera_row(point):
		view.mouse_default_cursor_shape=Control.CURSOR_HSIZE if hit_key(point)>=0 else Control.CURSOR_ARROW
		view.tooltip_text="Camera: click a diamond to select; drag to retime. Double-click adds/removes a key. Esc cancels a drag."
func draw_overlay(painter: Control,selected_color: Color,invalid_color: Color) -> void:
	if selected_frame<0 or view.hide_header:return
	var at: int=preview_frame if active() and moved else selected_frame
	if at<view.visible_start() or at>view.visible_start()+view.visible_span():return
	var point:=Vector2(view.x(at),38);var scale_factor:=maxf(.01,screen_transform().x.length())
	var color:=selected_color if preview_valid else invalid_color
	var points:=PackedVector2Array([point+Vector2(0,-8),point+Vector2(8,0),point+Vector2(0,8),point+Vector2(-8,0),point+Vector2(0,-8)])
	painter.draw_polyline(points,color,2./scale_factor,true)
	if active() and moved:painter.draw_line(Vector2(view.x(source_frame),38),point,color,.8/scale_factor,true)
func report(text: String) -> void:
	if app:app.message(text)
func _process(_delta: float) -> void:
	if app==null:return
	if session!=app.recovery_session:cancel();selected_frame=-1;session=app.recovery_session
	if scene_owner!=owner_id():cancel();selected_frame=-1;scene_owner=owner_id()
	if active() and (not matches(context) or not busy_error().is_empty()):cancel()
	if selected_frame>=0 and Edits.index_at(app.keys,selected_frame)<0:selected_frame=-1;view.queue_redraw()
