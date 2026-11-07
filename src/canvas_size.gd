extends RefCounted
# Bounded native raster profiles; legacy projects retain their existing pixels.
const PROFILES={"1080p":Vector2i(1920,1080),"720p":Vector2i(1280,720),"540p":Vector2i(960,540)}
static func profile(video) -> String:
 if not video is Dictionary:return ""
 var width=video.get("width");var height=video.get("height")
 if not (width is int or width is float) or not (height is int or height is float):return ""
 for id in PROFILES:
  if width==PROFILES[id].x and height==PROFILES[id].y:return id
 return ""
static func error(video) -> String:
 return "" if not profile(video).is_empty() else "Choose a supported native canvas: 1920 x 1080, 1280 x 720 or 960 x 540."
static func size(video) -> Vector2i:return PROFILES.get(profile(video),Vector2i.ZERO)
static func delivery(video: Dictionary) -> String:return str(video.get("output_size",profile(video)))
