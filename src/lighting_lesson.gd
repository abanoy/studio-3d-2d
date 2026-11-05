extends RefCounted
const ID="advanced-lighting-v1"
const DEFINITION={"title":"Advanced · Lighting and export","steps":[
	"Turn on Advanced in the blue top bar.",
	"Choose Unshaded beside the Scene / Draw / Pose selector. Compare the figure's base colors with the lit practice scene.",
	"Choose Studio light. It supplies preview illumination; Lit instead uses the lights imported with your scene.",
	"Export this practice as an MP4. The chosen lighting is shared by preview and export. You may keep the movie without saving the practice project."
],"hints":[
	"Advanced adds controls to the same scene. It does not create another project.",
	"Open the lighting menu near the viewport mode. Unshaded shows base colors without shading; your original materials stay unchanged.",
	"Choose Studio light in the same menu. Imported scenes without their own lamps may look dark in Lit; Studio light is an explicit fallback.",
	"Use Export movie here or in the footer, choose an output folder and wait for success. PNG-only output does not finish this MP4 task. A failed export is safe to retry."
]}
static func satisfied(lesson) -> bool:
	match lesson.step:
		0:return lesson.app.advanced_mode
		1:return lesson.app.video.get("lighting_mode","studio")=="unshaded"
		2:return lesson.app.video.get("lighting_mode","studio")=="studio"
		3:return lesson.observed.get("export_done",false)
	return false
static func highlight(lesson) -> Control:
	if lesson.step==0:return lesson.find_button("Advanced")
	if lesson.step in [1,2]:return lesson.app.lighting_choice
	return lesson.export_button
