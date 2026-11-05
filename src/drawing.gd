extends RefCounted
static var opacity_cache: Array=[] # At most four derived full-HD rasters, never source ownership.
static var opacity_pixels:=0
static var opacity_builds:=0

static func touch(image: Image,damage: Rect2i=Rect2i()) -> void:
	# Transient cache identity only; PNG/HAS pixel data and schemas are unchanged.
	image.set_meta("studio_pixels_revision",int(image.get_meta("studio_pixels_revision",0))+1)
	if not damage.has_area():image.set_meta("studio_pixels_full_damage",true)
	elif not image.get_meta("studio_pixels_full_damage",false):
		var previous: Rect2i=image.get_meta("studio_pixels_damage",Rect2i())
		image.set_meta("studio_pixels_damage",previous.merge(damage) if previous.has_area() else damage)

static func opacity_error(layers: Array) -> String:
	for layer in layers:
		if not layer is Dictionary:return "Invalid drawing layer."
		var value=layer.get("opacity",1.0)
		if not (value is int or value is float) or not is_finite(float(value)) or value<0 or value>1:return "Drawing layer opacity must be between0 and1."
	return ""

static func faded(image: Image,amount: float) -> Image:
	# Pure detached-image operation: also safe for the recovery CPU worker. Exact
	# RGBA8 alpha rounding, straight RGB retained even underneath zero alpha.
	if amount==1:return image
	var data:=image.get_data();var lookup:=PackedByteArray();lookup.resize(256)
	for a in range(256):lookup[a]=roundi(a*amount)
	for offset in range(3,data.size(),4):data[offset]=lookup[data[offset]]
	return Image.create_from_data(image.get_width(),image.get_height(),false,Image.FORMAT_RGBA8,data)

static func layer_image(image: Image,amount: float) -> Image:
	if amount==1:return image
	var revision: int=image.get_meta("studio_pixels_revision",0)
	var entry: Dictionary={}
	for i in range(opacity_cache.size()-1,-1,-1):
		var cached: Dictionary=opacity_cache[i];var original=cached.source.get_ref()
		if original==null:opacity_cache.remove_at(i)
		elif is_same(original,image):entry=cached;opacity_cache.remove_at(i)
	if entry.is_empty() or entry.amount!=amount or entry.image.get_size()!=image.get_size():
		entry={"source":weakref(image),"amount":amount,"revision":revision,"image":faded(image,amount)}
		opacity_pixels+=image.get_width()*image.get_height();opacity_builds+=1
	elif entry.revision!=revision:
		var damage: Rect2i=image.get_meta("studio_pixels_damage",Rect2i())
		damage=damage.intersection(Rect2i(Vector2i.ZERO,image.get_size()))
		if image.get_meta("studio_pixels_full_damage",false) or not damage.has_area():
			entry.image=faded(image,amount);opacity_pixels+=image.get_width()*image.get_height()
		else:
			var patch:=faded(image.get_region(damage),amount)
			entry.image.blit_rect(patch,Rect2i(Vector2i.ZERO,patch.get_size()),damage.position);opacity_pixels+=damage.get_area()
		entry.revision=revision;opacity_builds+=1
	image.set_meta("studio_pixels_full_damage",false);image.set_meta("studio_pixels_damage",Rect2i())
	opacity_cache.append(entry)
	while opacity_cache.size()>4:opacity_cache.pop_front()
	return entry.image

static func blank(width: int, height: int) -> Image:
	var image := Image.create(width, height, false, Image.FORMAT_RGBA8)
	image.fill(Color.TRANSPARENT)
	return image

static func cel_at(layer: Dictionary, frame: int) -> Dictionary:
	for cel in layer.cels:
		if frame >= cel.start and frame < cel.start + cel.duration:
			return cel
	return {}

static func insert(layer: Dictionary, frame: int, end: int, image: Image) -> Dictionary:
	# Split the active exposure; later cels retain their original boundaries.
	var next := end
	for cel in layer.cels:
		if cel.start == frame:
			cel.image = image
			return cel
		if cel.start < frame and cel.start + cel.duration > frame:
			next = mini(next, cel.start + cel.duration)
			cel.duration = frame - cel.start
		if cel.start > frame:
			next = mini(next, cel.start)
	var cel := {"id": str(ResourceUID.create_id()), "start": frame, "duration": maxi(1, next - frame), "image": image}
	layer.cels.append(cel)
	layer.cels.sort_custom(func(a, b): return a.start < b.start)
	return cel

static func stroke(image: Image, from: Vector2, to: Vector2, radius: float, color: Color, erase: bool) -> Rect2i:
	var rect := Rect2i(Vector2i((from.min(to) - Vector2.ONE * (radius + 1)).floor()), Vector2i((from.max(to) - from.min(to) + Vector2.ONE * (radius * 2 + 3)).ceil()))
	rect = rect.intersection(Rect2i(0, 0, image.get_width(), image.get_height()))
	# Distance-to-segment brush: no gaps even with sparse mouse events.
	var delta := to - from
	for y in range(rect.position.y, rect.end.y):
		for x in range(rect.position.x, rect.end.x):
			var p := Vector2(x + 0.5, y + 0.5)
			var u := 0.0 if delta.length_squared() == 0 else clampf((p - from).dot(delta) / delta.length_squared(), 0, 1)
			var coverage := clampf(radius + 0.5 - p.distance_to(from + delta * u), 0, 1)
			if coverage == 0:
				continue
			var old := image.get_pixel(x, y)
			if erase:
				old.a *= 1.0 - coverage
				image.set_pixel(x, y, old)
			else:
				var paint := color
				paint.a *= coverage
				image.set_pixel(x, y, old.blend(paint))
	touch(image,rect)
	return rect

static func composite(layers: Array, frame: int, width: int, height: int) -> Image:
	var result := blank(width, height)
	for layer in layers:
		var amount: float=layer.get("opacity",1.0)
		if not layer.visible or amount==0:
			continue
		var cel := cel_at(layer, frame)
		if not cel.is_empty():
			result.blend_rect(layer_image(cel.image,amount), Rect2i(0, 0, width, height), Vector2i.ZERO)
	return result
