extends SceneTree
const Drawing=preload("res://src/drawing.gd")
const World=preload("res://src/world_document.gd")
const Storage=preload("res://src/storage.gd")
const Limb=preload("res://tests/limb_fixture.gd")
const T=preload("res://src/timeline.gd")
var app
var checks:=0
var failures:=0
var id: String
var simulation
var generation: int
func _initialize() -> void:
	create_timer(150).timeout.connect(func():push_error("Drawing history watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settle() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func alive(label: String) -> void:
	check(app.physics_editor.is_running() and is_same(app.physics_editor.simulations.get(id),simulation) and app.physics_editor.generation==generation,"live simulation identity/generation preserved: "+label)
func equal(a,b) -> bool:return JSON.parse_string(JSON.stringify(a,"",true,true))==JSON.parse_string(JSON.stringify(b,"",true,true))
func mouse(point: Vector2,pressed: bool) -> void:
	var e:=InputEventMouseButton.new();e.button_index=MOUSE_BUTTON_LEFT;e.pressed=pressed;var rect: Rect2=app.canvas.image_rect();e.position=rect.position+point/Vector2(1920,1080)*rect.size;app.canvas._gui_input(e)
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0];var baseline: bool="--baseline" in args;var reader: bool="--read" in args
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery-cold" if reader else "recovery");app.recent_path=folder.path_join("recents-cold.json" if reader else "recents.json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache-cold" if reader else "cache")
	var packed:=folder.path_join("Drawing Undo.has")
	if reader:
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")));app.has_project.open_file(packed)
		while app.has_project.pid>0:await process_frame
		await settle();check(Storage.image_hash(Drawing.composite(app.layers,12,1920,1080))==expected.overlay,"cold Open preserves exact post-Undo drawings")
		check(equal(app.keys,expected.keys) and equal(World.portable(app.current_world()),expected.world),"cold Open preserves authored world and camera keys")
		var rendered: Image=await app.renderer.capture(app.keys,app.layers,12,true);check(Storage.image_hash(rendered)==expected.render and FileAccess.get_sha256(packed)==expected.project_hash,"cold preview matches movie input and leaves manual save untouched")
		print("DRAWING_HISTORY_READ ",JSON.stringify({"checks":checks,"failures":failures}));app.free();quit(0 if failures==0 else 1);return
	check(app.restore_world(app.current_world()).is_empty(),"standard environment is installed")
	var asset:=folder.path_join("limb.glb");check(Limb.create(asset)==OK,"validated original ragdoll fixture is created")
	var doc: Dictionary=app.current_world().duplicate(true);var row:=World.object(asset,"model","Practice limb");doc.objects.append(row);check(app.restore_world(doc).is_empty(),"standard poseable model is installed")
	app.keys=[T.key(0,Vector3(-1.5,2,5),Quaternion.IDENTITY,60),T.key(48,Vector3(1.5,1.5,3),Quaternion.IDENTITY,52)];app.set_frame(12)
	var ink: Dictionary=app.layers[1];var image:=Drawing.blank(1920,1080);Drawing.insert(ink,0,48,image);app.history.clear();app.redo_history.clear();app.history_bytes=0
	id=row.id;app.world_selection.select_entity(id);app.physics_editor.enable_body(app.renderer.active_model());app.mode.select(0);app.change_mode(0);await settle()
	simulation=app.physics_editor.simulations.get(id);generation=app.physics_editor.generation;check(simulation!=null and app.physics_editor.is_running(),"real ragdoll runs while Draw is active")
	var world: Dictionary=World.portable(app.current_world());var keys: Array=app.keys.duplicate(true);var view: Dictionary=app.renderer.view_state();var original:=image.get_data();app.color.color=Color.CYAN
	mouse(Vector2(350,400),true);var motion:=InputEventMouseMotion.new();var rect: Rect2=app.canvas.image_rect();motion.position=rect.position+Vector2(700,400)/Vector2(1920,1080)*rect.size;app.canvas._gui_input(motion);mouse(Vector2(700,400),false);var painted:=image.get_data()
	check(painted!=original and app.history[-1].type=="pixels","routed brush creates an actual pixel history command")
	var before: Dictionary={}
	for bone in simulation.bodies:before[bone]=simulation.bodies[bone].global_transform
	app.undo()
	if baseline:
		var result:={"before_running":true,"after_running":app.physics_editor.is_running(),"before_generation":generation,"after_generation":app.physics_editor.generation,"pixels_restored":image.get_data()==original}
		FileAccess.open(folder.path_join("baseline.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("DRAWING_HISTORY_BASELINE ",JSON.stringify(result));app.free();quit(0 if not result.after_running and result.pixels_restored else 1);return
	alive("brush Undo");check(image.get_data()==original,"pixel Undo restores exact source bytes")
	var positions:=true
	for bone in before:positions=positions and before[bone]==simulation.bodies[bone].global_transform
	check(positions,"drawing Undo does not teleport any physics body within the input event")
	app.redo();alive("brush Redo");check(image.get_data()==painted,"pixel Redo restores exact painted bytes")
	app.create_cel(true);var copy:=Drawing.cel_at(ink,12);check(copy.start==12 and Drawing.image(copy).get_data()==painted,"copy exposure creates an independent held drawing")
	app.undo();alive("cel Undo");check(ink.cels.size()==1 and Drawing.cel_at(ink,12).start==0,"cel Undo restores the original exposure")
	app.redo();alive("cel Redo");app.exposure.value=5;app.set_exposure();app.undo();alive("exposure Undo");check(app.exposure.value==36 and Drawing.cel_at(ink,12).duration==36,"exposure control refreshes correctly without reevaluating3D")
	app.redo();alive("exposure Redo");app.undo();app.delete_cel();app.undo();alive("delete-cel Undo");check(Drawing.cel_at(ink,12).start==12,"deleted cel is restored at the correct frame")
	app.layer_editor.set_opacity(45);app.undo();alive("opacity Undo");check(not ink.has("opacity"),"opacity Undo restores the default field")
	app.layer_editor.set_visible(false);app.undo();alive("visibility Undo");check(ink.visible and app.layer_visibility.button_pressed,"visibility and its checkbox restore")
	app.layer_editor.rename_layer("Color ink");app.undo();alive("name Undo");check(ink.name=="Ink","layer name restores")
	app.layer_editor.add_layer("Effects");app.undo();alive("new-layer Undo");check(app.layers.size()==2 and app.layers[app.active_layer].id==ink.id,"layer Undo restores order and active selection")
	app.redo();alive("new-layer Redo");app.layer_editor.move_layer(-1);app.undo();alive("stack-order Undo");app.layer_editor.request_remove();app.undo();alive("remove-layer Undo");app.redo();alive("remove-layer Redo")
	check(app.layers.size()==2 and equal(world,World.portable(app.current_world())) and equal(keys,app.keys) and equal(view,app.renderer.view_state()) and app.frame==12,"drawing history preserves authored world, shot, view and playhead")
	await settle();alive("continued physics frames");check(app.canvas.overlay.get_image().get_data()==Drawing.composite(app.layers,12,1920,1080).get_data(),"visible drawing overlay refreshes through its ordinary render path")
	if "--patch" in args:
		var held: Dictionary=Drawing.cel_at(app.cel_timing.layer_by_id(ink.id),12)
		app.cel_clipboard.open_menu(ink.id,held.id,12,Vector2i(300,200));app.cel_clipboard.menu.id_pressed.emit(1);await settle();alive("patch Cut")
		app.undo();alive("patch Cut Undo");app.redo();alive("patch Cut Redo")
		app.cel_clipboard.open_menu(ink.id,"",12,Vector2i(300,200));app.cel_clipboard.menu.id_pressed.emit(2);await settle();alive("patch Paste")
		app.undo();alive("patch Paste Undo");app.undo();alive("patch Cut restoration")
		check(Drawing.cel_at(app.cel_timing.layer_by_id(ink.id),12).id==held.id and equal(world,World.portable(app.current_world())) and equal(keys,app.keys),"patch Undo restores original cel and preserves authored world/camera")
	app.physics_editor.clear();check(app.restore_world(doc).is_empty(),"deterministic authored world is restored after the live-physics test")
	var overlay:=Storage.image_hash(Drawing.composite(app.layers,12,1920,1080));world=World.portable(app.current_world());var rendered: Image=await app.renderer.capture(app.keys,app.layers,12,true);app.has_project.save_file(packed,"packed")
	while app.has_project.pid>0:await process_frame
	await settle();var manual:=FileAccess.get_sha256(packed);var error: String=await app.export_movie(folder);check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000013.png")).get_data()==rendered.get_data(),"post-history drawing and camera produce an exact normal movie PNG")
	var expected:={"overlay":overlay,"world":world,"keys":keys,"render":Storage.image_hash(rendered),"project_hash":manual};FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify(expected))
	var result:={"checks":checks,"failures":failures,"project":packed,"movie":app.last_export_folder.path_join("movie.mp4")};FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("DRAWING_HISTORY_SMOKE ",JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
