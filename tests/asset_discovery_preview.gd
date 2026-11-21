extends SceneTree
const Preview = preload("res://src/discovery/local_preview.gd")
const SceneIO = preload("res://src/scene3d.gd")
var checks := 0
var failures: Array = []

func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok: failures.append(label); printerr("FAIL: " + label)

func _initialize() -> void:
	create_timer(20).timeout.connect(func(): quit(2))
	call_deferred("run")

func write_glb(path: String, data: Dictionary, binary: PackedByteArray) -> void:
	var json := JSON.stringify(data).to_utf8_buffer()
	while json.size() % 4: json.append(32)
	var file := FileAccess.open(path, FileAccess.WRITE)
	for word in [0x46546c67, 2, 20 + json.size() + binary.size(), json.size(), 0x4e4f534a]: file.store_32(word)
	file.store_buffer(json); file.store_buffer(binary); file.close()

func run() -> void:
	var folder := OS.get_cmdline_user_args()[0]
	var path := folder.path_join("preview.glb")
	check(SceneIO.make_fixture(path) == OK, "generate original procedural preview geometry")
	var original := FileAccess.get_file_as_bytes(path)
	var count := original.decode_u32(12)
	var data: Dictionary = JSON.parse_string(original.slice(20, 20 + count).get_string_from_utf8())
	var binary := original.slice(20 + count)
	var result := Preview.prepare(path)
	check(result.has("bytes"), "prepare embedded GLB geometry")
	var clean: Dictionary = JSON.parse_string(result.bytes.slice(20, 20 + result.bytes.decode_u32(12)).get_string_from_utf8())
	check(not clean.has("materials") and not clean.has("images") and not clean.has("animations"), "preview bytes omit materials images and animation")
	data.images = [{"uri":"https://example.invalid/not-requested.png"}]
	data.animations = [{"channels":[], "samplers":[]}]
	data.extras = {"script":"not loaded"}
	var variant := folder.path_join("variant.glb")
	write_glb(variant, data, binary)
	var stripped := Preview.prepare(variant)
	check(stripped.has("bytes") and not stripped.bytes.get_string_from_ascii().contains("https://"), "external image metadata is discarded rather than fetched")
	data.buffers[0].uri = "../outside.bin"; write_glb(variant, data, binary)
	check(Preview.prepare(variant).error.contains("buffers"), "external geometry buffers refused")
	data.buffers[0].erase("uri"); var declared = data.buffers[0].byteLength
	data.buffers[0].byteLength = Preview.MAX_BYTES + 1; write_glb(variant, data, binary)
	check(Preview.prepare(variant).error.contains("buffer length"), "declared buffer length cannot exceed embedded data")
	data.buffers[0].byteLength = declared
	var children = data.nodes[0].get("children", [])
	data.nodes[0].children = [0]; write_glb(variant, data, binary)
	check(Preview.prepare(variant).error.contains("cyclic"), "cyclic preview hierarchy rejected before import")
	data.nodes[0].children = children
	data.buffers[0].erase("uri"); data.extensionsRequired = ["KHR_draco_mesh_compression"]; write_glb(variant, data, binary)
	check(Preview.prepare(variant).error.contains("extensions"), "required extensions do not launch a converter")
	data.erase("extensionsRequired"); data.accessors[0].count = 250001; write_glb(variant, data, binary)
	check(Preview.prepare(variant).has("error"), "excessive geometry rejected before importing")
	var file := FileAccess.open(variant, FileAccess.WRITE); file.store_string("not glb"); file.close()
	check(Preview.prepare(variant).error.contains("header"), "malformed local file reports header error")
	check(Preview.prepare(folder.path_join("source.pmx")).error.contains("GLB"), "other model formats never launch preview conversion")
	file = FileAccess.open(variant, FileAccess.WRITE); file.seek(Preview.MAX_BYTES); file.store_8(0); file.close()
	check(Preview.prepare(variant).error.contains("8 MiB"), "preview file byte limit enforced")
	var opened := Preview.open(root, path)
	check(opened.has("window"), "geometry opens in independent preview window")
	var window: Window = opened.window
	var camera: Camera3D = window.get_meta("preview_camera")
	var before := camera.transform
	var slider: HSlider = window.get_meta("preview_orbit"); slider.value += 60
	check(camera.transform != before, "preview orbit changes only its own camera")
	check(window.get_meta("preview_viewport").own_world_3d, "preview has its own 3D world")
	check(FileAccess.get_file_as_bytes(path) == original, "preview leaves the original GLB bytes unchanged")
	window.close_requested.emit(); await process_frame; await process_frame
	check(not is_instance_valid(window), "closing preview frees its isolated scene")
	var report := {"checks":checks, "failures":failures, "scope":"Generated local GLB geometry only; no external files, network, conversion or owner artwork."}
	file = FileAccess.open(folder.path_join("preview-result.json"), FileAccess.WRITE); file.store_string(JSON.stringify(report, "  ")); file.close()
	print("DISCOVERY_GEOMETRY_PREVIEW " + JSON.stringify(report))
	quit(1 if not failures.is_empty() else 0)
