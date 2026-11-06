extends SceneTree
const Reader=preload("res://src/cel_raster_reader.gd")
const Snapshot=preload("res://src/cel_raster_snapshot.gd")
const Cache=preload("res://src/cel_raster_snapshot_cache.gd")
func fixtures(folder: String) -> Array:
	var rows: Array=[];var noise:=PackedInt32Array()
	if "--existing" in OS.get_cmdline_user_args():
		for i in range(32):
			var path:=folder.path_join("unique_%02d.png"%i);var image:=Image.load_from_file(path);image.convert(Image.FORMAT_RGBA8);rows.append({"path":path,"sha":Snapshot.digest(image.get_data())})
		return rows
	if "--noise" in OS.get_cmdline_user_args():
		noise.resize(1920*1080);var random:=RandomNumberGenerator.new();random.seed=917
		for i in range(noise.size()):noise[i]=random.randi_range(-2147483648,2147483647)
	for i in range(32):
		var image:=Image.create(1920,1080,false,Image.FORMAT_RGBA8)
		image.fill(Color(0,.5,0,0));image.fill_rect(Rect2i(100+i*20,200+i*10,140,80),Color(float(i+1)/32,.7,.2,.5))
		if not noise.is_empty():
			noise[0]=i;image=Image.create_from_data(1920,1080,false,Image.FORMAT_RGBA8,noise.to_byte_array())
		var path:=folder.path_join("unique_%02d.png"%i);image.save_png(path);rows.append({"path":path,"sha":Snapshot.digest(image.get_data())})
	return rows
func one(rows: Array,cold: bool) -> Dictionary:
	var before:=OS.get_static_memory_usage();var started:=Time.get_ticks_usec();var reader:=Reader.new();var sources: Array=[]
	for row in rows:
		var result: Dictionary=reader.read_cold(row.path,1920,1080,row.sha,true) if cold else reader.read(row.path,1920,1080,row.sha,true)
		if result.has("error"):return result
		sources.append(result.raster if cold else result.image)
	var load_ms:=(Time.get_ticks_usec()-started)/1000.;var load_bytes:=OS.get_static_memory_usage()-before
	var stored:=0
	for item in sources:stored+=item.storage_bytes() if cold else item.get_data_size()
	var cache:=Cache.new();started=Time.get_ticks_usec();var exact:=true
	for i in range(rows.size()):
		if cold:exact=exact and verify_row(cache,sources[i],rows[i].sha)
		else:exact=exact and Snapshot.digest(sources[i].get_data())==rows[i].sha
	var seek_ms:=(Time.get_ticks_usec()-started)/1000.;var after_seek:=OS.get_static_memory_usage()-before
	return {"cold":cold,"count":sources.size(),"exact_all_rgba":exact,"capture_or_load_ms":load_ms,"loaded_tracked_bytes":load_bytes,"owned_payload_bytes":stored,"sequential_read_verify_ms":seek_ms,"after_sequential_tracked_bytes":after_seek,"decoded_cache_bytes":cache.retained_bytes,"decoded_cache_ceiling":Cache.DEFAULT_BUDGET,"decodes":cache.decodes}
func verify_row(cache,snapshot,expected: String) -> bool:
	var result: Dictionary=cache.read(snapshot)
	return not result.has("error") and Snapshot.digest(result.image.get_data())==expected
func _initialize() -> void:
	var folder: String=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder);var rows:=fixtures(folder);var runs: Array=[]
	for i in range(3):runs.append({"eager":one(rows,false),"cold":one(rows,true)})
	var ok:=runs.all(func(row):return row.eager.get("exact_all_rgba",false) and row.cold.get("exact_all_rgba",false) and row.cold.decoded_cache_bytes<=Cache.DEFAULT_BUDGET)
	var result:={"ok":ok,"fixture":"noise" if "--noise" in OS.get_cmdline_user_args() else "sparse","runs":runs,"raster":[1920,1080],"count":32,"scope":"Original32distinct fullHD PNGs, sparse with hidden RGB or seeded incompressible noise as specified; three same-process eager-reader versus opt-in cold-reader runs; tracked Godot allocations exclude fixture creation; sequential read verifies every RGBA SHA; no production app/Undo/GPU integration or whole-process RSS claim."}
	FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("CEL_RASTER_SNAPSHOT_BENCHMARK "+JSON.stringify(result));quit(0 if ok else 1)
