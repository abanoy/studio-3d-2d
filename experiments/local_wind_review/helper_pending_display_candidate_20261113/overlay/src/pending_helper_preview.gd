extends Node
# Preview-only owner. Actual imported transfer precedes graphical admission.
# The graphical player owns only derived state; Apply remains a separate action.
const Bridge=preload("res://src/wind_helper_bridge.gd")
const Runtime=preload("res://src/wind_helper_runtime.gd")
const Adapter=preload("res://src/wind_helper_candidate.gd")
const Model=preload("res://src/model.gd")
const Player=preload("res://src/pending_helper_wind_player.gd")
var player: Node
var catalog: Dictionary={}
var wind_ids: Dictionary={}
var focused_group:=-1
var group_notice:=""
var selection_cache: Dictionary={}
var selection_cache_sha:=""
var candidate_prepared: Dictionary={}
var editor
var app
var phase:="stopped"
var epoch:=0
var bridge: Node
var candidate: RefCounted
var holder: Node3D
var hidden_space: SubViewport
var frozen_context: Dictionary={}
var frozen_shape: Dictionary={}
var frozen_pose: Dictionary={}
var source_actor: RefCounted
var source_root: WeakRef
var items: Array=[]
var last_error:=""
var last_receipt: Dictionary={}
var last_transport: Dictionary={}
var next_poll:=0
var run_mode:=""

class Admission extends RefCounted:
	var owner: WeakRef
	var token: int
	func run(source: RefCounted,path: String,shape: Dictionary,pose: Dictionary,video: Dictionary,operations: Array,sha: String) -> void:
		var keep_alive: RefCounted=self
		var result: Dictionary=await Adapter.prepare(source,path,shape,pose,video,operations,sha)
		var host=owner.get_ref()
		if not is_instance_valid(host) or not host.is_inside_tree() or host.epoch!=token:
			if result.has("model") and is_instance_valid(result.model.root):result.model.root.free()
			return
		host.admit(result)

func active() -> bool:return phase in ["starting","building","importing","prepared_hidden","warming","running"]

func _ready() -> void:
	player=Player.new();player.app=app;add_child(player);player.phase_changed.connect(player_phase);player.failed.connect(on_failed)

func display_active() -> bool:
	return is_instance_valid(player) and player.phase in ["warming","running"]

func player_phase(value: String) -> void:
	phase=value;refresh()

func target_idle(actor: RefCounted) -> bool:
	if not actor or not is_instance_valid(actor.root):return false
	var id: String=actor.data.id
	return not app.physics_editor.simulations.has(id) and not app.physics_editor.pending.has(id) and not app.physics_editor.recording.active

func reviewed() -> Dictionary:
	if not is_instance_valid(editor.window) or editor.pid>0 or editor.point_review_after>0:return {"error":"Wait for this part's review to finish."}
	var result: Array=[]
	if not editor.included.is_empty():
		for key in editor.included:
			var row: Dictionary=editor.included[key]
			if not row.get("valid",false):return {"error":"Review all included parts before trying wind."}
			var request: Dictionary=row.request.duplicate(true);request["reviewed"]=true;result.append(request)
		return {"items":result,"mode":"included-batch"}
	if not editor.preview_ready or not editor.preview.get("can_apply",false):return {"error":"Review a usable part before trying wind."}
	var request: Dictionary=editor.request.duplicate(true);request["reviewed"]=true
	return {"items":[request],"mode":"focused-single"}

static func digest(value) -> String:
	var hash:=HashingContext.new();hash.start(HashingContext.HASH_SHA256);hash.update(var_to_bytes(value));return hash.finish().hex_encode()

func pose(actor: RefCounted) -> Dictionary:
	var result: Dictionary={}
	for id in actor.order:
		var info: Dictionary=actor.bones[id];var current: Transform3D=info.skeleton.get_bone_pose(info.index)
		var p: Vector3=current.origin-info.base.origin
		var q: Quaternion=(info.base.basis.get_rotation_quaternion().inverse()*current.basis.get_rotation_quaternion()).normalized()
		result[id]={"position":[p.x,p.y,p.z],"rotation_xyzw":[q.x,q.y,q.z,q.w]}
	return result

func shape(actor: RefCounted) -> Dictionary:
	var overrides: Dictionary={}
	var snapshot: Dictionary=Model.Shape.snapshot(actor.root)
	for node in snapshot:
		var weights: Array=snapshot[node];var row: Dictionary={}
		for index in weights.size():row[str(index)]=weights[index]
		overrides[str(node)]=row
	return {"format":"studio_source_shape_2","enabled":false,"overrides":overrides}

