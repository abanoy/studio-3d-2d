extends Control
const Clips=preload("res://src/animation_clips.gd")
const ObjectTiming=preload("res://src/object_timing.gd")
const Channels=preload("res://src/animated_channels.gd")
signal navigation_requested(action: String, at: float)
signal channel_selected(id: String, channel: String, at: int)
signal piece_moved(id: String, piece_id: String, start: int, before: Dictionary)
signal clip_action(action: String, id: String, piece_id: String, frame: int)
signal object_selected(id: String)
signal object_moved(id: String, delta: int, before: Dictionary)
signal seek(frame: int)
signal import_requested(frame: int, actor: bool)
signal audio_chosen(index: int)
signal audio_moved(id: String, start: int, previous: int)
signal audio_end_trimmed(id: String, last: int, context: Dictionary)
var import_menu: PopupMenu
var import_frame:=0
var keys: Array = []
var layers: Array = []
var window_start:=0.0
var window_span:=0.0
var picture: Control
var duration := 48
var frame := 0
var dragging := false
var audio_clip := {}
var audio_clips: Array = []
var audio_selected := 0
var audio_fps := 24.0
var audio_rate:={"fps_num":24,"fps_den":1}
var clip_waveforms: Array = []
var clip_waveform_levels: Array=[]
var moving_audio := ""
var audio_anchor := 0
var audio_previous := 0
var audio_preview := 0
var trimming_audio:=""
var trim_previous:=0
var trim_preview:=0
var trim_anchor:=0
var trim_visible_end:=0
var trim_limit:=0
var trim_context:={}
var audio_trim_context: Callable
var waveform := PackedFloat32Array()
var pose_keys: Array = []
var has_model := false
var presence_start:=0
var object_rows: Array=[]
var selected_id:=""
var selected_channel:="@root"
var last_bone:=""
var expanded:={}
var channel_cache:={}
var advanced_labels:=false
var visual_rows: Array=[]
var object_positions: Array=[]
var layout_ids: Array=[]
var channel_font:=SystemFont.new()
var interactive:=true
var header_only:=false
var hide_header:=false
var world_token:=0
var moving_piece:=""
var moving_valid:=true
var can_paste:=false
var context_object:=""
var context_piece:=""
var moving_id:=""
var moving_before:={}
var moving_anchor:=0
var moving_delta:=0
const ROW_HEIGHT:=26.0
var cel_style := preload("res://src/studio_theme.gd").surface("e2f3ff", "91bedd", "729bb8", 0)
const LEFT := 190.0

func set_label_mode(enabled: bool) -> void:
	if advanced_labels==enabled:return
	advanced_labels=enabled
	if not enabled and selected_channel in ["@root/position","@root/rotation_xyzw","@root/scale"]:selected_channel="@root"
	channel_cache.clear()
	rebuild_rows()

func set_objects(rows: Array, token: int, active: String) -> void:
	if world_token!=token:
		finish_move(true);cancel_audio();expanded.clear();channel_cache.clear();layout_ids=[];visual_rows=[];object_positions=[]
	if selected_id!=active:last_bone="";selected_channel="@root"
	world_token=token;object_rows=rows;selected_id=active
	var ids: Array=[]
	var rebuild:=false
	for data in rows:
		ids.append(data.id)
		if expanded.get(data.id,false) and (not channel_cache.has(data.id) or channel_cache[data.id].data!=data):
			channel_cache[data.id]={"data":data.duplicate(true),"channels":Channels.describe(data,advanced_labels)};rebuild=true
	if ids!=layout_ids or rebuild:
		layout_ids=ids;rebuild_rows()
	custom_minimum_size.y=maxf(100,audio_y()+maxi(1,audio_clips.size())*30+6)
	queue_redraw()

func rebuild_rows() -> void:
	visual_rows=[];object_positions=[]
	for i in range(object_rows.size()):
		var data: Dictionary=object_rows[i]
		object_positions.append(visual_rows.size());visual_rows.append({"index":i,"channel":{}})
		if expanded.get(data.id,false):
			if not channel_cache.has(data.id):channel_cache[data.id]={"data":data.duplicate(true),"channels":Channels.describe(data,advanced_labels)}
			for channel in channel_cache[data.id].channels:visual_rows.append({"index":i,"channel":channel})
	custom_minimum_size.y=maxf(100,audio_y()+maxi(1,audio_clips.size())*30+6)
	queue_redraw()

