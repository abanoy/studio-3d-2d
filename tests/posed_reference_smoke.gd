extends "res://tests/walking_path_smoke.gd"
const World=preload("res://src/world_document.gd")
func _initialize() -> void:
	create_timer(300).timeout.connect(func():push_error("Posed reference watchdog");quit(2));call_deferred("run")
func named_button(text: String) -> Button:
	for node in app.find_children("*","Button",true,false):
		if node.text==text:return node
	return null
func reveal(control: Control) -> void:
	await settled();app.inspector_scroll.ensure_control_visible(control);await settled()
	check(control.is_visible_in_tree() and app.inspector_scroll.get_global_rect().encloses(control.get_global_rect()),"actual control is visible and reachable: "+control.name)
func rotate_part(id: String,degrees: Vector3) -> void:
	var editor=app.pose_editor;editor.tree_items[id].select(0);editor.selected=id;editor.operation.select(0);editor.refresh_values()
	for i in range(3):editor.fields[i].value=degrees[i]
	var button:=named_button("Apply local values");await reveal(button);await click(button)
func opacity(percent: float) -> void:
	app.pose_editor.reference_opacity.value=percent;await reveal(app.pose_editor.apply_reference_opacity);await click(app.pose_editor.apply_reference_opacity)
func run() -> void:
	var args:=OS.get_cmdline_user_args();folder=args[0];app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("reader-recovery" if "--read" in args else "recovery");app.recent_path=folder.path_join("recents.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("reader-cache" if "--read" in args else "writer-cache")
	if "--read" in args:
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")));app.has_project.open_file(folder.path_join("Reference.has"));await wait_job();app.world_selection.select_entity(expected.id);var actor=rig()
		check(actor!=null and actor.data.reference_only and actor.data.reference_opacity==.25 and str(actor.data.source).begins_with(app.has_project.cache_root),"cold source/cache-offline packed Open restores reference-only opacity and real rig")
		var exact:=true
		for at in [48,36,24,12,0]:exact=exact and stamp(actor,at)==expected.samples[str(at)]
		check(exact,"fresh reverse seek restores all five exact root/body poses")
		for at in [12,24,36]:
			var picture: Image=await app.renderer.capture(app.keys,app.layers,at,true);check(picture.get_data()==Image.load_from_file(folder.path_join("final%d.png"%at)).get_data(),"cold final frame excludes reference and preserves exact environment/paint: "+str(at))
		var working: Image=await app.renderer.capture(app.keys,app.layers,24,false);check(working.get_data()==Image.load_from_file(folder.path_join("faded.png")).get_data(),"cold working preview exactly restores transparent posed reference")
		check(Storage.image_hash(Drawing.image(Drawing.cel_at(app.layers[1],0)))==expected.art,"reference-only rendering never flattens editable drawing")
		print("POSED_REFERENCE_READ "+JSON.stringify({"checks":checks,"failures":failures}));await app.quit_studio();quit(0 if failures==0 else 1);return
	var source:=folder.path_join("source-figure.glb");var map:=folder.path_join("source-map.glb");DirAccess.copy_absolute("res://examples/tutorials/Practice figure.glb",source);DirAccess.copy_absolute("res://examples/tutorials/Practice room.glb",map);var hashes: Dictionary={source:FileAccess.get_sha256(source),map:FileAccess.get_sha256(map)}
	app.new_project();var placement: Dictionary=app.import_actions.placement();placement.physics_on_import=false
	check(app.append_object(Model.definition(map),"environment",0,placement).is_empty() and app.pose_editor.add_model(source,0,placement).is_empty(),"original room and separately poseable reference import beside each other")
	app.mode.select(2);app.change_mode(2);var actor=rig();var id: String=actor.data.id;app.world_selection.select_entity(id);app.world_selection.context_action(1);app.set_advanced(true);await settled();var editor=app.pose_editor
	var arm: String=""
	for bone in actor.order:
		if actor.bones[bone].name=="upper_arm_L":arm=bone
	check(not arm.is_empty() and editor.tree_items.has(arm),"real seventeen-bone reference has a meaningful selectable arm")
	if arm.is_empty():await app.quit_studio();quit(1);return
	# Ordinary import places a model in front of the current view. Move the
	# reference to the authored stage origin before setting the test camera.
	editor.selected="@root";editor.operation.select(1);editor.refresh_values()
	for field in editor.fields:field.value=0
	await reveal(named_button("Apply local values"));await click(named_button("Apply local values"))
	check(Timeline.vector(actor.sample_transform(0).position).length()<.00001,"actual numeric root move places imported reference at the authored stage origin")
	app.set_frame(48);await rotate_part(arm,Vector3(0,0,60));await rotate_part("@root",Vector3(0,45,0));app.set_frame(24)
	check(absf(Timeline.quaternion(actor.sample_transform(24).rotation_xyzw).dot(Quaternion(Vector3.UP,deg_to_rad(22.5))))>.99999 and absf(Timeline.quaternion(actor.sample(24)[arm].rotation_xyzw).dot(Quaternion(Vector3.BACK,deg_to_rad(30))))>.99999,"root three-quarter turn and independent waving arm interpolate at shared midpoint")
	app.renderer.camera.position=Vector3(2,1.6,4);app.renderer.camera.look_at(Vector3(0,1,0),Vector3.UP);app.keys=[Timeline.from_camera(0,app.renderer.camera,"ease"),Timeline.from_camera(48,app.renderer.camera,"ease")];var shots: Array=app.keys.duplicate(true)
	app.mode.select(0);app.change_mode(0);app.set_frame(0);app.create_cel(false);var art: Image=Drawing.edit_image(Drawing.cel_at(app.layers[1],0)).image;art.fill_rect(Rect2i(80,80,70,12),Color.CYAN);Drawing.touch(art);app.changed();var art_sha:=Storage.image_hash(art);check(app.import_audio(folder.path_join("tone.wav"),24).is_empty(),"independent drawing and voice offset share reference timeline")
	var start: Image=await app.renderer.capture(app.keys,app.layers,0,true);var visible: Image=await app.renderer.capture(app.keys,app.layers,24,true);check(start.get_data()!=visible.get_data(),"saved root/arm animation visibly changes actual rendered reference")
	app.mode.select(2);app.change_mode(2);app.set_frame(24);app.world_selection.select_entity(id);await reveal(editor.reference_toggle);var before: Dictionary=actor.data.duplicate(true);var history: int=app.history.size();await click(editor.reference_toggle)
	check(actor.data.reference_only and app.history.size()==history+1,"actual reference-only toggle is one reversible edit")
	var full: Image=await app.renderer.capture(app.keys,app.layers,24,false);var excluded: Image=await app.renderer.capture(app.keys,app.layers,24,true);check(full.get_data()==visible.get_data() and full.get_data()!=excluded.get_data(),"working reference stays visible while final hides it")
	app.undo();check(actor.data==before,"Undo restores exact reference/output flags");app.redo();check(actor.data.reference_only,"Redo restores reference-only intent")
	await opacity(25);var saved: Dictionary=actor.data.duplicate(true);var faded: Image=await app.renderer.capture(app.keys,app.layers,24,false);faded.save_png(folder.path_join("faded.png"));check(actor.data.reference_opacity==.25 and faded.get_data()!=full.get_data() and faded.get_data()!=excluded.get_data(),"working opacity visibly fades real reference geometry without hiding scene")
	check((await app.renderer.capture(app.keys,app.layers,24,true)).get_data()==excluded.get_data(),"reference opacity leaves final pixels exactly unchanged")
	app.undo();check(not actor.data.has("reference_opacity"),"opacity Undo restores legacy full-opacity state");app.redo();check(actor.data==saved,"opacity Redo restores exact setting and pose keys")
	await opacity(0);check((await app.renderer.capture(app.keys,app.layers,24,false)).get_data()==excluded.get_data(),"zero working reference opacity matches geometry excluded from output");app.undo()
	await opacity(100);check(not actor.data.has("reference_opacity") and (await app.renderer.capture(app.keys,app.layers,24,false)).get_data()==full.get_data(),"full opacity removes optional field and restores exact original appearance");app.undo()
	await reveal(editor.reference_toggle);await click(editor.reference_toggle);check(not actor.data.reference_only and not editor.reference_opacity_row.visible and (await app.renderer.capture(app.keys,app.layers,24,true)).get_data()==visible.get_data(),"turning reference-only off restores full output geometry despite retained working amount");app.undo()
	app.video.visibility_fade_ms=0;await reveal(editor.visible_toggle);await click(editor.visible_toggle);var hidden: Image=await app.renderer.capture(app.keys,app.layers,24,false);check(not actor.visible_at(24) and hidden.get_data()==excluded.get_data(),"working visibility toggle hides reference independently of final exclusion");app.undo();check(actor.visible_at(24) and actor.data==saved,"visibility Undo restores prior reference pose/opacity exactly")
	var data: Dictionary=actor.data.duplicate(true);var view: Dictionary=app.renderer.view_state();app.navigation_scheme="orbit";var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.pressed=true;event.ctrl_pressed=true;app.canvas_input(event,Vector2(960,540));var motion:=InputEventMouseMotion.new();motion.relative=Vector2(190,0);app.canvas_input(motion,Vector2(960,540));event=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;app._input(event);await settled()
	check(app.renderer.view_state()!=view and actor.data==data and app.keys==shots,"routed three-quarter orbit changes only inspection camera, preserving reference and authored shot")
	root.get_texture().get_image().save_png(folder.path_join("reference-inspection.png"));app.renderer.restore_view(view)
	var bad:=data.duplicate(true);bad["reference_opacity"]=2.;var world_before=app.renderer.world_runtime.root;check(not editor.restore_state(bad).is_empty() and actor.data==data and app.renderer.world_runtime.root==world_before,"invalid opacity edit refuses before changing installed reference")
	var samples: Dictionary={}
	for at in [0,12,24,36,48]:samples[str(at)]=stamp(actor,at)
	for at in [12,24,36]:
		var picture: Image=await app.renderer.capture(app.keys,app.layers,at,true);picture.save_png(folder.path_join("final%d.png"%at))
	app.set_frame(24);app.changed();app.autosave_tick(true);await preload("res://tests/recovery_wait.gd").checkpoint(app);var recovered:=Storage.load_project(app.recovery_root.path_join(app.recovery_session));var found:=false
	if not recovered.has("error"):
		for row in recovered.world.objects:
			if row.id==id:found=row.reference_only and row.reference_opacity==.25
	check(found,"real recovery checkpoint preserves reference-only pose and working opacity")
	app.has_project.save_file(folder.path_join("Reference.has"),"packed");await wait_job();check(FileAccess.file_exists(folder.path_join("Reference.has")),"ordinary packed save preserves reference model and separate working-opacity intent")
	var movie_error: String=await app.export_movie(folder);var movie: String=app.last_finished_movie;check(movie_error.is_empty() and FileAccess.file_exists(movie),"ordinary MP4 exports scene/drawing/audio with reference excluded")
	for at in [12,24,36]:check(Image.load_from_file(app.last_export_folder.path_join("frame_%06d.png"%(at+1))).get_data()==Image.load_from_file(folder.path_join("final%d.png"%at)).get_data(),"movie input exactly equals reference-excluded final preview: "+str(at))
	check(app.keys==shots and Storage.image_hash(Drawing.image(Drawing.cel_at(app.layers[1],0)))==art_sha and FileAccess.get_sha256(source)==hashes[source] and FileAccess.get_sha256(map)==hashes[map],"reference workflow preserves authored camera, independent RGBA and both original assets")
	FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify({"id":id,"art":art_sha,"samples":samples,"sources":hashes,"movie":movie}));print("POSED_REFERENCE_WRITE "+JSON.stringify({"checks":checks,"failures":failures,"movie":movie}));await app.quit_studio();quit(0 if failures==0 else 1)