func reviewed_shapes_match(actor: RefCounted,draft: Array) -> bool:
	# Requests contain the actual shape snapshot captured during geometric review.
	# Seeking can change evaluated shapes without changing document revision.
	var actual: Dictionary=Model.Shape.snapshot(actor.root)
	for item in draft:
		if item.get("source_morph_defaults",false)!=false or not item.get("morph_weights",{}) is Dictionary:return false
		var normalized: Dictionary={}
		for node in item.get("morph_weights",{}):
			var weights=item.morph_weights[node]
			if not weights is Array:return false
			var nonzero:=false
			for weight in weights:
				if not (weight is float or weight is int) or not is_finite(weight):return false
				nonzero=nonzero or weight!=0.
			if nonzero:normalized[str(node)]=weights
		if normalized!=actual:return false
	return true

func context(actor: RefCounted,draft: Array) -> Dictionary:
	var bindings: Dictionary={}
	for id in actor.order:
		var info: Dictionary=actor.bones[id]
		bindings[id]={"base":info.base,"index":info.index,"skeleton":info.skeleton.get_instance_id()}
	return {"actor_id":str(actor.data.id),"root_instance_id":str(actor.root.get_instance_id()),"revision":str(app.recovery_revision),"frame":str(app.frame),"authored_sha256":digest(actor.data),"shape_sha256":digest(shape(actor)),"bindings_sha256":digest([actor.root.get_meta("has_source_bones",{}),bindings,pose(actor),actor.root.global_transform,draft,app.video])}

func context_valid() -> bool:
	if not active() or not is_instance_valid(editor) or not is_instance_valid(editor.window) or not app.is_inside_tree():return false
	if not source_actor or source_root==null or not is_instance_valid(source_root.get_ref()) or source_actor.root!=source_root.get_ref():return false
	if editor.actor()!=source_actor or app.renderer.active_model()!=source_actor or not target_idle(source_actor):return false
	if app.renderer.capturing_final or app.playing or app.exporting or app.source_import.pid>0 or app.has_project.pid>0 or app.pose_editor.dragging or app.drawing:return false
	var current:=reviewed()
	if current.has("error") or current.mode!=run_mode or current.items!=items:return false
	if not reviewed_shapes_match(source_actor,items):return false
	if FileAccess.get_sha256(editor.source)!=source_actor.data.sha256:return false
	return context(source_actor,items)==frozen_context

func start() -> String:
	stop("Restarting")
	app.stop_local_wind("Another wind preview")
	var current: RefCounted=editor.actor()
	if not target_idle(current):return fail("Pause this model's Physics and Hair & clothes before trying this setup.")
	if app.renderer.capturing_final or app.playing or app.exporting or app.pose_editor.dragging or app.drawing or app.source_import.pid>0 or app.has_project.pid>0:return fail("Finish the current action before trying this setup.")
	var draft:=reviewed()
	if draft.has("error"):return fail(draft.error)
	if not reviewed_shapes_match(current,draft.items):return fail("The model's expression changed since this part was reviewed. Reopen review at this frame before trying it.")
	var config:=Runtime.configuration(app)
	if config.has("error"):return fail(config.error)
	items=draft.items.duplicate(true);run_mode=draft.mode;source_actor=current;source_root=weakref(current.root)
	frozen_pose=pose(current);frozen_shape=shape(current);frozen_context=context(current,items)
	epoch+=1;app.local_wind_generation+=1;phase="starting";last_error="";last_receipt={}
	bridge=Bridge.new();add_child(bridge);bridge.received.connect(received);bridge.failed.connect(on_failed)
	var error: String=bridge.launch(config)
	if not error.is_empty():return fail(error)
	refresh();return ""

