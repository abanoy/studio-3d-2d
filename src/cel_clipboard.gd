extends Node
const Timing=preload("res://src/cel_timing.gd")
const Drawing=preload("res://src/drawing.gd")
const Patch=preload("res://src/cel_patch.gd")
var app
var clipboard: Dictionary={}
var context: Dictionary={}
var menu: PopupMenu

func _ready() -> void:
	menu=PopupMenu.new();add_child(menu)
	for title in ["Copy drawing","Cut drawing","Paste drawing here","Split drawing here"]:menu.add_item(title)
	menu.id_pressed.connect(func(id):menu.hide();perform(["copy","cut","paste","split"][id]))
	menu.popup_hide.connect(func():call_deferred("clear_context"))

func clear_context() -> void:
	if not menu.visible:context.clear()

func _process(_delta: float) -> void:
	clear_stale()

func clear_stale() -> void:
	if not clipboard.is_empty() and (clipboard.session!=app.recovery_session or clipboard.owner!=app.sequence_editor.active_owner or app.cel_timing.layer_by_id(clipboard.layer).is_empty()):clipboard.clear()

func available(layer_id: String) -> bool:
	clear_stale()
	return not clipboard.is_empty() and clipboard.layer==layer_id

func blocked() -> bool:
	return app.exporting or app.drawing or app.navigating or app.pose_editor.dragging or app.physics_editor.recording.active or app.timeline.cel_gesture_active() or app.timeline.audio_gesture_active() or not app.timeline.moving_id.is_empty()

func open_menu(layer_id: String,id: String,at: int,position: Vector2i) -> void:
	context={}
	if blocked():app.message("Finish the current edit or recording before editing drawing clips.");return
	var layer: Dictionary=app.cel_timing.layer_by_id(layer_id)
	if layer.is_empty() or at<0 or at>=app.video.duration_frames:return
	app.stop();app.drawing_selection_editor.cancel();app.fill_editor.cancel();app.color_sampler.cancel(false)
	context={"layer":layer_id,"cel":id,"at":at,"session":app.recovery_session,"owner":app.sequence_editor.active_owner,"revision":app.recovery_revision,"video":app.video.duplicate(true),"shape":app.cel_timing.shape(layer)}
	menu.set_item_disabled(0,id.is_empty());menu.set_item_disabled(1,id.is_empty());menu.set_item_disabled(2,not available(layer_id))
	var can_split:=false
	for cel in layer.cels:
		if cel.id==id:can_split=at>cel.start and at<cel.start+cel.duration;break
	menu.set_item_disabled(3,not can_split)
	menu.position=position;menu.popup()

static func placement(cels: Array,id: String,at,length,frames) -> Dictionary:
	# Reuse the same end-exclusive, non-overlapping timing contract as dragging.
	if not Timing.integer(frames,1,Timing.MAX_FRAMES) or not Timing.integer(at,0,int(frames)-1) or not Timing.integer(length,1,int(frames)):return {"error":"Choose a whole drawing exposure inside the scene."}
	if not cels.is_empty():
		var first=cels[0]
		if not first is Dictionary or not first.get("id") is String:return {"error":"Invalid drawing exposures."}
		var checked:=Timing.proposal(cels,first.id,first.get("start"),frames)
		if checked.has("error"):return checked
	var proposed: Array=cels.duplicate()
	proposed.append({"id":id,"start":at,"duration":length})
	proposed.sort_custom(func(a,b):return a.start<b.start)
	return Timing.proposal(proposed,id,at,frames)

