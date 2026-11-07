extends "res://tests/lighting_smoke.gd"
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0];var asset:=folder.path_join("scene.glb");var original:=FileAccess.get_sha256(asset)
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	check(app.load_scene(asset).is_empty(),"ordinary map import accepts portable baked brush lighting")
	var actor=app.renderer.world_runtime.instance(app.last_import_id);var metadata: Dictionary=actor.data.metadata.duplicate(true)
	check(metadata.get("native_parameters",{}).get("static_brush_lightmaps",{}).get("faces")==1,"native report retains static face count and explicit styled-light limitation")
	var uv2:=false
	for node in actor.root.find_children("*","MeshInstance3D",true,false):
		for surface in node.mesh.get_surface_count():
			var material: Material=node.mesh.surface_get_material(surface)
			if material is BaseMaterial3D and material.emission_enabled:uv2=uv2 or material.emission_on_uv2
	check(uv2,"standard GLB import honors explicit emission UV1 selection")
	app.keys=[Model.Timeline.key(0,Vector3(0,1,4),Quaternion.IDENTITY,55)];app.set_frame(0);mode(app,"lit")
	var lit: Image=await app.renderer.capture(app.keys,[],0,true);var tl:=lit.get_pixel(830,410);var tr:=lit.get_pixel(1090,410);var bl:=lit.get_pixel(830,670)
	check(tl.b>tl.r+.05 and tr.g>tr.r+.05 and bl.r>bl.g+.05,"actual rendered blue green red luxel regions preserve source orientation")
	var lamp:=DirectionalLight3D.new();lamp.light_energy=20;lamp.rotation=Vector3(-.6,.3,0);actor.root.add_child(lamp);await settled();var relit: Image=await app.renderer.capture(app.keys,[],0,true)
	check(relit.get_region(Rect2i(730,320,450,440)).get_data()==lit.get_region(Rect2i(730,320,450,440)).get_data(),"baked surface keeps exact illumination when a runtime light is added")
	lamp.free();var history: int=app.history.size();mode(app,"unshaded");var flat: Image=await app.renderer.capture(app.keys,[],0,true);var color:=flat.get_pixel(830,410)
	check(color.r>.2 and absf(color.r-color.b)<.01 and absf(flat.get_pixel(830,410).r-flat.get_pixel(1090,410).r)>.05 and flat.get_data()!=lit.get_data(),"Unshaded hides baked lighting and restores original striped base texture through the existing mode control")
	app.undo();check(Lighting.mode(app.video)=="lit" and app.history.size()==history,"ordinary lighting Undo restores Lit without rewriting baked asset")
	Drawing.insert(app.layers[1],0,48,Drawing.blank(1920,1080));var image: Image=Drawing.edit_image(Drawing.cel_at(app.layers[1],0)).image;image.set_pixel(80,80,Color.CYAN);Drawing.touch(image);app.changed()
	var expected: Image=await app.renderer.capture(app.keys,app.layers,0,true);expected.save_png(folder.path_join("expected.png"));var packed:=folder.path_join("Lightmaps.has");app.has_project.save_file(packed,"packed");await wait_job(app.has_project)
	check(FileAccess.file_exists(packed),"portable HAS saves baked textures and editable native report")
	DirAccess.rename_absolute(asset,asset+".offline");app.new_project();app.has_project.open_file(packed);await wait_job(app.has_project)
	check(Lighting.mode(app.video)=="lit" and (await app.renderer.capture(app.keys,app.layers,0,true)).get_data()==expected.get_data(),"source-offline packed Open restores exact baked lighting camera and independent drawing")
	actor=app.renderer.world_runtime.instances.values()[0];check(actor.data.metadata.native_parameters==metadata.native_parameters,"packed replay preserves complete lightmap provenance and limitations")
	app.changed();app.autosave_tick(true);await preload("res://tests/recovery_wait.gd").checkpoint(app);var recovery: String=app.recovery_root.path_join(app.recovery_session);app.new_project()
	check(app.restore_checkpoint({"folder":recovery}) and (await app.renderer.capture(app.keys,app.layers,0,true)).get_data()==expected.get_data(),"recovery restores exact baked textures and independent pixels")
	var error: String=await app.export_movie(folder);check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000001.png")).get_data()==expected.get_data(),"real movie input agrees exactly with reopened baked scene")
	DirAccess.rename_absolute(asset+".offline",asset);check(FileAccess.get_sha256(asset)==original,"map import and authoring preserve emitted source GLB bytes")
	var movie: String=app.last_export_folder.path_join("movie.mp4");print("SOURCE_LIGHTMAPS "+JSON.stringify({"checks":checks,"failures":failures,"movie":movie}));await app.quit_studio();quit(0 if failures==0 else 1)
