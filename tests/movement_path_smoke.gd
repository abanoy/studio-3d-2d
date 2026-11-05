extends SceneTree
const PathData=preload("res://src/movement_path.gd")
const Model=PathData.Model
var app
var checks:=0
var failures:=0
var folder: String
func _initialize() -> void:
	create_timer(90).timeout.connect(func():push_error("Movement path watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS "if ok else"FAIL ")+label)
	if not ok:failures+=1
func settled() -> void:
	for n in range(5):await process_frame
	await RenderingServer.frame_post_draw
func event_at(control: Control,local: Vector2,event: InputEvent) -> void:
	var viewport:=control.get_viewport();var point: Vector2=control.get_global_transform_with_canvas()*local
	while viewport is Window and viewport.is_embedded():
		point+=Vector2(viewport.position);viewport=viewport.get_parent().get_viewport()
	event.position=point;viewport.push_input(event,true)
func click(control: Control) -> void:
	for down in [true,false]:
		var e:=InputEventMouseButton.new();e.button_index=MOUSE_BUTTON_LEFT;e.pressed=down;event_at(control,control.size/2,e);await process_frame
	await settled()
func click_at(control: Control,point: Vector2) -> void:
	for down in [true,false]:
		var e:=InputEventMouseButton.new();e.button_index=MOUSE_BUTTON_LEFT;e.pressed=down;event_at(control,point,e);await process_frame
	await settled()
func drag(plot: Control,point: Vector2,delta: Vector2) -> void:
	var press:=InputEventMouseButton.new();press.button_index=MOUSE_BUTTON_LEFT;press.pressed=true;event_at(plot,point,press);await process_frame
	var motion:=InputEventMouseMotion.new();motion.button_mask=MOUSE_BUTTON_MASK_LEFT;motion.relative=delta;event_at(plot,point+delta,motion);await process_frame
	var release:=InputEventMouseButton.new();release.button_index=MOUSE_BUTTON_LEFT;event_at(plot,point+delta,release);await settled()
func wait_job() -> void:
	while app.has_project.pid>0:await process_frame
	await settled()
