extends SceneTree
const Motion=preload("res://src/generated_secondary_motion.gd")
var app
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(100).timeout.connect(func():push_error("Generated settling reader watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;if not ok:failures+=1
	print(("PASS " if ok else "FAIL ")+label)
func settle() -> void:
	for i in range(4):await process_frame
func run() -> void:
	var args: PackedStringArray=OS.get_cmdline_user_args()
	if args.size()!=3 or DisplayServer.get_name()!="headless":quit(2);return
	var folder: String=args[0];var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(args[2]));root.size=Vector2i(1400,900);root.gui_embed_subwindows=true
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recent.json")
	root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	app.has_project.open_file(args[1])
	while app.has_project.pid>0:await process_frame
	await settle();check(app.renderer.world_runtime.order.size()==1,"fresh Studio opens self-contained saved helper")
	app.world_selection.select_entity(expected.id,false);var actor: RefCounted=app.renderer.active_model()
	check(actor!=null and actor.data.sha256==expected.sha and Motion.setting(actor.data)==expected.setting,"fresh process retains source identity and Natural setting")
	var rig: Dictionary=actor.root.get_meta("has_secondary_rig",{});var original: bool=not rig.get("chains",[]).is_empty()
	for chain in rig.get("chains",[]):
		for joint in chain.joints:original=original and joint.gravity==0. and joint.stiffness==1.
	var owned_cache: bool=actor.data.source.replace("\\","/").begins_with(folder.path_join("cache").replace("\\","/"))
	check(original and owned_cache,"packed source is restored into this reader cache with unchanged original tuning")
	var ui=app.physics_editor.generated_motion_editor;ui.sync();ui.change(0);app.undo();await settle()
	check(Motion.setting(app.renderer.active_model().data)==expected.setting,"freshly opened preset remains editable with ordinary Undo")
	print("GENERATED_SECONDARY_READER "+JSON.stringify({"checks":checks,"failures":failures,"user_profile":OS.get_user_data_dir(),"fresh_process":true,"original_tuning_preserved":original,"reader_cache_owned":owned_cache}));await app.quit_studio();quit(0 if failures==0 else 1)
