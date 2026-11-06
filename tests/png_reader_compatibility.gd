extends SceneTree
const Reader=preload("res://src/cel_raster_reader.gd")
func _initialize() -> void:
	var folder:=OS.get_cmdline_user_args()[0];var reader:=Reader.new();var cases:=[];var failures:=0;var golden: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
	for name in DirAccess.get_files_at(folder):
		if not name.ends_with(".png"):continue
		var path:=folder.path_join(name);var before:=FileAccess.get_sha256(path);var original:=Image.load_from_file(path)
		if original==null:failures+=1;continue
		original.convert(Image.FORMAT_RGBA8);var digest:=Reader.digest_bytes(original.get_data());var first:=reader.read(path,original.get_width(),original.get_height(),digest,true);var second:=reader.read(path,original.get_width(),original.get_height(),digest,true)
		var expected: Dictionary=golden[name]
		var ok: bool=original.get_width()==expected.width and original.get_height()==expected.height and digest==expected.pixel_sha256 and before==expected.source_sha256 and not first.has("error") and not second.has("error") and first.image.get_data()==original.get_data() and second.image.get_data()==original.get_data() and not is_same(first.image,second.image) and FileAccess.get_sha256(path)==before
		if not ok:failures+=1
		cases.append({"name":name,"ok":ok,"pixel_sha256":digest,"source_sha256":before})
	if cases.size()!=16 or reader.png_decodes!=16 or reader.hits!=16:failures+=1
	print("PNG_READER_COMPATIBILITY ",JSON.stringify({"cases":cases,"failures":failures,"png_decodes":reader.png_decodes,"cache_hits":reader.hits}));quit(0 if failures==0 else 1)
