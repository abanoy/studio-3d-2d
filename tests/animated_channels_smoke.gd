extends SceneTree
const Support=preload("res://tests/world_test_support.gd")
const Channels=preload("res://src/animated_channels.gd")
const SceneIO=preload("res://src/scene3d.gd")
const Model=preload("res://src/model.gd")
const Clips=preload("res://src/animation_clips.gd")
const World=preload("res://src/world_document.gd")
const Storage=preload("res://src/storage.gd")
const Timeline=preload("res://src/timeline.gd")
const Drawing=preload("res://src/drawing.gd")
var checks:=0
var failures:=0

func _initialize() -> void:
	create_timer(110).timeout.connect(func():push_error("Animated-channel watchdog expired");quit(2))
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

func click(app,point: Vector2, button:=MOUSE_BUTTON_LEFT,routed:=false) -> void:
	var event:=InputEventMouseButton.new();event.button_index=button;event.pressed=true
	event.position=app.timeline.get_global_transform()*point if routed else point
	if routed:app.get_viewport().push_input(event,true)
	else:app.timeline._gui_input(event)
	await settled();event.pressed=false
	if routed:app.get_viewport().push_input(event,true)
	else:app.timeline._gui_input(event)
	await settled()

func find_channel(rows: Array,id: String) -> Dictionary:
	for row in rows:
		if row.id==id:return row
	return {}

func pixel_difference(a: Image,b: Image) -> Dictionary:
	var aa:=a.get_data();var bb:=b.get_data();var count:=0;var total:=0
	for i in range(aa.size()):
		if aa[i]!=bb[i]:count+=1;total+=absi(int(aa[i])-int(bb[i]))
	return {"channels":count,"mean":float(total)/aa.size(),"close":count<=384 and float(total)/aa.size()<0.002}

