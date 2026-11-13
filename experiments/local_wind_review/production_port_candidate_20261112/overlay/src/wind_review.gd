extends Node
# Session-only local wind. The source actor and its physics remain borrowed,
# read-only inputs; all simulation state belongs to the disposable candidate.
const Model=preload("res://src/model.gd")
const Groups=preload("res://src/wind_review_groups.gd")
const Spring=preload("res://src/secondary_spring.gd")
const Secondary=preload("res://src/secondary_live.gd")
const Airflow=preload("res://src/airflow.gd")
const Definition=preload("res://src/secondary_rig.gd")
var app
var button: Button
var window: Window
var parts: ItemList
var wind_check: CheckButton
var master: CheckButton
var strength: SpinBox
var direction: OptionButton
var status: Label
var detail: Label
var target_id:=""
var root_id:=0
var source_sha:=""
var source_modified:=0
var revision:=-1
var opened_frame:=-1
var original_data: Dictionary={}
var catalog: Dictionary={}
var focused:=-1
var wind_ids: Dictionary={}
var changing:=false
var phase:="stopped"
var settling:=0
var candidate: RefCounted
var simulation: RefCounted
var private_space: SubViewport
var hidden: Dictionary={}
var previous_pointer:=Callable()
var pointer_pending:=false
var wind_direction:=Vector3.LEFT
var catalogue_notice:=""

func setup(parent: Node) -> void:
	process_physics_priority=10
	button=app.button(parent,"Review local wind…",open)
	button.tooltip_text="Try wind on checked declared hair/clothing groups in the main view. Scene settings and animation remain unchanged."
	app.renderer.before_final_capture=Callable(self,"stop_for_capture")
	app.renderer.before_asset_replace=Callable(self,"stop_for_asset")
	app.renderer.assets_changed.connect(close)

func actor() -> RefCounted:
	return app.renderer.world_runtime.instance(target_id) if app.renderer.world_runtime else app.renderer.model

func available() -> bool:
	var current: RefCounted=app.renderer.active_model()
	return current!=null and not app.renderer.capturing_final and not app.playing and not app.exporting and not app.physics_editor.recording.active and not app.pose_editor.dragging and not app.drawing and app.source_import.pid<=0 and app.has_project.pid<=0 and not is_instance_valid(app.physics_editor.helper_editor.window) and current.root.get_meta("has_secondary_rig",{}).get("error","").is_empty() and not current.root.get_meta("has_secondary_rig",{}).get("chains",[]).is_empty()

func context_valid() -> bool:
	var source: RefCounted=actor()
	return is_instance_valid(window) and window.visible and app.is_inside_tree() and source!=null and source==app.renderer.active_model() and is_instance_valid(source.root) and source.root.get_instance_id()==root_id and source.data.sha256==source_sha and FileAccess.get_modified_time(source.data.source)==source_modified and source.data==original_data and source.root.get_meta("has_secondary_rig",{})==catalog.get("definition",{}) and app.recovery_revision==revision and app.frame==opened_frame and not app.renderer.capturing_final and not app.playing and not app.exporting and not app.physics_editor.recording.active

func other_roots(source: RefCounted) -> Array:
	var result: Array=[]
	if app.renderer.world_runtime:
		for current in app.renderer.world_runtime.instances.values():
			if current!=source:result.append(current.root)
	return result

