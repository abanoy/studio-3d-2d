extends Node
# Explicit capture samples the shared physics proxies into ordinary editable pieces.
const Model=preload("res://src/model.gd")
const Clips=preload("res://src/animation_clips.gd")
const World=preload("res://src/world_document.gd")
const Contacts=preload("res://src/foot_contacts.gd")
var editor
var scope: OptionButton
var button: Button
var active:=false
var advancing:=false
var start_frame:=0
var last_frame:=0
var ticks:=0
var armed:=false
var targets:={}
var samples:={}
var previous:={}
var last_error:=""
var last_bytes:=0
var max_sample_ms:=0.0
var fps_num:=24
var fps_den:=1
var duration:=48
var static_bytes:=0
var sample_bytes:=0
var retained_keys:={}
var was_dirty:=false
var start_revision:=0
var last_end_reason:=""

func restore_dirty() -> void:
	var app=editor.app
	if app.recovery_revision!=start_revision:return
	for id in targets:
		var actor: RefCounted=app.renderer.world_runtime.instance(id) if app.renderer.world_runtime else app.renderer.model
		if not actor or actor.data!=targets[id]:return
	app.dirty=was_dirty

static func bytes(value) -> int:return JSON.stringify(value,"",true,true).to_utf8_buffer().size()

func pose_bytes(states: Dictionary) -> int:
	var size:=0
	for id in states:size+=bytes(states[id].pose)+bytes(states[id].transform)
	return size

func rebase(candidate: Dictionary) -> void:
	static_bytes=last_bytes-sample_bytes-pose_bytes(previous)
	retained_keys={}
	for id in candidate.values:
		var count:=0
		for piece in candidate.values[id].animation_clips:
			count+=piece.keys.size()+piece.get("shape_keys",[]).size()+piece.get("body_rest_keys",[]).size()
			for part in piece.get("body_controls",{}):count+=piece.body_controls[part].size()
			for part in piece.get("body_removed",{}):count+=piece.body_removed[part].size()
		for tracks in candidate.values[id].get("root_components",{}).values():
			for field in ["position","rotation_xyzw","scale"]:count+=tracks[field].size()
		retained_keys[id]=count-samples[id].size()*sample_controls(id)

func sample_controls(id: String) -> int:
	var count:=2 if Model.ShapeAnimation.independent(targets[id]) and not targets[id].shape_base.is_empty() else 1
	return count+3 if targets[id].get("format")=="studio_model_9" else count

func sample_cost(id: String,sample: Dictionary) -> int:
	var cost:=bytes(sample)
	if Model.ShapeAnimation.independent(targets[id]) and not targets[id].shape_base.is_empty():
		var body:=sample.duplicate();body.erase("shapes")
		cost=bytes(body)+bytes({"frame":sample.frame,"shapes":sample.shapes,"interpolation":sample.interpolation})+1
	if targets[id].get("format")=="studio_model_9":cost+=bytes(load("res://src/root_component_curves.gd").split([{"frame":sample.frame,"value":sample.transform,"interpolation":sample.interpolation}]))
	return cost

func setup(parent: Node) -> void:
	scope=OptionButton.new();scope.add_item("Local record");scope.add_item("World record");parent.add_child(scope)
	scope.item_selected.connect(func(_index):sync())
	scope.tooltip_text="Local captures only the selected live model. World captures all currently simulated models and props, including boxes they hit."
	button=Button.new();button.text="Record";button.focus_mode=Control.FOCUS_NONE;parent.add_child(button)
	button.pressed.connect(func():finish() if active else start())

