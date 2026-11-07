extends SceneTree
const Reader=preload("res://src/cel_raster_reader.gd")
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
const World=preload("res://src/world_document.gd")
const Timeline=preload("res://src/timeline.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func layer(id: String,digest: String) -> Dictionary:
	return {"id":id,"name":id,"visible":true,"cels":[{"id":id+"a","start":0,"duration":1,"path":"full.png","pixel_sha256":digest},{"id":id+"b","start":1,"duration":1,"path":"full.png","pixel_sha256":digest}]}
func _initialize() -> void:
	var folder: String=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder);var source:=Drawing.blank(128,96);source.fill(Color(.2,.7,.8,.5));source.set_pixel(0,0,Color(.9,.4,.2,0));var raw:=source.get_data();var digest:=Reader.digest_bytes(raw);var path:=folder.path_join("source.png");source.save_png(path);var file_sha:=FileAccess.get_sha256(path);var reader:=Reader.new()
	var first:=reader.read_adaptive(path,128,96,digest,true);var second:=reader.read_adaptive(path,128,96,digest,true)
	check(first.has("raster_owner") and second.has("raster_owner") and Drawing.image(first).get_data()==raw and Drawing.image(second).get_data()==raw,"compressible adaptive reads retain cold owners with exact RGBA")
	check(reader.reads==2 and reader.png_decodes==1 and reader.hits==1 and reader.entries.is_empty(),"adaptive repeated PNG captures once while every declared file is checked")
	check(not is_same(first.raster_owner,second.raster_owner) and is_same(first.raster_owner._cold,second.raster_owner._cold),"independent cel owners share one immutable captured pixel backing")
	var staged: Dictionary=reader.adaptive_entries.values()[0];check(staged.has("raster") and not staged.has("image") and staged.raster.storage_bytes()<raw.size()/2,"adaptive decode context retains compressed backing instead of eager source Image")
	var edit:=Drawing.edit_image(first);Drawing.stroke(edit.image,Vector2(3,3),Vector2(15,8),2,Color.RED,false)
	check(Drawing.image(first).get_data()!=raw and Drawing.image(second).get_data()==raw and source.get_data()==raw,"pinning/painting one adaptive cel preserves shared cold peer and original")
	check(reader.read_adaptive(path,128,96,"0".repeat(64),true).has("error"),"adaptive cache hit still refuses wrong declared checksum")
	for bad in [null,false,1,{}]:check(reader.read_adaptive(path,128,96,bad,true).has("error"),"adaptive malformed checksum refuses: "+str(bad))
	check(reader.read_adaptive(path,129,96,digest,true).has("error"),"cached source must match every declared canvas")
	var alias:=folder.path_join("alias.png");DirAccess.copy_absolute(path,alias);var alias_read:=reader.read_adaptive(alias,128,96,digest,true)
	check(alias_read.has("raster_owner") and reader.png_decodes==1 and Drawing.image(alias_read).get_data()==raw,"identical encoded aliases share cold capture after independent file read")
	DirAccess.remove_absolute(alias);check(reader.read_adaptive(alias,128,96,digest,true).has("error"),"missing alias cannot be concealed by cached cold pixels")
	var changed:=Drawing.blank(128,96);changed.fill(Color.MAGENTA);changed.save_png(alias)
	check(reader.read_adaptive(alias,128,96,digest,true).has("error"),"changed alias bytes cannot borrow old cached pixels")
	var changed_read:=reader.read_adaptive(alias,128,96,Storage.image_hash(changed),true);check(Drawing.image(changed_read).get_data()==changed.get_data(),"changed valid identity captures its own exact cold pixels")
	var noisy:=PackedByteArray();noisy.resize(64*64*4);var random:=RandomNumberGenerator.new();random.seed=917
	for i in range(noisy.size()):noisy[i]=random.randi_range(0,255)
	var noise:=Image.create_from_data(64,64,false,Image.FORMAT_RGBA8,noisy);var noise_path:=folder.path_join("noise.png");noise.save_png(noise_path);var noise_reader:=Reader.new();var n1:=noise_reader.read_adaptive(noise_path,64,64,Reader.digest_bytes(noisy),true);var n2:=noise_reader.read_adaptive(noise_path,64,64,Reader.digest_bytes(noisy),true)
	check(n1.has("raster_owner") and n2.has("raster_owner") and not is_same(n1.raster_owner,n2.raster_owner) and not is_same(Drawing.image(n1),Drawing.image(n2)) and Drawing.image(n1).get_data()==noisy and Drawing.image(n2).get_data()==noisy,"incompressible adaptive fallback retains independent exact owned Images")
	var budget:=preload("res://src/cel_raster_budget.gd").new(0);budget.install(noise_reader.adaptive_cache)
	check(budget.sample().owners==2 and budget.sample().hot_bytes==noisy.size()*2,"incompressible adaptive owners report conservative decoded bytes instead of zero")
	noise_reader.adaptive_entries.clear()
	var pressure:=budget.step()
	check(not pressure.released and pressure.reason=="incompressible" and pressure.after.hot_bytes==noisy.size()*2,"incompressible pressure reports unreleased bytes without discarding pixels")
	var noise_edit:=Drawing.edit_image(n1);noise_edit.image.fill(Color.GREEN);Drawing.touch(noise_edit.image);check(Drawing.image(n2).get_data()==noisy and noise_reader.adaptive_cache.decodes==0 and noise_reader.png_decodes==1,"noise fallback keeps COW independence without cold cache/materialization overhead")
	var jpeg:=folder.path_join("legacy.jpg");source.save_jpg(jpeg);var reference:=Image.load_from_file(jpeg);reference.convert(Image.FORMAT_RGBA8);var j:=reader.read_adaptive(jpeg,128,96,Storage.image_hash(reference),true)
	check(not j.has("error") and Drawing.image(j).get_data()==reference.get_data() and reader.fallback_decodes==1,"legacy non-PNG image loader keeps exact validated adaptive compatibility")
	check(not reader.read_adaptive(path,128,96,digest,true,file_sha).has("error"),"prepared input validates the exact captured encoded-file identity")
	check(reader.read_adaptive(path,128,96,digest,true,"0".repeat(64)).has("error"),"prepared encoded checksum mismatch refuses even with cached matching decoded pixels")
	check(FileAccess.get_sha256(path)==file_sha,"all adaptive reads/edits preserve original PNG file")
	staged.raster._payload[0]=staged.raster._payload[0]^1
	check(reader.read_adaptive(path,128,96,digest,true).has("error"),"corrupt captured backing refuses even when original alias file remains valid")
	check(not reader.read(path,128,96,digest,true).has("error"),"eager API remains independent of adaptive context ownership")
	var full:=Drawing.blank(1920,1080);full.fill_rect(Rect2i(100,100,200,100),Color(.2,.7,.8,.5));full.save_png(folder.path_join("full.png"));var full_sha:=Storage.image_hash(full);var video:={"width":1920,"height":1080,"fps_num":24,"fps_den":1,"duration_frames":48};var keys: Array=[Timeline.key(0,Vector3(0,1,5),Quaternion.IDENTITY,60)]
	var child:={"schema_version":4,"video":video,"camera_keys":keys,"world":World.empty(),"layers":[layer("child",full_sha)],"audio":{},"editor":{"frame":0}}
	var graph:={"format":"studio_sequences_1","assets":[{"id":"child","name":"Child","scene":child,"clips":[]}],"clips":[]}
	var project:={"schema_version":6,"video":video,"camera_keys":keys,"world":World.empty(),"layers":[layer("root",full_sha)],"audio":{},"editor":{"frame":0},"sequence_graph":graph}
	var context:=Reader.new();context.cold_cels=true;var decoded:=Storage.decode_project(project.duplicate(true),folder,false,context)
	check(not decoded.has("error") and decoded.layers[0].cels[0].has("raster_owner") and decoded.sequence_graph.assets[0].scene.layers[0].cels[0].has("raster_owner"),"nested Storage decode installs cold owners only through explicit adaptive context")
	check(context.png_decodes==1 and context.hits==3 and context.adaptive_entries.size()==1,"root/child adaptive decode shares one captured backing across four records")
	var children: Array=decoded.sequence_graph.assets[0].scene.layers[0].cels;var child_edit:=Drawing.edit_image(children[0]);child_edit.image.fill(Color.RED);Drawing.touch(child_edit.image)
	check(Storage.image_hash(Drawing.image(decoded.layers[0].cels[0]))==full_sha and Storage.image_hash(Drawing.image(children[1]))==full_sha,"editing nested cold owner preserves parent and sibling pixels")
	FileAccess.open(folder.path_join("project.json"),FileAccess.WRITE).store_string(JSON.stringify(project));var cold_open:=Storage.load_project(folder,"project.json",true);var normal_open:=Storage.load_project(folder)
	check(not cold_open.has("error") and cold_open.layers[0].cels[0].has("raster_owner") and normal_open.layers[0].cels[0].has("image"),"explicit cold directory loading and unchanged default eager API coexist")
	var invalid:=project.duplicate(true);invalid.layers[0].cels[1].path="../full.png";check(Storage.decode_project(invalid,folder,false,context).has("error"),"adaptive context never bypasses normal unsafe-path validation")
	invalid=project.duplicate(true);invalid.layers[0].cels[1].pixel_sha256="0".repeat(64);check(Storage.decode_project(invalid,folder,false,context).has("error"),"late nested/checksum failure refuses the project despite an earlier cached record")
	print("CEL_RASTER_ADAPTIVE_UNIT "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
