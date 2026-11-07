extends RefCounted
const RasterReader=preload("res://src/cel_raster_reader.gd")
const Drawing = preload("res://src/drawing.gd")
const AudioTrack = preload("res://src/audio_track.gd")
const Model = preload("res://src/model.gd")
const WorldDocument = preload("res://src/world_document.gd")
const Lighting=preload("res://src/lighting.gd")
const Timeline=preload("res://src/timeline.gd")
const Journal=preload("res://src/recovery_journal.gd")
const Sequences=preload("res://src/sequence_graph.gd")
const ReferenceSheet=preload("res://src/reference_sheet_data.gd")
const Extended=preload("res://src/extended_timing.gd")

static func safe_relative(path: String) -> bool:
	if path.is_empty() or path.is_absolute_path() or path.contains(":") or path.contains("\\"):
		return false
	for part in path.split("/"):
		if part in ["..", ".", ""]:
			return false
	return true

static func image_hash(image: Image) -> String:
	var hash := HashingContext.new()
	hash.start(HashingContext.HASH_SHA256)
	hash.update(image.get_data())
	return hash.finish().hex_encode()

static func write_path_error(folder: String, relative: String) -> String:
	if not safe_relative(relative):return "Unsafe project write path. Previous save preserved."
	var filesystem:=DirAccess.open(ProjectSettings.globalize_path("res://"))
	if filesystem==null:return "Cannot check project write path. Previous save preserved."
	var path:=ProjectSettings.globalize_path(folder)
	for part in relative.split("/"):
		path=path.path_join(part)
		if filesystem.is_link(path):return "Project write path is a symbolic link: "+relative+". Previous save preserved."
	return ""

static func fresh_temporary(target: String,suffix: String) -> String:
	# Never truncate an existing temporary inode (including a hard-linked source).
	var temporary:=target+"."+str(ResourceUID.create_id())+suffix
	var filesystem:=DirAccess.open(target.get_base_dir())
	if filesystem==null or filesystem.is_link(temporary) or FileAccess.file_exists(temporary) or DirAccess.dir_exists_absolute(temporary):return ""
	return temporary

static func managed_copy(source: String, target: String, expected: String) -> String:
	var path_error:=write_path_error(target.get_base_dir(),target.get_file())
	if not path_error.is_empty():return path_error
	if FileAccess.file_exists(target) and FileAccess.get_sha256(target) == expected: return ""
	var temp:=fresh_temporary(target,".import.tmp")
	if temp.is_empty():return "Cannot create a fresh managed asset temporary. Previous save preserved."
	if DirAccess.copy_absolute(source, temp) != OK or FileAccess.get_sha256(temp) != expected:
		return "Cannot copy/verify managed asset; previous manifest preserved."
	if DirAccess.rename_absolute(temp, target) != OK: return "Cannot commit managed asset; previous manifest preserved."
	return ""

static func readable_manifest(path: String) -> bool:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null or file.get_length() > 1024 * 1024: return false
	var parser := JSON.new()
	if parser.parse(file.get_as_text()) != OK or not parser.data is Dictionary: return false
	var data: Dictionary=parser.data
	if data.get("video") is Dictionary and not preload("res://src/output_size.gd").project_error(data.video).is_empty():return false
	var extended:=false
	if data.get("schema_version")==8:
		var timing:=Extended.unwrap(data)
		if timing.has("error"):return false
		data=timing.base;extended=true
	elif data.has("timing_content_schema_version"):return false
	if not extended and Extended.required(data):return false
	if data.get("schema_version")==7:
		var unwrapped:=ReferenceSheet.unwrap(data)
		if unwrapped.has("error"):return false
		data=unwrapped.base
	elif data.has("reference_sheet") or data.has("content_schema_version"):return false
	if not integer(data.get("schema_version"),1,6):return false
	if data.schema_version==6:
		if not Sequences.error(data.get("sequence_graph"),data).is_empty():return false
	elif data.has("sequence_graph"):return false
	elif data.get("editor",{}) is Dictionary and data.get("editor",{}).has("sequence_editor"):return false
	if data.get("video") is Dictionary and not Lighting.validate(data.video).is_empty():return false
	if not preload("res://src/color_palette.gd").error(data.get("palette",[])).is_empty():return false
	if data.get("video") is Dictionary and data.video.has("visibility_fade_ms") and not integer(data.video.visibility_fade_ms,0,10000):return false
	if not data.get("camera_keys") is Array or not Timeline.range_error(data.camera_keys).is_empty():return false
	if not data.get("layers") is Array or not Drawing.opacity_error(data.layers).is_empty():return false
	if not preload("res://src/drawing_origin.gd").layers_error(data.layers).is_empty():return false
	if not data.get("audio",{}) is Dictionary or not AudioTrack.layout_error(data.get("audio",{})).is_empty():return false
	if data.schema_version>=4:
		var video=data.get("video")
		if not video is Dictionary or not Extended.video_error(video).is_empty() or not extended and video.duration_frames>240:return false
		if not WorldDocument.validate(data.get("world"),int(video.duration_frames),true).is_empty():return false
		if data.schema_version!=6 and (data.schema_version==5)!=(data.world.format==WorldDocument.EFFECT_FORMAT):return false
	return integer(data.get("schema_version"), 1, 6) and data.get("layers") is Array and data.get("camera_keys") is Array

