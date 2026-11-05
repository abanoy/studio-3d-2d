extends RefCounted
const MAX_PIXELS:=1920*1080

static func rectangle(from: Vector2,to: Vector2,size: Vector2i) -> Rect2i:
	if not from.is_finite() or not to.is_finite() or size.x<1 or size.y<1:return Rect2i()
	var a:=Vector2i(from.clamp(Vector2.ZERO,Vector2(size)).floor());var b:=Vector2i(to.clamp(Vector2.ZERO,Vector2(size)).floor())
	return Rect2i(a.min(b),(a-b).abs())

static func clamp_offset(rect: Rect2i,offset: Vector2i,size: Vector2i) -> Vector2i:
	return offset.clamp(-rect.position,size-rect.end)

static func move(image: Image,rect: Rect2i,requested: Vector2i,copy: bool=false) -> Dictionary:
	if image==null or image.is_empty() or image.get_format()!=Image.FORMAT_RGBA8 or image.get_width()*image.get_height()>MAX_PIXELS:return {"error":"Selection needs a bounded RGBA drawing."}
	var size:=image.get_size()
	if rect.position.x<0 or rect.position.y<0 or rect.size.x<1 or rect.size.y<1 or rect.position.x>=size.x or rect.position.y>=size.y or rect.size.x>size.x-rect.position.x or rect.size.y>size.y-rect.position.y:return {"error":"Select an area inside the drawing first."}
	var offset:=clamp_offset(rect,requested,size);var destination:=Rect2i(rect.position+offset,rect.size)
	var unchanged:={"image":image,"selection":destination,"offset":offset,"changed":false,"damage":Rect2i()}
	if offset==Vector2i.ZERO:return unchanged
	var patch:=image.get_region(rect)
	if patch.is_invisible():return unchanged
	var result: Image=image.duplicate()
	if not copy:result.fill_rect(rect,Color(0,0,0,0))
	result.blend_rect(patch,Rect2i(Vector2i.ZERO,patch.get_size()),destination.position)
	var damage:=destination if copy else rect.merge(destination)
	var changed: bool=image.get_region(damage).get_data()!=result.get_region(damage).get_data()
	return {"image":result,"selection":destination,"offset":offset,"changed":changed,"damage":damage if changed else Rect2i()}
