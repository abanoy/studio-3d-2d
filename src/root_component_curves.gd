extends RefCounted
# Experimental component sampler. Not yet a saved model format or editor adapter.
const Model=preload("res://src/model.gd")
const FIELDS=["position","rotation_xyzw","scale"]
const FORMAT:="studio_root_components_1"

static func validate(data) -> String:
	if not data is Dictionary or data.get("format")!=FORMAT or data.size()!=4:return "Unsupported root component format."
	var total:=0
	for field in FIELDS:
		var keys=data.get(field)
		if not keys is Array or keys.size()>241:return "Invalid root component key count."
		total+=keys.size();var previous:=-1
		for key in keys:
			if not key is Dictionary or key.size()!=(4 if key.has("authored") else 3) or key.has("authored") and not key.authored is bool or not Model.integer(key.get("frame"),0,Model.Clips.MAX_SOURCE_FRAME) or key.frame<=previous or not key.get("interpolation") in ["ease","linear","hold"]:return "Invalid root component key."
			var value=key.get("value")
			if not Model.transform_valid(value) or not Model.scale_valid(value.get("scale")):return "Invalid root component value."
			var neutral:=Model.identity();neutral["scale"]=1.
			for peer in FIELDS:
				if peer==field:continue
				if peer=="scale":
					if float(value[peer])!=1.:return "A component key cannot contain another component's edits."
				else:
					for n in range(neutral[peer].size()):
						if float(value[peer][n])!=float(neutral[peer][n]):return "A component key cannot contain another component's edits."
			previous=int(key.frame)
	if total>Model.Clips.MAX_TOTAL_KEYS:return "Too many root component keys."
	return ""

static func put(data: Dictionary,field: String,frame: int,value,mode: String) -> Dictionary:
	var error:=validate(data)
	if not error.is_empty():return {"error":error}
	if not field in FIELDS:return {"error":"Unknown root component."}
	var result:=data.duplicate(true);var transform:=Model.identity();transform["scale"]=1.
	transform[field]=value.duplicate() if value is Array else value
	Model.Timeline.put_key(result[field],{"frame":frame,"value":transform,"interpolation":mode})
	error=validate(result)
	return {"error":error} if not error.is_empty() else {"data":result}

static func split(keys: Array) -> Dictionary:
	var result:={"format":FORMAT,"position":[],"rotation_xyzw":[],"scale":[]}
	for key in keys:
		for field in FIELDS:
			var value: Dictionary=Model.identity();value["scale"]=1.
			value[field]=key.value[field].duplicate() if key.value[field] is Array else key.value[field]
			result[field].append({"frame":key.frame,"value":value,"interpolation":key.interpolation})
	return result

static func sample(tracks: Dictionary,frame: float,base: Dictionary) -> Dictionary:
	var result:=base.duplicate(true)
	for field in FIELDS:
		if tracks[field].is_empty():continue
		var pair:=Model.curve_pair(tracks[field],frame)
		result[field]=Model.blend_transform(pair.a.value,pair.b.value,pair.t)[field]
	return result
