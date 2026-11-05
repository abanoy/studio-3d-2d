extends SceneTree
const T=preload("res://src/timeline.gd")
const SceneIO=preload("res://src/scene3d.gd")
const Drawing=preload("res://src/drawing.gd")
const Audio=preload("res://src/audio_track.gd")
var app
var checks:=0
var failures:=0
var movie_events:=0
class Watch extends Node:
	var app
	var action: String
	var fired:=false
	func _process(_delta: float) -> void:
		if fired or not app.exporting or not FileAccess.file_exists(app.last_export_folder.path_join("frame_000001.png")):return
		fired=true
		if action=="cancel":app.cancel_button.pressed.emit()
		elif action=="frame":DirAccess.make_dir_absolute(app.last_export_folder.path_join("frame_000003.png"))
		elif action=="manifest":DirAccess.make_dir_absolute(app.last_export_folder.path_join("sequence.json"))
func _initialize() -> void:
	create_timer(170).timeout.connect(func():quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settle() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func read(path: String) -> Dictionary:return JSON.parse_string(FileAccess.get_file_as_string(path))
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0];var asset:=folder.path_join("room.glb");check(SceneIO.make_fixture(asset)==OK,"original room fixture is written")
	var source_hash:=FileAccess.get_sha256(asset)
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false
	check(app.load_scene(asset).is_empty(),"standard scene loads for image rendering")
	app.keys=[T.key(0,Vector3(-1.5,2,5),Quaternion.IDENTITY,60),T.key(48,Vector3(1.5,1.6,3),Quaternion(Vector3.UP,-.15),52)]
	var red:=Drawing.blank(1920,1080);red.fill_rect(Rect2i(800,480,200,100),Color.RED)
	var blue:=Drawing.blank(1920,1080);blue.fill_rect(Rect2i(1000,480,200,100),Color.BLUE)
	Drawing.insert(app.layers[1],0,24,red);Drawing.insert(app.layers[1],24,24,blue);app.layers[1].opacity=.5
	check(app.import_audio(folder.path_join("tone.wav"),6).is_empty(),"sound loads for a synchronized sidecar")
	app.audio_fade_editor.open();app.audio_fade_editor.fade_in.value=100;app.audio_fade_editor.fade_out.value=100;app.audio_fade_editor.apply()
	var mixed: PackedByteArray=app.audio_mix.pcm.duplicate();app.encoder_path.text=folder.path_join("absent-ffmpeg.exe")
	app.set_frame(7);app.mode.select(1);app.change_mode(1);app.renderer.camera.position+=Vector3(2,1,0)
	var view: Dictionary=app.renderer.view_state();var shots: Array=app.keys.duplicate(true);var world: Dictionary=app.current_world().duplicate(true);var history: int=app.history.size();var frame: int=app.frame
	var expected: Image=await app.renderer.capture(app.keys,app.layers,24,true);app.renderer.restore_view(view)
	app.movie_export_finished.connect(func(_folder,_ok):movie_events+=1)
	check(await app.export_images(folder)=="","complete PNG export works without FFmpeg")
	var full: String=app.last_export_folder;var record:=read(full.path_join("sequence.json"))
	check(record.status=="complete" and record.rendered_frames==48 and record.first_frame==1 and record.video.fps_num==24 and record.video.fps_den==1,"timing record identifies every output frame and rational rate")
	check(Image.load_from_file(full.path_join("frame_000025.png")).get_data()==expected.get_data(),"scene PNG equals the shared final renderer at frame24")
	check(not FileAccess.file_exists(full.path_join("movie.mp4")) and not FileAccess.file_exists(full.path_join("encoder.log")),"image export does not start an encoder or invent a movie")
	check(Audio.read_wav(full.path_join("mixed_audio.wav")).pcm==mixed and record.audio=="mixed_audio.wav","WAV sidecar contains the exact preview mix including fades")
	check(app.renderer.view_state()==view and app.frame==frame and app.mode.selected==1 and app.keys==shots and app.current_world()==world and app.history.size()==history,"export restores editor view/frame/mode and preserves authored world/history")
	check(app.saved_frames_button.visible and app.interrupted_frames_folder==full and movie_events==0,"PNG success exposes its folder and does not complete a movie lesson")
	var old_data:=FileAccess.get_sha256(full.path_join("frame_000025.png"))
	check(await app.export_images(folder,true)=="","transparent drawing-only export succeeds")
	var transparent: String=app.last_export_folder;var alpha:=Image.load_from_file(transparent.path_join("frame_000025.png"));alpha.convert(Image.FORMAT_RGBA8)
	check(alpha.get_data()==Drawing.composite(app.layers,24,1920,1080).get_data() and alpha.get_pixel(10,10).a==0 and alpha.get_pixel(1050,500).a>.49 and alpha.get_pixel(1050,500).a<.51,"drawing-only PNG retains transparency, held cels and layer opacity")
	check(transparent!=full and FileAccess.get_sha256(full.path_join("frame_000025.png"))==old_data,"new image exports never overwrite a previous sequence")
	var saved:=folder.path_join("scene.has");app.has_project.save_file(saved,"packed")
	while app.has_project.pid>0:await process_frame
	await settle();check(app.has_project.path==saved,"normal HAS save supplies the image export destination")
	app.set_advanced(true);app.png_drawing_only.button_pressed=true
	var export_button: Button
	for control in app.png_drawing_only.get_parent().get_children():
		if control is Button and control.text=="Export PNG sequence…":export_button=control
	check(export_button!=null and export_button.is_visible_in_tree(),"PNG export is accessible in Advanced encoder options")
	export_button.pressed.emit()
	while app.exporting:await process_frame
	var gui_record:=read(app.last_export_folder.path_join("sequence.json"))
	check(gui_record.status=="complete" and gui_record.drawing_only and app.last_export_folder.get_base_dir()==folder,"actual PNG action uses the saved project folder and transparency choice")
	app.set_advanced(false)
	var previous_folder: String=app.last_export_folder
	var absent: String=await app.export_movie(folder);check("FFmpeg" in absent and app.last_export_folder==previous_folder,"MP4 retains its encoder requirement")
	for action in ["cancel","frame","manifest"]:
		var watch:=Watch.new();watch.app=app;watch.action=action;root.add_child(watch)
		var error: String=await app.export_images(folder,true);watch.free();var output: String=app.last_export_folder
		check(not error.is_empty() and not app.exporting and not app.cancel_button.visible and app.renderer.view_state()==view and app.history.size()==history,"failure/cancel restores controls and editor state: "+action)
		check(FileAccess.file_exists(output.path_join("frame_000001.png")) and app.saved_frames_button.visible,"completed images remain available: "+action)
		if action!="manifest":
			var partial:=read(output.path_join("sequence.json"));var written:=0
			for name in DirAccess.get_files_at(output):
				if name.begins_with("frame_") and name.ends_with(".png"):written+=1
			check(partial.status==("cancelled" if action=="cancel" else "failed") and partial.rendered_frames==written and written>=1 and written<48,"partial timing record reports exact completion state: "+action)
	check(FileAccess.get_sha256(asset)==source_hash and red.get_pixel(850,500)==Color.RED and movie_events==0,"exports and failures preserve source assets and drawings")
	app.audio_clip={};app.rebuild_audio();app.video.fps_num=25;app.video.fps_den=2;app.video.duration_frames=6;app.set_frame(0)
	check(await app.export_images(folder,true)=="","silent rational-rate sequence exports")
	var silent: String=app.last_export_folder;var rational:=read(silent.path_join("sequence.json"))
	check(rational.video.fps_num==25 and rational.video.fps_den==2 and rational.rendered_frames==6 and rational.audio=="" and not FileAccess.file_exists(silent.path_join("mixed_audio.wav")),"silent sequence preserves25/2fps and exactly six frames")
	var result:={"checks":checks,"failures":failures,"full":full,"transparent":transparent,"silent":silent,"source_hash":source_hash,"movie_events":movie_events}
	FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("PNG_EXPORT_SMOKE ",JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
