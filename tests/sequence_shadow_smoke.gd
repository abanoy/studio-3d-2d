extends SceneTree
const Drawing=preload("res://src/drawing.gd")
const Graph=preload("res://src/sequence_graph.gd")
const Recovery=preload("res://src/recovery.gd")
const Storage=preload("res://src/storage.gd")
var app
var editor
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(140).timeout.connect(func():push_error("Sequence shadow watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settle() -> void:
	for i in range(5):await process_frame
	await RenderingServer.frame_post_draw
func job() -> void:
	while app.has_project.pid>0:await process_frame
	await settle()
func picture() -> Image:return await editor.runtime.render("",0,true)
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0]
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache");editor=app.sequence_editor
	if "--read" in args:
		for name in ["Shadow packed.has","Shadow linked.has"]:
			app.has_project.open_file(folder.path_join(name));await job()
			check(editor.graph.get("format")==Graph.SHADOW_FORMAT and not editor.graph.clips[0].shadow.is_empty(),"cold HAS restores explicit versioned shadow: "+name)
			var image: Image=await picture();check(absf(image.get_pixel(970,450).a-.125)<.015 and image.get_pixel(850,450).r>.99,"cold reopened shadow preserves translucent alpha and original ink")
		check(app.restore_checkpoint({"folder":folder.path_join("shadow-recovery/test"),"manifest":"project.json","recovery":true}),"ordinary recovery restores style graph and source assets")
		var image: Image=await picture();check(absf(image.get_pixel(970,450).a-.125)<.015,"recovered style reproduces shadow pixels")
		print("SEQUENCE_SHADOW_READ ",JSON.stringify({"checks":checks,"failures":failures}));await app.quit_studio();quit(0 if failures==0 else 1);return
	check(app.load_demo_room(),"original procedural parent background loads")
	var parent: Dictionary=app.current_world().duplicate(true);var shots: Array=app.keys.duplicate(true)
	var id: String=editor.new_sequence("Shadow artwork");check(not id.is_empty() and editor.enter(id).is_empty(),"create actual editable child for compositing")
	app.mode.select(0);app.change_mode(0);app.active_layer=1;app.refresh_layer();app.create_cel(false)
	var cel: Dictionary=app.layers[1].cels[0];cel.duration=48;Drawing.image(cel).fill_rect(Rect2i(800,400,100,100),Color(1,0,0,.5));Drawing.touch(Drawing.image(cel));app.changed();var pixels: PackedByteArray=Drawing.image(cel).get_data()
	editor.return_to_parent();await settle();var clip: Dictionary=editor.graph.clips[0]
	var keys: Array=clip.keys.duplicate(true);keys[0].opacity=.5;check(editor.change_clip(clip.id,{"keys":keys}).is_empty(),"placement opacity stays independent of source artwork")
	var before: Image=await picture();check(before.get_pixel(970,450).a==0 and absf(before.get_pixel(850,450).a-.25)<.015,"legacy graph has no shadow and correct source alpha")
	var history: int=app.history.size();check(editor.change_shadow(clip.id,{}).is_empty() and editor.graph.format==Graph.FORMAT and app.history.size()==history,"disabled shadow no-op preserves old graph and history")
	var style:={"offset":[120,0],"color":[0,0,0,.5],"softness":0}
	check(editor.change_shadow(clip.id,style).is_empty() and editor.graph.format==Graph.SHADOW_FORMAT,"applying shadow explicitly promotes graph and fills clip styles")
	var shadowed: Image=await picture();var shadow:=shadowed.get_pixel(970,450)
	check(shadow.r<.01 and shadow.g<.01 and shadow.b<.01 and absf(shadow.a-.125)<.015,"actual shadow multiplies source alpha, style opacity and placement opacity once")
	check(shadowed.get_pixel(850,450)==before.get_pixel(850,450) and Drawing.image(cel).get_data()==pixels,"shadow leaves source picture and editable source pixels unchanged")
	shadowed.save_png(folder.path_join("hard-shadow.png"))
	app.undo();await settle();var undone: Image=await picture();check(editor.graph.format==Graph.FORMAT and undone.get_data()==before.get_data(),"one Undo restores old graph version and exact original pixels")
	app.redo();await settle();var redone: Image=await picture();check(redone.get_data()==shadowed.get_data(),"Redo restores shadow without flattening the child")
	style.softness=16;check(editor.change_shadow(clip.id,style).is_empty(),"bounded soft shadow prepares mip-filtered silhouette")
	var soft: Image=await picture();var edge:=soft.get_pixel(919,450)
	check(edge.a>0 and edge.a<.125 and absf(soft.get_pixel(970,450).a-.125)<.02,"softness feathers outside silhouette while retaining interior opacity")
	soft.save_png(folder.path_join("soft-shadow.png"))
	var graph: Dictionary=editor.clone_graph();var why: String=editor.change_shadow(clip.id,{"offset":[2049,0],"color":[0,0,0,.5],"softness":4})
	check(not why.is_empty() and editor.graph==graph,"invalid shadow edit refuses atomically")
	editor.show_panel();await settle();var toggle: CheckButton
	for node in editor.panel.find_children("","CheckButton",true,false):
		if node.text=="Drop shadow":toggle=node
	check(toggle!=null and toggle.button_pressed,"real sequence browser exposes enabled shadow review")
	if toggle:toggle.button_pressed=false
	for button in editor.panel.find_children("","Button",true,false):
		if button.text=="Apply shadow":button.pressed.emit();break
	await settle();var disabled: Image=await picture();check(editor.graph.clips[0].shadow.is_empty() and disabled.get_data()==before.get_data(),"actual Apply shadow control disables effect and restores exact image")
	editor.close_panel()
	var precise:={"offset":[120.001,0.002],"color":[.123456789,.2,.3,.5123456789],"softness":4.123456789}
	editor.change_shadow(clip.id,precise);editor.show_panel();await settle();history=app.history.size()
	for button in editor.panel.find_children("","Button",true,false):
		if button.text=="Apply shadow":button.pressed.emit();break
	await settle();check(editor.graph.clips[0].shadow==precise and app.history.size()==history,"unchanged inspector retains exact saved fractional style without adding history")
	editor.close_panel();style.softness=0;editor.change_shadow(clip.id,style);await settle()
	var extra: String=editor.new_sequence("No shadow");check(not extra.is_empty() and editor.graph.clips[-1].shadow=={},"new sequence in promoted project receives explicit disabled style")
	editor.remove_clip(editor.graph.clips[-1].id);editor.remove_asset(extra)
	check(editor.copy_clip(clip.id).is_empty() and editor.paste_clip().is_empty() and editor.graph.clips[-1].shadow==style,"copy/paste retains independent shadow parameters")
	editor.remove_clip(editor.graph.clips[-1].id)
	check(app.current_world()==parent and app.keys==shots and Drawing.image(cel).get_data()==pixels,"all style operations preserve parent world, camera and child source pixels")
	for mode in ["packed","linked"]:
		app.has_project.save_file(folder.path_join("Shadow "+mode+".has"),mode);await job();check(FileAccess.file_exists(folder.path_join("Shadow "+mode+".has")),"ordinary "+mode+" HAS saves style and editable child")
	var snapshot: Dictionary=app.project_snapshot();var error:=Recovery.checkpoint(folder.path_join("shadow-recovery"),"test",snapshot.video,snapshot.camera_keys,snapshot.layers,"",0,snapshot.audio,"",app.recovery_revision,{},snapshot.world,snapshot.palette,snapshot.sequence_graph)
	check(error.is_empty(),"normal recovery writer saves shadow graph without mutating manual HAS")
	var composite: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	var movie_error: String=await app.export_movie(folder);var movie: String=app.last_export_folder.path_join("movie.mp4")
	check(movie_error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000001.png")).get_data()==composite.get_data(),"real MP4 uses exact shadow and parent composite input")
	print("SEQUENCE_SHADOW_SMOKE ",JSON.stringify({"checks":checks,"failures":failures,"movie":movie}));await app.quit_studio();quit(0 if failures==0 else 1)
