extends SceneTree
const Timeline=preload("res://src/timeline.gd")
const Drawing=preload("res://src/drawing.gd")
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(180).timeout.connect(func():push_error("Shape comparison watchdog");quit(2));call_deferred("run")
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func settled() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func wait_preview(comparison) -> void:
	while comparison.phase!=0:await process_frame
	await settled()
func choose(editor,name: String) -> bool:
	for row in editor.rows():
		var index: int=row.names.find(name)
		if index<0:continue
		editor.node_index=int(row.node);editor.shape_index=index;editor.area_filter.select(0);editor.rebuild();return true
	return false
func difference(a: Image,b: Image) -> int:
	if a==null or b==null or a.get_size()!=b.get_size():return -1
	var av:=a.get_data();var bv:=b.get_data();var changed:=0
	for i in range(av.size()):changed+=int(av[i]!=bv[i])
	return changed
func colored(image: Image) -> int:
	if image==null:return 0
	var data:=image.get_data();var result:=0
	for i in range(0,data.size(),4):
		if maxi(data[i],maxi(data[i+1],data[i+2]))-mini(data[i],mini(data[i+1],data[i+2]))>15:result+=1
	return result
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0]
	var plans: Array=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("plans.json")))
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled();app.autosave_enabled.button_pressed=false
	var results:=[]
	for plan in plans:
		app.new_project();app.set_advanced(true);var error: String=app.pose_editor.add_model(plan.source);var actor: RefCounted=app.renderer.active_model()
		check(error.is_empty() and actor!=null,"comparison imports standard model: "+plan.label)
		if not actor:continue
		actor.data.rotation_xyzw=plan.rotation;actor.apply(0,false,false,app.video)
		app.pose_editor.frame_model();app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,55)];app.set_frame(0)
		Drawing.insert(app.layers[1],0,48,Drawing.blank(1920,1080));Drawing.cel_at(app.layers[1],0).image.set_pixel(80,80,Color.CYAN)
		app.pose_editor.open_shapes();await settled();var editor=app.pose_editor.animated_shapes
		check(choose(editor,plan.control),"comparison resolves exact native control: "+plan.label)
		editor.amount.value=editor.amount.value+.125
		var pending_amount: float=editor.amount.value
		var before: Dictionary=actor.data.duplicate(true);var keys: Array=app.keys.duplicate(true);var history: int=app.history.size();var revision: int=app.recovery_revision
		var main_before: Image=await app.renderer.capture(app.keys,app.layers,0,true);var view: Dictionary=app.renderer.view_state()
		var comparison=editor.comparison;comparison.button.pressed.emit();await wait_preview(comparison)
		var ready: bool=comparison.before_image!=null and comparison.after_image!=null
		check(ready,"actual isolated before/after renders finish: "+plan.label)
		if not ready:
			print("COMPARISON_ERROR "+str(comparison.info.text));comparison.close();continue
		var changed:=difference(comparison.before_image,comparison.after_image)
		check(changed>30 and colored(comparison.before_image)>100 and colored(comparison.after_image)>100,"actual visible geometry changes in focused snapshots: "+plan.label)
		check(comparison.renderer.camera.transform==comparison.capture_camera,"before/after retain one exact camera: "+plan.label)
		check(actor.data==before and app.keys==keys and app.history.size()==history and app.recovery_revision==revision and app.renderer.view_state()==view and editor.dirty and editor.amount.value==pending_amount,"comparison preserves document, camera, history and pending amount: "+plan.label)
		var while_open: Image=await app.renderer.capture(app.keys,app.layers,0,true)
		check(while_open.get_data()==main_before.get_data() and Drawing.cel_at(app.layers[1],0).image.get_pixel(80,80)==Color.CYAN,"isolated preview never enters final scene or independent drawing: "+plan.label)
		comparison.before_image.save_png(folder.path_join(plan.id+"-before.png"));comparison.after_image.save_png(folder.path_join(plan.id+"-after.png"))
		if plan.id=="0":
			comparison.amount.value=0;await wait_preview(comparison);check(difference(comparison.before_image,comparison.after_image)==0,"zero test amount yields exact identical images")
			comparison.amount.value=-1;await wait_preview(comparison);check(difference(comparison.before_image,comparison.after_image)>30,"negative mathematical position test changes the isolated model")
			var direction: Vector3=comparison.direction;comparison.turn_left.pressed.emit();await wait_preview(comparison)
			check(comparison.direction!=direction and comparison.before_image!=null and comparison.after_image!=null,"turn controls rerender both sides from the same changed view")
			root.get_texture().get_image().save_png(folder.path_join("comparison-ui.png"))
		results.append({"label":plan.label,"control":plan.control,"changed_channels":changed,"focus_moved":comparison.focus.moved,"focus_bounds":str(comparison.focus.bounds)})
		comparison.close();await settled()
		check(not RenderingServer.frame_post_draw.is_connected(comparison.rendered) and comparison.renderer==null and comparison.window==null,"Close disconnects readback and frees isolated resources: "+plan.label)
		check(actor.data==before and app.renderer.view_state()==view and editor.dirty,"Close keeps exact source edits and view: "+plan.label)
		if plan.id=="0":
			comparison.open();comparison.close();await settled();check(comparison.window==null and comparison.renderer==null,"close before deferred import cannot install a stale preview")
			comparison.open();await process_frame;app.new_project();await settled();check(comparison.window==null and app.renderer.active_model()==null,"New cancels a pending comparison without touching the replacement scene")
	var result:={"checks":checks,"failures":failures,"models":results};FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("SHAPE_COMPARISON_APP "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
