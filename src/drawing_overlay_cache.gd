extends RefCounted
# One app-owned preview image; callers borrow it read-only. Final export uses
# Drawing.composite directly. Sources are weak so this cache cannot own old cels.
const Drawing=preload("res://src/drawing.gd")
const MAX_PIXELS=1920*1080
var image: Image
var stamp: Array=[]
var sources: Array[WeakRef]=[]
var builds:=0
var hits:=0
var pixels:=0
func clear() -> void:
	image=null;stamp=[];sources=[]
func sample(layers: Array,frame: int,width: int,height: int,document_revision: int) -> Dictionary:
	var key: Array=[width,height,document_revision];var active: Array[Image]=[]
	for layer in layers:
		var amount: float=layer.get("opacity",1.0)
		if not layer.visible or amount==0:continue
		var cel:=Drawing.cel_at(layer,frame)
		if cel.is_empty():continue
		var source: Image=cel.image
		active.append(source)
		key.append([source.get_instance_id(),int(source.get_meta("studio_pixels_revision",0)),source.get_width(),source.get_height(),amount])
	var valid:=image!=null and key==stamp and sources.size()==active.size()
	if valid:
		for i in range(active.size()):
			if not is_same(sources[i].get_ref(),active[i]):valid=false;break
	if valid:hits+=1;return {"image":image,"changed":false}
	clear()
	var result:=Drawing.composite(layers,frame,width,height);builds+=1;pixels+=width*height
	if width>0 and height>0 and width*height<=MAX_PIXELS:
		image=result;stamp=key
		for source in active:sources.append(weakref(source))
	return {"image":result,"changed":true}
