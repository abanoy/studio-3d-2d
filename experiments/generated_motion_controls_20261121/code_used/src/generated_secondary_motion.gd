extends RefCounted
# Explicit model-level choice; original helper declarations and native springs
# remain unchanged. Missing settings retain historical Keep shape behavior.
const KEY:="generated_secondary_motion"
const FORMAT:="studio_generated_secondary_motion_1"
const PREVIEW_FORMAT:="studio_generated_secondary_preview_1"
const LimbIK=preload("res://src/limb_ik.gd")
const CORE_NAMES=["body","root","center","hips","pelvis","spine","spine1","spine2","chest","upperchest","neck","head","bip001pelvis","bip001spine","bip001spine1","bip001spine2","bip001neck","bip001head","valvebipedbip01pelvis","valvebipedbip01spine","valvebipedbip01spine1","valvebipedbip01spine2","valvebipedbip01neck1","valvebipedbip01head1","センター","上半身","上半身2","下半身","首","頭"]
static func normalized(name: String) -> String:return name.to_lower().replace("_","").replace(".","").replace("-","").replace(" ","")
static func core(data: Dictionary,name: String) -> bool:
	# Conservative exclusions, not inferred humanoid bindings. Exact declared
	# roles and familiar core names must never gain a loose-part gravity preset.
	var parameters=data.get("metadata",{}).get("native_parameters",{})
	if parameters is Dictionary and parameters.get("humanoid") is Dictionary:
		for entry in parameters.humanoid.values():
			if entry is Dictionary and entry.get("node_name")==name:return true
	var clean:=normalized(name)
	if clean in CORE_NAMES:return true
	for aliases in LimbIK.ALIASES.values():
		if clean in aliases:return true
	return clean in ["leftshoulder","rightshoulder","claviclel","clavicler","valvebipedbip01lclavicle","valvebipedbip01rclavicle"]
static func flexible_first(data: Dictionary,name: String,node_index: int=-1) -> bool:
	if core(data,name):return false
	var report=data.get("metadata",{}).get("generated_helpers",{})
	if report is Dictionary and report.get("format")=="studio_generated_helpers_1" and report.get("mode","")!="existing_joints":
		var nodes=report.get("helper_nodes",[])
		if node_index>=0 and nodes is Array and node_index in nodes:return true
	var clean:=normalized(name)
	if clean.begins_with("hasloose"):return true
	for word in ["hair","髪","skirt","cloth","ribbon","cape","tail","sleeve","裾","袖"]:
		if word in clean:return true
	return false
static func policy(data: Dictionary) -> Dictionary:
	var selected: Dictionary=setting(data)
	if selected.has("error"):return selected
	# Disposable previews need tuning and exclusion flags, never a copy of the
	# original model's arbitrary import report, source arrays or saved edits.
	var metadata: Dictionary={KEY:{"format":FORMAT,"mode":selected.mode}}
	var parameters=data.get("metadata",{}).get("native_parameters",{})
	if parameters is Dictionary and parameters.get("humanoid") is Dictionary:
		var humanoid: Dictionary={}
		for role in parameters.humanoid:
			var entry=parameters.humanoid[role]
			if entry is Dictionary and entry.get("node_name") is String:humanoid[str(role)]={"node_name":entry.node_name}
		if not humanoid.is_empty():metadata.native_parameters={"humanoid":humanoid}
	var report=data.get("metadata",{}).get("generated_helpers",{})
	if report is Dictionary and report.get("format")=="studio_generated_helpers_1" and report.get("helper_nodes") is Array:
		var nodes: Array=[]
		for value in report.helper_nodes:
			if (value is int or value is float) and is_finite(value) and value==floor(value) and value>=0 and value<100000:nodes.append(int(value))
		if not nodes.is_empty():metadata.generated_helpers={"format":"studio_generated_helpers_1","mode":str(report.get("mode","")),"helper_nodes":nodes}
	return {"metadata":metadata}
static func fingerprint(definition: Dictionary) -> String:
	var hash:=HashingContext.new();hash.start(HashingContext.HASH_SHA256);hash.update(var_to_bytes(definition));return hash.finish().hex_encode()
static func preview_context(source: RefCounted,target: RefCounted,definition: Dictionary) -> Dictionary:
	if definition.get("source_family","")!="HAS":return {}
	if source==null or target==null or not is_instance_valid(source.root) or not is_instance_valid(target.root) or not source.root.is_inside_tree() or not target.root.is_inside_tree():return {"error":"The generated wind preview no longer owns its models."}
	if target.root.get_meta("has_secondary_rig",{}).get("source_family","")!="HAS":return {"error":"Generated wind tuning needs the checked HAS helper profile."}
	var tuning: Dictionary=policy(source.data)
	if tuning.has("error"):return tuning
	return {"format":PREVIEW_FORMAT,"source":weakref(source),"source_id":source.data.id,"source_sha":source.data.sha256,"source_root":source.root.get_instance_id(),"target_sha":target.data.sha256,"target_root":target.root.get_instance_id(),"definition":fingerprint(definition),"policy":tuning}
static func preview_error(context: Dictionary,target: RefCounted,definition: Dictionary) -> String:
	if context.get("format")!=PREVIEW_FORMAT or not context.get("source") is WeakRef or not context.get("policy") is Dictionary:return "Invalid generated wind tuning context."
	var source: RefCounted=context.source.get_ref()
	if source==null or not is_instance_valid(source.root) or not source.root.is_inside_tree() or source.root.get_instance_id()!=context.get("source_root") or source.data.id!=context.get("source_id") or source.data.sha256!=context.get("source_sha"):return "The wind preview's source changed. Reopen its review."
	if target==null or not is_instance_valid(target.root) or not target.root.is_inside_tree() or target.root.get_instance_id()!=context.get("target_root") or target.data.sha256!=context.get("target_sha"):return "The generated wind candidate changed. Reopen its review."
	if definition.get("source_family","")!="HAS" or target.root.get_meta("has_secondary_rig",{}).get("source_family","")!="HAS" or fingerprint(definition)!=context.get("definition"):return "The checked generated wind groups changed. Reopen their review."
	if policy(source.data)!=context.policy:return "The generated hair setting changed. Reopen wind review."
	return ""
static func setting(data: Dictionary) -> Dictionary:
	var value=data.get("metadata",{}).get(KEY)
	if value==null:return {"mode":"keep_shape"}
	if not value is Dictionary or value.size()!=2 or value.get("format")!=FORMAT or value.get("mode") not in ["keep_shape","natural"]:return {"error":"Invalid generated hair motion setting. Choose Keep hair shape or Natural gravity again."}
	return {"mode":value.mode}
static func natural(data: Dictionary,definition: Dictionary) -> bool:
	return definition.get("source_family","")=="HAS" and setting(data).get("mode","")=="natural"
static func values(original: Dictionary,is_natural: bool,joint: int,first_flexible:=false) -> Dictionary:
	var result: Dictionary=original.duplicate(true)
	if not is_natural:return result
	# The scratch Anchor fixes attachment position. Its first rotating hair
	# joint may relax too; ambiguous first joints keep their original tuning.
	if joint==0 and not first_flexible:return result
	result.stiffness*=.08
	result.gravity=maxf(float(result.gravity),1.)
	result.gravity_direction=[0.,-1.,0.]
	return result
