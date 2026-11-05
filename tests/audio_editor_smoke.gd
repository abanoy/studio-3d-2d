extends Node
const AudioTrack = preload("res://src/audio_track.gd")
const Storage = preload("res://src/storage.gd")
var failures := 0
var checks := 0

func check(ok: bool, message: String) -> void:
	checks += 1
	print(("PASS " if ok else "FAIL ") + message)
	if not ok: failures += 1

func energy(samples: PackedVector2Array) -> float:
	var peak := 0.0
	for sample in samples: peak = maxf(peak, maxf(absf(sample.x), absf(sample.y)))
	return peak

func waveform_peak(samples: PackedFloat32Array) -> float:
	var peak := 0.0
	for sample in samples: peak = maxf(peak, sample)
	return peak

func wait_realtime(seconds: float) -> void:
	# SceneTree timers can consume the previous long edit's delta on their first tick.
	var until := Time.get_ticks_usec() + int(seconds * 1000000)
	var rendered_frames := 0
	while Time.get_ticks_usec() < until or rendered_frames < 3:
		await RenderingServer.frame_post_draw
		rendered_frames += 1

func run(app) -> void:
	await get_tree().process_frame
	var parent := ProjectSettings.globalize_path("res://output/audio-editor")
	DirAccess.make_dir_recursive_absolute(parent)
	var fixture := ProjectSettings.globalize_path("res://output/fixtures/voice — тест.wav")
	var hash := FileAccess.get_sha256(fixture)
	# Combine the core workflow in one saved/exported fixture, without external artwork.
	app.set_frame(0)
	print("AUDIO_DRAW mode=",app.mode.selected," layer=",app.active_layer," tool=",app.tool.selected," color=",app.color.color," exporting=",app.exporting)
	var pen := InputEventMouseButton.new()
	pen.button_index = MOUSE_BUTTON_LEFT
	pen.pressed = true
	app.canvas_input(pen, Vector2(960, 430))
	for i in range(1, 65):
		var angle := TAU * i / 64
		app.paint_segment(Vector2(960 + sin(angle) * 60, 490 - cos(angle) * 60))
	for point in [Vector2(960, 550), Vector2(960, 700), Vector2(900, 790), Vector2(960, 700), Vector2(1020, 790), Vector2(960, 700), Vector2(960, 600), Vector2(860, 650), Vector2(960, 600), Vector2(1060, 650)]:
		app.paint_segment(point)
	pen.pressed = false
	app.canvas_input(pen, Vector2(1060, 650))
	check(app.layers[1].cels[0].image.get_pixel(960, 430).a > 0.9, "held character drawing remains independent above animated room")
	check(app.import_audio(fixture).is_empty(), "import real PCM16 WAV at 44.1 kHz")
	app.audio_start.value = 24
	app.audio_gain.value = -6
	app.apply_audio_settings()
	check(app.audio_clip.start_frame == 24 and app.audio_clip.gain_db == -6, "apply frame offset and gain")
	check(app.audio_mix.samples == 96000 and app.audio_mix.pcm.size() == 384000, "full-length 48kHz stereo project mix")
	var pcm: PackedByteArray = app.audio_mix.pcm
	check(pcm.decode_s16(24000 * 4) == 0, "mix is silent before clip starts")
	var peak := 0
	for sample in range(48000, 49000): peak = maxi(peak, absi(pcm.decode_s16(sample * 4)))
	check(peak > 7900 and peak < 8100, "44.1→48kHz resampling and -6dB gain")
	check(app.timeline.waveform.size() == 256 and app.timeline.waveform[10] == 0, "timeline waveform follows project-time silence")
	app.audio_trim.value = 100
	app.apply_audio_settings()
	check(app.audio_clip.source_in_sample == 4410, "trim stored in exact source sample units")
	app.undo()
	check(app.audio_clip.source_in_sample == 0, "audio settings undo restores source trim")
	app.audio_mute.button_pressed = true
	check(app.audio_clip.muted and waveform_peak(app.audio_mix.peaks) == 0, "mute produces silent preview/export mix")
	app.undo()
	check(not app.audio_clip.muted and waveform_peak(app.audio_mix.peaks) > 0.2, "mute undo restores audible mix")
	var clip_id: String = app.audio_clip.id
	var invalid := ProjectSettings.globalize_path("res://output/fixtures/float.wav")
	check(not app.import_audio(invalid).is_empty() and app.audio_clip.id == clip_id, "unsupported WAV keeps current clip")
	# Capture the application's actual audio bus, muted after effects to avoid loud test tones.
	var bus := AudioServer.bus_count
	AudioServer.add_bus()
	AudioServer.set_bus_name(bus, "StudioTestCapture")
	var capture := AudioEffectCapture.new()
	capture.buffer_length = 1
	AudioServer.add_bus_effect(bus, capture)
	AudioServer.set_bus_mute(bus, true)
	app.audio_player.bus = "StudioTestCapture"
	# Three GPU readbacks can exceed the remaining second on a busy machine.
	# Inspect the running clock in a longer fixture, then restore the 48-frame film.
	var film_duration: int=app.video.duration_frames
	app.video.duration_frames=240
	app.rebuild_audio()
	app.set_frame(24)
	app.toggle_play()
	await wait_realtime(0.14)
	var actual := capture.get_buffer(capture.get_frames_available())
	var dummy := AudioServer.get_driver_name() == "Dummy"
	if dummy:
		check(not app.audio_clock and app.status.text.contains("fallback"), "Dummy driver reports explicit silent fallback")
	else:
		check(actual.size() > 0 and energy(actual) > 0.1, "AudioStreamPlayer emits real mixed samples when seeking to frame 24")
	# A fresh clock read after rendering/logging refers to a later instant. Compare
	# the displayed frame against the clock actually sampled by the normal process.
	var sampled: float=app.preview_sample_seconds;var clock_now: float=app.preview_seconds()
	var expected := floori(sampled * 24)
	print("CLOCK frame=%d sampled=%.4f current=%.4f position=%.4f latency=%.4f driver=%s playing=%s" % [app.frame,sampled,clock_now,app.audio_player.get_playback_position(),app.audio_latency,AudioServer.get_driver_name(),app.playing])
	check(app.playing and app.frame>24 and sampled>1.03 and clock_now>=sampled and absi(app.frame - expected) <= 1 and (dummy or app.audio_player.get_playback_position() > 1.01), "preview follows selected audio/fallback clock")
	var earlier_frame: int=app.frame
	await wait_realtime(0.12)
	var later: float=app.preview_sample_seconds
	check(app.playing and later>sampled and app.frame>earlier_frame and absi(app.frame-floori(later*24))<=1,"preview continues following the live clock across later rendered frames")
	check(app.audio_clock == (AudioServer.get_driver_name() != "Dummy"), "audio driver chooses hardware clock or explicit silent fallback")
	app.toggle_play()
	var paused: int = app.frame
	await wait_realtime(0.08)
	check(not app.audio_player.playing and app.frame == paused, "pause stops audio and holds exact frame")
	app.video.duration_frames=film_duration
	app.rebuild_audio()
	app.set_frame(0)
	capture.clear_buffer()
	app.toggle_play()
	await wait_realtime(0.12)
	actual = capture.get_buffer(capture.get_frames_available())
	check((dummy or actual.size() > 0) and energy(actual.slice(actual.size() / 2)) < 0.001, "seek to frame 0 previews silence before offset")
	app.stop()
	app.audio_player.stream = null
	await wait_realtime(0.1)
	app.audio_player.bus = "Master"
	AudioServer.remove_bus(bus)
	capture = null
	await wait_realtime(0.05)
	if "--dummy-audio-test" in OS.get_cmdline_user_args():
		print("AUDIO_DUMMY failures=", failures)
		get_tree().quit(0 if failures == 0 else 1)
		return
	var folder := parent.path_join("Editable audio — проект")
	app.project_folder = folder
	app.set_frame(12)
	app.save()
	var mixed: PackedByteArray = app.audio_mix.pcm
	check(not Storage.load_project(folder).has("error"), "schema2 manifest loads independently")
	app.remove_audio()
	app.set_frame(0)
	app.open_project(folder)
	check(not app.dirty and app.frame == 12 and not app.audio_clip.is_empty() and app.audio_clip.start_frame == 24 and app.audio_clip.gain_db == -6, "schema2 reopen restores audio after clearing live state")
	check(app.audio_mix.pcm == mixed and FileAccess.get_sha256(app.audio_clip.source.path) == hash, "save/reopen retains exact mix and original audio bytes")
	app.remove_audio()
	check(app.audio_clip.is_empty() and app.audio_mix.is_empty(), "remove clip restores silent workflow")
	app.undo()
	check(app.audio_mix.pcm == mixed, "remove audio undo restores full clip")
	app.set_frame(0)
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(parent.path_join("editor.png"))
	var error: String = await app.export_movie(parent)
	check(error.is_empty() and FileAccess.file_exists(app.last_export_folder.path_join("mixed_audio.wav")), "editor exports MP4 with deterministic mixed WAV")
	var export_folder: String = app.last_export_folder
	# Backward-compatible migration from a genuine schema1 manifest.
	var file := FileAccess.open(folder.path_join("project.json"), FileAccess.READ)
	var data: Dictionary = JSON.parse_string(file.get_as_text())
	data.schema_version = 1
	data.erase("audio")
	# Assets/cels stay in same directory: preserve current manifest separately while testing migration.
	var saved_bytes := FileAccess.get_file_as_bytes(folder.path_join("project.json"))
	var legacy_file := FileAccess.open(folder.path_join("project.json"), FileAccess.WRITE)
	legacy_file.store_string(JSON.stringify(data))
	legacy_file.close()
	var loaded := Storage.load_project(folder)
	print("MIGRATION ", loaded.get("error", "ok"), " audio_empty=", loaded.get("audio", {}).is_empty())
	check(not loaded.has("error") and loaded.audio.is_empty(), "schema1 projects migrate as silent projects")
	legacy_file = FileAccess.open(folder.path_join("project.json"), FileAccess.WRITE)
	legacy_file.store_buffer(saved_bytes)
	legacy_file.close()
	var report := {"checks": checks, "failures": failures, "export": export_folder, "audio_driver": AudioServer.get_driver_name()}
	var output := FileAccess.open(parent.path_join("result.json"), FileAccess.WRITE)
	output.store_string(JSON.stringify(report, "\t"))
	print("AUDIO_EDITOR ", JSON.stringify(report))
	get_tree().quit(0 if failures == 0 else 1)
