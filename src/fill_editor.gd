extends Node
const Fill=preload("res://src/fill.gd")
const Drawing=preload("res://src/drawing.gd")
var app
var thread: Thread
var context:={}
var pending:={}
var panel: VBoxContainer
var preview_row: VBoxContainer
var sample_visible: CheckButton
var tolerance: SpinBox
var close_gaps: SpinBox
var expand_edges: SpinBox
var connectivity_choice: OptionButton
var last_result:={}
var cancelled:=false

func setup(parent: Control) -> void:
	panel=VBoxContainer.new();parent.add_child(panel)
	parent.move_child(panel,app.tool.get_index()+1)
	app.button(panel,"Color layer below",color_layer).tooltip_text="Create or select Flats beneath the current layer. Line art stays separate. Maximum four layers."
	sample_visible=CheckButton.new();sample_visible.text="Sample visible drawings";sample_visible.button_pressed=true;panel.add_child(sample_visible)
	sample_visible.tooltip_text="Use visible 2D cels as fill boundaries. Never samples the 3D scene. Off: use this layer only."
	tolerance=app.advanced_spin(panel,"Fill tolerance (0–255)",0,255,8)
	var connections:=VBoxContainer.new();panel.add_child(connections);app.advanced(connections);app.label(connections,"Fill connections")
	connectivity_choice=OptionButton.new();connections.add_child(connectivity_choice);connectivity_choice.add_item("Edges only",4);connectivity_choice.add_item("Edges and corners",8)
	connectivity_choice.tooltip_text="Edges only keeps diagonally touching areas separate. Edges and corners joins them and can pass diagonal openings. Edge/large fills preview before Apply."
	close_gaps=app.spin(panel,"Close gaps (pixels)",0,8,0)
	close_gaps.tooltip_text="0: ordinary fill.1–8: virtual barriers can seal small breaks; always preview before Apply. Original lines remain unchanged. Narrow intentional openings can also close."
	expand_edges=app.advanced_spin(panel,"Grow under lines (pixels)",0,8,0)
	expand_edges.tooltip_text="Grow color0–8 pixels in a square neighborhood beneath line art. Use Flats below ink. Can cross narrow details or nearby colors; always preview before Apply. Only the active layer is painted."
	preview_row=VBoxContainer.new();panel.add_child(preview_row);app.label(preview_row,"Fill preview")
	var row:=HBoxContainer.new();preview_row.add_child(row);app.button(row,"Apply fill",apply_pending);app.button(row,"Cancel",cancel)
	preview_row.hide();refresh()

func refresh() -> void:
	if panel:panel.visible=app.tool.selected==2

func busy() -> bool:return thread!=null and thread.is_started()

func settings() -> Dictionary:
	return {"visible":sample_visible.button_pressed,"tolerance":int(tolerance.value),"gap":int(close_gaps.value),"expand":int(expand_edges.value),"connectivity":connectivity_choice.get_selected_id(),"color":app.color.color.to_rgba32()}

func layer_by_id(id: String) -> Dictionary:
	for layer in app.layers:
		if layer.id==id:return layer
	return {}

func valid_context() -> bool:
	return not cancelled and not context.is_empty() and settings()==context.settings and app.recovery_session==context.session and app.recovery_revision==context.revision and app.frame==context.frame and app.layers[app.active_layer].id==context.layer_id and app.layers[app.active_layer].visible and app.mode.selected==0 and app.tool.selected==2 and not app.playing and not app.exporting and not (app.home and app.home.visible) and not app.has_dialog(app)

func start(point: Vector2) -> void:
	if busy():app.message("Preparing the previous fill. Escape cancels it.");return
	cancel();cancelled=false
	var layer: Dictionary=app.layers[app.active_layer];var cel:=Drawing.cel_at(layer,app.frame)
	if not layer.visible or float(layer.get("opacity",1.0))<=0:app.message("Show the active layer and raise its opacity before filling.");return
	if cel.is_empty():
		var count:=0
		for row in app.layers:count+=row.cels.size()
		if app.get("sequence_editor"):count=app.sequence_editor.used("cels")
		if count>=32:app.message("Prototype memory limit: 32 full-HD cels.");return
	var target: Image=cel.image if not cel.is_empty() else Drawing.blank(app.video.width,app.video.height)
	var sample: Image=Drawing.composite(app.layers,app.frame,app.video.width,app.video.height) if sample_visible.button_pressed else target
	var color: int=app.color.color.to_rgba32();var paint:=PackedByteArray([(color>>24)&255,(color>>16)&255,(color>>8)&255,color&255])
	context={"session":app.recovery_session,"revision":app.recovery_revision,"frame":app.frame,"layer_id":layer.id,"cel_id":cel.get("id",""),"settings":settings()}
	thread=Thread.new()
	var error:=thread.start(Fill.calculate.bind(sample.get_data(),target.get_data(),int(app.video.width),int(app.video.height),Vector2i(point.floor()),paint,int(tolerance.value),int(close_gaps.value),int(expand_edges.value),connectivity_choice.get_selected_id()),Thread.PRIORITY_LOW)
	if error!=OK:thread=null;context={};app.message("Cannot prepare fill; drawing preserved.")
	else:app.message("Preparing fill. You can continue editing; changes cancel this fill.")

