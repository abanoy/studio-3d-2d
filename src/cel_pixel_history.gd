extends RefCounted
const Owner=preload("res://src/cel_raster_owner.gd")
const Drawing=preload("res://src/drawing.gd")
static func promote(command: Dictionary,layers: Array,scene: String) -> void:
	if command.get("type")!="pixels" or not command.get("image") is Image or command.has("raster_owner"):return
	var matches: Array=[]
	for layer in layers:
		for cel in layer.cels:
			var owner=cel.get("raster_owner")
			if owner is Owner and owner.owns(command.image):matches.append(owner)
	# Preserve legacy ownership if a malformed caller aliases one Image among
	# multiple logical owners; its strong reference will safely prevent cooling.
	if matches.size()!=1:return
	command.raster_owner=matches[0];command.scene_owner=scene;command.erase("image")
static func apply(command: Dictionary,side: String,layers: Array,scene: String) -> Dictionary:
	if not side in ["before","after"] or not command.get(side) is Dictionary or command[side].is_empty():return {"error":"Invalid drawing pixel history."}
	var size:=Vector2i.ZERO;var owner=command.get("raster_owner");var image: Image
	if owner is Owner:
		if command.has("image") or command.get("scene_owner")!=scene:return {"error":"Drawing pixel history belongs to another scene."}
		var found:=0
		for layer in layers:
			for cel in layer.cels:
				if is_same(cel.get("raster_owner"),owner):found+=1
		if found!=1:return {"error":"Drawing pixel history target is missing or ambiguous."}
		size=owner.dimensions()
	elif command.get("image") is Image and not command.has("raster_owner"):
		image=command.image;size=image.get_size()
	else:return {"error":"Drawing pixel history has no readable target."}
	var damage:=Rect2i()
	# Check every tile before pinning or writing, so malformed/stale commands
	# cannot partly change pixels or unnecessarily hydrate an offscreen owner.
	for pos in command[side]:
		var tile=command[side][pos]
		if not pos is Vector2i or not tile is Image or tile.is_empty() or tile.get_format()!=Image.FORMAT_RGBA8 or tile.has_mipmaps() or not Rect2i(Vector2i.ZERO,size).encloses(Rect2i(pos,tile.get_size())):return {"error":"Drawing pixel history exceeds its canvas."}
		var rect:=Rect2i(pos,tile.get_size());damage=damage.merge(rect) if damage.has_area() else rect
	if owner is Owner:
		var pinned: Dictionary=owner.pin()
		if pinned.has("error"):return pinned
		image=pinned.image
	for pos in command[side]:
		var tile: Image=command[side][pos];image.blit_rect(tile,Rect2i(Vector2i.ZERO,tile.get_size()),pos)
	Drawing.touch(image,damage)
	return {"damage":damage}
