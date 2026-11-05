extends Control
var editor
var dragging:=""
var original:=0
var press_frame:=0
var delta:=0
var revision:=-1
var drag_owner:=""
func _ready() -> void:
	mouse_filter=Control.MOUSE_FILTER_STOP;focus_mode=Control.FOCUS_ALL
func row_rect(clip: Dictionary,index: int) -> Rect2:
	var begin: float=editor.app.timeline.x(int(clip.start)+(delta if clip.id==dragging else 0))
	var end: float=editor.app.timeline.x(int(clip.start+clip.duration)+(delta if clip.id==dragging else 0))
	return Rect2(begin,index*26+2,maxf(3,end-begin),22)
func cancel_drag() -> void:
	dragging="";delta=0;queue_redraw()
func _process(_dt: float) -> void:
	if not dragging.is_empty() and (revision!=editor.app.recovery_revision or drag_owner!=editor.active_owner or editor.app.exporting):cancel_drag()
func _draw() -> void:
	if not editor:return
	var rows: Array=editor.clips()
	for i in range(rows.size()):
		var clip: Dictionary=rows[i];draw_rect(Rect2(0,i*26,size.x,26),Color("edf0f8"))
		draw_string(ThemeDB.fallback_font,Vector2(8,i*26+18),"Sequence %d" % (i+1),HORIZONTAL_ALIGNMENT_LEFT,172,12,Color("283c51"))
		var rect:=row_rect(clip,i)
		draw_rect(rect,Color("b8d7ed") if clip.id==editor.selected_clip else Color("d5c8ee"))
		draw_rect(rect,Color("557a9a"),false,1)
		draw_string(ThemeDB.fallback_font,rect.position+Vector2(4,16),str(editor.asset(clip.asset_id).get("name","Sequence"))+(" ↻" if clip.loop else ""),HORIZONTAL_ALIGNMENT_LEFT,maxf(1,rect.size.x-8),12,Color("283c51"))
	var x: float=editor.app.timeline.x(editor.app.frame);draw_line(Vector2(x,0),Vector2(x,size.y),Color("d34545"),2)
func _gui_input(event: InputEvent) -> void:
	if editor.app.exporting:return
	if event is InputEventMouseButton:
		if event.button_index==MOUSE_BUTTON_LEFT:
			if not event.pressed:
				if not dragging.is_empty():
					var id:=dragging;var start:=original+delta;var changed:=delta!=0;cancel_drag()
					if changed:
						var why: String=editor.change_clip(id,{"start":start});if not why.is_empty():editor.app.message(why)
					else:editor.app.set_frame(press_frame)
				accept_event();return
			grab_focus();editor.app.stop()
			var rows: Array=editor.clips()
			for i in range(rows.size()-1,-1,-1):
				if row_rect(rows[i],i).has_point(event.position):
					editor.selected_clip=rows[i].id
					if event.double_click:
						var why: String=editor.enter(rows[i].asset_id);if not why.is_empty():editor.app.message(why)
					else:dragging=rows[i].id;original=int(rows[i].start);press_frame=editor.app.timeline.frame_at(event.position);revision=editor.app.recovery_revision;drag_owner=editor.active_owner
					queue_redraw();accept_event();return
			if event.position.x>=190:editor.app.set_frame(editor.app.timeline.frame_at(event.position));accept_event()
		elif event.button_index==MOUSE_BUTTON_RIGHT and event.pressed:editor.show_panel();accept_event()
	elif event is InputEventMouseMotion and not dragging.is_empty():
		var clip: Dictionary=editor.find_clip(dragging)
		if clip.is_empty():cancel_drag();return
		delta=clampi(editor.app.timeline.frame_at(event.position)-press_frame,-original,int(editor.app.video.duration_frames)-original-int(clip.duration));queue_redraw();accept_event()
	elif event is InputEventKey and event.pressed and not event.echo:
		if event.keycode==KEY_ESCAPE:cancel_drag();accept_event()
		elif event.keycode==KEY_DELETE and not editor.selected_clip.is_empty():
			var why: String=editor.remove_clip(editor.selected_clip);if not why.is_empty():editor.app.message(why)
			accept_event()
		elif event.keycode==KEY_S and not event.ctrl_pressed and not event.alt_pressed and not editor.selected_clip.is_empty():
			var why: String=editor.split_clip(editor.selected_clip,editor.app.frame);if not why.is_empty():editor.app.message(why)
			accept_event()
		elif event.ctrl_pressed and event.keycode in [KEY_C,KEY_V]:
			var why: String=editor.copy_clip(editor.selected_clip) if event.keycode==KEY_C else editor.paste_clip()
			if not why.is_empty():editor.app.message(why)
			accept_event()
func _notification(what: int) -> void:
	if what==NOTIFICATION_WM_WINDOW_FOCUS_OUT:cancel_drag()
