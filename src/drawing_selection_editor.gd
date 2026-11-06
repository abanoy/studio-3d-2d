extends Node
const Selection=preload("res://src/drawing_selection.gd")
const Drawing=preload("res://src/drawing.gd")
var app
var panel: VBoxContainer
var hint: Label
var clear_button: Button
var selected:=Rect2i()
var context:={}
var gesture:=""
var anchor:=Vector2.ZERO
var offset:=Vector2i.ZERO
var copying:=false
var preview_dirty:=false
var prepared:={}
var preview_builds:=0
var max_preview_ms:=0.0
var transforms

func setup(parent: Control) -> void:
	panel=VBoxContainer.new();parent.add_child(panel);parent.move_child(panel,app.tool.get_index()+1)
	hint=app.label(panel,"Drag a rectangle, then drag inside it to move.\nShift-drag keeps a copy. Escape clears.")
	hint.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART;hint.size_flags_horizontal=Control.SIZE_EXPAND_FILL
	clear_button=app.button(panel,"Clear selection",cancel);clear_button.focus_mode=Control.FOCUS_NONE
	clear_button.tooltip_text="Hide the selection border without erasing drawing pixels."
	transforms=preload("res://src/drawing_transform_editor.gd").new();add_child(transforms);transforms.setup(self)
	app.get_window().focus_exited.connect(cancel);refresh()

func available() -> bool:
	return app.mode.selected==0 and not app.layers.is_empty() and not app.playing and not app.exporting and not app.navigating and not (app.home and app.home.visible) and not app.has_dialog(app) and app.source_import.pid<=0 and app.has_project.pid<=0 and not (app.physics_editor.recording and app.physics_editor.recording.active)

func arm() -> void:
	if not available():return
	app.finish_stroke();app.fill_editor.cancel();app.color_sampler.cancel(false);cancel();app.tool.select(4);refresh()
	app.message("Select an area of the active drawing. Drag inside to move; Shift-drag copies. Held frames share this cel.")

func refresh() -> void:
	if panel:
		var opening: bool=app.tool.selected==4 and not panel.visible
		panel.visible=app.tool.selected==4
		if opening and not get_tree().process_frame.is_connected(reveal):get_tree().process_frame.connect(reveal,CONNECT_ONE_SHOT)
	if clear_button:clear_button.disabled=not selected.has_area() and gesture.is_empty()

func reveal() -> void:
	if is_instance_valid(app) and panel.is_visible_in_tree():app.inspector_scroll.ensure_control_visible(transforms.launch if transforms else clear_button)

func snapshot() -> void:
	var layer: Dictionary=app.layers[app.active_layer];var cel:=Drawing.cel_at(layer,app.frame)
	if cel.is_empty():context={};return
	var pixels:=Drawing.read_image(cel)
	if pixels.has("error"):context={};app.message(pixels.error);return
	context={"session":app.recovery_session,"revision":app.recovery_revision,"frame":app.frame,"layer_id":layer.id,"cel_id":cel.id,"image":pixels.image,"raster_token":Drawing.raster_token(cel),"pixels_revision":int(pixels.image.get_meta("studio_pixels_revision",0))}

func valid_context() -> bool:
	if context.is_empty() or not available() or app.tool.selected!=4 or app.recovery_session!=context.session or app.recovery_revision!=context.revision or app.frame!=context.frame:return false
	var layer: Dictionary=app.layers[app.active_layer];var cel:=Drawing.cel_at(layer,app.frame)
	return layer.id==context.layer_id and layer.visible and float(layer.get("opacity",1.0))>0 and not cel.is_empty() and cel.id==context.cel_id and Drawing.raster_token(cel)==context.raster_token and int(context.image.get_meta("studio_pixels_revision",0))==context.pixels_revision

func cancel() -> void:
	selected=Rect2i();context={};gesture="";offset=Vector2i.ZERO;preview_dirty=false;prepared={}
	if transforms:transforms.cancel()
	if is_instance_valid(app) and is_instance_valid(app.canvas):
		app.canvas.selection_preview=null;app.canvas.drawing_selection=Rect2i();app.canvas.queue_redraw()
	refresh()

func before_history() -> bool:
	var active: bool=not gesture.is_empty() or transforms and transforms.active();cancel();return active

func outline(rect: Rect2i) -> void:
	app.canvas.drawing_selection=rect;app.canvas.queue_redraw();refresh()

func _process(_delta: float) -> void:
	if not context.is_empty() and not valid_context():cancel()
	refresh()
	if gesture=="move" and preview_dirty and valid_context():
		var started:=Time.get_ticks_usec();prepared=Selection.move(context.image,selected,offset,copying);preview_dirty=false
		if prepared.has("error"):app.message(prepared.error);cancel();return
		if not prepared.changed:app.canvas.selection_preview=null
		else:
			var candidate: Array=app.layers.duplicate(true);var cel:=Drawing.cel_at(candidate[app.active_layer],app.frame);Drawing.replace_image(cel,prepared.image)
			var image:=Drawing.composite(candidate,app.frame,app.video.width,app.video.height)
			if app.canvas.selection_preview==null:app.canvas.selection_preview=ImageTexture.create_from_image(image)
			else:app.canvas.selection_preview.update(image)
		preview_builds+=1;max_preview_ms=maxf(max_preview_ms,(Time.get_ticks_usec()-started)/1000.0);app.canvas.queue_redraw()

