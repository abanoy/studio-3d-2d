extends Node
const Timing=preload("res://src/cel_timing.gd")
var app
func layer_by_id(id: String) -> Dictionary:
	for layer in app.layers:
		if layer.id==id:return layer
	return {}
func shape(layer: Dictionary) -> Array:
	var result:=[]
	for cel in layer.get("cels",[]):result.append([cel.id,int(cel.start),int(cel.duration),cel.image.get_instance_id(),int(cel.image.get_meta("studio_pixels_revision",0))])
	return result
func begin(layer_id: String,cel_id: String,at: int) -> Dictionary:
	if app.exporting or app.physics_editor.recording.active or app.pose_editor.dragging or app.drawing:app.message("Finish the current edit or recording before moving a drawing exposure.");return {}
	var layer:=layer_by_id(layer_id)
	if layer.is_empty():return {}
	var found: Dictionary={}
	for cel in layer.cels:
		if cel.id==cel_id:found=cel;break
	if found.is_empty() or not found.get("image") is Image:return {}
	app.stop();app.finish_stroke();app.pose_editor.finish_drag()
	app.drawing_selection_editor.cancel();app.fill_editor.cancel();app.color_sampler.cancel(false)
	for i in range(app.layers.size()):
		if app.layers[i].id==layer_id:app.active_layer=i;break
	app.layer_choice.select(app.active_layer);app.set_frame(clampi(at,int(found.start),int(found.start+found.duration)-1));app.refresh_layer()
	return {"layer":layer_id,"cel":cel_id,"session":app.recovery_session,"owner":app.sequence_editor.active_owner,"revision":app.recovery_revision,"video":app.video.duplicate(true),"shape":shape(layer)}
func commit(id: String,start: int,context: Dictionary) -> void:
	var layer:=layer_by_id(str(context.get("layer","")))
	if app.exporting or app.playing or context.get("cel")!=id or context.get("session")!=app.recovery_session or context.get("owner")!=app.sequence_editor.active_owner or context.get("revision")!=app.recovery_revision or context.get("video")!=app.video or layer.is_empty() or context.get("shape")!=shape(layer):app.message("The drawing or scene changed. Drag the exposure again.");return
	var result:=Timing.proposal(layer.cels,id,start,app.video.duration_frames)
	if result.has("error"):app.message(result.error);return
	if not result.changed:return
	layer.cels[result.index].start=result.after;layer.cels.sort_custom(func(a,b):return a.start<b.start)
	app.push_history({"type":"cel_timing","layer_id":layer.id,"cel_id":id,"owner":app.sequence_editor.active_owner,"before":result.before,"after":result.after,"bytes":512})
	app.changed();app.refresh_layer();app.message("Drawing exposure moved. Its pixels and length stay unchanged; Undo restores its timing.")
func resize(id: String,length: int,context: Dictionary) -> void:
	var layer:=layer_by_id(str(context.get("layer","")))
	if app.exporting or app.playing or context.get("cel")!=id or context.get("session")!=app.recovery_session or context.get("owner")!=app.sequence_editor.active_owner or context.get("revision")!=app.recovery_revision or context.get("video")!=app.video or layer.is_empty() or context.get("shape")!=shape(layer):app.message("The drawing or scene changed. Drag the exposure again.");return
	set_exposure(layer.id,id,length)
func set_exposure(layer_id: String,id: String,length: int) -> void:
	if app.exporting or app.timeline.cel_gesture_active() or app.physics_editor.recording.active or app.pose_editor.dragging or app.drawing:app.message("Finish the current edit or recording before changing a drawing exposure.");return
	var layer:=layer_by_id(layer_id)
	if layer.is_empty():return
	var target: Dictionary={}
	for cel in layer.cels:
		if cel.id==id:target=cel;break
	if target.is_empty():return
	var limit: int=app.video.duration_frames-int(target.start)
	for cel in layer.cels:
		if cel.start>target.start:limit=mini(limit,int(cel.start-target.start))
	var result:=Timing.proposal(layer.cels,id,target.start,app.video.duration_frames,mini(length,limit))
	if result.has("error"):app.message(result.error);return
	if not result.changed:return
	app.stop();app.finish_stroke()
	layer.cels[result.index].duration=result.after_duration
	app.push_history({"type":"cel_exposure","layer_id":layer.id,"cel_id":id,"owner":app.sequence_editor.active_owner,"before":result.duration,"after":result.after_duration,"bytes":512})
	app.changed();app.refresh_layer()
func apply_command(command: Dictionary,side: String) -> String:
	if command.get("owner")!=app.sequence_editor.active_owner:return "Drawing history belongs to another sequence."
	var layer:=layer_by_id(str(command.get("layer_id","")))
	if layer.is_empty():return "Drawing history layer is missing."
	var id:=str(command.get("cel_id",""))
	var start=command.get(side);var length=null
	if command.get("type")=="cel_exposure":
		for cel in layer.cels:
			if cel.id==id:start=cel.start;length=command.get(side);break
		if length==null:return "Drawing history cel is missing."
	var result:=Timing.proposal(layer.cels,id,start,app.video.duration_frames,length)
	if result.has("error"):return result.error
	layer.cels[result.index].start=result.after;layer.cels[result.index].duration=result.after_duration;layer.cels.sort_custom(func(a,b):return a.start<b.start)
	return ""
