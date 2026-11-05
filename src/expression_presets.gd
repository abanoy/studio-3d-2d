extends RefCounted
# Source adapters describe groups; one shared evaluator produces standard amounts.
const META:="has_expression_presets_1"
const FORMAT:="studio_expression_presets_1"
const MAX_ENTRIES:=256
const MAX_BINDS:=2048
const LABELS={"happy":"Happy","joy":"Happy","sad":"Sad","sorrow":"Sad","angry":"Angry","relaxed":"Relaxed","fun":"Relaxed","surprised":"Surprised","aa":"Mouth A","a":"Mouth A","ih":"Mouth I","i":"Mouth I","ou":"Mouth U","u":"Mouth U","ee":"Mouth E","e":"Mouth E","oh":"Mouth O","o":"Mouth O","blink":"Blink","blinkLeft":"Blink left","blink_l":"Blink left","blinkRight":"Blink right","blink_r":"Blink right","neutral":"Neutral"}

static func has_data(root: Node) -> bool:
	var data: Dictionary=root.get_meta(META,{"entries":[],"error":""})
	return not data.entries.is_empty() or not data.error.is_empty()

static func index(value,limit: int) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and value==floor(value) and value>=0 and value<limit

static func number(value,maximum: float) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and value>=0 and value<=maximum