static func save_project(folder: String, video: Dictionary, keys: Array, layers: Array, source: String, frame: int, audio: Dictionary = {}, recovery: Dictionary = {}, model: Dictionary = {}, content_addressed := false, world: Dictionary = {}, editor_extra: Dictionary = {},palette: Array=[],sequence_graph: Dictionary={},_manifest_out: Variant=null,reference_sheet: Dictionary={}) -> String:
	var output_error:=preload("res://src/output_size.gd").project_error(video)
	if not output_error.is_empty():return output_error+" Previous save preserved."
	var video_error:=Extended.video_error(video)
	if not video_error.is_empty():return video_error+" Previous save preserved."
	if not reference_sheet.is_empty():
		var reference_error:=ReferenceSheet.error(reference_sheet)
		if not reference_error.is_empty():return reference_error
		var checked_reference:=ReferenceSheet.read_image(reference_sheet.source)
		if checked_reference.has("error"):return checked_reference.error
		if checked_reference.sha256!=reference_sheet.sha256:return "Reference sheet source changed. Previous save preserved."
	if not sequence_graph.is_empty():
		if world.is_empty():return "Editable sequences require a world project."
		var sequence_error:=Sequences.error(sequence_graph,{"video":video,"layers":layers,"audio":audio,"world":world})
		if not sequence_error.is_empty():return sequence_error
	var palette_error:=preload("res://src/color_palette.gd").error(palette)
	if not palette_error.is_empty():return palette_error+" Previous save preserved."
	var rate_error:=preload("res://src/video_timing.gd").error(video.get("fps_num"),video.get("fps_den"))
	if not rate_error.is_empty():return rate_error+" Previous save preserved."
	var audio_layout := AudioTrack.layout_error(audio)
	if not audio_layout.is_empty(): return audio_layout
	if AudioTrack.memory(audio) > AudioTrack.MAX_PCM: return "Audio sources exceed64MiB. Previous save preserved."
	var opacity_error:=Drawing.opacity_error(layers)
	if not opacity_error.is_empty():return opacity_error+" Previous save preserved."
	var origin_error:=preload("res://src/drawing_origin.gd").layers_error(layers)
	if not origin_error.is_empty():return origin_error+" Previous save preserved."
	if not editor_extra.is_empty() and (editor_extra.size()!=1 or not (editor_extra.get("lesson_ui") is Dictionary or editor_extra.get("sequence_editor") is Dictionary) or JSON.stringify(editor_extra,"",true,true).to_utf8_buffer().size()>16384):return "Invalid lesson editor snapshot. Previous save preserved."
	if editor_extra.has("sequence_editor"):
		var why:=Sequences.context_error(editor_extra.sequence_editor,sequence_graph)
		if not why.is_empty():return why
	var camera_error:=Timeline.range_error(keys)
	if not camera_error.is_empty():return camera_error+" Previous save preserved."
	var lighting_error:=Lighting.validate(video)
	if not lighting_error.is_empty():return lighting_error+" Previous save preserved."
	if video.has("visibility_fade_ms") and not integer(video.visibility_fade_ms,0,10000):return "Visibility fade must be0–10000 milliseconds. Previous save preserved."
	if not world.is_empty():
		var world_error := WorldDocument.validate(world,int(video.duration_frames))
		if not world_error.is_empty(): return world_error
		var checked := {}
		for row in WorldDocument.assets(world):
			if checked.has(row.source):
				if checked[row.source]!=row.sha256: return "Conflicting world source identity."
				continue
			var input := FileAccess.open(row.source,FileAccess.READ)
			if input==null or input.get_length()>row.limit or FileAccess.get_sha256(row.source)!=row.sha256: return "World asset changed, disappeared or exceeds its size limit. Previous save preserved."
			checked[row.source]=row.sha256
		var particles:=WorldDocument.Particles.collection(world)
		if particles.has("error"):return particles.error
	elif not FileAccess.file_exists(source):
		return "Scene source is missing; save aborted."
	var revision := "%d_%d" % [Time.get_unix_time_from_system() * 1000, Time.get_ticks_usec()]
	var cel_dir := "cels/" + revision
	if not recovery.is_empty() or content_addressed: cel_dir = "cels/content"
	for path in ["assets",cel_dir,"project.json","project.backup.json","project.json.tmp"]+(["references"] if not reference_sheet.is_empty() else []):
		var path_error:=write_path_error(folder,path)
		if not path_error.is_empty():return path_error
	if DirAccess.dir_exists_absolute(folder.path_join("project.json.tmp")):return "Cannot write manifest: an existing temporary directory blocks saving. Previous save preserved."
	for sub in ["assets", cel_dir]:
		var error := DirAccess.make_dir_recursive_absolute(folder.path_join(sub))
		if error != OK:
			return "Cannot create project directory: " + error_string(error)
	var hash := ""
	var asset := ""
	if world.is_empty():
		hash=FileAccess.get_sha256(source);asset="assets/"+hash+".glb"
		var scene_error := managed_copy(source,folder.path_join(asset),hash)
		if not scene_error.is_empty(): return scene_error
	else:
		var copied := {}
		for row in WorldDocument.assets(world):
			if copied.has(row.path): continue
			var error := managed_copy(row.source,folder.path_join(row.path),row.sha256)
			if not error.is_empty(): return error
			copied[row.path]=true
	var png_verifier=preload("res://src/cel_png_verifier.gd").new()
	var tracks := []
	for layer_index in range(layers.size()):
		var layer=layers[layer_index]
		var track := {"id": layer.id, "name": layer.name, "visible": layer.visible, "cels": []}
		if layer.has("opacity"):track.opacity=layer.opacity
		if layer.has("origin"):track.origin=layer.origin.duplicate(true)
		for cel_index in range(layer.cels.size()):
			var cel=layer.cels[cel_index]
			var source_pixels:=Drawing.read_image(cel)
			if source_pixels.has("error"):return source_pixels.error+" Previous project manifest preserved."
			var image: Image=source_pixels.image
			if image.get_size()!=Vector2i(int(video.width),int(video.height)) or image.get_format()!=Image.FORMAT_RGBA8:return "Cel pixels differ from the supported canvas. Previous project manifest preserved."
			# IDs are opaque document data, never filesystem path components.
			# Ordinals also keep equal IDs on separate layers from overwriting ink.
			var path := cel_dir.path_join("layer_%d_cel_%d.png" % [layer_index,cel_index])
			var pixels := ""
			if not recovery.is_empty() or content_addressed:
				pixels = image_hash(image)
				path = cel_dir.path_join(pixels + ".png")
			var path_error:=write_path_error(folder,path)
			if not path_error.is_empty():return path_error
			var reuse := false
			if not pixels.is_empty() and FileAccess.file_exists(folder.path_join(path)):
				reuse=png_verifier.matches(folder.path_join(path),int(video.width),int(video.height),pixels)
			if not reuse:
				var temporary:=fresh_temporary(folder.path_join(path),".tmp.png")
				if temporary.is_empty():return "Cannot create a fresh drawing temporary. Previous save preserved."
				var expected_pixels:=pixels if not pixels.is_empty() else image_hash(image)
				if image.save_png(temporary) != OK or not png_verifier.matches(temporary,int(video.width),int(video.height),expected_pixels) or DirAccess.rename_absolute(temporary, folder.path_join(path)) != OK:
					return "Cannot commit cel PNG; previous project manifest preserved."
			var entry := {"id": cel.id, "start": cel.start, "duration": cel.duration, "path": path}
			if not pixels.is_empty(): entry["pixel_sha256"] = pixels
			track.cels.append(entry)
		tracks.append(track)
	var saved_clips := []
	for clip in AudioTrack.clips(audio):
		var timing_error := AudioTrack.clip_error(clip,video)
		if not timing_error.is_empty(): return timing_error
		if FileAccess.get_sha256(clip.source.path) != clip.source.sha256:
			return "Audio source changed or disappeared. Re-import it before saving; previous manifest preserved."
		var audio_asset: String = "assets/" + clip.source.sha256 + ".wav"
		var audio_error := managed_copy(clip.source.path, folder.path_join(audio_asset), clip.source.sha256)
		if not audio_error.is_empty(): return audio_error
		saved_clips.append({"id": clip.id, "path": audio_asset, "sha256": clip.source.sha256, "source_name": clip.source.name, "start_frame": clip.start_frame, "source_in_sample": clip.source_in_sample, "gain_db": clip.gain_db, "muted": clip.muted})
		for field in AudioTrack.EXTRA_FIELDS:
			if clip.has(field):saved_clips[-1][field]=clip[field]
	var saved_audio := AudioTrack.document(saved_clips)
	var saved_model := model.duplicate(true)
	if world.is_empty() and not model.is_empty():
		var model_error := Model.validate(model, video.duration_frames)
		if not model_error.is_empty(): return model_error
		if not model.get("source") is String or FileAccess.get_sha256(model.source) != model.sha256: return "Model source changed or disappeared. Re-import before saving."
		var model_asset: String = "assets/" + model.sha256 + ".glb"
		model_error = managed_copy(model.source, folder.path_join(model_asset), model.sha256)
		if not model_error.is_empty(): return model_error
		saved_model.erase("source")
		saved_model["path"] = model_asset
	var manifest := {"schema_version": 3, "model": saved_model, "video": video, "camera_keys": keys, "layers": tracks, "audio": saved_audio, "scene": {"path": asset, "sha256": hash, "source_name": source.get_file(), "provenance": "unknown / must verify"}, "editor": {"frame": frame}}
	if not world.is_empty():
		manifest.schema_version=4;manifest.erase("scene");manifest.erase("model")
		if world.format==WorldDocument.EFFECT_FORMAT:manifest.schema_version=5
		manifest["world"]=WorldDocument.portable(world)
	if not recovery.is_empty(): manifest.editor["recovery"] = recovery
	if not palette.is_empty():manifest["palette"]=palette.duplicate(true)
	if editor_extra.has("lesson_ui"):manifest.editor["lesson_ui"]=editor_extra.lesson_ui.duplicate(true)
	if editor_extra.has("sequence_editor"):manifest.editor["sequence_editor"]=editor_extra.sequence_editor.duplicate(true)
	if not sequence_graph.is_empty():
		var saved_graph:={"format":sequence_graph.format,"clips":sequence_graph.clips.duplicate(true),"assets":[]}
		var decoded_audio_bytes:=AudioTrack.memory(audio)
		for sequence in sequence_graph.assets:
			var child: Dictionary=sequence.scene;var out:={}
			var error:=save_project(folder,child.video,child.camera_keys,child.layers,"",int(child.get("editor",{}).get("frame",0)),child.get("audio",{}),{},{},true,child.world,{},child.get("palette",[]),{},out)
			if not error.is_empty():return "Sequence %s: %s" % [sequence.name,error]
			decoded_audio_bytes+=AudioTrack.memory(child.get("audio",{}))
			if decoded_audio_bytes>AudioTrack.MAX_PCM:return "Nested audio sources exceed64MiB. Previous save preserved."
			saved_graph.assets.append({"id":sequence.id,"name":sequence.name,"clips":sequence.clips.duplicate(true),"scene":out.manifest})
		manifest.schema_version=6;manifest["sequence_graph"]=saved_graph
	if not reference_sheet.is_empty():
		var portable_reference:=ReferenceSheet.portable(reference_sheet)
		if DirAccess.make_dir_recursive_absolute(folder.path_join("references"))!=OK:return "Cannot create reference asset directory."
		var reference_error:=managed_copy(reference_sheet.source,folder.path_join(portable_reference.path),reference_sheet.sha256)
		if not reference_error.is_empty():return reference_error
		manifest["content_schema_version"]=manifest.schema_version;manifest.schema_version=7;manifest["reference_sheet"]=portable_reference
	if Extended.required(manifest):
		manifest["timing_content_schema_version"]=manifest.schema_version;manifest.schema_version=8
	# Compact JSON keeps dense recorded motion within the unchanged1MiB metadata cap.
	# Preserve small quaternion components across repeated editable saves.
	var serialized := JSON.stringify(manifest,"",true,true)
	if serialized.to_utf8_buffer().size() > 1024 * 1024: return "Project metadata exceeds 1 MiB. Reduce pose keys/metadata; previous manifest preserved."
	# Child scenes share content-addressed assets/cels in the parent folder, but
	# never replace its manifest. Only the fully checked root commits project.json.
	if _manifest_out is Dictionary:
		_manifest_out["manifest"]=manifest;return ""
	var temp:=fresh_temporary(folder.path_join("project.json"),".tmp")
	if temp.is_empty():return "Cannot create a fresh manifest temporary. Previous save preserved."
	var file := FileAccess.open(temp, FileAccess.WRITE)
	if file == null:
		return "Cannot write manifest; previous save preserved."
	file.store_string(serialized)
	file.flush()
	var write_error := file.get_error()
	file.close()
	if write_error != OK:
		return "Manifest write failed. Previous save preserved."
	if FileAccess.get_file_as_string(temp)!=serialized or not readable_manifest(temp):return "Manifest readback differs. Previous save preserved."
	var target := folder.path_join("project.json")
	if FileAccess.file_exists(target) and readable_manifest(target):
		var backup:=folder.path_join("project.backup.json");var backup_temp:=fresh_temporary(backup,".tmp")
		if backup_temp.is_empty() or DirAccess.copy_absolute(target,backup_temp)!=OK or FileAccess.get_sha256(backup_temp)!=FileAccess.get_sha256(target) or DirAccess.rename_absolute(backup_temp,backup)!=OK:
			return "Cannot back up/verify previous manifest; replacement aborted."
	var error := DirAccess.rename_absolute(temp, target)
	return "" if error == OK else "Cannot replace manifest: " + error_string(error)

