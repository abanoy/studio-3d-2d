extends "res://tests/posed_bounds_app_headless.gd"
const Parts=preload("res://src/character_parts.gd")

func write_part(path: String, offset: Vector3, color: Color) -> Error:
	var scene: Node3D=Fixture.scene()
	var mesh: MeshInstance3D=scene.get_node("Panel")
	# Sibling parts share a source origin; their weighted vertices carry offsets.
	var arrays: Array=mesh.mesh.surface_get_arrays(0)
	var vertices: PackedVector3Array=arrays[Mesh.ARRAY_VERTEX]
	for i in range(vertices.size()):vertices[i]+=offset
	arrays[Mesh.ARRAY_VERTEX]=vertices
	var resource:=ArrayMesh.new();resource.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)
	mesh.mesh=resource;mesh.material_override.albedo_color=color
	var document:=GLTFDocument.new();var state:=GLTFState.new()
	var why: Error=document.append_from_scene(scene,state)
	if why==OK:why=document.write_to_filesystem(state,path)
	scene.free();return why

func bundle() -> Dictionary:
	for row in app.current_world().objects:
		if row.kind=="group":return Parts.describe(app.current_world(),row.id,int(app.video.duration_frames))
	return {"error":"No character root"}

func focus_character() -> void:
	app.mode.select(1);app.change_mode(1);app.frame_3d_scene()
	var camera: Camera3D=app.renderer.camera
	var key: Dictionary=app.Timeline.key(0,camera.position,camera.quaternion,camera.fov)
	key.near=camera.near;key.far=camera.far
	app.keys=[key];app.set_frame(0);app.renderer.evaluate(app.keys,0)
	await settle()

func press_control(control: Control) -> void:
	var window: Window=control.get_window();var position: Vector2=control.get_global_rect().get_center()
	if window.is_embedded():position+=Vector2(window.position)
	var view: Window=root if window.is_embedded() else window
	var motion:=InputEventMouseMotion.new();motion.position=position;view.push_input(motion,true)
	for down in [true,false]:
		var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.pressed=down;event.position=position
		view.push_input(event,true);await process_frame
	await settle()