func sync() -> void:
	if not is_instance_valid(button):return
	var app=editor.app
	button.text="Stop recording" if active else "Record"
	var reason: String="" if active else start_reason()
	button.disabled=app.exporting or not reason.is_empty()
	button.tooltip_text="Stop keeps the take. Escape discards it (release a grabbed body first)." if active else reason
	if not active and reason.is_empty():
		if scope.selected==0:button.tooltip_text="Record %s from frame %d." % [app.renderer.active_model().data.name,app.frame]
		else:button.tooltip_text="Record %d simulated objects from frame %d." % [editor.simulations.size(),app.frame]
		button.tooltip_text+=" Existing motion in the recorded range is replaced. Undo restores it."
	scope.disabled=active or app.exporting
	scope.set_item_text(0,"Local record")
	scope.set_item_text(1,"World record")
	if active and not targets.is_empty():
		var names:=PackedStringArray()
		for id in targets:names.append(str(targets[id].name))
		if scope.selected==0:scope.set_item_text(0,"Local · "+names[0].left(22))
		else:scope.set_item_text(1,"World · %d objects" % names.size())
		scope.tooltip_text="Recording from frame %d: %s" % [start_frame,", ".join(names)]
	else:
		scope.tooltip_text="Local captures the selected live model. World captures all currently simulated models and props."

func read_state(id: String) -> Dictionary:
	var simulation: RefCounted=editor.simulations[id]
	return {"pose":simulation.capture_pose() if simulation.has_method("capture_pose") else simulation.pose(),"transform":simulation.root_transform(editor.app.frame,false)}

func start_reason() -> String:
	var app=editor.app
	if not editor.is_running():return "Turn Physics on for a model or prop before recording."
	if app.frame>=app.video.duration_frames:return "Move to a frame before the project end to record physics."
	var actor: RefCounted=app.renderer.active_model()
	if scope.selected==0 and (not actor or not editor.active(actor.data.id)):
		return "Select a simulated object for Local recording, or choose World to record all simulated objects."
	return ""

func start() -> bool:
	var app=editor.app
	last_error="";last_end_reason="";last_bytes=0;max_sample_ms=0
	if active or app.exporting:return false
	var reason:=start_reason()
	if not reason.is_empty():app.message(reason);return false
	var actor: RefCounted=app.renderer.active_model()
	var ids: Array=editor.simulations.keys()
	if scope.selected==0:
		ids=[actor.data.id]
	app.stop();app.finish_stroke();app.pose_editor.finish_drag()
	if app.mode.selected==0:app.mode.select(1);app.change_mode(1)
	targets={};samples={};previous={};ticks=0;sample_bytes=0;armed=false;start_frame=app.frame;last_frame=start_frame
	fps_num=int(app.video.fps_num);fps_den=int(app.video.fps_den);duration=int(app.video.duration_frames)
	for id in ids:
		targets[id]=editor.simulations[id].rig.data.duplicate(true)
		previous[id]=read_state(id)
		samples[id]=[key(previous[id],start_frame)]
		if Model.ShapeAnimation.has_data(targets[id]):samples[id][0]["shapes"]=Model.ShapeAnimation.sample(targets[id],start_frame)
		sample_bytes+=sample_cost(id,samples[id][0])
	var candidate:=build(start_frame)
	if candidate.has("error"):last_error=candidate.error;targets.clear();samples.clear();previous.clear();app.message(last_error);sync();return false
	rebase(candidate)
	was_dirty=app.dirty;start_revision=app.recovery_revision
	active=true;app.dirty=true;sync()
	app.message(("Local" if scope.selected==0 else "World")+" recording: "+str(targets.size())+" model(s). Stop keeps the take; Escape discards it. Audio plays during recorded playback, not live capture.")
	return true

static func key(state: Dictionary, frame: int) -> Dictionary:
	return {"frame":frame,"pose":state.pose.duplicate(true),"transform":state.transform.duplicate(true),"interpolation":"linear"}

