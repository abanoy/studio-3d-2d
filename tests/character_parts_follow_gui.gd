extends "res://tests/posed_bounds_app_headless.gd"
const Parts=preload("res://src/character_parts.gd")

func character() -> Dictionary:
	for row in app.current_world().objects:
		if row.kind=="group":return Parts.describe(app.current_world(),row.id,int(app.video.duration_frames))
	return {"error":"No character"}
func render() -> Image:return await app.renderer.capture(app.keys,app.layers,0,true)
func click(control: Control) -> void:
	var parent: Node=control.get_parent()
	while parent!=null and not parent is ScrollContainer:parent=parent.get_parent()
	if parent is ScrollContainer:parent.ensure_control_visible(control);await settle()
	var window: Window=control.get_window();var point: Vector2=control.get_global_rect().get_center()
	if window.is_embedded():point+=Vector2(window.position)
	var view: Window=root if window.is_embedded() else window
	var motion:=InputEventMouseMotion.new();motion.position=point;view.push_input(motion,true)
	for down in [true,false]:
		var event:=InputEventMouseButton.new();event.position=point;event.button_index=MOUSE_BUTTON_LEFT;event.pressed=down;view.push_input(event,true);await process_frame
	await settle()
func run() -> void:
	var args:=OS.get_cmdline_user_args()
	if args.size()<2 or DisplayServer.get_name()=="headless":push_error("Private native snapshot and data folder required");quit(2);return
	var snapshot: String=args[0];var folder: String=args[1];var reading: bool="--read" in args
	await setup_app(folder);app.has_project.cache_root=folder.path_join("reader-cache" if reading else "writer-cache")
	var packed: String=folder.path_join("Following.has")
	if reading:app.has_project.open_file(packed);await wait_project()
	else:check(app.open_project(snapshot),"ordinary Open loads the six-part native character");await settle()
	var bundle: Dictionary=character()
	if bundle.has("error"):check(false,"character root exists");await shutdown();return
	var ids:={}
	for part in bundle.parts:ids[part.role]=part.row.id
	var runtime: RefCounted=app.renderer.world_runtime;var body: RefCounted=runtime.instance(ids.body);var dress: RefCounted=runtime.instance(ids.dress)
	var report: Dictionary=runtime.follow_report(ids.dress)
	check(not report.has("error") and report.matched==50 and report.ambiguous==0,"actual prepared dress has fifty unambiguous compatible joints")
	check(runtime.instances.size()==7 and body.bones.size()==145 and dress.bones.size()==112,"body and dress remain independent native rigs under their character")
	if report.has("error"):await shutdown();return
	var editor: Node=app.character_parts_editor
	if reading:
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected-follow.json")))
		check(app.has_project.path==packed and dress.data.metadata.character_part.follow_body==true,"fresh reader restores opted-in following from the packed project")
		var followed: Image=await render()
		check(app.Storage.image_hash(followed)==expected.followed and app.renderer.native_readbacks==0,"cold derived dress pose reproduces exact writer pixels")
		check(dress.data.pose==expected.dress_pose and dress.data.pose_keys==expected.dress_keys,"cold following does not bake copied body poses into the dress")
		editor.open(bundle.root_id);await settle()
		check(editor.follow_switches[ids.dress].button_pressed and not editor.follow_switches[ids.dress].disabled,"cold Parts dialog exposes the saved active following choice")
		await click(editor.follow_switches[ids.dress]);editor.apply_visibility();editor.dialog.hide();await settle()
		check(app.Storage.image_hash(await render())==expected.independent,"cold Off restores the independent dress while retaining the body edit")
		if checks!=7:push_error("Expected7 following reader checks");quit(2);return
		print("CHARACTER_PARTS_FOLLOW_GUI_READ "+JSON.stringify({"checks":checks,"failures":failures}));await shutdown();return
	var pins: Dictionary={body.data.source:FileAccess.get_sha256(body.data.source),dress.data.source:FileAccess.get_sha256(dress.data.source)}
	editor.open(bundle.root_id);await settle()
	for role in ids:editor.switches[ids[role]].button_pressed=role=="dress"
	editor.apply_visibility();editor.dialog.hide();await settle()
	app.mode.select(1);app.change_mode(1);app.frame_3d_scene()
	var camera: Camera3D=app.renderer.camera;var key: Dictionary=app.Timeline.key(0,camera.position,camera.quaternion,camera.fov);key.near=camera.near;key.far=camera.far
	app.keys=[key];app.set_frame(0);app.renderer.evaluate(app.keys,0);await settle()
	var independent: Image=await render();independent.save_png(folder.path_join("dress-independent.png"))
	editor.open(bundle.root_id);await settle();var history: int=app.history.size()
	await click(editor.follow_switches[ids.dress])
	check(editor.follow_switches[ids.dress].button_pressed and not editor.follow_switches[ids.dress].disabled,"routed Parts checkbox enables body following")
	editor.apply_visibility();editor.dialog.hide();await settle()
	check(dress.data.metadata.character_part.follow_body==true and app.history.size()==history+1,"following applies through one ordinary settings Undo command")
	if failures>0:await shutdown();return
	var plan: Dictionary=runtime.part_follow.plans[report.plan_key];var source_id:=""
	for token in ["upperarm","spine"]:
		for index in plan.links:
			var source_index: int=plan.links[index]
			if str(plan.master.names[source_index]).to_lower().replace("_","").contains(token):source_id=plan.master.ids[source_index];break
		if not source_id.is_empty():break
	if source_id.is_empty():check(false,"a demonstrated matched arm or spine joint exists");await shutdown();return
	var dress_authored: Dictionary=dress.data.duplicate(true)
	app.world_selection.select_entity(ids.body,false);app.mode.select(2);app.change_mode(2);app.pose_editor.selected=source_id
	var before: Dictionary=body.data.duplicate(true)
	app.pose_editor.set_delta(Vector3.ZERO,Quaternion(Vector3.FORWARD,.55));app.pose_editor.commit(before,true);await settle()
	check(body.data!=before and dress.data==dress_authored,"ordinary body pose edit leaves dress authored poses and expressions unchanged")
	var followed: Image=await render();followed.save_png(folder.path_join("dress-followed.png"))
	check(app.Storage.image_hash(followed)!=app.Storage.image_hash(independent) and not runtime.part_follow.reports[ids.dress].has("error"),"body edit visibly deforms the independently rendered dress")
	if failures>0:await shutdown();return
	editor.open(bundle.root_id);await settle();await click(editor.follow_switches[ids.dress]);editor.apply_visibility();editor.dialog.hide();await settle()
	check(app.Storage.image_hash(await render())==app.Storage.image_hash(independent),"Off restores independent dress pixels without undoing the body pose")
	app.undo();await settle()
	check(dress.data.metadata.character_part.follow_body and app.Storage.image_hash(await render())==app.Storage.image_hash(followed),"Undo restores following and exact derived pixels")
	app.redo();await settle()
	check(not dress.data.metadata.character_part.follow_body and app.Storage.image_hash(await render())==app.Storage.image_hash(independent),"Redo restores independent dress pixels")
	app.undo();await settle()
	check(dress.data.metadata.character_part.follow_body and dress.data.pose==dress_authored.pose and dress.data.pose_keys==dress_authored.pose_keys,"following is ready to save without copying body animation into the dress")
	app.has_project.save_file(packed,"packed");await wait_project()
	check(app.has_project.path==packed and FileAccess.file_exists(packed),"ordinary packed Save retains following and the edited body")
	check(FileAccess.get_sha256(body.data.source)==pins[body.data.source] and FileAccess.get_sha256(dress.data.source)==pins[dress.data.source],"original prepared body and dress GLBs remain unchanged")
	check(app.renderer.native_readbacks==0 and runtime.instances.size()==7,"all native readbacks balance with six separate model parts")
	FileAccess.open(folder.path_join("expected-follow.json"),FileAccess.WRITE).store_string(JSON.stringify({"followed":app.Storage.image_hash(followed),"independent":app.Storage.image_hash(independent),"dress_pose":dress_authored.pose,"dress_keys":dress_authored.pose_keys}))
	if checks!=14:push_error("Expected14 following writer checks");quit(2);return
	print("CHARACTER_PARTS_FOLLOW_GUI "+JSON.stringify({"checks":checks,"failures":failures}));await shutdown()
