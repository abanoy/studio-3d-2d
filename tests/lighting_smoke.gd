extends SceneTree
const Lighting=preload("res://src/lighting.gd")
const Model=preload("res://src/model.gd")
const SceneIO=preload("res://src/scene3d.gd")
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
var checks:=0
var failures:=0
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func _initialize() -> void:
	create_timer(150).timeout.connect(func():push_error("Lighting watchdog");quit(2));call_deferred("run")
func settled() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func wait_job(job) -> void:
	while job.pid>0:await process_frame
	await settled()
func energy(image: Image) -> float:
	var bytes:=image.get_data();var total:=0.
	for i in range(0,bytes.size(),4*5):total+=int(bytes[i])+int(bytes[i+1])+int(bytes[i+2])
	return total
func mode(app,kind: String) -> void:
	app.lighting_choice.item_selected.emit(Lighting.MODES.find(kind))
func find_light(node: Node) -> Light3D:
	if node is Light3D:return node
	for child in node.get_children():
		var found:=find_light(child)
		if found:return found
	return null
func fixture(path: String) -> void:
	var scene:=Node3D.new();scene.name="LightFixture"
	SceneIO.box(scene,"Panel",Vector3(0,1,0),Vector3(2,2,.2),Color("8080c0"))
	var light:=DirectionalLight3D.new();scene.add_child(light);light.owner=scene;light.rotation_degrees=Vector3(-30,20,0);light.light_energy=1.5
	var doc:=GLTFDocument.new();var state:=GLTFState.new();assert(doc.append_from_scene(scene,state)==OK);assert(doc.write_to_filesystem(state,path)==OK);scene.free()
func materials() -> void:
	var mesh:=MeshInstance3D.new();mesh.mesh=BoxMesh.new();var authored:=StandardMaterial3D.new()
	authored.albedo_color=Color(.3,.5,.7,.2);authored.emission_enabled=true;authored.emission=Color.RED;mesh.material_override=authored
	var controller:=Model.Opacity.new();controller.inventory(mesh);controller.set_appearance(1.,true)
	check(mesh.material_override!=authored and mesh.material_override.shading_mode==BaseMaterial3D.SHADING_MODE_UNSHADED and not mesh.material_override.emission_enabled,"unshaded uses an instance copy and base color without added emission")
	check(authored.shading_mode==BaseMaterial3D.SHADING_MODE_PER_PIXEL and authored.emission_enabled and authored.albedo_color.a==Color(.3,.5,.7,.2).a,"native shading, emission and alpha remain unchanged")
	controller.set_appearance(.5,true)
	check(absf(mesh.material_override.albedo_color.a-.5)<.00001 and mesh.material_override.shading_mode==BaseMaterial3D.SHADING_MODE_UNSHADED,"unshaded and visibility fade compose once from effective opaque alpha")
	controller.set_appearance(.5,false);check(absf(mesh.material_override.albedo_color.a-.5)<.00001 and mesh.material_override.shading_mode==authored.shading_mode,"switching to Lit during a fade retains the current opacity")
	controller.set_appearance(1.,false);check(mesh.material_override==authored and not controller.active,"Lit endpoint restores the exact authored material reference")
	mesh.free()
	var shared:=BoxMesh.new();var cutout:=StandardMaterial3D.new();cutout.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
	var pixels:=Image.create(2,2,false,Image.FORMAT_RGBA8);pixels.fill(Color(.2,.6,.8,.4));cutout.albedo_texture=ImageTexture.create_from_image(pixels);shared.material=cutout
	var first:=MeshInstance3D.new();first.mesh=shared;var peer:=MeshInstance3D.new();peer.mesh=shared;var independent:=Model.Opacity.new();independent.inventory(first)
	independent.set_appearance(1.,true)
	check(first.get_active_material(0)!=cutout and peer.get_active_material(0)==cutout and shared.surface_get_material(0)==cutout,"shared mesh/material resources and peer instances remain authored")
	check(first.get_active_material(0).albedo_texture==cutout.albedo_texture and first.get_active_material(0).transparency==cutout.transparency,"unshaded keeps texture identity and native cutout mode")
	independent.set_appearance(.4,true);independent.set_appearance(1.,true)
	check(first.get_active_material(0).transparency==cutout.transparency and pixels.get_pixel(0,0)==Color(.2,.6,.8,.4),"fade endpoint restores cutouts without modifying texture pixels")
	independent.set_appearance(1.,false);check(first.get_surface_override_material(0)==null and first.get_active_material(0)==cutout,"surface overrides restore their exact original absence")
	first.free();peer.free()
