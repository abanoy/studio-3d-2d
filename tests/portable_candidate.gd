extends SceneTree
# Cold-folder acceptance of actual packed Model7/8 native scenes. No old cache.
const World = preload("res://src/world_document.gd")
const Storage = preload("res://src/storage.gd")
const Drawing = preload("res://src/drawing.gd")
var app
var checks := 0
var failures := 0

func _initialize() -> void:
	create_timer(170).timeout.connect(func(): push_error("Portable candidate watchdog"); quit(2))
	call_deferred("run")

func check(ok: bool, label: String) -> void:
	checks += 1
	print(("PASS " if ok else "FAIL ") + label)
	if not ok: failures += 1

func settled() -> void:
	for i in range(5): await process_frame
	await RenderingServer.frame_post_draw

func job() -> void:
	while app.has_project.pid > 0: await process_frame
	await settled()

func read(path: String) -> Dictionary:
	return JSON.parse_string(FileAccess.get_file_as_string(path))

func same(a, b) -> bool:
	return JSON.parse_string(JSON.stringify(a,"",true,true)) == JSON.parse_string(JSON.stringify(b,"",true,true))

func run() -> void:
	var config := read(OS.get_cmdline_user_args()[0])
	var expected := read(config.expected)
	var folder := ProjectSettings.globalize_path("res://output/portable")
	DirAccess.make_dir_recursive_absolute(folder)
	app = load("res://main.tscn").instantiate()
	app.recovery_root = folder.path_join("recovery")
	app.recent_path = folder.path_join("recents.json")
	root.add_child(app)
	await settled()
	app.autosave_enabled.button_pressed = false
	app.has_project.cache_root = folder.path_join("cache")
	check(app.current_world().objects.is_empty() and not app.advanced_mode and app.video.world_background == "black", "cold copy starts with the normal empty Simple world")
	app.home.open_home()
	await settled()
	check(app.home.visible and app.home.new_button.visible and app.home.tutorials_button.visible, "cold copy has usable Home and tutorial entry points")
	app.home.new_button.pressed.emit()
	await settled()
	check(not app.home.visible and app.current_world().objects.is_empty(), "Home New returns to the actual empty editor")
	var original := FileAccess.get_sha256(config.project)
	app.has_project.open_file(config.project)
	await job()
	check(app.has_project.path == config.project and not app.dirty, "ordinary Open loads the relocated packed HAS without relinking")
	if app.has_project.path != config.project:
		app.free(); quit(1); return
	var world: Dictionary = expected.world if config.kind == "model7" else expected.expected_world
	check(same(World.portable(app.current_world()), world), "all portable native world data survives a cache-free source copy")
	var local_assets := true
	var cache := folder.path_join("cache").replace("\\","/").to_lower() + "/"
	for row in app.current_world().objects:
		if row.kind == "group": continue
		var path: String = ProjectSettings.globalize_path(row.source).replace("\\","/")
		local_assets = local_assets and path.to_lower().begins_with(cache) and FileAccess.get_sha256(path) == row.sha256
	check(local_assets, "every runtime 3D asset resolves inside this copy's newly extracted cache")
	var poses_exact := true
	if config.kind == "model7":
		for id in expected.ids:
			var actor: RefCounted = app.renderer.world_runtime.instance(id)
			if not actor: poses_exact = false; continue
			for half in range(96,-1,-1):
				poses_exact = poses_exact and JSON.stringify(actor.sample(float(half)/2),"",true,true).sha256_text() == expected.samples[id][half] and actor.evaluation_error.is_empty()
		check(same(app.video,expected.video) and same(app.keys,expected.keys), "legacy video and explicit camera keys survive exactly")
		check(Storage.image_hash(Drawing.image(app.layers[1].cels[0])) == expected.paint, "legacy editable drawing survives exactly")
		check(app.audio_clip.source.sha256 == expected.audio.sha256 and app.audio_clip.start_frame == expected.audio.start_frame and app.audio_clip.gain_db == expected.audio.gain_db, "legacy audio bytes, timing and gain survive exactly")
	else:
		var actor: RefCounted = app.renderer.world_runtime.instance("actor")
		poses_exact = actor != null and actor.motion_enabled()
		if actor:
			for half in range(96,-1,-1):
				poses_exact = poses_exact and JSON.stringify(actor.sample(float(half)/2),"",true,true).sha256_text() == expected.pose_hashes[half] and actor.evaluation_error.is_empty()
		check(Drawing.image(app.layers[1].cels[0]).get_data().hex_encode().sha256_text() == expected.layer_sha, "Model8 independent editable drawing survives exactly")
		check(app.import_audio(config.audio).is_empty(), "Model8 scene accepts a real local PCM sound clip")
		app.audio_clip.start_frame = 24
		app.audio_clip.gain_db = -6
		app.rebuild_audio()
	check(poses_exact, "native poses evaluate exactly in reverse without original import history")
	app.set_frame(int(config.frame))
	app.world_selection.clear()
	var image: Image = await app.renderer.capture(app.keys,app.layers,int(config.frame),true)
	var reference := Image.load_from_file(config.reference)
	reference.convert(Image.FORMAT_RGBA8)
	var a := image.get_data()
	var b := reference.get_data()
	var changed := 0
	var total := 0.0
	check(a.size() == b.size(), "relocated preview has the original output dimensions")
	if a.size() == b.size():
		for i in range(a.size()):
			if a[i] != b[i]: changed += 1; total += absf(float(a[i])-float(b[i]))
	var mean := total / float(a.size())
	check(changed <= 384 and mean < .002, "preview keeps the existing native mesh-edge pixel bound")
	image.save_png(folder.path_join("reopened.png"))
	# Edit an existing cel through the routed drawing control, then undo it.
	app.mode.select(0); app.change_mode(0)
	app.active_layer = 1; app.layer_choice.select(1); app.refresh_layer()
	var cel: Dictionary = Drawing.cel_at(app.layers[1],int(config.frame))
	var paint: String = Storage.image_hash(Drawing.image(cel))
	var before: Dictionary = World.portable(app.current_world())
	var shots: Array = app.keys.duplicate(true)
	app.color.color = Color.CYAN
	var press := InputEventMouseButton.new()
	press.button_index = MOUSE_BUTTON_LEFT; press.pressed = true
	app.canvas_input(press,Vector2(80,140))
	app.canvas_input(InputEventMouseMotion.new(),Vector2(240,140))
	press.pressed = false; app.canvas_input(press,Vector2(240,140))
	check(Storage.image_hash(Drawing.image(cel)) != paint and same(World.portable(app.current_world()),before) and app.keys == shots, "relocated drawing remains editable and independent of native 3D and shots")
	app.undo()
	check(Storage.image_hash(Drawing.image(Drawing.cel_at(app.layers[1],int(config.frame)))) == paint, "drawing Undo restores exact portable cel bytes")
	app.has_project.save_file(folder.path_join("Resaved portable.has"),"packed")
	await job()
	var saved: String = app.has_project.path
	check(saved == folder.path_join("Resaved portable.has") and not app.dirty, "relocated app saves a new portable HAS through its local worker")
	app.has_project.open_file(saved)
	await job()
	check(same(World.portable(app.current_world()),world), "new save reopens with exact native world data")
	check(app.audio_clip.start_frame == 24 and app.audio_clip.gain_db == -6 and app.audio_clip.source.path.replace("\\","/").to_lower().begins_with(cache), "resaved sound retains timing and gain in the new embedded cache")
	app.set_frame(int(config.frame))
	var own_preview: Image = await app.renderer.capture(app.keys,app.layers,int(config.frame),true)
	app.export_dialog()
	while app.exporting: await process_frame
	var movie: String = app.last_export_folder.path_join("movie.mp4")
	check(FileAccess.file_exists(movie) and app.last_export_folder.get_base_dir() == folder, "normal Simple export writes an MP4 beside the relocated HAS")
	check(own_preview.get_data() == Image.load_from_file(app.last_export_folder.path_join("frame_%06d.png" % (int(config.frame)+1))).get_data(), "exported frame exactly matches this process's synchronized preview")
	check(FileAccess.get_sha256(config.project) == original, "Open, drawing, Save and render preserve the supplied HAS bytes")
	await settled()
	root.get_texture().get_image().save_png(folder.path_join("editor.png"))
	var result := {"checks":checks,"failures":failures,"kind":config.kind,"changed_channels":changed,"mean_error":mean,"movie":movie,"project":saved}
	var file := FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify(result)); file.close()
	app.free(); await process_frame
	print("PORTABLE_CANDIDATE " + JSON.stringify(result))
	quit(0 if failures == 0 else 1)