static func capture(document: Dictionary,rows: Array) -> Dictionary:
	var asset=document.get("asset",{})
	if asset is Dictionary and asset.get("extras",{}) is Dictionary and asset.get("extras",{}).has("studio_expression_groups"):
		if document.get("extensions",{}) is Dictionary and (document.get("extensions",{}).has("VRM") or document.get("extensions",{}).has("VRMC_vrm")):
			return {"format":FORMAT,"entries":[],"error":"Ambiguous embedded expression sources."}
		return capture_prepared(asset.extras.studio_expression_groups,rows)
	var result:={"format":FORMAT,"entries":[],"error":""};var extensions=document.get("extensions",{})
	if not extensions is Dictionary:return result
	var native=extensions.get("VRMC_vrm",extensions.get("VRM",{}))
	if not native is Dictionary:result.error="Invalid native expression data.";return result
	var version1: bool=extensions.has("VRMC_vrm");var definitions:=[]
	if version1 and extensions.has("VRM") or not native.is_empty() and native.get("specVersion")!=("1.0" if version1 else "0.0"):result.error="Unsupported native expression version.";return result
	if version1:
		var expressions=native.get("expressions",{})
		if not expressions is Dictionary:result.error="Invalid embedded expression list.";return result
		for group in ["preset","custom"]:
			var values=expressions.get(group,{})
			if not values is Dictionary or definitions.size()+values.size()>MAX_ENTRIES:result.error="Invalid or excessive embedded expression group.";return result
			for name in values:
				definitions.append({"id":group+":"+str(name),"native_name":str(name),"preset":str(name) if group=="preset" else "","value":values[name],"group":group})
	else:
		var master=native.get("blendShapeMaster",{})
		if not master is Dictionary:result.error="Invalid embedded expression list.";return result
		var groups=master.get("blendShapeGroups",[])
		if not groups is Array or groups.size()>MAX_ENTRIES:result.error="Invalid or excessive embedded expression group.";return result
		for i in range(groups.size()):
			var value=groups[i]
			if not value is Dictionary:result.error="Invalid embedded expression.";return result
			var preset=value.get("presetName","unknown")
			definitions.append({"id":"group:"+str(i),"native_name":str(value.get("name","Expression "+str(i+1))),"preset":str(preset) if preset!="unknown" else "","value":value,"group":"preset" if preset!="unknown" else "custom"})
	if definitions.size()>MAX_ENTRIES:result.error="Embedded expressions exceed 256 entries.";return result
	var nodes=document.get("nodes",[]);var known:={}
	for row in rows:known[int(row.node)]=row
	var total:=0;var resolved:=0
	for definition in definitions:
		var entry:={"id":definition.id,"native_name":definition.native_name,"preset":definition.preset,"label":LABELS.get(definition.preset,definition.native_name),"group":definition.group,"binary":false,"overrides":{"blink":"none","mouth":"none","look":"none"},"binds":[],"error":""}
		result.entries.append(entry);var value=definition.value
		if not value is Dictionary:entry.error="Invalid embedded expression.";continue
		if not value.get("isBinary",false) is bool:entry.error="Invalid binary expression switch.";continue
		entry.binary=value.get("isBinary",false)
		for field in (["materialColorBinds","textureTransformBinds"] if version1 else ["materialValues"]):
			if not value.get(field,[]) is Array or not value.get(field,[]).is_empty():entry.error="This expression needs unsupported material or texture effects."
		if version1:
			for pair in [["blink","overrideBlink"],["mouth","overrideMouth"],["look","overrideLookAt"]]:
				var mode=value.get(pair[1],"none")
				if not mode in ["none","block","blend"]:entry.error="Invalid expression override mode."
				else:entry.overrides[pair[0]]=mode
		var binds=value.get("morphTargetBinds" if version1 else "binds",[])
		if not binds is Array or binds.size()>MAX_BINDS:entry.error="Invalid or excessive expression bindings.";continue
		var seen:={}
		for bind in binds:
			total+=1
			if total>MAX_BINDS:result.error="Embedded expressions exceed 2048 bindings.";return result
			if not bind is Dictionary or not index(bind.get("index"),2048) or not number(bind.get("weight"),1. if version1 else 100.):entry.error="Invalid expression morph binding.";continue
			var targets:=[]
			if version1:
				if index(bind.get("node"),nodes.size()):targets.append(int(bind.node))
			else:
				if index(bind.get("mesh"),document.get("meshes",[]).size()):
					for node in known:
						if nodes[node].get("mesh",-1)==bind.mesh:targets.append(node)
			if targets.is_empty():entry.error="An expression part is missing from the imported scene.";continue
			for node in targets:
				resolved+=1
				if resolved>MAX_BINDS:result.error="Resolved expressions exceed 2048 bindings.";return result
				if not known.has(node) or int(bind.index)>=known[node].names.size():entry.error="An expression target is missing from the imported scene.";continue
				var key:=str(node)+":"+str(int(bind.index))
				if seen.has(key):entry.error="Duplicate expression morph binding.";continue
				seen[key]=true;entry.binds.append({"node":str(node),"index":str(int(bind.index)),"weight":float(bind.weight)/(1. if version1 else 100.),"native_name":str(known[node].names[int(bind.index)])})
		if entry.binds.is_empty() and entry.error.is_empty():entry.error="This expression has no supported morph bindings."
	return result