func toggle_expanded(index: int) -> void:
	finish_move(true)
	if not Channels.has_data(object_rows[index]):return
	var id: String=object_rows[index].id
	expanded[id]=not expanded.get(id,false);rebuild_rows()

func hit_row(point: Vector2) -> Dictionary:
	var index:=floori((point.y-header_height())/ROW_HEIGHT)
	return visual_rows[index] if index>=0 and index<visual_rows.size() else {}

func sync_bone(id: String) -> void:
	if id!=last_bone:selected_channel=id;last_bone=id;queue_redraw()

func row_in_view(y: float) -> bool:
	if not get_parent() is ScrollContainer:return true
	var top: float=get_parent().scroll_vertical
	return y+ROW_HEIGHT>=top and y<=top+get_parent().size.y

func header_height() -> float:
	return 0 if hide_header else 52

func audio_y() -> float:
	var shift: float = visual_rows.size()*ROW_HEIGHT if not object_rows.is_empty() else (24 if has_model else 0)
	return header_height()+5+shift+layers.size()*30

func audio_rect(index: int) -> Rect2:
	var clip: Dictionary = audio_clips[index]
	var start: int = audio_preview if moving_audio == clip.id else int(clip.start_frame)
	var last: int=trim_preview if trimming_audio==clip.id else preload("res://src/audio_track.gd").last_frame(clip,audio_rate)
	var end := mini(duration,start+last-int(clip.start_frame)+1)
	return Rect2(x(start),audio_y()+index*30,maxf(1,x(end)-x(start)),29)

func audio_end_handle(index: int) -> Rect2:
	var rect:=audio_rect(index)
	var width:=minf(rect.size.x,minf(9,maxf(2,rect.size.x*.3)))
	return Rect2(rect.end.x-width,rect.position.y,width,rect.size.y)

func audio_gesture_active() -> bool:
	return not moving_audio.is_empty() or not trimming_audio.is_empty()

func cancel_audio() -> void:
	moving_audio="";trimming_audio="";trim_context={};mouse_default_cursor_shape=Control.CURSOR_ARROW;queue_redraw()

func row_y(index: int) -> float:
	return header_height()+(object_positions[index] if index<object_positions.size() else index)*ROW_HEIGHT

func channel_y(id: String, channel: String) -> float:
	for i in range(visual_rows.size()):
		var row: Dictionary=visual_rows[i]
		if object_rows[row.index].id==id and row.channel.get("id","")==channel:return header_height()+i*ROW_HEIGHT
	return -1

func _get_tooltip(point: Vector2) -> String:
	for index in range(audio_clips.size()):
		if point.x>=LEFT and audio_end_handle(index).has_point(point):return "Drag the right edge to shorten or extend this sound. Original samples stay available."
		if point.x>=LEFT and audio_rect(index).has_point(point):return "Drag to move this sound. Drag its right edge to trim the end."
	var row:=hit_row(point)
	if not row.is_empty():
		if not row.channel.is_empty():return row.channel.tooltip+"\nClick a key to select this part and inspect its frame."
		for key in object_rows[row.index].get("visibility_keys",[]):
			if absf(point.x-x(int(key.frame)))<=5 and point.y>=row_y(row.index)+16:return "Visibility %s at frame %d • stays until the next visibility key" % ["ON" if key.visible else "OFF",int(key.frame)]
	return tooltip_text

func block_rect(data: Dictionary, index: int, delta:=0) -> Rect2:
	var bounds:=ObjectTiming.span(data)
	return Rect2(x(bounds.x+delta),row_y(index)+2,maxf(10,x(mini(duration,bounds.y+delta+1))-x(bounds.x+delta)),21)

func piece_rect(piece: Dictionary, index: int, delta:=0) -> Rect2:
	return Rect2(x(int(piece.start)+delta),row_y(index)+2,maxf(10,x(mini(duration,int(piece.start)+int(piece.length)+delta))-x(int(piece.start)+delta)),21)

