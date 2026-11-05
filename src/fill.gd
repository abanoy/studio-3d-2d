extends RefCounted
# Four/eight-connected scanline fill over detached RGBA8 bytes. No scene/GPU access.
const MAX_PIXELS:=1920*1080

static func matches(data: PackedByteArray,pixel: int,seed: PackedInt32Array,threshold: int) -> bool:
	var i:=pixel*4;var alpha:=int(data[i+3])
	return absi(alpha-seed[3])*255<=threshold and absi(int(data[i])*alpha-seed[0])<=threshold and absi(int(data[i+1])*alpha-seed[1])<=threshold and absi(int(data[i+2])*alpha-seed[2])<=threshold

static func calculate(sample: PackedByteArray,target: PackedByteArray,width: int,height: int,point: Vector2i,paint: PackedByteArray,tolerance: int,gap_pixels: int=0,expand_pixels: int=0,connectivity: int=4) -> Dictionary:
	var started:=Time.get_ticks_usec();var count:=width*height
	if width<1 or height<1 or count>MAX_PIXELS or sample.size()!=count*4 or target.size()!=count*4 or paint.size()!=4 or tolerance<0 or tolerance>255 or gap_pixels<0 or gap_pixels>8 or expand_pixels<0 or expand_pixels>8 or connectivity not in [4,8] or point.x<0 or point.y<0 or point.x>=width or point.y>=height:return {"error":"Invalid fill snapshot."}
	var offset:=(point.y*width+point.x)*4;var a:=int(sample[offset+3])
	var seed:=PackedInt32Array([int(sample[offset])*a,int(sample[offset+1])*a,int(sample[offset+2])*a,a])
	var threshold:=tolerance*255;var seen:=PackedByteArray();seen.resize(count)
	var allowed:=PackedByteArray();var sealed:=0
	if gap_pixels>0:
		allowed.resize(count)
		for i in range(count):allowed[i]=int(matches(sample,i,seed,threshold))
		var closed:=preload("res://src/fill_gaps.gd").close(allowed,width,height,gap_pixels)
		for i in range(count):sealed+=int(allowed[i]!=closed[i])
		allowed=closed
		if allowed[point.y*width+point.x]==0:return {"error":"Gap closing removes the clicked narrow region. Reduce Close gaps or set it to0; drawing preserved."}
	var stack:=PackedInt32Array([point.y*width+point.x]);var result:=target.duplicate()
	# Eight-connected span endpoints can meet the same diagonal seed repeatedly.
	# Schedule each pixel at most once; default four-connectivity needs no extra mask.
	var queued:=PackedByteArray()
	if connectivity==8:queued.resize(count);queued[point.y*width+point.x]=1
	var pending_peak:=1
	var changed:=0;var region:=0;var edge:=false;var min_x:=width;var min_y:=height;var max_x:=-1;var max_y:=-1
	while not stack.is_empty():
		var at:=stack[-1];stack.remove_at(stack.size()-1)
		if seen[at]!=0 or not (matches(sample,at,seed,threshold) if allowed.is_empty() else allowed[at]!=0):continue
		var y:=int(at/width);var x:=at%width
		while x>0 and seen[y*width+x-1]==0 and (matches(sample,y*width+x-1,seed,threshold) if allowed.is_empty() else allowed[y*width+x-1]!=0):x-=1
		var first:=x;var above:=false;var below:=false
		while x<width:
			var pixel:=y*width+x
			if seen[pixel]!=0 or not (matches(sample,pixel,seed,threshold) if allowed.is_empty() else allowed[pixel]!=0):break
			seen[pixel]=1;region+=1
			edge=edge or x==0 or y==0 or x==width-1 or y==height-1
			var i:=pixel*4
			if result[i]!=paint[0] or result[i+1]!=paint[1] or result[i+2]!=paint[2] or result[i+3]!=paint[3]:
				for channel in range(4):result[i+channel]=paint[channel]
				changed+=1;min_x=mini(min_x,x);min_y=mini(min_y,y);max_x=maxi(max_x,x);max_y=maxi(max_y,y)
			var upper: bool=y>0 and seen[pixel-width]==0 and (matches(sample,pixel-width,seed,threshold) if allowed.is_empty() else allowed[pixel-width]!=0)
			var lower: bool=y<height-1 and seen[pixel+width]==0 and (matches(sample,pixel+width,seed,threshold) if allowed.is_empty() else allowed[pixel+width]!=0)
			if upper and not above and (queued.is_empty() or queued[pixel-width]==0):
				stack.append(pixel-width)
				if not queued.is_empty():queued[pixel-width]=1
			if lower and not below and (queued.is_empty() or queued[pixel+width]==0):
				stack.append(pixel+width)
				if not queued.is_empty():queued[pixel+width]=1
			above=upper;below=lower;x+=1
		if connectivity==8:
			# The two endpoints outside this row span supply its diagonal neighbors.
			for side_x in [first-1,x]:
				if side_x<0 or side_x>=width:continue
				for next_y in [y-1,y+1]:
					if next_y<0 or next_y>=height:continue
					var neighbor: int=next_y*width+side_x
					if seen[neighbor]==0 and queued[neighbor]==0 and (matches(sample,neighbor,seed,threshold) if allowed.is_empty() else allowed[neighbor]!=0):
						queued[neighbor]=1;stack.append(neighbor)
		pending_peak=maxi(pending_peak,stack.size())
		if stack.size()>count*2:return {"error":"Fill workspace limit reached; drawing preserved."}
	var expanded:=0
	if expand_pixels>0:
		# Dilate the discovered region, never the sampled ink or live target image.
		var grown:=preload("res://src/fill_gaps.gd").axis(seen,width,height,expand_pixels,expand_pixels,true,false)
		grown=preload("res://src/fill_gaps.gd").axis(grown,width,height,expand_pixels,expand_pixels,false,false)
		for pixel in range(count):
			if grown[pixel]==0 or seen[pixel]!=0:continue
			expanded+=1
			var x:=pixel%width;var y:=int(pixel/width);var i:=pixel*4
			edge=edge or x==0 or y==0 or x==width-1 or y==height-1
			if result[i]!=paint[0] or result[i+1]!=paint[1] or result[i+2]!=paint[2] or result[i+3]!=paint[3]:
				for channel in range(4):result[i+channel]=paint[channel]
				changed+=1;min_x=mini(min_x,x);min_y=mini(min_y,y);max_x=maxi(max_x,x);max_y=maxi(max_y,y)
	return {"data":result,"changed":changed,"region":region,"edge":edge,"gap_pixels":gap_pixels,"sealed_pixels":sealed,"expand_pixels":expand_pixels,"expanded_pixels":expanded,"connectivity":connectivity,"pending_peak":pending_peak,"bounds":Rect2i(min_x,min_y,max_x-min_x+1,max_y-min_y+1) if changed else Rect2i(),"worker_ms":(Time.get_ticks_usec()-started)/1000.0,"background_thread":not Thread.is_main_thread()}