func _physics_process(_delta: float) -> void:
	if not active:return
	var app=editor.app;var began:=Time.get_ticks_usec()
	if int(app.video.fps_num)!=fps_num or int(app.video.fps_den)!=fps_den or int(app.video.duration_frames)!=duration:
		cancel("Recording cancelled because project timing changed. Your settings were kept.");return
	var current:={}
	for id in targets:
		if not editor.active(id):cancel("Recording cancelled: a captured body disappeared.");return
		current[id]=read_state(id)
	if not armed:
		# The first callback establishes fixed-tick zero. Node body transforms still
		# represent the completed previous step; don't count a step that hasn't run.
		armed=true
		static_bytes+=pose_bytes(current)-pose_bytes(previous)
		for id in targets:
			var first:=key(current[id],start_frame)
			if Model.ShapeAnimation.has_data(targets[id]):first["shapes"]=Model.ShapeAnimation.sample(targets[id],start_frame)
			sample_bytes+=sample_cost(id,first)-sample_cost(id,samples[id][0]);samples[id][0]=first
		previous=current
		return
	ticks+=1
	var numerator:=fps_num;var denominator:=fps_den*Engine.physics_ticks_per_second
	while last_frame<int(app.video.duration_frames) and (last_frame+1-start_frame)*denominator<=ticks*numerator:
		var next:=last_frame+1
		var fraction:=clampf(float((next-start_frame)*denominator-(ticks-1)*numerator)/numerator,0,1)
		for id in targets:
			var state:={"pose":Model.blend(previous[id].pose,current[id].pose,fraction),"transform":Model.blend_transform(previous[id].transform,current[id].transform,fraction)}
			var sample:=key(state,next)
			if Model.ShapeAnimation.has_data(targets[id]):sample["shapes"]=Model.ShapeAnimation.sample(targets[id],next)
			samples[id].append(sample);sample_bytes+=sample_cost(id,sample)+1
		last_frame=next
		advancing=true;app.set_frame(next);advancing=false
		# Count only the new samples on normal ticks. Rebuild the complete candidate
		# at a possible limit, or once on Stop, avoiding repeated whole-world copies.
		var at_limit:=static_bytes+sample_bytes+pose_bytes(current)>1024*1024
		for id in targets:at_limit=at_limit or retained_keys[id]+samples[id].size()*sample_controls(id)>Clips.MAX_TOTAL_KEYS
		if at_limit:
			var candidate:=build(last_frame)
			if candidate.has("error"):
				last_error=candidate.error;finish("limit");return
			var old_previous: Dictionary=previous;previous=current;rebase(candidate);previous=old_previous
		if last_frame>=int(app.video.duration_frames):finish("project end");return
	previous=current
	max_sample_ms=maxf(max_sample_ms,float(Time.get_ticks_usec()-began)/1000)

