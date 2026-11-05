extends RefCounted
const Drawing=preload("res://src/drawing.gd")
# One transient stroke. Only the resulting RGBA pixels enter a HAS document.
var radius:=6.0
var ink:=Color.WHITE
var erase:=false
var opacity:=1.0
var pressure_size:=false
var before: Dictionary={}
var masks: Dictionary={}

func paint(image: Image,from: Vector2,to: Vector2,start_radius: float=-1,end_radius: float=-1) -> bool:
	if not is_finite(opacity) or opacity<=0 or not from.is_finite() or not to.is_finite():return false
	if not erase and ink.a<=0:return false
	var r0:=radius if start_radius<0 else start_radius
	var r1:=radius if end_radius<0 else end_radius
	if not is_finite(r0) or not is_finite(r1) or r0<0 or r1<0 or maxf(r0,r1)>64:return false
	var maximum:=maxf(r0,r1)
	var bounds:=Rect2i(Vector2i((from.min(to)-Vector2.ONE*(maximum+2)).floor()),Vector2i((to.max(from)-to.min(from)+Vector2.ONE*(maximum*2+4)).ceil())).intersection(Rect2i(Vector2i.ZERO,image.get_size()))
	for ty in range(bounds.position.y/64,(bounds.end.y+63)/64):
		for tx in range(bounds.position.x/64,(bounds.end.x+63)/64):
			var pos:=Vector2i(tx*64,ty*64)
			if not before.has(pos):before[pos]=image.get_region(Rect2i(pos,Vector2i(64,64)).intersection(Rect2i(Vector2i.ZERO,image.get_size())))
	# Retain the existing full-strength mouse brush byte for byte.
	if not pressure_size and r0==radius and r1==radius and opacity==1 and (erase or ink.a==1):
		Drawing.stroke(image,from,to,radius,ink,erase);return bounds.has_area()
	var delta:=to-from
	var length_squared:=delta.length_squared()
	var length:=sqrt(length_squared)
	var change:=r1-r0
	var unit:=delta/length if length>0 else Vector2.ZERO
	var denominator:=sqrt(maxf(0,length_squared-change*change))
	var changed:=false
	for y in range(bounds.position.y,bounds.end.y):
		for x in range(bounds.position.x,bounds.end.x):
			var point:=Vector2(x+0.5,y+0.5)
			# Maximize radius(t)-distance(point,center(t)) over the segment.
			# This is the union of continuously varying discs, including caps;
			# closest-center projection alone pinches a quickly widening stroke.
			var u:=0.0
			if length==0:u=1.0 if r1>r0 else 0.0
			elif change>=length:u=1
			elif change>-length:
				var relative:=point-from
				u=clampf((relative.dot(unit)+change*absf(relative.cross(unit))/denominator)/length,0,1)
			var coverage:=clampf(lerpf(r0,r1,u)+0.5-point.distance_to(from+delta*u),0,1)
			if coverage==0:continue
			var pos:=Vector2i(x/64*64,y/64*64)
			var local:=Vector2i(x,y)-pos
			if not masks.has(pos):
				var mask:=Image.create(before[pos].get_width(),before[pos].get_height(),false,Image.FORMAT_RF)
				mask.fill(Color(0,0,0));masks[pos]=mask
			var mask: Image=masks[pos]
			if coverage<=mask.get_pixelv(local).r:continue
			mask.set_pixelv(local,Color(coverage,0,0))
			var original: Color=before[pos].get_pixelv(local)
			var result:=original
			if erase:result.a*=1-clampf(opacity,0,1)*coverage
			else:
				var paint:=ink;paint.a*=clampf(opacity,0,1)*coverage
				result=original.blend(paint)
			if result!=image.get_pixel(x,y):image.set_pixel(x,y,result);changed=true
	if changed:Drawing.touch(image,bounds)
	return changed
