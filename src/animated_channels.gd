extends RefCounted
# UI index over legacy snapshots and independent controls; never changes evaluation.
const Clips=preload("res://src/animation_clips.gd")
const Timeline=preload("res://src/timeline.gd")
const Labels=preload("res://src/bone_labels.gd")
const ShapeLabels=preload("res://src/shape_labels.gd")

static func identity() -> Dictionary:
	return {"position":[0,0,0],"rotation_xyzw":[0,0,0,1],"scale":1.0}

static func has_data(data: Dictionary) -> bool:
	if data.get("format")=="studio_model_9":return not data.get("visibility_keys",[]).is_empty() or not describe_components(data,false).is_empty()
	for tracks in data.get("root_components",{}).values():
		for field in ["position","rotation_xyzw","scale"]:
			if tracks[field].any(func(key):return key.get("authored",true)):return true
	if not data.get("visibility_keys",[]).is_empty() or not data.pose_keys.is_empty():return true
	for piece in data.get("animation_clips",[]):
		if not piece.keys.is_empty() or not piece.get("shape_keys",[]).is_empty():return true
		if not piece.get("body_controls",{}).is_empty():return true
	return false

static func different(a: Dictionary, b: Dictionary) -> bool:
	return Timeline.vector(a.position).distance_squared_to(Timeline.vector(b.position))>1e-12 or absf(Timeline.quaternion(a.rotation_xyzw).dot(Timeline.quaternion(b.rotation_xyzw)))<1-1e-7 or absf(float(a.get("scale",1))-float(b.get("scale",1)))>1e-7

static func key_channels(key: Dictionary, previous_pose: Dictionary, previous_transform: Dictionary) -> Array:
	if key.has("authored_channels"):return key.authored_channels.duplicate()
	var result: Array=[]
	if different(key.transform,previous_transform):result.append("@root")
	for id in key.pose.keys()+previous_pose.keys():
		if not id in result and different(key.pose.get(id,identity()),previous_pose.get(id,identity())):result.append(id)
	return result

static func describe(data: Dictionary, advanced:=false) -> Array:
	if data.get("format")=="studio_model_9":return describe_components(data,advanced)
	if data.get("format") in ["studio_model_6","studio_model_7","studio_model_8"]:return describe_body(data,advanced)
	var curves: Array=[]
	if Clips.has_pieces(data):
		for piece in data.animation_clips:curves.append({"keys":piece.keys,"base":piece.base_transform,"start":int(piece.start),"source_in":int(piece.source_in),"length":int(piece.length)})
	else:curves.append({"keys":data.pose_keys,"base":Clips.transform(data),"start":0,"source_in":0,"length":100001})
	var channels:={}
	for curve in curves:
		var previous_pose: Dictionary={};var previous_transform: Dictionary=curve.base
		var left:=-1;var right:=-1
		for i in range(curve["keys"].size()):
			if curve["keys"][i].frame<=curve.source_in:left=i
			if right<0 and curve["keys"][i].frame>curve.source_in+curve.length-1:right=i
		var index:=-1
		for key in curve["keys"]:
			index+=1
			var ids:=key_channels(key,previous_pose,previous_transform)
			if data.get("format")=="studio_model_5":ids=ids.filter(func(id):return not str(id).begins_with("@shape/"))
			for node in key.get("shapes",{}):
				for shape_index in key.shapes[node]:
					var shape_id: String="@shape/"+node+"/"+shape_index
					if not shape_id in ids:ids.append(shape_id)
			var relevant: bool=key.frame>=curve.source_in and key.frame<curve.source_in+curve.length or index==left or index==right and index>0 and curve["keys"][index-1].interpolation!="hold"
			previous_pose=key.pose;previous_transform=key.transform
			if not relevant:continue
			# Old full-pose takes with a single neutral key still expose that authored key.
			if ids.is_empty() and curve["keys"].size()==1 and not key.has("authored_channels"):ids=["@root"]
			for id in ids:
				if not channels.has(id):channels[id]={"id":id,"frames":[],"ranges":[],"estimated":not key.has("authored_channels")}
				var row: Dictionary=channels[id]
				row.estimated=row.estimated or not key.has("authored_channels")
				if Clips.has_pieces(data) and not Vector2i(curve.start,curve.length) in row.ranges:row.ranges.append(Vector2i(curve.start,curve.length))
				var frame:=int(curve.start)+int(key.frame)-int(curve.source_in)
				if key.frame>=curve.source_in and key.frame<curve.source_in+curve.length and not frame in row.frames:row.frames.append(frame)
	if channels.is_empty():
		for curve in curves:
			if not curve["keys"].is_empty():channels["@root"]={"id":"@root","frames":[],"ranges":[],"estimated":true};break
	var result: Array=[]
	var ids: Array=channels.keys();ids.sort()
	for id in ids:
		var row: Dictionary=channels[id]
		# Existing evaluator uses complete pose snapshots. Every snapshot controls
		# every displayed part, including implicit neutral values; hints only choose rows.
		row.frames=[];row.ranges=[]
		for curve in curves:
			if Clips.has_pieces(data):row.ranges.append(Vector2i(curve.start,curve.length))
			for key in curve["keys"]:
				var at:=int(curve.start)+int(key.frame)-int(curve.source_in)
				if key.frame>=curve.source_in and key.frame<curve.source_in+curve.length and not at in row.frames:row.frames.append(at)
		row.frames.sort()
		var name:=str(id).rsplit("::",true,1)[-1]
		row["label"]="Root / transform" if id=="@root" else Labels.display(name,advanced,Labels.role(data,name))
		row["tooltip"]="Root position, rotation and scale" if id=="@root" else Labels.tooltip(name,str(id),advanced,Labels.role(data,name))
		if str(id).begins_with("@shape/"):
			var parts: PackedStringArray=str(id).split("/")
			var original: String=data.get("shape_names",{}).get(parts[1],{}).get(parts[2],"Shape "+str(int(parts[2])+1))
			row.label=ShapeLabels.display(original,advanced);row.tooltip=original+"\nImported shape, part "+parts[1]+", channel "+parts[2]+"\n"+str(id)
		if row.estimated:row.tooltip+="\nChannel inferred from an older whole-pose snapshot."
		row.tooltip+="\nPose keys are shared snapshots; click to inspect this part at a key."
		result.append(row)
	if data.get("format")=="studio_model_5":
		var shape_rows:={}
		for piece in data.animation_clips:
			for key in piece.get("shape_keys",[]):
				for node in key.shapes:
					for index in key.shapes[node]:
						var id: String="@shape/"+node+"/"+index
						if not shape_rows.has(id):
							var original: String=data.get("shape_names",{}).get(node,{}).get(index,"Shape "+str(int(index)+1))
							shape_rows[id]={"id":id,"label":ShapeLabels.display(original,advanced),"tooltip":original+"\n"+id+"\nIndependent expression controls; body keys are unchanged.","frames":[],"ranges":[],"estimated":false}
						var row: Dictionary=shape_rows[id];var range:=Vector2i(int(piece.start),int(piece.length))
						if not range in row.ranges:row.ranges.append(range)
						var frame:=int(piece.start)+int(key.frame)-int(piece.source_in)
						if key.frame>=piece.source_in and key.frame<piece.source_in+piece.length and not frame in row.frames:row.frames.append(frame)
		var shape_ids: Array=shape_rows.keys();shape_ids.sort()
		for id in shape_ids:shape_rows[id].frames.sort();result.append(shape_rows[id])
	if not data.get("visibility_keys",[]).is_empty():
		var frames:=[]
		for key in data.visibility_keys:frames.append(int(key.frame))
		result.append({"id":"@visibility","label":"Visibility","tooltip":"Persistent visibility; independent of motion pieces","frames":frames,"ranges":[],"estimated":false})
	return result