func motion(point: Vector2) -> void:
	if not point.is_finite():return
	if gesture=="marquee":outline(Selection.rectangle(anchor,point,Vector2i(app.video.width,app.video.height)))
	elif gesture=="move":
		var next:=Selection.clamp_offset(selected,Vector2i((point-anchor).round()),Vector2i(app.video.width,app.video.height))
		if next!=offset:offset=next;preview_dirty=true;prepared={}
		outline(Rect2i(selected.position+offset,selected.size))

func pointer(event: InputEvent,point: Vector2) -> void:
	if not available():cancel();return
	if not context.is_empty() and not valid_context():cancel()
	if event is InputEventMouseButton and event.pressed and event.button_index==MOUSE_BUTTON_RIGHT:cancel();return
	if event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_LEFT:
		if event.pressed:
			if transforms and transforms.active():transforms.invalidate()
			if not point.is_finite() or not Rect2(Vector2.ZERO,Vector2(app.video.width,app.video.height)).has_point(point) or app.frame>=app.video.duration_frames:return
			var layer: Dictionary=app.layers[app.active_layer];var cel:=Drawing.cel_at(layer,app.frame)
			if not layer.visible or float(layer.get("opacity",1.0))<=0:app.message("Show the active layer and raise its opacity before selecting.");return
			if cel.is_empty():app.message("This layer has no drawing here. Paint or copy a cel first.");return
			app.finish_stroke();app.fill_editor.cancel();app.color_sampler.cancel(false)
			if selected.has_point(Vector2i(point.floor())) and valid_context():gesture="move";offset=Vector2i.ZERO;copying=event.shift_pressed;prepared={};preview_dirty=false
			else:cancel();snapshot();gesture="marquee"
			anchor=point;motion(point)
		else:finish(point)
	elif event is InputEventMouseMotion and not gesture.is_empty():motion(point)

func finish(point: Vector2) -> void:
	if gesture.is_empty():return
	if not point.is_finite() or not valid_context():cancel();return
	motion(point)
	if gesture=="marquee":
		selected=Selection.rectangle(anchor,point,Vector2i(app.video.width,app.video.height));gesture=""
		if not selected.has_area():cancel()
		else:outline(selected)
		return
	var result: Dictionary=prepared if not prepared.is_empty() and not preview_dirty else Selection.move(context.image,selected,offset,copying)
	if result.has("error"):app.message(result.error);cancel();return
	var was_copy:=copying
	gesture="";prepared={};preview_dirty=false;app.canvas.selection_preview=null
	commit_result(result,"Copied selected drawing pixels. Undo restores the cel." if was_copy else "Moved selected drawing pixels. Undo restores the cel.")

func commit_result(result: Dictionary,note: String) -> bool:
	if not valid_context():cancel();return false
	var image: Image=context.image;var destination: Rect2i=result.selection
	app.canvas.selection_preview=null
	if result.changed:
		var cel:=Drawing.cel_at(app.layers[app.active_layer],app.frame)
		var editable:=Drawing.edit_image(cel,context.raster_token,context.image)
		if editable.has("error"):app.message(editable.error);cancel();return false
		image=editable.image
		var before:={};var after:={};var cost:=0;var damage: Rect2i=result.damage
		for y in range(int(damage.position.y/64),int((damage.end.y+63)/64)):
			for x in range(int(damage.position.x/64),int((damage.end.x+63)/64)):
				var pos:=Vector2i(x*64,y*64);var tile:=Rect2i(pos,Vector2i(64,64)).intersection(Rect2i(Vector2i.ZERO,image.get_size()))
				var old:=image.get_region(tile);var fresh: Image=result.image.get_region(tile)
				if old.get_data()==fresh.get_data():continue
				before[pos]=old;after[pos]=fresh;cost+=old.get_data_size()*2
		image.blit_rect(result.image,damage,damage.position);Drawing.touch(image,damage);context={}
		app.push_history({"type":"pixels","image":image,"before":before,"after":after,"bytes":cost});app.changed()
		app.message(note)
	selected=destination;snapshot();outline(selected)
	return true

func global_event(event: InputEvent) -> bool:
	if not context.is_empty() and not valid_context():cancel();return false
	if transforms and transforms.active() and event is InputEventKey and event.pressed and event.keycode==KEY_ESCAPE and not app.has_dialog(app):transforms.cancel_preview();return true
	if not gesture.is_empty():
		if event is InputEventKey and event.pressed and event.keycode==KEY_ESCAPE or event is InputEventMouseButton and event.pressed and event.button_index==MOUSE_BUTTON_RIGHT:cancel();return true
		if event is InputEventMouseMotion or event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_LEFT and not event.pressed:
			var rect: Rect2=app.canvas.image_rect();var local: Vector2=app.canvas.get_global_transform().affine_inverse()*event.position;var point: Vector2=(local-rect.position)/rect.size*Vector2(app.video.width,app.video.height)
			if event is InputEventMouseMotion:motion(point)
			else:finish(point)
			return true
	elif selected.has_area() and event is InputEventKey and event.pressed and event.keycode==KEY_ESCAPE and not app.has_dialog(app):
		var focus: Control=app.get_viewport().gui_get_focus_owner()
		if focus is LineEdit or focus is TextEdit:return false
		cancel();return true
	return false