func run() -> void:
	var args:=OS.get_cmdline_user_args()
	if args.is_empty() or DisplayServer.get_name()=="headless":push_error("Private graphical folder required");quit(2);return
	var folder: String=args[0];await setup_app(folder);var reading: bool="--read" in args
	var packed: String=folder.path_join("Character.has")
	if reading:
		app.has_project.cache_root=folder.path_join("reader-cache")
		app.has_project.open_file(packed);await wait_project()
		var loaded: Dictionary=bundle()
		check(app.has_project.path==packed and not loaded.has("error") and loaded.parts.size()==2,"fresh Open restores one character and both independent parts")
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected-parts.json")))
		var runtime: RefCounted=app.renderer.world_runtime;var root_id: String=loaded.root_id
		var factor_bits: String=PackedFloat64Array([runtime.instance(root_id).base_root.basis.get_scale().y]).to_byte_array().hex_encode()
		check(runtime.instance(root_id).data.scale==1. and factor_bits==expected.factor_bits,"cold root keeps Scale 1 and its exact shared intrinsic height")
		var managed:=true;var independent:=true
		for part in loaded.parts:
			var actor: RefCounted=runtime.instance(part.row.id)
			managed=managed and actor.data.source.simplify_path().begins_with(app.has_project.cache_root.simplify_path()+"/")
			independent=independent and actor.bones.size()==1 and actor.root.get_parent()==runtime.instance(root_id).root
		check(managed and independent,"cold assets belong to reader cache with separate child rigs")
		check(not runtime.instance(expected.hidden_id).root.visible,"cold replay retains per-part visibility")
		app.character_parts_editor.open(root_id);await settle()
		check(app.character_parts_editor.switches.size()==2 and not app.character_parts_editor.switches[expected.hidden_id].button_pressed,"cold Manage parts reflects the saved switches")
		app.character_parts_editor.dialog.hide()
		var image: Image=await app.renderer.capture(app.keys,app.layers,0,true)
		check(image!=null and app.Storage.image_hash(image)==expected.hidden_hash and app.renderer.native_readbacks==0,"cold render matches saved visible parts exactly")
		if checks!=6:push_error("Expected6 reader checks");quit(2);return
		print("CHARACTER_PARTS_GUI_READ "+JSON.stringify({"checks":checks,"failures":failures}));await shutdown();return
	var body: String=folder.path_join("body.glb");var hair: String=folder.path_join("hair.glb")
	check(write_part(body,Vector3.ZERO,Color.BLUE)==OK and write_part(hair,Vector3(.8,.4,0),Color.GREEN)==OK,"distinct weighted parts export from generated source")
	var hashes: Dictionary={body:FileAccess.get_sha256(body),hair:FileAccess.get_sha256(hair)}
	var history: int=app.history.size()
	app.source_import.start_bundle([{"path":body,"role":"body"},{"path":hair,"role":"hair"}],{"name":"Test character","fit_height":true,"reference_index":0})
	while app.source_import.bundle_active:await process_frame
	await settle();var installed: Dictionary=bundle()
	check(not installed.has("error") and installed.parts.size()==2 and app.history.size()==history+1,"ordinary bundle import installs two parts in one history command")
	if installed.has("error"):await shutdown();return
	var root_id: String=installed.root_id;var hidden_id: String=installed.parts[1].row.id
	var runtime: RefCounted=app.renderer.world_runtime
	var factor: float=runtime.instance(root_id).base_root.basis.get_scale().y
	check(runtime.instance(root_id).data.scale==1. and absf(factor*.5-1.8288)<.00001,"body is six feet at Scale 1 through a single shared factor")
	check(runtime.instance(installed.parts[0].row.id).root.global_transform==runtime.instance(hidden_id).root.global_transform,"part roots stay aligned while geometry retains its source offsets")
	await focus_character()
	var visible: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	app.character_parts_editor.open(root_id);await settle()
	var editor: Node=app.character_parts_editor
	check(editor.dialog.visible and editor.switches.size()==2,"resizable Parts dialog exposes the two actual members")
	await press_control(editor.switches[hidden_id])
	check(not editor.switches[hidden_id].button_pressed,"routed checkbox click selects a part to hide")
	if failures>0:await shutdown();return
	editor.apply_visibility();editor.dialog.hide();await settle()
	var hidden: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	visible.save_png(folder.path_join("parts-visible.png"));hidden.save_png(folder.path_join("part-hidden.png"))
	print("PARTS_VISIBILITY_STATE "+JSON.stringify({"visible":runtime.instance(hidden_id).root.visible,"base":runtime.instance(hidden_id).data.visible,"note":editor.info.text,"same_pixels":app.Storage.image_hash(hidden)==app.Storage.image_hash(visible)}))
	check(not runtime.instance(hidden_id).root.visible and app.Storage.image_hash(hidden)!=app.Storage.image_hash(visible),"hiding one part visibly changes rendered geometry")
	if failures>0:await shutdown();return
	app.undo();await settle()
	check(runtime.instance(hidden_id).root.visible and app.Storage.image_hash(await app.renderer.capture(app.keys,app.layers,0,true))==app.Storage.image_hash(visible),"Undo restores both visibility and exact pixels")
	app.redo();await settle()
	check(not runtime.instance(hidden_id).root.visible,"Redo restores the hidden part")
	app.has_project.save_file(packed,"packed")
	check(is_instance_valid(app.has_project.progress) and not app.has_project.progress.find_children("*","ProgressBar",true,false).is_empty(),"project save displays the loading activity bar")
	await wait_project()
	check(app.has_project.path==packed and FileAccess.file_exists(packed),"ordinary packed Save includes the complete character")
	check(FileAccess.get_sha256(body)==hashes[body] and FileAccess.get_sha256(hair)==hashes[hair] and app.renderer.native_readbacks==0,"input parts stay unchanged and rendering waits balance")
	FileAccess.open(folder.path_join("expected-parts.json"),FileAccess.WRITE).store_string(JSON.stringify({"factor_bits":PackedFloat64Array([factor]).to_byte_array().hex_encode(),"hidden_id":hidden_id,"hidden_hash":app.Storage.image_hash(hidden)}))
	visible.save_png(folder.path_join("parts-visible.png"));hidden.save_png(folder.path_join("part-hidden.png"))
	if checks!=12:push_error("Expected12 writer checks");quit(2);return
	print("CHARACTER_PARTS_GUI "+JSON.stringify({"checks":checks,"failures":failures}));await shutdown()
