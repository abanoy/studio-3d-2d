extends "res://tests/lighting_smoke.gd"
func lights(node: Node,result: Array) -> void:
	if node is Light3D:result.append(node)
	for child in node.get_children():lights(child,result)
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0];var asset:=folder.path_join("scene.glb");var before:=FileAccess.get_sha256(asset)
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	app.load_scene(asset);check(not app.last_import_id.is_empty(),"ordinary scene import accepts emitted static Source entity lights")
	var actor=app.renderer.world_runtime.instance(app.last_import_id);var imported: Array=[];lights(actor.root,imported);var kinds:={}
	for light in imported:kinds[light.get_class()]=true
	check(imported.size()==3 and kinds.has("OmniLight3D") and kinds.has("SpotLight3D") and kinds.has("DirectionalLight3D"),"point spot and sun all survive actual GLB scene loading")
	app.keys=[Model.Timeline.key(0,Vector3(0,1,4),Quaternion.IDENTITY,55)];app.set_frame(0)
	mode(app,"unshaded");var flat: Image=await app.renderer.capture(app.keys,[],0,true);var original: Array=[]
	for light in imported:original.append(light.light_energy);light.light_energy=0
	check((await app.renderer.capture(app.keys,[],0,true)).get_data()==flat.get_data(),"default Unshaded pixels stay independent of Source light intensities")
	mode(app,"lit");var dark: Image=await app.renderer.capture(app.keys,[],0,true)
	for i in range(imported.size()):imported[i].light_energy=original[i]
	var lit: Image=await app.renderer.capture(app.keys,[],0,true)
	check(energy(lit)>energy(dark)+1000 and lit.get_data()!=flat.get_data(),"Lit uses imported static lights without an injected studio lamp")
	var count: int=app.history.size();mode(app,"unshaded");app.undo();check(Lighting.mode(app.video)=="lit" and app.history.size()==count,"lighting Undo restores Lit without changing imported light data")
	Drawing.insert(app.layers[1],0,48,Drawing.blank(1920,1080));var image: Image=Drawing.edit_image(Drawing.cel_at(app.layers[1],0)).image;image.set_pixel(80,80,Color.CYAN);Drawing.touch(image);app.changed()
	var expected: Image=await app.renderer.capture(app.keys,app.layers,0,true);expected.save_png(folder.path_join("expected.png"));var packed:=folder.path_join("Lights.has");app.has_project.save_file(packed,"packed");await wait_job(app.has_project)
	DirAccess.rename_absolute(asset,asset+".offline");app.new_project();app.has_project.open_file(packed);await wait_job(app.has_project)
	check(Lighting.mode(app.video)=="lit" and (await app.renderer.capture(app.keys,app.layers,0,true)).get_data()==expected.get_data(),"packed Open restores exact lit scene and independent drawing with original GLB offline")
	app.changed();app.autosave_tick(true);await preload("res://tests/recovery_wait.gd").checkpoint(app);var recovery: String=app.recovery_root.path_join(app.recovery_session);app.new_project()
	check(app.restore_checkpoint({"folder":recovery}) and (await app.renderer.capture(app.keys,app.layers,0,true)).get_data()==expected.get_data(),"recovery restores exact static lighting and drawing pixels")
	var error: String=await app.export_movie(folder);check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000001.png")).get_data()==expected.get_data(),"actual movie frame matches reopened Lit scene and independent cel exactly")
	DirAccess.rename_absolute(asset+".offline",asset);check(FileAccess.get_sha256(asset)==before,"lighting import never changes emitted source GLB bytes")
	var movie: String=app.last_export_folder.path_join("movie.mp4");print("SOURCE_LIGHTS "+JSON.stringify({"checks":checks,"failures":failures,"movie":movie}));await app.quit_studio();quit(0 if failures==0 else 1)
