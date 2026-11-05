extends RefCounted
# Immutable source-time contact edits over ordinary animation pieces.
const Contact=preload("res://src/contact_animation.gd")
const Model=Contact.Body.Model
const Clips=Model.Clips

static func empty_piece(data: Dictionary,start: int,length: int) -> Dictionary:
	var piece:=Clips.clip(data,start,length,0,[])
	piece["body_rest_keys"]=[];piece["body_placeholder"]=false;piece["body_untrimmed"]=false
	return piece

static func replace_track(track: Dictionary,first: int,last: int,target: Dictionary) -> Dictionary:
	var segments:=[]
	for old in track.get("segments",[]):
		if old.to<=first or old.from>=last:segments.append(old.duplicate(true));continue
		if old.from<first:
			var left: Dictionary=old.duplicate(true);left.to=first;segments.append(left)
		if old.to>last:
			var right: Dictionary=old.duplicate(true);right.from=last
			right.id=str(ResourceUID.create_id());segments.append(right)
	if not target.is_empty():
		var added:=target.duplicate(true);added.from=first;added.to=last;segments.append(added)
	segments.sort_custom(func(a,b):return a.from<b.from)
	return Contact.Contacts.track(segments)

static func edit(data: Dictionary,first: int,last: int,target: Dictionary,duration: int) -> Dictionary:
	if first< int(data.get("start_frame",0)) or first<0 or last<=first or last>duration+1:return {"error":"Choose a range within this object's presence and project frames."}
	if target.is_empty():
		var any_contact:=false
		for frame in range(first,last):any_contact=any_contact or not Contact.Contacts.active(data.get("animation_clips",[]),frame).is_empty()
		if not any_contact:return {"data":data.duplicate(true),"changed":false}
	else:
		var test:=target.duplicate(true);test.from=0;test.to=1
		var error:=Contact.Contacts.validate(Contact.Contacts.track([test]))
		if not error.is_empty():return {"error":error}
	var result:=Contact.promote(data,duration)
	if result.has("error"):return result
	if result.animation_clips.is_empty():return {"error":"Add an animation block before planting feet."}
	var after: Dictionary=Contact.Contacts.active(result.animation_clips,last)
	for boundary in [first,last]:
		var index:=Clips.index_at(result,boundary)
		if index>=0 and result.animation_clips[index].start!=boundary:
			var divided: Dictionary=load("res://src/root_component_document.gd").edit_clip(result,"split","",boundary,duration) if result.get("format")=="studio_model_9" else Clips.split(result,boundary)
			if divided.has("error"):return divided
			result=divided.data
	# Contact-only gaps own no body/expression controls, preserving their interpolation.
	var additions:=[];var cursor:=first
	for piece in result.animation_clips:
		if piece.start+piece.length<=first or piece.start>=last:continue
		if piece.start>cursor:additions.append(empty_piece(result,cursor,int(piece.start)-cursor))
		cursor=maxi(cursor,int(piece.start)+int(piece.length))
	if cursor<last:additions.append(empty_piece(result,cursor,last-cursor))
	if last<=duration and Clips.index_at(result,last)<0:
		var boundary:=empty_piece(result,last,1)
		if not after.is_empty():boundary["foot_contacts"]=replace_track({},0,1,after)
		additions.append(boundary)
	if result.animation_clips.size()+additions.size()>Clips.MAX_CLIPS:return {"error":"This contact range needs more animation pieces than the32-piece limit. Choose a shorter range."}
	result.animation_clips.append_array(additions);result.animation_clips.sort_custom(func(a,b):return a.start<b.start)
	for piece in result.animation_clips:
		if piece.start<first or piece.start>=last:continue
		var track:=replace_track(piece.get("foot_contacts",{}),int(piece.source_in),int(piece.source_in)+int(piece.length),target)
		piece["foot_contacts"]=track;piece.auto_extend=false;piece["body_untrimmed"]=false
	var error: String=load("res://src/root_component_document.gd").validate(result,duration) if result.get("format")=="studio_model_9" else Model.validate(result,duration)
	return {"error":error} if not error.is_empty() else {"data":result,"changed":result!=data}
