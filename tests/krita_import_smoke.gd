extends SceneTree
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
const Clip=preload("res://src/raster_clip.gd")
var app
var checks:=0
var failures:=0
func equal(a,b) -> bool:
	return JSON.parse_string(JSON.stringify(a,"",true,true))==JSON.parse_string(JSON.stringify(b,"",true,true))
func _initialize() -> void:
	create_timer(170).timeout.connect(func():push_error("Krita import watchdog");quit(2));call_deferred("run")
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func settle() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func click(control: Control) -> void:
	var window: Window=control.get_window();var position:=control.get_global_rect().get_center()
	if window.is_embedded():position+=Vector2(window.position)
	var target: Window=root if window.is_embedded() else window
	var motion:=InputEventMouseMotion.new();motion.position=position;target.push_input(motion,true)
	for down in [true,false]:
		var e:=InputEventMouseButton.new();e.position=position;e.button_index=MOUSE_BUTTON_LEFT;e.pressed=down;target.push_input(e,true);await process_frame
	await settle()
func wait_phase(expected: String) -> void:
	while app.raster_importer.phase!=expected and not app.raster_importer.phase.is_empty():await process_frame
	await settle()
func wait_save() -> void:
	while app.has_project.pid>0:await process_frame
	await settle()
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0];var reading: bool="--read" in args
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery-cold" if reading else "recovery");app.recent_path=folder.path_join("recent.json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache-cold" if reading else "cache")
	var importer=app.raster_importer;var packed:=folder.path_join("Krita scene.has")
	if reading:
		app.has_project.open_file(packed);await wait_save();var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
		check(app.layers.size()==3 and app.layers[2].cels.size()==8 and app.layers[2].origin==expected.origin,"cold packed HAS restores eight editable holds and portable ancestry")
		check(Storage.image_hash(Drawing.cel_at(app.layers[2],12).image)==expected.paint and Storage.image_hash(await app.renderer.capture(app.keys,app.layers,12,true))==expected.render,"cold imported frame and composite are exact")
		check(not app.layers[2].origin.has("path"),"cold ancestry has no required external native path")
		var recovered:=Storage.load_project(folder.path_join("import-recovery/imported"));check(not recovered.has("error") and equal(recovered.layers[2].origin,expected.origin) and Storage.image_hash(Drawing.cel_at(recovered.layers[2],12).image)==expected.paint,"fresh process restores recovery ancestry and exact imported pixels")
		app.has_project.save_file(folder.path_join("Krita scene linked.has"),"linked");await wait_save()
		check(FileAccess.file_exists(folder.path_join("Krita scene linked.has")),"linked HAS still embeds imported drawing pixels")
		print("KRITA_IMPORT_READ ",JSON.stringify({"checks":checks,"failures":failures}));app.free();quit(0 if failures==0 else 1);return
	check(app.load_demo_room(),"original 3D room loads")
	app.mode.select(0);app.change_mode(0);app.set_frame(0);root.size=Vector2i(1280,800);app.set_advanced(false);await settle()
	var original:=Drawing.blank(1920,1080);original.fill_rect(Rect2i(800,400,120,90),Color.CYAN);Drawing.insert(app.layers[1],0,48,original);app.changed();app.history.clear();app.redo_history.clear();app.history_bytes=0
	var oldpixels:=Storage.image_hash(original);var keys: Array=app.keys.duplicate(true);var world: Dictionary=app.current_world().duplicate(true);var source:=FileAccess.get_sha256(app.source)
	app.inspector_scroll.ensure_control_visible(importer.launch);await settle();await click(importer.launch)
	var picker: FileDialog
	for child in app.get_children():
		if child is FileDialog and child.visible:picker=child
	check(picker!=null,"actual Simple import button opens a KRA file chooser")
	if picker:picker.hide();picker.queue_free()
	importer.begin(args[1]);await wait_phase("layers")
	check(importer.phase=="layers" and importer.inventory.layers.size()==19,"actual async KRA inspection exposes native layer review")
	if importer.phase!="layers":print(app.status.text);app.free();quit(1);return
	check(not importer.review.exclusive and importer.review.visible and app.history.is_empty(),"layer review stays nonexclusive with no scene edit")
	var id:="{afd6e736-c189-4c60-b0f5-a4892a32902c}"
	check(importer.choices.has(id) and importer.choices[id].check.button_pressed,"native background is initially retained")
	# Reveal layer list, then route a real checkbox click.
	# Locate its actual containing scroll independent of Window's internal children.
	var checkbox: CheckBox=importer.choices[id].check
	var scroll: ScrollContainer=checkbox.get_parent().get_parent();scroll.show();await settle();scroll.ensure_control_visible(checkbox);await settle()
	root.get_texture().get_image().save_png(folder.path_join("krita-layers-before-click.png"));print("CHECKBOX_RECT ",checkbox.get_global_rect()," SCROLL ",scroll.get_global_rect()," WIN ",importer.review.position," SIZE ",importer.review.size)
	await click(checkbox)
	check(not checkbox.button_pressed,"actual source-layer checkbox explicitly hides background in scratch render")
	app.set_advanced(true);await settle();check(not checkbox.button_pressed and app.history.is_empty(),"Advanced presentation preserves reviewed layer policy")
	await click(importer.review.get_ok_button());await wait_phase("candidate")
	check(importer.phase=="candidate" and importer.decoded.size()==8,"actual hidden native preparation yields eight reviewed editable holds")
	if importer.phase!="candidate":print(app.status.text);app.free();quit(1);return
	check(app.layers.size()==2 and app.keys==keys and app.current_world()==world and Storage.image_hash(original)==oldpixels,"prepared candidate leaves 3D, camera and original overlay untouched")
	check(importer.candidate.origin.visibility.get(id)==false and equal(importer.candidate.origin.range,[0,47]),"candidate retains explicit policy and inclusive source range")
	importer.scrub.value=12;await settle();check(app.frame==0,"preview scrubbing never seeks main scene")
	root.get_texture().get_image().save_png(folder.path_join("krita-review.png"))
	var native_job: String=importer.job;var sha: String=importer.inventory.source_sha256
	await click(importer.preview.get_ok_button())
	check(app.layers.size()==3 and app.layers[2].cels.size()==8 and app.history.size()==1,"actual Add commits one new layer with one Undo")
	var imported: Dictionary=app.layers[2];var paint:=Storage.image_hash(Drawing.cel_at(imported,12).image);var origin: Dictionary=imported.origin.duplicate(true)
	app.undo();check(app.layers.size()==2 and Storage.image_hash(original)==oldpixels and app.keys==keys and app.current_world()==world,"Undo removes import without touching other authored content")
	app.redo();check(app.layers.size()==3 and is_same(app.layers[2],imported) and Storage.image_hash(Drawing.cel_at(imported,12).image)==paint,"Redo restores same independent editable Images")
	var packet: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(native_job.path_join("prepared/clip.json")))
	var invalid: Dictionary=packet.duplicate(true);invalid.holds[0].path="../outside.png"
	check(Clip.validate(invalid,native_job.path_join("prepared"),app.video,0,32,sha).has("error"),"packet traversal refuses")
	invalid=packet.duplicate(true);invalid.holds[1].start=0;check(Clip.validate(invalid,native_job.path_join("prepared"),app.video,0,32,sha).has("error"),"packet timing overlap refuses")
	check(Clip.validate(packet,native_job.path_join("prepared"),app.video,0,1,sha).has("error"),"packet cel budget refuses")
	for change in [{"duration_frames":0},{"fit":[]},{"fps_num":25},{"source":{}},{"holds":[null]}]:
		invalid=packet.duplicate(true).merged(change,true);check(Clip.validate(invalid,native_job.path_join("prepared"),app.video,0,32,sha).has("error"),"malformed prepared dimensions/source/holds refuse")
	var recovery: String=folder.path_join("import-recovery")
	var recovery_error:=preload("res://src/recovery.gd").checkpoint(recovery,"imported",app.video,app.keys,app.layers,app.source,app.frame,app.audio_document(),"",app.recovery_revision,app.renderer.model_state(),app.renderer.world_state(),app.palette)
	var restored:=Storage.load_project(recovery.path_join("imported"))
	check(recovery_error.is_empty() and not restored.has("error") and equal(restored.layers[2].origin,origin) and Storage.image_hash(Drawing.cel_at(restored.layers[2],12).image)==paint,"actual recovery storage retains original ancestry and imported pixels")
	var render: Image=await app.renderer.capture(app.keys,app.layers,12,true)
	app.has_project.save_file(packed,"packed");await wait_save();check(app.has_project.path==packed,"ordinary HAS saves normalized import")
	var error: String=await app.export_movie(folder);check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000013.png")).get_data()==render.get_data(),"real MP4 frame equals shared 3D/camera/imported drawing preview")
	check(FileAccess.get_sha256(args[1])==sha and FileAccess.get_sha256(app.source)==source,"owner native artwork and 3D source stay unchanged")
	# Re-enter a real inspection then invalidate by seeking. No prepared layer leaks.
	app.undo();app.set_frame(0);importer.begin(args[1]);app.set_frame(1);await wait_phase("")
	check(importer.phase.is_empty() and importer.pid<0 and app.layers.size()==2,"frame change cancels async source review without late adoption")
	app.set_frame(0);importer.begin(args[1]);await wait_phase("layers");importer.cancel();check(importer.phase.is_empty() and app.layers.size()==2,"Cancel from layer review adds nothing")
	importer.begin(args[1]);app.changed();await wait_phase("");check(app.layers.size()==2 and importer.pid<0,"authored revision cancels old inspection")
	var copy:=folder.path_join("changed-source.kra");DirAccess.copy_absolute(args[1],copy);importer.begin(copy);await wait_phase("layers")
	var changed:=FileAccess.open(copy,FileAccess.READ_WRITE);changed.seek_end();changed.store_8(0);changed.close();importer.prepare();await wait_phase("")
	check(app.layers.size()==2 and "changed" in app.status.text.to_lower(),"source changed after layer review refuses before native rendering")
	importer.begin(args[1]);await wait_phase("layers");importer.prepare();var cancelled_job: String=importer.job
	var deadline:=Time.get_ticks_msec()+20000
	while importer.phase=="prepare" and Time.get_ticks_msec()<deadline:
		var native:=cancelled_job.path_join("prepared/native")
		if DirAccess.dir_exists_absolute(native) and not DirAccess.get_files_at(native).is_empty():break
		await process_frame
	if is_instance_valid(importer.progress):await click(importer.progress.get_ok_button())
	await wait_phase("");check(app.layers.size()==2 and importer.pid<0 and not FileAccess.file_exists(cancelled_job.path_join("prepared/clip.json")),"actual progress Cancel drains native render with no late clip or layer")
	importer.begin(args[1]);app.new_project();await wait_phase("");check(importer.pid<0 and app.layers.size()==2 and app.layers[0].cels.is_empty() and app.layers[1].cels.is_empty(),"New scene cancels old inspection without late import")
	FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify({"paint":paint,"origin":origin,"render":Storage.image_hash(render)},"",true,true))
	var report:={"checks":checks,"failures":failures,"movie":app.last_export_folder.path_join("movie.mp4"),"native_job":native_job,"cancelled_job":cancelled_job};print("KRITA_IMPORT_SMOKE ",JSON.stringify(report));app.free();quit(0 if failures==0 else 1)