func received(value: Dictionary) -> void:
	if not context_valid():stop("The scene or reviewed setup changed.");return
	match str(value.event):
		"ready":
			var error: String=bridge.send("start",{"source":editor.source,"items":items,"context":frozen_context,"mode":run_mode})
			if not error.is_empty():fail(error)
		"started","running":phase="building";next_poll=Time.get_ticks_msec()+75
		"prepared":
			var path: String=bridge.job.path_join("preview-receipt.json")
			if FileAccess.get_sha256(path)!=str(bridge.prepared_completion.get("receipt_sha256","")):fail("The prepared setup receipt changed.");return
			var file:=FileAccess.open(path,FileAccess.READ)
			var receipt=JSON.parse_string(file.get_as_text()) if file and file.get_length()<=4*1024*1024 else null
			if file:file.close()
			if not receipt is Dictionary or receipt.get("purpose")!="preview_only" or receipt.get("status")!="prepared_hidden" or receipt.get("context")!=frozen_context or receipt.get("managed_asset_created")!=false or receipt.get("authored_edit_created")!=false or receipt.get("render_admitted")!=false:fail("The prepared setup is not a temporary checked preview.");return
			if receipt.get("candidate",{}).get("path")!="candidate/scene.glb" or receipt.get("bindings",{}).get("path")!="bindings.json" or not receipt.get("operations") is Array:fail("The prepared setup paths changed.");return
			if FileAccess.get_sha256(bridge.job.path_join("bindings.json"))!=receipt.bindings.get("sha256"):fail("The prepared binding proof changed.");return
			var candidate_path: String=bridge.job.path_join("candidate/scene.glb")
			var sha: String=receipt.candidate.identity.get("sha256","")
			if sha.length()!=64 or FileAccess.get_sha256(candidate_path)!=sha:fail("The prepared model changed.");return
			last_receipt=receipt.duplicate(true);phase="importing"
			bridge.close_transport();last_transport={"releases":bridge.release_calls,"result":bridge.release_result,"completion":bridge.prepared_completion.duplicate(true)}
			var admission:=Admission.new();admission.owner=weakref(self);admission.token=epoch
			admission.run(source_actor,candidate_path,frozen_shape.duplicate(true),frozen_pose.duplicate(true),app.video.duplicate(true),receipt.operations.duplicate(true),sha)
		"refused","invalidated":fail(str(value.get("reason","This setup could not be prepared.")))
	refresh()

func admit(result: Dictionary) -> void:
	if result.has("error"):fail(result.error);return
	if not context_valid():
		if is_instance_valid(result.model.root):result.model.root.free()
		stop("The scene changed while preparing this setup.");return
	# A hidden Node3D alone does not isolate WorldEnvironment or current cameras.
	# Keep the admitted intermediate in its own nonrendering world as well.
	candidate=result.model;candidate_prepared=result.duplicate();catalog=result.catalog.duplicate(true);group_notice=result.get("notice","");wind_ids={}
	var default_ids: Array=result.selected_group_ids
	if selection_cache_sha==catalog.source_sha256:default_ids=selection_cache.keys()
	for group in catalog.groups:
		if group.id in default_ids:wind_ids[group.id]=true
	focused_group=0 if not catalog.groups.is_empty() else -1
	if DisplayServer.get_name()=="headless":park_candidate();phase="prepared_hidden";refresh()
	else:restart_wind()

func park_candidate() -> void:
	if not candidate or not is_instance_valid(candidate.root):return
	if candidate.root.get_parent():candidate.root.get_parent().remove_child(candidate.root)
	if not is_instance_valid(hidden_space):
		hidden_space=SubViewport.new();hidden_space.name="PendingHelperPrivateWorld";hidden_space.own_world_3d=true;hidden_space.render_target_update_mode=SubViewport.UPDATE_DISABLED;hidden_space.size=Vector2i(1,1);add_child(hidden_space)
		holder=Node3D.new();holder.name="PendingHelperHiddenHost";holder.visible=false;hidden_space.add_child(holder)
	candidate.root.visible=false;holder.add_child(candidate.root)

func restart_wind() -> void:
	if not candidate or not is_instance_valid(candidate.root) or not context_valid():return
	if DisplayServer.get_name()=="headless":refresh();return
	player.stop("Wind settings changed",false)
	if wind_ids.is_empty():park_candidate();phase="prepared_hidden";refresh();return
	var selected: Dictionary=candidate_prepared.duplicate();selected.selected_group_ids=wind_ids.keys()
	var error: String=player.start(source_actor,selected,Callable(self,"context_valid"),editor.wind_strength.value,editor.wind_direction.selected)
	if not error.is_empty():fail(error)

func group_label(group: Dictionary,index: int) -> String:
	var names: Array=[]
	for name in group.names:
		var text: String="Configured loose part" if str(name).begins_with("__HAS_") else str(name)
		if not text in names:names.append(text)
	return ", ".join(names).left(100)+" · group "+str(index+1)+(" (linked)" if group.linked else "")