static func replace_range(data: Dictionary, keys: Array, first: int, last: int, duration: int, preserve_contacts:=false) -> Dictionary:
	keys=keys.duplicate(true)
	if Model.ShapeAnimation.has_data(data):
		for sample in keys:
			if not sample.has("shapes"):sample["shapes"]=Model.ShapeAnimation.sample(data,float(sample.frame))
	var result:=Clips.promote(data);var pieces: Array=[];var components: Dictionary={}
	for original in result.animation_clips:
		var end:=int(original.start)+int(original.length)
		if end<=first or original.start>last:
			pieces.append(original)
			if data.get("root_components",{}).has(original.id):components[original.id]=data.root_components[original.id].duplicate(true)
			continue
		if original.start<first:
			var left: Dictionary=original.duplicate(true);left.length=first-int(left.start);left.auto_extend=false;pieces.append(left)
			if Model.is_body(result):left["body_untrimmed"]=false
			if data.get("root_components",{}).has(original.id):components[left.id]=data.root_components[original.id].duplicate(true)
		if end>last+1:
			var right: Dictionary=original.duplicate(true);right.id=str(ResourceUID.create_id());right.start=last+1;right.source_in=int(original.source_in)+last+1-int(original.start);right.length=end-last-1;right.auto_extend=false;pieces.append(right)
			if Model.is_body(result):right["body_untrimmed"]=false
			if data.get("root_components",{}).has(original.id):components[right.id]=data.root_components[original.id].duplicate(true)
	var take:=Clips.clip(result,first,last-first+1,first,keys)
	if Model.is_body(data):
		var body=Model.body_animation();var prior_parts: Array=body.B.known_channels(body.view(data))
		body.prepare_take(data,take)
		var new_parts: Array=take.body_legacy_channels.filter(func(id):return not id in prior_parts)
		# A first captured value also holds backwards when no earlier piece owns
		# that part. Preserve the pre-take baseline explicitly, not an interpolation
		# from introduction to the already-fallen first simulation snapshot.
		var preceding: Dictionary={}
		for piece in pieces:
			if piece.start<first and (preceding.is_empty() or piece.start>preceding.start):preceding=piece
		if preceding.is_empty() and not new_parts.is_empty() and first>int(data.start_frame):
			preceding=Clips.clip(result,first-1,1,first-1,[])
			preceding.base_pose=data.body_base_pose.duplicate(true);preceding.base_transform=data.body_base_transform.duplicate(true)
			preceding["body_untrimmed"]=false;pieces.append(preceding)
		if not preceding.is_empty():
			for id in new_parts:
				var value: Dictionary=data.body_base_transform if id=="@root" else data.body_base_pose.get(id,Model.identity())
				preceding.body_controls[id]=[{"frame":int(preceding.source_in)+int(preceding.length)-1,"value":value.duplicate(true),"interpolation":"hold"}]
		# Newly captured parts must not hold the fallen pose through a retained
		# following block that never owned those parts (e.g. a contact-only tail).
		# Give only those new parts their original baseline at that block's entry.
		var following: Dictionary={}
		for piece in pieces:
			if piece.start>last and (following.is_empty() or piece.start<following.start):following=piece
		if not following.is_empty():
			for id in take.body_legacy_channels:
				if id in prior_parts:continue
				var value: Dictionary=data.body_base_transform if id=="@root" else data.body_base_pose.get(id,Model.identity())
				following.body_controls[id]=[{"frame":int(following.source_in),"value":value.duplicate(true),"interpolation":"hold"}]
	if preserve_contacts and Model.is_contact(data):
		take["foot_contacts"]=Contacts.slice(data.animation_clips,first,last+1,first)
	take.base_pose=keys[0].pose.duplicate(true);take.base_transform=keys[0].transform.duplicate(true)
	if Model.ShapeAnimation.has_data(data):take["base_shapes"]=keys[0].shapes.duplicate(true)
	if Model.ShapeAnimation.independent(data):
		take["shape_origin"]=first
		for i in range(take.keys.size()):
			if not keys[i].shapes.is_empty():take.shape_keys.append({"frame":keys[i].frame,"shapes":keys[i].shapes.duplicate(true),"interpolation":keys[i].interpolation})
			take.keys[i].erase("shapes")
	pieces.append(take);pieces.sort_custom(func(a,b):return a.start<b.start);result.animation_clips=pieces
	if data.get("format")=="studio_model_9":
		var root_keys:=[]
		for sample in keys:root_keys.append({"frame":sample.frame,"value":sample.transform,"interpolation":sample.interpolation})
		components[take.id]=load("res://src/root_component_curves.gd").split(root_keys)
		result.root_components=components
	result.start_frame=mini(int(data.get("start_frame",0)),first)
	result.presence_offset=maxi(0,int(result.start_frame)-int(pieces[0].start))
	var final: Dictionary=keys[-1]
	result.pose=final.pose.duplicate(true);result.position=final.transform.position.duplicate();result.rotation_xyzw=final.transform.rotation_xyzw.duplicate();result.scale=final.transform.scale;result.draft_frame=last
	if Model.ShapeAnimation.has_data(data):result.shape_pose=final.shapes.duplicate(true)
	if Model.ShapeAnimation.independent(data):result.shape_draft_frame=last
	var error: String=load("res://src/root_component_document.gd").validate(result,duration) if result.get("format")=="studio_model_9" else Model.validate(result,duration)
	return {"error":error} if not error.is_empty() else {"data":result}

