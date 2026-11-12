extends Control

# Helpers keep native projection coordinates. Their clip is the full rendered
# scene in Setup, or the fitted image in Focus, independently of drawing pixels.
class FrameOverlay extends Control:
	var canvas_view
	func _draw() -> void:
		var scale_factor: Vector2=size/canvas_view.resolution
		for line in canvas_view.pose_lines:
			draw_line(line.a*scale_factor,line.b*scale_factor,line.color,2,true)
		for joint in canvas_view.pose_joints:
			draw_circle(joint.point*scale_factor,4 if joint.selected else 2,Color("ffe086") if joint.selected else Color("a0e5f5"))
		if not canvas_view.review_lines.is_empty():
			var points:=PackedVector2Array()
			for p in canvas_view.review_lines:points.append(p*scale_factor)
			draw_multiline(points,Color(1,0.6,0.16,0.75),1,true)
		if canvas_view.review_chain.size()>1:
			var points:=PackedVector2Array()
			for p in canvas_view.review_chain:points.append(p*scale_factor)
			draw_polyline(points,Color("fff1a0"),3,true)
			for p in points:draw_circle(p,4,Color("fff1a0"))
		if canvas_view.review_box_visible:
			draw_rect(Rect2(canvas_view.review_box.position*scale_factor,canvas_view.review_box.size*scale_factor),Color("8cd9ff"),false,2)

var middle_target: Callable
var middle_clicked: Callable
var middle_pending := ""
var middle_motion := Vector2.ZERO

func cancel_middle() -> void:
	middle_pending="";middle_motion=Vector2.ZERO;panning=false
signal pointer(event: InputEvent, point: Vector2)
var background: Texture2D
var setup_background: Texture2D
var scene_editing:=false
var scene_setup:=false
var show_camera_frame:=false
var show_thirds:=false
var overlay: Texture2D
var sequence_overlay: Texture2D
var fill_preview: Texture2D
var selection_preview: ImageTexture
var drawing_selection:=Rect2i()
var scene_background: Node2D
var frame_clip: Control
var frame_overlay: FrameOverlay
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
	frame_clip=Control.new();frame_clip.mouse_filter=Control.MOUSE_FILTER_IGNORE;frame_clip.clip_contents=true;add_child(frame_clip)
	frame_overlay=FrameOverlay.new();frame_overlay.canvas_view=self;frame_overlay.mouse_filter=Control.MOUSE_FILTER_IGNORE;frame_clip.add_child(frame_overlay)

func image_rect() -> Rect2:
	if scene_setup:
		var area:=scene_rect()
		var factor:=minf(area.size.x/resolution.x,area.size.y/resolution.y)
		return Rect2(area.position+(area.size-resolution*factor)/2.,resolution*factor)
	var scale_factor := minf(size.x / resolution.x, size.y / resolution.y) * zoom
	var extent := resolution * scale_factor
	return Rect2((size - extent) / 2 + pan, extent)

func setup_size() -> Vector2i:
	# Match the texture's actual aspect without stretching to fractional UI sizes.
	return Vector2i(maxi(1,floori(size.x)),maxi(1,floori(size.y)))

func scene_rect() -> Rect2:
	if scene_setup:
		var extent:=Vector2(setup_size())
		return Rect2((size-extent)/2.,extent)
	return image_rect()

func scene_contains(point: Vector2) -> bool:
	if not point.is_finite():return false
	var frame:=image_rect()
	var screen:=frame.position+point/resolution*frame.size
	return Rect2(Vector2.ZERO,size).has_point(screen) and scene_rect().has_point(screen)

func scene_uv(point: Vector2) -> Vector2:
	var frame:=image_rect();var area:=scene_rect()
	return (frame.position+point/resolution*frame.size-area.position)/area.size

func _draw() -> void:
	var rect := image_rect()
	scene_background.texture=setup_background if scene_setup else background;scene_background.rect=scene_rect() if scene_setup else rect;scene_background.queue_redraw()
	if sequence_overlay:draw_texture_rect(sequence_overlay,rect,false)
	if selection_preview:draw_texture_rect(selection_preview,rect,false)
	elif fill_preview:draw_texture_rect(fill_preview,rect,false)
	elif overlay:draw_texture_rect(overlay,rect,false)
	var bounds:=scene_rect()
	frame_clip.position=bounds.position;frame_clip.size=bounds.size;frame_overlay.position=rect.position-bounds.position;frame_overlay.size=rect.size;frame_overlay.queue_redraw()
	if drawing_selection.has_area():
		var selected:=Rect2(rect.position+Vector2(drawing_selection.position)/resolution*rect.size,Vector2(drawing_selection.size)/resolution*rect.size)
		draw_rect(selected,Color.BLACK,false,3);draw_rect(selected,Color.WHITE,false,1)
	if not scene_editing or show_camera_frame:draw_rect(rect, Color("dce8f2"), false, 1)
	if scene_editing and show_thirds:
		for i in [1,2]:
			var portion:=float(i)/3.
			draw_line(rect.position+Vector2(rect.size.x*portion,0),rect.position+Vector2(rect.size.x*portion,rect.size.y),Color(1,1,1,.6),1,true)
			draw_line(rect.position+Vector2(0,rect.size.y*portion),rect.position+Vector2(rect.size.x,rect.size.y*portion),Color(1,1,1,.6),1,true)

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
