extends RefCounted
# A character owns ordinary independent model rows, never merged skeletons.
const World=preload("res://src/world_document.gd")
const Model=preload("res://src/model.gd")
const Visibility=preload("res://src/visibility_track.gd")
const Clips=preload("res://src/animation_clips.gd")
const FORMAT:="studio_character_parts_1"
const MAX_PARTS:=32

static func role_for(path: String) -> String:
	var text:=path.get_file().get_basename().to_lower().replace("_"," ")
	for role in ["miniskirt","hair","dress","skirt","mask","body","head","hat","eyes"]:
		if text.contains(role):return role
	return "part"

static func intrinsic_scale(row: Dictionary) -> Dictionary:
	var metadata=row.get("metadata",{}).get("character_parts",{})
	if row.get("kind")!="group" or not metadata is Dictionary or metadata.get("format")!=FORMAT:return {"factor":1.0}
	var factor=metadata.get("height_factor",1.)
	if not Model.scale_valid(factor):return {"error":"The character's shared height factor is invalid."}
	return {"factor":float(factor)}

static func describe(world: Dictionary, selected: String, duration: int) -> Dictionary:
	var index:={}
	for row in world.objects:index[row.id]=row
	if not index.has(selected):return {"error":"Select a character or one of its parts."}
	var chosen: Dictionary=index[selected]
	var root: Dictionary=chosen if chosen.get("kind")=="group" else index.get(chosen.get("parent_id",""),{})
	var metadata=root.get("metadata",{}).get("character_parts",{})
	if not metadata is Dictionary or metadata.get("format")!=FORMAT:return {"error":"This object is not a character bundle."}
	var parts:=[];var seen:={}
	for member in metadata.get("members",[]):
		if not member is Dictionary or not index.has(member.get("id")) or seen.has(member.id):continue
		var row: Dictionary=index[member.id]
		if row.parent_id!=root.id or row.kind!="model":continue
		seen[row.id]=true;parts.append({"role":str(member.get("role","part")),"row":row.duplicate(true)})
	return {"root_id":root.id,"name":root.name,"parts":parts,"metadata":metadata.duplicate(true)}

static func assemble(world: Dictionary, group: Dictionary, incoming: Array, duration: int, options: Dictionary={}) -> Dictionary:
	if incoming.is_empty() or incoming.size()>MAX_PARTS:return {"error":"Choose between1 and32 character parts."}
	var result: Dictionary=world.duplicate(true)
	var root: Dictionary=group.duplicate(true)
	var existing:=str(options.get("existing_root",""))
	var members: Array=[]
	if not existing.is_empty():
		var bundle:=describe(world,existing,duration)
		if bundle.has("error"):return bundle
		for row in result.objects:
			if row.id==bundle.root_id:root=row;break
		members=root.metadata.character_parts.members.duplicate(true)
	elif result.objects.size()+incoming.size()+1>World.MAX_OBJECTS:return {"error":"The scene has no room for this character's parts."}
	if result.objects.size()+incoming.size()>World.MAX_OBJECTS:return {"error":"The scene has reached its object limit."}
	for item in incoming:
		var row: Dictionary=item.row.duplicate(true)
		row.kind="model";row.parent_id=root.id;row.start_frame=int(options.get("start_frame",0));row.visible=bool(item.get("visible",true))
		# Keep every prepared source origin and original model proportions.
		row.position=[0,0,0];row.rotation_xyzw=[0,0,0,1];row.scale=1.
		row.metadata["character_part"]={"root_id":root.id,"role":str(item.get("role","part"))}
		result.objects.append(row)
		members.append({"id":row.id,"role":str(item.get("role","part")),"sha256":row.sha256})
	if existing.is_empty():
		root.kind="group";root.parent_id="";root.start_frame=int(options.get("start_frame",0));root.scale=1.
		root.metadata["character_parts"]={"format":FORMAT,"members":members,"height_factor":1.,"height_reference_id":str(options.get("reference_id",incoming[0].row.id)),"scale_owner":"root_only","independent_rigs":true,"bone_following":false}
		result.objects.append(root)
	else:root.metadata.character_parts.members=members
	var why: String=World.validate(result,duration)
	return {"world":result,"root_id":root.id} if why.is_empty() else {"error":why}

static func visibility_edit(world: Dictionary, selected: String, values: Dictionary, frame: int, duration: int) -> Dictionary:
	var bundle:=describe(world,selected,duration)
	if bundle.has("error"):return bundle
	var before:={};var after:={}
	for part in bundle.parts:
		var row: Dictionary=part.row
		if not values.has(row.id) or not values[row.id] is bool or Visibility.target(row,frame)==values[row.id]:continue
		var changed: Dictionary=Clips.promote(row)
		# There is no earlier animation at frame0: startup visibility is immediate.
		if frame==0:changed.visible=values[row.id]
		if not Model.ShapeAnimation.has_data(changed):changed.format=Visibility.FORMAT
		if not changed.has("visibility_keys"):changed.visibility_keys=[]
		Visibility.put(changed,frame,values[row.id])
		var why: String=Model.validate(changed,duration)
		if not why.is_empty():return {"error":why}
		before[row.id]=row;after[row.id]=changed
	return {"type":"world_objects","before":before,"after":after}
