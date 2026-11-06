extends RefCounted
# Delivery sizes only. Authored raster/camera coordinates remain full HD.
const PROFILES={"1080p":Vector2i(1920,1080),"720p":Vector2i(1280,720),"540p":Vector2i(960,540)}
static func error(value) -> String:
	return "" if value is String and PROFILES.has(value) else "Choose an available Output size in Advanced → Movie encoder."

static func resample(image: Image,size: Vector2i) -> Image:
	if image==null or image.is_empty() or size.x<1 or size.y<1 or size.x>1920 or size.y>1080:return null
	if image.get_size()==size:return image
	var resized: Image=image.duplicate();resized.convert(Image.FORMAT_RGBA8)
	# Resize detached premultiplied pixels, then return straight RGBA. Hidden RGB
	# under transparent pixels must not bleed into the visible drawing edges.
	var alpha: bool=resized.detect_alpha()!=Image.ALPHA_NONE
	if alpha:resized.premultiply_alpha()
	resized.resize(size.x,size.y,Image.INTERPOLATE_BILINEAR)
	return preload("res://src/sequence_pixels.gd").straight(resized) if alpha else resized
