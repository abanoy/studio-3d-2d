extends RefCounted
# Explicit six-family static assembly. No conversion, centring or skeleton merge.
const World=preload("res://src/world_document.gd")
const Model=preload("res://src/model.gd")
const Clips=preload("res://src/animation_clips.gd")
const Visibility=preload("res://src/visibility_track.gd")
const FORMAT:="studio_character_parts_1"
const ROLES:=["body","hair","dress","skirt","miniskirt","mask"]
const OUTFITS:=["dress","skirt","miniskirt"]
const MDL:={
	"body":"d916863f801d0894009fad43c587ae630bf05556f484ebae4803734bd15c8af7",
	"hair":"8da09c905227ddc8eef73a3f83594a4eb1c3a6d5304ee41ba5471bef834bc716",
	"dress":"be03e608fc7fc0316a5441e65d01cef355e076b4eff17dd5b57fbf4defb35fdf",
	"skirt":"b753091a9e32e84cb81ae182df0b6c7c341feb0e51e5b2e190eccff2f92b397b",
	"miniskirt":"55d13238fe67c4ead4ac6c2cb6c4ac43d7f2275d722021af5ce030e93cf1745d",
	"mask":"8cb588d2e45268c79d83632cae4e0545d953025c9ea48a3bf42a1975a74db0f2"}

static func policy_error(value) -> String:
	if not value is Dictionary or value.size()!=3 or value.get("origin")!="retain_prepared_roots" or not value.get("units_already_in_glb") is bool or not value.units_already_in_glb:return "Use one explicit prepared-origin/unit policy for every part."
	var factor=value.get("metres_per_source_unit")
	if not (factor is int or factor is float) or not is_finite(float(factor)) or factor<=0 or factor>1:return "Use finite positive common source units."
	return ""

static func indexed(world: Dictionary) -> Dictionary:
	var result:={}
	for row in world.objects:result[row.id]=row
	return result

static func fresh_root(row: Dictionary) -> bool:
	return row.get("format")=="studio_model_1" and row.get("parent_id")=="" and row.get("position")==[0,0,0] and row.get("rotation_xyzw")==[0,0,0,1] and row.get("scale")==1 and row.get("pose_keys")==[] and row.get("start_frame")==0 and not row.has("asset_basis") and not row.get("metadata",{}).has("import_basis_lineage")

static func assemble(world: Dictionary, group: Dictionary, supplied: Dictionary, policy: Dictionary, duration: int, root_scale=1.) -> Dictionary:
	var why: String=World.validate(world,duration)
	if not why.is_empty():return {"error":why}
	why=policy_error(policy)
	if not why.is_empty():return {"error":why}
	if supplied.size()!=ROLES.size():return {"error":"Supply the six explicitly reviewed model families, not their sidecars."}
	if not Model.scale_valid(root_scale):return {"error":"Whole-character scale is out of range."}
	why=Model.validate(group,duration)
	if not why.is_empty() or group.get("kind")!="group" or not fresh_root(group):return {"error":"Use a fresh real inert group asset at the shared origin."}
	var result: Dictionary=world.duplicate(true)
	var ids: Dictionary=indexed(world)
	if not World.identifier(group.get("id")) or ids.has(group.id) or world.objects.size()+7>World.MAX_OBJECTS:return {"error":"Bundle IDs must be new and the world must fit seven new entries."}
	ids[group.id]=true
	var members:=[]
	var rows:=[]
	for role in ROLES:
		var incoming=supplied.get(role)
		if not incoming is Dictionary or incoming.get("source_mdl_sha256")!=MDL[role] or incoming.get("unit_policy")!=policy or not incoming.get("row") is Dictionary:return {"error":"A reviewed model family or common conversion policy changed."}
		var row: Dictionary=incoming.row
		why=Model.validate(row,duration)
		if not why.is_empty() or row.get("kind")!="model" or not fresh_root(row):return {"error":"Parts must be fresh independent models; keep their prepared origins and one shared scale."}
		if not World.identifier(row.get("id")) or ids.has(row.id):return {"error":"Every bundle member needs a distinct new ID."}
		ids[row.id]=true
		var part: Dictionary=row.duplicate(true)
		part.parent_id=group.id
		part.visible=role in ["body","hair"]
		rows.append(part)
		members.append({"role":role,"id":part.id,"sha256":part.sha256,"source_mdl_sha256":MDL[role]})
	var root: Dictionary=group.duplicate(true)
	root.scale=root_scale
	root.metadata["character_parts"]={"format":FORMAT,"members":members,"unit_policy":policy.duplicate(true),"height_reference_role":"body","scale_owner":"root_only","independent_rigs":true,"bone_following":false}
	result.objects.append(root);result.objects.append_array(rows)
	why=World.validate(result,duration)
	return {"world":result,"root_id":root.id} if why.is_empty() else {"error":why}