func piece_at(data: Dictionary, index: int, point: Vector2) -> String:
	if point.x<LEFT or not Clips.has_pieces(data):return ""
	for piece in data.animation_clips:
		if piece_rect(piece,index).has_point(point):return piece.id
	return ""

func drag_motion(point: Vector2) -> void:
	if moving_id.is_empty():return
	if moving_piece.is_empty():moving_delta=ObjectTiming.clamp_delta(moving_before,frame_at(point)-moving_anchor,duration)
	else:
		var piece: Dictionary=moving_before.animation_clips[Clips.index_id(moving_before,moving_piece)]
		moving_delta=clampi(frame_at(point)-moving_anchor,-int(piece.start),duration+1-int(piece.start)-int(piece.length))
		moving_valid=Clips.can_place(moving_before,moving_piece,int(piece.start)+moving_delta,int(piece.length),duration)
	tooltip_text="Move by %d frames • release to apply • Escape to cancel" % moving_delta
	queue_redraw()

func finish_move(cancel:=false) -> void:
	if moving_id.is_empty():return
	var id:=moving_id;var delta:=moving_delta;var before:=moving_before;var piece_id:=moving_piece
	moving_id="";moving_piece="";moving_delta=0;moving_before={};moving_valid=true;tooltip_text="Drag an object's block to move its presence and all animation keys together."
	queue_redraw()
	if not cancel and delta!=0:
		if piece_id.is_empty():object_moved.emit(id,delta,before)
		else:
			var piece: Dictionary=before.animation_clips[Clips.index_id(before,piece_id)]
			piece_moved.emit(id,piece_id,int(piece.start)+delta,before)

func _ready() -> void:
	picture=preload("res://src/timeline_picture.gd").new();picture.timeline=self;picture.clip_contents=true;picture.mouse_filter=Control.MOUSE_FILTER_IGNORE;add_child(picture)
	resized.connect(layout_picture);layout_picture()
	focus_mode = Control.FOCUS_ALL
	focus_exited.connect(cancel_audio)
	channel_font.font_names=PackedStringArray(["Yu Gothic UI","Segoe UI","Arial"])
	mouse_filter=Control.MOUSE_FILTER_STOP
	tooltip_text="Drag an object's block to move its presence and all animation keys together."
	import_menu=PopupMenu.new();add_child(import_menu)
	import_menu.add_item("Add model / prop here…",0)
	import_menu.add_item("Add environment / map here…",1)
	import_menu.add_separator()
	for action in ["Split here","Copy piece","Cut piece","Paste piece here","Delete piece"]:import_menu.add_item(action,10+import_menu.item_count-3)
	import_menu.id_pressed.connect(func(id):
		import_menu.hide()
		if id<2:import_requested.emit(import_frame,id==0)
		else:clip_action.emit(["split","copy","cut","paste","delete"][id-10],context_object,context_piece,import_frame))

func layout_picture() -> void:
	if picture:picture.position=Vector2(LEFT,0);picture.size=Vector2(maxf(1,size.x-LEFT-16),size.y);picture.queue_redraw()
func visible_span() -> float:
	return float(duration) if window_span<=0 else clampf(window_span,1,duration)
func visible_start() -> float:return clampf(window_start,0,maxf(0,duration-visible_span()))
func frame_at(point: Vector2) -> int:
	return clampi(roundi(visible_start()+(point.x-LEFT)/maxf(1,size.x-LEFT-16)*visible_span()),0,duration)
func x(f: float) -> float:
	return LEFT+(f-visible_start())/visible_span()*maxf(1,size.x-LEFT-16)

