extends "res://tests/movement_path_smoke.gd"
const SheetData=preload("res://src/reference_sheet_data.gd")
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
func _initialize() -> void:
	create_timer(220).timeout.connect(func():push_error("Project reference watchdog");quit(2));call_deferred("run")
func run() -> void:
	var args:=OS.get_cmdline_user_args();folder=args[0];app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("reader-has-cache" if "--read" in args else "writer-has-cache")
	var sheet=app.reference_sheet;sheet.cache_root=folder.path_join("reader-sheet-cache" if "--read" in args else "writer-sheet-cache")
	if "--read" in args:
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
		for kind in ["Legacy packed","Legacy linked","Nested packed","Nested linked"]:
			var path:=folder.path_join(kind+".has");app.has_project.open_file(path);await wait_job()
			check(app.has_project.path==path and sheet.document().sha256==expected.reference and sheet.image!=null,"cold "+kind+" restores kept PNG without original or writer cache")
			check(Storage.image_hash(sheet.image)==expected.pixels and not sheet.guide.visible,"cold "+kind+" retains exact reference alpha with guide initially off")
			var image: Image=await app.renderer.capture(app.keys,app.layers,0,true)
			check(image.get_data()==Image.load_from_file(folder.path_join("nested.png" if kind.begins_with("Nested") else "legacy.png")).get_data(),"cold "+kind+" repeats exact scene/ink pixels with reference excluded")
		check(app.audio_mix.pcm==Marshalls.base64_to_raw(expected.audio),"cold nested source preserves exact synchronized PCM")
		var previous_path: String=app.has_project.path;var previous_document: Dictionary=sheet.document();var previous_world: Dictionary=app.current_world().duplicate(true);var previous_pixels: PackedByteArray=sheet.image.get_data()
		app.has_project.open_file(folder.path_join("Invalid PNG.has"));await wait_job()
		check(app.has_project.path==previous_path and sheet.document()==previous_document and sheet.image.get_data()==previous_pixels and app.current_world()==previous_world,"invalid kept PNG refuses Open without replacing current identity world or reference")
		print("REFERENCE_PROJECT_READ ",JSON.stringify({"checks":checks,"failures":failures}));await app.quit_studio();quit(0 if failures==0 else 1);return
	check(app.load_demo_room(),"legacy practice scene opens before any reference upgrade")
	var original:=Image.create(128,64,false,Image.FORMAT_RGBA8);original.fill(Color(1,.25,.5,.5));original.fill_rect(Rect2i(64,0,64,64),Color(.1,.8,.2,.75))
	var png:=folder.path_join("Original sheet α.png");original.save_png(png);var original_hash:=FileAccess.get_sha256(png)
	sheet.open();await settled();check(sheet.load_sheet(png).is_empty(),"local sheet previews before choosing project ownership")
	var history: int=app.history.size();var revision: int=app.recovery_revision;sheet.keep.button_pressed=true;await settled()
	check(not sheet.document().is_empty() and app.history.size()==history+1 and app.recovery_revision>revision,"Keep PNG in project commits exactly one document Undo and marks dirty")
	var kept: Dictionary=sheet.document();check(kept.source!=png and FileAccess.get_sha256(kept.source)==original_hash,"kept source is an immutable verified managed PNG copy")
	app.undo();await settled();check(sheet.document().is_empty() and sheet.image.get_data()==original.get_data() and not sheet.keep.button_pressed,"Undo Keep returns sheet to session-only without discarding its pixels")
	app.redo();await settled();check(sheet.document()==kept and sheet.keep.button_pressed,"Redo Keep restores exact reference identity")
	var replacement:=original.duplicate();replacement.fill(Color.BLUE);var revised:=folder.path_join("Replacement.png");replacement.save_png(revised);history=app.history.size()
	check(sheet.load_sheet(revised).is_empty() and app.history.size()==history+1 and sheet.source_hash!=original_hash,"replacing a kept sheet is one versioned Undo action")
	DirAccess.rename_absolute(png,png+".offline");app.undo();await settled();check(sheet.document()==kept and sheet.image.get_data()==original.get_data(),"Undo replacement uses the managed PNG even while original is unavailable")
	app.redo();await settled();check(sheet.image.get_data()==replacement.get_data(),"Redo replacement restores new reference pixels")
	app.undo();await settled();DirAccess.rename_absolute(png+".offline",png)
	history=app.history.size();sheet.clear();check(sheet.document().is_empty() and sheet.image==null and app.history.size()==history+1,"Clear removes kept reference in one Undo action")
	app.undo();await settled();check(sheet.document()==kept and sheet.image.get_data()==original.get_data(),"Undo Clear restores complete reference and original alpha")
	sheet.keep.button_pressed=false;await settled();check(sheet.document().is_empty() and sheet.image!=null,"unchecking Keep retains session reference without project ownership")
	app.undo();await settled();check(sheet.document()==kept,"Undo uncheck restores project reference")
	sheet.overlay_toggle.button_pressed=true;sheet.opacity.value=50;sheet.window.hide();app.mode.select(0);app.change_mode(0);app.set_frame(0);app.create_cel(false);Drawing.stroke(Drawing.cel_at(app.layers[1],0).image,Vector2(80,80),Vector2(180,80),5,Color.CYAN,false);app.changed()
	var cue:=ProjectSettings.globalize_path("res://examples/tutorials/Practice cue.wav");check(app.import_audio(cue,6).is_empty(),"synchronized sound remains independent of reference ownership")
	var pcm: PackedByteArray=app.audio_mix.pcm.duplicate();var legacy: Image=await app.renderer.capture(app.keys,app.layers,0,true);legacy.save_png(folder.path_join("legacy.png"))
	for mode in ["packed","linked"]:
		var path:=folder.path_join("Legacy "+mode+".has");app.has_project.save_file(path,mode);await wait_job();check(app.has_project.path==path,"schema7 legacy "+mode+" HAS commits with kept reference")
	var editor=app.sequence_editor;var child: String=editor.new_sequence("Child artwork");check(not child.is_empty() and editor.enter(child).is_empty(),"editable nested scene opens while enclosing project keeps its reference")
	check(sheet.document()==kept,"enclosing reference remains shared while editing child scene")
	app.mode.select(0);app.change_mode(0);app.set_frame(0);app.create_cel(false);Drawing.cel_at(app.layers[1],0).image.fill_rect(Rect2i(800,400,80,80),Color.GREEN);Drawing.touch(Drawing.cel_at(app.layers[1],0).image);app.changed();editor.return_to_parent();await settled()
	var nested: Image=await app.renderer.capture(app.keys,app.layers,0,true);nested.save_png(folder.path_join("nested.png"));check(app.audio_mix.pcm==pcm,"nested reference workflow keeps exact parent sound mix")
	for mode in ["packed","linked"]:
		var path:=folder.path_join("Nested "+mode+".has");app.has_project.save_file(path,mode);await wait_job();check(app.has_project.path==path,"schema7 nested "+mode+" HAS includes reference and editable child")
	var error: String=await app.export_movie(folder);check(error.is_empty() and nested.get_data()==Image.load_from_file(app.last_export_folder.path_join("frame_000001.png")).get_data(),"real MP4 preserves complete nested picture while excluding kept reference guide")
	var movie: String=app.last_export_folder.path_join("movie.mp4");check(FileAccess.get_sha256(png)==original_hash,"original user PNG remains byte-identical through save and export")
	check(editor.enter(child).is_empty(),"child opens for crash recovery of reference plus editor context");app.set_frame(6);app.changed()
	while app.recovery_preview.busy():app.poll_recovery_preview();await process_frame
	app.autosave_tick(true);check(app.checkpoint_revision==app.recovery_revision,"ordinary autosave commits reference and active child before abrupt exit")
	var expected:={"reference":original_hash,"pixels":Storage.image_hash(original),"audio":Marshalls.raw_to_base64(pcm),"child":child,"recovery":app.recovery_session}
	FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify(expected,"",true,true))
	app.tree_exiting.connect(func():FileAccess.open(folder.path_join("graceful-exit.txt"),FileAccess.WRITE).store_string("unexpected graceful hook"))
	print("REFERENCE_PROJECT_SMOKE ",JSON.stringify({"checks":checks,"failures":failures,"movie":movie}))
	if "--crash" in args:
		OS.kill(OS.get_process_id());FileAccess.open(folder.path_join("kill-returned.txt"),FileAccess.WRITE).store_string("unexpected return");quit(2);return
	await app.quit_studio();quit(0 if failures==0 else 1)
