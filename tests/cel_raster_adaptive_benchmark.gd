extends "res://tests/cel_raster_snapshot_benchmark.gd"
const Drawing=preload("res://src/drawing.gd")
func one(rows: Array,cold: bool) -> Dictionary:
	var before:=OS.get_static_memory_usage();var started:=Time.get_ticks_usec();var reader:=Reader.new();var records: Array=[]
	for row in rows:
		var result: Dictionary=reader.read_adaptive(row.path,1920,1080,row.sha,true) if cold else reader.read(row.path,1920,1080,row.sha,true)
		if result.has("error"):return result
		records.append(result)
	var load_ms:=(Time.get_ticks_usec()-started)/1000.;var load_bytes:=OS.get_static_memory_usage()-before;var payload:=0;var cold_records:=0
	for entry in (reader.adaptive_entries if cold else reader.entries).values():payload+=entry.raster.storage_bytes() if entry.has("raster") else entry.image.get_data_size()
	for record in records:
		if record.has("raster_owner"):cold_records+=1
	started=Time.get_ticks_usec();var exact:=true
	for i in range(rows.size()):exact=exact and verify_record(records[i],rows[i].sha)
	return {"adaptive":cold,"count":records.size(),"cold_owner_records":cold_records,"png_decodes":reader.png_decodes,"cache_hits":reader.hits,"exact_all_rgba":exact,"load_ms":load_ms,"loaded_tracked_bytes":load_bytes,"unique_payload_bytes":payload,"sequential_read_verify_ms":(Time.get_ticks_usec()-started)/1000.,"after_sequential_tracked_bytes":OS.get_static_memory_usage()-before,"decoded_cache_bytes":reader.adaptive_cache.retained_bytes}
func verify_record(record: Dictionary,expected: String) -> bool:
	var pixels:=Drawing.read_image(record)
	return not pixels.has("error") and Reader.digest_bytes(pixels.image.get_data())==expected
func _initialize() -> void:
	var folder: String=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder);var rows:=fixtures(folder)
	if "--repeat" in OS.get_cmdline_user_args():
		for i in range(rows.size()):rows[i]=rows[0]
	var runs: Array=[]
	for i in range(3):runs.append({"eager":one(rows,false),"adaptive":one(rows,true)})
	var ok:=runs.all(func(row):return row.eager.get("exact_all_rgba",false) and row.adaptive.get("exact_all_rgba",false) and row.adaptive.decoded_cache_bytes<=Cache.DEFAULT_BUDGET)
	var result:={"ok":ok,"fixture":"repeated" if "--repeat" in OS.get_cmdline_user_args() else "noise" if "--noise" in OS.get_cmdline_user_args() else "sparse","runs":runs,"raster":[1920,1080],"count":32,"scope":"Three same-process current eager versus opt-in adaptive reader runs; sparse/noise32distinct PNGs or32records of one repeated PNG. Captured PNG validation remains eager; tracked CPU allocations exclude fixture creation and are not RSS/peak/GPU. No app adoption/performance acceptance claim."}
	FileAccess.open(folder.path_join("adaptive-result"+("-repeat" if "--repeat" in OS.get_cmdline_user_args() else "")+".json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("CEL_RASTER_ADAPTIVE_BENCHMARK "+JSON.stringify(result));quit(0 if ok else 1)
