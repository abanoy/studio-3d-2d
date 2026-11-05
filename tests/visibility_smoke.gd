extends SceneTree
const Track=preload("res://src/visibility_track.gd")
const Clips=preload("res://src/animation_clips.gd")
const Model=preload("res://src/model.gd")
const SceneIO=preload("res://src/scene3d.gd")
const Timeline=preload("res://src/timeline.gd")
const Drawing=preload("res://src/drawing.gd")
const World=preload("res://src/world_document.gd")
const Storage=preload("res://src/storage.gd")
var checks:=0
var failures:=0

func _initialize() -> void:
	create_timer(110).timeout.connect(func():push_error("Visibility watchdog expired");quit(2))
	call_deferred("run")

func check(ok: bool,text: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+text)
	if not ok:failures+=1

func settled() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw

func wait_job(job) -> void:
	while job.pid>0:await process_frame
	await settled()

func energy(image: Image, background: Image) -> float:
	var a:=image.get_data();var b:=background.get_data();var total:=0.0
	for i in range(0,a.size(),4):
		for c in range(3):total+=absf(float(a[i+c])-float(b[i+c]))
	return total

func run() -> void:
	var folder:=ProjectSettings.globalize_path("res://output/visibility/run_%d" % Time.get_ticks_usec());DirAccess.make_dir_recursive_absolute(folder)
	var asset:=folder.path_join("actor.glb");SceneIO.make_pose_fixture(asset)
	var digest:=FileAccess.get_sha256(asset)
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled()
	app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	check(app.video.visibility_fade_ms==300 and not app.advanced_mode,"new Simple project defaults to300ms visibility fades")
	app.pose_editor.add_model(asset)
	var rig: RefCounted=app.renderer.active_model();var id: String=rig.data.id;var editor=app.pose_editor
	editor.record_key();app.set_frame(32);editor.record_key();editor.frame_model()
	app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,app.renderer.camera.fov)]
	var motion: Dictionary=rig.data.duplicate(true)
	app.set_frame(10);var history: int=app.history.size();editor.visible_toggle.button_pressed=false
	check(rig.data.format==Model.BODY_FORMAT and rig.data.visibility_keys==[{"frame":10,"visible":false}] and app.history.size()==history+1,"actual Simple toggle records visibility while retaining independent body controls in one Undo")
	check(rig.data.visible and not rig.visible_at(40) and rig.visible_at(9),"visibility persists independently of the unchanged base flag")
	check(not rig.visible_at(100),"an unset later frame100 retains the previous OFF key")
	history=app.history.size();editor.visible_toggle.toggled.emit(false)
	check(app.history.size()==history,"repeating the same current key does not create another Undo command")
	var data: Dictionary=rig.data.duplicate(true)
	check(Model.validate(data,48).is_empty() and not Track.validate(motion,48).contains("Invalid"),"version3 validates and legacy records retain static behavior")
	var bad: Dictionary=data.duplicate(true);bad.format=Clips.FORMAT
	check(not Model.validate(bad,48).is_empty(),"older model versions cannot silently carry visibility animation")
	bad=data.duplicate(true);bad.visibility_keys.append({"frame":10,"visible":true})
	check(not Model.validate(bad,48).is_empty(),"duplicate visibility addresses fail validation")
	var a:=Track.opacity(data,10,app.video);var b:=Track.opacity(data,14,app.video);var c:=Track.opacity(data,18,app.video)
	check(a==1 and absf(b-(1-4.0/7.2))<0.00001 and c==0,"300milliseconds samples on the rational frame clock without rounding to frames")
	var fractional:={"fps_num":30,"fps_den":1,"visibility_fade_ms":300}
	check(absf(Track.opacity(data,14,fractional)-(1-4.0/9))<0.00001,"fade duration follows project frame rate")
	fractional={"fps_num":120,"fps_den":1001,"visibility_fade_ms":300}
	check(Track.opacity(data,11,fractional)==0,"fractional FPS denominator is included in visibility timing")
	var reverse: Dictionary=data.duplicate(true);Track.put(reverse,14,true)
	check(absf(Track.opacity(reverse,14,app.video)-b)<0.00001 and Track.opacity(reverse,16,app.video)>b,"a visibility reversal starts from current opacity without jumping")
	Track.put(reverse,16,true)
	check(Track.opacity(reverse,18,app.video)>Track.opacity(reverse,16,app.video),"repeated same-state keys do not restart an active fade")
	app.undo();check(rig.data==motion,"Undo restores the whole pre-visibility legacy record")
	app.redo();check(rig.data==data,"Redo restores exact visibility and motion ownership")
	app.clip_editor.request("split",id,"",20)
	var right: String=rig.data.animation_clips[1].id
	var moved:=Clips.move(rig.data,right,40,48)
	check(moved.has("error"),"overlong motion move remains rejected with visibility keys")
	moved=Clips.move(rig.data,right,28,48);editor.restore_state(moved.data)
	app.set_frame(32)
	check(not rig.root.visible and not editor.visible_toggle.button_pressed,"later animation piece and intervening gap cannot re-enable hidden state")
	var snapshot: Dictionary=rig.data.duplicate(true)
	app.world_selection.select_entity(id);await settled()
	check(app.world_selection.selected==id and not rig.root.visible and rig.data==snapshot,"hidden selection leaves animated visibility untouched")
	# The real Compatibility renderer must show intermediate opacity, not merely a flag.
	app.set_frame(20);var hidden: Image=await app.renderer.capture(app.keys,app.layers,20,true)
	var visible: Image=await app.renderer.capture(app.keys,app.layers,9,true)
	var partial: Image=await app.renderer.capture(app.keys,app.layers,14,true)
	var full_energy:=energy(visible,hidden);var partial_energy:=energy(partial,hidden)
	check(full_energy>1000 and partial_energy>full_energy*0.1 and partial_energy<full_energy*0.9,"actual OpenGL fade pixels lie between visible and hidden renders")
	visible.save_png(folder.path_join("visible.png"));partial.save_png(folder.path_join("partial.png"));hidden.save_png(folder.path_join("hidden.png"))
	await app.renderer.capture(app.keys,app.layers,9,true);await settled()
	check(not rig.opacity_materials.active,"opaque endpoint restores source material references")
	var test_mesh:=MeshInstance3D.new();test_mesh.mesh=BoxMesh.new();var material:=StandardMaterial3D.new();material.albedo_color=Color(1,1,1,0.2);test_mesh.material_override=material
	var opacity:=Model.Opacity.new();opacity.inventory(test_mesh);opacity.set_alpha(0.5)
	check(test_mesh.material_override.albedo_color.a==0.5 and is_equal_approx(material.albedo_color.a,0.2),"opaque material fade starts from effective alpha1 without altering authored material")
	opacity.set_alpha(1);check(test_mesh.material_override==material,"material override reference restores exactly after a fade");test_mesh.free()
	app.show_project_options();await settled()
	check(app.project_options.visible and app.visibility_fade.value==300,"Simple Options exposes the project-wide fade setting")
	root.get_viewport().get_texture().get_image().save_png(folder.path_join("options.png"))
	app.visibility_fade.value=0;app.project_options.hide();app.set_frame(10)
	check(app.video.visibility_fade_ms==0 and not rig.root.visible,"zero milliseconds gives an instantaneous visibility cut")
	app.undo();check(app.video.visibility_fade_ms==300,"Undo restores the global fade setting")
	app.redo();check(app.video.visibility_fade_ms==0,"Redo restores the cut setting")
	app.set_frame(30);editor.visible_toggle.button_pressed=true;app.set_frame(32)
	check(rig.root.visible and rig.visible_at(32),"explicit later visibility key reintroduces the object")
	editor.remove_visibility_key();check(rig.visible_at(32),"removing an absent current-frame key is a no-op")
	app.set_frame(30);editor.remove_visibility_key();check(not rig.visible_at(40),"removing a key restores the preceding persistent state")
	app.undo();check(rig.visible_at(40),"visibility-key removal is undoable")
	app.change_visibility_fade(300)
	app.set_frame(0);app.create_cel(false);Drawing.stroke(Drawing.cel_at(app.layers[1],0).image,Vector2(80,80),Vector2(180,80),5,Color.RED,false);app.changed()
	var wav:=ProjectSettings.globalize_path("res://output/fixtures/voice — тест.wav")
	if FileAccess.file_exists(wav):
		check(app.import_audio(wav).is_empty(),"fade fixture imports independent audio")
		app.audio_clip.start_frame=24;app.audio_clip.gain_db=-6;app.rebuild_audio()
	var paint: PackedByteArray=Drawing.cel_at(app.layers[1],0).image.get_data()
	var project:=folder.path_join("visibility.has");app.has_project.save_file(project,"packed");await wait_job(app.has_project)
	check(FileAccess.file_exists(project),"visibility project saves as packed HAS")
	var invalid: Dictionary=app.video.duplicate(true);invalid.visibility_fade_ms=-1
	var invalid_folder:=folder.path_join("invalid-save")
	check(not Storage.save_project(invalid_folder,invalid,app.keys,app.layers,app.source,app.frame,{}, {}, {},false,app.renderer.world_state()).is_empty() and not DirAccess.dir_exists_absolute(invalid_folder),"invalid project fade is rejected before writing any save files")
	app.new_project();await settled();app.has_project.open_file(project);await wait_job(app.has_project)
	rig=app.renderer.world_runtime.instance(id)
	check(rig.data.format==Model.BODY_FORMAT and rig.data.visibility_keys.size()==2 and app.video.visibility_fade_ms==300 and Drawing.cel_at(app.layers[1],0).image.get_data()==paint,"packed HAS reopens independent body controls, visibility, global fade and drawing")
	var linked:=folder.path_join("visibility-linked.has");app.has_project.save_file(linked,"linked");await wait_job(app.has_project)
	app.new_project();app.has_project.open_file(linked);await wait_job(app.has_project);rig=app.renderer.world_runtime.instance(id)
	check(rig.data.visibility_keys.size()==2 and app.video.visibility_fade_ms==300,"linked HAS preserves visibility keys and project fade")
	app.changed();app.autosave_tick(true)
	var recovery: String=app.recovery_root.path_join(app.recovery_session)
	check(not Storage.load_project(recovery).has("error") and app.open_project(recovery),"actual recovery checkpoint restores visibility project")
	rig=app.renderer.world_runtime.instance(id)
	app.set_frame(24);check(not rig.root.visible,"packed reopen retains persistent hidden state between pieces")
	app.set_frame(34);check(rig.root.visible and rig.evaluated_opacity>0 and rig.evaluated_opacity<1,"packed reopen retains the later fade-in")
	app.renderer.viewport.get_texture().get_image().save_png(folder.path_join("viewport.png"))
	var movie_frame: Image=await app.renderer.capture(app.keys,app.layers,34,true)
	var error: String=await app.export_movie(folder)
	check(error.is_empty(),"visibility project exports MP4 successfully")
	var png:=Image.load_from_file(app.last_export_folder.path_join("frame_000035.png"));png.convert(Image.FORMAT_RGBA8)
	check(png.get_data()==movie_frame.get_data(),"exported fade frame matches the same reopened preview exactly")
	check(FileAccess.get_sha256(asset)==digest,"visibility and material fades preserve the original model bytes")
	await settled();root.get_viewport().get_texture().get_image().save_png(folder.path_join("editor.png"))
	var movie: String=app.last_export_folder.path_join("movie.mp4")
	# Parent opacity multiplies descendants, without fading a child's mesh twice.
	var document: Dictionary=app.renderer.world_state();var child: Dictionary=document.objects[0].duplicate(true)
	child.id="visibility-child";child.parent_id=id;child.position[0]=3;child.visibility_keys=[]
	document.objects.append(child);app.restore_world(document);app.set_frame(14)
	var parent: RefCounted=app.renderer.world_runtime.instance(id);var descendant: RefCounted=app.renderer.world_runtime.instance(child.id)
	check(absf(parent.evaluated_opacity-b)<0.00001 and absf(descendant.evaluated_opacity-b)<0.00001 and parent.opacity_materials.meshes.size()==descendant.opacity_materials.meshes.size(),"parent fade propagates once to independently owned child meshes")
	app.set_frame(24);check(not descendant.root.is_visible_in_tree(),"hidden parent remains authoritative over child visibility")
	var native_samples:=[]
	for sample in ["pose-smoke/miku-project","source-smoke/source-project","sfm-smoke/project"]:
		var path:=ProjectSettings.globalize_path("res://output/"+sample)
		if not FileAccess.file_exists(path.path_join("project.json")):print("SKIP optional native visibility fixture: "+sample);continue
		var loaded: Dictionary=Storage.load_project(path);var row: Dictionary=World.from_project(loaded).objects[-1]
		row.id="native-fade";row.parent_id="";row.start_frame=0;row.visible=true;row.reference_only=false
		var source_sha:=FileAccess.get_sha256(row.source);var metadata: Dictionary=row.metadata.duplicate(true)
		app.new_project();var native:=World.empty();native.objects.append(row);app.restore_world(native);app.world_selection.select_entity(row.id);app.pose_editor.frame_model()
		app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,60)]
		app.set_frame(10);app.pose_editor.visible_toggle.button_pressed=false
		rig=app.renderer.active_model()
		var native_hidden: Image=await app.renderer.capture(app.keys,[],20,true)
		var native_visible: Image=await app.renderer.capture(app.keys,[],9,true)
		var native_partial: Image=await app.renderer.capture(app.keys,[],14,true)
		var total:=energy(native_visible,native_hidden);var part:=energy(native_partial,native_hidden)
		check(total>1000 and part>total*0.05 and part<total*0.95,"native imported materials visibly fade: "+sample)
		check(rig.data.metadata==metadata and FileAccess.get_sha256(row.source)==source_sha,"native fade preserves provenance and source: "+sample)
		native_partial.save_png(folder.path_join("native-%d.png" % native_samples.size()));native_samples.append(sample)
	var legacy:=folder.path_join("legacy-project")
	var legacy_model:=Model.definition(asset)
	check(Storage.save_project(legacy,app.video,app.keys,app.layers,asset,0,{}, {},legacy_model).is_empty() and app.open_project(legacy),"old single-slot project opens without a first-presence field")
	app.world_selection.select_entity("model");app.set_frame(10);app.pose_editor.visible_toggle.button_pressed=false
	rig=app.renderer.active_model()
	check(not app.renderer.world_runtime and rig.data.format==Track.FORMAT and rig.data.start_frame==0 and not rig.visible_at(40),"legacy model visibility edit promotes safely with explicit introduction0")
	app.undo();check(rig.data.format=="studio_model_1" and not rig.data.has("start_frame"),"legacy visibility Undo restores the exact old record contract")
	app.redo();var legacy_has:=folder.path_join("legacy-visibility.has");app.has_project.save_file(legacy_has,"packed");await wait_job(app.has_project)
	app.new_project();app.has_project.open_file(legacy_has);await wait_job(app.has_project);rig=app.renderer.active_model()
	check(rig!=null and rig.data.format==Track.FORMAT and not rig.visible_at(40),"legacy packed HAS retains newly authored visibility keys")
	var report:={"checks":checks,"failures":failures,"folder":folder,"project":project,"movie":movie,"full_energy":full_energy,"partial_energy":partial_energy,"native_samples":native_samples}
	var file:=FileAccess.open(ProjectSettings.globalize_path("res://output/visibility-result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(report));file.close()
	print("VISIBILITY_SMOKE "+JSON.stringify(report));app.queue_free();await process_frame;quit(0 if failures==0 else 1)
