extends RefCounted
# Correct one foot without flattening body curves, the other foot, or release gaps.
const Ranges=preload("res://src/contact_ranges.gd")
const Contacts=Ranges.Contact.Contacts
const T=Contacts.T

static func edit(data: Dictionary,first: int,last: int,foot_index: int,changes: Dictionary,duration: int) -> Dictionary:
	if foot_index<0 or foot_index>1 or first<int(data.get("start_frame",0)) or last<=first or last>duration+1:return {"error":"Choose a foot and a range inside this object's presence."}
	for field in changes:
		if not field in ["position","rotation_xyzw","pole","flip_bend"]:return {"error":"Unsupported foot correction."}
		if field=="flip_bend" and changes[field]!=null and not changes[field] is bool:return {"error":"Invalid knee bend direction."}
	var track:=Contacts.slice(data.get("animation_clips",[]),first,last,first)
	if track.segments.is_empty():return {"error":"Plant feet in this range before correcting a foot."}
	var result:=data.duplicate(true);var changed:=false
	for segment in track.segments:
		var target: Dictionary=segment.duplicate(true);var foot: Dictionary=target.feet[foot_index]
		for field in changes:
			if changes[field]==null or field=="flip_bend" and changes[field]==false:foot.erase(field)
			else:foot[field]=changes[field].duplicate(true) if changes[field] is Array else changes[field]
		var error:=Contacts.validate(Contacts.track([target]))
		if not error.is_empty():return {"error":error}
		if Contacts.same_contact(segment,target):continue
		target.id=str(ResourceUID.create_id())
		var update:=Ranges.edit(result,int(segment.from),int(segment.to),target,duration)
		if update.has("error"):return update
		result=update.data;changed=changed or update.changed
	return {"data":result,"changed":changed}
