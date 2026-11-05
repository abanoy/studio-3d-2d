extends RefCounted
# Versioned beginner tasks; older three-task courses retain their identities.
const ID:="first-movie-v1"
const Timeline=preload("res://src/timeline.gd")
const DEFINITION={"title":"Basic · Your first movie","steps":[
	"Add the included practice map to this empty scene.",
	"Add the practice figure. Let Physics run, then switch Physics off to freeze it.",
	"Select the figure. Right-click it and choose Reset pose to stand it up.",
	"At frame 0, move the camera a little with Ctrl + left-drag and WASD.",
	"Save this new camera view at frame 0 with Save camera key.",
	"At frame 24, raise the figure’s left hand above its shoulder. Pose edits key automatically.",
	"At frame 24, move the camera closer and Save camera key.",
	"At frame 24, choose Draw and add a visible mark on Ink.",
	"Play your scene, then pause. The camera, pose and drawing share one timeline.",
	"Split the figure’s block at frame 12. Drag its right-hand piece to frame 28.",
	"Save if you want to keep this practice. Export movie to finish; saving is optional."],"hints":[
	"Add practice map opens the normal file picker in the included examples folder. Choose Practice room.glb.",
	"Choose Practice figure.glb. Compatible imports begin with Physics on. Try grabbing it, then turn Physics off; nothing is recorded without Record.",
	"Use the left World tree to select the figure. Right-click its visible surface and choose Reset pose. This records a neutral pose at frame 0.",
	"Choose Scene / camera. Hold Ctrl and the left mouse button, then use WASD for a short move. Release the mouse to stop.",
	"Choose Scene / camera and Save camera key [K]. Confirm replacing the frame 0 key. Navigation alone changes only your temporary view.",
	"Set frame 24. Hold Alt, select the left upper-arm joint and rotate upward. A hand above the shoulder counts only with a real frame 24 pose key.",
	"Choose Scene / camera. Move toward the figure, then Save camera key at frame 24. This second shot interpolates from your frame 0 key.",
	"Choose Draw, select Ink, then New drawing if needed. Paint a mark. Drawing does not modify the figure, room or camera keys.",
	"Click Play (or Space while the canvas has focus), watch some movement, then pause. You can scrub any frame afterward.",
	"On the figure’s timeline row, right-click inside its block at frame 12 and choose Split. Drag the right piece’s body until it starts at 28.",
	"Save project chooses a personal HAS file. Export movie uses its folder; without a save it asks for an output folder. Wait for successful export. No need to keep disposable practice." ]}

static func object(lesson,kind: String) -> RefCounted:
	if not lesson.app.renderer.world_runtime:return null
	var hash: String=lesson.asset_digest("Practice figure.glb" if kind=="model" else "Practice room.glb")
	if hash.is_empty():return null
	for rig in lesson.app.renderer.world_runtime.instances.values():
		if rig.data.kind==kind and rig.data.sha256==hash:return rig
	return null

static func observe(lesson) -> void:
	var app=lesson.app
	if lesson.step==1:
		var rig:=object(lesson,"model")
		if rig and app.physics_editor.body_active(rig.data.id):lesson.observed["physics_seen"]=true
	if lesson.step==8 and app.playing:lesson.observed["preview_seen"]=true

static func satisfied(lesson) -> bool:
	var app=lesson.app
	var rig:=object(lesson,"model")
	match lesson.step:
		0:return object(lesson,"environment")!=null
		1:return rig!=null and lesson.observed.get("physics_seen",false) and not app.physics_editor.body_active(rig.data.id)
		2:
			if not rig or app.world_selection.selected!=rig.data.id or app.frame!=0:return false
			for value in rig.sample(0,true).values():
				if Timeline.vector(value.position).length()>.005 or Timeline.quaternion(value.rotation_xyzw).get_angle()>.02:return false
			return true
		3:
			if app.frame!=0 or lesson.baseline.is_empty():return false
			var original:=basis(lesson.baseline)
			return app.renderer.camera.position.distance_to(Timeline.vector(lesson.baseline.origin))>=.25 or app.renderer.camera.basis.get_rotation_quaternion().angle_to(original.get_rotation_quaternion())>=.15
		4:
			var key: Dictionary=lesson.key_at(0)
			return app.frame==0 and not key.is_empty() and not lesson.baseline.is_empty() and Timeline.vector(key.position).distance_to(Timeline.vector(lesson.baseline.origin))<.01 and Timeline.quaternion(key.rotation_xyzw).angle_to(basis(lesson.baseline).get_rotation_quaternion())<.01
		5:return rig!=null and lesson.raised_arm(rig)
		6:return lesson.changed_camera()
		7:return lesson.visible_ink()
		8:return lesson.observed.get("preview_seen",false) and not app.playing
		9:
			if not rig:return false
			var pieces: Array=rig.data.get("animation_clips",[])
			return pieces.size()==2 and pieces[0].start==0 and pieces[0].length==12 and pieces[1].start==28 and pieces[1].source_in==12
		10:return lesson.observed.get("export_done",false)
	return false

static func basis(value: Dictionary) -> Basis:
	var b: Array=value.basis
	return Basis(Vector3(b[0],b[1],b[2]),Vector3(b[3],b[4],b[5]),Vector3(b[6],b[7],b[8]))

static func action_label(step: int) -> String:
	return "Add practice map" if step==0 else "Add practice figure" if step==1 else "Save project…" if step==10 else ""

static func action(lesson) -> void:
	var app=lesson.app
	if app.exporting or app.source_import.pid>0 or app.has_dialog(app):return
	if lesson.step==10:app.save();return
	if not lesson.step in [0,1]:return
	var actor: bool=lesson.step==1
	if object(lesson,"model" if actor else "environment")!=null:app.message("That practice asset is already in the scene.");return
	app.choose_file("Add practice figure" if actor else "Add practice map",app.import_actions.MODEL_FILTERS if actor else app.import_actions.MAP_FILTERS,func(path):app.import_actions.add(path,actor,0),ProjectSettings.globalize_path(lesson.assets_root))
