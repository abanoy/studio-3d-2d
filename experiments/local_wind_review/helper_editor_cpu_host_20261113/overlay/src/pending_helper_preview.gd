extends Node
# Preview-only owner. This first increment ends at a hidden, transferred model;
# display/spring execution is deliberately not admitted by this CPU-host gate.
const Bridge=preload("res://src/wind_helper_bridge.gd")
const Runtime=preload("res://src/wind_helper_runtime.gd")
const Adapter=preload("res://src/wind_helper_candidate.gd")
const Model=preload("res://src/model.gd")
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

func active() -> bool:return phase in ["starting","building","importing","prepared_hidden"]

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
	if app.playing or app.exporting or app.source_import.pid>0 or app.has_project.pid>0 or app.pose_editor.dragging or app.drawing:return false
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
	if app.playing or app.exporting or app.pose_editor.dragging or app.drawing or app.source_import.pid>0 or app.has_project.pid>0:return fail("Finish the current action before trying this setup.")
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
	candidate=result.model
	hidden_space=SubViewport.new();hidden_space.name="PendingHelperPrivateWorld";hidden_space.own_world_3d=true;hidden_space.render_target_update_mode=SubViewport.UPDATE_DISABLED;hidden_space.size=Vector2i(1,1);add_child(hidden_space)
	holder=Node3D.new();holder.name="PendingHelperHiddenHost";holder.visible=false;hidden_space.add_child(holder);holder.add_child(candidate.root)
	phase="prepared_hidden";refresh()

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
	if is_instance_valid(editor) and is_instance_valid(editor.try_wind):editor.try_wind.set_pressed_no_signal(active())
	if is_instance_valid(editor) and is_instance_valid(editor.wind_status):editor.wind_status.text=last_error if not last_error.is_empty() else "Setup checked in a hidden preview. Display review is pending." if phase=="prepared_hidden" else "Preparing a temporary setup…" if active() else "Try the reviewed setup before Apply."

func stop(reason: String="Stopped") -> void:
	epoch+=1;phase="stopped"
	if is_instance_valid(bridge):
		bridge.close_transport();last_transport={"releases":bridge.release_calls,"result":bridge.release_result,"completion":bridge.prepared_completion.duplicate(true)};bridge.queue_free()
	bridge=null
	if candidate and is_instance_valid(candidate.root):candidate.root.visible=false;candidate.root.free()
	candidate=null
	if is_instance_valid(holder):holder.free()
	if is_instance_valid(hidden_space):hidden_space.free()
	holder=null;hidden_space=null;source_actor=null;source_root=null
	if reason!="Restarting":last_error=reason
	refresh()

func _exit_tree() -> void:stop("Closed")
