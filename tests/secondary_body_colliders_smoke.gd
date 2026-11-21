extends SceneTree
const Fit=preload("res://src/secondary_body_colliders.gd")
const Spring=preload("res://src/secondary_spring.gd")
const IK=preload("res://src/limb_ik.gd")
const PROJECT_SHA:="036eb37fcb17d71e6292751bb1af4b73350512c69a0c31a59efb4fa6a4341101"
const MODEL_SHA:="cc040e35f47280599ea083ac78d36855c99861791b0e66a28e091c12655c5aaf"
var app
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func _initialize() -> void:
	create_timer(150).timeout.connect(func():push_error("Arm fit watchdog");quit(2));call_deferred("run")
func settle() -> void:
	for i in range(4):await process_frame
func run() -> void:
	var args:=OS.get_cmdline_user_args()
	if args.size()!=2 or DisplayServer.get_name()!="headless" or FileAccess.get_sha256(args[1])!=PROJECT_SHA:push_error("Use owned headless output and protected saved case");quit(2);return
	var folder: String=args[0];var archive: String=args[1]
	root.size=Vector2i(1600,1000);root.gui_embed_subwindows=true
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recent.json");root.add_child(app);await settle()
	app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache");app.has_project.open_file(archive)
	while app.has_project.pid>0:await process_frame
	await settle();check(app.has_project.path==archive,"ordinary Open loads protected saved hair case")
	var actor: RefCounted
	for value in app.renderer.world_runtime.instances.values():
		if value.data.sha256==MODEL_SHA:actor=value
	check(actor!=null,"exact Miku asset is installed")
	if actor==null:await app.quit_studio();quit(1);return
	app.world_selection.select_entity(actor.data.id,false);actor.apply(0,true)
	var definition: Dictionary=actor.root.get_meta("has_secondary_rig");var before: PackedByteArray=var_to_bytes(definition);var authored: PackedByteArray=var_to_bytes(actor.data)
	check(definition.source_family=="HAS" and definition.chains.size()==1 and definition.colliders.is_empty(),"saved generated helper has no original collision geometry")
	var fit: Dictionary=Fit.build(actor);var right_ids: Array=[]
	for id in actor.order:
		var limb: Dictionary=IK.chain(actor,id)
		if limb.get("role")=="rightHand":right_ids=limb.ids.slice(0,2)
	var found: Array=[]
	for c in fit.colliders:found.append(c.binding.id)
	check(right_ids.size()==2 and found.has(right_ids[0]) and found.has(right_ids[1]),"actual weighted geometry fits both right upper and lower arm envelopes")
	check(var_to_bytes(definition)==before and var_to_bytes(actor.data)==authored,"fitting preserves source rig joint settings and saved authored data")
	var made: Dictionary=Spring.construct(actor)
	check(not made.has("error") and made.runner.chains[0].colliders.size()==fit.colliders.size(),"ordinary spring construction automatically includes runtime arm collisions")
	if made.has("error"):await app.quit_studio();quit(1);return
	var runner: RefCounted=made.runner;var bindings_ok:=true
	for chain in runner.chains:
		for collider in chain.colliders:
			var c: Dictionary=collider.definition;var t: Transform3D=actor.bone_transform(c.binding.id);var finish: Vector3=actor.bone_transform(c.tail_binding.id).origin
			bindings_ok=bindings_ok and collider.node.global_position.is_equal_approx((t.origin+finish)*.5)
	check(bindings_ok,"runtime capsules follow actual arm endpoints")
	runner.dispose();await settle()
	check(var_to_bytes(definition)==before and var_to_bytes(actor.data)==authored and FileAccess.get_sha256(archive)==PROJECT_SHA,"runner disposal leaves rig settings poses and original project unchanged")
	print("SECONDARY_BODY_COLLIDERS "+JSON.stringify({"checks":checks,"failures":failures,"user_profile":OS.get_user_data_dir(),"fitted_colliders":fit.colliders.size(),"inspected_vertices":fit.get("inspected_vertices",0),"matched_vertices":fit.get("matched_vertices",0),"source_arrays_published":false,"graphics_or_contact_response_qualified":false}));await app.quit_studio();quit(0 if failures==0 else 1)
