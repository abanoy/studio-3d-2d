extends RefCounted
# Missing settings preserve the original studio illumination of older projects.
const MODES: Array[String]=["unshaded","lit","studio"]
static func mode(video: Dictionary) -> String:return str(video.get("lighting_mode","studio"))
static func validate(video: Dictionary) -> String:
	if video.has("lighting_mode") and (not video.lighting_mode is String or not video.lighting_mode in MODES):return "Unknown lighting mode. Choose Unshaded, Lit or Studio light."
	return preload("res://src/scene_lighting_document.gd").error(video.scene_lighting) if video.has("scene_lighting") else ""