func _process(_delta: float) -> void:
	refresh()
	if not context.is_empty() and not valid_context():
		var changed_settings: bool=settings()!=context.settings
		cancel()
		if changed_settings:app.message("Fill settings changed. Click again to prepare a new fill.")
	if not busy() or thread.is_alive():return
	var result: Dictionary=thread.wait_to_finish();thread=null;last_result=result.duplicate();last_result.erase("data")
	if not valid_context():context={};return
	if result.has("error"):app.message(result.error);context={};return
	if result.changed==0:app.message("That region already has this color.");context={};return
	pending=result
	if result.expand_pixels>0 or result.gap_pixels>0 or result.edge or result.region>int(app.video.width*app.video.height/2):
		var candidate: Array=app.layers.duplicate(true);var candidate_layer: Dictionary=candidate[app.active_layer]
		var candidate_cel:=Drawing.cel_at(candidate_layer,app.frame)
		var candidate_image:=Image.create_from_data(app.video.width,app.video.height,false,Image.FORMAT_RGBA8,result.data)
		if candidate_cel.is_empty():Drawing.insert(candidate_layer,app.frame,app.video.duration_frames,candidate_image)
		else:candidate_cel.image=candidate_image
		preview_row.show();app.canvas.fill_preview=ImageTexture.create_from_image(Drawing.composite(candidate,app.frame,app.video.width,app.video.height));app.canvas.queue_redraw()
		# Let containers lay out the newly visible row before scrolling it into view.
		if not get_tree().process_frame.is_connected(reveal_preview):get_tree().process_frame.connect(reveal_preview,CONNECT_ONE_SHOT)
		app.message("Grown fill preview. Check narrow details, then Apply fill or Cancel; only the active layer changes." if result.expand_pixels>0 else "Gap-aware fill preview. Review, then Apply fill or Cancel; original lines stay unchanged." if result.gap_pixels>0 else "Fill reaches the canvas edge or covers a large region. Review, then Apply fill or Cancel.")
	else:apply_pending()

func reveal_preview() -> void:
	if not pending.is_empty() and is_instance_valid(app) and not app.is_queued_for_deletion() and preview_row.is_visible_in_tree():app.inspector_scroll.ensure_control_visible(preview_row)

func apply_pending() -> void:
	if pending.is_empty():return
	if not valid_context():cancel();app.message("Fill changed. Click again to prepare a new fill.");return
	var layer:=layer_by_id(context.layer_id);var cel:=Drawing.cel_at(layer,app.frame)
	if cel.get("id","")!=context.cel_id:cancel();return
	var image:=Image.create_from_data(app.video.width,app.video.height,false,Image.FORMAT_RGBA8,pending.data)
	if cel.is_empty():
		var before: Array=layer.cels.duplicate(true);Drawing.insert(layer,app.frame,app.video.duration_frames,image)
		app.push_history({"type":"cels","layer":layer,"before":before,"after":layer.cels.duplicate(true)})
	else:
		var before:={};var after:={};var cost:=0;var bounds: Rect2i=pending.bounds
		for ty in range(int(bounds.position.y/64),int((bounds.end.y+63)/64)):
			for tx in range(int(bounds.position.x/64),int((bounds.end.x+63)/64)):
				var pos:=Vector2i(tx*64,ty*64);var rect:=Rect2i(pos,Vector2i(64,64)).intersection(Rect2i(0,0,app.video.width,app.video.height))
				var old: Image=cel.image.get_region(rect);var fresh:=image.get_region(rect)
				if old.get_data()==fresh.get_data():continue
				before[pos]=old;after[pos]=fresh;cost+=old.get_data_size()*2
		cel.image.copy_from(image);Drawing.touch(cel.image);app.push_history({"type":"pixels","image":cel.image,"before":before,"after":after,"bytes":cost})
	app.changed();app.refresh_layer();cancel();app.message("Filled the active drawing layer. Undo restores it; line art and 3D stay separate.")

func cancel() -> void:
	cancelled=true;pending={};context={}
	if preview_row:preview_row.hide()
	if app.canvas:app.canvas.fill_preview=null;app.canvas.queue_redraw()

func color_layer() -> void:
	if app.exporting or app.playing:return
	app.finish_stroke();cancel()
	for i in range(app.layers.size()):
		if app.layers[i].name.nocasecmp_to("Flats")==0:app.active_layer=i;app.refresh_layer_choices();return
	if app.layers.size()>=4:app.message("This prototype supports four drawing layers. Use an existing layer.");return
	var before: Array=app.layers.duplicate();var selected: String=app.layers[app.active_layer].id
	var layer:={"id":str(ResourceUID.create_id()),"name":"Flats","visible":true,"cels":[]}
	app.layers.insert(app.active_layer,layer)
	app.push_history({"type":"layers","before":before,"after":app.layers.duplicate(),"before_selected":selected,"after_selected":layer.id,"bytes":0})
	app.refresh_layer_choices();app.changed();app.message("Flats sits below the line art. Click inside an outlined region to fill it.")

func _exit_tree() -> void:
	if get_tree().process_frame.is_connected(reveal_preview):get_tree().process_frame.disconnect(reveal_preview)
	if busy():thread.wait_to_finish();thread=null