func focus_group(index: int) -> void:
	if index<0 or index>=catalog.get("groups",[]).size():return
	focused_group=index;refresh()

func check_group(enabled: bool) -> void:
	if focused_group<0 or focused_group>=catalog.get("groups",[]).size():return
	var id: String=catalog.groups[focused_group].id
	if enabled:wind_ids[id]=true
	else:wind_ids.erase(id)
	selection_cache=wind_ids.duplicate();selection_cache_sha=catalog.source_sha256
	if editor.try_wind.button_pressed:restart_wind()
	refresh()

func settings_changed() -> void:
	if editor.try_wind.button_pressed:restart_wind()

func global_event(event: InputEvent) -> bool:
	if event is InputEventKey and event.pressed and event.keycode==KEY_ESCAPE and active():stop("Stopped");app.release_mouse();return true
	return is_instance_valid(player) and player.global_event(event)

func _process(_delta: float) -> void:
	if not active():return
	if not context_valid():stop("The scene or reviewed setup changed.");return
	if phase=="building" and is_instance_valid(bridge) and not bridge.outstanding and Time.get_ticks_msec()>=next_poll:
		var error: String=bridge.send("poll",{"context":frozen_context})
		if not error.is_empty():fail(error)

func on_failed(reason: String) -> void:fail(reason)
func fail(reason: String) -> String:
	stop(reason);last_error=reason;refresh();return reason

func refresh() -> void:
	if not is_instance_valid(editor):return
	if is_instance_valid(editor.try_wind):editor.try_wind.set_pressed_no_signal(phase in ["starting","building","importing","warming","running"] or DisplayServer.get_name()=="headless" and phase=="prepared_hidden")
	if is_instance_valid(editor.wind_status):editor.wind_status.text=last_error if not last_error.is_empty() else "Setup checked in a hidden preview; graphical review is separate." if DisplayServer.get_name()=="headless" and phase=="prepared_hidden" else str(wind_ids.size())+" motion groups checked · "+("local try-out running" if phase=="running" else "preparing" if active() and phase!="prepared_hidden" else "scene settings unchanged")
	if is_instance_valid(editor.wind_parts):
		if editor.wind_parts.item_count!=catalog.get("groups",[]).size():
			editor.wind_parts.clear()
			for i in catalog.get("groups",[]).size():editor.wind_parts.add_item(group_label(catalog.groups[i],i))
		for i in catalog.get("groups",[]).size():editor.wind_parts.set_item_text(i,("✓ " if wind_ids.has(catalog.groups[i].id) else "")+group_label(catalog.groups[i],i))
		if focused_group>=0:editor.wind_parts.select(focused_group)
	if is_instance_valid(editor.wind_check):
		editor.wind_check.disabled=focused_group<0
		editor.wind_check.set_pressed_no_signal(focused_group>=0 and wind_ids.has(catalog.groups[focused_group].id))
	if is_instance_valid(editor.wind_detail):
		editor.wind_detail.text="These checks only affect this temporary wind try-out. Include in setup still controls Apply."
		if focused_group>=0 and catalog.groups[focused_group].linked:editor.wind_detail.text+=" This linked group tries "+str(catalog.groups[focused_group].chain_indices.size())+" chains together; individual exclusion needs different weights."
		if not group_notice.is_empty():editor.wind_detail.text+=" "+group_notice

func stop(reason: String="Stopped") -> void:
	epoch+=1;phase="stopped"
	if not catalog.is_empty():selection_cache=wind_ids.duplicate();selection_cache_sha=catalog.source_sha256
	if is_instance_valid(player):player.stop(reason)
	if is_instance_valid(bridge):
		bridge.close_transport();last_transport={"releases":bridge.release_calls,"result":bridge.release_result,"completion":bridge.prepared_completion.duplicate(true)};bridge.queue_free()
	bridge=null
	if candidate and is_instance_valid(candidate.root):candidate.root.visible=false;candidate.root.free()
	candidate=null
	if is_instance_valid(holder):holder.free()
	if is_instance_valid(hidden_space):hidden_space.free()
	holder=null;hidden_space=null;source_actor=null;source_root=null;candidate_prepared={};catalog={};wind_ids={};focused_group=-1;group_notice=""
	if reason!="Restarting":last_error=reason
	refresh()

func _exit_tree() -> void:stop("Closed")