static func numeric_array(value, length: int) -> bool:
	if not value is Array or value.size() != length:
		return false
	for v in value:
		if not (v is int or v is float) or not is_finite(float(v)):
			return false
	return true

static func integer(value, minimum: int, maximum: int) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and float(value) == floor(float(value)) and value >= minimum and value <= maximum

static func raster_reserve(data) -> int:
	# Policy estimate only, never validation. Saved schema wrappers keep tracks at
	# the root; editable sequence assets contain one additional scene level.
	if not data is Dictionary:return 0
	var documents: Array=[data];var graph=data.get("sequence_graph",{})
	if graph is Dictionary and graph.get("assets") is Array:
		for asset in graph.assets:
			if asset is Dictionary and asset.get("scene") is Dictionary:documents.append(asset.scene)
	var count:=0
	for scene in documents:
		if not scene.get("layers") is Array:continue
		for layer in scene.layers:
			if layer is Dictionary and layer.get("cels") is Array:count+=layer.cels.size()
	return count*1920*1080*4

static func load_project(folder: String, manifest_name := "project.json",cold_cels:=false,cold_min_bytes:=0) -> Dictionary:
	if manifest_name not in ["project.json", "project.backup.json"] and not Journal.valid_manifest(folder,manifest_name): return {"error": "Unsupported or changed recovery manifest."}
	var manifest_path := folder.path_join(manifest_name)
	if not FileAccess.file_exists(manifest_path):
		return {"error": "No project.json in selected directory."}
	var file := FileAccess.open(manifest_path, FileAccess.READ)
	if file == null or file.get_length() > 1024 * 1024:
		return {"error": "Cannot read manifest or it exceeds 1 MiB."}
	var parser := JSON.new()
	if parser.parse(file.get_as_text()) != OK:
		return {"error": "Corrupt JSON manifest: " + parser.get_error_message()}
	var rasters:=RasterReader.new();rasters.cold_cels=cold_cels and (cold_min_bytes==0 or raster_reserve(parser.data)>cold_min_bytes)
	var loaded:=decode_project(parser.data,folder,false,rasters)
	if not loaded.has("error") and rasters.cold_cels:loaded["raster_cache"]=rasters.adaptive_cache
	return loaded

