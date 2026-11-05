extends RefCounted
const Assets=preload("res://src/tutorial_assets.gd")
const ID="advanced-physics-v1"
const DEFINITION={"title":"Advanced · Physics recording","steps":[
	"Turn on Advanced, select Practice figure in World and choose Pose. The included room supplies real collisions; the editor grid does not.",
	"Turn Physics on, let the figure move, then turn it off. This freezes a pose; live motion has not become a recorded take.",
	"Seek frame 0. Turn Physics on, choose Local record and press Record. Let the playhead reach at least12, then Stop recording. Physics turns off and the take becomes editable animation.",
	"Seek frame 0, Play the recorded animation, then pause. The saved take plays with Physics off; you do not need to resimulate it.",
	"Export an MP4 of the recorded practice. Preview and export use the saved take. Saving a personal HAS project is optional."
],"hints":[
	"Choose Advanced in the top bar, select Practice figure in World, then Pose. The imported room's floor is a collision surface.",
	"Use Physics beside Local/World record. Try grabbing the figure, then turn Physics off. Nothing continuously writes animation unless you press Record.",
	"Seek0 before enabling Physics. Local captures the selected live figure; World captures all currently simulated objects. Press Record, wait until12 or later, then Stop recording. Escape discards a take; Undo restores replaced motion.",
	"With Physics off, seek0, press Play and then pause. You are viewing authored capture keys, not restarting a simulation. Local leaves unrecorded peers out; use World for a future multi-object take.",
	"Use Export movie here or in the footer. Wait for a successful MP4; a failed encoder or PNG-only export does not finish. Recorded motion is already editable and can be kept in an ordinary HAS."
]}
static func rig(lesson) -> RefCounted:
	return lesson.app.renderer.world_runtime.instance(Assets.FIGURE_ID) if lesson.app.renderer.world_runtime else null
static func committed(lesson,scope: String,ids: Array,first: int,last: int) -> void:
	if lesson.active and lesson.course==ID and lesson.step==2 and scope=="local" and ids==[Assets.FIGURE_ID] and first==0 and last>=12:
		lesson.observed["local_record_seen"]=true
static func observe(lesson) -> void:
	var model:=rig(lesson)
	if not model:return
	if lesson.step==1 and lesson.app.physics_editor.body_active(model.data.id):lesson.observed["physics_seen"]=true
	if lesson.step==3 and lesson.app.playing:lesson.observed["preview_seen"]=true
static func recorded(model: RefCounted) -> bool:
	var frames:={}
	for key in model.authored_keys():frames[int(key.frame)]=true
	for at in range(13):
		if not frames.has(at):return false
	return true
static func satisfied(lesson) -> bool:
	var model:=rig(lesson)
	if not model:return false
	match lesson.step:
		0:return lesson.app.advanced_mode and lesson.app.mode.selected==2 and lesson.app.world_selection.selected==Assets.FIGURE_ID
		1:return lesson.observed.get("physics_seen",false) and not lesson.app.physics_editor.is_running() and not lesson.app.physics_editor.recording.active
		2:return lesson.observed.get("local_record_seen",false) and recorded(model) and not lesson.app.physics_editor.is_running() and not lesson.app.physics_editor.recording.active
		3:return recorded(model) and lesson.observed.get("preview_seen",false) and not lesson.app.playing
		4:return recorded(model) and lesson.observed.get("export_done",false)
	return false
static func highlight(lesson) -> Control:
	match lesson.step:
		0:return lesson.app.world_selection.tree
		1:return lesson.app.physics_editor.toggle
		2:return lesson.app.physics_editor.recording.button
		3:return lesson.app.play_button
		4:return lesson.export_button
	return null
