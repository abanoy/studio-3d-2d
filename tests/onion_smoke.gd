extends SceneTree
const Onion=preload("res://src/onion_editor.gd")
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
const World=preload("res://src/world_document.gd")
var app
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(130).timeout.connect(func():push_error("Onion watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func equal(a,b) -> bool:return JSON.parse_string(JSON.stringify(a,"",true,true))==JSON.parse_string(JSON.stringify(b,"",true,true))
func settled() -> void:
	for i in range(5):await process_frame
	await RenderingServer.frame_post_draw
func job() -> void:
	while app.has_project.pid>0:await process_frame
	await settled()
func sample(image: Image,point: Vector2) -> Color:
	var rect: Rect2=app.canvas.image_rect();var p: Vector2=app.canvas.global_position+rect.position+point/Vector2(1920,1080)*rect.size
	return image.get_pixel(int(p.x),int(p.y))
func click(point: Vector2) -> void:
	var e:=InputEventMouseButton.new();e.button_index=MOUSE_BUTTON_LEFT;e.pressed=true
	var rect: Rect2=app.canvas.image_rect();e.position=rect.position+point/Vector2(1920,1080)*rect.size;app.canvas._gui_input(e);e.pressed=false;app.canvas._gui_input(e)
func hashes() -> Array:
	var result: Array=[]
	for cel in app.layers[1].cels:result.append(Storage.image_hash(Drawing.image(cel)))
	return result
func run() -> void:
	var layer:={"cels":[{"id":"none","start":0,"duration":8},{"id":"held","start":12,"duration":12},{"id":"end","start":36,"duration":12}]}
	var n:=Onion.neighbors(layer,18);check(n.previous.id=="none" and n.next.id=="end","held frames use previous and next exposures rather than the current held drawing")
	n=Onion.neighbors(layer,8);check(n.previous.id=="none" and n.next.id=="held","gaps retain their surrounding exposure guides")
	n=Onion.neighbors(layer,0);check(n.previous.is_empty() and n.next.id=="held","first exposure has no invented previous drawing")
	n=Onion.neighbors(layer,47);check(n.previous.id=="held" and n.next.is_empty(),"last exposure has no invented next drawing")
	n=Onion.neighbors({"cels":[]},0);check(n.previous.is_empty() and n.next.is_empty(),"empty layer has no guides")
	var folder: String=OS.get_cmdline_user_args()[0];app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settled()
	app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache");app.mode.select(0);app.change_mode(0)
	check(not app.onion_editor.enabled.button_pressed and not app.onion_editor.views[0].visible,"onion guides default off in Simple")
	var boxes: Array=[Rect2i(400,300,140,140),Rect2i(900,500,140,140),Rect2i(1300,300,140,140)]
	for i in range(3):
		var image:=Drawing.blank(1920,1080);image.fill_rect(boxes[i],Color.BLACK)
		app.layers[1].cels.append({"id":str(i),"start":[0,12,36][i],"duration":[8,12,12][i],"image":image})
	app.changed();app.set_frame(18);await settled()
	var original:=hashes();var keys: Array=app.keys.duplicate(true);var world: Dictionary=World.portable(app.current_world());var view: Dictionary=app.renderer.view_state();var source_hash:=FileAccess.get_sha256(app.source)
	var revision: int=app.recovery_revision;var actions: int=app.autosave_actions;var history: int=app.history.size();var baseline: Image=root.get_texture().get_image()
	var final_before: Image=await app.renderer.capture(app.keys,app.layers,18,true)
	app.onion_editor.enabled.button_pressed=true;await settled()
	check(app.onion_editor.views[0].visible and app.onion_editor.views[1].visible,"Simple toggle shows two actual GPU ghost drawings")
	check(app.onion_editor.views[0].texture.get_image().get_data()==Drawing.image(app.layers[1].cels[0]).get_data() and app.onion_editor.views[1].texture.get_image().get_data()==Drawing.image(app.layers[1].cels[2]).get_data(),"guides bind exact unmodified source alpha textures")
	var screen: Image=root.get_texture().get_image();screen.save_png(folder.path_join("onion.png"))
	check(sample(screen,Vector2(470,370))!=sample(baseline,Vector2(470,370)) and sample(screen,Vector2(1370,370))!=sample(baseline,Vector2(1370,370)),"previous and next opaque-black source marks become visible tinted screen guides")
	check(sample(screen,Vector2(970,570))==sample(baseline,Vector2(970,570)),"current opaque drawing remains exactly above the ghosts")
	check(app.onion_editor.views[0].material.get_shader_parameter("ghost_color")!=app.onion_editor.views[1].material.get_shader_parameter("ghost_color"),"previous blue and next pink remain distinguishable")
	check(hashes()==original and equal(keys,app.keys) and equal(world,World.portable(app.current_world())) and equal(view,app.renderer.view_state()) and FileAccess.get_sha256(app.source)==source_hash,"guides preserve exact source drawings, world, camera/view and geometry")
	check(app.recovery_revision==revision and app.autosave_actions==actions and app.history.size()==history,"enabling guides is not a document edit or autosave action")
	var final_on: Image=await app.renderer.capture(app.keys,app.layers,18,true);check(final_on.get_data()==final_before.get_data(),"ghosts are absent from the actual final-render evaluator")
	app.set_frame(8);app.tool.select(2);click(Vector2(470,370));var until:=Time.get_ticks_msec()+15000
	while app.fill_editor.busy() and Time.get_ticks_msec()<until:await process_frame
	await settled();check(not app.fill_editor.busy() and not app.fill_editor.pending.is_empty() and app.fill_editor.last_result.region==1920*1080,"fill samples real drawing pixels rather than visible onion guides in an empty exposure")
	check(Drawing.cel_at(app.layers[1],8).is_empty() and not app.onion_editor.views[0].visible,"unapplied fill preview creates no cel and temporarily hides onion guides");app.fill_editor.cancel();app.tool.select(0);app.set_frame(18);await settled()
	var uploaded: int=app.onion_editor.uploads
	for i in range(30):await process_frame
	app.set_frame(19);await settled();check(app.onion_editor.uploads==uploaded,"idle frames and scrubbing inside a hold reuse both GPU textures")
	app.tool.select(0);app.color.color=Color.WHITE;click(Vector2(1100,700));await settled()
	check(app.onion_editor.uploads==uploaded,"painting the current cel does not reupload unchanged neighboring rasters")
	app.set_frame(0);click(Vector2(600,300));app.set_frame(18);await settled();uploaded=app.onion_editor.uploads
	app.undo();await settled();check(app.onion_editor.uploads==uploaded+1 and app.onion_editor.views[0].texture.get_image().get_data()==Drawing.image(app.layers[1].cels[0]).get_data(),"Undo of an earlier drawing invalidates only its ghost texture")
	app.redo();await settled();check(app.onion_editor.uploads==uploaded+2,"Redo refreshes the edited neighbor without rebuilding its peer")
	app.onion_editor.opacity.value=45;await settled();check(absf(app.onion_editor.views[0].material.get_shader_parameter("ghost_color").a-.45)<.001 and app.onion_editor.uploads==uploaded+2,"opacity updates shader uniforms without copying full-HD rasters")
	app.advanced_toggle.button_pressed=true;await settled();app.advanced_toggle.button_pressed=false;await settled();check(app.onion_editor.opacity.value==45 and not app.onion_editor.opacity.is_visible_in_tree(),"Advanced opacity persists when returning to Simple")
	app.layers[1].visible=false;app.changed();await settled();check(not app.onion_editor.views[0].visible and not app.onion_editor.views[1].visible,"hidden active layer has no onion silhouette");app.layers[1].visible=true;app.changed()
	app.active_layer=0;app.layer_choice.select(0);app.refresh_layer();await settled();check(not app.onion_editor.views[0].visible,"empty Rough never borrows Ink guides");app.active_layer=1;app.layer_choice.select(1);app.refresh_layer()
	app.mode.select(1);app.change_mode(1);await settled();check(not app.onion_editor.views[0].visible,"Scene navigation hides the drawing guides");app.mode.select(0);app.change_mode(0)
	app.set_frame(18);app.toggle_play();await settled();check(app.playing and not app.onion_editor.views[0].visible,"normal timeline playback hides guides");app.stop();app.set_frame(18)
	app.canvas.zoom=1.3;app.canvas.pan=Vector2(23,-11);await settled();check(app.onion_editor.views[0].rect==app.canvas.image_rect() and app.canvas.scene_background.rect==app.canvas.image_rect(),"background, ghosts and front drawing share the exact floating-point zoom/pan rectangle")
	var zoom_on: Image=root.get_texture().get_image();app.onion_editor.enabled.button_pressed=false;await settled();var zoom_off: Image=root.get_texture().get_image()
	check(sample(zoom_on,Vector2(470,370))!=sample(zoom_off,Vector2(470,370)) and sample(zoom_on,Vector2(970,570))==sample(zoom_off,Vector2(970,570)),"zoomed GPU guides move with their source pixels and stay beneath current ink");app.onion_editor.enabled.button_pressed=true
	var expected:=hashes();var packed:=folder.path_join("onion.has");app.has_project.save_file(packed,"packed");await job();var manual:=FileAccess.get_sha256(packed)
	app.new_project();await settled();check(not app.onion_editor.views[0].visible and not app.onion_editor.views[1].visible,"New immediately has no stale drawing texture")
	app.has_project.open_file(packed);await job();check(hashes()==expected and app.onion_editor.enabled.button_pressed,"packed HAS keeps exact cels while the guide toggle remains a personal session setting")
	app.mode.select(0);app.change_mode(0);await settled();check(app.onion_editor.views[0].texture.get_image().get_data()==Drawing.image(app.layers[1].cels[0]).get_data(),"freshly loaded images replace the old ghost-cache identities")
	app.changed();app.autosave_tick(true)
	while app.recovery_preview.busy():app.poll_recovery_preview();await process_frame
	var recovery: String=app.recovery_root.path_join(app.recovery_session);check(app.open_project(recovery) and hashes()==expected and FileAccess.get_sha256(packed)==manual,"recovery retains actual artwork and preserves the manual HAS")
	app.mode.select(0);app.change_mode(0);app.set_frame(18);var reference: Image=await app.renderer.capture(app.keys,app.layers,18,true);var error: String=await app.export_movie(folder)
	check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000019.png")).get_data()==reference.get_data(),"MP4 PNG matches reopened artwork exactly without onion guides")
	root.size=Vector2i(1200,760);app.mode.select(0);app.change_mode(0);await settled();root.get_texture().get_image().save_png(folder.path_join("onion-1200.png"));check(app.canvas.size.x>=500 and app.onion_editor.enabled.is_visible_in_tree(),"Simple onion toggle fits the actual1200pixel workspace")
	print("ONION_SMOKE "+JSON.stringify({"checks":checks,"failures":failures,"folder":folder,"project":packed,"movie":app.last_export_folder.path_join("movie.mp4"),"uploads":app.onion_editor.uploads}));app.free();quit(0 if failures==0 else 1)