func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO,size),Color("f5f8fb"))
	if not hide_header:draw_string(ThemeDB.fallback_font,Vector2(8,43),"Camera",HORIZONTAL_ALIGNMENT_LEFT,-1,14,Color("283c51"))
	if header_only:
		if picture:picture.queue_redraw()
		return
	for i in range(object_rows.size()):
		var data: Dictionary=object_rows[i];var y:=row_y(i)
		if not row_in_view(y):continue
		draw_rect(Rect2(0,y,LEFT,ROW_HEIGHT),Color("dceaf6") if data.id==selected_id else Color("eef2f6") if i%2==0 else Color("f5f8fb"))
		if Channels.has_data(data):draw_string(ThemeDB.fallback_font,Vector2(5,y+18),"▾" if expanded.get(data.id,false) else "▸",HORIZONTAL_ALIGNMENT_LEFT,14,14,Color("425a70"))
		draw_string(channel_font,Vector2(22,y+18),data.name,HORIZONTAL_ALIGNMENT_LEFT,LEFT-28,12,Color("283c51"))
	for i in range(visual_rows.size()):
		var row: Dictionary=visual_rows[i];var y:=header_height()+i*ROW_HEIGHT
		if row.channel.is_empty() or not row_in_view(y):continue
		var selected: bool=object_rows[row.index].id==selected_id and row.channel.id==selected_channel
		draw_rect(Rect2(0,y,LEFT,ROW_HEIGHT),Color("d2e7f5") if selected else Color("f4f7fb"))
		draw_string(channel_font,Vector2(30,y+18),row.channel.label,HORIZONTAL_ALIGNMENT_LEFT,LEFT-36,12,Color("36516a"))
	if has_model and object_rows.is_empty():draw_string(ThemeDB.fallback_font,Vector2(8,header_height()+16),"Model pose",HORIZONTAL_ALIGNMENT_LEFT,85,13,Color("283c51"))
	var shift: float=visual_rows.size()*ROW_HEIGHT if not object_rows.is_empty() else (24 if has_model else 0)
	for i in range(layers.size()):draw_string(ThemeDB.fallback_font,Vector2(8,header_height()+21+shift+i*30),layers[i].name,HORIZONTAL_ALIGNMENT_LEFT,80,14,Color("283c51"))
	if audio_clips.is_empty():draw_string(ThemeDB.fallback_font,Vector2(8,audio_y()+18),"Audio",HORIZONTAL_ALIGNMENT_LEFT,80,14,Color("283c51"))
	for i in range(audio_clips.size()):draw_string(ThemeDB.fallback_font,Vector2(8,audio_y()+i*30+18),"Audio" if audio_clips.size()==1 else "Audio %d" % (i+1),HORIZONTAL_ALIGNMENT_LEFT,80,14,Color("283c51"))
	if picture:picture.queue_redraw()

func visible_waveform(index: int) -> PackedFloat32Array:
	var overview: PackedFloat32Array=clip_waveforms[index] if index<clip_waveforms.size() else PackedFloat32Array()
	if window_span<=0 or index>=clip_waveform_levels.size():return overview
	var target:=ceili(float(duration)/visible_span()*maxf(1,size.x-LEFT-16)/4.0)
	var result:=overview
	for level: PackedFloat32Array in clip_waveform_levels[index]:
		result=level
		if result.size()>=target:break
	return result

