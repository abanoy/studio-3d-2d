extends SceneTree
const Storage=preload("res://src/storage.gd")
const Drawing=preload("res://src/drawing.gd")
const Graph=preload("res://src/sequence_graph.gd")
const SceneIO=preload("res://src/scene3d.gd")
var app
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(260).timeout.connect(func():push_error("Sequence editor watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func backdrop(path: String) -> Error:
	var node:=Node3D.new();node.name="OriginalBlueBackdrop"
	SceneIO.box(node,"Blue wall",Vector3(0,2,0),Vector3(30,20,.15),Color(.05,.15,.8))
	var document:=GLTFDocument.new();var state:=GLTFState.new();var error:=document.append_from_scene(node,state)
	if error==OK:error=document.write_to_filesystem(state,path)
	node.free();return error
func digest(bytes: PackedByteArray) -> String:
	var context:=HashingContext.new();context.start(HashingContext.HASH_SHA256);context.update(bytes);return context.finish().hex_encode()
func settle() -> void:
	for i in range(5):await process_frame
	await RenderingServer.frame_post_draw
func jobs() -> void:
	while app.has_project.pid>0:await process_frame
	await settle()
func find_button(node: Node,text: String) -> Button:
	for button in node.find_children("","Button",true,false):
		if button.text==text:return button
	return null
func labeled_spin(node: Node,text: String) -> SpinBox:
	for field in node.find_children("","SpinBox",true,false):
		var i: int=field.get_index();var siblings: Array=field.get_parent().get_children()
		if i>0 and siblings[i-1] is Label and siblings[i-1].text==text:return field
	return null
func full_mask(clip: Dictionary) -> bool:
	var mask: Dictionary=clip.get("mask",{})
	if mask.is_empty() or mask.invert:return false
	var r: Array=mask.rect
	return Rect2i(int(r[0]),int(r[1]),int(r[2]),int(r[3]))==Rect2i(0,0,1920,1080)
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0]
	app=load("res://main.tscn").instantiate();app.cold_cel_loading="--adaptive-open" in args;app.display_prefs_path=folder.path_join("prefs.cfg");app.recent_path=folder.path_join("recents.json");app.recovery_root=folder.path_join("recovery-cold" if "--read" in args else "recovery")
	if "--crash" in args:app.tree_exiting.connect(func():FileAccess.open(folder.path_join("graceful-exit.txt"),FileAccess.WRITE).store_string("unexpected cleanup"))
	root.add_child(app);await settle();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache-cold" if "--read" in args else "cache")
	var editor=app.sequence_editor
	app.home.hide()
	if "--read" in args:
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
		for name in ["Nested packed.has","Nested linked.has","Nested editing.has"]:
			app.has_project.open_file(folder.path_join(name));await jobs()
			if name=="Nested editing.has":
				check(editor.active_owner==expected.asset and app.frame==6 and app.has_project.path==folder.path_join(name),"ordinary saved parent reopens the active child editor and frame")
				editor.return_to_parent();await settle()
			check(editor.graph.assets.size()==1 and editor.clips().size()==2 and app.has_project.path==folder.path_join(name),"cold project restores shared editable definition and two independent instances")
			if expected.get("full_masks",false):check(editor.graph.format==Graph.MASK_FORMAT and editor.clips().all(full_mask),"cold project preserves full-frame masks alongside editable rig/audio")
			var child: Dictionary=editor.graph.assets[0].scene
			check(child.layers[1].cels.size()==2 and Storage.image_hash(Drawing.image(child.layers[1].cels[0]))==expected.paint,"cold child drawing holds remain editable and exact")
			var prepared: Dictionary=app.renderer.prepare_world(child.world,int(child.video.duration_frames))
			check(not prepared.has("error") and prepared.runtime.instance(child.world.objects[0].id).authored_keys().size()==2,"cold child preserves two parametric character keys")
			if not prepared.has("error"):prepared.runtime.dispose()
			check(not app.audio_mix.is_empty() and app.audio_document().is_empty() and digest(app.audio_mix.pcm)==expected.audio,"cold parent reproduces exact child audio without flattening editable sound tracks")
			var image: Image=await app.renderer.capture(app.keys,app.layers,0,true)
			check(Storage.image_hash(image)==expected.render,"cold nested composite matches original render")
			if app.cold_cel_loading and name=="Nested packed.has":
				check(child.layers[1].cels[0].has("raster_owner") and not child.layers[1].cels[0].raster_owner.is_pinned(),"ordinary nested Open preserves cold child ownership before editing")
				check(editor.enter(expected.asset).is_empty(),"cold shared child opens through normal editor navigation")
				app.mode.select(0);app.change_mode(0);app.active_layer=1;app.layer_choice.select(1);app.tool.select(0);app.brush_pressure.button_pressed=false;app.set_frame(0);app.color.color=Color.MAGENTA;await settle()
				var press:=InputEventMouseButton.new();press.button_index=MOUSE_BUTTON_LEFT;press.pressed=true;app.canvas_input(press,Vector2(820,420));app.paint_segment(Vector2(850,430));press.pressed=false;app.canvas_input(press,Vector2(850,430));await settle()
				var edited_sha:=Storage.image_hash(Drawing.image(app.layers[1].cels[0]));var edited_image:=Drawing.image(app.layers[1].cels[0])
				check(edited_sha!=expected.paint and app.layers[1].cels[0].raster_owner.is_pinned(),"actual child brush pins and changes only its authoritative cold drawing")
				app.undo();await settle();check(Storage.image_hash(Drawing.image(app.layers[1].cels[0]))==expected.paint and is_same(Drawing.image(app.layers[1].cels[0]),edited_image),"cold child Undo restores original pixels and writable identity")
				app.redo();await settle();check(Storage.image_hash(Drawing.image(app.layers[1].cels[0]))==edited_sha,"cold child Redo restores authored stroke")
				app.undo();editor.return_to_parent();await settle();var restored: Image=await app.renderer.capture(app.keys,app.layers,0,true)
				check(restored.get_data()==image.get_data(),"both parent instances restore exact nested composite after child Undo/navigation")
		print("SEQUENCE_EDITOR_READ ",JSON.stringify({"checks":checks,"failures":failures}));await app.sequence_editor.finish();app.free();quit(0 if failures==0 else 1);return
	check(app.load_demo_room(),"parent procedural room opens")
	var parent_keys: Array=app.keys.duplicate(true);var parent_source: String=app.source;var parent_sha:=FileAccess.get_sha256(parent_source)
	var parent_ink:=Drawing.blank(1920,1080);parent_ink.fill_rect(Rect2i(30,30,80,80),Color.CYAN);Drawing.insert(app.layers[1],0,48,parent_ink);app.changed();app.history.clear();app.redo_history.clear();app.history_bytes=0
	var ink_hash:=Storage.image_hash(parent_ink)
	var launch:=find_button(editor.toolbar,"Sequences…");launch.pressed.emit();await settle()
	check(editor.panel!=null and editor.panel.visible,"actual sequence toolbar opens the asset/clip browser")
	var create:=find_button(editor.panel,"New sequence and edit…");create.pressed.emit();await settle()
	var id: String=editor.active_owner;editor.return_to_parent();await settle()
	check(not id.is_empty() and editor.graph.assets.size()==1 and app.history.size()==1,"new editable asset and parent clip are one Undo")
	check(editor.rename_asset(id,"Reusable character").is_empty(),"asset can be named independently of its instances")
	var clip_id: String=editor.clips()[0].id
	check(editor.change_clip(clip_id,{"loop":true}).is_empty(),"parent instance explicitly enables looping")
	check(editor.enter(id).is_empty() and editor.active_owner==id and app.renderer.world_runtime.instances.is_empty(),"child editor opens its own empty editable world")
	# The child has its own camera keys. Shorten it without touching the parent.
	app.keys=[app.keys[0]];app.changed()
	app.show_project_options();await settle()
	check(app.project_timing.apply_duration(24).is_empty(),"child timeline can shorten independently inside a looping parent instance")
	app.project_options.hide()
	var actor:=folder.path_join("Original actor.glb");check(SceneIO.make_pose_fixture(actor)==OK,"original procedural skinned fixture is created")
	check(app.pose_editor.add_model(actor).is_empty(),"normal model import authors the child world")
	var rig: RefCounted=app.renderer.active_model()
	check(rig!=null and not rig.order.is_empty(),"child character retains ordinary editable rig bindings")
	app.pose_editor.record_key()
	var samples:=PackedByteArray();samples.resize(12000*2);samples.fill(0)
	for sample in range(12000):samples.encode_s16(sample*2,roundi(12000*sin(TAU*1000*sample/48000.0)))
	var sound:=AudioStreamWAV.new();sound.format=AudioStreamWAV.FORMAT_16_BITS;sound.mix_rate=48000;sound.data=samples
	var wave:=folder.path_join("Original cue.wav");check(sound.save_to_wav(wave)==OK and app.import_audio(wave,6).is_empty(),"ordinary editable child sound starts at local frame6")
	var first:=Drawing.blank(1920,1080);first.fill_rect(Rect2i(800,400,120,100),Color(1,0,0,.5))
	var second:=Drawing.blank(1920,1080);second.fill_rect(Rect2i(800,400,120,100),Color.BLUE)
	Drawing.insert(app.layers[1],0,12,first);Drawing.insert(app.layers[1],12,24,second);app.changed()
	app.set_frame(12);app.pose_editor.selected=rig.order[0];app.pose_editor.operation.select(0);app.pose_editor.refresh_values();app.pose_editor.fields[2].value=15;app.pose_editor.apply_numeric()
	check(rig.authored_keys().size()==2,"child posing uses parametric keys rather than rasterizing the rig")
	editor.return_to_parent();await settle()
	check(editor.active_owner.is_empty() and app.video.duration_frames==48 and app.keys==parent_keys and Storage.image_hash(parent_ink)==ink_hash,"return preserves parent timing, camera and original ink")
	check(editor.add_instance(id).is_empty(),"same editable child can be placed again")
	if "--mask-recovery" in args:
		for clip in editor.clips():editor.change_mask(clip.id,{"rect":[0,0,1920,1080],"invert":false})
		check(editor.graph.format==Graph.MASK_FORMAT and editor.clips().all(full_mask),"full-frame masks retain ordinary editable 3D rig, ink and audio before crash test")
	var second_id: String=editor.clips()[1].id
	check(editor.change_clip(second_id,{"start":24,"duration":24}).is_empty(),"second instance has an independent parent range")
	check(editor.placement_key(clip_id,{"frame":0,"offset":[-240,0],"scale":1.0,"rotation":0.0,"opacity":1.0,"interpolation":"ease"}).is_empty() and editor.placement_key(second_id,{"frame":0,"offset":[240,0],"scale":.75,"rotation":0.0,"opacity":.5,"interpolation":"ease"}).is_empty(),"instances have independent keyed placement and opacity")
	check(editor.change_clip(second_id,{"gain_db":-6.5}).is_empty(),"instance audio supports fractional gain")
	editor.selected_clip=second_id;editor.show_panel();await settle()
	check(is_equal_approx(labeled_spin(editor.panel,"Picture scale").value,.75) and is_equal_approx(labeled_spin(editor.panel,"Child sound gain (dB)").value,-6.5),"clip inspector retains fractional scale and gain instead of snapping to initial integer steps")
	editor.close_panel()
	check(editor.placement_key(clip_id,{"frame":48,"offset":[-120,0],"scale":1.0,"rotation":0.0,"opacity":1.0,"interpolation":"linear"}).is_empty(),"instance movement keeps an editable eased placement curve")
	await settle()
	var target: Rect2=editor.strip.row_rect(editor.clips()[1],1)
	var press:=InputEventMouseButton.new();press.button_index=MOUSE_BUTTON_LEFT;press.pressed=true;press.position=target.get_center();editor.strip._gui_input(press)
	var motion:=InputEventMouseMotion.new();motion.position=press.position+Vector2(app.timeline.x(24)-app.timeline.x(36),0);editor.strip._gui_input(motion)
	press.pressed=false;press.position=motion.position;editor.strip._gui_input(press)
	check(editor.find_clip(second_id).start==12,"actual timeline drag moves an instance on the shared frame scale")
	app.undo();check(editor.find_clip(second_id).start==24,"instance drag is one reversible layout edit")
	var old: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	check(editor.enter(id).is_empty(),"shared definition reopens for real editing")
	var changed: Image=Drawing.edit_image(app.layers[1].cels[0]).image;changed.fill_rect(Rect2i(800,400,120,100),Color.GREEN);Drawing.touch(changed);app.changed()
	var paint:=Storage.image_hash(changed);editor.return_to_parent();await settle()
	var render: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	check(old.get_data()!=render.get_data() and Drawing.image(editor.graph.assets[0].scene.layers[1].cels[0]).get_data()==changed.get_data(),"child changes invalidate cached parent pictures without a duplicate/manual render")
	app.undo();app.redo();check(Storage.image_hash(Drawing.image(editor.graph.assets[0].scene.layers[1].cels[0]))==paint,"placement Undo/Redo retains later edits to the shared child")
	check(app.project_timing.apply_values(30,1).is_empty() and editor.graph.assets[0].scene.video.fps_num==30,"project rate changes propagate to child local timelines atomically")
	app.undo();check(app.video.fps_num==24 and editor.graph.assets[0].scene.video.fps_num==24,"rate Undo restores parent and child clocks together")
	var audio_hash: String=digest(app.audio_mix.pcm)
	var placement_samples:=[];var source_frames:=[]
	for frame in range(48):placement_samples.append(Graph.placement(editor.find_clip(clip_id),frame));source_frames.append(Graph.local_frame(editor.find_clip(clip_id),frame,24))
	check(editor.split_clip(clip_id,17).is_empty() and editor.clips().size()==3,"splitting a looping instance creates independent source windows")
	var exact:=true
	for frame in range(48):
		var piece: Dictionary=editor.clips()[0] if frame<17 else editor.clips()[1]
		exact=exact and Graph.placement(piece,frame)==placement_samples[frame] and Graph.local_frame(piece,frame,24)==source_frames[frame]
	check(exact and digest(app.audio_mix.pcm)==audio_hash,"actual split preserves all placement, source-frame and PCM samples exactly")
	app.undo();check(editor.clips().size()==2,"split Undo rejoins the original instance")
	check(editor.copy_clip(second_id).is_empty(),"copy retains the editable child reference and independent placement")
	app.set_frame(0);check(editor.paste_clip().is_empty() and editor.clips().size()==3,"paste adds another instance without duplicating its child asset")
	check(editor.remove_clip(editor.selected_clip).is_empty() and editor.clips().size()==2,"deleting a pasted clip preserves the reusable asset")
	check(not editor.remove_asset(id).is_empty(),"referenced definitions cannot be removed silently")
	var reject: String=editor.change_clip(clip_id,{"duration":49})
	check(not reject.is_empty() and editor.find_clip(clip_id).duration==48,"invalid timing refuses atomically")
	check(editor.enter(id).is_empty(),"enter child for cycle refusal")
	check(not editor.add_instance(id).is_empty() and editor.clips().is_empty(),"self-nesting refuses without partial clips")
	app.set_frame(6);app.changed();app.autosave_tick(true)
	var recovery_folder: String=app.recovery_root.path_join(app.recovery_session)
	var recovered:=Storage.load_project(recovery_folder)
	check(not recovered.has("error") and recovered.sequence_graph.assets.size()==1 and recovered.editor.sequence_editor.asset_id==id and recovered.editor.sequence_editor.frame==6,"recovery retains complete enclosing project and active child context")
	app.has_project.save_file(folder.path_join("Nested editing.has"),"packed");await jobs()
	check(FileAccess.file_exists(folder.path_join("Nested editing.has")),"Save inside child writes the complete parent with editing context")
	editor.return_to_parent();await settle()
	var background:=folder.path_join("Original second backdrop.glb")
	check(backdrop(background)==OK and app.load_scene(background,24).is_empty(),"same child sequence is reused across a second original background appearing at frame24")
	var later: Image=await app.renderer.capture(app.keys,app.layers,36,true)
	var color:=later.get_pixel(1200,100)
	check(color.b>color.r*2 and app.current_world().objects.size()==2,"later frames show the second background beneath the repeated editable character")
	app.set_frame(0);render=await app.renderer.capture(app.keys,app.layers,0,true)
	check(editor.enter(id).is_empty(),"child can reopen after parent background changes")
	app.set_frame(6);app.has_project.save_file(folder.path_join("Nested editing.has"),"packed");await jobs();editor.return_to_parent();await settle()
	app.has_project.save_file(folder.path_join("Nested packed.has"),"packed");await jobs()
	check(FileAccess.file_exists(folder.path_join("Nested packed.has")),"packed HAS saves nested scenes and source assets")
	app.has_project.save_file(folder.path_join("Nested linked.has"),"linked");await jobs()
	check(FileAccess.file_exists(folder.path_join("Nested linked.has")),"linked HAS retains embedded editable definitions/cels and checked source references")
	var error: String=await app.export_movie(folder)
	check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000001.png")).get_data()==render.get_data(),"actual MP4 uses exact shared nested preview/export pipeline")
	check(FileAccess.get_sha256(parent_source)==parent_sha,"original parent geometry stays unchanged")
	var expected_file:=FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE);expected_file.store_string(JSON.stringify({"paint":paint,"render":Storage.image_hash(render),"audio":audio_hash,"asset":id,"full_masks":"--mask-recovery" in args},"",true,true));expected_file.close()
	if "--crash" in args:
		check(editor.enter(id).is_empty(),"enter the child for abrupt-exit recovery fixture")
		app.set_frame(6);app.changed()
		while app.recovery_preview.busy():app.poll_recovery_preview();await process_frame
		app.autosave_tick(true)
		check(app.checkpoint_revision==app.recovery_revision,"complete nested checkpoint is committed before abrupt exit")
		var partial:=FileAccess.open(app.recovery_root.path_join(app.recovery_session).path_join("project.json.tmp"),FileAccess.WRITE);partial.store_string("{unfinished");partial.flush();partial.close()
	print("SEQUENCE_EDITOR_SMOKE ",JSON.stringify({"checks":checks,"failures":failures,"movie":app.last_export_folder.path_join("movie.mp4")}))
	if "--crash" in args:
		OS.kill(OS.get_process_id())
		FileAccess.open(folder.path_join("kill-returned.txt"),FileAccess.WRITE).store_string("unexpected return")
		quit(2);return
	await app.sequence_editor.finish();app.free();quit(0 if failures==0 else 1)