static func describe_components(data: Dictionary,advanced: bool) -> Array:
	var document=load("res://src/root_component_document.gd")
	var result: Array=describe_body(document.legacy_view(data),advanced).filter(func(row):return row.id!="@root")
	var rows:={};var labels:={"position":"Position","rotation_xyzw":"Rotation","scale":"Scale"}
	for piece in data.animation_clips:
		var tracks: Dictionary=data.root_components.get(piece.id,{})
		if tracks.is_empty():tracks=document.Adapter.extract(document.Body.view(document.legacy_view(data))).get(piece.id,{})
		for field in labels:
			var keys: Array=tracks.get(field,[])
			if not keys.any(func(key):return key.get("authored",true)):continue
			var id: String="@root/"+field if advanced else "@root"
			if not rows.has(id):rows[id]={"id":id,"label":labels[field] if advanced else "Root / transform","tooltip":"Independent "+field+" keys; select to inspect the model root." if advanced else "Model position, rotation and scale keys.","frames":[],"ranges":[],"estimated":false}
			var row: Dictionary=rows[id];var span:=Vector2i(int(piece.start),int(piece.length))
			if not span in row.ranges:row.ranges.append(span)
			for key in keys:
				if not key.get("authored",true) or key.frame<piece.source_in or key.frame>=piece.source_in+piece.length:continue
				var at:=int(piece.start)+int(key.frame)-int(piece.source_in)
				if not at in row.frames:row.frames.append(at)
	for row in rows.values():row.frames.sort();result.append(row)
	return result

static func describe_body(data: Dictionary,advanced: bool) -> Array:
	var adapter=load("res://src/body_animation.gd");var body: Dictionary=adapter.view(data)
	var expression:=data.duplicate();expression.format="studio_model_5";expression.animation_clips=[]
	for piece in data.animation_clips:
		var copy: Dictionary=piece.duplicate();copy["keys"]=[];expression.animation_clips.append(copy)
	var result:=describe(expression,advanced);var ids: Array=adapter.B.known_channels(body);ids.sort()
	for id in ids:
		var frames: Array=adapter.B.frames(body,id);var ranges:=[]
		for piece in body.pieces:
			if adapter.B.owns(piece,id) and not adapter.B.points(body,piece,id,false).is_empty():ranges.append(Vector2i(int(piece.start),int(piece.length)))
		if frames.is_empty() and ranges.is_empty():continue
		var name:=str(id).rsplit("::",true,1)[-1]
		result.append({"id":id,"label":"Root / transform" if id=="@root" else Labels.display(name,advanced,Labels.role(data,name)),"tooltip":("Root position, rotation and scale" if id=="@root" else Labels.tooltip(name,str(id),advanced,Labels.role(data,name)))+"\nIndependent body controls; other parts retain their own timing.","frames":frames,"ranges":ranges,"estimated":false})
	return result
