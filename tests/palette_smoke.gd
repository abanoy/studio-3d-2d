extends SceneTree
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
const World=preload("res://src/world_document.gd")
const SceneIO=preload("res://src/scene3d.gd")
const Limb=preload("res://tests/limb_fixture.gd")
const T=preload("res://src/timeline.gd")
const Lesson=preload("res://src/lesson_store.gd")
var app
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(180).timeout.connect(func():push_error("Palette watchdog");quit(2));call_deferred("run")
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
func button(text: String,node: Node) -> Button:
	for child in node.get_children():
		if child is Button and child.text==text:return child
		var found:=button(text,child)
		if found:return found
	return null
func click_control(control: Control) -> void:
	app.inspector_scroll.ensure_control_visible(control);await settle();var p:=control.get_global_rect().get_center()
	var motion:=InputEventMouseMotion.new();motion.position=p;root.push_input(motion,true)
	for pressed in [true,false]:
		var e:=InputEventMouseButton.new();e.position=p;e.button_index=MOUSE_BUTTON_LEFT;e.pressed=pressed;root.push_input(e,true);await process_frame
	await settle()
func mouse(p: Vector2,pressed: bool) -> void:
	var e:=InputEventMouseButton.new();e.button_index=MOUSE_BUTTON_LEFT;e.pressed=pressed;var rect: Rect2=app.canvas.image_rect();e.position=rect.position+p/Vector2(1920,1080)*rect.size;app.canvas._gui_input(e)