func build(end: int) -> Dictionary:
	var app=editor.app;var values:={}
	for id in targets:
		if not editor.active(id):return {"error":"A captured model is no longer simulated."}
		if editor.simulations[id].rig.data!=targets[id]:return {"error":"Authored model data changed during recording. The take was not installed; your edits were kept."}
		var keys: Array=samples[id].filter(func(k):return k.frame<=end)
		var result:=replace_range(targets[id],keys,start_frame,end,int(app.video.duration_frames),not editor.body_active(id))
		if result.has("error"):return result
		values[id]=result.data
	var world: Dictionary=app.renderer.world_state()
	if not world.is_empty():
		for i in range(world.objects.size()):
			if values.has(world.objects[i].id):world.objects[i]=values[world.objects[i].id]
		var error:=World.validate(world,int(app.video.duration_frames))
		if not error.is_empty():return {"error":error}
	# Include real scene/shot/audio/layer names and conservative cel/path overhead.
	var layer_info: Array=[]
	for layer in app.layers:
		var cels: Array=[]
		for cel in layer.cels:cels.append({"id":cel.id,"start":cel.start,"duration":cel.duration,"path":"cels/"+"0".repeat(128+str(cel.id).length())+".png","pixel_sha256":"0".repeat(64)})
		layer_info.append({"id":layer.id,"name":layer.name,"visible":layer.visible,"cels":cels})
		if layer.has("opacity"):layer_info[-1].opacity=layer.opacity
	var audio: Dictionary=preload("res://src/audio_track.gd").metadata(app.audio_document())
	last_bytes=bytes({"world":World.portable(world) if not world.is_empty() else values,"video":app.video,"camera_keys":app.keys,"layers":layer_info,"audio":audio,"editor":{"frame":end}})+8192
	if last_bytes>1024*1024:return {"error":"Recording reached the1MiB project metadata limit. Use fewer recorded models or a shorter take."}
	return {"values":values}

func release_all() -> void:
	editor.release_grab()
	for simulation in editor.simulations.values():simulation.dispose()
	editor.simulations.clear();editor.clear_colliders();editor.clear_previews();editor.sync()

func finish(reason: String="explicit stop") -> bool:
	if not active:return true
	last_end_reason=reason
	var app=editor.app;var end:=last_frame;var result:=build(end)
	# Keep the longest valid sampled prefix if the current take reaches a budget.
	while result.has("error") and end>start_frame and ("limit" in str(result.error) or "exceed" in str(result.error)):
		last_error=result.error;end-=1;result=build(end)
	active=false
	if result.has("error"):
		last_error=result.error;restore_dirty();release_all();app.pose_editor.apply_frame();sync();app.message(last_error);return false
	var before: Dictionary=targets.duplicate(true)
	release_all()
	if app.renderer.world_runtime:
		var error: String=app.renderer.world_runtime.restore_instances(result.values)
		if not error.is_empty():last_error=error;app.pose_editor.apply_frame();sync();app.message(error);return false
		app.push_history({"type":"world_objects","before":before,"after":result.values.duplicate(true)})
	else:
		var id: String=result.values.keys()[0];app.renderer.model.data=result.values[id]
		app.push_history({"type":"model","before":before[id],"after":result.values[id].duplicate(true)})
	app.changed();advancing=true;app.set_frame(end);advancing=false;sync()
	app.message("Recorded frames %d–%d for %d model(s). Physics is off; the take is editable and Undo restores it." % [start_frame,end,targets.size()]+(" "+last_error+" Later motion was not saved." if not last_error.is_empty() else ""))
	return true

func cancel(reason: String="Recording discarded; authored animation is unchanged.", restore_frame:=true) -> void:
	if not active:return
	active=false;last_end_reason=reason;restore_dirty();release_all();samples.clear();targets.clear();previous.clear();sync()
	if restore_frame and editor.app.is_inside_tree():editor.app.set_frame(start_frame);editor.app.message(reason)

func _exit_tree() -> void:
	# Parent PhysicsEditor disposes proxies. Avoid rebuilding UI/reading a renderer
	# during tree teardown; quitting already passed the app's unsaved-work prompt.
	active=false
