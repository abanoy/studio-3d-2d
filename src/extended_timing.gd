extends RefCounted
const Timing=preload("res://src/video_timing.gd")
const LEGACY_FRAMES=240
const MAX_FRAMES=7200
const MAX_SECONDS=60
const LEGACY_PLACEMENT=1000240
const MAX_PLACEMENT=1000000+MAX_FRAMES
static func max_frames(video: Dictionary) -> int:
	if not Timing.error(video.get("fps_num"),video.get("fps_den")).is_empty():return LEGACY_FRAMES
	# Retain the legacy 240-frame domain at unusual slow rates. Extended scenes
	# are additionally bounded by the existing 60-second audio envelope.
	return maxi(LEGACY_FRAMES,mini(MAX_FRAMES,int(video.fps_num)*MAX_SECONDS/int(video.fps_den)))
static func video_error(video) -> String:
	if not video is Dictionary:return "Missing project timing."
	var why:=Timing.error(video.get("fps_num"),video.get("fps_den"))
	if not why.is_empty():return why
	if not Timing.whole(video.get("duration_frames"),MAX_FRAMES):return "Scene length must be a supported whole frame count."
	if video.duration_frames>max_frames(video):return "Longer scenes support up to 60 seconds and 7200 frames. Shorten the scene before lowering its frame rate."
	return ""
static func origin_extended(layers) -> bool:
	if not layers is Array:return false
	for layer in layers:
		if layer is Dictionary and layer.get("origin") is Dictionary and layer.origin.get("format") in ["studio_drawing_origin_3","studio_drawing_origin_4"]:return true
	return false
static func extended_keys(clips) -> bool:
	if not clips is Array:return false
	for clip in clips:
		if not clip is Dictionary or not clip.get("keys") is Array:continue
		for key in clip.keys:
			if key is Dictionary and (key.get("frame") is int or key.get("frame") is float) and key.frame>LEGACY_PLACEMENT:return true
	return false
static func required(document: Dictionary) -> bool:
	var video=document.get("video",{})
	if video is Dictionary and (video.get("duration_frames") is int or video.get("duration_frames") is float) and video.duration_frames>LEGACY_FRAMES:return true
	if origin_extended(document.get("layers",[])):return true
	var graph=document.get("sequence_graph",{})
	if graph is Dictionary:
		if extended_keys(graph.get("clips",[])):return true
		if graph.get("assets") is Array:
			for asset in graph.assets:
				if not asset is Dictionary:continue
				if extended_keys(asset.get("clips",[])):return true
				var scene=asset.get("scene",{})
				if scene is Dictionary and (scene.get("schema_version")==8 or origin_extended(scene.get("layers",[]))):return true
	return false
static func unwrap(value: Dictionary) -> Dictionary:
	var version=value.get("timing_content_schema_version")
	if not (version is int or version is float) or not is_finite(float(version)) or version!=floor(version) or not int(version) in [3,4,5,6,7]:return {"error":"Invalid extended-timing content schema."}
	var why:=video_error(value.get("video"))
	if not why.is_empty():return {"error":why}
	var base:=value.duplicate(true);base.schema_version=int(version);base.erase("timing_content_schema_version")
	return {"base":base}
static func child_schema(scene: Dictionary) -> int:
	if scene.get("schema_version")==8:
		var decoded:=unwrap(scene)
		return int(decoded.base.schema_version) if not decoded.has("error") else -1
	var value=scene.get("schema_version")
	return int(value) if Timing.whole(value,7) else -1
