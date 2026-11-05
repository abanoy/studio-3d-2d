extends RefCounted
# Four-connected scanline fill over detached RGBA8 bytes. No scene/GPU access.
const MAX_PIXELS:=1920*1080

static func matches(data: PackedByteArray,pixel: int,seed: PackedInt32Array,threshold: int) -> bool:
	var i:=pixel*4;var alpha:=int(data[i+3])
	return absi(alpha-seed[3])*255<=threshold and absi(int(data[i])*alpha-seed[0])<=threshold and absi(int(data[i+1])*alpha-seed[1])<=threshold and absi(int(data[i+2])*alpha-seed[2])<=threshold

static func calculate(sample: PackedByteArray,target: PackedByteArray,width: int,height: int,point: Vector2i,paint: PackedByteArray,tolerance: int) -> Dictionary:
	var started:=Time.get_ticks_usec();var count:=width*height
	if width<1 or height<1 or count>MAX_PIXELS or sample.size()!=count*4 or target.size()!=count*4 or paint.size()!=4 or tolerance<0 or tolerance>255 or point.x<0 or point.y<0 or point.x>=width or point.y>=height:return {"error":"Invalid fill snapshot."}
	var offset:=(point.y*width+point.x)*4;var a:=int(sample[offset+3])
	var seed:=PackedInt32Array([int(sample[offset])*a,int(sample[offset+1])*a,int(sample[offset+2])*a,a])
	var threshold:=tolerance*255;var seen:=PackedByteArray();seen.resize(count)
	var stack:=PackedInt32Array([point.y*width+point.x]);var result:=target.duplicate()
	var changed:=0;var region:=0;var edge:=false;var min_x:=width;var min_y:=height;var max_x:=-1;var max_y:=-1
	while not stack.is_empty():
		var at:=stack[-1];stack.remove_at(stack.size()-1)
		if seen[at]!=0 or not matches(sample,at,seed,threshold):continue
		var y:=int(at/width);var x:=at%width
		while x>0 and seen[y*width+x-1]==0 and matches(sample,y*width+x-1,seed,threshold):x-=1
		var above:=false;var below:=false
		while x<width:
			var pixel:=y*width+x
			if seen[pixel]!=0 or not matches(sample,pixel,seed,threshold):break
			seen[pixel]=1;region+=1
			edge=edge or x==0 or y==0 or x==width-1 or y==height-1
			var i:=pixel*4
			if result[i]!=paint[0] or result[i+1]!=paint[1] or result[i+2]!=paint[2] or result[i+3]!=paint[3]:
				for channel in range(4):result[i+channel]=paint[channel]
				changed+=1;min_x=mini(min_x,x);min_y=mini(min_y,y);max_x=maxi(max_x,x);max_y=maxi(max_y,y)
			var upper: bool=y>0 and seen[pixel-width]==0 and matches(sample,pixel-width,seed,threshold)
			var lower: bool=y<height-1 and seen[pixel+width]==0 and matches(sample,pixel+width,seed,threshold)
			if upper and not above:stack.append(pixel-width)
			if lower and not below:stack.append(pixel+width)
			above=upper;below=lower;x+=1
		if stack.size()>count*2:return {"error":"Fill workspace limit reached; drawing preserved."}
	return {"data":result,"changed":changed,"region":region,"edge":edge,"bounds":Rect2i(min_x,min_y,max_x-min_x+1,max_y-min_y+1) if changed else Rect2i(),"worker_ms":(Time.get_ticks_usec()-started)/1000.0,"background_thread":not Thread.is_main_thread()}
