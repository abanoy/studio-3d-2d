extends "res://tests/movement_path_smoke.gd"
const Audio=preload("res://src/audio_track.gd")
func _initialize() -> void:
	create_timer(100).timeout.connect(func():push_error("Waveform cache watchdog");quit(2));call_deferred("run")
func signature(value: PackedByteArray) -> String:
	var digest:=HashingContext.new();digest.start(HashingContext.HASH_SHA256);digest.update(value);return digest.finish().hex_encode()
func peak_value(values: PackedFloat32Array) -> float:
	var result:=0.0
	for value in values:result=maxf(result,value)
	return result
func run() -> void:
	folder=OS.get_cmdline_user_args()[0];app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false
	app.show_project_options();app.project_options.hide();check(app.project_timing.apply_duration(1440).is_empty(),"long waveform scene opens")
	var wav:=folder.path_join("impulses.wav");var source_sha:=FileAccess.get_sha256(wav)
	check(app.import_audio(wav,1296).is_empty(),"original four-transient source imports at54seconds")
	var view=app.timeline;var nav=app.timeline_navigation
	check(view.visible_waveform(0).size()==256 and app.audio_mix.clip_waveform_levels[0].size()==6,"Fit keeps original overview with bounded detailed levels cached")
	app.set_frame(1298)
	for i in range(6):nav.zoom(.5,1298)
	check(view.visible_waveform(0).size()==8192,"zoom uses fine cached detail for short sound")
	var mixed: Dictionary=app.audio_mix;var pcm:=signature(mixed.pcm);var fine: PackedFloat32Array=mixed.clip_waveform_levels[0][-1];var peaks_sha:=signature(fine.to_byte_array());var revision: int=app.recovery_revision;var history: int=app.history.size()
	DirAccess.rename_absolute(wav,wav+".offline")
	for i in range(20):nav.navigate("left" if i%2==0 else "right",1298)
	nav.scrollbar.value=1290;await settled()
	check(is_same(mixed,app.audio_mix) and pcm==signature(app.audio_mix.pcm) and peaks_sha==signature(view.visible_waveform(0).to_byte_array()),"zoom and pan reuse identical mix/cache without source-file access")
	check(app.history.size()==history and app.recovery_revision==revision,"waveform navigation leaves content/history unchanged")
	# Reveal the actual sampled Audio row in the compact viewport; drawing rows precede it.
	var tracks_scroll: ScrollContainer=view.get_parent()
	var dock_scroll: ScrollContainer=app.workspace_layout.panels.timeline.get_node("TimelineContentScroll")
	dock_scroll.ensure_control_visible(tracks_scroll);await settled()
	tracks_scroll.scroll_vertical=int(view.audio_y());await settled()
	var screen: Image=app.get_viewport().get_texture().get_image();screen.save_png(folder.path_join("fine-waveform.png"))
	var green:=Color("467d45");var bars:=0
	# Approved Neon palette, derived from source RGBA layers, never from captured pixels.
	var neon_style: bool=preload("res://src/studio_theme.gd").is_neon()
	var neon_wave:=Color(0.239,0.863,0.592,0.85)
	var neon_body:=Color("0c0d11").blend(Color(0.239,0.863,0.592,0.12)).blend(neon_wave)
	var neon_border:=Color("3ddc97").blend(neon_wave)
	var sample_bounds_valid:=true
	var image_bounds:=Rect2i(Vector2i.ZERO,screen.get_size())
	var diagnostic_clip_rect: Rect2=view.audio_rect(0)
	print("WAVEFORM_PALETTE_CONTEXT ",JSON.stringify({"format":"has_waveform_palette_context_1","neon":neon_style,"selected_audio":view.audio_selected,"focus_lane":view.focus_lane,"fill_source_rgba":[0.239,0.863,0.592,0.12],"wave_source_rgba":[0.239,0.863,0.592,0.85],"body_expected_rgb":[neon_body.r,neon_body.g,neon_body.b],"border_expected_rgb":[neon_border.r,neon_border.g,neon_border.b],"view_global":[view.global_position.x,view.global_position.y],"view_size":[view.size.x,view.size.y],"clip_rect":[diagnostic_clip_rect.position.x,diagnostic_clip_rect.position.y,diagnostic_clip_rect.size.x,diagnostic_clip_rect.size.y],"audio_y":view.audio_y(),"tracks_scroll_vertical":tracks_scroll.scroll_vertical,"dock_scroll_vertical":dock_scroll.scroll_vertical,"image_size":[screen.get_width(),screen.get_height()],"audio_muted":view.audio_clips[0].get("muted",false),"text_drawn_after_waveform":true}))
	for i in range(fine.size()):
		if fine[i]<=0:continue
		var point: Vector2=view.global_position+Vector2(maxf(view.x(float(i)/fine.size()*view.duration),view.audio_rect(0).position.x),view.audio_y()+14)
		var diagnostic_raw_x: float=view.x(float(i)/fine.size()*view.duration)
		var diagnostic_right_x: float=view.x(float(i+1)/fine.size()*view.duration)
		var diagnostic_border: bool=view.audio_selected==0 and diagnostic_raw_x<=diagnostic_clip_rect.position.x
		var diagnostic: Dictionary={"format":"has_waveform_transient_sample_1","index":i,"value":fine[i],"raw_x":diagnostic_raw_x,"renderer_right_x":diagnostic_right_x,"renderer_culled_by_clip":diagnostic_right_x<=diagnostic_clip_rect.position.x or diagnostic_raw_x>=diagnostic_clip_rect.end.x,"amplitude":fine[i]*11,"clip_rect":[diagnostic_clip_rect.position.x,diagnostic_clip_rect.position.y,diagnostic_clip_rect.size.x,diagnostic_clip_rect.size.y],"global_point":[point.x,point.y],"integer_point":[Vector2i(point).x,Vector2i(point).y],"selected_left_border":diagnostic_border,"neon":neon_style,"selected_audio":view.audio_selected}
		# Check all nine pixels before reading any, and prove they belong to the visible tracks.
		var sample_pixels:=Rect2i(Vector2i(point)-Vector2i.ONE,Vector2i(3,3))
		var sample_region:=Rect2(Vector2(sample_pixels.position),Vector2(sample_pixels.size))
		if not image_bounds.encloses(sample_pixels) or not tracks_scroll.get_global_rect().encloses(sample_region) or not dock_scroll.get_global_rect().encloses(sample_region):
			sample_bounds_valid=false
			diagnostic["sample_bounds_valid"]=false
			diagnostic["expected_rgb"]=[neon_border.r,neon_border.g,neon_border.b] if neon_style and diagnostic_border else [neon_body.r,neon_body.g,neon_body.b] if neon_style else [green.r,green.g,green.b]
			diagnostic["found"]=false;diagnostic["samples"]=[]
			print("WAVEFORM_TRANSIENT_DIAGNOSTIC ",JSON.stringify(diagnostic))
			continue
		if neon_style:
			# The sample-zero transient clamps to the selected clip's one-pixel left border.
			# The other transients are in its translucent fill. Select by draw geometry only.
			var on_selected_left_border: bool=view.audio_selected==0 and view.x(float(i)/fine.size()*view.duration)<=view.audio_rect(0).position.x
			green=neon_border if on_selected_left_border else neon_body
		var found:=false
		var diagnostic_pixels: Array=[]
		for dx in range(-1,2):
			for dy in range(-1,2):
				var pixel:=screen.get_pixelv(Vector2i(point)+Vector2i(dx,dy))
				diagnostic_pixels.append({"offset":[dx,dy],"rgb":[pixel.r,pixel.g,pixel.b],"alpha":pixel.a})
				if absf(pixel.r-green.r)<.02 and absf(pixel.g-green.g)<.02 and absf(pixel.b-green.b)<.02:found=true
		diagnostic["sample_bounds_valid"]=true;diagnostic["expected_rgb"]=[green.r,green.g,green.b];diagnostic["found"]=found;diagnostic["samples"]=diagnostic_pixels
		print("WAVEFORM_TRANSIENT_DIAGNOSTIC ",JSON.stringify(diagnostic))
		if found:bars+=1
	check(sample_bounds_valid,"all waveform sample neighborhoods lie inside the image and both visible track viewports")
	check(bars==4,"actual zoomed viewport displays all four independent transient bars")
	var old: Dictionary=app.audio_document().duplicate(true);app.audio_clip.muted=true;app.commit_audio(old);await settled()
	check(view.visible_waveform(0).count(0.0)==8192,"mute rebuilds zero cached detail")
	app.undo();await settled();check(pcm==signature(app.audio_mix.pcm) and peaks_sha==signature(view.visible_waveform(0).to_byte_array()),"mute Undo restores exact PCM and detailed peaks")
	old=app.audio_document().duplicate(true);app.audio_clip.gain_db=-6;app.commit_audio(old);await settled()
	check(absf(peak_value(view.visible_waveform(0))-peak_value(fine)*db_to_linear(-6))<.0001,"gain edit updates actual quantized waveform amplitude")
	app.undo();await settled();check(pcm==signature(app.audio_mix.pcm) and peaks_sha==signature(view.visible_waveform(0).to_byte_array()),"gain Undo restores original detail and PCM")
	nav.fit_all();await settled();check(view.visible_waveform(0).size()==256,"Fit restores existing overview resolution")
	DirAccess.rename_absolute(wav+".offline",wav);check(FileAccess.get_sha256(wav)==source_sha,"source WAV remains byte-identical")
	print("WAVEFORM_LEVELS_SMOKE ",JSON.stringify({"checks":checks,"failures":failures,"drawn_transients":bars,"fine_payload_bytes":fine.size()*4}));await app.quit_studio();quit(0 if failures==0 else 1)
