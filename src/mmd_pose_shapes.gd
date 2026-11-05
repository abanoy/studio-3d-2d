extends RefCounted
# Resolve native VPD names once; animation stores the usual node/target amounts.
static func resolve(controls,rows: Array,presets: Dictionary) -> Dictionary:
	var result:={"values":{},"matched":[],"skipped":[]}
	if not controls is Array or controls.size()>4096:return {"error":"Invalid or excessive pose shape controls."}
	var raw:={};var groups:={};var seen:={};var operations:=0
	for row in rows:
		var local:={}
		for i in range(row.names.size()):
			var name: String=row.names[i]
			if not raw.has(name):raw[name]=[]
			if local.has(name):raw[name].append({"error":"Duplicate target name in one model part."})
			else:raw[name].append({"node":str(row.node),"index":str(i),"weight":1.})
			local[name]=true
	for group in presets.get("entries",[]):
		var name: String=group.native_name
		if not groups.has(name):groups[name]=[]
		groups[name].append(group)
	for control in controls:
		if not control is Dictionary or not control.get("name") is String or control.name.is_empty() or control.name.length()>512 or seen.has(control.name):
			return {"error":"Invalid or repeated pose shape name."}
		seen[control.name]=true
		var weight=control.get("weight")
		if not (weight is int or weight is float) or not is_finite(float(weight)) or absf(float(weight))>100:
			return {"error":"A pose shape amount exceeds the supported range."}
		var binds: Array=[];var reason:=""
		if raw.has(control.name) and groups.has(control.name):reason="This name refers to both a raw shape and an expression group."
		elif groups.has(control.name):
			if groups[control.name].size()!=1:reason="More than one expression group uses this name."
			else:
				var group: Dictionary=groups[control.name][0]
				reason=presets.get("error","")
				if reason.is_empty():reason=group.get("error","")
				if reason.is_empty():binds=group.binds
		elif raw.has(control.name):binds=raw[control.name]
		else:reason="No matching shape in this character."
		for bind in binds:
			if bind.has("error"):reason=bind.error;break
		if not reason.is_empty():result.skipped.append({"name":control.name,"reason":reason});continue
		if binds.is_empty():result.skipped.append({"name":control.name,"reason":"No supported shape targets."});continue
		result.matched.append(control.name)
		for bind in binds:
			operations+=1
			if operations>32768:return {"error":"Pose shape expansion exceeds its work limit."}
			if not result.values.has(bind.node):result.values[bind.node]={}
			var amount: float=result.values[bind.node].get(bind.index,0.)+float(weight)*float(bind.weight)
			if not is_finite(amount) or absf(amount)>100:return {"error":"Combined pose shapes exceed the supported range."}
			result.values[bind.node][bind.index]=amount
	if not preload("res://src/shape_animation.gd").values_valid(result.values):return {"error":"Invalid resolved pose shape amounts."}
	return result
