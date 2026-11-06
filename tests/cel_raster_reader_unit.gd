extends SceneTree
const Reader=preload("res://src/cel_raster_reader.gd")
const Storage=preload("res://src/storage.gd")
const Drawing=preload("res://src/drawing.gd")
const World=preload("res://src/world_document.gd")
const Graph=preload("res://src/sequence_graph.gd")
const Reference=preload("res://src/reference_sheet_data.gd")
const Timeline=preload("res://src/timeline.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func layer(path: String,digest: String,id: String) -> Dictionary:
	return {"id":id,"name":"Ink "+id,"visible":true,"cels":[{"id":id+"a","start":0,"duration":1,"path":path,"pixel_sha256":digest},{"id":id+"b","start":1,"duration":1,"path":path,"pixel_sha256":digest}]}
func _initialize() -> void:
	var folder: String=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder)
	var original:=Drawing.blank(4,3);original.fill(Color(.2,.7,.8,.5));original.set_pixel(0,0,Color(.9,.4,.2,0));var pixels:=original.get_data();var path:=folder.path_join("original.png");original.save_png(path);var file_sha:=FileAccess.get_sha256(path);var digest:=Storage.image_hash(original);var reader:=Reader.new()
	var first:=reader.read(path,4,3,digest,true);var second:=reader.read(path,4,3,digest,true)
	check(not first.has("error") and not second.has("error") and first.image.get_data()==pixels and second.image.get_data()==pixels,"captured-buffer PNG decode retains exact RGBA including transparent RGB")
	check(reader.reads==2 and reader.png_decodes==1 and reader.hits==1,"repeated PNG bytes decode once while every declared file is read")
	check(not is_same(first.image,second.image),"reused pixels have independent Image resource identities")
	first.image.set_pixel(1,1,Color.RED)
	check(second.image.get_data()==pixels and original.get_data()==pixels,"editing first cel cannot change its peer or original pixels")
	first.image.set_meta("studio_pixels_revision",7);check(not second.image.has_meta("studio_pixels_revision"),"transient edit metadata stays local to each Image")
	var bulk:=reader.read(path,4,3,digest,true);bulk.image.fill_rect(Rect2i(0,0,2,2),Color.BLUE)
	check(second.image.get_data()==pixels,"bulk fill also separates writable backing storage")
	var stroke:=reader.read(path,4,3,digest,true);Drawing.stroke(stroke.image,Vector2(0,1),Vector2(3,1),1,Color.GREEN,false)
	check(second.image.get_data()==pixels,"ordinary drawing stroke preserves independently loaded peers")
	check(reader.read(path,4,3,"0".repeat(64),true).has("error"),"cache hit still rejects incorrect declared pixel checksum")
	for bad in [null,false,1,{}]:check(reader.read(path,4,3,bad,true).has("error"),"malformed checksum refuses without native comparison errors: "+str(bad))
	var alias:=folder.path_join("alias.png");DirAccess.copy_absolute(path,alias);var same:=reader.read(alias,4,3,digest,true)
	check(not same.has("error") and reader.png_decodes==1 and same.image.get_data()==pixels,"identical encoded bytes at another declared path reuse validated decode")
	DirAccess.remove_absolute(alias);check(reader.read(alias,4,3,digest,true).has("error"),"missing duplicate member cannot be concealed by an earlier cached PNG")
	var replacement:=Drawing.blank(4,3);replacement.fill(Color.MAGENTA);replacement.save_png(alias)
	check(reader.read(alias,4,3,digest,true).has("error"),"changed bytes at a declared path cannot borrow old cached pixels")
	var changed:=reader.read(alias,4,3,Storage.image_hash(replacement),true)
	check(not changed.has("error") and changed.image.get_data()==replacement.get_data(),"new encoded identity decodes its own valid pixels")
	check(reader.read(path,5,3,digest,true).has("error"),"cached PNG must match each requested canvas dimension")
	var broken:=folder.path_join("broken.png");FileAccess.open(broken,FileAccess.WRITE).store_buffer(PackedByteArray([137,80,78,71,13,10,26,10]))
	check(reader.read(broken,4,3,digest,true).has("error"),"truncated PNG header refuses before pixel allocation")
	var empty:=folder.path_join("empty.png");FileAccess.open(empty,FileAccess.WRITE).close();check(reader.read(empty,4,3).has("error"),"empty cel refuses cleanly")
	var large:=folder.path_join("large.png");var output:=FileAccess.open(large,FileAccess.WRITE);output.seek(Reader.MAX_BYTES);output.store_8(0);output.close();var reads:=reader.reads
	check(reader.read(large,4,3).has("error") and reader.reads==reads,"oversized cel is refused before its bytes are allocated/read")
	var legacy:=Reader.new();var no_hash:=legacy.read(path,4,3);var checked:=legacy.read(path,4,3,digest,true)
	check(not no_hash.has("error") and not checked.has("error") and legacy.png_decodes==1 and legacy.hits==1,"legacy cel without pixel checksum shares later validated decode safely")
	var jpeg:=folder.path_join("legacy.jpg");original.save_jpg(jpeg);var reference:=Image.load_from_file(jpeg);reference.convert(Image.FORMAT_RGBA8);var jpeg_sha:=Storage.image_hash(reference);var j1:=reader.read(jpeg,4,3,jpeg_sha,true);var j2:=reader.read(jpeg,4,3,jpeg_sha,true)
	check(not j1.has("error") and not j2.has("error") and j1.image.get_data()==reference.get_data() and not is_same(j1.image,j2.image) and reader.fallback_decodes==2,"other legacy image-loader formats preserve fresh independent decode behavior")
	check(FileAccess.get_sha256(path)==file_sha,"all cache lookups/edits preserve original PNG file bytes")
	# Real schema8→7→6 recursion must share one reader but four distinct cel Images.
	var full:=Drawing.blank(1920,1080);full.fill_rect(Rect2i(100,100,80,40),Color(.2,.7,.8,.5));full.save_png(folder.path_join("full.png"));var full_digest:=Storage.image_hash(full)
	var video:={"width":1920,"height":1080,"fps_num":24,"fps_den":1,"duration_frames":252};var keys: Array=[Timeline.key(0,Vector3(0,1,5),Quaternion.IDENTITY,60)];var child_video:=video.duplicate(true);child_video.duration_frames=48
	var child:={"schema_version":4,"video":child_video,"camera_keys":keys,"world":World.empty(),"layers":[layer("full.png",full_digest,"child")],"audio":{},"editor":{"frame":0}}
	var clip:={"id":"clip","asset_id":"child","start":240,"duration":12,"source_in":0,"time_in":0,"key_in":0,"loop":false,"visible":true,"muted":false,"gain_db":0.,"keys":[Graph.key()]}
	var graph:={"format":Graph.FORMAT,"assets":[{"id":"child","name":"Child","scene":child,"clips":[]}],"clips":[clip]}
	var sheet_sha:=FileAccess.get_sha256(folder.path_join("full.png"));DirAccess.make_dir_recursive_absolute(folder.path_join("references"));DirAccess.copy_absolute(folder.path_join("full.png"),folder.path_join("references/"+sheet_sha+".png"))
	var data:={"schema_version":8,"timing_content_schema_version":7,"content_schema_version":6,"reference_sheet":{"format":Reference.FORMAT,"name":"Sheet.png","path":"references/"+sheet_sha+".png","sha256":sheet_sha},"video":video,"camera_keys":keys,"world":World.empty(),"layers":[layer("full.png",full_digest,"root")],"sequence_graph":graph,"audio":{},"editor":{"frame":0}}
	var shared:=Reader.new();var decoded:=Storage.decode_project(data.duplicate(true),folder,false,shared)
	check(not decoded.has("error"),"nested timing/reference/sequence project decodes with existing schemas")
	if decoded.has("error"):print(decoded);print("CEL_RASTER_READER_UNIT ",JSON.stringify({"checks":checks,"failures":failures}));quit(1);return
	check(shared.png_decodes==1 and shared.hits==3 and shared.reads==4,"root/child cel buffers share one project-scoped validated PNG decode")
	var root_images: Array=decoded.layers[0].cels;var child_images: Array=decoded.sequence_graph.assets[0].scene.layers[0].cels;var ids:={}
	for cel in root_images+child_images:ids[cel.image.get_instance_id()]=true
	check(ids.size()==4,"four cels across parent/child keep four editable resource identities")
	child_images[0].image.set_pixel(100,100,Color.RED)
	check(Storage.image_hash(root_images[0].image)==full_digest and Storage.image_hash(root_images[1].image)==full_digest and Storage.image_hash(child_images[1].image)==full_digest,"editing child after shared decode preserves parent and sibling cel pixels")
	var weak: WeakRef=weakref(shared);shared=null;check(weak.get_ref()==null and Storage.image_hash(root_images[0].image)==full_digest,"decode context can die while independent cel Images stay valid")
	var invalid:=data.duplicate(true);invalid.layers[0].cels[1].path="../full.png"
	check(Storage.decode_project(invalid,folder).has("error"),"cached content never bypasses normal relative-path validation")
	invalid=data.duplicate(true);invalid.layers[0].cels[1].pixel_sha256="0".repeat(64)
	check(Storage.decode_project(invalid,folder).has("error"),"recursive storage still refuses bad checksum on a repeated cel")
	var again:=Storage.decode_project(data.duplicate(true),folder)
	check(not again.has("error") and not is_same(again.layers[0].cels[0].image,root_images[0].image) and Storage.image_hash(again.layers[0].cels[0].image)==full_digest,"later project decode starts independent source ownership without stale edited pixels")
	print("CEL_RASTER_READER_UNIT ",JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
