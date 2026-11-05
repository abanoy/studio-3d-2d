extends RefCounted
const Assets=preload("res://src/tutorial_assets.gd")
const Contacts=preload("res://src/foot_contacts.gd")
const Timeline=preload("res://src/timeline.gd")
const ID="advanced-constraints-v1"
const DEFINITION={"title":"Advanced · Rig posing and foot constraints","steps":[
	"Turn on Advanced, select Practice figure in World and choose Pose. Its existing bone hierarchy controls the skinned mesh.",
	"At frame 24, select Left upper arm and rotate it until the hand rises above the shoulder. Auto-key records the joint pose; the body stays independent.",
	"At frame 0 open Planted feet, set Through frame to 24 and Plant feet. This saved range holds both feet during playback, unlike Hold feet while posing.",
	"At frame 12 select Practice figure / root, choose Move and lower Local Y by about 0.03 with Apply local values. Keep both planted feet in place as the knees bend.",
	"At frame 12 open Planted feet, set Through frame to 24 and Release feet. Frames 0–11 keep their saved pins; from 12 the feet follow ordinary pose keys again."
],"hints":[
	"Choose Advanced in the top bar, Practice figure in the World tree, then Pose beside the viewport. The bone tree belongs to the selected figure.",
	"Seek24, search for Left upper arm in Model / pose, choose Rotate and raise Local Z to about65 degrees, then Apply local values. Auto-key must be on. Moving the whole model does not count.",
	"Seek0 with Physics off. Planted feet opens a range window: Through frame24 is inclusive. Press Plant feet. Merely opening it or enabling Hold feet while posing does not save a playback constraint.",
	"Seek12. Choose Practice figure / root at the top of the bone tree, Move, and Local Y about−0.03. Apply local values. Small moves stay within leg reach; an unreachable move refuses safely. Do not move a planted foot directly.",
	"Seek12, open Planted feet, set Through frame24, then Release feet. This changes that range, not the earlier pins. Undo or Previous can restore the saved constraints."
]}
static func rig(lesson) -> RefCounted:
	return lesson.app.renderer.world_runtime.instance(Assets.FIGURE_ID) if lesson.app.renderer.world_runtime else null
static func contact(model: RefCounted,frame: int) -> Dictionary:
	return Contacts.active(model.data.get("animation_clips",[]),frame)
static func satisfied(lesson) -> bool:
	var model:=rig(lesson)
	if not model:return false
	if lesson.step==0:return lesson.app.advanced_mode and lesson.app.mode.selected==2 and lesson.app.world_selection.selected==Assets.FIGURE_ID
	if lesson.step==1:return lesson.app.frame==24 and lesson.raised_arm(model)
	if lesson.step==2:return lesson.app.frame==0 and not contact(model,0).is_empty() and not contact(model,24).is_empty() and contact(model,25).is_empty()
	if lesson.step==3:
		if lesson.app.frame!=12:return false
		var pin:=contact(model,12)
		if pin.is_empty():return false
		var root: Dictionary=model.sample_transform(12)
		if root.position[1]>-.015 or root.position[1]<-.12:return false
		var keyed:=false
		for key in model.authored_keys():
			if key.frame==12 and "@root" in key.get("authored_channels",[]):keyed=true
		if not keyed:return false
		model.sample(12)
		if not model.evaluation_error.is_empty():return false
		for foot in pin.feet:
			if model.bone_transform(foot.ids[2]).origin.distance_to(Timeline.vector(foot.position))>.001:return false
		return true
	if lesson.step==4:return lesson.app.frame==12 and not contact(model,0).is_empty() and not contact(model,11).is_empty() and contact(model,12).is_empty() and contact(model,24).is_empty()
	return false
static func highlight(lesson) -> Control:
	match lesson.step:
		0:return lesson.app.world_selection.tree
		1:return lesson.app.pose_editor.tree
		2,4:return lesson.app.pose_editor.contacts.control
		3:return lesson.app.pose_editor.fields[1]
	return null
