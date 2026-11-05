extends SceneTree
const Clip=preload("res://src/raster_clip.gd")
var checks:=0
var failures:=0
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func _initialize() -> void:
	var folder: String=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder.path_join("images"))
	var image:=Image.create_empty(1920,1080,false,Image.FORMAT_RGBA8);image.fill_rect(Rect2i(40,40,80,80),Color(1,0,0,.5));image.save_png(folder.path_join("temp.png"))
	var hash:=FileAccess.get_sha256(folder.path_join("temp.png"));var path:=folder.path_join("images/"+hash+".png");DirAccess.rename_absolute(folder.path_join("temp.png"),path)
	var file:=FileAccess.open(path,FileAccess.READ);var size:=file.get_length();file.close()
	var source:={"kind":"krita","path":"original.kra","sha256":"a".repeat(64),"width":1920,"height":1080,"fps":24,"range":{"start":3,"end_inclusive":8},"layer_visibility":{}}
	var video:={"width":1920,"height":1080,"fps_num":24,"fps_den":1,"duration_frames":48}
	var packet:={"format":"studio_raster_clip_1","source":source,"width":1920,"height":1080,"fps_num":24,"fps_den":1,"duration_frames":6,"fit":{"width":1920,"height":1080,"x":0,"y":0},"holds":[{"start":0,"duration":6,"sha256":hash,"path":"images/"+hash+".png","bytes":size}]}
	check(not Clip.validate(packet,folder,video,10,1,source.sha256).has("error"),"valid packet fits current frame and resources")
	for change in [{"format":"other"},{"duration_frames":49},{"source":null},{"fit":[]},{"holds":[]},{"holds":[null]},{"fps_den":2}]:
		check(Clip.validate(packet.duplicate(true).merged(change,true),folder,video,0,32,source.sha256).has("error"),"malformed packet refuses before decode")
	for change in [{"path":"../outside.png"},{"sha256":"b".repeat(64)},{"bytes":size+1},{"start":1},{"duration":5}]:
		var bad:=packet.duplicate(true);bad.holds[0].merge(change,true);check(Clip.validate(bad,folder,video,0,32,source.sha256).has("error"),"bad drawing reference or hold refuses")
	check(Clip.validate(packet,folder,video,45,32,source.sha256).has("error"),"scene end refuses without truncation")
	check(Clip.validate(packet,folder,video,0,0,source.sha256).has("error"),"zero remaining cel slots refuses")
	check(Clip.validate(packet,folder,video,0,32,"b".repeat(64)).has("error"),"source identity mismatch refuses")
	# Same encoded size/header, different byte: checksum must catch corruption.
	var bytes:=FileAccess.get_file_as_bytes(path);bytes[bytes.size()-1]^=1;file=FileAccess.open(path,FileAccess.WRITE);file.store_buffer(bytes);file.close()
	check(Clip.validate(packet,folder,video,0,32,source.sha256).has("error"),"changed encoded image refuses before adoption")
	print("RASTER_CLIP_UNIT ",JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
