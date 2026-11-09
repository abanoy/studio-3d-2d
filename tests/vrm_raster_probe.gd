extends SceneTree
const Storage=preload("res://src/storage.gd")
var app
var noise: Array=[]
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func _initialize() -> void:
	create_timer(240).timeout.connect(func():quit(2));call_deferred("run")
func settle() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func snapshot(actor) -> Dictionary:
	var bones:={}
	for id in actor.order:
		var row: Dictionary=actor.bones[id]
		bones[id]={"base":var_to_bytes(row.base).hex_encode(),"global":var_to_bytes(actor.bone_transform(id)).hex_encode()}
	return {"camera":var_to_bytes(app.renderer.camera.global_transform).hex_encode(),"fov":app.renderer.camera.fov,"root":var_to_bytes(actor.root.global_transform).hex_encode(),"bones":bones}
func order_materials(actor,mode: String) -> Array:
	var materials: Array=[];var rows: Array=[]
	for mesh in actor.root.find_children("*","MeshInstance3D",true,false):
		for surface in range(mesh.mesh.get_surface_count()):
			var material=mesh.get_active_material(surface)
			if not material is BaseMaterial3D:continue
			if mode=="copy":
				material=material.duplicate();mesh.set_surface_override_material(surface,material)
			if not material in materials:materials.append(material)
	for i in range(materials.size()):
		var material: BaseMaterial3D=materials[i]
		if mode=="order" and material.transparency in [BaseMaterial3D.TRANSPARENCY_DISABLED,BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR]:material.render_priority=-128+i
		if mode=="legacy" and material.transparency==BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR:material.render_priority=0
		rows.append({"name":material.resource_name,"transparency":material.transparency,"priority":material.render_priority})
	return rows
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0];var original: String=args[1];var mode: String=args[2]
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recent.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	var rows: Array=[]
	for name in ["Avatar1","Marisa"]:
		var first_pixels:="";var first_state:={}
		for count in [0,7,23,13,31]:
			for i in range(count):noise.append(StandardMaterial3D.new())
			app.new_project();app.has_project.open_file(original.path_join(name+".has"))
			while app.has_project.pid>0:await process_frame
			await settle();var actor=app.renderer.world_runtime.instances.values()[0]
			var materials:=order_materials(actor,mode);var image: Image=await app.renderer.capture(app.keys,[],0,true)
			var prefix:="%s-%s-%d" % [name,mode,count];image.save_png(folder.path_join(prefix+".png"))
			var state:=snapshot(actor);var pixels:=Storage.image_hash(image)
			FileAccess.open(folder.path_join(prefix+"-state.json"),FileAccess.WRITE).store_string(JSON.stringify(state,"",true,true))
			if first_pixels.is_empty():first_pixels=pixels;first_state=state
			else:
				check(state==first_state,name+" bone/root/camera transform bits stay exact across rebuild")
				if mode=="default":check(pixels==first_pixels,name+" unmodified product pixels stay exact across GPU allocation changes")
			var row:={"name":name,"mode":mode,"noise":count,"pixels":Storage.image_hash(image),"materials":materials};rows.append(row);print("RASTER_PROBE "+JSON.stringify(row))
	FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE).store_string(JSON.stringify(rows,"",true,true));print("RASTER_PROBE_RESULT "+JSON.stringify({"checks":checks,"failures":failures,"mode":mode}));app.free();quit(0 if failures==0 else 1)
