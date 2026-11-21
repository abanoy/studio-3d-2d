extends SceneTree
const Model=preload("res://src/model.gd")
const Fixture=preload("res://tests/posed_bounds_fixture.gd")
var app
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func _initialize() -> void:
	create_timer(180).timeout.connect(func():push_error("Bounds integration watchdog");quit(2));call_deferred("run")
func settle() -> void:
	for i in range(4):await process_frame
func setup_app(folder: String) -> void:
	root.size=Vector2i(1600,1000);root.gui_embed_subwindows=true
	var prefs:=ConfigFile.new();prefs.set_value("display","theme","light" if "--classic" in OS.get_cmdline_user_args() else "neon");prefs.set_value("display","percent",150 if "--150" in OS.get_cmdline_user_args() else 100);prefs.save(folder.path_join("prefs.cfg"))
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recent.json");root.add_child(app);await settle()
	app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache");app.set_advanced("--advanced" in OS.get_cmdline_user_args());await settle()
func wait_project() -> void:
	while app.has_project.pid>0:await process_frame
	await settle()
func first_actor() -> RefCounted:
	if not app.renderer.world_runtime or app.renderer.world_runtime.order.is_empty():return null
	var id: String=app.renderer.world_runtime.order[0];app.world_selection.select_entity(id,false);return app.renderer.active_model()
func mesh_for(actor: RefCounted) -> MeshInstance3D:
	var rows: Array=actor.root.find_children("*","MeshInstance3D",true,false)
	return rows[0] if not rows.is_empty() else null
func mask_margin_matches(mesh: MeshInstance3D) -> bool:
	app.world_selection._process(0.)
	for entry in app.world_selection.entries:
		if entry.original==mesh:return entry.copy.extra_cull_margin==mesh.extra_cull_margin
	return false
func pose_actor(actor: RefCounted) -> void:
	app.mode.select(2);app.change_mode(2);app.pose_editor.selected=actor.order[0]
	var before: Dictionary=actor.data.duplicate(true);app.pose_editor.set_delta(Vector3(5,0,0),Quaternion.IDENTITY);app.pose_editor.commit(before,false)
func shutdown() -> void:
	await app.quit_studio();quit(0 if failures==0 else 1)
func run() -> void:
	var args:=OS.get_cmdline_user_args()
	if args.is_empty() or DisplayServer.get_name()!="headless":push_error("Owned headless data folder required");quit(2);return
	var folder: String=args[0];await setup_app(folder);var source: String=folder.path_join("synthetic.glb")
	check(Fixture.write(source)==OK,"synthetic weighted shape fixture exports without native source")
	var original: String=FileAccess.get_sha256(source)
	check(app.pose_editor.add_model(source).is_empty(),"ordinary Add model installs generated GLB")
	var actor: RefCounted=first_actor();var mesh: MeshInstance3D=mesh_for(actor)
	check(actor!=null and mesh!=null and actor.render_bounds_diagnostics().active,"ordinary installed Model automatically owns a render cache")
	check(not actor.data.has("render_bounds") and not actor.data.metadata.has("render_bounds"),"render cache is not persisted into model document")
	var initial: Dictionary=actor.data.duplicate(true);var history: int=app.history.size();pose_actor(actor)
	check(app.history.size()==history+1 and actor.data.pose!=initial.pose,"ordinary pose commit authors exactly its existing history command")
	var posed: Dictionary=actor.data.duplicate(true);var margin: float=mesh.extra_cull_margin
	check(margin>4.9 and actor.render_bounds_diagnostics().error.is_empty() and mask_margin_matches(mesh),"pose commit refreshes render and selection-mask instance bounds automatically")
	app.undo();check(actor.data==initial and mesh.extra_cull_margin<.001,"ordinary Undo restores both authored state and derived rest bounds")
	app.redo();check(actor.data==posed and mesh.extra_cull_margin==margin,"ordinary Redo reconstructs derived bound from restored pose")
	var descriptor: Dictionary=actor.root.get_meta(Model.Shape.META,{});var rows: Array=descriptor.get("rows",[])
	check(rows.size()==1 and rows[0].names.size()==1,"loaded GLB exposes its actual supported shape channel")
	var values: Dictionary={str(rows[0].node):{"0":.5}}
	check(app.pose_editor.set_shape_amounts(values).is_empty(),"ordinary expression edit applies through shared shape path")
	var shape_box: AABB=mesh.custom_aabb
	check(mesh.has_meta("has_shape_bounds") and shape_box==mesh.get_meta("has_shape_bounds") and actor.render_bounds_diagnostics().active,"shape owner retains custom_aabb while render envelope remains active")
	var warm: Dictionary=actor.render_bounds_diagnostics()
	var state: PackedByteArray=var_to_bytes(actor.data);history=app.history.size()
	for i in range(100):actor.apply_current(app.frame,true)
	var steady: Dictionary=actor.render_bounds_diagnostics()
	check(steady.stats.hot_array_reads==0 and steady.stats.inventory_array_reads==warm.stats.inventory_array_reads and steady.stats.margin_writes==warm.stats.margin_writes,"one hundred ordinary pose updates do no array rescan or repeated margin write")
	actor.root.get_parent().transform=Transform3D(Basis(Vector3.UP,.2).scaled(Vector3.ONE*2),Vector3(2,1,-3));actor.apply_current(app.frame,true)
	check(mesh.custom_aabb==shape_box and actor.render_bounds_diagnostics().error.is_empty(),"uniform ancestor movement leaves morph-bound ownership intact")
	check(var_to_bytes(actor.data)==state and app.history.size()==history,"warm refresh and ancestor movement do not add authored state or Undo")
	actor.root.get_parent().transform=Transform3D.IDENTITY
	actor.live_pose={actor.order[0]:{"position":[-3,0,0],"rotation_xyzw":[0,0,0,1]}};actor.apply_current(app.frame,true)
	check(mesh.extra_cull_margin>2.9 and mesh.extra_cull_margin<3.1,"ordinary live-pose apply follows current deformed bound")
	actor.live_pose=null;actor.apply_current(app.frame,true)
	check(mesh.extra_cull_margin>4.9 and mesh.custom_aabb==shape_box,"clearing live pose restores authored envelope and shape bounds")
	check(FileAccess.get_sha256(source)==original,"source GLB remains byte-identical after posing and shaping")
	var packed: String=folder.path_join("Bounds.has");app.has_project.save_file(packed,"packed");await wait_project()
	check(app.has_project.path==packed and FileAccess.file_exists(packed),"ordinary packed save succeeds with transient bound cache active")
	check(not JSON.stringify(app.project_snapshot()).contains("render_bounds"),"project snapshot excludes transient cache and its diagnostics")
	app.new_project();await settle()
	check(not actor.render_bounds_diagnostics().active and app.renderer.native_readbacks==0,"New disposes previous model cache with no unbalanced native readback")
	if checks!=20:push_error("Expected20 actual-app integration controls");quit(2);return
	print("POSED_BOUNDS_APP "+JSON.stringify({"checks":checks,"failures":failures,"user_profile":OS.get_user_data_dir(),"actual_app":true,"synthetic_only":true,"graphics_qualified":false,"native_owner_face_qualified":false}));await shutdown()
