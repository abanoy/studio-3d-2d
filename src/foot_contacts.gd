extends RefCounted
# Versioned contact track. Development Model7 accepts it; canonical activation is gated.
const IK=preload("res://src/limb_ik.gd")
const Hold=preload("res://src/foot_hold.gd")
const T=preload("res://src/timeline.gd")
const FORMAT:="studio_foot_contacts_1"
const CORRECTION_FORMAT:="studio_foot_contacts_2"
const MAX_SEGMENTS:=64
const MAX_SOURCE:=100001

static func integer(value) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and value==floor(value) and value>=0 and value<=MAX_SOURCE

static func vector_valid(value,size: int) -> bool:
	if not value is Array or value.size()!=size:return false
	for n in value:
		if not (n is int or n is float) or not is_finite(float(n)) or absf(n)>100000:return false
	return true

static func track(segments: Array) -> Dictionary:
	var format:=FORMAT
	for segment in segments:
		if not segment is Dictionary or not segment.get("feet") is Array:continue
		for foot in segment.feet:
			if foot is Dictionary and (foot.has("pole") or foot.has("flip_bend")):format=CORRECTION_FORMAT
	return {"format":format,"segments":segments}

static func validate(track) -> String:
	if not track is Dictionary or not track.get("format") in [FORMAT,CORRECTION_FORMAT] or not track.get("segments") is Array or track.segments.size()>MAX_SEGMENTS:return "Invalid foot contact track."
	var seen:={};var end:=-1
	for segment in track.segments:
		if not segment is Dictionary or not segment.get("id") is String or segment.id.is_empty() or segment.id.length()>128 or seen.has(segment.id):return "Invalid foot contact identity."
		seen[segment.id]=true
		if not integer(segment.get("from")) or not integer(segment.get("to")) or segment.to<=segment.from or segment.from<end:return "Invalid or overlapping foot contact range."
		end=int(segment.to)
		if not segment.get("feet") is Array or segment.feet.size()!=2:return "A planted pair requires two feet."
		var ids:={}
		for foot in segment.feet:
			if not foot is Dictionary or not foot.get("ids") is Array or foot.ids.size()!=3 or not vector_valid(foot.get("position"),3) or not vector_valid(foot.get("rotation_xyzw"),4):return "Invalid foot contact target."
			if (foot.has("pole") or foot.has("flip_bend")) and track.format!=CORRECTION_FORMAT:return "Knee corrections require foot contact version2."
			if foot.has("pole") and not vector_valid(foot.pole,3):return "Invalid knee direction target."
			if foot.has("flip_bend") and not foot.flip_bend is bool:return "Invalid knee bend direction."
			for id in foot.ids:
				if not id is String or id.is_empty() or id.length()>512 or ids.has(id):return "Invalid or shared foot contact bone."
				ids[id]=true
			var q: Array=foot.rotation_xyzw
			if absf(Vector4(q[0],q[1],q[2],q[3]).length_squared()-1)>0.00001:return "Foot contact orientation must be normalized."
	return ""

static func capture(rig: RefCounted, from: int, to: int, id: String) -> Dictionary:
	var captured:=Hold.capture(rig,"@root")
	if captured.has("error"):return captured
	var feet:=[]
	for foot in captured.feet:
		var p: Vector3=foot.position;var q: Quaternion=foot.rotation
		feet.append({"ids":foot.limb.ids.duplicate(),"position":[p.x,p.y,p.z],"rotation_xyzw":[q.x,q.y,q.z,q.w]})
	var track:={"format":FORMAT,"segments":[{"id":id,"from":from,"to":to,"feet":feet}]}
	var error:=validate(track)
	return {"error":error} if not error.is_empty() else track

static func at(track: Dictionary, source_frame: float) -> Dictionary:
	for segment in track.segments:
		if source_frame>=segment.from and source_frame<segment.to:return segment.duplicate(true)
	return {}

static func active(pieces: Array, frame: float) -> Dictionary:
	if not is_finite(frame) or frame<0:return {}
	var previous: Dictionary={};var following: Dictionary={}
	for piece in pieces:
		if frame>=piece.start and frame<piece.start+piece.length:
			return at(piece.foot_contacts,float(piece.source_in)+frame-piece.start) if piece.has("foot_contacts") else {}
		if piece.start+piece.length<=frame:previous=piece
		elif piece.start>frame and following.is_empty():following=piece
	if previous.is_empty():return {}
	var left:=at(previous.foot_contacts,float(previous.source_in)+previous.length-1) if previous.has("foot_contacts") else {}
	if following.is_empty():return left
	var right:=at(following.foot_contacts,float(following.source_in)) if following.has("foot_contacts") else {}
	# A split/move gap can retain the SAME declared contact, never invent a new one.
	return left if same_contact(left,right) else {}

