extends Control
var picture: Texture2D
var zoom:=1.
var pan:=Vector2.ZERO
var dragging:=false
func _ready() -> void:
	clip_contents=true;mouse_filter=Control.MOUSE_FILTER_STOP;focus_mode=Control.FOCUS_ALL;resized.connect(queue_redraw)
func set_picture(value: Texture2D) -> void:
	picture=value;fit()
func fit() -> void:zoom=1.;pan=Vector2.ZERO;dragging=false;queue_redraw()
func picture_rect() -> Rect2:
	if not picture:return Rect2()
	var dimensions:=Vector2(picture.get_size());var extent:=dimensions*minf(size.x/dimensions.x,size.y/dimensions.y)*zoom
	return Rect2((size-extent)/2+pan,extent)
func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO,size),Color("c5cdd5"))
	if not picture:return
	var rect:=picture_rect()
	# Limit the checkerboard to the visible control, even at maximum zoom.
	var visible:=rect.intersection(Rect2(Vector2.ZERO,size))
	for y in range(int(visible.position.y)/16,int(ceil(visible.end.y/16))):
		for x in range(int(visible.position.x)/16,int(ceil(visible.end.x/16))):
			var tile:=Rect2(Vector2(x,y)*16,Vector2(16,16)).intersection(visible)
			draw_rect(tile,Color("f5f5f5") if (x+y)%2==0 else Color("dddddd"))
	draw_texture_rect(picture,rect,false);draw_rect(rect,Color("71869a"),false,1)
func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		if event.button_index in [MOUSE_BUTTON_LEFT,MOUSE_BUTTON_MIDDLE]:dragging=event.pressed;grab_focus();accept_event()
		elif event.pressed and event.button_index in [MOUSE_BUTTON_WHEEL_UP,MOUSE_BUTTON_WHEEL_DOWN] and picture:
			var old:=picture_rect();zoom=clampf(zoom*(1.2 if event.button_index==MOUSE_BUTTON_WHEEL_UP else 1./1.2),.1,16.)
			var rect:=picture_rect();pan+=event.position-(rect.position+(event.position-old.position)/old.size*rect.size);queue_redraw();accept_event()
	elif event is InputEventMouseMotion and dragging:pan+=event.relative;queue_redraw();accept_event()