func draw_content(painter: Control) -> void:
	var stride:=maxi(1,ceili(visible_span()/12.0))
	for f in range(floori(visible_start()/stride)*stride,ceili((visible_start()+visible_span())/stride)*stride+1,stride):
		painter.draw_line(Vector2(x(f), 18), Vector2(x(f), size.y), Color("d3dce5"))
		if not hide_header:painter.draw_string(ThemeDB.fallback_font, Vector2(x(f) + 3, 15), str(f), HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color("425a70"))
	if not hide_header:
		for key in keys:
			var p := Vector2(x(key.frame), 38)
			painter.draw_colored_polygon(PackedVector2Array([p + Vector2(0, -6), p + Vector2(6, 0), p + Vector2(0, 6), p + Vector2(-6, 0)]), Color("ce922e"))
	if header_only:
		painter.draw_line(Vector2(x(frame),0),Vector2(x(frame),size.y),Color("bf613c"),2);return
	var shift: float=visual_rows.size()*ROW_HEIGHT if not object_rows.is_empty() else (24 if has_model else 0)
	for i in range(object_rows.size()):
		var data: Dictionary=object_rows[i]
		var delta:=moving_delta if moving_id==data.id and moving_piece.is_empty() else 0
		var y:=row_y(i);var selected: bool=data.id==selected_id
		if not row_in_view(y):continue
		painter.draw_rect(Rect2(0,y,size.x,ROW_HEIGHT),Color("dceaf6") if selected else Color("eef2f6") if i%2==0 else Color("f5f8fb"))
		if not Clips.has_pieces(data) or not data.animation_clips.is_empty():painter.draw_rect(Rect2(x(int(data.start_frame)+delta),y+3,maxf(1,x(duration)-x(int(data.start_frame)+delta)),20),Color("e9e1f1"))
		if Clips.has_pieces(data):
			for piece in data.animation_clips:
				var offset:=moving_delta if moving_id==data.id and moving_piece==piece.id else delta
				var rect:=piece_rect(piece,i,offset);painter.draw_style_box(cel_style,rect)
				painter.draw_rect(rect,Color("b74949") if moving_id==data.id and moving_piece==piece.id and not moving_valid else Color("5b79a0") if selected else Color("929cb0"),false,2 if selected else 1)
				for key in piece.keys:
					if key.frame>=piece.source_in and key.frame<piece.source_in+piece.length:draw_diamond(painter,Vector2(x(int(piece.start)+int(key.frame)-int(piece.source_in)+offset),y+12))
		else:
			var rect:=block_rect(data,i,delta);painter.draw_style_box(cel_style,rect)
			painter.draw_rect(rect,Color("5b79a0") if selected else Color("929cb0"),false,2 if selected else 1)
			for key in data.pose_keys:draw_diamond(painter,Vector2(x(int(key.frame)+delta),y+12))
		for key in data.get("visibility_keys",[]):
			painter.draw_circle(Vector2(x(int(key.frame)),y+21),3,Color("348468") if key.visible else Color("ad4c4c"))
	for i in range(visual_rows.size()):
		var row: Dictionary=visual_rows[i]
		if row.channel.is_empty():continue
		var y:=header_height()+i*ROW_HEIGHT
		if not row_in_view(y):continue
		var channel: Dictionary=row.channel;var selected: bool=object_rows[row.index].id==selected_id and channel.id==selected_channel
		painter.draw_rect(Rect2(0,y,size.x,ROW_HEIGHT),Color("d2e7f5") if selected else Color("f4f7fb"))
		for span in channel.ranges:painter.draw_rect(Rect2(x(span.x),y+6,maxf(1,x(span.x+span.y)-x(span.x)),14),Color("e5edf5"))
		for at in channel.frames:
			if channel.id=="@visibility":
				var on:=preload("res://src/visibility_track.gd").target(object_rows[row.index],int(at))
				painter.draw_circle(Vector2(x(at),y+13),4,Color("348468") if on else Color("ad4c4c"))
			else:draw_diamond(painter,Vector2(x(at),y+13))
	if has_model and object_rows.is_empty():
		painter.draw_rect(Rect2(x(presence_start),header_height()+1,maxf(1,x(duration)-x(presence_start)),20),Color("ebe4f5"))
		for key in pose_keys:
			var p := Vector2(x(key.frame), header_height()+11)
			painter.draw_colored_polygon(PackedVector2Array([p + Vector2(0, -5), p + Vector2(5, 0), p + Vector2(0, 5), p + Vector2(-5, 0)]), Color("1d2430"))
	for i in range(layers.size()):
		var y := header_height()+3 + shift + i * 30
		for cel in layers[i].cels:
			var rect := Rect2(x(cel.start) + 1, y, maxf(2, x(cel.start + cel.duration) - x(cel.start) - 2), 23)
			if layers[i].visible: cel_style.draw(painter.get_canvas_item(), rect)
			else: painter.draw_rect(rect, Color("c5cbd1"))
			painter.draw_string(ThemeDB.fallback_font, rect.position + Vector2(4, 16), "%d–%d" % [cel.start, cel.start + cel.duration - 1], HORIZONTAL_ALIGNMENT_LEFT, rect.size.x - 4, 12, Color("1e4159"))
	for index in range(audio_clips.size()):
		var clip: Dictionary = audio_clips[index]
		var y := audio_y()+index*30
		var rect := audio_rect(index)
		painter.draw_rect(rect,Color("d4e9fa") if trimming_audio==clip.id else Color("c6d0d5") if clip.muted else Color("e1edd5"))
		if index==audio_selected: painter.draw_rect(rect,Color("749c69"),false,1)
		var peaks:=visible_waveform(index)
		var offset := x(audio_preview)-x(clip.start_frame) if moving_audio==clip.id else 0.0
		var delta: int=audio_preview-int(clip.start_frame) if moving_audio==clip.id else 0
		var first:=maxi(0,floori((visible_start()-delta)/duration*peaks.size())-1)
		var last:=mini(peaks.size(),ceili((visible_start()+visible_span()-delta)/duration*peaks.size())+1)
		for i in range(first,last):
			var left:=x(float(i)/peaks.size()*duration)+offset
			var right:=x(float(i+1)/peaks.size()*duration)+offset
			if right<=rect.position.x or left>=rect.end.x:continue
			var xx:=clampf(left,rect.position.x,rect.end.x)
			var amplitude := peaks[i]*11
			painter.draw_line(Vector2(xx,y+14-amplitude),Vector2(xx,y+14+amplitude),Color("467d45"))
		painter.draw_string(ThemeDB.fallback_font,rect.position+Vector2(4,11),clip.source.name.left(24)+(" [mute]" if clip.muted else ""),HORIZONTAL_ALIGNMENT_LEFT,maxf(1,rect.size.x-8),11,Color("315835"))
		painter.draw_line(Vector2(rect.end.x-3,y+6),Vector2(rect.end.x-3,y+23),Color("3e708d") if trimming_audio==clip.id else Color("749c69"),2)
	painter.draw_line(Vector2(x(frame), 0), Vector2(x(frame), size.y), Color("bf613c"), 2)