static func same_contact(a: Dictionary,b: Dictionary) -> bool:
	if a.is_empty() or b.is_empty() or a.id!=b.id or a.feet.size()!=b.feet.size():return false
	for i in range(a.feet.size()):
		if a.feet[i].ids!=b.feet[i].ids or T.vector(a.feet[i].position)!=T.vector(b.feet[i].position) or T.quaternion(a.feet[i].rotation_xyzw)!=T.quaternion(b.feet[i].rotation_xyzw):return false
		if a.feet[i].get("flip_bend",false)!=b.feet[i].get("flip_bend",false) or a.feet[i].has("pole")!=b.feet[i].has("pole"):return false
		if a.feet[i].has("pole") and T.vector(a.feet[i].pole)!=T.vector(b.feet[i].pole):return false
	return true

static func slice(pieces: Array,first: int,last: int,source_in: int) -> Dictionary:
	# Record's half-open integer interval maps to its new take's source address.
	# Preserve exact targets across ordinary pieces, bridging gaps and held tails.
	var segments:=[];var seen:={};var previous: Dictionary={}
	for frame in range(first,last):
		var current:=active(pieces,frame)
		if current.is_empty():continue
		var at:=source_in+frame-first
		if not segments.is_empty() and segments[-1].to==at and same_contact(previous,current):
			segments[-1].to=at+1;continue
		previous=current.duplicate(true)
		if seen.has(current.id):current.id=str(ResourceUID.create_id())
		seen[current.id]=true;current.from=at;current.to=at+1;segments.append(current)
	return track(segments)

static func check_bindings(rig: RefCounted, track: Dictionary) -> String:
	var error:=validate(track)
	if not error.is_empty():return error
	var legs: Array=rig.contact_legs() if rig.has_method("contact_legs") else Hold.chains(rig)
	if legs.size()!=2:return "This rig has no validated pair of legs for foot contacts."
	for segment in track.segments:
		for i in range(2):
			if segment.feet[i].ids!=legs[i].ids:return "Foot contact bones do not match the imported leg chains."
	return ""

static func apply_pose(rig: RefCounted, pose: Dictionary) -> void:
	var updated:=[]
	for id in rig.order:
		var bone: Dictionary=rig.bones[id];var base: Transform3D=bone.base
		var delta: Dictionary=pose.get(id,{"position":[0,0,0],"rotation_xyzw":[0,0,0,1]})
		bone.skeleton.set_bone_pose_position(bone.index,base.origin+T.vector(delta.position))
		bone.skeleton.set_bone_pose_rotation(bone.index,base.basis.get_rotation_quaternion()*T.quaternion(delta.rotation_xyzw))
		bone.skeleton.set_bone_pose_scale(bone.index,base.basis.get_scale())
		if not bone.skeleton in updated:updated.append(bone.skeleton)
	for skeleton in updated:skeleton.force_update_all_bone_transforms()

static func resolve(rig: RefCounted, pose: Dictionary, segment: Dictionary) -> Dictionary:
	# The caller evaluates the ordinary world/root first. Never edit model dictionaries,
	# author keys, use prior solver output, or advance wall-clock simulation here.
	if segment.is_empty():
		apply_pose(rig,pose)
		return {"pose":pose.duplicate(true)}
	var descriptor:=track([segment])
	var error:=check_bindings(rig,descriptor)
	if not error.is_empty():return {"error":error}
	var result:=pose.duplicate(true);apply_pose(rig,result)
	for i in range(2):
		var foot: Dictionary=segment.feet[i]
		var limb:={"ids":foot.ids,"role":"leftFoot" if i==0 else "rightFoot"}
		var solved:=IK.solve(rig,limb,T.vector(foot.position),foot.get("flip_bend",false),result,T.vector(foot.pole) if foot.has("pole") else null)
		if solved.has("error") or solved.get("clamped",false):
			apply_pose(rig,pose)
			return {"error":solved.get("error","Planted foot is out of reach at this frame.")}
		result=solved.pose
		# Contact orientation is world-space, independent of root/parent rotation.
		var id: String=foot.ids[2];var bone: Dictionary=rig.bones[id]
		var parent: int=bone.skeleton.get_bone_parent(bone.index)
		var parent_basis: Basis=bone.skeleton.get_bone_global_pose(parent).basis
		# First apply the solved upper and lower leg before computing the foot rotation.
		apply_pose(rig,result);parent_basis=bone.skeleton.get_bone_global_pose(parent).basis
		var local_basis: Basis=parent_basis.inverse()*bone.skeleton.global_basis.inverse()*Basis(T.quaternion(foot.rotation_xyzw)).scaled(Vector3.ONE*rig.bone_transform(id).basis.get_scale().x)
		var q: Quaternion=(bone.base.basis.get_rotation_quaternion().inverse()*local_basis.orthonormalized().get_rotation_quaternion()).normalized()
		result[id].rotation_xyzw=[q.x,q.y,q.z,q.w];apply_pose(rig,result)
	for foot in segment.feet:
		var actual: Transform3D=rig.bone_transform(foot.ids[2])
		if actual.origin.distance_to(T.vector(foot.position))>0.0002 or absf(actual.basis.orthonormalized().get_rotation_quaternion().dot(T.quaternion(foot.rotation_xyzw)))<0.99999:
			apply_pose(rig,pose);return {"error":"The contact solver could not hold both feet at this frame."}
	return {"pose":result}
