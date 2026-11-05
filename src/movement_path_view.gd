extends Control
const PathData=preload("res://src/movement_path.gd")
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
	draw_style_box(preload("res://src/studio_theme.gd").surface("e8f2fb","c9d9e8"),Rect2(Vector2.ZERO,size))
	var origin:=screen(Vector3.ZERO);draw_line(Vector2(0,origin.y),Vector2(size.x,origin.y),Color("9aaebe"));draw_line(Vector2(origin.x,0),Vector2(origin.x,size.y),Color("9aaebe"))
	for n in range(1,line.size()):
		if line[n].join:draw_line(screen(line[n-1].position),screen(line[n].position),Color("257ac2"),2,true)
	for point in points:
		var p:=screen(point.position);draw_circle(p,8,Color("f5be4b")if point.frame==selected else Color("172b3b"));draw_circle(p,3,Color.WHITE)
		var font:=ThemeDB.fallback_font;draw_string(font,p+Vector2(10,-7),str(point.frame),HORIZONTAL_ALIGNMENT_LEFT,-1,14,Color("172b3b"))

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
