extends RefCounted
# Transparent viewport readback is premultiplied; Image.blend_rect takes straight RGBA.
static var lookup: Array=[]
static func straight(image: Image) -> Image:
	if lookup.is_empty():
		for a in range(256):
			var row:=PackedByteArray();row.resize(256)
			for c in range(256):row[c]=0 if a==0 else mini(255,roundi(float(c)*255/a))
			lookup.append(row)
	var bytes:=image.get_data()
	for at in range(0,bytes.size(),4):
		var alpha:=bytes[at+3]
		if alpha==255:continue
		var row: PackedByteArray=lookup[alpha]
		bytes[at]=row[bytes[at]];bytes[at+1]=row[bytes[at+1]];bytes[at+2]=row[bytes[at+2]]
	return Image.create_from_data(image.get_width(),image.get_height(),false,Image.FORMAT_RGBA8,bytes)