func open() -> void:
	if is_instance_valid(window) or not available():return
	var source: RefCounted=app.renderer.active_model();target_id=source.data.id;root_id=source.root.get_instance_id();source_sha=source.data.sha256;revision=app.recovery_revision;opened_frame=app.frame;original_data=source.data.duplicate(true)
	if FileAccess.get_sha256(source.data.source)!=source_sha:return
	source_modified=FileAccess.get_modified_time(source.data.source)
	var definition: Dictionary=source.root.get_meta("has_secondary_rig",{});var parent_ids:=Groups.parents(source)
	var linked:=Groups.vertex_links(source,definition.chains,parent_ids,other_roots(source));var links: Array=linked.get("links",[]);catalogue_notice=""
	if not linked.get("error","").is_empty():
		# Unknown weights cannot support a promise of independent exclusion.
		for i in range(1,definition.chains.size()):links.append([0,i])
		catalogue_notice="These joints are linked for this try-out because the weights could not be separated safely."
	catalog=Groups.build(definition,source_sha,parent_ids,links)
	if not catalog.get("error","").is_empty():app.message(catalog.error);return
	wind_ids.clear();focused=-1
	window=Window.new();window.title="Try local wind";window.theme=app.theme;window.close_requested.connect(close);window.window_input.connect(window_input);app.add_child(window)
	var panel:=PanelContainer.new();window.add_child(panel);panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var column:=VBoxContainer.new();panel.add_child(column)
	app.label(column,"Choose which motion groups to try. Clicking a row changes the focus; checks stay separate.").autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	parts=ItemList.new();parts.custom_minimum_size=Vector2(410,150);column.add_child(parts);parts.item_selected.connect(focus_group);parts.gui_input.connect(list_input)
	for i in range(catalog.groups.size()):parts.add_item(group_label(catalog.groups[i],i))
	wind_check=CheckButton.new();wind_check.text="Try wind on this group";wind_check.toggled.connect(check_group);column.add_child(wind_check)
	detail=app.label(column,"");detail.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	var options:=HBoxContainer.new();column.add_child(options);app.label(options,"Strength")
	strength=SpinBox.new();strength.min_value=0;strength.max_value=50;strength.step=1;strength.value=6;options.add_child(strength);strength.value_changed.connect(func(_value):restart())
	direction=OptionButton.new();options.add_child(direction)
	for label in ["From right","From left","From front","From behind"]:direction.add_item(label)
	direction.item_selected.connect(func(_index):restart())
	master=CheckButton.new();master.text="Try a local blow";master.toggled.connect(change_preview);column.add_child(master)
	status=app.label(column,"");status.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	app.button(column,"Close",close)
	window.popup_centered(Vector2i(450,460));window.position+=Vector2i(maxi(0,int((app.get_viewport_rect().size.x-window.size.x)/2)-12),0)
	if not catalog.groups.is_empty():parts.select(0);focus_group(0)
	refresh()

func group_label(group: Dictionary,index: int) -> String:
	var names: Array=[]
	for name in group.names:
		var value: String=str(name)
		if value.begins_with("__HAS_"):value="Configured loose part"
		if not value in names:names.append(value)
	return ", ".join(names).left(100)+" · group "+str(index+1)+(" (linked)" if group.linked else "")

func focus_group(index: int) -> void:
	if index<0 or index>=catalog.get("groups",[]).size():return
	focused=index;refresh()

func check_group(enabled: bool) -> void:
	if changing or focused<0:return
	var id: String=catalog.groups[focused].id
	if enabled:wind_ids[id]=true
	else:wind_ids.erase(id)
	refresh();restart()

func list_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and event.keycode==KEY_SPACE and parts.has_focus() and not app.navigating and focused>=0:
		wind_check.button_pressed=not wind_check.button_pressed;parts.accept_event()

func refresh() -> void:
	if not is_instance_valid(window):return
	changing=true;wind_check.set_pressed_no_signal(focused>=0 and wind_ids.has(catalog.groups[focused].id));changing=false
	wind_check.disabled=focused<0;master.disabled=wind_ids.is_empty()
	for i in range(catalog.groups.size()):parts.set_item_text(i,("✓ " if wind_ids.has(catalog.groups[i].id) else "")+group_label(catalog.groups[i],i))
	detail.text="This linked group tries "+str(catalog.groups[focused].chain_indices.size())+" chains together. Weighted regions and descendant joints can move together; individual surface exclusion needs different weights." if focused>=0 and catalog.groups[focused].linked else "One declared joint chain. Its weighted regions move together; recorded motion is kept."
	if not catalogue_notice.is_empty():detail.text+=" "+catalogue_notice
	status.text=str(wind_ids.size())+" motion group"+("s" if wind_ids.size()!=1 else "")+" checked · "+("preparing" if phase=="warming" else "local try-out running" if phase=="running" else "scene settings unchanged")

func change_preview(enabled: bool) -> void:
	if changing:return
	if enabled:begin_preview()
	else:stop_preview("Stopped")

func restart() -> void:
	if not is_instance_valid(master) or not master.button_pressed:return
	stop_preview("Restarting",false)
	if wind_ids.is_empty():master.set_pressed_no_signal(false);refresh();return
	begin_preview()

func body_ids(source: RefCounted) -> Dictionary:
	var simulation=app.physics_editor.simulations.get(source.data.id)
	if simulation is Secondary:simulation=simulation.primary
	return simulation.bodies if simulation else {}

