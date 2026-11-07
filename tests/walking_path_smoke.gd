extends "res://tests/movement_path_smoke.gd"
const Walking=preload("res://src/walking_animation.gd")
const Paths=Walking.Evaluator.Paths
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
const Timeline=preload("res://src/timeline.gd")
func _initialize() -> void:
	create_timer(230).timeout.connect(func():push_error("Walking app watchdog");quit(2));call_deferred("run")
func rig():return app.renderer.active_model()
func run() -> void:
	folder=OS.get_cmdline_user_args()[0];app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("reader-cache" if "--read" in OS.get_cmdline_user_args() else "writer-cache")
	if "--read" in OS.get_cmdline_user_args():
		app.has_project.open_file(folder.path_join("Walking.has"));await wait_job();var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")));var actor=app.renderer.world_runtime.instances.values()[0];app.world_selection.select_entity(actor.data.id)
		check(Walking.active(actor.data) and actor.data.motion_assist.walking.lift==.1 and actor.data.motion_assist.format==Walking.ASSIST_FORMAT and str(actor.data.source).begins_with(app.has_project.cache_root),"fresh packed Open restores active walking and correction intent without original/writer cache")
		var picture: Image=await app.renderer.capture(app.keys,app.layers,12,true);check(picture.get_data()==Image.load_from_file(folder.path_join("walking12.png")).get_data(),"cold final render exactly reproduces saved walking/camera/drawing")
		check(Storage.image_hash(Drawing.image(Drawing.cel_at(app.layers[1],0)))==expected.art,"independent editable drawing survives walking cold Open")
		var before: Dictionary=actor.data.duplicate(true);var root_before=app.renderer.world_runtime.root;var frame_before: int=app.frame;var broken: Dictionary=app.current_world();var leg: String=actor.contact_legs()[0].ids[0];var keyed: Dictionary=Paths.Components.put_bones(before,24,{leg:Model.identity()},"ease",48).data
		for i in range(broken.objects.size()):
			if broken.objects[i].id==before.id:broken.objects[i]=keyed
		var bad_folder:=folder.path_join("bad-walk");var error:=Storage.save_project(bad_folder,app.video,app.keys,app.layers,"",app.frame,{}, {},{},true,broken)
		check(error.is_empty() and not app.open_project(bad_folder) and app.renderer.world_runtime.root==root_before and rig().data==before and app.frame==frame_before,"unsupported saved walking refuses before replacing current world/editor state")
		print("WALKING_PATH_READ "+JSON.stringify({"checks":checks,"failures":failures}));await app.quit_studio();quit(0 if failures==0 else 1);return
	var source:=folder.path_join("source-figure.glb");DirAccess.copy_absolute("res://examples/tutorials/Practice figure.glb",source);var source_sha:=FileAccess.get_sha256(source);app.new_project();check(app.pose_editor.add_model(source).is_empty(),"ordinary Add model imports original practice figure")
	await settled();app.physics_editor.freeze_all();app.physics_editor.clear_previews();app.mode.select(2);app.change_mode(2);app.world_selection.select_entity(rig().data.id);app.world_selection.context_action(1);await settled()
	var actor=rig();var original: Dictionary=actor.data.duplicate(true);var route: Dictionary=Paths.change(original,0,Vector3.ZERO,48).data;route=Paths.change(route,48,Vector3(0,0,.6),48).data;check(app.pose_editor.restore_state(route).is_empty(),"normal Reset pose and authored path preserve neutral starting keys")
	app.renderer.camera.position=Vector3(2,1.4,4);app.renderer.camera.look_at(Vector3(0,.9,.3),Vector3.UP);app.keys=[Timeline.from_camera(0,app.renderer.camera,"ease"),Timeline.from_camera(48,app.renderer.camera,"ease")]
	var art:=Drawing.blank(1920,1080);art.fill_rect(Rect2i(170,180,70,50),Color(0,1,1,.6));Drawing.insert(app.layers[1],0,48,art);app.changed();app.set_frame(0);await settled()
	var editor=app.pose_editor.movement_path;var before: Dictionary=actor.data.duplicate(true);var history: int=app.history.size();var before_frame: int=app.frame;var view: Dictionary=app.renderer.view_state();var shots: Array=app.keys.duplicate(true);var art_sha:=Storage.image_hash(art)
	var unassisted: Image=await app.renderer.capture(app.keys,app.layers,12,true);app.set_frame(before_frame);app.renderer.restore_view(view);editor.open();await settled()
	check(editor.window.visible and editor.walking_enabled.visible and not editor.walking_enabled.button_pressed,"Simple movement path offers explicit optional walking")
	editor.frame.value=12;editor.walking_enabled.button_pressed=true;await settled();check(Walking.active(editor.draft) and actor.data==before and app.history.size()==history,"walking choice stages saved intent without touching scene/history")
	editor.walk_preview.pressed.emit();await settled();check(actor.preview_frame==12 and not actor.preview_pose.is_empty() and app.frame==12 and actor.data==before,"preview shows derived pose at shared frame without authoring keys")
	var staged: Image=await app.renderer.capture(app.keys,app.layers,12,true);check(staged.get_data()==unassisted.get_data(),"unapplied preview cannot leak into final/export sampling")
	editor.close();await settled();check(actor.preview_frame==-1 and actor.preview_pose.is_empty() and actor.data==before and app.history.size()==history and app.frame==before_frame and app.renderer.view_state()==view,"Cancel restores prior pose/playhead/view with source/history intact")
	app.set_advanced(true);editor.open();await settled();editor.walking_enabled.button_pressed=true;editor.walk_values.lift.value=10;await settled();check(editor.walk_values.lift.is_visible_in_tree() and editor.draft.motion_assist.walking.lift==.1,"Advanced corrects foot lift before committing suggestion")
	var saved: Dictionary=editor.draft.duplicate(true);editor.frame.value=12;await click(editor.apply_button);await settled()
	check(not is_instance_valid(editor.window) and actor.data==saved and app.history.size()==history+1 and Walking.active(actor.data),"Apply commits path/walking correction as one ordinary Undo")
	var animated: Image=await app.renderer.capture(app.keys,app.layers,12,true);animated.save_png(folder.path_join("walking12.png"));check(animated.get_data()!=unassisted.get_data(),"saved walking visibly changes final character pose")
	app.undo();check(actor.data==before and not Walking.active(actor.data),"Undo restores prior authored model and keys exactly")
	app.redo();check(actor.data==saved and Walking.active(actor.data),"Redo restores walking intent and correction exactly")
	check(app.keys==shots and Storage.image_hash(art)==art_sha and FileAccess.get_sha256(source)==source_sha,"walking edits preserve camera/drawing/original GLB")
	app.set_frame(0);var zero: Dictionary=actor.sample_transform(0);var source_probe:=Model.new();source_probe.data=before;source_probe.motion_video=app.video;check(zero==source_probe.sample_authored_transform(0) and actor.sample(0)==source_probe.sample_body(0),"neutral starting keys remain exact before walking eases in")
	app.set_frame(12);app.autosave_tick(true);await preload("res://tests/recovery_wait.gd").checkpoint(app);await settled();var recovered:=Storage.load_project(app.recovery_root.path_join(app.recovery_session));check(not recovered.has("error") and Walking.active(recovered.world.objects[0]),"real recovery checkpoint persists walking intent")
	app.has_project.save_file(folder.path_join("Walking.has"),"packed");await wait_job();check(FileAccess.file_exists(folder.path_join("Walking.has")),"ordinary packed save includes walking settings and original model")
	var movie_error: String=await app.export_movie(folder);var movie: String=app.last_finished_movie;check(movie_error.is_empty() and FileAccess.file_exists(movie),"ordinary MP4 exports saved walking through shared evaluator")
	var rendered:=Image.load_from_file(app.last_export_folder.path_join("frame_000013.png"));check(rendered.get_data()==animated.get_data(),"movie input exactly agrees with final walking preview plus independent drawing")
	app.set_frame(12);editor.open();await settled();check(editor.window.get_visible_rect().encloses(editor.apply_button.get_global_rect()),"reopened Advanced path keeps Apply fully reachable after export")
	editor.walking_enabled.button_pressed=false;await click(editor.apply_button);await settled();check(not Walking.active(actor.data) and actor.sample(12)==source_probe.sample_body(12) and actor.sample_transform(12)==source_probe.sample_authored_transform(12),"explicit walking off restores authored animation without deleting source keys")
	app.undo();check(actor.data==saved,"Undo after disabling restores full walking intent")
	if not actor.data.has("motion_assist"):await app.quit_studio();quit(1);return
	var bad: Dictionary=actor.data.duplicate(true);bad.motion_assist.walking.amount="bad";var current: Dictionary=actor.data.duplicate(true);check(not app.pose_editor.restore_state(bad).is_empty() and actor.data==current,"malformed walking edit refuses atomically in actual app")
	FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify({"art":art_sha,"movie":movie,"source_sha256":source_sha}));print("WALKING_PATH_SMOKE "+JSON.stringify({"checks":checks,"failures":failures,"movie":movie}));await app.quit_studio();quit(0 if failures==0 else 1)
