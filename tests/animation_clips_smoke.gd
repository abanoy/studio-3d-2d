extends SceneTree
const Support=preload("res://tests/world_test_support.gd")
const Clips=preload("res://src/animation_clips.gd")
const SceneIO=preload("res://src/scene3d.gd")
const Model=preload("res://src/model.gd")
const Timeline=preload("res://src/timeline.gd")
const Drawing=preload("res://src/drawing.gd")
const World=preload("res://src/world_document.gd")
const Storage=preload("res://src/storage.gd")
const Body=preload("res://src/body_animation.gd")
var checks:=0
var failures:=0

func _initialize() -> void:
	create_timer(110).timeout.connect(func():push_error("Animation clip watchdog expired");quit(2))
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

func action(app, frame: int, id: int) -> void:
	var click:=InputEventMouseButton.new();click.button_index=MOUSE_BUTTON_RIGHT;click.pressed=true
	click.position=Vector2(app.timeline.x(frame),app.timeline.row_y(1)+12)
	app.timeline._gui_input(click);await settled();app.timeline.import_menu.id_pressed.emit(id);await settled()

func pixel_difference(a: Image, b: Image) -> Dictionary:
	var aa:=a.get_data();var bb:=b.get_data();var count:=0;var total:=0
	for i in range(aa.size()):
		if aa[i]!=bb[i]:count+=1;total+=absi(int(aa[i])-int(bb[i]))
	return {"channels":count,"mean":float(total)/aa.size(),"close":count<=384 and float(total)/aa.size()<0.002}

func source_frames(data: Dictionary,index: int,part: String) -> Array:
	var body:=Body.view(data)
	return Body.B.points(body,body.pieces[index],part,false).map(func(key):return int(key.frame))