func run() -> void:
	folder=OS.get_cmdline_user_args()[0];app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false
	var source:=folder.path_join("limb.glb");check(preload("res://tests/limb_fixture.gd").create(source)==OK,"authored skinned fixture exports")
	var placement: Dictionary=app.import_actions.placement();placement.physics_on_import=false
	check(app.pose_editor.add_model(source,0,placement).is_empty(),"ordinary model import succeeds")
	var rig: RefCounted=app.renderer.active_model();var data: Dictionary=rig.data.duplicate(true)
	var components: bool="--components" in OS.get_cmdline_user_args()
	for at in [0,48]:
		var transform:=Model.identity();transform["scale"]=1.;transform.position=[float(at)/24.,0,0]
		transform.scale=1.+float(at)/240.;var q:=Quaternion(Vector3.UP,float(at)/48.);transform.rotation_xyzw=[q.x,q.y,q.z,q.w]
		data.pose_keys.append({"frame":at,"pose":{},"transform":transform,"interpolation":"ease"})
	if components:data=PathData.Components.promote(data,48).data
	check(app.pose_editor.restore_state(data).is_empty(),"standard model accepts authored root movement")
	app.mode.select(2);app.change_mode(2);app.set_frame(24);app.set_advanced(false);await settled();var before: Dictionary=rig.data.duplicate(true);var history: int=app.history.size();var shots: Array=app.keys.duplicate(true)
	var editor=app.pose_editor.movement_path;app.inspector_scroll.ensure_control_visible(editor.button);await settled();await click(editor.button)
	check(is_instance_valid(editor.window)and editor.window.visible and not editor.window.exclusive,"Simple button opens modeless path editor")
	if not is_instance_valid(editor.window):quit(1);return
	check(editor.window.get_visible_rect().encloses(editor.apply_button.get_global_rect()),"Apply stays fully visible")
	check(editor.plot.size.x>500 and editor.plot.pixels>1,"path fits a laid out drawing area")
	await click(editor.add_button);check(PathData.controls(editor.draft).size()==3 and rig.data==before and app.history.size()==history,"Add stages a point without changing scene or Undo")
	var initial: Vector3=PathData.controls(editor.draft)[1].position;var plot: Control=editor.plot;var delta:=Vector2(35,-21);var expected:=initial+Vector3(delta.x/plot.pixels,0,delta.y/plot.pixels)
	await drag(plot,plot.screen(initial)+Vector2(5,4),delta)
	var moved: Vector3=PathData.controls(editor.draft)[1].position
	check(moved.distance_to(expected)<.00001 and moved.y==initial.y,"routed Top drag changes X/Z and preserves Y")
	plot.view=1;plot.fit();await settled();initial=moved;delta=Vector2(14,-28);expected=initial+Vector3(delta.x/plot.pixels,-delta.y/plot.pixels,0);await drag(plot,plot.screen(initial),delta);moved=PathData.controls(editor.draft)[1].position
	check(moved.distance_to(expected)<.00001 and moved.z==initial.z,"routed Front drag changes X/Y and preserves Z")
	plot.view=2;plot.fit();await settled();initial=moved;delta=Vector2(14,-14);expected=initial+Vector3(0,-delta.y/plot.pixels,delta.x/plot.pixels);await drag(plot,plot.screen(initial),delta);moved=PathData.controls(editor.draft)[1].position
	check(moved.distance_to(expected)<.00001 and moved.x==initial.x,"routed Side drag changes Z/Y and preserves X")
	var draft: Dictionary=editor.draft.duplicate(true);editor.window.get_texture().get_image().save_png(folder.path_join("path-panel.png"));await click(editor.apply_button)
	check(not is_instance_valid(editor.window)and rig.data==draft and app.history.size()==history+1,"Apply commits complete path with one Undo")
	check(app.keys==shots,"path editing preserves explicit camera keys")
	var prior:=Model.new();prior.data=before;var exact:=true
	for half in range(97):
		var a:=prior.sample_authored_transform(float(half)/2.);var b: Dictionary=rig.sample_authored_transform(float(half)/2.);exact=exact and a.rotation_xyzw==b.rotation_xyzw and a.scale==b.scale
	check(exact and rig.data.format=="studio_model_9","ordinary component path edits preserve animated turn/scale")
	var timeline=app.timeline
	await click_at(timeline,Vector2(9,timeline.row_y(0)+12))
	check(timeline.visual_rows.size()==2 and timeline.channel_y(rig.data.id,"@root")>=0,"Simple shows a single combined movement row")
	app.set_advanced(true);await settled()
	check(timeline.visual_rows.size()==4 and timeline.channel_y(rig.data.id,"@root/position")>=0 and timeline.channel_y(rig.data.id,"@root/rotation_xyzw")>=0 and timeline.channel_y(rig.data.id,"@root/scale")>=0,"Advanced reveals independent position rotation and scale rows")
	app.pose_editor.operation.select(0)
	await click_at(timeline,Vector2(timeline.x(24),timeline.channel_y(rig.data.id,"@root/position")+12))
	check(app.pose_editor.selected=="@root" and app.pose_editor.operation.selected==1 and timeline.selected_channel=="@root/position" and app.frame==24,"position row selects Move and its exact frame")
	app.pose_editor.operation.select(1)
	await click_at(timeline,Vector2(timeline.x(0),timeline.channel_y(rig.data.id,"@root/rotation_xyzw")+12))
	check(app.pose_editor.operation.selected==0 and timeline.selected_channel=="@root/rotation_xyzw","rotation row selects Rotate")
	await click_at(timeline,Vector2(timeline.x(0),timeline.channel_y(rig.data.id,"@root/scale")+12))
	check(timeline.selected_channel=="@root/scale" and app.inspector_scroll.get_global_rect().encloses(app.pose_editor.scale_field.get_global_rect()),"scale row exposes its numeric control")
	app.set_advanced(false);await settled()
	check(timeline.visual_rows.size()==2 and timeline.selected_channel=="@root" and rig.data==draft and app.history.size()==history+1 and app.keys==shots,"Simple Advanced inspection preserves model keys camera and history")
	await click_at(timeline,Vector2(9,timeline.row_y(0)+12))
	app.set_frame(24);app.inspector_scroll.ensure_control_visible(editor.button);await settled()
	app.undo();await settled();check(rig.data==before,"Undo restores exact previous model")
	app.redo();await settled();check(rig.data==draft,"Redo restores exact edited path")
	await click(editor.button);editor.frame.value=32;await click(editor.add_button);check(editor.draft!=draft,"Cancel test stages a genuinely new movement point");editor.close();check(rig.data==draft,"Cancel leaves committed movement intact")
	await click(editor.button);app.set_advanced(true);await settled();check(editor.window.visible,"changing UI detail leaves modeless editor usable")
	editor.close();app.set_advanced(false);app.set_frame(0);await settled();app.inspector_scroll.ensure_control_visible(editor.button);await settled();await click(editor.button)
	check(is_instance_valid(editor.window),"frame-zero path button remains accessible")
	if not is_instance_valid(editor.window):quit(1);return
	var zero: Vector3=PathData.controls(editor.draft)[0].position
	await drag(editor.plot,editor.plot.screen(zero),Vector2(20,-12));await click(editor.apply_button)
	check(rig.sample_authored_transform(0,true)==rig.sample_authored_transform(0,false) and rig.sample_authored_transform(0,true).position!=[0.,0.,0.],"frame-zero drag displays the committed curve immediately")
	await click(editor.button);editor.frame.value=0;await click(editor.remove_button);await click(editor.apply_button)
	check(rig.sample_authored_transform(0,true)==rig.sample_authored_transform(0,false),"frame-zero deletion displays resampled movement immediately")
	app.undo();app.undo();await settled();check(rig.data==draft,"Undo of frame-zero edits restores the complete prior path")
	editor.close();app.pose_editor.frame_model();app.keys=[Model.Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,60)]
	app.mode.select(0);app.change_mode(0);app.set_frame(0);app.create_cel(false)
	var ink=preload("res://src/drawing.gd");ink.stroke(ink.cel_at(app.layers[1],0).image,Vector2(80,80),Vector2(180,80),5,Color.CYAN,false);app.changed();app.set_frame(24)
	var picture: Image=await app.renderer.capture(app.keys,app.layers,24,true);picture.save_png(folder.path_join("reference.png"))
	var packed:=folder.path_join("path.has");app.has_project.cache_root=folder.path_join("cache");app.has_project.save_file(packed,"packed");await wait_job();check(app.has_project.path==packed,"ordinary packed HAS saves movement controls")
	app.new_project();app.has_project.open_file(packed);await wait_job();app.world_selection.select_entity(draft.id);rig=app.renderer.active_model()
	check(PathData.controls(rig.data)==PathData.controls(draft),"ordinary Open restores editable movement points")
	check(rig.data.format=="studio_model_9","ordinary HAS Open retains component model version")
	var reopened: Image=await app.renderer.capture(app.keys,app.layers,24,true);check(picture.get_data()==reopened.get_data(),"reopened movement and independent ink repeat exact picture")
	var error: String=await app.export_movie(folder);check(error.is_empty()and picture.get_data()==Image.load_from_file(app.last_export_folder.path_join("frame_000025.png")).get_data(),"MP4 export frame matches edited path preview")
	var movie: String=app.last_export_folder.path_join("movie.mp4");app.mode.select(2);app.change_mode(2);app.world_selection.select_entity(rig.data.id);await settled();app.inspector_scroll.ensure_control_visible(editor.button);await settled();await click(editor.button)
	app.new_project();await settled();check(not is_instance_valid(editor.window) or editor.apply_button.disabled and not editor.plot.enabled,"New closes or disables stale path editing")
	editor.close();app.dirty=false;app.queue_free();await settled();var result:={"checks":checks,"failures":failures,"movie":movie};var file:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close();print("MOVEMENT_PATH "+JSON.stringify(result));quit(0 if failures==0 else 1)
