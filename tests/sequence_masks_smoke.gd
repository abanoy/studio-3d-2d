extends SceneTree
const Graph=preload("res://src/sequence_graph.gd")
const Drawing=preload("res://src/drawing.gd")
const Recovery=preload("res://src/recovery.gd")
const Storage=preload("res://src/storage.gd")
var app
var editor
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(230).timeout.connect(func():push_error("Sequence masks watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settle() -> void:
	for i in range(5):await process_frame
	await RenderingServer.frame_post_draw
func job() -> void:
	while app.has_project.pid>0:await process_frame
	await settle()
func picture() -> Image:return await editor.runtime.render("",0,true)
func crop_mask(clip: Dictionary) -> bool:
	var mask: Dictionary=clip.get("mask",{})
	if mask.is_empty() or mask.invert:return false
	var r: Array=mask.rect
	return Rect2i(int(r[0]),int(r[1]),int(r[2]),int(r[3]))==Rect2i(800,400,50,100)
func apply_panel(label: String) -> void:
	for button in editor.panel.find_children("","Button",true,false):
		if button.text==label:button.pressed.emit();break
	await settle()
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0]
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache");editor=app.sequence_editor
	if "--read" in args:
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
		for mode in ["packed","linked"]:
			app.has_project.open_file(folder.path_join("Masks "+mode+".has"));await job()
			check(app.has_project.path==folder.path_join("Masks "+mode+".has") and editor.graph.get("format")==Graph.MASK_FORMAT and editor.graph.clips.size()==2 and editor.graph.clips.all(crop_mask),"cold "+mode+" HAS retains exact masks on split clips")
			editor.show_panel();await settle();var history: int=app.history.size();await apply_panel("Apply mask");editor.close_panel();check(app.history.size()==history,"cold whole-number JSON mask remains unchanged on inspector Apply")
			var image: Image=await picture();check(absf(image.get_pixel(825,450).a-.25)<.015 and image.get_pixel(875,450).a==0 and image.get_pixel(995,450).a==0,"cold mask and shadow reproduce clipped silhouette")
			check(Storage.image_hash(editor.graph.assets[0].scene.layers[1].cels[0].image)==expected.source and app.audio_mix.pcm==Marshalls.base64_to_raw(expected.audio),"cold reopen retains full editable source artwork and exact child sound")
		check(app.restore_checkpoint({"folder":folder.path_join("mask-recovery/test"),"manifest":"project.json","recovery":true}),"ordinary recovery restores graph3 masks and source assets")
		var recovered: Image=await picture();check(recovered.get_pixel(875,450).a==0 and app.audio_mix.pcm==Marshalls.base64_to_raw(expected.audio),"recovery keeps cropped appearance and synchronized editable audio")
		print("SEQUENCE_MASKS_READ ",JSON.stringify({"checks":checks,"failures":failures}));await app.quit_studio();quit(0 if failures==0 else 1);return
	check(app.load_demo_room(),"original parent world loads for actual masked composition")
	var parent: Dictionary=app.current_world().duplicate(true);var shots: Array=app.keys.duplicate(true)
	var asset: String=editor.new_sequence("Masked artwork");check(not asset.is_empty() and editor.enter(asset).is_empty(),"editable child opens without rasterizing parent world")
	app.mode.select(0);app.change_mode(0);app.active_layer=1;app.refresh_layer();app.create_cel(false)
	var cel: Dictionary=app.layers[1].cels[0];cel.duration=48;cel.image.fill_rect(Rect2i(800,400,100,100),Color(1,0,0,.5));app.changed();var original: PackedByteArray=cel.image.get_data()
	var cue:=ProjectSettings.globalize_path("res://examples/tutorials/Practice cue.wav");var cue_hash:=FileAccess.get_sha256(cue)
	check(app.import_audio(cue,6).is_empty(),"editable child sound starts at frame6 independently of mask")
	editor.return_to_parent();await settle();var id: String=editor.graph.clips[0].id
	var keys: Array=editor.find_clip(id).keys.duplicate(true);keys[0].opacity=.5;editor.change_clip(id,{"keys":keys})
	editor.change_shadow(id,{"offset":[120,0],"color":[0,0,0,.5],"softness":0})
	var full: Image=await picture();var pcm: PackedByteArray=app.audio_mix.pcm.duplicate();var history: int=app.history.size()
	check(editor.change_mask(id,{}).is_empty() and editor.graph.format==Graph.SHADOW_FORMAT and app.history.size()==history,"disabled-mask no-op preserves graph2 and history")
	var crop:={"rect":[800,400,50,100],"invert":false}
	check(editor.change_mask(id,crop).is_empty() and editor.graph.format==Graph.MASK_FORMAT,"first picture mask explicitly promotes graph with strict clip fields")
	var cropped: Image=await picture()
	check(absf(cropped.get_pixel(825,450).a-.25)<.015 and cropped.get_pixel(875,450).a==0 and absf(cropped.get_pixel(945,450).a-.125)<.015 and cropped.get_pixel(995,450).a==0,"actual crop and shadow preserve alpha while removing right half")
	check(cel.image.get_data()==original and app.audio_mix.pcm==pcm,"mask changes preserve full source pixels and exact nested sound")
	app.undo();await settle();var undone: Image=await picture();check(editor.graph.format==Graph.SHADOW_FORMAT and undone.get_data()==full.get_data(),"one Undo restores old graph version and exact full picture")
	app.redo();await settle();var redone: Image=await picture();check(editor.graph.format==Graph.MASK_FORMAT and redone.get_data()==cropped.get_data(),"Redo restores mask without flattening child artwork")
	editor.show_panel();await settle();var inverted: CheckButton
	for node in editor.panel.find_children("","CheckButton",true,false):
		if node.text=="Cut out this rectangle instead":inverted=node
	check(inverted!=null and not inverted.button_pressed,"actual browser exposes crop-versus-cutout control")
	if inverted:inverted.button_pressed=true
	await apply_panel("Apply mask");var cutout: Image=await picture()
	check(cutout.get_pixel(825,450).a==0 and absf(cutout.get_pixel(875,450).a-.25)<.015 and absf(cutout.get_pixel(995,450).a-.125)<.015,"actual Apply mask control cuts a hole and updates the shadow")
	history=app.history.size();await apply_panel("Apply mask");check(app.history.size()==history,"unchanged mask inspector is an honest no-op")
	editor.close_panel();editor.change_shadow(id,{"offset":[120,0],"color":[0,0,0,.5],"softness":8})
	check(editor.graph.format==Graph.MASK_FORMAT and editor.find_clip(id).mask.invert,"editing a shadow preserves graph3 mask contract")
	var before: Dictionary=editor.clone_graph();history=app.history.size()
	check(not editor.change_mask(id,{"rect":[1919,0,2,1],"invert":false}).is_empty() and editor.graph==before and app.history.size()==history,"mask outside child canvas refuses atomically")
	editor.show_panel();await settle()
	for node in editor.panel.find_children("","CheckButton",true,false):
		if node.text=="Picture mask":node.button_pressed=false
	await apply_panel("Apply mask");var disabled: Image=await picture()
	check(editor.find_clip(id).mask.is_empty() and absf(disabled.get_pixel(825,450).a-.25)<.015 and absf(disabled.get_pixel(875,450).a-.25)<.015,"actual mask disable restores full editable picture")
	editor.close_panel();var extra: String=editor.new_sequence("Unmasked")
	check(not extra.is_empty() and editor.graph.clips[-1].mask.is_empty() and editor.graph.clips[-1].shadow.is_empty(),"new instance in graph3 carries explicit disabled mask/shadow defaults")
	editor.remove_clip(editor.graph.clips[-1].id);editor.remove_asset(extra);editor.change_mask(id,crop)
	editor.copy_clip(id);check(editor.paste_clip().is_empty(),"copy/paste retains editable instance mask")
	var peer: String=editor.graph.clips[-1].id;var placed: Array=editor.find_clip(peer).keys.duplicate(true);placed[0].offset=[400,0];editor.change_clip(peer,{"keys":placed})
	editor.change_mask(id,{"rect":[800,400,50,100],"invert":true});var separate: Image=await picture()
	check(separate.get_pixel(825,450).a==0 and absf(separate.get_pixel(875,450).a-.25)<.015 and absf(separate.get_pixel(1225,450).a-.25)<.015 and separate.get_pixel(1275,450).a==0,"shared child instances keep independent crop and cutout masks")
	check(editor.runtime.frames.size()==1 and editor.runtime.masked_frames.size()==2,"masked texture cache stays per instance while sharing source picture")
	editor.remove_clip(peer);editor.change_mask(id,crop);check(editor.split_clip(id,24).is_empty() and editor.graph.clips.all(func(c):return c.mask==crop),"timeline split retains mask on both source windows")
	check(app.audio_mix.pcm==pcm and cel.image.get_data()==original and app.current_world()==parent and app.keys==shots and FileAccess.get_sha256(cue)==cue_hash,"mask/copy/split operations preserve original scene, camera, source artwork and sound")
	for mode in ["packed","linked"]:
		app.has_project.save_file(folder.path_join("Masks "+mode+".has"),mode);await job();check(FileAccess.file_exists(folder.path_join("Masks "+mode+".has")),"normal "+mode+" HAS saves editable mask graph and child sound")
	var snapshot: Dictionary=app.project_snapshot();var error:=Recovery.checkpoint(folder.path_join("mask-recovery"),"test",snapshot.video,snapshot.camera_keys,snapshot.layers,"",0,snapshot.audio,"",app.recovery_revision,{},snapshot.world,snapshot.palette,snapshot.sequence_graph)
	check(error.is_empty(),"ordinary recovery writer retains mask metadata and original child source")
	var composite: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	var movie_error: String=await app.export_movie(folder);var movie: String=app.last_finished_movie
	check(movie_error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000001.png")).get_data()==composite.get_data(),"actual MP4 uses exact parent world plus masked child and shadow")
	var png_error: String=await app.export_images(folder,true);var png: String=app.last_export_folder.path_join("frame_000001.png");var image:=Image.load_from_file(png)
	check(png_error.is_empty() and image.get_pixel(0,0).a==0 and absf(image.get_pixel(825,450).a-.25)<.015 and image.get_pixel(875,450).a==0,"transparent drawing-only PNG shares masks/shadows while excluding parent world")
	var expected:={"source":Storage.image_hash(cel.image),"audio":Marshalls.raw_to_base64(pcm)};FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify(expected))
	print("SEQUENCE_MASKS_SMOKE ",JSON.stringify({"checks":checks,"failures":failures,"movie":movie,"png":png}));await app.quit_studio();quit(0 if failures==0 else 1)