func perform(action: String) -> bool:
	var layer: Dictionary=app.cel_timing.layer_by_id(str(context.get("layer","")))
	if blocked() or app.playing or context.get("session")!=app.recovery_session or context.get("owner")!=app.sequence_editor.active_owner or context.get("revision")!=app.recovery_revision or context.get("video")!=app.video or layer.is_empty() or context.get("shape")!=app.cel_timing.shape(layer):app.message("The drawing or scene changed. Open the drawing menu again.");return false
	if not action in ["copy","cut","paste","split"]:return false
	var selected: Dictionary={};var index:=-1
	for i in range(layer.cels.size()):
		if layer.cels[i].id==context.cel:selected=layer.cels[i];index=i;break
	var pasted: Dictionary={}
	var selected_image: Image
	if action=="paste":
		if not available(layer.id):app.message("Copy a drawing from this layer first. Drawing copies stay within their scene and layer.");return false
		if app.sequence_editor.used("cels")>=32:app.message("Prototype memory limit: 32 full-HD cels.");return false
		var id:=str(ResourceUID.create_id())
		var proposed:=placement(layer.cels,id,context.at,clipboard.duration,app.video.duration_frames)
		if proposed.has("error"):app.message(proposed.error);return false
		if clipboard.image.get_width()!=app.video.width or clipboard.image.get_height()!=app.video.height:app.message("The drawing size changed. Copy it again.");return false
		pasted={"id":id,"start":int(context.at),"duration":int(clipboard.duration),"image":clipboard.image.duplicate()}
	else:
		if selected.is_empty():return false
		var proposed:=Timing.proposal(layer.cels,selected.id,selected.start,app.video.duration_frames)
		if proposed.has("error"):app.message(proposed.error);return false
		var pixels:=Drawing.read_image(selected)
		if pixels.has("error"):app.message(pixels.error);return false
		selected_image=pixels.image
		if selected_image.get_size()!=Vector2i(app.video.width,app.video.height) or selected_image.get_format()!=Image.FORMAT_RGBA8 or selected_image.get_data_size()>8294400:app.message("This drawing cannot be copied at the current canvas size.");return false
		if action=="split":
			if context.at<=selected.start or context.at>=selected.start+selected.duration:app.message("Split inside the drawing's hold, after its first frame.");return false
			if app.sequence_editor.used("cels")>=32:app.message("Prototype memory limit: 32 full-HD cels.");return false
		else:
			clipboard={"layer":layer.id,"owner":app.sequence_editor.active_owner,"session":app.recovery_session,"duration":int(selected.duration),"image":selected_image.duplicate()}
			if action=="copy":app.message("Drawing copied. Right-click a free range on this layer to paste it.");return true
	var before: Array=layer.cels.duplicate(true)
	if action=="cut":layer.cels.remove_at(index)
	elif action=="split":
		var created:=Drawing.insert(layer,int(context.at),int(app.video.duration_frames),selected_image.duplicate());var why: String=app.own_created_cel(created)
		if not why.is_empty():layer.cels=before;app.message(why);return false
	else:
		var why: String=app.own_created_cel(pasted)
		if not why.is_empty():app.message(why);return false
		layer.cels.append(pasted);layer.cels.sort_custom(func(a,b):return a.start<b.start)
	app.push_history(Patch.create(layer.id,app.sequence_editor.active_owner,before,layer.cels))
	for i in range(app.layers.size()):
		if app.layers[i].id==layer.id:app.active_layer=i;break
	app.layer_choice.select(app.active_layer)
	app.changed();app.set_frame(int(context.at));app.refresh_layer()
	app.message("Drawing split into independent cels. Undo restores the original hold." if action=="split" else "Drawing cut. Undo restores it; paste places an independent copy." if action=="cut" else "Independent drawing pasted with its original exposure length. Undo removes it.")
	return true

func apply_patch(command: Dictionary,side: String) -> String:
	if command.get("owner")!=app.sequence_editor.active_owner:return "Drawing history belongs to another sequence."
	var layer: Dictionary=app.cel_timing.layer_by_id(str(command.get("layer_id","")))
	if layer.is_empty():return "Drawing history layer is missing."
	var limit: int=32-app.sequence_editor.used("cels")+layer.cels.size()
	var result:=Patch.apply(layer.cels,command,side,int(app.video.duration_frames),limit)
	if result.has("error"):return result.error
	layer.cels=result.cels
	return ""
