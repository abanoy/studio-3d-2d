extends "res://tests/posed_bounds_app_headless.gd"
const Parts=preload("res://src/character_parts.gd")

func find_character() -> Dictionary:
	for row in app.current_world().objects:
		if row.kind=="group":return Parts.describe(app.current_world(),row.id,int(app.video.duration_frames))
	return {"error":"No character root"}

func render() -> Image:
	return await app.renderer.capture(app.keys,app.layers,0,true)

func run() -> void:
	var args:=OS.get_cmdline_user_args()
	if args.size()<2 or DisplayServer.get_name()=="headless":push_error("Private graphical job needs native snapshot and output folder");quit(2);return
	var snapshot: String=args[0];var folder: String=args[1];var reading: bool="--read" in args
	await setup_app(folder);app.has_project.cache_root=folder.path_join("reader-cache" if reading else "writer-cache")
	var packed: String=folder.path_join("Junko character.has")
	if reading:app.has_project.open_file(packed);await wait_project()
	else:check(app.open_project(snapshot),"ordinary Open installs the prepared native snapshot");await settle()
	var character: Dictionary=find_character()
	check(not character.has("error") and character.parts.size()==6,"ordinary runtime restores all six native character members")
	if character.has("error"):await shutdown();return
	var root_id: String=character.root_id;var runtime: RefCounted=app.renderer.world_runtime
	var inventory:={};var ids:={};var managed:=true
	for part in character.parts:
		inventory[part.role]=runtime.instance(part.row.id).bones.size();ids[part.role]=part.row.id
		if reading:managed=managed and part.row.source.simplify_path().begins_with(app.has_project.cache_root.simplify_path()+"/")
	check(inventory=={"body":145,"dress":112,"hair":69,"skirt":136,"miniskirt":136,"mask":19},"native parts retain complete separate bone inventories")
	check(runtime.instance(root_id).data.scale==1. and runtime.instance(root_id).bones.is_empty(),"character root remains Scale 1 without merging child rigs")
	if reading:
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("native-expected.json")))
		check(managed,"fresh reader restores every native member into its own packed cache")
		var visibility:=true
		for role in ids:visibility=visibility and runtime.instance(ids[role]).root.visible==(role in ["body","hair","skirt"])
		check(visibility,"cold project retains the chosen outfit switches")
		var image: Image=await render();image.save_png(folder.path_join("native-cold.png"))
		check(app.Storage.image_hash(image)==expected.outfit and app.renderer.native_readbacks==0,"cold native character matches writer pixels with balanced readback")
		if checks!=6:push_error("Expected6 native reader checks");quit(2);return
		print("CHARACTER_PARTS_NATIVE_GUI_READ "+JSON.stringify({"checks":checks,"failures":failures,"parts":6}));await shutdown();return
	app.mode.select(1);app.change_mode(1);app.frame_3d_scene()
	var camera: Camera3D=app.renderer.camera
	var shot: Dictionary=app.Timeline.key(0,camera.position,camera.quaternion,camera.fov);shot.near=camera.near;shot.far=camera.far
	app.keys=[shot];app.set_frame(0);app.renderer.evaluate(app.keys,0);await settle()
	var all_parts: Image=await render();all_parts.save_png(folder.path_join("native-all-parts.png"))
	var editor: Node=app.character_parts_editor;editor.open(root_id);await settle()
	for role in ids:editor.switches[ids[role]].button_pressed=role in ["body","hair","skirt"]
	editor.apply_visibility();editor.dialog.hide();await settle()
	var outfit: Image=await render();outfit.save_png(folder.path_join("native-outfit.png"))
	check(app.Storage.image_hash(all_parts)!=app.Storage.image_hash(outfit),"native outfit switches visibly remove alternative parts")
	editor.open(root_id);await settle();editor.switches[ids.hair].button_pressed=false;editor.apply_visibility();editor.dialog.hide();await settle()
	var hair_hidden: Image=await render();hair_hidden.save_png(folder.path_join("native-hair-hidden.png"))
	check(not runtime.instance(ids.hair).root.visible and app.Storage.image_hash(hair_hidden)!=app.Storage.image_hash(outfit),"hiding the independent native hair changes actual rendered geometry")
	app.undo();await settle()
	check(runtime.instance(ids.hair).root.visible and app.Storage.image_hash(await render())==app.Storage.image_hash(outfit),"native visibility Undo restores exact outfit pixels")
	app.has_project.save_file(packed,"packed");await wait_project()
	check(app.has_project.path==packed and FileAccess.file_exists(packed) and app.renderer.native_readbacks==0,"ordinary packed Save includes all six native members and current outfit")
	FileAccess.open(folder.path_join("native-expected.json"),FileAccess.WRITE).store_string(JSON.stringify({"outfit":app.Storage.image_hash(outfit)}))
	# Keep a complete default character available for the owner's later review.
	editor.open(root_id);await settle();editor.set_all_parts(true);editor.apply_visibility();editor.dialog.hide()
	var complete: String=folder.path_join("Junko all parts.has")
	app.has_project.save_file(complete,"packed");await wait_project()
	check(app.has_project.path==complete and FileAccess.file_exists(complete) and app.Storage.image_hash(await render())==app.Storage.image_hash(all_parts),"complete default character is saved separately with all parts visible")
	if checks!=9:push_error("Expected9 native writer checks");quit(2);return
	print("CHARACTER_PARTS_NATIVE_GUI "+JSON.stringify({"checks":checks,"failures":failures,"parts":6}));await shutdown()