static func describe(world: Dictionary, selected: String, duration: int) -> Dictionary:
	var why: String=World.validate(world,duration)
	if not why.is_empty():return {"error":why}
	var ids: Dictionary=indexed(world)
	if not ids.has(selected):return {"error":"Select a bundled character or one of its direct parts."}
	var chosen: Dictionary=ids[selected]
	var root: Dictionary=chosen if chosen.kind=="group" else ids.get(chosen.parent_id,{})
	var raw=root.get("metadata",{}).get("character_parts",{})
	if not raw is Dictionary:return {"error":"The bundle metadata must be an explicit record."}
	var data: Dictionary=raw
	if root.get("kind")!="group" or data.get("format")!=FORMAT or not data.get("independent_rigs") is bool or not data.independent_rigs or not data.get("bone_following") is bool or data.bone_following or data.get("scale_owner")!="root_only" or data.get("height_reference_role")!="body" or not policy_error(data.get("unit_policy")).is_empty():return {"error":"This is not an explicitly assembled character."}
	var members=data.get("members")
	if not members is Array or members.size()!=6:return {"error":"The bundle member list changed."}
	var roles:={};var seen:={};var parts:=[]
	for member in members:
		if not member is Dictionary or not member.get("role") in ROLES or roles.has(member.role) or not ids.has(member.get("id")) or seen.has(member.id):return {"error":"A bundle member is missing or duplicated."}
		var row: Dictionary=ids[member.id]
		if row.kind!="model" or row.parent_id!=root.id or row.sha256!=member.get("sha256") or member.get("source_mdl_sha256")!=MDL[member.role]:return {"error":"A bundled asset or parent changed. Rebuild its explicit membership first."}
		roles[member.role]=true;seen[member.id]=true
		parts.append({"role":member.role,"row":row.duplicate(true)})
	for row in world.objects:
		if row.parent_id==root.id and not seen.has(row.id):return {"error":"An unlisted direct part was attached. Review membership before editing the bundle."}
	return {"root_id":root.id,"name":root.name,"parts":parts}

static func visibility_edit(world: Dictionary, selected: String, values: Dictionary, frame, duration: int) -> Dictionary:
	var bundle: Dictionary=describe(world,selected,duration)
	if bundle.has("error"):return bundle
	if not Model.integer(frame,0,duration):return {"error":"Choose a whole frame inside the scene."}
	var allowed:={}
	for part in bundle.parts:allowed[part.row.id]=part.row
	if values.is_empty():return {"error":"Choose at least one part."}
	var before:={};var after:={}
	for id in values:
		if not allowed.has(id) or not values[id] is bool:return {"error":"Visibility may change only explicit members of this character."}
		var row: Dictionary=allowed[id]
		if Visibility.target(row,frame)==values[id]:continue
		var changed: Dictionary=Clips.promote(row)
		if not Model.ShapeAnimation.has_data(changed):changed.format=Visibility.FORMAT
		if not changed.has("visibility_keys"):changed["visibility_keys"]=[]
		Visibility.put(changed,frame,values[id])
		var why: String=Model.validate(changed,duration)
		if not why.is_empty():return {"error":why}
		before[id]=row.duplicate(true);after[id]=changed
	return {"type":"world_objects","before":before,"after":after}

static func outfit_edit(world: Dictionary, selected: String, outfit: Array, frame, duration: int) -> Dictionary:
	var bundle: Dictionary=describe(world,selected,duration)
	if bundle.has("error"):return bundle
	var seen:={}
	for role in outfit:
		if not role in OUTFITS or seen.has(role):return {"error":"Choose explicit, distinct clothing parts."}
		seen[role]=true
	var values:={}
	for part in bundle.parts:
		if part.role in OUTFITS:values[part.row.id]=seen.has(part.role)
	return visibility_edit(world,selected,values,frame,duration)

static func suggest_body_scale(converted_body_height) -> Dictionary:
	if not (converted_body_height is int or converted_body_height is float) or not is_finite(float(converted_body_height)) or converted_body_height<=0:return {"error":"Measure the complete converted body once."}
	var factor: float=1.8288/float(converted_body_height)
	if not Model.scale_valid(factor):return {"error":"Body reference factor is outside the model scale range."}
	return {"root_scale_suggestion":factor,"target_metres":1.8288,"applied":false,"classification_qualified":false,"per_part_height_normalization":false}
