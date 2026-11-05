extends RefCounted
# Detached RGBA8 resampling only. No Images, scene nodes, textures or GPU access.
const MAX_PIXELS:=1920*1080

static func sample(data: PackedByteArray,width: int,rect: Rect2i,u: float,v: float) -> Vector4:
	if u<-.5 or v<-.5 or u>=rect.size.x-.5 or v>=rect.size.y-.5:return Vector4.ZERO
	var x:=floori(u);var y:=floori(v);var fx:=u-x;var fy:=v-y;var result:=Vector4.ZERO
	for j in range(2):
		var yy:=clampi(y+j,0,rect.size.y-1);var wy:=fy if j==1 else 1-fy
		for i in range(2):
			var xx:=clampi(x+i,0,rect.size.x-1);var weight:=wy*(fx if i==1 else 1-fx);var at:=((rect.position.y+yy)*width+rect.position.x+xx)*4
			var alpha: float=data[at+3]*weight
			result+=Vector4(data[at]*alpha,data[at+1]*alpha,data[at+2]*alpha,alpha)
	return result

static func calculate(data: PackedByteArray,width: int,height: int,rect: Rect2i,scale_x: float,scale_y: float,degrees: float,copy: bool=false) -> Dictionary:
	var started:=Time.get_ticks_usec();var count:=width*height
	if width<1 or height<1 or count>MAX_PIXELS or data.size()!=count*4 or rect.position.x<0 or rect.position.y<0 or rect.size.x<1 or rect.size.y<1 or rect.position.x>=width or rect.position.y>=height or rect.size.x>width-rect.position.x or rect.size.y>height-rect.position.y or not is_finite(scale_x) or not is_finite(scale_y) or not is_finite(degrees) or scale_x<.05 or scale_y<.05 or scale_x>4 or scale_y>4 or absf(degrees)>180:return {"error":"Invalid drawing transform. Size must be5–400percent and angle−180–180degrees."}
	var radians:=deg_to_rad(degrees);var c:=cos(radians);var s:=sin(radians)
	if absf(c)<1e-12:c=0
	if absf(s)<1e-12:s=0
	# Tiny tolerance removes trigonometric roundoff at exact pixel/quarter turns.
	var extent:=Vector2i(maxi(1,ceili(absf(rect.size.x*scale_x*c)+absf(rect.size.y*scale_y*s)-1e-9)),maxi(1,ceili(absf(rect.size.x*scale_x*s)+absf(rect.size.y*scale_y*c)-1e-9)))
	if extent.x>width or extent.y>height:return {"error":"Transformed selection is larger than the frame. Reduce its size or angle; drawing preserved."}
	var center:=rect.position+Vector2i(int(rect.size.x/2),int(rect.size.y/2));var wanted:=center-Vector2i(int(extent.x/2),int(extent.y/2));var position:=wanted.clamp(Vector2i.ZERO,Vector2i(width,height)-extent);var destination:=Rect2i(position,extent)
	var unchanged:={"data":data,"selection":destination,"changed":false,"damage":Rect2i(),"repositioned":position!=wanted,"worker_ms":0.0,"background_thread":not Thread.is_main_thread()}
	if scale_x==1 and scale_y==1 and degrees==0:return unchanged
	var visible:=false
	for y in range(rect.position.y,rect.end.y):
		for x in range(rect.position.x,rect.end.x):
			if data[(y*width+x)*4+3]>0:visible=true;break
		if visible:break
	if not visible:return unchanged
	var result:=data.duplicate()
	if not copy:
		for y in range(rect.position.y,rect.end.y):
			for x in range(rect.position.x,rect.end.x):
				var at:=(y*width+x)*4
				for channel in range(4):result[at+channel]=0
	var orthogonal: bool=c==0 or s==0
	var offsets: Array=[Vector2(.5,.5)] if orthogonal else [Vector2(.25,.25),Vector2(.75,.25),Vector2(.25,.75),Vector2(.75,.75)]
	for y in range(extent.y):
		for x in range(extent.x):
			var source:=Vector4.ZERO
			for sub in offsets:
				var dx: float=x+sub.x-extent.x/2.0;var dy: float=y+sub.y-extent.y/2.0
				source+=sample(data,width,rect,(c*dx+s*dy)/scale_x+rect.size.x/2.0-.5,(-s*dx+c*dy)/scale_y+rect.size.y/2.0-.5)
			source/=offsets.size()
			if source.w<=0:continue
			var at:=((position.y+y)*width+position.x+x)*4;var back: float=result[at+3]*(1-source.w/255.0);var alpha:=source.w+back
			result[at]=clampi(roundi((source.x+result[at]*back)/alpha),0,255)
			result[at+1]=clampi(roundi((source.y+result[at+1]*back)/alpha),0,255)
			result[at+2]=clampi(roundi((source.z+result[at+2]*back)/alpha),0,255)
			result[at+3]=clampi(roundi(alpha),0,255)
	var changed: bool=result!=data
	return {"data":result,"selection":destination,"changed":changed,"damage":(destination if copy else rect.merge(destination)) if changed else Rect2i(),"repositioned":position!=wanted,"worker_ms":(Time.get_ticks_usec()-started)/1000.0,"background_thread":not Thread.is_main_thread()}
