extends SceneTree
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
const World=preload("res://src/world_document.gd")
const Model=preload("res://src/model.gd")
const Recovery=preload("res://src/recovery.gd")
var app
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(160).timeout.connect(func():push_error("Stroke smoothing watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settle() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func job() -> void:
	while app.has_project.pid>0:await process_frame
	await settle()
func equal(a,b) -> bool:return JSON.parse_string(JSON.stringify(a,"",true,true))==JSON.parse_string(JSON.stringify(b,"",true,true))
func point(event: InputEventMouse,p: Vector2) -> Vector2:
	var rect: Rect2=app.canvas.image_rect();event.position=rect.position+p/Vector2(1920,1080)*rect.size
	var mapped: Vector2=(event.position-rect.position)/rect.size*Vector2(1920,1080);app.canvas._gui_input(event);return mapped.clamp(Vector2.ZERO,Vector2(1919,1079))
func button(p: Vector2,pressed: bool) -> Vector2:
	var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.pressed=pressed;return point(event,p)
func motion(p: Vector2,value: float=1) -> Vector2:
	var event:=InputEventMouseMotion.new();event.button_mask=MOUSE_BUTTON_MASK_LEFT;event.pressure=value;return point(event,p)
func box_asset(path: String) -> Error:
	var node:=Node3D.new();var mesh:=MeshInstance3D.new();var shape:=BoxMesh.new();shape.size=Vector3.ONE*.5;mesh.mesh=shape;node.add_child(mesh);mesh.owner=node
	var doc:=GLTFDocument.new();var state:=GLTFState.new();var error:=doc.append_from_scene(node,state)
	if error==OK:error=doc.write_to_filesystem(state,path)
	node.free();return error
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0]
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	var project:=folder.path_join("Smoothed.has")
	if "--read" in args:
		var expected:=Recovery.read_json(folder.path_join("expected.json"));app.has_project.open_file(project);await job()
		check(app.brush_smoothing.value==0 and Storage.image_hash(Drawing.cel_at(app.layers[1],0).image)==expected.pixels,"cold HAS keeps exact smoothed pixels while session smoothing defaults off")
		FileAccess.open(folder.path_join("cold-state.json"),FileAccess.WRITE).store_string(JSON.stringify({"world":World.portable(app.current_world()),"keys":app.keys},"",true,true))
		check(equal(World.portable(app.current_world()),expected.world) and equal(app.keys,expected.keys),"cold project retains editable world and original camera independently")
		var image: Image=await app.renderer.capture(app.keys,app.layers,0,true)
		check(Storage.image_hash(image)==expected.render and FileAccess.get_sha256(project)==expected.project_hash,"cold rendered output matches writer exactly without changing manual HAS")
		check(app.restore_checkpoint({"folder":folder.path_join("smooth-recovery/test"),"manifest":"project.json","recovery":true}) and Storage.image_hash(Drawing.cel_at(app.layers[1],0).image)==expected.pixels,"ordinary recovery restores smoothed ink without transient filter metadata")
		print("STROKE_STABILIZER_READ ",JSON.stringify({"checks":checks,"failures":failures}));app.free();quit(0 if failures==0 else 1);return
	check(app.load_demo_room(),"original parent environment loads for independent drawing")
	app.mode.select(0);app.change_mode(0);app.layers[1].cels.clear();var image:=Drawing.blank(1920,1080);Drawing.insert(app.layers[1],0,48,image);app.set_frame(0);app.history.clear();app.redo_history.clear();app.history_bytes=0
	var world: Dictionary=World.portable(app.current_world());var shots: Array=app.keys.duplicate(true);var view: Dictionary=app.renderer.view_state()
	check(app.brush_smoothing.value==0 and not app.brush_smoothing.is_visible_in_tree(),"smoothing starts disabled and its precision control stays under Advanced")
	app.set_advanced(true);check(app.brush_smoothing.is_visible_in_tree(),"Advanced exposes optional smoothing without altering document")
	app.radius.value=4;app.color.color=Color.CYAN
	var path: Array[Vector2]=[Vector2(200,300),Vector2(240,308),Vector2(280,292),Vector2(320,308),Vector2(360,292),Vector2(400,300)]
	var mapped: Array=[button(path[0],true)]
	for i in range(1,path.size()):mapped.append(motion(path[i]))
	button(path[-1],false);var raw:=image.get_data();var reference:=Drawing.blank(1920,1080)
	for i in range(mapped.size()):Drawing.stroke(reference,mapped[maxi(0,i-1)],mapped[i],4,Color.CYAN,false)
	check(raw==reference.get_data(),"default-zero routed brush remains byte-identical to original direct raster brush")
	app.undo();check(image.get_used_rect().get_area()==0,"default stroke retains one complete Undo")
	app.brush_smoothing.value=24;button(path[0],true)
	for i in range(1,path.size()):motion(path[i])
	check(app.drawing and app.stroke_stabilizer.distance==24 and image.get_pixel(395,300).a==0,"enabled smoothing trails the actual pointer before release")
	app.brush_smoothing.value=0;check(app.stroke_stabilizer.distance==24,"changing smoothing setting mid-stroke does not change captured gesture settings")
	var release:=InputEventMouseButton.new();release.button_index=MOUSE_BUTTON_LEFT;release.pressed=false;release.position=Vector2(-40,-40);app._input(release)
	var smooth:=image.get_data()
	check(not app.drawing and app.stroke_stabilizer==null and app.active_brush==null and image.get_pixel(399,300).a>.99,"release outside the view finishes tail at final input point and clears transient state")
	check(smooth!=raw and app.history.size()==1,"smoothing changes jagged path as one ordinary pixel command")
	app.undo();check(image.get_used_rect().get_area()==0,"smoothed stroke Undo restores exact empty cel");app.redo();check(image.get_data()==smooth,"smoothed stroke Redo restores exact anti-aliased pixels")
	app.brush_smoothing.value=24;app.brush_pressure.button_pressed=true;app.brush_opacity.value=50;app.radius.value=10
	button(Vector2(300,550),true);motion(Vector2(300,550),.5);motion(Vector2(350,550),.5);motion(Vector2(600,550),0)
	check(image.get_pixel(347,550).a>.49 and image.get_pixel(450,550).a==0,"zero pressure finishes preceding tail without painting toward the hover position")
	motion(Vector2(650,550),.5);motion(Vector2(750,550),.5);button(Vector2(750,550),false)
	check(image.get_pixel(500,550).a==0 and image.get_pixel(650,550).a>.49 and image.get_pixel(747,550).a>.49,"new contact resets stabilizer and keeps hover gap empty through release")
	check(absf(image.get_pixel(700,550).a-.5)<.005,"stabilizer tail retains captured pressure size and even stroke opacity")
	var before_erase:=image.get_data();app.tool.select(1);app.brush_pressure.button_pressed=false;app.brush_opacity.value=50;app.radius.value=5
	button(Vector2(650,550),true);motion(Vector2(750,550));button(Vector2(750,550),false)
	check(absf(image.get_pixel(747,550).a-.25)<.01,"eraser smoothing also flushes endpoint with captured strength")
	app.undo();check(image.get_data()==before_erase,"eraser Undo restores exact prior pressure pixels")
	app.tool.select(0);app.brush_opacity.value=100;app.radius.value=4;button(Vector2(300,650),true);motion(Vector2(400,650));app._notification(Window.NOTIFICATION_WM_WINDOW_FOCUS_OUT)
	check(not app.drawing and app.stroke_stabilizer==null and image.get_pixel(399,650).a>.99,"focus loss completes current tail without keeping filter state alive")
	check(equal(world,World.portable(app.current_world())) and equal(shots,app.keys) and equal(view,app.renderer.view_state()),"all smoothed pen/eraser edits preserve independent world, camera and view")
	app.layers[1].cels[0].duration=24;app.set_frame(24);app.brush_pressure.button_pressed=true
	var pending_history: int=app.history.size();var pending_revision: int=app.recovery_revision
	button(Vector2(1000,700),true);motion(Vector2(1100,700),0);button(Vector2(1100,700),false)
	check(Drawing.cel_at(app.layers[1],24).is_empty() and app.history.size()==pending_history and app.recovery_revision==pending_revision and app.stroke_stabilizer==null,"smoothing with no positive pressure creates no cel, pixels, history or lingering filter")
	app.brush_pressure.button_pressed=false;app.layers[1].cels[0].duration=48;app.set_frame(0);app.changed()
	var source:=folder.path_join("original-box.glb");check(box_asset(source)==OK,"original physics prop fixture writes without external assets")
	var data:=Model.definition(source);data.position=[0,2,0];check(app.append_object(data,"model").is_empty(),"actual solid prop imports into same world")
	var id: String=app.last_import_id;app.world_selection.select_entity(id);app.mode.select(0);app.change_mode(0);app.physics_editor.change(true);await settle()
	var simulation=app.physics_editor.simulations.get(id);var history: int=app.history.size();var source_hash:=FileAccess.get_sha256(source)
	button(Vector2(800,650),true);motion(Vector2(900,650));button(Vector2(900,650),false)
	check(simulation!=null and app.physics_editor.simulations.get(id)==simulation and app.physics_editor.body_active(id) and app.history.size()==history+1,"smoothing creates one ink command without replacing a running physics simulation")
	app.undo();app.redo();check(app.physics_editor.simulations.get(id)==simulation and app.physics_editor.body_active(id) and FileAccess.get_sha256(source)==source_hash,"drawing Undo/Redo preserves live physics identity and original model file")
	app.physics_editor.freeze_all();app.physics_editor.clear_previews();app.set_frame(0)
	app.has_project.save_file(project,"packed");await job();check(FileAccess.file_exists(project),"normal packed HAS saves only resulting raster and ordinary editable world")
	var snapshot: Dictionary=app.project_snapshot();var error:=Recovery.checkpoint(folder.path_join("smooth-recovery"),"test",snapshot.video,snapshot.camera_keys,snapshot.layers,"",0,snapshot.audio,"",app.recovery_revision,{},snapshot.world,snapshot.palette)
	check(error.is_empty(),"normal recovery checkpoint saves smoothed artwork without session filter")
	var preview: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	var exported: String=await app.export_movie(folder);var movie: String=app.last_export_folder.path_join("movie.mp4")
	check(exported.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000001.png")).get_data()==preview.get_data(),"actual movie receives exact independent world plus smoothed drawing pixels")
	var expected:={"pixels":Storage.image_hash(image),"render":Storage.image_hash(preview),"world":World.portable(app.current_world()),"keys":app.keys,"project_hash":FileAccess.get_sha256(project)}
	FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify(expected,"",true,true))
	print("STROKE_STABILIZER_SMOKE ",JSON.stringify({"checks":checks,"failures":failures,"movie":movie}));app.free();quit(0 if failures==0 else 1)
