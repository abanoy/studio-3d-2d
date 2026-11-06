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
	var key: Array=[width,height,document_revision];var active: Array[RefCounted]=[]
	for layer in layers:
		var amount: float=layer.get("opacity",1.0)
		if not layer.visible or amount==0:continue
		var cel:=Drawing.cel_at(layer,frame)
		if cel.is_empty():continue
		var why:=Drawing.raster_error(cel)
		if not why.is_empty():return {"error":why,"image":null,"changed":false}
		var source:=Drawing.raster_source(cel);var token:=Drawing.raster_token(cel);var size:=Drawing.raster_size(cel)
		active.append(source)
		key.append([token[0],token[1],size.x,size.y,amount])
	var valid:=image!=null and key==stamp and sources.size()==active.size()
	if valid:
		for i in range(active.size()):
			if not is_same(sources[i].get_ref(),active[i]):valid=false;break
	if valid:hits+=1;return {"image":image,"changed":false}
	clear()
	var composite:=Drawing.composite_result(layers,frame,width,height)
	if composite.has("error"):return {"error":composite.error,"image":null,"changed":false}
	var result: Image=composite.image;builds+=1;pixels+=width*height
	if width>0 and height>0 and width*height<=MAX_PIXELS:
		image=result;stamp=key
		for source in active:sources.append(weakref(source))
	return {"image":result,"changed":true}
