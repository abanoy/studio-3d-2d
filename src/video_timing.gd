extends RefCounted
const PRESETS:=[[12,1],[15,1],[24,1],[24000,1001],[25,1],[30,1],[30000,1001],[48,1],[50,1],[60,1],[60000,1001],[120,1]]
static func whole(value,maximum: int) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and value==floor(value) and value>=1 and value<=maximum
static func error(numerator,denominator) -> String:
	if not whole(numerator,120000) or not whole(denominator,1001) or numerator>120*denominator:return "Invalid project frame rate (positive rational rate, at most120fps)."
	return ""
static func label(numerator,denominator) -> String:
	return ("%.3f" % (float(numerator)/float(denominator))).rstrip("0").trim_suffix(".")
static func preset_index(video: Dictionary) -> int:
	for index in range(PRESETS.size()):
		if video.fps_num==PRESETS[index][0] and video.fps_den==PRESETS[index][1]:return index
	return -1
