extends SceneTree
const Catalog=preload("res://src/shape_catalog.gd")
const Model=preload("res://src/model.gd")
const Shape=Model.Shape
const Timeline=Model.Timeline
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(180).timeout.connect(func():push_error("Shape catalogue watchdog");quit(2));call_deferred("run")
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func settled() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func wait_job(job) -> void:
	while job.pid>0:await process_frame
	await settled()
func choose(editor,target: int) -> bool:
	for i in range(editor.shapes.item_count):
		if int(editor.shapes.get_item_metadata(i))==target:editor.shapes.select(i);editor.shapes.item_selected.emit(i);return true
	return false
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0]
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled()
	app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("has-cache")
	if args.size()>1:
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
		app.has_project.open_file(folder.path_join("catalogue-packed.has"));await wait_job(app.has_project);var actor: RefCounted=app.renderer.world_runtime.instance(expected.id)
		check(actor!=null,"cold engine opens catalogue project")
		if actor:
			var entry:=Catalog.lookup(actor.data,int(expected.node),int(expected.target),expected.native_name)
			check(entry.manual and entry.area=="Mouth" and entry.label=="Artist mouth","cold Open retains manual category and label")
			check(actor.data.metadata==expected.metadata,"cold Open retains exact native and catalogue metadata")
			var keys: Array=JSON.parse_string(JSON.stringify(actor.authored_shape_keys(),"",true,true))
			check(keys==expected.keys,"cold Open retains every authored shape value at full precision")
			app.set_frame(12);await settled();var image: Image=await app.renderer.capture(app.keys,app.layers,12,true);image.save_png(folder.path_join("cold.png"))
			var a:=image.get_data();var b:=Image.load_from_file(folder.path_join("middle.png")).get_data();var changed:=0;var total:=0
			for i in range(mini(a.size(),b.size())):
				var d:=absi(int(a[i])-int(b[i]));total+=d
				if d>0:changed+=1
			check(a.size()==b.size() and changed<=384 and float(total)/maxi(a.size(),1)<=.002,"cold render preserves the saved expression within native mesh-edge bound")
		var result:={"checks":checks,"failures":failures};FileAccess.open(folder.path_join("reader-result.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("SHAPE_CATALOG_READER "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1);return
	var plans: Array=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("catalogue-plans.json")))
	var native_results:=[];var selected_node:=-1;var selected_target:=-1;var native_name:=""
	for plan in plans:
		app.new_project();app.set_advanced(false);var error: String=app.pose_editor.add_model(plan.source);var actor: RefCounted=app.renderer.active_model()
		check(error.is_empty() and actor!=null,"catalogue imports standard asset: "+plan.label)
		if not actor:continue
		app.pose_editor.frame_model();app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,55)];app.set_frame(0);await settled()
		app.pose_editor.open_shapes();await settled();var editor=app.pose_editor.animated_shapes;editor.area_filter.select(0);editor.rebuild()
		var current: Dictionary=editor.row();check(not current.is_empty() and editor.shapes.item_count==current.names.size(),"All areas keeps every target and exact binding: "+plan.label)
		if current.is_empty():continue
		if plan.label=="SFM":
			var lid: int=current.names.find("CloseLidUpL");var compound: int=current.names.find("BrowOutV_CloseLidUpL")
			editor.area_filter.select(Catalog.AREAS.find("Eyes")+1);editor.rebuild()
			check(lid>=0 and choose(editor,lid),"actual Scout eyelid appears in Eyes after CamelCase parsing")
			await settled();root.get_texture().get_image().save_png(folder.path_join("scout-eyes-filter.png"))
			editor.area_filter.select(Catalog.AREAS.find("Brows")+1);editor.rebuild()
			check(not choose(editor,lid),"actual Scout eyelid is absent from Brows")
			editor.area_filter.select(Catalog.AREAS.find("Other")+1);editor.rebuild()
			check(compound>=0 and choose(editor,compound),"actual mixed brow-eyelid stays available in Other")
			editor.area_filter.select(0);editor.rebuild()
		selected_node=int(current.node);selected_target=0;native_name=str(current.names[0]);choose(editor,selected_target)
		var all_ids:=[]
		for i in range(editor.shapes.item_count):all_ids.append(editor.shapes.get_item_metadata(i))
		editor.area_filter.select(Catalog.AREAS.find("Eyes")+1);editor.area_filter.item_selected.emit(editor.area_filter.selected)
		var exact_filter:=true
		for i in range(editor.shapes.item_count):
			var target:=int(editor.shapes.get_item_metadata(i));exact_filter=exact_filter and target in all_ids and Catalog.lookup(actor.data,selected_node,target,current.names[target]).area=="Eyes"
		check(exact_filter,"Eyes filter uses estimates without renumbering targets: "+plan.label)
		editor.area_filter.select(0);editor.rebuild();choose(editor,selected_target)
		check(not editor.organize.is_visible_in_tree(),"Simple keeps manual catalogue details hidden: "+plan.label)
		var before: Dictionary=actor.data.duplicate(true);var neutral: Image=await app.renderer.capture(app.keys,app.layers,0,true)
		app.set_advanced(true);await settled();editor.assigned_area.select(Catalog.AREAS.find("Mouth"));editor.assigned_label.text="Artist mouth";await settled()
		check(editor.assigned_label.text=="Artist mouth" and editor.assigned_area.selected==Catalog.AREAS.find("Mouth"),"ordinary UI refresh preserves pending naming input: "+plan.label)
		var history: int=app.history.size();editor.assign_button.pressed.emit();await settled()
		var assigned: Dictionary=actor.data.duplicate(true);var unrelated:=assigned.duplicate(true);unrelated.metadata=before.metadata
		var entry:=Catalog.lookup(actor.data,selected_node,selected_target,native_name)
		check(entry.manual and entry.area=="Mouth" and entry.label=="Artist mouth" and app.history.size()==history+1,"manual classification is one saved Undo action: "+plan.label)
		check(unrelated==before and editor.shape_index==selected_target,"classification preserves every animation/root field and selected target: "+plan.label)
		var image: Image=await app.renderer.capture(app.keys,app.layers,0,true)
		check(image.get_data()==neutral.get_data(),"organizing does not change visible deformation: "+plan.label)
		check(editor.shapes.get_item_text(editor.shapes.get_selected_items()[0])==native_name,"Advanced retains the exact internal shape name: "+plan.label)
		app.set_advanced(false);await settled();choose(editor,selected_target)
		check(editor.shapes.get_item_text(editor.shapes.get_selected_items()[0])=="Artist mouth","Simple uses the chosen friendly name: "+plan.label)
		editor.search.text="Artist mouth";editor.search.text_changed.emit(editor.search.text)
		check(editor.shapes.item_count==1 and int(editor.shapes.get_item_metadata(0))==selected_target,"friendly-name search retains original identity: "+plan.label)
		editor.search.text="";editor.search.text_changed.emit("");choose(editor,selected_target)
		app.undo();await settled();check(actor.data==before,"Undo restores exact original control data: "+plan.label)
		app.redo();await settled();check(actor.data==assigned,"Redo restores only the intended assignment: "+plan.label)
		app.set_advanced(true);await settled();choose(editor,selected_target);editor.estimate_button.pressed.emit();await settled()
		check(actor.data==before,"Use estimate again removes only the manual assignment: "+plan.label)
		app.undo();await settled();choose(editor,selected_target)
		var guard: Dictionary=actor.data.duplicate(true);editor.amount.value=editor.amount.value+.123;editor.assign_control()
		check(actor.data==guard and editor.dirty,"organizing defers an unapplied amount without consuming it: "+plan.label)
		editor.load_amount();app.set_advanced(false);await settled();native_results.append(plan.label)
	var actor: RefCounted=app.renderer.active_model();var editor=app.pose_editor.animated_shapes;var id: String=actor.data.id
	app.set_frame(12);choose(editor,selected_target);editor.amount.value=.42;editor.apply_button.pressed.emit();await settled()
	check(absf(float(Shape.snapshot(actor.root)[str(selected_node)][selected_target])-.42)<.00001,"categorized target still edits its actual animated amount")
	app.pose_editor.shape_window.hide();var saved_metadata: Dictionary=actor.data.metadata.duplicate(true);var saved_keys: Array=actor.authored_shape_keys().duplicate(true)
	for mode in ["packed","linked"]:
		app.has_project.save_file(folder.path_join("catalogue-"+mode+".has"),mode);await wait_job(app.has_project);app.new_project();app.has_project.open_file(folder.path_join("catalogue-"+mode+".has"));await wait_job(app.has_project)
		actor=app.renderer.world_runtime.instance(id);app.set_frame(12);await settled();var entry:=Catalog.lookup(actor.data,selected_node,selected_target,native_name)
		check(entry.manual and entry.label=="Artist mouth" and actor.data.metadata==saved_metadata and actor.authored_shape_keys()==saved_keys,"classification and actual animation survive "+mode+" HAS")
	var preview: Image=await app.renderer.capture(app.keys,app.layers,12,true);preview.save_png(folder.path_join("middle.png"))
	var export_error: String=await app.export_movie(folder);var movie: String=app.last_export_folder.path_join("movie.mp4")
	check(export_error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000013.png")).get_data()==preview.get_data(),"catalogue metadata leaves normal movie pixels exact")
	var expected:={"id":id,"node":selected_node,"target":selected_target,"native_name":native_name,"metadata":saved_metadata,"keys":saved_keys};FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify(expected,"",true,true))
	var result:={"checks":checks,"failures":failures,"plans":native_results,"movie":movie};FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("SHAPE_CATALOG_APP "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
