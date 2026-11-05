extends RefCounted
const Timeline=preload("res://src/timeline.gd")
const ID="advanced-interpolation-v1"
const DEFINITION={"title":"Advanced · Interpolation and cuts","steps":[
	"Turn on Advanced in the blue top bar. This chapter compares camera timing without changing your drawings.",
	"In Scene / camera, keep a camera key at frame 0. Move the view at frame 24 and Save camera key. Give the two views visibly different positions.",
	"In Draw seek 0 to reload the saved shot. Switch to Scene / camera, choose hold and replace its key. Return to Draw and seek 12: the camera waits, then cuts at frame 24.",
	"In Draw seek 0, switch to Scene / camera, choose linear and replace its key. Return to Draw and seek 6: the camera has travelled a quarter of the way to frame 24.",
	"In Draw seek 0, switch to Scene / camera, choose ease and replace its key. Return to Draw and seek 6: it starts more slowly than linear, then catches up. Key poses and painted holds stay unchanged."
],"hints":[
	"Advanced reveals more controls on the same project. Choose Scene / camera to reach the camera controls.",
	"Seek frame 24 with the frame control, move the camera with Ctrl + left-drag and WASD, then Save camera key. Navigating without saving is only a temporary view.",
	"Draw reloads recorded shots; Scene keeps a temporary view even when seeking. In Draw seek 0, switch to Scene, select hold, Save camera key and confirm. Return to Draw and seek 12. The outgoing key controls the interval; changing the menu alone does not record it.",
	"In Draw seek 0, switch to Scene, choose linear and Save camera key again. Confirm replacement, return to Draw and seek 6. Linear advances at constant speed between the saved views.",
	"In Draw seek 0, switch to Scene, choose ease, Save camera key and confirm. Return to Draw and seek 6. Ease accelerates and slows down between keys. Frame 24 still lands exactly on its key; raster cels keep their own exposures."
]}
static func pair(lesson) -> Array:
	var a: Dictionary=lesson.key_at(0);var b: Dictionary=lesson.key_at(24)
	if a.is_empty() or b.is_empty() or Timeline.vector(a.position).distance_to(Timeline.vector(b.position))<.3:return []
	# Additional keys inside this interval change what the learner is comparing.
	for key in lesson.app.keys:
		if key.frame>0 and key.frame<24:return []
	return [a,b]
static func satisfied(lesson) -> bool:
	if lesson.step==0:return lesson.app.advanced_mode
	if lesson.step<1 or lesson.step>4:return false
	var keys:=pair(lesson)
	if keys.is_empty():return false
	if lesson.step==1:return lesson.app.frame==24
	var modes:=["hold","linear","ease"]
	var at:=12 if lesson.step==2 else 6
	if lesson.app.mode.selected!=0 or lesson.app.frame!=at or keys[0].interpolation!=modes[lesson.step-2]:return false
	var progress:=0.0 if lesson.step==2 else .25 if lesson.step==3 else .15625
	var expected:=Timeline.vector(keys[0].position).lerp(Timeline.vector(keys[1].position),progress)
	return Timeline.sample(lesson.app.keys,at).position.distance_to(expected)<.0001 and lesson.app.renderer.camera.position.distance_to(expected)<.0001
static func highlight(lesson) -> Control:
	if lesson.step==0:return lesson.find_button("Advanced")
	if lesson.step==1:return lesson.find_button("Save camera key")
	return lesson.app.interpolation
