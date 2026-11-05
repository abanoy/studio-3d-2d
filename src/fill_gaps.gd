extends RefCounted
# Binary opening of seed-passable pixels: virtual barriers close narrow gaps.
# Four separable rolling-count passes; no live Images/nodes/GPU ownership.
static func axis(mask: PackedByteArray,width: int,height: int,before: int,after: int,horizontal: bool,erode: bool) -> PackedByteArray:
	var result:=PackedByteArray();result.resize(mask.size())
	var length:=width if horizontal else height
	var lines:=height if horizontal else width
	var step:=1 if horizontal else width
	var padding:=1 if erode else 0
	var window:=before+after+1
	for line in range(lines):
		var base:=line*width if horizontal else line
		var count:=0
		for p in range(-before,after+1):count+=mask[base+p*step] if p>=0 and p<length else padding
		for p in range(length):
			result[base+p*step]=int(count==window if erode else count>0)
			var leaving:=p-before;var entering:=p+after+1
			count-=mask[base+leaving*step] if leaving>=0 and leaving<length else padding
			count+=mask[base+entering*step] if entering>=0 and entering<length else padding
	return result

static func close(passable: PackedByteArray,width: int,height: int,gap: int) -> PackedByteArray:
	var left:=int(gap/2);var right:=gap-left
	var result:=axis(passable,width,height,left,right,true,true)
	result=axis(result,width,height,left,right,false,true)
	# Reflect the asymmetric anchor for odd gaps; otherwise the mask drifts.
	result=axis(result,width,height,right,left,true,false)
	result=axis(result,width,height,right,left,false,false)
	for i in range(result.size()):result[i]&=passable[i]
	return result
