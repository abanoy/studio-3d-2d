extends Control
const PathData=preload("res://src/movement_path.gd")
const StudioTheme=preload("res://src/studio_theme.gd")
signal chosen(frame: int)
signal moved(frame: int,position: Vector3)
var points: Array=[]
var line: Array=[]
var selected:=-1
var view:=0
var center:=Vector2.ZERO
var pixels:=70.
var dragging:=-1
var grab_offset:=Vector2.ZERO
var enabled:=true

func fit() -> void:
	var all:=points+line
	if all.is_empty():center=Vector2.ZERO;pixels=70.;queue_redraw();return
	var first: Vector2=PathData.projected(all[0].position,view);var bounds:=Rect2(first,Vector2.ZERO)
	for point in all:bounds=bounds.expand(PathData.projected(point.position,view))
	center=bounds.get_center();var extent:=bounds.size.max(Vector2(2,2));pixels=maxf(1.,minf((size.x-70)/extent.x,(size.y-70)/extent.y));queue_redraw()

func screen(position: Vector3) -> Vector2:
	var p: Vector2=(PathData.projected(position,view)-center)*pixels
	return size/2.+Vector2(p.x,-p.y)

func _draw() -> void:
	# Neon Pro step 9: neon plot is a #05060A stage card (1 px #2C303B, r8) with #363B48 axes, a
	# #4DA3FF path, #A98BFF key dots (selected #FFC24B) and #F4F6FA mono frame numbers (18:1).
	# Classic keeps the pale card, navy dots and navy numbers.
	var neon:=StudioTheme.is_neon()
	if neon:draw_style_box(StudioTheme.flat(StudioTheme.STAGE,StudioTheme.LINE2,8,1),Rect2(Vector2.ZERO,size))
	else:draw_style_box(StudioTheme.surface("e8f2fb","c9d9e8"),Rect2(Vector2.ZERO,size))
	var axis:=StudioTheme.LINE3 if neon else Color("9aaebe")
	var origin:=screen(Vector3.ZERO);draw_line(Vector2(0,origin.y),Vector2(size.x,origin.y),axis);draw_line(Vector2(origin.x,0),Vector2(origin.x,size.y),axis)
	for n in range(1,line.size()):
		if line[n].join:draw_line(screen(line[n-1].position),screen(line[n].position),StudioTheme.DRAWING if neon else Color("257ac2"),2,true)
	var ink:=StudioTheme.TEXT if neon else Color("172b3b")
	var font: Font=StudioTheme.mono(500) if neon else ThemeDB.fallback_font
	for point in points:
		var p:=screen(point.position);draw_circle(p,8,(StudioTheme.WARNING if neon else Color("f5be4b")) if point.frame==selected else (StudioTheme.MODEL if neon else Color("172b3b")));draw_circle(p,3,StudioTheme.STAGE if neon else Color.WHITE)
		draw_string(font,p+Vector2(10,-7),str(point.frame),HORIZONTAL_ALIGNMENT_LEFT,-1,13 if neon else 14,ink)

func _gui_input(event: InputEvent) -> void:
	if not enabled:return
	if event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_LEFT:
		if not event.pressed:dragging=-1;accept_event();return
		var nearest:=-1;var distance:=15.
		for n in range(points.size()):
			var d: float=screen(points[n].position).distance_to(event.position)
			if d<distance:nearest=n;distance=d
		if nearest>=0:dragging=nearest;grab_offset=event.position-screen(points[nearest].position);selected=points[nearest].frame;chosen.emit(selected);queue_redraw();accept_event()
	if event is InputEventMouseMotion and dragging>=0:
		var point: Dictionary=points[dragging];var offset: Vector2=(event.position-grab_offset-size/2.)/pixels
		var projected:=center+Vector2(offset.x,-offset.y);var value: Vector3=PathData.unprojected(projected,point.position,view)
		moved.emit(point.frame,value);accept_event()
