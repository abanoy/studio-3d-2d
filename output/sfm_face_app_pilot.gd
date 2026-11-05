extends SceneTree
const Model=preload("res://src/model.gd")
const Shape=Model.Shape
const A=Model.ShapeAnimation
const Timeline=Model.Timeline
const Drawing=preload("res://src/drawing.gd")
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(220).timeout.connect(func():push_error("SFM face pilot watchdog");quit(2));call_deferred("run")
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func settled() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func wait_job(job) -> void:
	while job.pid>0:await process_frame
	await settled()
func select_shape(app,node: int,index: int) -> void:
	var editor=app.pose_editor.animated_shapes
	for i in range(editor.parts.item_count):
		if int(editor.parts.get_item_metadata(i))==node:editor.parts.select(i);editor.parts.item_selected.emit(i);break
	for i in range(editor.shapes.item_count):
		if int(editor.shapes.get_item_metadata(i))==index:editor.shapes.select(i);editor.shapes.item_selected.emit(i);return
	check(false,"requested native target is available in real shape editor")
func apply_amount(app,node: int,index: int,value: float) -> void:
	select_shape(app,node,index);var editor=app.pose_editor.animated_shapes;editor.amount.value=value;editor.apply_button.pressed.emit()
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0]
	var plan: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("app-plan.json")))
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled()
	app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("has-cache")
	if args.size()>1 and args[1]=="reader":
		app.has_project.open_file(folder.path_join("face-packed.has"));await wait_job(app.has_project)
		var actor: RefCounted=app.renderer.world_runtime.instance(plan.id)
		check(actor!=null,"cold engine opens actual packed face project")
		if actor:
			app.set_frame(12);await settled();var snapshot:=Shape.snapshot(actor.root)
			for control in plan.controls:check(absf(float(snapshot[str(int(control.node))][int(control.index)])-.45)<.00001,"cold open preserves animated "+control.name)
			check(actor.data.metadata==plan.metadata and actor.order==plan.bone_ids,"cold open preserves exact native metadata and bone identities")
			var managed: String=actor.data.source.replace("\\","/")
			check(managed.begins_with(folder.path_join("has-cache").replace("\\","/")+"/") and FileAccess.get_sha256(actor.data.source)==plan.source_sha256,"cold open resolves exact managed packed GLB")
			check(Drawing.cel_at(app.layers[1],12).image.get_pixel(80,80)==Color.CYAN,"cold open preserves independent editable overlay")
			var image: Image=await app.renderer.capture(app.keys,app.layers,12,true);image.save_png(folder.path_join("cold.png"))
			var reference:=Image.load_from_file(folder.path_join("middle.png"));var left:=reference.get_data();var right:=image.get_data();var changed:=0;var total:=0
			for i in range(mini(left.size(),right.size())):
				var distance:=absi(int(left[i])-int(right[i]));total+=distance
				if distance>0:changed+=1
			var mean:=float(total)/maxi(left.size(),1);plan.cold_pixels={"changed_channels":changed,"mean_absolute_byte_error":mean}
			check(left.size()==right.size() and changed<=384 and mean<=.002,"cold render agrees within retained native mesh-edge bound")
		var result:={"checks":checks,"failures":failures,"pixels":plan.get("cold_pixels",{})};FileAccess.open(folder.path_join("reader-result.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("SFM_FACE_READER "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1);return
	var error: String=app.pose_editor.add_model(plan.source);var actor: RefCounted=app.renderer.active_model()
	check(error.is_empty() and actor!=null,"actual supplied Source head imports into ordinary standard model")
	if not actor:app.free();quit(1);return
	var id: String=actor.data.id;var original: Dictionary=actor.data.duplicate(true);var bone_ids: Array=actor.order.duplicate()
	var descriptor: Dictionary=actor.root.get_meta(Shape.META)
	check(actor.order.size()==229 and descriptor.error.is_empty() and descriptor.rows.size()==1,"229 native bones and exact facial mesh binding resolve")
	check(actor.data.metadata.native_parameters.native_parameters.flex_controllers.size()==82,"82 native controller descriptions are retained")
	var bounds: AABB=app.renderer.scene_bounds(actor.root);var center:=bounds.get_center()
	var framing_distance:=maxf(bounds.size.y,bounds.size.x/(1920./1080.))*.6/tan(deg_to_rad(45.)*.5)+bounds.size.z*.5
	app.renderer.camera.position=center+Vector3(0,0,maxf(framing_distance,.5));app.renderer.camera.look_at(center,Vector3.UP)
	app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,45)]
	var camera_keys: Array=app.keys.duplicate(true);app.set_frame(0);await settled()
	var neutral: Image=await app.renderer.capture(app.keys,app.layers,0,true);neutral.save_png(folder.path_join("neutral.png"))
	app.pose_editor.open_shapes();await settled()
	check(not app.advanced_mode and app.pose_editor.shape_window.visible,"actual imported face controls open in Simple")
	for frame in [0,24]:
		app.set_frame(frame);app.pose_editor.interpolation.select(1)
		for control in plan.controls:apply_amount(app,control.node,control.index,.1 if frame==0 else .8)
		await settled()
	check(actor.authored_keys().is_empty() and actor.data.pose==original.pose and app.keys==camera_keys,"expression edits leave bone pose, body keys and explicit camera keys intact")
	app.set_frame(12);await settled();var snapshot:=Shape.snapshot(actor.root)
	for control in plan.controls:check(absf(float(snapshot[str(int(control.node))][int(control.index)])-.45)<.00001,"master timeline interpolates native "+control.name)
	app.set_frame(24);await settled();var before: Image=await app.renderer.capture(app.keys,app.layers,24,true)
	app.undo();await settled();var undone: Image=await app.renderer.capture(app.keys,app.layers,24,true)
	app.redo();await settled();var redone: Image=await app.renderer.capture(app.keys,app.layers,24,true)
	check(before.get_data()!=undone.get_data() and before.get_data()==redone.get_data(),"actual face deformation visibly changes and exact Undo/Redo restores it")
	redone.save_png(folder.path_join("expressive.png"));check(neutral.get_data()!=redone.get_data(),"native face has a visible neutral-to-expression change")
	var geometry_error:=0.0
	for row in descriptor.rows:
		var baked: ArrayMesh=row.mesh.bake_mesh_from_current_blend_shape_mix()
		for surface in range(baked.get_surface_count()):
			var positions: PackedVector3Array=baked.surface_get_arrays(surface)[Mesh.ARRAY_VERTEX]
			var cpu:=Shape.vertices(row.mesh,surface,row.mesh.mesh.surface_get_arrays(surface)[Mesh.ARRAY_VERTEX])
			for v in range(positions.size()):geometry_error=maxf(geometry_error,positions[v].distance_to(cpu[v]))
	check(geometry_error<.00001,"actual baked geometry agrees with shared shape evaluation")
	Drawing.insert(app.layers[1],0,48,Drawing.blank(1920,1080));Drawing.cel_at(app.layers[1],0).image.set_pixel(80,80,Color.CYAN)
	app.pose_editor.shape_window.hide();app.set_frame(12);await settled()
	var metadata: Dictionary=actor.data.metadata.duplicate(true)
	for mode in ["packed","linked"]:
		app.has_project.save_file(folder.path_join("face-"+mode+".has"),mode);await wait_job(app.has_project)
		app.new_project();app.has_project.open_file(folder.path_join("face-"+mode+".has"));await wait_job(app.has_project);actor=app.renderer.world_runtime.instance(id);app.set_frame(12);await settled()
		check(actor!=null and actor.order==bone_ids and actor.data.metadata==metadata,"native identities and metadata survive "+mode+" HAS")
		if actor:
			var reopened:=Shape.snapshot(actor.root)
			for control in plan.controls:check(absf(float(reopened[str(int(control.node))][int(control.index)])-.45)<.00001,"reopened "+mode+" retains "+control.name)
		check(Drawing.cel_at(app.layers[1],12).image.get_pixel(80,80)==Color.CYAN,"reopened "+mode+" overlay remains editable")
	var preview: Image=await app.renderer.capture(app.keys,app.layers,12,true);preview.save_png(folder.path_join("middle.png"))
	var export_error: String=await app.export_movie(folder);var movie: String=app.last_export_folder.path_join("movie.mp4")
	check(export_error.is_empty() and FileAccess.file_exists(movie) and Image.load_from_file(app.last_export_folder.path_join("frame_000013.png")).get_data()==preview.get_data(),"normal MP4 frame12 matches reopened expression and overlay exactly")
	plan.id=id;plan.metadata=metadata;plan.bone_ids=bone_ids;FileAccess.open(folder.path_join("app-plan.json"),FileAccess.WRITE).store_string(JSON.stringify(plan))
	var result:={"checks":checks,"failures":failures,"movie":movie,"geometry_error":geometry_error,"face_targets":descriptor.rows[0].names.size()}
	FileAccess.open(folder.path_join("app-result.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("SFM_FACE_APP "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
