extends SceneTree
# Generated geometry; ordinary controls and both temporary wind routes.
const Fixture=preload("res://tests/generated_secondary_fixture.gd")
const GLB=preload("res://tests/secondary_fixture.gd")
const Motion=preload("res://src/generated_secondary_motion.gd")
const StudioTheme=preload("res://src/studio_theme.gd")
var app
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(140).timeout.connect(func():push_error("Generated hair controls watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;if not ok:failures+=1
	print(("PASS " if ok else "FAIL ")+label)
func settle() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func wait_for(test: Callable,seconds:=35.) -> bool:
	var end: int=Time.get_ticks_msec()+int(seconds*1000.)
	while not test.call() and Time.get_ticks_msec()<end:await process_frame
	return test.call()
func shot(path: String) -> bool:
	await settle();var image: Image=root.get_texture().get_image()
	return image!=null and image.get_size()==root.size and image.save_png(path)==OK
func active() -> RefCounted:return app.renderer.active_model()
func visible_flags(actor: RefCounted) -> Array:
	var values: Array=[]
	for mesh in actor.root.find_children("*","MeshInstance3D",true,false):values.append(mesh.visible)
	return values
func run() -> void:
	var args: PackedStringArray=OS.get_cmdline_user_args()
	if args.is_empty() or DisplayServer.get_name()=="headless":push_error("Use an owned private graphical desktop");quit(2);return
	var folder: String=args[0];root.size=Vector2i(1600,1000);root.gui_embed_subwindows=true
	var prefs:=ConfigFile.new();prefs.set_value("display","theme","light" if "--classic" in args else "neon");prefs.set_value("display","percent",100);prefs.save(folder.path_join("prefs.cfg"))
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recent.json");root.add_child(app)
	await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache");app.set_advanced("--advanced" in args)
	var source: String=folder.path_join("generated.glb");var created: Error=Fixture.create(source)
	if created==OK:
		var bytes: PackedByteArray=FileAccess.get_file_as_bytes(source);var length: int=bytes.decode_u32(12);var data: Dictionary=JSON.parse_string(bytes.slice(20,20+length).get_string_from_utf8())
		data.extras.has_secondary_helpers_1.springs=data.extras.has_secondary_helpers_1.springs.slice(0,1)
		created=GLB.write_glb(source,Fixture.json_integers(data),bytes.slice(28+length))
	check(created==OK,"generated fixture has configured hair and an unconfigured clothing part")
	var sha: String=FileAccess.get_sha256(source)
	check(app.pose_editor.add_model(source).is_empty(),"ordinary Add model opens generated fixture")
	app.pose_editor.frame_model();await settle()
	var ui=app.physics_editor.generated_motion_editor;ui.sync()
	check(ui.choice.is_visible_in_tree() and not ui.choice.disabled and ui.choice.selected==0 and app.advanced_mode==("--advanced" in args) and StudioTheme.style==("light" if "--classic" in args else "neon"),"visible Keep shape control uses the requested actual theme and workspace")
	var history: int=app.history.size();ui.choice.get_popup().popup();await process_frame;ui.choice.get_popup().hide();ui.choice.select(1);ui.choice.item_selected.emit(1);await settle()
	check(Motion.setting(active().data).mode=="natural" and app.history.size()==history+1,"actual dropdown signal applies Natural gravity as one edit")
	check(ui.choice.get_global_rect().size.x>=145 and Rect2(Vector2.ZERO,Vector2(root.size)).encloses(ui.choice.get_global_rect()),"complete preset control fits the ordinary interface")
	var baseline: PackedByteArray=var_to_bytes(active().data);var visible: Array=visible_flags(active());history=app.history.size()
	var pictures:=await shot(folder.path_join("controls.png"))
	app.physics_editor.hair_toggle.button_pressed=true
	var started: bool=await wait_for(func():return app.physics_editor.active(active().data.id) and app.physics_editor.pending.is_empty())
	var simulation: RefCounted=app.physics_editor.simulations.get(active().data.id)
	check(started and simulation!=null and simulation.runner.chains[0].natural_gravity and simulation.runner.chains[0].world_airflow,"actual Hair & clothes control starts selected Natural tuning")
	app.physics_editor.hair_toggle.button_pressed=false;await settle()
	check(active().live_pose==null and var_to_bytes(active().data)==baseline,"ordinary Off restores authored state without baking the preview")
	var review: Node=app.local_wind_review;review.button.pressed.emit();await settle();ui.sync()
	check(is_instance_valid(review.window) and review.master.disabled and ui.choice.disabled,"local wind opens while preset editing is safely disabled")
	review.wind_check.button_pressed=true;review.master.button_pressed=true
	var local_running: bool=await wait_for(func():return review.phase=="running")
	check(local_running and review.simulation!=null and not review.simulation.runner.preview_context.is_empty() and review.simulation.runner.chains[0].natural_gravity and review.simulation.runner.chains[0].world_airflow,"Review local wind inherits generated mode and world direction")
	pictures=await shot(folder.path_join("local-wind.png")) and pictures
	active().data.metadata[Motion.KEY].mode="keep_shape"
	var stopped: bool=await wait_for(func():return review.phase=="stopped")
	active().data.metadata[Motion.KEY].mode="natural";review.close();await settle()
	check(stopped and review.simulation==null and visible_flags(active())==visible and var_to_bytes(active().data)==baseline,"stale source tuning stops local preview and restores its borrowed owner")
	var helper: Node=app.physics_editor.helper_editor;helper.button.pressed.emit();await wait_for(func():return helper.pid<=0);await settle()
	var selected:=-1
	for i in range(helper.assessment.get("regions",[]).size()):
		var row: Dictionary=helper.assessment.regions[i]
		if not row.already_rigged and "skirt" in str(row.anchor_name).to_lower():selected=i;break
	check(selected>=0,"ordinary loose-part review finds the unconfigured generated clothing part")
	if selected<0:helper.close();await app.quit_studio();quit(1);return
	helper.parts.select(selected);helper.parts.item_selected.emit(selected);await wait_for(func():return helper.pid<=0);await settle()
	check(helper.preview_ready and helper.preview.get("can_apply",false),"ordinary reviewed part is ready for temporary Try a local blow")
	helper.try_wind.button_pressed=true
	var pending_running: bool=await wait_for(func():return helper.pending_preview.phase=="running",70.)
	var player: Node=helper.pending_preview.player
	check(pending_running and player.simulation!=null and not player.simulation.runner.preview_context.is_empty() and player.simulation.runner.chains[0].natural_gravity and player.simulation.runner.chains[0].world_airflow,"Try a local blow inherits Natural tuning before Apply")
	pictures=await shot(folder.path_join("pending-wind.png")) and pictures
	helper.try_wind.button_pressed=false;helper.close();await settle()
	check(var_to_bytes(active().data)==baseline and app.history.size()==history and visible_flags(active())==visible,"stopping and closing both try-outs creates no authored edits or visibility loss")
	check(FileAccess.get_sha256(source)==sha and app.renderer.native_readbacks==0,"generated source remains unchanged and native readbacks are balanced")
	check(pictures,"all three whole-interface captures are retained for visual review")
	print("GENERATED_SECONDARY_CONTROLS "+JSON.stringify({"checks":checks,"failures":failures,"user_profile":OS.get_user_data_dir(),"classic":not StudioTheme.is_neon(),"advanced":app.advanced_mode,"captures":3,"owner_assets_used":false}));await app.quit_studio();quit(0 if failures==0 else 1)