func draw_diamond(painter: Control,point: Vector2) -> void:
	painter.draw_colored_polygon(PackedVector2Array([point+Vector2(0,-5),point+Vector2(5,0),point+Vector2(0,5),point+Vector2(-5,0)]),Color("1d2430"))

func _gui_input(event: InputEvent) -> void:
	if not interactive:accept_event();return
	if event is InputEventMouseButton and event.button_index in [MOUSE_BUTTON_WHEEL_UP,MOUSE_BUTTON_WHEEL_DOWN] and (event.ctrl_pressed or event.shift_pressed):
		if event.pressed:navigation_requested.emit(("in" if event.button_index==MOUSE_BUTTON_WHEEL_UP else "out") if event.ctrl_pressed else ("left" if event.button_index==MOUSE_BUTTON_WHEEL_UP else "right"),frame_at(event.position))
		accept_event();return
	if not trimming_audio.is_empty():
		if event is InputEventKey and event.pressed and event.keycode==KEY_ESCAPE or event is InputEventMouseButton and event.pressed and event.button_index==MOUSE_BUTTON_RIGHT:
			cancel_audio();accept_event();return
		if event is InputEventMouseMotion:
			var delta:=frame_at(event.position)-trim_anchor
			var index:=-1
			for i in range(audio_clips.size()):
				if audio_clips[i].id==trimming_audio:index=i;break
			if index<0:cancel_audio();return
			trim_preview=trim_previous if delta==0 else clampi(trim_visible_end+delta,int(audio_clips[index].start_frame)+1,trim_limit)-1
			mouse_default_cursor_shape=Control.CURSOR_HSIZE;queue_redraw();accept_event();return
		if event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_LEFT and not event.pressed:
			var id:=trimming_audio;var last:=trim_preview;var prior:=trim_previous;var context:=trim_context;cancel_audio()
			if last!=prior:audio_end_trimmed.emit(id,last,context)
			accept_event();return
		accept_event();return
	if not moving_audio.is_empty():
		if event is InputEventKey and event.pressed and event.keycode==KEY_ESCAPE or event is InputEventMouseButton and event.pressed and event.button_index==MOUSE_BUTTON_RIGHT:
			cancel_audio();accept_event();return
		if event is InputEventMouseMotion:
			audio_preview=clampi(audio_previous+frame_at(event.position)-audio_anchor,0,duration-1)
			queue_redraw();accept_event();return
		if event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_LEFT and not event.pressed:
			var id := moving_audio; moving_audio=""
			if audio_preview!=audio_previous: audio_moved.emit(id,audio_preview,audio_previous)
			queue_redraw();accept_event();return
		accept_event();return
	if event is InputEventMouseButton and event.pressed and event.button_index==MOUSE_BUTTON_LEFT and not header_only:
		var index := floori((event.position.y-audio_y())/30)
		if index>=0 and index<audio_clips.size():
			audio_chosen.emit(index)
			if event.position.x<LEFT:accept_event();return
			if event.position.x>=LEFT and audio_rect(index).has_point(event.position):
				finish_move(true);dragging=false;cancel_audio()
				if audio_end_handle(index).has_point(event.position):
					var clip: Dictionary=audio_clips[index];var full:=clip.duplicate();full.erase("source_out_sample")
					trimming_audio=clip.id;trim_previous=preload("res://src/audio_track.gd").last_frame(clip,audio_rate);trim_preview=trim_previous
					trim_visible_end=mini(duration,trim_previous+1);trim_limit=mini(duration,preload("res://src/audio_track.gd").last_frame(full,audio_rate)+1);trim_anchor=frame_at(event.position)
					trim_context=audio_trim_context.call(clip.id) if audio_trim_context.is_valid() else {}
					grab_focus();accept_event();return
				moving_audio=audio_clips[index].id
				audio_anchor=frame_at(event.position);audio_previous=int(audio_clips[index].start_frame);audio_preview=audio_previous
				grab_focus();accept_event();return
	if event is InputEventMouseButton and event.pressed and event.button_index==MOUSE_BUTTON_LEFT:
		var row:=hit_row(event.position)
		if not row.is_empty() and not row.channel.is_empty():
			finish_move(true);dragging=false
			selected_channel=row.channel.id
			channel_selected.emit(object_rows[row.index].id,row.channel.id,frame_at(event.position) if event.position.x>=LEFT else -1)
			accept_event();return
	if event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_RIGHT:
		if event.pressed:
			finish_move(true);dragging=false;import_frame=mini(duration-1,frame_at(event.position));context_object="";context_piece=""
			var hit:=hit_row(event.position);var row:=int(hit.get("index",-1))
			var on_piece:=false
			if row>=0 and row<object_rows.size():
				var data: Dictionary=object_rows[row];context_object=data.id;context_piece=piece_at(data,row,event.position)
				on_piece=not context_piece.is_empty() if Clips.has_pieces(data) else event.position.x>=LEFT and block_rect(data,row).has_point(event.position)
				if not hit.channel.is_empty():
					context_object="";context_piece="";on_piece=false;channel_selected.emit(data.id,hit.channel.id,-1)
				else:object_selected.emit(data.id)
			for id in range(10,15):import_menu.set_item_disabled(import_menu.get_item_index(id),context_object.is_empty() or (not can_paste if id==13 else not on_piece))
			import_menu.position=Vector2i(get_screen_position()+event.position);import_menu.popup()
		accept_event();return
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if not event.pressed and not moving_id.is_empty():finish_move();accept_event();return
		if event.pressed:
			var hit:=hit_row(event.position);var index:=int(hit.get("index",-1))
			if index>=0 and index<object_rows.size():
				var data: Dictionary=object_rows[index]
				if event.position.x<19:
					dragging=false;toggle_expanded(index);object_selected.emit(data.id);accept_event();return
				var piece:=piece_at(data,index,event.position)
				if event.position.x<LEFT or (not piece.is_empty() if Clips.has_pieces(data) else block_rect(data,index).has_point(event.position)):
					dragging=false
					if event.position.x>=LEFT:
						moving_id=data.id;moving_piece="" if event.shift_pressed else piece;moving_valid=true;moving_before=data.duplicate(true);moving_anchor=frame_at(event.position);moving_delta=0
					object_selected.emit(data.id);accept_event();return
			if event.position.x<LEFT:accept_event();return
			dragging=true
		else:dragging=false
	if event is InputEventMouseMotion:
		mouse_default_cursor_shape=Control.CURSOR_ARROW
		for index in range(audio_clips.size()):
			if event.position.x>=LEFT and audio_end_handle(index).has_point(event.position):mouse_default_cursor_shape=Control.CURSOR_HSIZE;break
		if not moving_id.is_empty():drag_motion(event.position);accept_event();return
		var hit:=hit_row(event.position);var hover:=int(hit.get("index",-1))
		if hover>=0 and hover<object_rows.size():tooltip_text=str(object_rows[hover].name)+" • drag a piece; Shift-drag moves all its animation."

	if event is InputEventMouse and (dragging or event is InputEventMouseButton and event.pressed):
		seek.emit(frame_at(event.position))
