extends SceneTree
const Recovery=preload("res://src/recovery.gd")
const Journal=preload("res://src/recovery_journal.gd")
const Storage=preload("res://src/storage.gd")
const Drawing=preload("res://src/drawing.gd")
const SceneIO=preload("res://src/scene3d.gd")
const Model=preload("res://src/model.gd")
var checks:=0
var failures:=0
var tested_app
func _initialize() -> void:
	create_timer(200).timeout.connect(func():push_error("Recovery history watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settled() -> void:
	for i in range(5):await process_frame
	await RenderingServer.frame_post_draw
	while tested_app and tested_app.recovery_preview.busy():await process_frame
func wait_job(job) -> void:
	while job.pid>0:await process_frame
	await settled()
func canonical(value):return JSON.parse_string(JSON.stringify(value,"",false,true))
func portable(world: Dictionary) -> Dictionary:
	var result: Dictionary=canonical(world)
	for row in result.objects:row.erase("path");row.erase("source")
	return result
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0]
	var app=load("res://main.tscn").instantiate();tested_app=app;app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled()
	app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	var map:=folder.path_join("map.glb");var actor:=folder.path_join("actor.glb")
	check(SceneIO.make_fixture(map)==OK and SceneIO.make_pose_fixture(actor)==OK,"create original standard fixtures")
	check(app.load_scene(map).is_empty() and app.pose_editor.add_model(actor).is_empty(),"load map and poseable model")
	var actor_id: String=app.last_import_id;var bone: String=app.renderer.active_model().order[1]
	var plans: Array=Recovery.read_json(folder.path_join("plan.json")).native
	for plan in plans:
		var model:=Model.definition(plan.source);model.position=[20,0,-20];model.metadata=plan.metadata.duplicate(true)
		check(app.append_object(model,"model").is_empty(),"native model uses shared journal: "+plan.label)
	app.world_selection.select_entity(actor_id);app.import_audio(folder.path_join("voice.wav"));app.audio_start.value=24;app.audio_gain.value=-6;app.apply_audio_settings()
	app.create_cel(false);var cel: Dictionary=Drawing.cel_at(app.layers[1],0)
	var manual:=folder.path_join("manual.has");app.has_project.save_file(manual,"packed");await wait_job(app.has_project)
	check(FileAccess.file_exists(manual) and not app.dirty,"explicit manual HAS created")
	var expected:={"manual":manual,"manual_sha256":FileAccess.get_sha256(manual),"states":{},"native_models":plans.size()}
	var isolation:=true;var preview_count:=0;var max_preview_ms:=0.;var max_capture_ms:=0.;var max_worker_ms:=0.
	for at in range(18):
		app.set_frame(at);app.pose_editor.selected=bone;app.pose_editor.operation.select(0);app.pose_editor.refresh_values();app.pose_editor.fields[2].value=at*3;app.pose_editor.apply_numeric()
		cel.image.fill_rect(Rect2i(0,0,192,144),Color(0,0.3+at/34.,1,1));app.changed();app.renderer.camera.far=12000;app.insert_key()
		var keys: Array=app.keys.duplicate(true);var view: Dictionary=app.renderer.view_state();var history: int=app.history.size();var pixels:=Storage.image_hash(cel.image)
		app.autosave_tick(true);await settled()
		isolation=isolation and app.keys==keys and app.renderer.view_state()==view and app.history.size()==history and Storage.image_hash(cel.image)==pixels
		var checkpoint: String=app.recovery_root.path_join(app.recovery_session);var records:=Journal.entries(checkpoint)
		var preview: Image=Journal.preview(checkpoint,records[0].preview)
		if preview and preview.get_pixel(8,8)==cel.image.get_pixel(80,80):preview_count+=1
		max_preview_ms=maxf(max_preview_ms,app.last_recovery_preview_ms)
		max_capture_ms=maxf(max_capture_ms,app.last_recovery_preview_capture_ms);max_worker_ms=maxf(max_worker_ms,app.last_recovery_preview_worker_ms)
		if at in [12,15,17]:
			var orders:={};var transforms:={}
			for id in app.renderer.world_runtime.order:
				var rig: RefCounted=app.renderer.world_runtime.instance(id);orders[id]=rig.order.duplicate();transforms[id]=rig.sample_transform(at)
			expected.states[str(at)]={"frame":at,"world":portable(app.renderer.world_state()),"keys":app.keys.duplicate(true),"video":app.video.duplicate(true),"orders":orders,"transforms":transforms,"paint":pixels}
			var image: Image=await app.renderer.capture(app.keys,app.layers,at,true);image.save_png(folder.path_join("frame%d.png" % at))
	check(isolation,"deferred previews preserve shot keys, temporary view, Undo and original cel pixels")
	check(preview_count==18,"all eighteen stable checkpoints get the correct scene-and-drawing preview")
	var checkpoint: String=app.recovery_root.path_join(app.recovery_session);expected["checkpoint"]=checkpoint
	var records:=Journal.entries(checkpoint);var all_previews:=true
	for record in records:all_previews=all_previews and Journal.preview(checkpoint,record.preview)!=null
	check(records.size()==12 and all_previews,"bounded retained history contains twelve usable previews")
	var objects:=0
	for name in DirAccess.get_files_at(checkpoint):
		if Journal.is_manifest(name):objects+=1
	check(objects<=13 and FileAccess.get_sha256(manual)==expected.manual_sha256,"retention bounds metadata and leaves manual HAS untouched")
	app.show_recovery()
	await settled();var simple: AcceptDialog
	for child in app.get_children():
		if child is AcceptDialog and child.title=="Recover work":simple=child
	var simple_list: ItemList=app.find_child("RecoveryChoices",true,false)
	check(simple!=null and simple_list.item_count==2,"Simple recovery offers only recent choices")
	var simple_preview: TextureRect=app.find_child("RecoveryChoicePreview",true,false)
	for i in range(simple_list.item_count):
		simple_list.select(i);simple_list.item_selected.emit(i)
		var entry: Dictionary=records[i]
		var image:=Journal.preview(checkpoint,entry.preview)
		check(simple_list.get_item_text(i).contains("frame %d" % (17-i)) and simple_preview.texture!=null and simple_preview.texture.get_image().get_data()==image.get_data(),"Simple recovery shows the selected checkpoint frame and its own preview")
	simple.hide();simple.queue_free();await settled()
	app.advanced_toggle.button_pressed=true;app.advanced_toggle.pressed.emit()
	app.get_window().size=Vector2i(1200,760);await settled()
	var history_button: Button
	for child in app.find_children("*","Button",true,false):
		if child.text=="Recovery History…":history_button=child;break
	check(history_button!=null and history_button.is_visible_in_tree(),"Advanced exposes the actual Recovery History button")
	history_button.pressed.emit();await settled()
	var dialog: AcceptDialog
	for child in app.get_children():
		if child is AcceptDialog and child.title=="Recovery History":dialog=child
	var list: ItemList=app.find_child("RecoveryHistoryList",true,false);var preview: TextureRect=app.find_child("RecoveryHistoryPreview",true,false)
	check(dialog!=null and list.item_count==12 and list.get_item_text(0).contains("UTC") and preview.texture!=null,"Advanced history displays timestamped states and a real preview")
	check(dialog.size.x<=1000 and dialog.size.y<=500 and dialog.get_ok_button().get_global_rect().end.y<=dialog.size.y,"history dialog and Restore fit inside a smaller app window")
	var chosen:=-1;var candidates:=Recovery.candidates(app.recovery_root,"",true,true)
	for i in range(candidates.size()):
		if candidates[i].frame==12:chosen=i
	list.select(chosen);list.item_selected.emit(chosen);await settled()
	var original:=Image.load_from_file(folder.path_join("frame12.png"));original.resize(256,144,Image.INTERPOLATE_BILINEAR)
	check(preview.texture.get_image().get_pixel(8,8)==original.get_pixel(8,8),"selecting an older timestamp changes the thumbnail to its original paint")
	dialog.get_texture().get_image().save_png(folder.path_join("history-ui.png"))
	dialog.get_ok_button().pressed.emit();await settled();var confirm: ConfirmationDialog
	for child in app.get_children():
		if child is ConfirmationDialog and child.visible:confirm=child
	check(confirm!=null,"restoring history asks before replacing unsaved edits")
	if confirm:confirm.get_ok_button().pressed.emit()
	await settled()
	check(app.frame==12 and app.dirty and portable(app.renderer.world_state())==expected.states["12"].world and canonical(app.keys)==canonical(expected.states["12"].keys) and Storage.image_hash(Drawing.cel_at(app.layers[1],12).image)==expected.states["12"].paint,"actual history Restore installs the exact older editable world, camera and drawing")
	var current: Image=await app.renderer.capture(app.keys,app.layers,12,true);var export_error: String=await app.export_movie(folder)
	check(export_error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000013.png")).get_data()==current.get_data(),"older history exports synchronized movie with exact preview PNG")
	var movie: String=app.last_export_folder.path_join("movie.mp4")
	app.has_project.save_file(folder.path_join("chosen.has"),"packed");await wait_job(app.has_project)
	check(not app.dirty and FileAccess.get_sha256(manual)==expected.manual_sha256 and Recovery.candidates(app.recovery_root,"",true).is_empty() and Recovery.candidates(app.recovery_root,"",true,true).size()==12,"explicit Save resolves startup notice while Advanced retains history and manual HAS")
	app.new_project();app.has_project.open_file(folder.path_join("chosen.has"));await wait_job(app.has_project)
	check(app.frame==12 and portable(app.renderer.world_state())==expected.states["12"].world and Storage.image_hash(Drawing.cel_at(app.layers[1],12).image)==expected.states["12"].paint,"packed HAS from older history reopens with native data and editable paint")
	app.set_frame(20);app.changed();app.autosave_tick(true);var later: String=app.recovery_root.path_join(app.recovery_session);app.exporting=true;await settled();app.exporting=false
	check(Journal.entries(later)[0].preview.is_empty(),"preview readback defers when export begins before the idle frame")
	app.set_frame(21);app.changed();app.autosave_tick(true);Drawing.cel_at(app.layers[1],21).image.set_pixel(80,80,Color.RED);app.changed();await settled()
	check(Journal.entries(later)[0].preview.is_empty(),"a later edit cannot attach a misleading thumbnail to the older checkpoint")
	check(Recovery.resolve(later).is_empty(),"dismiss the separate preview-guard fixture before restart history tests")
	var file:=FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE);file.store_string(JSON.stringify(expected,"",false,true));file.close()
	var report:={"checks":checks,"failures":failures,"folder":folder,"checkpoint":checkpoint,"movie":movie,"native_models":plans.size(),"max_preview_ms":max_preview_ms,"max_capture_ms":max_capture_ms,"max_worker_ms":max_worker_ms}
	file=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(report));file.close();print("RECOVERY_HISTORY "+JSON.stringify(report));app.free();quit(0 if failures==0 else 1)