func baseline_pose(source: RefCounted) -> Dictionary:
	var result: Dictionary={};var authored: Dictionary=source.sample(app.frame,app.mode.selected==2);var driven:=body_ids(source);var rotating_ids:={}
	for chain in catalog.definition.chains:
		for joint in Groups.rotating(chain):rotating_ids[joint.binding.id]=true
	for id in source.order:
		var info: Dictionary=source.bones[id];var current: Transform3D=info.skeleton.get_bone_pose(info.index);var p: Vector3=current.origin-info.base.origin;var q: Quaternion=(info.base.basis.get_rotation_quaternion().inverse()*current.basis.get_rotation_quaternion()).normalized()
		result[id]={"position":[p.x,p.y,p.z],"rotation_xyzw":[q.x,q.y,q.z,q.w]}
		# Never bake original live hair offsets into the try-out's rest pose.
		if rotating_ids.has(id) and not driven.has(id):result[id]=authored.get(id,Model.identity()).duplicate(true)
	return result

func shape_snapshot(source: RefCounted) -> Dictionary:
	var overrides:={};var snapshot: Dictionary=Model.Shape.snapshot(source.root)
	for node in snapshot:
		var weights: Array=snapshot[node];var values:={}
		for i in range(weights.size()):values[str(i)]=weights[i]
		overrides[str(node)]=values
	return {"format":"studio_source_shape_2","enabled":false,"overrides":overrides}

func begin_preview() -> void:
	if not context_valid() or wind_ids.is_empty():stop_preview("Review no longer matches this model");return
	var source: RefCounted=actor();var filtered:=Groups.filter(catalog,wind_ids.keys())
	if not filtered.get("error","").is_empty():fail(filtered.error);return
	var driven:=body_ids(source)
	for chain in filtered.chains:
		for joint in Groups.rotating(chain):
			if driven.has(joint.binding.id):fail("This group also drives a body joint. Pause this model's body Physics before trying it.");return
	if FileAccess.get_sha256(source.data.source)!=source_sha:fail("The model source changed. Open wind review again.");return
	var data:=Model.definition(source.data.source);data.pose=baseline_pose(source);data.draft_frame=app.frame;data.metadata={"source_shape":shape_snapshot(source)}
	if data.sha256!=source_sha:fail("The model source changed. Open wind review again.");return
	var prepared: Dictionary=app.renderer.prepare_model(data,app.video)
	if prepared.has("error"):fail(prepared.error);return
	if FileAccess.get_sha256(source.data.source)!=source_sha:prepared.model.root.free();fail("The model source changed during preparation.");return
	# A queued recovery frame must stay invalid even if this try-out stops before
	# native-frame dispatch. Mark the interval before any temporary mesh is visible.
	app.local_wind_generation+=1
	candidate=prepared.model;app.renderer.world.add_child(candidate.root);app.renderer.disable_cameras(candidate.root)
	candidate.live_pose=data.pose.duplicate(true);candidate.live_world_transform=source.root.global_transform;candidate.apply(app.frame,false,false,app.video,source.evaluated_opacity)
	private_space=SubViewport.new();private_space.name="LocalWindPrivateSpace";private_space.own_world_3d=true;private_space.render_target_update_mode=SubViewport.UPDATE_DISABLED;add_child(private_space)
	var result:=Spring.construct(candidate,filtered,private_space)
	if result.has("error"):fail(result.error);return
	simulation=Secondary.new();simulation.rig=candidate;simulation.runner=result.runner;simulation.initial_pose=data.pose.duplicate(true);simulation.latest=data.pose.duplicate(true);simulation.initial_world=source.root.global_transform
	var camera: Camera3D=app.renderer.camera
	wind_direction=([-camera.global_basis.x,camera.global_basis.x,-camera.global_basis.z,camera.global_basis.z][direction.selected] as Vector3).normalized()
	for mesh in Groups.mesh_nodes(source.root,other_roots(source)):hidden[mesh]=mesh.visible;mesh.visible=false
	previous_pointer=app.canvas.review_pointer;app.canvas.review_pointer=Callable(self,"pointer")
	app.canvas.pose_lines=[];app.canvas.pose_joints=[];app.canvas.queue_redraw()
	phase="warming";settling=2;schedule_warmup();refresh()

func schedule_warmup() -> void:
	if RenderingServer.frame_post_draw.is_connected(warm_frame):RenderingServer.frame_post_draw.disconnect(warm_frame)
	RenderingServer.frame_post_draw.connect(warm_frame,CONNECT_ONE_SHOT)

func warm_frame() -> void:
	if RenderingServer.frame_post_draw.is_connected(warm_frame):RenderingServer.frame_post_draw.disconnect(warm_frame)
	if not context_valid() or not candidate or not is_instance_valid(candidate.root):stop_preview("Cancelled");return
	settling-=1
	if settling>0:schedule_warmup();return
	phase="running";simulation.start();refresh()

