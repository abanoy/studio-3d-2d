extends RefCounted
# Versioned intent; generated poses are never serialized over authored controls.
const Evaluator=preload("res://src/path_locomotion.gd")
const FORMAT="studio_path_walking_1"
const ASSIST_FORMAT="studio_motion_assist_4"
static func defaults() -> Dictionary:return {"format":FORMAT,"enabled":false,"stride":.36,"lift":.08,"lowering":.03,"amount":1.}
static func error(value) -> String:
	if not value is Dictionary or value.size()!=6 or value.get("format")!=FORMAT or not value.get("enabled") is bool:return "Invalid walking suggestion settings."
	for field in ["stride","lift","lowering","amount"]:
		if not value.has(field):return "Incomplete walking suggestion settings."
	var why:=Evaluator.settings_error({"stride":value.stride,"lift":value.lift,"lowering":value.lowering})
	if not why.is_empty():return why
	var amount=value.amount
	return "" if (amount is int or amount is float) and is_finite(float(amount)) and amount>=0 and amount<=1 else "Walking amount must be between0 and1."
static func active(data: Dictionary) -> bool:
	var value=data.get("motion_assist",{})
	return value is Dictionary and value.get("enabled",false)==true and value.get("walking",{}) is Dictionary and value.get("walking",{}).get("enabled",false)==true and not data.get("animation_clips",[]).is_empty()
static func corrections(data: Dictionary) -> Dictionary:
	var value: Dictionary=data.get("motion_assist",{}).get("walking",defaults())
	return {"stride":value.stride,"lift":value.lift,"lowering":value.lowering}
static func configure(data: Dictionary,on: bool,values: Dictionary,duration: int) -> Dictionary:
	var value: Dictionary=data.get("motion_assist",{}).get("walking",defaults()).duplicate(true)
	var prior_error:=error(value)
	if not prior_error.is_empty():return {"error":prior_error}
	for field in values:
		if not field in ["stride","lift","lowering","amount"]:return {"error":"Unknown walking correction."}
		value[field]=values[field]
	value.enabled=on
	var why:=error(value)
	if not why.is_empty():return {"error":why}
	var motion=load("res://src/motion_animation.gd");var promoted:=Evaluator.Paths.Components.promote(data,duration)
	if promoted.has("error"):return promoted
	var old: Dictionary=data.get("motion_assist",{});var was_on: bool=old.get("enabled",false);var strengths: Dictionary=old.get("part_strengths",{}).duplicate(true)
	# Enabling walking must not also add previously disabled arm/body helpers.
	if on and not was_on:
		for id in motion.parts(promoted.data):strengths[id]=0.
	var changed: Dictionary=motion.configure(promoted.data,on or was_on,1. if on and not was_on else float(old.get("strength",.65)),duration,strengths,old.get("track_helper_edits",{}))
	if changed.has("error"):return changed
	var setting: Dictionary=changed.data.motion_assist;setting.format=ASSIST_FORMAT;setting["part_strengths"]=strengths;setting["track_helper_edits"]=old.get("track_helper_edits",{}).duplicate(true);setting["walking"]=value
	why=Evaluator.Model.validate(changed.data,duration)
	return changed if why.is_empty() else {"error":why}
static func binding_error(actor: RefCounted,data: Dictionary,video: Dictionary) -> String:
	if not active(data):return ""
	if data.get("format")!="studio_model_9":return "Walking needs independent movement-path controls. Apply a path first."
	var plan:=Evaluator.new()
	return plan.build(actor,data,video,corrections(data)) if actor.root.is_inside_tree() else plan._build(actor,data,video,corrections(data),true)
static func preflight_detached(node: Node3D,actors: Array,video: Dictionary) -> String:
	var selected: Array=actors.filter(func(actor):return active(actor.data))
	if selected.is_empty():return ""
	if node.get_parent()!=null:return "Walking preparation needs a detached candidate."
	var tree=Engine.get_main_loop()
	if not tree is SceneTree:return "Walking preparation needs an active scene tree."
	# A non-rendering private 3D world cannot register imported cameras on the
	# installed viewport. The old world remains untouched until all poses pass.
	var stage:=SubViewport.new();stage.size=Vector2i.ONE;stage.own_world_3d=true;stage.render_target_update_mode=SubViewport.UPDATE_DISABLED;tree.root.add_child(stage);stage.add_child(node)
	var why:=""
	for actor in selected:
		var plan:=Evaluator.new();why=plan.build(actor,actor.data,video,corrections(actor.data))
		if not why.is_empty():break
	stage.remove_child(node);stage.free();return why
