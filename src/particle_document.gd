extends RefCounted
# Canonical scene instances reference prepared data and PNG, never native PCFs.
const FORMAT := "studio_particle_instance_1"
const MAX_EFFECTS := 16
const MAX_JSON := 1024*1024
const MAX_TEXTURE := 8*1024*1024
const FIELDS := ["format","id","name","source","sha256","path","texture_source","texture_sha256","texture_path","position","rotation_xyzw","scale","start_frame","end_frame","source_in_seconds","visible"]
const Sprite=preload("res://src/particle_sprite.gd")

static func hash_ok(value) -> bool:
	if not value is String or value.length()!=64:return false
	for c in value:
		if not c in "0123456789abcdef":return false
	return true

static func integer(value,low: int,high: int) -> bool:
	return Sprite.number(value,low,high) and value==floor(value)

static func asset_path(digest: String,extension: String) -> String:
	return "assets/"+digest+"."+extension

static func definition(source: String,texture: String,name := "Particle effect") -> Dictionary:
	return {"format":FORMAT,"id":str(ResourceUID.create_id()),"name":name,"source":source,"sha256":FileAccess.get_sha256(source),"texture_source":texture,"texture_sha256":FileAccess.get_sha256(texture),"position":[0.,0.,0.],"rotation_xyzw":[0.,0.,0.,1.],"scale":1.,"start_frame":0,"end_frame":48,"source_in_seconds":0.,"visible":true}

static func validate(row,duration: int,portable := false) -> String:
	if not row is Dictionary or row.get("format")!=FORMAT or not row.get("name") is String or row.name.is_empty() or row.name.length()>256:return "Invalid particle instance."
	for key in row:
		if not key in FIELDS:return "Unsupported particle instance field: "+str(key)
	if not hash_ok(row.get("sha256")) or not hash_ok(row.get("texture_sha256")):return "Invalid particle asset identity."
	if not Sprite.vector(row.get("position"),3) or not Sprite.vector(row.get("rotation_xyzw"),4) or not Sprite.number(row.get("scale"),.0001,1000):return "Invalid particle placement."
	var q: Array=row.rotation_xyzw
	if Vector4(q[0],q[1],q[2],q[3]).length()<.001:return "Invalid particle rotation."
	if not integer(row.get("start_frame"),0,duration-1) or not integer(row.get("end_frame"),1,duration) or row.start_frame>=row.end_frame or not Sprite.number(row.get("source_in_seconds"),0,60) or not row.get("visible") is bool:return "Invalid particle timing or visibility."
	if portable:
		if row.has("source") or row.has("texture_source") or row.get("path")!=asset_path(row.sha256,"json") or row.get("texture_path")!=asset_path(row.texture_sha256,"png"):return "Invalid managed particle paths."
	elif not row.get("source") is String or row.source.is_empty() or not row.get("texture_source") is String or row.texture_source.is_empty():return "Missing prepared particle data or texture."
	return ""

static func assets(row: Dictionary) -> Array:
	return [{"source":row.get("source",""),"path":asset_path(row.sha256,"json"),"sha256":row.sha256,"limit":MAX_JSON},{"source":row.get("texture_source",""),"path":asset_path(row.texture_sha256,"png"),"sha256":row.texture_sha256,"limit":MAX_TEXTURE}]

static func load_data(row: Dictionary) -> Dictionary:
	for asset in assets(row):
		var file:=FileAccess.open(asset.source,FileAccess.READ)
		if file==null or file.get_length()>asset.limit or FileAccess.get_sha256(asset.source)!=asset.sha256:return {"error":"Particle asset is missing, changed or oversized: "+row.name}
	var parser:=JSON.new()
	if parser.parse(FileAccess.get_file_as_string(row.source))!=OK:return {"error":"Invalid prepared particle JSON."}
	var error:=Sprite.validate(parser.data)
	if not error.is_empty():return {"error":error}
	var value: Dictionary=parser.data
	if not value.get("texture") is Dictionary or value.texture.get("sha256")!=row.texture_sha256 or value.texture.get("blend")!="additive" or value.texture.get("path")!="sprite.png":return {"error":"Particle descriptor texture binding differs."}
	var bytes:=FileAccess.get_file_as_bytes(row.texture_source)
	if bytes.size()<24 or bytes.slice(0,8)!=PackedByteArray([137,80,78,71,13,10,26,10]):return {"error":"Particle texture is not a PNG."}
	# IHDR dimensions are big-endian. Reject decompression bombs before decoding.
	var width:=0;var height:=0
	for i in range(4):width=(width<<8)|bytes[16+i];height=(height<<8)|bytes[20+i]
	if width<1 or height<1 or width>4096 or height>4096 or width*height>4194304:return {"error":"Particle texture exceeds4MP."}
	var image:=Image.new()
	if image.load_png_from_buffer(bytes)!=OK or image.get_width()!=width or image.get_height()!=height:return {"error":"Particle PNG is unreadable."}
	image.convert(Image.FORMAT_RGBA8)
	return {"data":value,"image":image}

static func collection(world: Dictionary) -> Dictionary:
	var result:={};var bytes:=0;var births:=0
	for row in world.get("effects",[]):
		var loaded:=load_data(row)
		if loaded.has("error"):return loaded
		if row.source_in_seconds>=loaded.data.duration:return {"error":"Particle trim begins beyond the prepared effect duration."}
		bytes+=loaded.image.get_data_size();births+=loaded.data.particles.size()
		if bytes>64*1024*1024 or births>8192:return {"error":"Scene particles exceed64MiB decoded textures or8192 births."}
		result[row.id]=loaded
	return {"effects":result}
