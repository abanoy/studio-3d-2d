extends SceneTree
# Optional read-only compatibility probe, not a product importer or shared document.
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
var checks:=0
var failures:=0

func check(ok: bool,text: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+text)
	if not ok:failures+=1

func digest(bytes: PackedByteArray) -> String:
	var hash:=HashingContext.new();hash.start(HashingContext.HASH_SHA256);hash.update(bytes)
	return hash.finish().hex_encode()

func _initialize() -> void:
	var source:="C:/a/Programming/cloudflare/prototypes/artist-animation-assistant/experiments/EXP-0059-local-cel-exchange-fixture/fixture/exchange.json"
	if not FileAccess.file_exists(source):print("SKIP optional authored sibling cel fixture absent");quit();return
	var input:=FileAccess.open(source,FileAccess.READ)
	if input.get_length()>1024*1024:push_error("Exchange fixture metadata too large");quit(1);return
	var source_sha:=FileAccess.get_sha256(source);var packet=JSON.parse_string(input.get_as_text());input.close()
	if not packet is Dictionary:push_error("Invalid exchange fixture JSON");quit(1);return
	check(packet.get("format")=="artist-cel-exchange" and packet.get("version")==1,"authored exchange declares explicit format/version")
	check(packet.canvas.width==1920 and packet.canvas.height==1080 and packet.canvas.channel_order=="RGBA" and packet.canvas.bit_depth==8 and packet.canvas.alpha_mode=="straight" and packet.canvas.color_profile=="sRGB","fixture canvas/alpha/profile fit the current receiver profile")
	check(packet.clock.fps.numerator==24 and packet.clock.fps.denominator==1 and packet.clock.duration_frames==12 and packet.clock.frame_origin==0 and packet.clock.interval=="start-inclusive-end-exclusive","clock uses explicit zero-based half-open exposures and rational FPS")
	if failures>0:quit(1);return
	var images:={};var hashes:={};var composite_hashes:={};var alphas:={};var differences:={}
	for cel in packet.cels:
		if not Storage.safe_relative(cel.path) or not str(cel.path).begins_with("cels/") or images.has(cel.id):push_error("Unsafe or duplicate fixture asset");quit(1);return
		var path: String=source.get_base_dir().path_join(cel.path);var file:=FileAccess.open(path,FileAccess.READ)
		check(file!=null and file.get_length()==cel.bytes and FileAccess.get_sha256(path)==cel.sha256,"declared PNG byte length/hash matches: "+cel.id)
		if file:file.close()
		var image:=Image.load_from_file(path)
		check(image!=null and image.get_size()==Vector2i(1920,1080) and image.get_format()==Image.FORMAT_RGBA8,"native PNG decoder keeps RGBA8 dimensions: "+cel.id)
		if image==null:quit(1);return
		var pixels:=image.get_data();var hash:=digest(pixels)
		check(hash==cel.rgba_sha256,"decoded native RGBA hash matches producer: "+cel.id)
		var alpha:={}
		for i in range(3,pixels.size(),4):alpha[int(pixels[i])]=true
		check(alpha.has(0) and (alpha.size()==1 if cel.id=="cel-blank" else alpha.has(96) and alpha.has(255) and alpha.size()==3),"explicit blank/fractional/opaque alpha survives: "+cel.id)
		images[cel.id]=image;hashes[cel.id]=hash;alphas[cel.id]=alpha.keys()
	var layer:={"id":"probe-layer","name":"Read-only cel probe","visible":true,"cels":[]}
	for exposure in packet.layers[0].exposures:
		layer.cels.append({"id":"exposure-%d" % layer.cels.size(),"exchange_cel_id":exposure.cel_id,"start":int(exposure.start),"duration":int(exposure.length),"image":images[exposure.cel_id]})
	var expected:=["cel-a","cel-a","cel-a","cel-blank","cel-blank","cel-b","cel-b","cel-b","cel-b","cel-a","cel-a","cel-a"]
	for frame in range(12):
		var cel:=Drawing.cel_at(layer,frame)
		check(not cel.is_empty() and cel.exchange_cel_id==expected[frame],"Studio cel lookup matches explicit exposure at zero-based frame%d" % frame)
	check(Drawing.cel_at(layer,-1).is_empty() and Drawing.cel_at(layer,12).is_empty(),"shot boundaries are absent, not implicit holds or filename-derived frames")
	for frame in [0,3,5]:
		var image:=Drawing.composite([layer],frame,1920,1080);var id: String=expected[frame];composite_hashes[id]=digest(image.get_data())
		var a: PackedByteArray=images[id].get_data();var b: PackedByteArray=image.get_data();var alpha_mismatch:=0;var visible_rgb:=0;var hidden_rgb:=0;var partial_sample:=[]
		for i in range(0,a.size(),4):
			if a[i+3]!=b[i+3]:alpha_mismatch+=1
			for channel in range(3):
				if a[i+channel]!=b[i+channel]:
					if a[i+3]==0:hidden_rgb+=1
					else:visible_rgb+=1
			if a[i+3]==96 and partial_sample.is_empty():partial_sample=[Array(a.slice(i,i+4)),Array(b.slice(i,i+4))]
		differences[id]={"alpha":alpha_mismatch,"visible_rgb":visible_rgb,"hidden_rgb":hidden_rgb,"partial_sample":partial_sample}
		check(alpha_mismatch==0 and visible_rgb==0,"composite retains alpha and all visible RGB exactly: "+id)
		for background in [Color.BLACK,Color.WHITE]:
			var expected_background:=Image.create(1920,1080,false,Image.FORMAT_RGBA8);expected_background.fill(background)
			var actual_background:=expected_background.duplicate() as Image
			expected_background.blend_rect(images[id],Rect2i(0,0,1920,1080),Vector2i.ZERO)
			actual_background.blend_rect(image,Rect2i(0,0,1920,1080),Vector2i.ZERO)
			check(expected_background.get_data()==actual_background.get_data(),"composite agrees over known "+("black" if background==Color.BLACK else "white")+" background: "+id)
	var unchanged:=FileAccess.get_sha256(source)==source_sha
	for cel in packet.cels:unchanged=unchanged and FileAccess.get_sha256(source.get_base_dir().path_join(cel.path))==cel.sha256
	check(unchanged,"probe leaves manifest and every source PNG unchanged")
	var result:={"checks":checks,"failures":failures,"source":source,"source_sha256":source_sha,"rgba_hashes":hashes,"composite_hashes":composite_hashes,"alphas":alphas,"differences":differences,"product_importer":false,"has_roundtrip_tested":false}
	var output:=ProjectSettings.globalize_path("res://output/cel-exchange-probe.json");var file:=FileAccess.open(output,FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close()
	print("CEL_EXCHANGE_PROBE "+JSON.stringify(result));quit(0 if failures==0 else 1)
