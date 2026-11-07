extends Control
var middle_target: Callable
var middle_clicked: Callable
var middle_pending := ""
var middle_motion := Vector2.ZERO

func cancel_middle() -> void:
	middle_pending="";middle_motion=Vector2.ZERO;panning=false
signal pointer(event: InputEvent, point: Vector2)
var background: Texture2D
var overlay: Texture2D
var sequence_overlay: Texture2D
var fill_preview: Texture2D
var selection_preview: ImageTexture
var drawing_selection:=Rect2i()
var scene_background: Node2D
var zoom := 1.0
var pan := Vector2.ZERO
var panning := false
var scene_navigation := false
var pose_lines: Array = []
var pose_joints: Array = []
var review_lines:=PackedVector2Array()
var review_chain:=PackedVector2Array()
var review_pointer:=Callable()
var review_box:=Rect2()
var review_box_visible:=false
var resolution := Vector2(1920, 1080)

func _ready() -> void:
	clip_contents = true
	mouse_filter = Control.MOUSE_FILTER_STOP
	focus_mode = Control.FOCUS_ALL
	resized.connect(queue_redraw)
	var surround:=ColorRect.new();surround.color=Color("7e8f9e");surround.mouse_filter=Control.MOUSE_FILTER_IGNORE;surround.show_behind_parent=true;add_child(surround);surround.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	scene_background=preload("res://src/canvas_raster.gd").new();scene_background.show_behind_parent=true;add_child(scene_background)

func image_rect() -> Rect2:
	var scale_factor := minf(size.x / resolution.x, size.y / resolution.y) * zoom
	var extent := resolution * scale_factor
	return Rect2((size - extent) / 2 + pan, extent)

func _draw() -> void:
	var rect := image_rect()
	scene_background.texture=background;scene_background.rect=rect;scene_background.queue_redraw()
	if sequence_overlay:draw_texture_rect(sequence_overlay,rect,false)
	if selection_preview:draw_texture_rect(selection_preview,rect,false)
	elif fill_preview:draw_texture_rect(fill_preview,rect,false)
	elif overlay:draw_texture_rect(overlay,rect,false)
	for line in pose_lines:
		draw_line(rect.position + line.a / resolution * rect.size, rect.position + line.b / resolution * rect.size, line.color, 2, true)
	for joint in pose_joints:
		draw_circle(rect.position + joint.point / resolution * rect.size, 4 if joint.selected else 2, Color("ffe086") if joint.selected else Color("a0e5f5"))
	if not review_lines.is_empty():
		var points:=PackedVector2Array()
		for p in review_lines:points.append(rect.position+p/resolution*rect.size)
		draw_multiline(points,Color(1,0.6,0.16,0.75),1,true)
	if review_chain.size()>1:
		var points:=PackedVector2Array()
		for p in review_chain:points.append(rect.position+p/resolution*rect.size)
		draw_polyline(points,Color("fff1a0"),3,true)
		for p in points:draw_circle(p,4,Color("fff1a0"))
	if review_box_visible:
		draw_rect(Rect2(rect.position+review_box.position/resolution*rect.size,review_box.size/resolution*rect.size),Color("8cd9ff"),false,2)
	if drawing_selection.has_area():
		var selected:=Rect2(rect.position+Vector2(drawing_selection.position)/resolution*rect.size,Vector2(drawing_selection.size)/resolution*rect.size)
		draw_rect(selected,Color.BLACK,false,3);draw_rect(selected,Color.WHITE,false,1)
	draw_rect(rect, Color("dce8f2"), false, 1)

func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouse and review_pointer.is_valid():
		var rect:=image_rect()
		if review_pointer.call(event,(event.position-rect.position)/rect.size*resolution):accept_event();return
	if event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_MIDDLE:
		if event.pressed and middle_target.is_valid():
			var target: String=middle_target.call()
			if not target.is_empty():middle_pending=target;middle_motion=Vector2.ZERO;grab_focus();accept_event();return
		elif not event.pressed and not middle_pending.is_empty():
			var target:=middle_pending;middle_pending=""
			if middle_target.is_valid() and middle_target.call()==target and middle_clicked.is_valid():middle_clicked.call()
			accept_event();return
	if event is InputEventMouseMotion and not middle_pending.is_empty():
		middle_motion+=event.relative
		if middle_motion.length()<4:accept_event();return
		middle_pending=""
		if scene_navigation:
			var press:=InputEventMouseButton.new();press.button_index=MOUSE_BUTTON_MIDDLE;press.pressed=true
			pointer.emit(press,(event.position-image_rect().position)/image_rect().size*resolution)
			var motion: InputEventMouseMotion=event.duplicate();motion.relative=middle_motion
			pointer.emit(motion,(event.position-image_rect().position)/image_rect().size*resolution)
		else:panning=true;pan+=middle_motion;queue_redraw()
		accept_event();return
	if scene_navigation:
		if event is InputEventMouseButton and event.pressed: grab_focus()
		if event is InputEventMouse:
			var rect := image_rect()
			pointer.emit(event, (event.position-rect.position)/rect.size*resolution)
		return
	if event is InputEventMouseButton:
		grab_focus()
		if event.button_index == MOUSE_BUTTON_MIDDLE:
			panning = event.pressed
			return
		if event.pressed and event.button_index in [MOUSE_BUTTON_WHEEL_UP, MOUSE_BUTTON_WHEEL_DOWN]:
			zoom = clampf(zoom * (1.15 if event.button_index == MOUSE_BUTTON_WHEEL_UP else 1.0 / 1.15), 0.25, 4)
			queue_redraw()
			return
	if event is InputEventMouseMotion and panning:
		pan += event.relative
		queue_redraw()
		return
	if event is InputEventMouse:
		var rect := image_rect()
		var point: Vector2 = (event.position - rect.position) / rect.size * resolution
		pointer.emit(event, point)