func local_field() -> Dictionary:
	var center:=Vector3.ZERO;var count:=0;var radius:=.5
	for chain in simulation.runner.chains:center+=Definition.binding_transform(candidate,chain.source.joints[0].binding).origin;count+=1
	center/=maxi(count,1)
	for chain in simulation.runner.chains:radius=maxf(radius,center.distance_to(Definition.binding_transform(candidate,chain.source.joints[0].binding).origin)+.5)
	return {"transform":Transform3D(Basis(Quaternion(Vector3.BACK,wind_direction)),center-wind_direction*1.5-Vector3(0,.85,0)),"settings":{"format":Airflow.FORMAT,"enabled":true,"speed":strength.value,"radius":minf(radius,1000.),"reach":6.}}

func _physics_process(delta: float) -> void:
	if phase!="running":return
	if not context_valid():stop_preview("Review changed");return
	var source: RefCounted=actor();simulation.initial_pose=baseline_pose(source);simulation.initial_world=source.root.global_transform
	var error: String=simulation.advance(minf(delta,1./60.),app.frame,float(app.frame),false,[local_field()],null)
	if not error.is_empty():fail(error)

func _process(_delta: float) -> void:
	if not is_instance_valid(button):return
	button.disabled=not available() or is_instance_valid(window)
	if is_instance_valid(window) and not context_valid():close()

func pointer(event: InputEventMouse,point: Vector2) -> bool:
	if phase not in ["warming","running"]:return false
	if not pointer_pending and not app.canvas.scene_contains(point):return false
	if event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_LEFT and (not event.ctrl_pressed or pointer_pending):
		if event.pressed:pointer_pending=true;app.canvas.grab_focus();app.world_selection.input(event,point)
		elif pointer_pending:
			pointer_pending=false
			if app.navigating:app.world_selection.input(event,point)
			else:app.world_selection.cancel_gesture(true)
		return true
	if pointer_pending:app.world_selection.input(event,point);return true
	return false

func global_event(event: InputEvent) -> bool:
	if event is InputEventKey and event.pressed and event.keycode==KEY_ESCAPE and is_instance_valid(window):
		if phase!="stopped":stop_preview("Stopped")
		else:close()
		app.release_mouse()
		return true
	if pointer_pending and event is InputEventMouse:
		var local: Vector2=app.canvas.get_global_transform_with_canvas().affine_inverse()*event.position
		var rect: Rect2=app.canvas.image_rect()
		return pointer(event,(local-rect.position)/rect.size*Vector2(app.video.width,app.video.height))
	return false

func window_input(event: InputEvent) -> void:
	if global_event(event):window.set_input_as_handled()

func stop_for_capture() -> void:stop_preview("Final render")
func stop_for_asset() -> void:stop_preview("Asset replacement")

func stop_preview(_reason: String="Stopped",uncheck:=true) -> void:
	if RenderingServer.frame_post_draw.is_connected(warm_frame):RenderingServer.frame_post_draw.disconnect(warm_frame)
	phase="stopped";settling=0
	if pointer_pending and is_instance_valid(app.world_selection):app.world_selection.cancel_gesture(true)
	pointer_pending=false
	if is_instance_valid(app.canvas) and app.canvas.review_pointer==Callable(self,"pointer"):app.canvas.review_pointer=previous_pointer
	previous_pointer=Callable()
	if simulation:simulation.dispose();simulation=null
	if candidate and is_instance_valid(candidate.root):candidate.root.visible=false;candidate.root.queue_free()
	candidate=null
	if is_instance_valid(private_space):private_space.world_3d=null;private_space.queue_free()
	private_space=null
	for mesh in hidden:
		if is_instance_valid(mesh):mesh.visible=hidden[mesh]
	hidden.clear()
	if is_instance_valid(master) and uncheck:master.set_pressed_no_signal(false)
	if app.is_inside_tree() and is_instance_valid(app.pose_editor):app.pose_editor.update_gizmo()
	refresh()

func fail(message: String) -> void:
	stop_preview(message)
	if is_instance_valid(status):status.text=message

func close() -> void:
	stop_preview("Closed")
	if is_instance_valid(window):window.hide();window.queue_free()
	window=null;wind_ids.clear();catalog={};focused=-1

func _exit_tree() -> void:
	if is_instance_valid(app.renderer) and app.renderer.before_final_capture==Callable(self,"stop_for_capture"):app.renderer.before_final_capture=Callable()
	if is_instance_valid(app.renderer) and app.renderer.before_asset_replace==Callable(self,"stop_for_asset"):app.renderer.before_asset_replace=Callable()
	close()
