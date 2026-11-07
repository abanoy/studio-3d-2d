extends SceneTree
const World=preload("res://src/world_document.gd")
const Particles=preload("res://src/particle_document.gd")
const SceneIO=preload("res://src/scene3d.gd")
const Timeline=preload("res://src/timeline.gd")
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
const Recovery=preload("res://src/recovery.gd")
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(200).timeout.connect(func():push_error("Particle scene watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS "if ok else "FAIL ")+label)
	if not ok:failures+=1
func settled() -> void:
	for n in range(3):await process_frame
	await RenderingServer.frame_post_draw
func wait_job(has) -> void:
	while has.pid>0:await process_frame
	await settled()
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0];var cold:=args.size()>1
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled()
	app.has_project.cache_root=folder.path_join("cache-cold"if cold else "cache");app.autosave_enabled.button_pressed=false
	if cold:
		app.has_project.open_file(folder.path_join("particles.has"));await wait_job(app.has_project)
		check(app.has_project.path==folder.path_join("particles.has") and app.renderer.world_runtime.effects.size()==2,"fresh ordinary HAS Open restores both canonical particle instances")
		var image: Image=await app.renderer.capture(app.keys,app.layers,13,true)
		check(image!=null and image.get_data()==Image.load_from_file(folder.path_join("reference.png")).get_data(),"cold packed scene produces identical particle, room, camera and ink pixels")
		check(app.renderer.world_state().effects[0].start_frame==12 and app.renderer.world_runtime.effects.values()[0].data.format=="studio_sprite_effect_1","cold reader retains timing and shared standard effect descriptor")
		var silence:=PackedByteArray();silence.resize(48000*4);silence.fill(0)
		check(app.audio_clip.start_frame==24 and app.audio_mix.pcm.slice(0,48000*4)==silence and absi(app.audio_mix.pcm.decode_s16(48002*4))>1000,"cold packed scene retains independent delayed audio on the same clock")
	else:
		var inputs:=folder.path_join("inputs")
		var room:=inputs.path_join("room.glb");check(SceneIO.make_fixture(room)==OK,"original room GLB")
		var world:=World.empty();world.format=World.EFFECT_FORMAT;world["effects"]=[];world.objects=[World.object(room,"environment","Room")]
		for i in range(2):
			var effect:=Particles.definition(inputs.path_join("effect-%d.json"%i),inputs.path_join("texture-%d.png"%i),"SFM flash"if i==0 else "Workshop glow")
			effect.id="effect-%d"%i;effect.position=[-1.6 if i==0 else 1.5,1.,1.];effect.start_frame=12 if i==0 else 0;effect.end_frame=20 if i==0 else 48;world.effects.append(effect)
		check(World.validate(world,48).is_empty() and app.restore_world(world).is_empty(),"ordinary world transaction prepares installed SFM and Workshop sprite data")
		app.keys=[Timeline.key(0,Vector3(0,1,7),Quaternion.IDENTITY,60)];app.set_frame(13)
		app.mode.select(0);app.change_mode(0);app.create_cel(false)
		Drawing.stroke(Drawing.image(Drawing.cel_at(app.layers[1],13)),Vector2(72,72),Vector2(180,72),5,Color.CYAN,false);app.changed()
		check(app.import_audio(inputs.path_join("tone.wav")).is_empty(),"particle world accepts independent authored sound")
		app.audio_clip.start_frame=24;app.rebuild_audio();app.changed()
		var ink: PackedByteArray=Drawing.image(Drawing.cel_at(app.layers[1],13)).get_data()
		var shots:=JSON.stringify(app.keys,"",true,true)
		var live=app.renderer.world_runtime;var flash=live.effects["effect-0"]
		app.set_frame(11);check(not flash.root.visible and flash.root.multimesh.visible_instance_count==0,"effect absent before its first frame")
		app.set_frame(12);check(flash.root.visible and flash.root.multimesh.visible_instance_count==1,"effect starts on exact project frame")
		app.set_frame(13);check(flash.last_values==flash.sample(1./24.),"project FPS and local start frame determine effect age")
		app.renderer.video_settings={"fps_num":48,"fps_den":2};live.evaluate(13,false,"",app.renderer.video_settings)
		check(flash.last_values==flash.sample(1./24.),"equivalent rational frame rate preserves exact native sample")
		live.evaluate(13,false,"",{"fps_num":48,"fps_den":1});live.evaluate(13)
		check(flash.last_values==flash.sample(1./48.),"editing reevaluation retains explicit project FPS rather than falling back to24")
		live.evaluate(13,false,"",{"fps_num":0,"fps_den":1});check(not live.evaluation_error.is_empty(),"invalid FPS reports a runtime error")
		app.set_frame(20);check(not flash.root.visible and flash.root.multimesh.visible_instance_count==0,"particle clip end is exclusive")
		app.set_frame(13)
		var reference: Image=await app.renderer.capture(app.keys,app.layers,13,true);reference.save_png(folder.path_join("reference.png"))
		for f in [47,0,19,12,30,13]:app.set_frame(f)
		var repeat: Image=await app.renderer.capture(app.keys,app.layers,13,true)
		check(reference.get_data()==repeat.get_data(),"ordinary timeline reverse seeks repeat exact pixels")
		check(Drawing.image(Drawing.cel_at(app.layers[1],13)).get_data()==ink and JSON.stringify(app.keys,"",true,true)==shots,"particle timing never authors camera keys or modifies cel bytes")
		var before: Dictionary=app.current_world();var bad: Dictionary=before.duplicate(true);bad.effects[0].texture_sha256="0".repeat(64)
		check(not app.restore_world(bad).is_empty() and app.current_world()==before and app.renderer.world_runtime==live,"failed effect preparation preserves entire installed world")
		bad=before.duplicate(true);bad.format=World.FORMAT
		check(not World.validate(bad,48).is_empty(),"unversioned effect data cannot silently enter legacy worlds")
		bad=before.duplicate(true);bad.objects[0].parent_id=bad.effects[0].id
		check(not World.validate(bad,48).is_empty(),"model parent cannot refer to unsupported particle attachment")
		bad=before.duplicate(true);bad.effects[0]["future_behavior"]=true
		check(not World.validate(bad,48).is_empty(),"unknown instance behavior is refused rather than silently ignored")
		var recovery:=Recovery.checkpoint(app.recovery_root,"particles",app.video,app.keys,app.layers,"",13,app.audio_document(),"",1,{},before)
		check(recovery.is_empty() and Storage.load_project(app.recovery_root.path_join("particles")).get("schema_version")==5,"recovery includes particle descriptor and texture dependencies")
		app.has_project.save_file(folder.path_join("linked.has"),"linked");await wait_job(app.has_project)
		check(app.has_project.path==folder.path_join("linked.has") and not app.dirty,"ordinary linked HAS Save includes both effect dependencies")
		app.has_project.clear_identity();var old_runtime=app.renderer.world_runtime
		app.has_project.open_file(folder.path_join("linked.has"));await wait_job(app.has_project)
		var linked: Image=await app.renderer.capture(app.keys,app.layers,13,true)
		check(app.has_project.path==folder.path_join("linked.has") and app.renderer.world_runtime!=old_runtime and linked.get_data()==reference.get_data(),"ordinary linked Open replaces runtime and preserves complete particle scene pixels")
		app.has_project.save_file(folder.path_join("particles.has"),"packed");await wait_job(app.has_project)
		check(app.has_project.path==folder.path_join("particles.has") and not app.dirty,"ordinary packed HAS Save includes both effects and drawing")
		var snapshot:=folder.path_join("snapshot");check(Storage.save_project(snapshot,app.video,app.keys,app.layers,"",13,{}, {},{},true,app.current_world()).is_empty(),"editable directory save uses the same schema5 contract")
		var old=load(ProjectSettings.localize_path(folder.path_join("old_storage.gd")))
		check(old.load_project(snapshot).has("error"),"actual pre-particle Studio storage rejects schema5 explicitly")
		var legacy:=before.duplicate(true);legacy.erase("effects");legacy.format=World.FORMAT
		var legacy_folder:=folder.path_join("legacy");check(Storage.save_project(legacy_folder,app.video,app.keys,app.layers,"",13,{}, {},{},true,legacy).is_empty() and Storage.load_project(legacy_folder).get("schema_version")==4,"ordinary worlds remain schema4 instead of forced migration")
		var export_error: String=await app.export_movie(folder);var movie: String=app.last_export_folder
		check(export_error.is_empty() and FileAccess.file_exists(movie.path_join("movie.mp4")),"ordinary Studio Export samples project-timed effects into actual MP4")
		var movie_frame:=Image.load_from_file(movie.path_join("frame_000014.png")) if FileAccess.file_exists(movie.path_join("frame_000014.png")) else null
		check(movie_frame!=null and movie_frame.get_data()==reference.get_data(),"ordinary exported frame14 equals particle preview at frame13")
		var result:=FileAccess.open(folder.path_join("movie.json"),FileAccess.WRITE);result.store_string(JSON.stringify({"folder":movie}));result.close()
	app.has_project.clear_identity();app.dirty=false;app.queue_free();await settled()
	var result: Dictionary={"checks":checks,"failures":failures,"cold":cold};var file:=FileAccess.open(folder.path_join("cold.json"if cold else "result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close()
	print("PARTICLE_SCENE "+JSON.stringify(result));quit(0 if failures==0 else 1)
