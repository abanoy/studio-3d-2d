extends Node
# Session-only view state. Never changes project content, history or timing.
var app
var tracks
var ruler
var bar: HBoxContainer
var scrollbar: HScrollBar
var caption: Label
var zoom_in: Button
var zoom_out: Button
var fit: Button
var context:=""
var last_frame:=-1
var controls_busy:=false
var start:=0.0
var span:=0.0
func setup(parent: Control,body,header) -> void:
	tracks=body;ruler=header
	bar=HBoxContainer.new();bar.set_anchors_and_offsets_preset(Control.PRESET_TOP_WIDE);bar.offset_bottom=34;parent.add_child(bar)
	zoom_out=app.button(bar,"−",func():zoom(2.0,app.frame));zoom_out.tooltip_text="Zoom timeline out • Ctrl + wheel down"
	zoom_in=app.button(bar,"+",func():zoom(.5,app.frame));zoom_in.tooltip_text="Zoom timeline in • Ctrl + wheel up"
	fit=app.button(bar,"Fit",fit_all);fit.tooltip_text="Show the complete scene timeline"
	scrollbar=HScrollBar.new();scrollbar.size_flags_horizontal=Control.SIZE_EXPAND_FILL;scrollbar.custom_minimum_size.x=60;scrollbar.step=1;bar.add_child(scrollbar)
	scrollbar.tooltip_text="Pan the timeline • Shift + wheel over tracks"
	scrollbar.value_changed.connect(func(value):if not busy():start=value;publish())
	caption=Label.new();caption.custom_minimum_size.x=140;bar.add_child(caption)
	for view in [tracks,ruler]:view.navigation_requested.connect(func(action,at):navigate(action,at))
func apply_neon_style() -> void:
	# Neon Pro step 6 (row style only): 28 px ghost zoom buttons (− / + icons, "Fit"), 12/500
	# #B4BAC7, and a mono 11 px #8C93A3 range caption. Same controls, same signals.
	var S:=preload("res://src/studio_theme.gd")
	bar.add_theme_constant_override("separation",4)
	var pad:=Vector4(8,0,8,0)
	var clear:=S.flat(Color.TRANSPARENT,Color.TRANSPARENT,6,0,pad)
	for control in [zoom_out,zoom_in,fit]:
		control.size_flags_vertical=Control.SIZE_SHRINK_CENTER;control.custom_minimum_size.y=28
		app.override_button_boxes(control,clear,S.flat(S.HOVER,Color.TRANSPARENT,6,0,pad),S.flat(S.RAISE,Color.TRANSPARENT,6,0,pad),clear)
		app.override_button_colors(control,S.TEXT2,S.TEXT,Color.WHITE)
		control.add_theme_font_override("font",S.font(500));control.add_theme_font_size_override("font_size",12)
	for pair in [[zoom_out,"minus"],[zoom_in,"add"]]:
		var control: Button=pair[0]
		# 16 px icons tinted #B4BAC7 when enabled; disabled stays a dim #8C93A3 so the states differ.
		control.text="";control.icon=S.icon(pair[1],Color.WHITE,16);control.icon_alignment=HORIZONTAL_ALIGNMENT_CENTER;control.custom_minimum_size.x=28
		control.add_theme_constant_override("icon_max_width",16);control.add_theme_color_override("icon_disabled_color",Color(S.TEXT3,0.45))
	scrollbar.size_flags_vertical=Control.SIZE_SHRINK_CENTER
	caption.custom_minimum_size.x=96;caption.horizontal_alignment=HORIZONTAL_ALIGNMENT_RIGHT;caption.size_flags_vertical=Control.SIZE_SHRINK_CENTER
	caption.add_theme_font_override("font",S.mono(400));caption.add_theme_font_size_override("font_size",11);caption.add_theme_color_override("font_color",S.TEXT3)
func busy() -> bool:
	return app.exporting or tracks.dragging or ruler.dragging or not tracks.moving_id.is_empty() or tracks.audio_gesture_active() or tracks.cel_gesture_active()
func length() -> float:return float(maxi(1,int(app.video.duration_frames)))
func visible() -> float:return length() if span<=0 else clampf(span,1,length())
func publish() -> void:
	var count:=visible();start=clampf(start,0,length()-count)
	for view in [tracks,ruler]:
		view.window_start=start;view.window_span=span;view.queue_redraw()
	scrollbar.set_block_signals(true);scrollbar.max_value=length();scrollbar.page=count;scrollbar.value=start;scrollbar.set_block_signals(false)
	caption.text="Frames %d–%d" % [floori(start),ceili(start+count)]
	update_controls()
func update_controls() -> void:
	controls_busy=busy()
	zoom_in.disabled=controls_busy or visible()<=mini(12,int(length()))
	zoom_out.disabled=controls_busy or span<=0
	fit.disabled=controls_busy or span<=0
	scrollbar.mouse_filter=Control.MOUSE_FILTER_IGNORE if controls_busy else Control.MOUSE_FILTER_STOP
func _process(_delta: float) -> void:
	if scrollbar and busy()!=controls_busy:update_controls()
func sync() -> void:
	var next: String=app.recovery_session+"/"+app.sequence_editor.active_owner
	if context!=next:context=next;span=0;start=0;last_frame=-1
	var count:=visible()
	if last_frame!=app.frame and span>0 and (app.frame<start or app.frame>start+count):start=clampf(app.frame-count*.5,0,length()-count)
	last_frame=app.frame
	if span>=length():span=0;start=0
	publish()
func zoom(factor: float,anchor: float) -> void:
	if busy():return
	var old:=visible();var ratio:=clampf((anchor-start)/old,0,1)
	var count:=clampf(old*factor,mini(12,int(length())),length())
	span=0 if count>=length() else count;start=clampf(anchor-ratio*count,0,length()-count)
	publish()
func fit_all() -> void:
	if busy():return
	span=0;start=0;publish()
func navigate(action: String,at: float) -> void:
	if busy():return
	if action=="in":zoom(.5,at)
	elif action=="out":zoom(2.0,at)
	elif span>0:
		start+=visible()*.15*(-1 if action=="left" else 1);publish()