func run() -> void:
	materials();var folder: String=OS.get_cmdline_user_args()[0]
	var asset:=folder.path_join("lit.glb");fixture(asset);var hash:=FileAccess.get_sha256(asset)
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settled();app.home.hide()
	app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	check(not app.advanced_mode and app.lighting_choice.is_visible_in_tree() and Lighting.mode(app.video)=="unshaded","new Simple projects default to an accessible Unshaded control")
	app.load_scene(asset);var id: String=app.last_import_id;var actor: RefCounted=app.renderer.world_runtime.instance(id)
	app.renderer.camera.position=Vector3(3,2,6);app.renderer.camera.look_at(Vector3(0,1,0));app.keys=[Model.Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,55)]
	var light:=find_light(actor.root);check(light!=null,"ordinary GLB import retains an actual authored light")
	if not light:app.free();quit(1);return
	var authored_energy: float=light.light_energy
	app.set_frame(0);var flat: Image=await app.renderer.capture(app.keys,[],0,true);flat.save_png(folder.path_join("unshaded.png"))
	light.light_energy=0;var flat_dark: Image=await app.renderer.capture(app.keys,[],0,true)
	check(flat.get_data()==flat_dark.get_data() and energy(flat)>1000,"unshaded pixels do not depend on imported light intensity")
	var before: Dictionary=app.renderer.world_state().duplicate(true);var keys: Array=app.keys.duplicate(true);var view: Transform3D=app.renderer.camera.transform;var count: int=app.history.size()
	mode(app,"lit")
	var view_preserved: bool=app.renderer.camera.transform==view
	await settled();var dark: Image=await app.renderer.capture(app.keys,[],0,true)
	check(energy(dark)<energy(flat)*.01 and not app.renderer.studio_light.visible,"Lit without scene light is dark and does not inject the old studio lamp")
	check(app.history.size()==count+1 and app.keys==keys and app.renderer.world_state()==before and view_preserved,"lighting is one project Undo edit with no pose, camera or world-data mutation")
	light.light_energy=authored_energy;var lit: Image=await app.renderer.capture(app.keys,[],0,true);lit.save_png(folder.path_join("lit.png"))
	check(energy(lit)>energy(dark)+1000 and lit.get_data()!=flat.get_data(),"Lit responds to a real imported light")
	app.undo();await settled();check(Lighting.mode(app.video)=="unshaded" and (await app.renderer.capture(app.keys,[],0,true)).get_data()==flat.get_data(),"Undo restores exact Unshaded pixels")
	app.redo();await settled();check(Lighting.mode(app.video)=="lit","Redo restores the saved lighting choice")
	app.video.erase("lighting_mode");app.set_frame(0);var legacy: Image=await app.renderer.capture(app.keys,[],0,true)
	mode(app,"unshaded");mode(app,"studio");var studio: Image=await app.renderer.capture(app.keys,[],0,true)
	check(studio.get_data()==legacy.get_data() and app.renderer.studio_light.visible,"old projects without a mode retain their original studio illumination")
	mode(app,"unshaded");app.set_advanced(true);app.set_advanced(false)
	check(Lighting.mode(app.video)=="unshaded" and (await app.renderer.capture(app.keys,[],0,true)).get_data()==flat.get_data(),"Simple and Advanced retain identical lighting state and pixels")
	Drawing.insert(app.layers[1],0,48,Drawing.blank(1920,1080));Drawing.edit_image(Drawing.cel_at(app.layers[1],0)).image.set_pixel(80,80,Color.CYAN)
	var bad: Dictionary=app.video.duplicate(true);bad.lighting_mode="unknown"
	check(not Storage.save_project(folder.path_join("bad"),bad,app.keys,app.layers,"",0,{}, {},{},false,app.renderer.world_state()).is_empty() and not FileAccess.file_exists(folder.path_join("bad/project.json")),"invalid lighting modes refuse before writing project data")
	for kind in ["unshaded","lit"]:
		mode(app,kind)
		for packing in ["packed","linked"]:
			var path:=folder.path_join(kind+"-"+packing+".has");app.has_project.save_file(path,packing);await wait_job(app.has_project)
			var expected: Image=await app.renderer.capture(app.keys,app.layers,0,true);app.new_project();app.has_project.open_file(path);await wait_job(app.has_project)
			check(Lighting.mode(app.video)==kind and (await app.renderer.capture(app.keys,app.layers,0,true)).get_data()==expected.get_data() and Drawing.image(Drawing.cel_at(app.layers[1],0)).get_pixel(80,80)==Color.CYAN,kind+" and independent drawing survive "+packing+" HAS")
	mode(app,"unshaded");app.changed();app.autosave_tick(true);await preload("res://tests/recovery_wait.gd").checkpoint(app);var recovery: String=app.recovery_root.path_join(app.recovery_session);app.new_project()
	check(app.restore_checkpoint({"folder":recovery}) and Lighting.mode(app.video)=="unshaded","recovery retains project lighting as an unsaved editable copy")
	var expected: Image=await app.renderer.capture(app.keys,app.layers,0,true);var error: String=await app.export_movie(folder)
	check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000001.png")).get_data()==expected.get_data(),"final MP4 uses the same lighting and independent cel as reopened preview")
	check(FileAccess.get_sha256(asset)==hash,"lighting never edits the original asset")
	var movie: String=app.last_export_folder.path_join("movie.mp4")
	var plans: Array=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("native-plans.json")))
	for plan in plans:
		app.new_project();app.pose_editor.add_model(plan.source);actor=app.renderer.active_model()
		actor.data.metadata.merge(plan.metadata,true)
		var ids: Array=actor.order.duplicate();var metadata: Dictionary=actor.data.metadata.duplicate(true)
		mode(app,"lit");mode(app,"unshaded");app.pose_editor.frame_model();app.keys=[Model.Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,55)]
		var unlit: Image=await app.renderer.capture(app.keys,[],0,true)
		check(energy(unlit)>1000 and actor.order==ids and actor.data.metadata==metadata,"native material view preserves rig/provenance and shows base colors: "+plan.label)
	var result:={"checks":checks,"failures":failures,"movie":movie,"folder":folder};var file:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close()
	print("LIGHTING "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