func run() -> void:
	var folder:=ProjectSettings.globalize_path("res://output/animation-clips/run_%d" % Time.get_ticks_usec());DirAccess.make_dir_recursive_absolute(folder)
	var asset:=folder.path_join("actor.glb");var map:=folder.path_join("room.glb");SceneIO.make_pose_fixture(asset);SceneIO.make_fixture(map)
	var original:=FileAccess.get_sha256(asset)
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled()
	app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	app.load_scene(map);var map_id: String=app.last_import_id;app.pose_editor.add_model(asset)
	var id: String=app.last_import_id;var rig: RefCounted=app.renderer.active_model();var editor=app.pose_editor
	editor.record_key()
	for frame in [8,16]:
		app.set_frame(frame);editor.operation.select(1);editor.selected="@root";editor.refresh_values();editor.fields[0].value=float(frame)/8;editor.apply_numeric()
	var bone: String=rig.order[1];editor.tree_items[bone].select(0);editor.operation.select(0);editor.refresh_values();editor.fields[2].value=60;editor.apply_numeric()
	var before: Dictionary=rig.data.duplicate(true);var old:=Model.new();old.data=before
	editor.frame_model();var camera: Camera3D=app.renderer.camera;app.keys=[Timeline.key(0,camera.position,camera.quaternion,camera.fov)]
	app.mode.select(0);app.change_mode(0);app.set_frame(0);app.create_cel(false)
	Drawing.stroke(Drawing.cel_at(app.layers[1],0).image,Vector2(80,80),Vector2(180,80),5,Color.RED,false);app.changed()
	var wav:=ProjectSettings.globalize_path("res://output/fixtures/voice — тест.wav")
	check(app.import_audio(wav).is_empty(),"clip fixture contains actual independent WAV audio")
	app.audio_clip.start_frame=24;app.audio_clip.gain_db=-6;app.rebuild_audio()
	var audio: Dictionary=app.audio_clip.duplicate(true);var shots: Array=app.keys.duplicate(true)
	var paint: PackedByteArray=Drawing.cel_at(app.layers[1],0).image.get_data();var map_data: Dictionary=app.renderer.world_runtime.instance(map_id).data.duplicate(true)
	var image8: Image=await app.renderer.capture(app.keys,app.layers,8,true)
	var history: int=app.history.size();await action(app,8,10)
	check(rig.data.format==Model.BODY_FORMAT and rig.data.animation_clips.size()==2 and rig.data.animation_clips[1].start==8,"actual timeline context menu splits the independent model into owned source pieces")
	check(app.history.size()==history+1 and rig.data.pose_keys.is_empty(),"split owns source curves explicitly in one Undo step")
	var image_split: Image=await app.renderer.capture(app.keys,app.layers,8,true)
	image8.save_png(folder.path_join("before-split.png"));image_split.save_png(folder.path_join("after-split.png"))
	var split_pixels:=pixel_difference(image8,image_split)
	check(split_pixels.close,"split retains rendered cut-frame within the existing GPU edge tolerance")
	var exact:=true
	for frame in range(17):exact=exact and rig.sample(frame)==old.sample(frame) and rig.sample_transform(frame)==old.sample_transform(frame)
	check(exact,"all original pose and root samples survive splitting through an eased segment")
	var right: String=rig.data.animation_clips[1].id;var left: String=rig.data.animation_clips[0].id
	var press:=InputEventMouseButton.new();press.button_index=MOUSE_BUTTON_LEFT;press.pressed=true;press.position=Vector2(app.timeline.x(12),app.timeline.row_y(1)+12);app.timeline._gui_input(press)
	var motion:=InputEventMouseMotion.new();motion.position=app.timeline.get_global_transform()*Vector2(app.timeline.x(28),-100);app._input(motion)
	check(app.timeline.moving_piece==right and app.timeline.moving_delta==16 and rig.data.animation_clips[1].start==8,"piece drag previews independently without changing document")
	var release:=InputEventMouseButton.new();release.button_index=MOUSE_BUTTON_LEFT;release.pressed=false;release.position=Vector2(1,1);app._input(release)
	check(rig.data.animation_clips[0].start==0 and rig.data.animation_clips[1].start==24 and rig.sample(28)==old.sample(12),"outside release moves only the right piece with its original bone motion")
	var gap: float=rig.sample_transform(16).position[0]
	app.renderer.world_runtime.evaluate(16)
	check(rig.root.visible and gap>old.sample_transform(7).position[0] and gap<old.sample_transform(8).position[0],"gap remains visible and interprets connecting motion")
	check(app.keys==shots and app.audio_clip==audio and Drawing.cel_at(app.layers[1],0).image.get_data()==paint and app.renderer.world_runtime.instance(map_id).data==map_data,"split/move leaves shot keys, WAV, drawing and other map unchanged")
	app.undo();check(rig.data.animation_clips[1].start==8,"Undo restores only the moved piece's old timing")
	app.redo();check(rig.data.animation_clips[1].start==24,"Redo restores the independently moved piece")
	press.shift_pressed=true;press.position=Vector2(app.timeline.x(28),app.timeline.row_y(1)+12);app.timeline._gui_input(press)
	motion.position=app.timeline.get_global_transform()*Vector2(app.timeline.x(36),-100);app._input(motion);app._input(release)
	check(rig.data.start_frame==8 and rig.data.animation_clips[0].start==8 and rig.data.animation_clips[1].start==32 and source_frames(rig.data,1,"@root")==[0,8,16],"Shift-drag moves all pieces/presence together while retaining source-time keys")
	app.undo();check(rig.data.start_frame==0 and rig.data.animation_clips[0].start==0 and rig.data.animation_clips[1].start==24,"Undo whole-object clip retiming restores every piece")
	await action(app,4,12)
	check(rig.data.animation_clips.size()==1 and rig.data.start_frame==24 and not app.clip_editor.clipboard.is_empty(),"Cut stores the selected piece and moves introduction to the remaining first piece")
	app.renderer.world_runtime.evaluate(23);var absent: bool=not rig.root.visible;app.renderer.world_runtime.evaluate(24)
	check(absent and rig.root.visible,"lone later block is absent before introduction and appears at its first frame")
	await action(app,0,13)
	check(rig.data.animation_clips.size()==2 and rig.data.start_frame==0 and rig.sample(4)==old.sample(4),"Paste restores an editable left piece with its source-time motion")
	await action(app,28,11);await action(app,40,13)
	check(rig.data.animation_clips.size()==3 and rig.sample(44)==old.sample(12),"Copy/Paste duplicates a motion piece into free timeline space")
	var copied: Dictionary=rig.data.animation_clips[2].duplicate(true)
	app.set_frame(28);editor.selected="@root";editor.operation.select(1);editor.refresh_values();editor.fields[0].value=5;editor.apply_numeric()
	check(rig.sample_transform(28).position[0]==5 and rig.data.animation_clips[2]==copied and rig.sample_transform(44).position[0]==old.sample_transform(12).position[0],"manual auto-key edits its owning piece without changing the copied sibling")
	app.undo();check(rig.sample_transform(28).position[0]==old.sample_transform(12).position[0],"Undo restores an edit inside a split source curve")
	app.redo()
	var current: Dictionary=rig.data.duplicate(true);history=app.history.size()
	app.clip_editor.move_piece(id,right,4,current)
	check(rig.data==current and app.history.size()==history,"overlap rejection preserves the complete document and Undo history")
	app.clip_editor.request("paste",map_id,"",20)
	check(app.renderer.world_runtime.instance(map_id).data==map_data,"clipboard cannot paste incompatible bone motion onto another source asset")
	app.world_selection.select_entity(id);app.set_frame(28)
	var expected: Image=await app.renderer.capture(app.keys,app.layers,28,true)
	var saved_world: Dictionary=World.portable(app.renderer.world_state());var saved_transforms:={};var saved_video: Dictionary=app.video.duplicate(true)
	for object_id in app.renderer.world_runtime.order:
		var object: RefCounted=app.renderer.world_runtime.instance(object_id);saved_transforms[object_id]={"root":object.root.global_transform,"bones":{}}
		for part in object.order:saved_transforms[object_id].bones[part]=object.bone_transform(part)
	var project:=folder.path_join("clips.has");app.has_project.save_file(project,"packed");await wait_job(app.has_project)
	var project_sha:=FileAccess.get_sha256(project);app.new_project();app.has_project.open_file(project);await wait_job(app.has_project);rig=app.renderer.world_runtime.instance(id)
	check(rig.data.format==Model.BODY_FORMAT and rig.data.animation_clips==JSON.parse_string(JSON.stringify(current.animation_clips,"",true,true)) and app.renderer.world_runtime.instance(map_id).data.format=="studio_model_1","normal HAS reopen retains both record versions and independent piece ownership")
	var reopened: Image=await app.renderer.capture(app.keys,app.layers,28,true)
	expected.save_png(folder.path_join("before-open.png"));reopened.save_png(folder.path_join("after-open.png"))
	var packed_pixels:=pixel_difference(expected,reopened);var exact_transforms:=true
	for object_id in app.renderer.world_runtime.order:
		var object: RefCounted=app.renderer.world_runtime.instance(object_id)
		exact_transforms=exact_transforms and object.root.global_transform==saved_transforms[object_id].root
		for part in object.order:exact_transforms=exact_transforms and object.bone_transform(part)==saved_transforms[object_id].bones[part]
	var exact_state: bool=World.portable(app.renderer.world_state())==JSON.parse_string(JSON.stringify(saved_world,"",true,true))
	var exact_media: bool=Drawing.cel_at(app.layers[1],0).image.get_data()==paint and app.keys==JSON.parse_string(JSON.stringify(shots,"",true,true)) and app.video==JSON.parse_string(JSON.stringify(saved_video,"",true,true))
	print("PACKED_CLIP_DIAGNOSTIC "+JSON.stringify({"pixels":packed_pixels,"transforms_exact":exact_transforms,"data_exact":exact_state,"media_exact":exact_media}))
	check(exact_transforms and exact_state and exact_media and packed_pixels.close,"reopened multi-piece animation retains exact data/transforms/media within existing GLB rebuild edge bounds")
	var linked:=folder.path_join("clips-linked.has");app.has_project.save_file(linked,"linked");await wait_job(app.has_project);app.new_project();app.has_project.open_file(linked);await wait_job(app.has_project)
	check(app.renderer.world_runtime.instance(id).data.animation_clips==JSON.parse_string(JSON.stringify(current.animation_clips,"",true,true)),"linked HAS also preserves all piece curves and timing")
	app.changed();app.autosave_tick(true)
	var recovery: String=app.recovery_root.path_join(app.recovery_session)
	check(not Storage.load_project(recovery).has("error") and app.open_project(recovery) and app.renderer.world_runtime.instance(id).data.format==Model.BODY_FORMAT,"actual recovery checkpoint reopens the editable clip world")
	var recovered_image: Image=await app.renderer.capture(app.keys,app.layers,28,true)
	reopened.save_png(folder.path_join("packed-preview.png"));recovered_image.save_png(folder.path_join("recovered-preview.png"))
	var recovery_pixels:=pixel_difference(reopened,recovered_image)
	check(recovery_pixels.close,"separate recovery GLB rebuild stays within existing bounded edge tolerance")
	var error: String=await app.export_movie(folder)
	check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000029.png")).get_data()==recovered_image.get_data(),"MP4 uses retimed piece evaluation with independent cel/audio")
	app.world_selection.select_entity(id);rig=app.renderer.active_model()
	app.pose_editor.set_flag("visible",false);app.renderer.world_runtime.evaluate(16)
	check(not rig.root.visible,"explicit hidden state remains authoritative through an interpreted motion gap")
	app.undo()
	var piece_ids:=[]
	for piece in rig.data.animation_clips:piece_ids.append(piece.id)
	for piece_id in piece_ids:app.clip_editor.request("delete",id,piece_id,28)
	app.renderer.world_runtime.evaluate(28)
	check(rig.data.animation_clips.is_empty() and not rig.root.visible and app.world_selection.selected==id,"deleting all pieces keeps an editable selected object absent from the rendered world")
	app.set_frame(14);editor=app.pose_editor;editor.selected="@root";editor.operation.select(1);editor.refresh_values();editor.fields[0].value=1;editor.apply_numeric()
	check(rig.data.animation_clips.size()==1 and rig.data.start_frame==14,"manual auto-key reintroduces an object after its last piece was removed")
	app.set_frame(18);editor.refresh_values();editor.fields[0].value=2;editor.apply_numeric()
	check(rig.data.animation_clips.size()==1 and rig.data.animation_clips[0].length==5 and rig.authored_keys().size()==2,"fresh authored piece grows for later manual poses without making a new block per key")
	var authored_project:=folder.path_join("authored-take.has");app.has_project.save_file(authored_project,"packed");await wait_job(app.has_project)
	for i in range(5):app.undo()
	check(rig.data.animation_clips.size()==3,"Undo restores deleted pieces and their independent motion after a new manual edit")
	app.set_frame(28)
	check(FileAccess.get_sha256(asset)==original and FileAccess.get_sha256(project)==project_sha,"piece editing/recovery/render preserves source GLB and manual packed HAS")
	await settled();root.get_texture().get_image().save_png(folder.path_join("editor.png"))
	var movie: String=app.last_export_folder.path_join("movie.mp4");var native_samples:=[];var native_world:=World.empty()
	for sample in ["pose-smoke/miku-project","source-smoke/source-project","sfm-smoke/project"]:
		var path:=ProjectSettings.globalize_path("res://output/"+sample)
		if not FileAccess.file_exists(path.path_join("project.json")):print("SKIP optional native clip fixture: "+sample);continue
		var loaded: Dictionary=Storage.load_project(path);var row: Dictionary=World.from_project(loaded).objects[-1]
		row=Support.legacy_model(row)
		row.id="native-piece-%d" % native_samples.size();row.parent_id="";row.start_frame=0;row.pose_keys=[];row.pose={};row.draft_frame=0;row.visible=true;row.reference_only=false
		app.new_project();var doc:=World.empty();doc.objects.append(row);app.restore_world(doc);app.world_selection.select_entity(row.id)
		rig=app.renderer.active_model();editor=app.pose_editor;var native_hash:=FileAccess.get_sha256(rig.data.source);var metadata: Dictionary=rig.data.metadata.duplicate(true)
		var native_bone:=""
		for candidate in rig.order:
			if str(rig.bones[candidate].name).ends_with({"pose-smoke/miku-project":"左腕","source-smoke/source-project":"L_UpperArm","sfm-smoke/project":"bip_upperArm_L"}[sample]):native_bone=candidate
		check(not native_bone.is_empty(),"native clip rig retains its actual arm identity: "+sample)
		if native_bone.is_empty():continue
		editor.tree_items[native_bone].select(0);editor.record_key();editor.frame_model();camera=app.renderer.camera;app.keys=[Timeline.key(0,camera.position,camera.quaternion,camera.fov)]
		var neutral: Image=await app.renderer.capture(app.keys,[],0,true)
		for frame in [8,16]:
			app.set_frame(frame);editor.operation.select(0);editor.refresh_values();editor.fields[2].value=45 if frame==8 else 75;editor.apply_numeric()
		var posed: Image=await app.renderer.capture(app.keys,[],16,true)
		var native_before: Dictionary=rig.data.duplicate(true);var native_old:=Model.new();native_old.data=native_before
		app.clip_editor.request("split",row.id,"",8);var native_right: String=rig.data.animation_clips[1].id
		app.clip_editor.move_piece(row.id,native_right,24,rig.data.duplicate(true))
		check(neutral.get_data()!=posed.get_data() and rig.sample(28)==native_old.sample(12) and rig.sample_transform(28)==native_old.sample_transform(12),"native skin/source curve survives split and independent move: "+sample)
		var left_piece: Dictionary=rig.data.animation_clips[0].duplicate(true);var pre_edit: Dictionary=rig.data.duplicate(true)
		app.set_frame(28);editor.tree_items[native_bone].select(0);editor.operation.select(0);editor.refresh_values();editor.fields[2].value=85;editor.apply_numeric()
		check(rig.data.animation_clips[0]==left_piece and source_frames(rig.data,1,native_bone)==[0,8,12,16],"native manual bone edit belongs only to its selected-time piece: "+sample)
		app.undo();var undo_ok: bool=rig.data==pre_edit;app.redo()
		check(undo_ok and rig.data.metadata==metadata and FileAccess.get_sha256(rig.data.source)==native_hash,"native piece Undo/provenance/source bytes remain intact: "+sample)
		var bounds: AABB=app.renderer.scene_bounds(rig.root);var factor:=2/maxf(0.001,bounds.size.y);var offset: float=native_samples.size()*3-3
		var arranged: Dictionary=rig.data.duplicate(true);arranged.position[0]+=offset;arranged.scale*=factor
		arranged.body_base_transform.position[0]+=offset;arranged.body_base_transform.scale*=factor
		for piece in arranged.animation_clips:
			piece.base_transform.position[0]+=offset;piece.base_transform.scale*=factor
			for source_key in piece.keys:source_key.transform.position[0]+=offset;source_key.transform.scale*=factor
			for control in piece.body_controls.get("@root",[]):control.value.position[0]+=offset;control.value.scale*=factor
		native_world.objects.append(arranged);native_samples.append(sample)
	var native_project:=""
	if native_samples.size()==3:
		app.restore_world(native_world);camera.position=Vector3(0,3.2,10);camera.look_at(Vector3(0,1,0),Vector3.UP);app.keys=[Timeline.key(0,camera.position,camera.quaternion,60)];app.set_frame(28)
		var native_image: Image=await app.renderer.capture(app.keys,app.layers,28,true);native_image.save_png(folder.path_join("native-pieces.png"))
		native_project=folder.path_join("native-pieces.has");app.has_project.save_file(native_project,"packed");await wait_job(app.has_project)
		app.new_project();app.has_project.open_file(native_project);await wait_job(app.has_project)
		check(World.portable(app.renderer.world_state())==JSON.parse_string(JSON.stringify(World.portable(native_world),"",true,true)),"normal packed HAS reopens combined MMD/GMod/SFM piece ownership and native metadata")
	app.new_project();app.has_project.open_file(authored_project);await wait_job(app.has_project);app.world_selection.select_entity(id);rig=app.renderer.active_model();editor=app.pose_editor
	var preserved16: Dictionary=rig.sample_transform(16)
	app.set_frame(22);editor.selected="@root";editor.operation.select(1);editor.refresh_values();editor.fields[0].value=3;editor.apply_numeric()
	check(rig.data.animation_clips.size()==1 and rig.data.animation_clips[0].auto_extend and rig.data.animation_clips[0].length==9 and rig.authored_keys().size()==3 and rig.sample_transform(16)==preserved16,"normal HAS reopen retains authored-range growth without changing its earlier motion")
	app.new_project();app.pose_editor.add_model(asset,24);rig=app.renderer.active_model();editor=app.pose_editor
	app.set_frame(4);editor.selected="@root";editor.operation.select(1);editor.refresh_values();editor.fields[0].value=1;editor.apply_numeric()
	app.renderer.world_runtime.evaluate(3);var before_intro: bool=not rig.root.visible;app.renderer.world_runtime.evaluate(4)
	check(rig.data.format=="studio_model_6" and rig.data.start_frame==4 and rig.authored_keys()[0].frame==4 and before_intro and rig.root.visible,"explicit earlier manual key corrects introduction even before an unsplit object's import frame")
	app.clip_editor.clipboard={"sha256":rig.data.sha256,"fps_num":24,"fps_den":1,"piece":copied.duplicate(true)}
	var compatible_before: Dictionary=rig.data.duplicate(true);history=app.history.size();app.video.fps_num=30
	app.clip_editor.request("paste",rig.data.id,"",20)
	check(rig.data==compatible_before and app.history.size()==history and "same frame rate" in app.status.text,"cross-project clipboard cannot silently reinterpret motion at a different FPS")
	app.video.fps_num=24;app.clip_editor.request("paste",rig.data.id,"",20)
	check(rig.data.format==Model.BODY_FORMAT and rig.data.animation_clips.size()==2 and rig.data.animation_clips[1].start==20,"same-rate compatible clipboard remains available after a rejected paste")
	var result:={"checks":checks,"failures":failures,"folder":folder,"project":project,"linked_project":linked,"movie":movie,"native_samples":native_samples,"native_project":native_project,"split_pixels":split_pixels,"packed_pixels":packed_pixels,"recovery_pixels":recovery_pixels}
	var file:=FileAccess.open("res://output/animation-clips-result.json",FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close()
	print("ANIMATION_CLIPS_SMOKE "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
