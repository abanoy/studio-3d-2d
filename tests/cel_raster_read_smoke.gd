extends "res://tests/movement_path_smoke.gd"
const Snapshot=preload("res://src/cel_raster_snapshot.gd")
const Owner=preload("res://src/cel_raster_owner.gd")
const Cache=preload("res://src/cel_raster_snapshot_cache.gd")
const Drawing=preload("res://src/drawing.gd")
func _initialize() -> void:
	create_timer(200).timeout.connect(func():push_error("Cold read watchdog");quit(2));call_deferred("run")
func run() -> void:
	folder=OS.get_cmdline_user_args()[0];app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false
	check(app.load_demo_room(),"original demo room opens for staged cold-read integration")
	var source_sha:=FileAccess.get_sha256(app.source);var layer: Dictionary=app.layers[1];var hashes: Array=[]
	for i in range(4):
		var image:=Drawing.blank(1920,1080);image.fill(Color(0,.5,0,0));image.fill_rect(Rect2i(480+i*100,240,192,96),Color(float(i+1)/4,.3,.7,.5));Drawing.insert(layer,i*12,(i+1)*12,image);hashes.append(Snapshot.digest(image.get_data()))
	layer.opacity=.5;app.changed();app.set_frame(6);await settled();var eager: Image=await app.renderer.capture(app.keys,app.layers,6,true);eager.save_png(folder.path_join("eager6.png"))
	var cache:=Cache.new();var snapshots: Array=[]
	for cel in layer.cels:
		var captured:=Snapshot.capture(Drawing.image(cel));snapshots.append(captured.raster);cel.raster_owner=Owner.from_snapshot(captured.raster,cache).owner;cel.erase("image")
	app.overlay_dirty=true;await settled();var cold: Image=await app.renderer.capture(app.keys,app.layers,6,true)
	check(cold!=null and cold.get_data()==eager.get_data(),"actual final GPU frame agrees exactly before and after staged cold ownership")
	check(app.canvas.overlay.get_image().get_data()==Drawing.composite(app.layers,6,1920,1080).get_data() and app.raster_preview_error.is_empty(),"actual preview texture uses exact cold drawing composite")
	var decodes:=cache.decodes;var builds: int=app.drawing_overlay_cache.builds;cache.clear();app.set_frame(7);await settled()
	check(cache.decodes==decodes and app.drawing_overlay_cache.builds==builds,"seeking inside a hold reuses derived preview after decoded cache eviction")
	app.set_frame(18);app.onion_editor.enabled.button_pressed=true;await settled()
	check(app.onion_editor.views[0].visible and app.onion_editor.views[1].visible and app.onion_editor.views[0].texture.get_image().get_data()==snapshots[0].materialize().image.get_data() and app.onion_editor.views[1].texture.get_image().get_data()==snapshots[2].materialize().image.get_data(),"actual onion textures show exact cold previous and next drawings")
	var uploads: int=app.onion_editor.uploads;decodes=cache.decodes;app.set_frame(19);await settled()
	check(app.onion_editor.uploads==uploads and cache.decodes==decodes,"held onion/preview identities avoid repeated uploads and decoding")
	app.active_layer=1;app.layer_choice.select(1);app.color_sampler.source.select(2);app.tool.select(3);app.color_sampler.start(Vector2(600,270));await settled()
	check(app.color.color==Color(float(2)/4,.3,.7,.5) or app.color.color==snapshots[1].materialize().image.get_pixel(600,270),"actual active-layer sampler reads original cold source color")
	app.onion_editor.enabled.button_pressed=false;app.set_frame(12);await settled();var expected12: Image=await app.renderer.capture(app.keys,app.layers,12,true);expected12.save_png(folder.path_join("expected12.png"))
	var cue:="res://examples/tutorials/Practice cue.wav";var cue_sha:=FileAccess.get_sha256(cue);check(app.import_audio(ProjectSettings.globalize_path(cue),24).is_empty(),"original synchronized cue loads for cold movie rendering")
	var error: String=await app.export_movie(folder);var movie: String=app.last_finished_movie;var movie_folder: String=app.last_export_folder
	check(error.is_empty() and Image.load_from_file(movie_folder.path_join("frame_000013.png")).get_data()==expected12.get_data(),"actual cold-source movie input equals known final GPU frame")
	error=await app.export_images(folder,true);var images: String=app.last_export_folder
	check(error.is_empty() and Image.load_from_file(images.path_join("frame_000013.png")).get_data()==Drawing.composite(app.layers,12,1920,1080).get_data(),"transparent PNG export uses exact cold source pixels")
	var unchanged:=true
	for i in range(layer.cels.size()):unchanged=unchanged and not layer.cels[i].raster_owner.is_pinned() and layer.cels[i].raster_owner.snapshot().raster.pixel_sha256()==hashes[i]
	check(unchanged and FileAccess.get_sha256(app.source)==source_sha and FileAccess.get_sha256(cue)==cue_sha and cache.retained_bytes<=Cache.DEFAULT_BUDGET,"all readonly paths preserve cold ownership/source assets and decoded cache ceiling")
	app.set_frame(0);await settled();var previous: PackedByteArray=app.canvas.overlay.get_image().get_data();snapshots[0]._payload[0]=snapshots[0]._payload[0]^1;app.overlay_dirty=true;await settled()
	check(not app.raster_preview_error.is_empty() and not app.playing and app.canvas.overlay.get_image().get_data()==previous,"corrupt cold preview stops with explicit error and retains the last valid picture")
	error=await app.export_images(folder,true);var failed: String=app.last_export_folder;var record: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(failed.path_join("sequence.json")))
	check(not error.is_empty() and record.status=="failed" and record.rendered_frames==0 and not FileAccess.file_exists(failed.path_join("frame_000001.png")),"corrupt cold PNG export refuses before writing replacement artwork")
	error=await app.export_movie(folder);var refused_movie: String=app.last_export_folder
	check(not error.is_empty() and not FileAccess.file_exists(refused_movie.path_join("frame_000001.png")) and app.last_finished_movie==movie and not app.exporting,"corrupt cold movie render refuses before encoding and preserves earlier completed movie")
	print("CEL_RASTER_READ_SMOKE "+JSON.stringify({"checks":checks,"failures":failures,"movie":movie,"images":images,"failed_images":failed}));await app.quit_studio();quit(0 if failures==0 else 1)