func run() -> void:
	var folder:=ProjectSettings.globalize_path("res://output/animated-channels/run_%d" % Time.get_ticks_usec());DirAccess.make_dir_recursive_absolute(folder)
	var asset:=folder.path_join("日本語.glb");SceneIO.make_pose_fixture(asset,["センター","左腕"]);var digest:=FileAccess.get_sha256(asset)
	var held:=Model.definition(asset);held.pose_keys=[{"frame":0,"pose":{},"transform":Clips.transform(held),"interpolation":"hold"},{"frame":8,"pose":{},"transform":Clips.transform(held),"interpolation":"hold"}]
	var held_rows:=Channels.describe(held)
	check(held_rows.size()==1 and held_rows[0].id=="@root" and held_rows[0].frames==[0,8],"old neutral hold keys remain inspectable without empty disclosure rows")
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled()
	app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	app.pose_editor.add_model(asset);var id: String=app.last_import_id
	app.pose_editor.add_model(asset);var peer: String=app.last_import_id
	# Separate identical authored meshes; overlapping coplanar peers are not a stable pixel fixture.
	app.renderer.active_model().data.position[0]=3;app.world_selection.select_entity(id)
	var rig: RefCounted=app.renderer.active_model();var arm: String=rig.order[1];var center: String=rig.order[0];var editor=app.pose_editor;var timeline=app.timeline
	editor.record_key()
	for at in [4,8]:
		app.set_frame(at);editor.tree_items[arm].select(0);editor.operation.select(0);editor.refresh_values();editor.fields[2].value=at*7;editor.apply_numeric()
	check(rig.authored_keys()[1].authored_channels==[arm] and rig.authored_keys()[2].authored_channels==[arm],"new manual edits identify only the bone actually changed")
	app.set_frame(12);editor.set_visibility_key(false)
	var rows:=Channels.describe(rig.data)
	check(rows.size()==3 and find_channel(rows,center).is_empty() and not find_channel(rows,arm).is_empty(),"expanded index contains authored root, arm and visibility without unused center bone")
	var advanced_rows:=Channels.describe(rig.data,true)
	check(find_channel(rows,arm).label=="Left upper arm" and not arm in find_channel(rows,arm).tooltip and arm in find_channel(advanced_rows,arm).tooltip and "左腕" in find_channel(advanced_rows,arm).label,"Simple channel uses a body name and Advanced reveals native identity")
	check(find_channel(rows,arm).frames==[0,4,8] and find_channel(rows,"@root").frames==[0] and find_channel(rows,"@visibility").frames==[12],"recorded rest, independent part keys and visibility addresses stay distinct")
	editor.frame_model();app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,60)];app.set_frame(4)
	var before: Dictionary=rig.data.duplicate(true);var history: int=app.history.size();var camera: Transform3D=app.renderer.camera.transform
	check(not app.advanced_mode and timeline.visual_rows.size()==2 and timeline.expanded.is_empty(),"Simple starts with one collapsed row per object")
	var timeline_dock: ScrollContainer=app.workspace_layout.panels.timeline.get_node("TimelineContentScroll")
	timeline_dock.ensure_control_visible(timeline.get_parent());await settled()
	check(timeline_dock.get_global_rect().encloses(timeline.get_parent().get_global_rect()),"compressed Timeline scrolls complete channel editing area into view")
	await click(app,Vector2(9,timeline.row_y(0)+12),MOUSE_BUTTON_LEFT,true)
	check(timeline.expanded.get(id,false) and timeline.visual_rows.size()==5 and timeline.channel_y(id,arm)>=0,"routed disclosure click expands only animated channels")
	check(rig.data==before and app.history.size()==history and app.renderer.camera.transform==camera,"expanding rows changes no animation, history or temporary view")
	check(timeline.row_y(1)==4*timeline.ROW_HEIGHT and timeline.object_rows.size()==2,"following object rows map below expanded channels without changing domain order")
	await click(app,Vector2(45,timeline.row_y(1)+12))
	check(app.renderer.active_instance_id==peer,"clicking a following row still selects the correct peer object")
	editor.search.text="unrelated";editor.search.text_changed.emit("unrelated")
	await click(app,Vector2(timeline.x(8),timeline.channel_y(id,arm)+12))
	check(app.renderer.active_instance_id==id and editor.selected==arm and app.frame==8 and editor.search.text.is_empty(),"channel key click selects the actual bone and frame through a filtered inspector")
	check(timeline.selected_channel==arm and timeline.moving_id.is_empty() and not timeline.dragging,"channel inspection highlights its row without moving an animation block")
	check(app.renderer.camera.transform==camera and rig.data==before and app.history.size()==history,"part/key inspection preserves shot, model data and Undo history")
	editor.tree_items["@root"].select(0);await settled()
	check(timeline.selected_channel=="@root","bone-tree selection highlights the matching expanded channel")
	var frame_before: int=app.frame
	await click(app,Vector2(timeline.x(14),timeline.channel_y(id,arm)+12),MOUSE_BUTTON_RIGHT)
	check(timeline.import_menu.visible and timeline.import_menu.is_item_disabled(timeline.import_menu.get_item_index(10)) and app.frame==frame_before,"channel context retains timeline import and disables destructive whole-piece operations")
	timeline.import_menu.hide();await settled()
	await click(app,Vector2(45,timeline.channel_y(id,"@visibility")+12))
	check(timeline.selected_channel=="@visibility" and app.frame==frame_before and rig.data==before,"visibility channel selects for inspection without changing state or frame")
	timeline.interactive=false;await click(app,Vector2(9,timeline.row_y(0)+12));timeline.interactive=true
	check(timeline.expanded.get(id,false),"export-locked timeline cannot change expansion or selection")
	var old:=Support.legacy_model(before);old.pose_keys=Support.keys(before)
	for key in old.pose_keys:key.erase("authored_channels")
	var legacy_rows:=Channels.describe(old)
	check(find_channel(legacy_rows,arm).estimated and find_channel(legacy_rows,center).is_empty(),"older snapshots infer meaningful part rows without inventing unused joints")
	var bad:=old.duplicate(true);bad.pose_keys[0].authored_channels=[arm,arm]
	check(not Model.validate(bad,48).is_empty(),"duplicate channel hints are rejected")
	bad=old.duplicate(true);bad.pose_keys[0].authored_channels=["missing::bone"]
	check(not editor.restore_state(bad).is_empty() and rig.data==before,"unknown channel bindings fail without replacing the live pose")
	app.set_frame(8);editor.selected="@root";editor.operation.select(1);editor.refresh_values();editor.fields[0].value+=1;editor.apply_numeric()
	var merged: Array=rig.authored_keys()[-1].authored_channels
	check("@root" in merged and arm in merged,"editing another part at the same frame retains prior authored channel identity")
	app.undo();check(rig.data==before,"Undo restores channel annotations together with the actual transform")
	app.clip_editor.request("split",id,"",4);var right: String=rig.data.animation_clips[1].id
	app.clip_editor.move_piece(id,right,16,rig.data.duplicate(true))
	rows=Channels.describe(rig.data)
	check(find_channel(rows,arm).frames==[0,16,20] and timeline.channel_y(id,arm)>=0,"split and moved pieces update source-time channel key addresses")
	check(rig.data.visibility_keys[0].frame==12 and find_channel(rows,"@visibility").frames==[12],"motion retiming leaves the independent visibility channel at its original time")
	app.undo();app.undo();check(rig.data==before,"existing stable-ID Undo restores motion and channel hints after structural editing")
	await click(app,Vector2(9,timeline.row_y(0)+12))
	check(not timeline.expanded.get(id,false) and timeline.visual_rows.size()==2 and timeline.row_y(1)==timeline.ROW_HEIGHT,"collapse restores ordinary object layout and preserves both objects")
	await click(app,Vector2(9,timeline.row_y(0)+12))
	app.set_frame(0);app.create_cel(false);Drawing.stroke(Drawing.image(Drawing.cel_at(app.layers[1],0)),Vector2(80,80),Vector2(180,80),5,Color.RED,false);app.changed()
	var wav:=ProjectSettings.globalize_path("res://output/fixtures/voice — тест.wav")
	if FileAccess.file_exists(wav):
		check(app.import_audio(wav).is_empty(),"channel fixture retains independent audio")
		app.audio_clip.start_frame=24;app.audio_clip.gain_db=-6;app.rebuild_audio()
	app.set_frame(8);var expected: Image=await app.renderer.capture(app.keys,app.layers,8,true)
	expected.save_png(folder.path_join("before-reopen.png"))
	var original_world: Dictionary=World.portable(app.renderer.world_state())
	await settled();root.get_texture().get_image().save_png(folder.path_join("expanded.png"))
	var project:=folder.path_join("channels.has");app.has_project.save_file(project,"packed");await wait_job(app.has_project)
	app.new_project();await settled()
	check(timeline.visual_rows.is_empty() and timeline.object_positions.is_empty(),"New clears old expanded row addresses before the next draw")
	app.has_project.open_file(project);await wait_job(app.has_project);app.world_selection.select_entity(id);rig=app.renderer.active_model()
	check(rig.authored_keys()[1].authored_channels==[arm] and timeline.visual_rows.size()==2 and timeline.expanded.is_empty(),"packed HAS retains native independent controls while expansion remains editor-only")
	check(World.portable(app.renderer.world_state())==JSON.parse_string(JSON.stringify(original_world,"",true,true)),"packed HAS preserves all object transforms, poses, visibility and provenance with channel hints")
	app.changed();app.autosave_tick(true);await preload("res://tests/recovery_wait.gd").checkpoint(app)
	var recovery: String=app.recovery_root.path_join(app.recovery_session)
	check(not Storage.load_project(recovery).has("error") and app.open_project(recovery),"recovery preserves channel annotations and existing motion/visibility")
	app.set_frame(8);var recovered: Image=await app.renderer.capture(app.keys,app.layers,8,true)
	recovered.save_png(folder.path_join("after-recovery.png"));var pixels:=pixel_difference(expected,recovered);print("CHANNEL_RECOVERY_PIXELS "+JSON.stringify(pixels))
	check(pixels.close,"recovery GLB rebuild retains the frame within the existing bounded GPU edge tolerance")
	var error: String=await app.export_movie(folder)
	check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000009.png")).get_data()==recovered.get_data(),"MP4 samples existing motion/camera/cels identically after channel inspection")
	var movie: String=app.last_export_folder.path_join("movie.mp4");var native_samples:=[]
	for sample in ["pose-smoke/miku-project","source-smoke/source-project","sfm-smoke/project"]:
		var path:=ProjectSettings.globalize_path("res://output/"+sample)
		if not FileAccess.file_exists(path.path_join("project.json")):print("SKIP optional native channel fixture: "+sample);continue
		var loaded: Dictionary=Storage.load_project(path);var row: Dictionary=World.from_project(loaded).objects[-1]
		row=Support.legacy_model(row)
		row.id="native-channels";row.parent_id="";row.start_frame=0;row.format="studio_model_1";row.pose_keys=[];row.pose={};row.draft_frame=0;row.visible=true;row.reference_only=false
		for field in ["animation_clips","visibility_keys","presence_offset"]:row.erase(field)
		var metadata: Dictionary=row.metadata.duplicate(true);var native_sha:=FileAccess.get_sha256(row.source)
		app.new_project();var document:=World.empty();document.objects.append(row);app.restore_world(document);app.world_selection.select_entity(row.id);rig=app.renderer.active_model()
		var native_arm:=""
		for candidate in rig.order:
			if str(rig.bones[candidate].name).ends_with({"pose-smoke/miku-project":"左腕","source-smoke/source-project":"L_UpperArm","sfm-smoke/project":"bip_upperArm_L"}[sample]):native_arm=candidate
		check(not native_arm.is_empty(),"native channel retains arm binding: "+sample)
		if native_arm.is_empty():continue
		editor.frame_model();app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,60)]
		var neutral: Image=await app.renderer.capture(app.keys,[],0,true)
		app.set_frame(8);editor.tree_items[native_arm].select(0);editor.operation.select(0);editor.refresh_values();editor.fields[2].value=45;editor.apply_numeric()
		var posed: Image=await app.renderer.capture(app.keys,[],8,true)
		await click(app,Vector2(9,timeline.row_y(0)+12))
		rows=Channels.describe(rig.data)
		check(rows.size()==1 and rows[0].id==native_arm and timeline.visual_rows.size()==2 and posed.get_data()!=neutral.get_data(),"native arm channel expands without hundreds of inactive bones: "+sample)
		await click(app,Vector2(timeline.x(8),timeline.channel_y(row.id,native_arm)+12))
		check(editor.selected==native_arm and app.frame==8 and rig.data.metadata==metadata and FileAccess.get_sha256(row.source)==native_sha,"native row selection preserves binding, provenance and original bytes: "+sample)
		native_samples.append(sample)
		if sample=="pose-smoke/miku-project":
			var dense: Dictionary=rig.data.duplicate(true);var piece: Dictionary=dense.animation_clips[Clips.index_at(dense,8)]
			var values: Dictionary=rig.sample(8);var source_frame:=int(piece.source_in)+8-int(piece.start)
			for part in rig.order:piece.body_controls[part]=[{"frame":source_frame,"value":values.get(part,Model.identity()).duplicate(true),"interpolation":"ease"}]
			editor.restore_state(dense);app.refresh_timeline();await settled()
			var scroll: ScrollContainer=timeline.get_parent();scroll.scroll_vertical=100000;await settled()
			var dense_rows:=Channels.describe(rig.data);var last: String=dense_rows[-1].id
			check(dense_rows.size()==rig.order.size() and scroll.size.y<230 and app.canvas.size.y>100 and app.timeline_ruler.global_position.y<scroll.global_position.y,"many explicitly keyed native parts scroll inside a bounded timeline with pinned ruler")
			await click(app,Vector2(45,timeline.channel_y(row.id,last)+12),MOUSE_BUTTON_LEFT,true)
			check(editor.selected==last and timeline.selected_channel==last,"routed click selects the last scrolled native channel by its original binding")
			app.undo();await settled();check(Channels.describe(rig.data).size()==1,"Undo invalidates expanded channel cache and removes obsolete rows")
	check(FileAccess.get_sha256(asset)==digest,"channel UI never rewrites the authored source asset")
	var report:={"checks":checks,"failures":failures,"folder":folder,"project":project,"movie":movie,"native_samples":native_samples,"recovery_pixels":pixels}
	var file:=FileAccess.open(ProjectSettings.globalize_path("res://output/animated-channels-result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(report));file.close()
	print("ANIMATED_CHANNELS "+JSON.stringify(report));app.queue_free();await process_frame;quit(0 if failures==0 else 1)