static func decode_project(data,folder: String,extended:=false,rasters=null) -> Dictionary:
	if rasters==null:rasters=RasterReader.new()
	if data is Dictionary and data.get("schema_version")==8:
		var unwrapped:=Extended.unwrap(data)
		return unwrapped if unwrapped.has("error") else decode_project(unwrapped.base,folder,true,rasters)
	if data is Dictionary and data.has("timing_content_schema_version"):return {"error":"Extended project timing requires schema8."}
	if data is Dictionary and not extended and Extended.required(data):return {"error":"Extended project timing requires schema8."}
	if data is Dictionary and data.get("schema_version")==7:
		var unwrapped:=ReferenceSheet.unwrap(data)
		if unwrapped.has("error"):return unwrapped
		var reference: Dictionary=unwrapped.reference
		var loaded:=ReferenceSheet.read_image(folder.path_join(reference.path))
		if loaded.has("error"):return loaded
		if loaded.sha256!=reference.sha256:return {"error":"Reference sheet checksum differs. Previous project stays open."}
		var result:=decode_project(unwrapped.base,folder,extended,rasters)
		if result.has("error"):return result
		reference["source"]=folder.path_join(reference.path);reference.erase("path");result["reference_sheet"]=reference
		return result
	if data is Dictionary and (data.has("reference_sheet") or data.has("content_schema_version")):return {"error":"Project reference sheets require schema7."}
	if not data is Dictionary or not integer(data.get("schema_version"),1,6):
		return {"error":"Invalid manifest or unsupported schema. Previous project stays open."}
	if data.schema_version==6:
		var graph=data.get("sequence_graph");var why:=Sequences.error(graph,data)
		if not why.is_empty():return {"error":why}
		var base: Dictionary=data.duplicate(true);base.erase("sequence_graph")
		base.schema_version=5 if base.world.get("format")==WorldDocument.EFFECT_FORMAT else 4
		var context=base.get("editor",{}).get("sequence_editor",{}) if base.get("editor",{}) is Dictionary else {}
		if base.get("editor",{}) is Dictionary:base.editor.erase("sequence_editor")
		var result:=decode_project(base,folder,extended,rasters)
		if result.has("error"):return result
		var decoded: Dictionary=graph.duplicate(true)
		var pcm_bytes:=AudioTrack.memory(result.audio)
		for asset in decoded.assets:
			var child:=decode_project(asset.scene,folder,extended,rasters)
			if child.has("error"):return {"error":"Sequence %s: %s" % [asset.name,child.error]}
			pcm_bytes+=AudioTrack.memory(child.audio)
			if pcm_bytes>AudioTrack.MAX_PCM:return {"error":"Nested audio sources exceed64MiB."}
			asset.scene=child
		result.schema_version=6;result["sequence_graph"]=decoded
		if not context.is_empty():result.editor["sequence_editor"]=context
		return result
	if data.has("sequence_graph"):return {"error":"Editable sequences require project schema6."}
	if data.get("editor",{}) is Dictionary and data.get("editor",{}).has("sequence_editor"):return {"error":"Sequence editor context requires project schema6."}
	if not data is Dictionary or not integer(data.get("schema_version"), 1, 5):
		return {"error": "Invalid manifest or unsupported schema. Previous project stays open."}
	var palette_error:=preload("res://src/color_palette.gd").error(data.get("palette",[]))
	if not palette_error.is_empty():return {"error":palette_error}
	var video = data.get("video")
	if not video is Dictionary:
		return {"error": "Missing video settings."}
	var output_error:=preload("res://src/output_size.gd").project_error(video)
	if not output_error.is_empty():return {"error":output_error}
	var lighting_error:=Lighting.validate(video)
	if not lighting_error.is_empty():return {"error":lighting_error}
	if video.has("world_background") and not video.world_background in ["black","legacy_blue"]:
		return {"error": "Invalid world background setting."}
	if video.has("visibility_fade_ms") and not integer(video.visibility_fade_ms,0,10000):return {"error":"Visibility fade must be0–10000 milliseconds."}
	for prop in ["width", "height"]:
		if not integer(video.get(prop), 1, 1920):
			return {"error": "Invalid video setting: " + prop}
	if video.width != 1920 or video.height != 1080 or not Extended.video_error(video).is_empty():
		return {"error": "Unsupported canvas size or project timing."}
	var rate_error:=preload("res://src/video_timing.gd").error(video.get("fps_num"),video.get("fps_den"))
	if not rate_error.is_empty():return {"error":rate_error}
	var keys = data.get("camera_keys")
	if not keys is Array or keys.is_empty() or keys.size() > 241:
		return {"error": "Missing or excessive camera keys."}
	var camera_error:=Timeline.range_error(keys)
	if not camera_error.is_empty():return {"error":camera_error}
	var previous := -1
	for key in keys:
		if not key is Dictionary or not integer(key.get("frame"), 0, maxi(240,int(video.duration_frames))) or key.frame <= previous or not numeric_array(key.get("position"), 3) or not numeric_array(key.get("rotation_xyzw"), 4):
			return {"error": "Invalid or unsorted camera key."}
		if not integer(key.get("fov"), 1, 179) and not ((key.get("fov") is float) and key.fov > 1 and key.fov < 179):
			return {"error": "Invalid camera FOV."}
		var q: Array = key.rotation_xyzw
		if Vector4(q[0], q[1], q[2], q[3]).length() < 0.001 or not key.get("interpolation") in ["hold", "linear", "ease"]:
			return {"error": "Invalid camera rotation/interpolation."}
		previous = int(key.frame)
	var source := ""
	if data.schema_version==4 or data.schema_version==5:
		if data.has("scene") or data.has("model"): return {"error":"Schema4 cannot contain obsolete scene/model slots."}
		var world_error := WorldDocument.validate(data.get("world"),int(video.duration_frames),true)
		if not world_error.is_empty(): return {"error":world_error}
		if (data.schema_version==5)!=(data.world.format==WorldDocument.EFFECT_FORMAT):return {"error":"World format requires the matching project schema."}
		var checked := {}
		for row in WorldDocument.assets(data.world):
			if checked.has(row.path): continue
			var path := folder.path_join(row.path)
			var input := FileAccess.open(path,FileAccess.READ)
			if input==null or input.get_length()>row.limit or FileAccess.get_sha256(path)!=row.sha256:
				return {"error":"World asset missing, changed or oversized. Original project preserved."}
			checked[row.path]=true
		data.world=WorldDocument.resolve(data.world,folder)
		var particles:=WorldDocument.Particles.collection(data.world)
		if particles.has("error"):return particles
	else:
		var scene = data.get("scene")
		if not scene is Dictionary or not scene.get("path") is String or not safe_relative(scene.path):
			return {"error": "Unsafe or missing scene path."}
		source=folder.path_join(scene.path)
		if not FileAccess.file_exists(source) or FileAccess.get_sha256(source)!=scene.get("sha256"):
			return {"error":"Scene missing or checksum differs. Original project preserved."}
	var layers = data.get("layers")
	if not layers is Array or (data.schema_version<4 and layers.is_empty()) or layers.size() > 4:
		return {"error": "Expected 1–4 drawing layers."}
	var count := 0
	var opacity_error:=Drawing.opacity_error(layers)
	if not opacity_error.is_empty():return {"error":opacity_error}
	var origin_error:=preload("res://src/drawing_origin.gd").layers_error(layers)
	if not origin_error.is_empty():return {"error":origin_error}
	for layer in layers:
		if not layer is Dictionary or not layer.get("name") is String or not layer.get("id") is String or not layer.get("visible") is bool or not layer.get("cels") is Array:
			return {"error": "Invalid drawing layer."}
		var end := 0
		for cel in layer.cels:
			count += 1
			if not cel is Dictionary or not cel.get("id") is String or not cel.get("path") is String or not safe_relative(cel.path) or not integer(cel.get("start"), 0, video.duration_frames - 1) or not integer(cel.get("duration"), 1, video.duration_frames):
				return {"error": "Invalid cel or unsafe path."}
			if cel.start < end or cel.start + cel.duration > video.duration_frames or count > 32:
				return {"error": "Overlapping/out-of-range cels or >32 cels (memory limit)."}
			end = int(cel.start + cel.duration)
			var path := folder.path_join(cel.path)
			var raster: Dictionary=rasters.read_record(path,int(video.width),int(video.height),cel.get("pixel_sha256"),cel.has("pixel_sha256"))
			if raster.has("error"):return raster
			# Runtime ownership comes only from validated pixel loading, never JSON.
			cel.erase("raster_owner");cel.erase("image")
			if raster.has("raster_owner"):cel.raster_owner=raster.raster_owner
			else:cel.image=raster.image
	var audio = data.get("audio", {})
	if not audio is Dictionary:
		return {"error": "Invalid audio clip metadata."}
	var audio_layout := AudioTrack.layout_error(audio)
	if not audio_layout.is_empty(): return {"error":audio_layout}
	var decoded_sources := {}
	var audio_bytes := 0
	for clip in AudioTrack.clips(audio):
		if data.schema_version < 2 or not clip.get("path") is String or not safe_relative(clip.path) or not clip.get("sha256") is String:
			return {"error": "Invalid audio identity or unsafe asset path."}
		var timing_error := AudioTrack.clip_error(clip,video)
		if not timing_error.is_empty(): return {"error":timing_error}
		var audio_path := folder.path_join(clip.path)
		if not FileAccess.file_exists(audio_path) or FileAccess.get_sha256(audio_path) != clip.sha256:
			return {"error": "Audio asset missing or checksum changed. Open aborted."}
		var decoded: Dictionary = decoded_sources.get(clip.sha256,{})
		if decoded.is_empty(): decoded = AudioTrack.read_wav(audio_path)
		if decoded.has("error"): return decoded
		decoded_sources[clip.sha256] = decoded
		audio_bytes += decoded.pcm.size()
		if audio_bytes > AudioTrack.MAX_PCM: return {"error":"Audio sources exceed64MiB."}
		decoded = decoded.duplicate()
		if clip.get("source_name") is String: decoded.name = clip.source_name.left(200)
		if clip.source_in_sample >= decoded.frames:
			return {"error": "Audio trim starts past end of source."}
		if clip.get("source_out_sample",decoded.frames)>decoded.frames:return {"error":"Audio end trim exceeds the source."}
		clip["source"] = decoded
		if AudioTrack.sample_index(video.duration_frames, video) > AudioTrack.RATE * AudioTrack.MAX_SECONDS:
			return {"error": "Audio projects are limited to 60 seconds for this increment."}
	data["audio"] = audio
	if data.schema_version==4 or data.schema_version==5: return data
	var model = data.get("model", {})
	var model_error := Model.validate(model, video.duration_frames)
	if not model_error.is_empty(): return {"error": model_error}
	if not model.is_empty():
		if data.schema_version != 3 or not model.get("path") is String or not safe_relative(model.path): return {"error": "Invalid model asset path/schema."}
		model["source"] = folder.path_join(model.path)
		if not FileAccess.file_exists(model.source) or FileAccess.get_sha256(model.source) != model.sha256: return {"error": "Model asset missing or checksum changed."}
	data["model"] = model
	data["source"] = source
	return data
