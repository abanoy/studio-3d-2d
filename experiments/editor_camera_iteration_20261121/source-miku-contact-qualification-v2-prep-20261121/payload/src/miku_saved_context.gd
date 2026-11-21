extends RefCounted
# Fixture-only context admission: dense stored pose is not a count of edited joints.
const MIKU_SHA="cc040e35f47280599ea083ac78d36855c99861791b0e66a28e091c12655c5aaf"
const STORED_CHANNELS:=156
const CHANGED_CHANNELS:=6
static func same_domain(a: Dictionary,b: Dictionary) -> bool:
	if a.size()!=b.size():return false
	for id in a:
		if not b.has(id):return false
	return true
static func at_zero(value) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and value==0
static func assess(data: Dictionary,draft: Dictionary,timeline: Dictionary,frame,running,recording) -> Dictionary:
	var stored=data.get("pose");var base=data.get("body_base_pose")
	var fields: Dictionary={"loaded_frame":frame,"saved_draft_frame":data.get("draft_frame"),"stored_pose_channels":stored.size() if stored is Dictionary else -1,"body_base_channels":base.size() if base is Dictionary else -1,"draft_sample_channels":draft.size(),"timeline_sample_channels":timeline.size(),"changed_draft_channels":-1,"physics_running":running,"recording_active":recording,"source_identity_matches":data.get("sha256")==MIKU_SHA and data.get("format")=="studio_model_6","saved_frame_matches":at_zero(frame) and at_zero(data.get("draft_frame")),"dense_domains_match":false,"draft_matches_saved_pose":false,"timeline_matches_saved_body_base":false,"idle_matches":running is bool and recording is bool and not running and not recording,"accepted":false}
	if not stored is Dictionary or not base is Dictionary:return fields
	fields.dense_domains_match=stored.size()==STORED_CHANNELS and same_domain(stored,base) and same_domain(stored,draft) and same_domain(stored,timeline)
	fields.draft_matches_saved_pose=draft==stored
	fields.timeline_matches_saved_body_base=timeline==base
	var ids: Dictionary={}
	for id in draft:ids[id]=true
	for id in timeline:ids[id]=true
	var changed:=0
	for id in ids:
		if not draft.has(id) or not timeline.has(id) or draft.get(id)!=timeline.get(id):changed+=1
	fields.changed_draft_channels=changed
	fields.accepted=fields.source_identity_matches and fields.saved_frame_matches and fields.dense_domains_match and fields.draft_matches_saved_pose and fields.timeline_matches_saved_body_base and fields.idle_matches and changed==CHANGED_CHANNELS
	return fields
