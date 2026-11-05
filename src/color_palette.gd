extends RefCounted
const MAX_COLORS:=32
static func error(value) -> String:
	if not value is Array or value.size()>MAX_COLORS:return "A project supports up to32 color swatches."
	for row in value:
		if not row is Dictionary or row.size()!=2 or not row.get("name") is String or not row.get("rgba") is String:return "Invalid project color swatch."
		if row.name.is_empty() or row.name.length()>48:return "Swatch names must contain1–48 characters."
		for character in row.name:
			var code: int=character.unicode_at(0)
			if code<32 or code==127 or code>=0xd800 and code<=0xdfff:return "Swatch names cannot contain control characters."
		if row.rgba.length()!=8:return "Swatch colors must contain eight RGBA hexadecimal digits."
		for character in row.rgba:
			if not character in "0123456789abcdef":return "Swatch colors must contain eight lowercase RGBA hexadecimal digits."
	return ""

static func icon(ink: Color) -> ImageTexture:
	var image:=Image.create(24,24,false,Image.FORMAT_RGBA8)
	for y in range(24):
		for x in range(24):
			var checker:=Color("dddddd") if (int(x/6)+int(y/6))%2==0 else Color.WHITE
			image.set_pixel(x,y,checker.blend(ink))
	return ImageTexture.create_from_image(image)