static func capture_prepared(value,rows: Array) -> Dictionary:
	var result:={"format":FORMAT,"entries":[],"error":""}
	if not value is Dictionary or value.get("format")!=FORMAT or not value.get("entries") is Array or value.entries.size()>MAX_ENTRIES:
		result.error="Invalid or excessive prepared expression groups.";return result
	if not value.get("error","") is String:result.error="Invalid prepared expression diagnostics.";return result
	if not value.get("error","").is_empty():result.error=str(value.error).left(500);return result
	var known:={};var seen:={};var count:=0
	for row in rows:known[str(row.node)]=row
	for source in value.entries:
		if not source is Dictionary or not source.get("id") is String or source.id.is_empty() or source.id.length()>256 or seen.has(source.id):result.error="Invalid or duplicate expression identity.";return result
		seen[source.id]=true
		if source.get("binary",false)!=false or source.get("preset","")!="" or source.get("overrides",{"blink":"none","mouth":"none","look":"none"})!={"blink":"none","mouth":"none","look":"none"}:result.error="Unsupported prepared expression semantics.";return result
		for field in ["native_name","label","group","error"]:
			if not source.get(field) is String or str(source[field]).length()>500:result.error="Invalid prepared expression name or diagnostic.";return result
		var entry:={"id":source.id,"native_name":source.native_name,"label":source.label,"preset":"","group":source.group,"binary":false,"overrides":{"blink":"none","mouth":"none","look":"none"},"binds":[],"error":source.error}
		if entry.label==entry.native_name:entry.label=preload("res://src/shape_labels.gd").display(entry.native_name,false)
		if not source.get("binds") is Array:result.error="Invalid prepared expression bindings.";return result
		var targets:={}
		for bind in source.binds:
			count+=1
			if count>MAX_BINDS:result.error="Resolved expressions exceed 2048 bindings.";return result
			if not bind is Dictionary or not bind.get("node") is String or not bind.get("index") is String or not preload("res://src/source_shape.gd").index_key(bind.node,100000) or not preload("res://src/source_shape.gd").index_key(bind.index,2048) or not (bind.get("weight") is int or bind.get("weight") is float) or not is_finite(float(bind.weight)) or absf(float(bind.weight))>100:
				entry.error="Invalid prepared expression morph binding.";continue
			if not known.has(bind.node) or int(bind.index)>=known[bind.node].names.size():entry.error="An expression target is missing from the imported scene.";continue
			var key: String=bind.node+":"+bind.index
			if targets.has(key):entry.error="Duplicate expression morph binding.";continue
			targets[key]=true
			var native_name: String=str(known[bind.node].names[int(bind.index)])
			if bind.get("native_name")!=native_name:entry.error="An expression target's native identity changed.";continue
			entry.binds.append({"node":bind.node,"index":bind.index,"weight":float(bind.weight),"native_name":native_name})
		if entry.binds.is_empty() and entry.error.is_empty():entry.error="This expression has no supported morph bindings."
		if not entry.error.is_empty():entry.binds=[]
		result.entries.append(entry)
	return result

static func procedural(preset: String) -> String:
	if preset in ["blink","blinkLeft","blinkRight","blink_l","blink_r"]:return "blink"
	if preset in ["aa","ih","ou","ee","oh","a","i","u","e","o"]:return "mouth"
	if preset in ["lookUp","lookDown","lookLeft","lookRight","lookup","lookdown","lookleft","lookright"]:return "look"
	return ""

static func evaluate(catalogue: Dictionary,values: Dictionary) -> Dictionary:
	if catalogue.get("format")!=FORMAT or not catalogue.get("error","").is_empty():return {"error":catalogue.get("error","Invalid expression catalogue.")}
	var known:={};var weights:={};var output:={};var factors:={"blink":1.,"mouth":1.,"look":1.}
	for entry in catalogue.entries:known[entry.id]=entry
	for id in values:
		if not known.has(id) or not number(values[id],1.):return {"error":"Invalid expression or amount."}
		if not known[id].error.is_empty():return {"error":known[id].error}
		weights[id]=float(values[id])
		if known[id].binary:weights[id]=1. if weights[id]>.5 else 0.
	for id in weights:
		for category in factors:
			if procedural(known[id].preset)==category:continue
			var mode: String=known[id].overrides[category]
			if mode=="block" and weights[id]>0:factors[category]=-1000.
			elif mode=="blend":factors[category]-=weights[id]
	# A pose replaces the entire embedded morph set. Raw unrelated deforms survive.
	for entry in catalogue.entries:
		for bind in entry.binds:
			if not output.has(bind.node):output[bind.node]={}
			output[bind.node][bind.index]=0.
	for id in weights:
		var entry: Dictionary=known[id];var weight: float=weights[id];var category:=procedural(entry.preset)
		if not category.is_empty():
			var factor:=clampf(factors[category],0.,1.)
			weight*=float(factor==1.) if entry.binary else factor
		for bind in entry.binds:output[bind.node][bind.index]+=weight*bind.weight
	return {"values":output,"error":""}