func stroke(from: Vector2,to: Vector2) -> void:
	mouse(from,true);var e:=InputEventMouseMotion.new();var rect: Rect2=app.canvas.image_rect();e.position=rect.position+to/Vector2(1920,1080)*rect.size;app.canvas._gui_input(e);mouse(to,false)
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0];var mode: String=args[1] if args.size()>1 else "writer"
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery-"+mode);app.recent_path=folder.path_join("recents-"+mode+".json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache-"+mode)
	var packed:=folder.path_join("Palette.has");var linked:=folder.path_join("Palette linked.has")
	if mode!="writer":
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")));var ok:=true
		if mode in ["packed","linked"]:app.has_project.open_file(packed if mode=="packed" else linked);await job()
		elif mode=="recovery":ok=app.open_project(expected.recovery)
		elif mode=="folder":ok=app.open_project(folder.path_join("folder-save"))
		else:
			var store:=Lesson.new();store.root=folder.path_join("lessons");ok=store.load_snapshot(app,"basic-pose","123456_1","step_01")
		check(ok and app.palette==expected.palette and app.palette_editor.buttons.size()==expected.palette.size(),mode+" restores ordered named alpha swatches and their controls")
		check(Storage.image_hash(Drawing.cel_at(app.layers[1],0).image)==expected.ink and equal(app.keys,expected.keys) and equal(World.portable(app.current_world()),expected.world),mode+" keeps exact artwork and standard world/shot data")
		var reference: Image=await app.renderer.capture(app.keys,app.layers,0,true)
		check(Storage.image_hash(reference)==expected.render and FileAccess.get_sha256(packed)==expected.project_hash,mode+" preview is exact and manual HAS is untouched")
		print("PALETTE_READ ",JSON.stringify({"checks":checks,"failures":failures,"mode":mode}));app.free();quit(0 if failures==0 else 1);return
	check(app.restore_world(app.current_world()).is_empty(),"standard environment is installed")
	var asset:=folder.path_join("figure.glb");check(Limb.create(asset)==OK,"original validated limb fixture is created")
	var doc: Dictionary=app.current_world().duplicate(true);var actor:=World.object(asset,"model","Practice figure");doc.objects.append(actor);check(app.restore_world(doc).is_empty(),"poseable standard model coexists with project colors")
	app.keys=[T.key(0,Vector3(-1.5,2,5),Quaternion.IDENTITY,60),T.key(48,Vector3(1.5,1.5,3),Quaternion.IDENTITY,52)];app.mode.select(0);app.change_mode(0);app.set_frame(0);app.color.color=Color.CYAN;stroke(Vector2(300,400),Vector2(600,400));var image: Image=Drawing.cel_at(app.layers[1],0).image
	var ink_hash:=Storage.image_hash(image);var world: Dictionary=World.portable(app.current_world());var keys: Array=app.keys.duplicate(true);var view: Dictionary=app.renderer.view_state();var rendered: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	check(app.palette.is_empty() and not app.palette_editor.detail.visible,"Simple starts without invented project swatches or Advanced editing controls")
	app.color.color=Color8(241,210,180);await click_control(button("Keep this color",app.palette_editor.panel));check(app.palette.size()==1 and app.palette[0].rgba=="f1d2b4ff","actual Keep button stores the current RGBA color")
	app.advanced_toggle.button_pressed=true;await settle();app.palette_editor.name_field.text="Skin / 肌";app.palette_editor.name_field.text_submitted.emit("Skin / 肌");app.color.color=Color8(32,48,80,128);app.palette_editor.add_current();app.palette_editor.name_field.text="Hair";app.palette_editor.rename_selected();app.color.color=Color("12345600");app.palette_editor.add_current();app.advanced_toggle.button_pressed=false;await settle()
	check(app.palette.size()==3 and app.palette[0].name=="Skin / 肌" and app.palette[1].rgba=="20305080" and app.palette[2].rgba=="12345600" and not app.palette_editor.detail.visible,"names, half-alpha and transparent swatches remain available in Simple")
	var count: int=app.history.size();var revision: int=app.recovery_revision;await click_control(app.palette_editor.buttons[0]);app.palette_editor.add_current()
	check(app.color.color.to_html()=="f1d2b4ff" and app.palette.size()==3 and app.history.size()==count and app.recovery_revision==revision,"actual swatch click and duplicate Keep only choose color without document edits")
	app.color.color=Color.RED;app.palette_editor.replace_selected();app.undo();check(app.palette[0].rgba=="f1d2b4ff","replace is undoable without changing existing paint");app.redo();app.undo()
	app.palette_editor.select(1);var before: Array=app.palette.duplicate(true);app.palette_editor.remove_selected();app.undo();check(app.palette==before,"remove Undo restores order, names and alpha exactly")
	app.palette_editor.select(0);app.color_sampler.arm();app.color_sampler.start(Vector2(400,400));app.palette_editor.select(1);await settle();check(app.color_sampler.context.is_empty() and app.tool.selected==0 and app.color.color.to_html()=="20305080","choosing a swatch cancels pending sampler capture and returns to Pen")
	app.tool.select(2);app.color.color=Color.GREEN;mouse(Vector2(800,800),true);mouse(Vector2(800,800),false)
	while app.fill_editor.busy():await process_frame
	await settle();check(not app.fill_editor.pending.is_empty(),"edge fill provides an actual pending preview for palette interaction")
	app.palette_editor.select(0);app.fill_editor.apply_pending();check(app.fill_editor.pending.is_empty() and Storage.image_hash(image)==ink_hash,"swatch selection invalidates a differently colored fill preview")
	var after_palette: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	check(Storage.image_hash(image)==ink_hash and after_palette.get_data()==rendered.get_data() and equal(world,World.portable(app.current_world())) and equal(keys,app.keys) and equal(view,app.renderer.view_state()),"palette editing and selection preserve exact art/render/world/shot/view")
	app.world_selection.select_entity(actor.id);app.physics_editor.enable_body(app.renderer.active_model());await settle();var live: bool=app.physics_editor.is_running();app.mode.select(0);app.change_mode(0);app.color.color=Color.MAGENTA;app.palette_editor.add_current();app.undo()
	check(live and app.physics_editor.is_running(),"palette Undo preserves a real running physics simulation")
	app.physics_editor.clear();check(app.restore_world(doc).is_empty(),"original standard world is restored after the separate physics check");app.set_frame(0)
	var kept: Array=app.palette.duplicate(true);var capacity: Array=[]
	for i in range(32):capacity.append({"name":"Color%d"%i,"rgba":Color8(i,0,0).to_html()})
	app.palette=capacity;app.palette_editor.refresh(true);app.color.color=Color.CYAN;count=app.history.size();revision=app.recovery_revision;app.palette_editor.add_current();check(app.palette.size()==32 and app.history.size()==count and app.recovery_revision==revision,"32-color limit refuses new data without history/recovery edits")
	app.palette=kept;app.palette_editor.refresh(true);app.mode.select(0);app.change_mode(0);app.tool.select(0);app.palette_editor.select(0);stroke(Vector2(300,650),Vector2(600,650));check(image.get_pixel(450,650).to_html()==app.palette[0].rgba,"reused swatch paints exact saved RGBA through the ordinary brush")
	var final_ink:=Storage.image_hash(image);world=World.portable(app.current_world());app.has_project.save_file(packed,"packed");await job();check(FileAccess.file_exists(packed),"packed HAS saves the project palette")
	var manual:=FileAccess.get_sha256(packed);app.has_project.save_file(linked,"linked");await job()
	app.has_project.clear_identity();app.project_folder=folder.path_join("folder-save");app.save();check(Storage.load_project(app.project_folder).get("palette")==app.palette,"legacy folder Save also retains project colors")
	app.changed();app.autosave_tick(true)
	while app.recovery_preview.busy():app.poll_recovery_preview();await process_frame
	var recovery: String=app.recovery_root.path_join(app.recovery_session);var lesson:=Lesson.new();lesson.root=folder.path_join("lessons");check(lesson.save(app,"basic-pose","123456_1",1,false,"step_01"),"lesson checkpoint stores project colors with the whole document")
	var reference: Image=await app.renderer.capture(app.keys,app.layers,0,true);var error: String=await app.export_movie(folder);check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000001.png")).get_data()==reference.get_data(),"reused colors render into the ordinary movie with exact preview PNG")
	var expected:={"palette":app.palette.duplicate(true),"ink":final_ink,"world":world,"keys":keys,"render":Storage.image_hash(reference),"project_hash":manual,"recovery":recovery};FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify(expected))
	root.size=Vector2i(1280,720);await settle();app.inspector_scroll.ensure_control_visible(app.palette_editor.grid);await settle();root.get_texture().get_image().save_png(folder.path_join("palette-1280.png"));check(app.inspector_scroll.get_global_rect().encloses(app.palette_editor.grid.get_global_rect()),"complete swatch grid is reachable in the laptop workspace")
	var movie: String=app.last_export_folder.path_join("movie.mp4");app.new_project();check(app.palette.is_empty() and app.palette_editor.buttons.is_empty(),"New clears project colors without inheriting the old palette")
	var result:={"checks":checks,"failures":failures,"project":packed,"movie":movie};FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("PALETTE_SMOKE ",JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
