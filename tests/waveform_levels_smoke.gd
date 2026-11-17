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
	# Godot 4.6 StyleBoxFlat outer feather: alpha 0 at L-a/2, alpha 1 at L+a/2.
	# Keep this narrow oracle in unscaled, non-HDR, non-MSAA viewport coordinates.
	var vp: Viewport=app.get_viewport()
	var unit_basis: bool=view.get_global_transform_with_canvas().x.is_equal_approx(Vector2.RIGHT) and view.get_global_transform_with_canvas().y.is_equal_approx(Vector2.DOWN)
	var raster_conditions_valid: bool=not neon_style or (Engine.get_version_info().get("hash","").begins_with("89cea1439") and unit_basis and vp.get_final_transform().is_equal_approx(Transform2D.IDENTITY) and is_equal_approx(vp.get_oversampling(),1.0) and is_equal_approx(app.get_window().content_scale_factor,1.0) and not vp.snap_2d_transforms_to_pixel and not vp.snap_2d_vertices_to_pixel and vp.msaa_2d==Viewport.MSAA_DISABLED and not vp.use_hdr_2d and not vp.transparent_bg)
	var selected_box: StyleBoxFlat=view.neon_box("audio_selected") if neon_style else null
	if neon_style:
		raster_conditions_valid=raster_conditions_valid and selected_box.anti_aliasing and is_equal_approx(selected_box.anti_aliasing_size,1.0) and selected_box.border_width_left==1 and not selected_box.border_blend and selected_box.skew.is_zero_approx() and selected_box.shadow_size==0 and selected_box.expand_margin_left==0.0 and selected_box.bg_color==Color(0.239,0.863,0.592,0.12) and selected_box.border_color==Color("3ddc97")
	var sample_bounds_valid:=true
	var image_bounds:=Rect2i(Vector2i.ZERO,screen.get_size())
	for i in range(fine.size()):
		if fine[i]<=0:continue
		var point: Vector2=view.global_position+Vector2(maxf(view.x(float(i)/fine.size()*view.duration),view.audio_rect(0).position.x),view.audio_y()+14)
		# Check all nine pixels before reading any, and prove they belong to the visible tracks.
		var sample_pixels:=Rect2i(Vector2i(point)-Vector2i.ONE,Vector2i(3,3))
		var sample_region:=Rect2(Vector2(sample_pixels.position),Vector2(sample_pixels.size))
		if not image_bounds.encloses(sample_pixels) or not tracks_scroll.get_global_rect().encloses(sample_region) or not dock_scroll.get_global_rect().encloses(sample_region):
			sample_bounds_valid=false
			continue
		if neon_style:
			green=neon_body
			var clip_rect: Rect2=view.audio_rect(0)
			var on_selected_left_border: bool=view.audio_selected==0 and view.x(float(i)/fine.size()*view.duration)<=clip_rect.position.x
			if on_selected_left_border:
				var clip_global:=Rect2(view.global_position+clip_rect.position,clip_rect.size)
				var aa: float=selected_box.anti_aliasing_size
				var center:=Vector2(Vector2i(point))+Vector2(0.5,0.5)
				var coverage: float=(center.x-(clip_global.position.x-aa*0.5))/aa
				# Refuse curved corners, infill/inner-AA overlap and a sample outside this feather.
				var straight_top: float=clip_global.position.y+maxi(selected_box.corner_radius_top_left,selected_box.corner_radius_top_right)+aa
				var straight_bottom: float=clip_global.end.y-maxi(selected_box.corner_radius_bottom_left,selected_box.corner_radius_bottom_right)-aa
				var edge_valid: bool=raster_conditions_valid and coverage>=0.0 and coverage<=1.0 and center.x<clip_global.position.x+selected_box.border_width_left and sample_region.position.y>=straight_top and sample_region.end.y<=straight_bottom
				if not edge_valid:
					raster_conditions_valid=false
					continue
				var feather:=selected_box.border_color
				feather.a*=coverage
				green=Color("0c0d11").blend(feather).blend(neon_wave)
		var found:=false
		for dx in range(-1,2):
			for dy in range(-1,2):
				var pixel:=screen.get_pixelv(Vector2i(point)+Vector2i(dx,dy))
				if absf(pixel.r-green.r)<.02 and absf(pixel.g-green.g)<.02 and absf(pixel.b-green.b)<.02:found=true
		if found:bars+=1
	check(raster_conditions_valid,"Neon waveform edge oracle uses supported unscaled non-HDR non-MSAA straight-edge raster conditions")
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
