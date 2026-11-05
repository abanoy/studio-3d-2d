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
var last_result:={}
var cancelled:=false

func setup(parent: Control) -> void:
	panel=VBoxContainer.new();parent.add_child(panel)
	parent.move_child(panel,app.tool.get_index()+1)
	app.button(panel,"Color layer below",color_layer).tooltip_text="Create or select Flats beneath the current layer. Line art stays separate. Maximum four layers."
	sample_visible=CheckButton.new();sample_visible.text="Sample visible drawings";sample_visible.button_pressed=true;panel.add_child(sample_visible)
	sample_visible.tooltip_text="Use visible 2D cels as fill boundaries. Never samples the 3D scene. Off: use this layer only."
	tolerance=app.advanced_spin(panel,"Fill tolerance (0–255)",0,255,8)
	preview_row=VBoxContainer.new();panel.add_child(preview_row);app.label(preview_row,"Large / edge fill preview")
	var row:=HBoxContainer.new();preview_row.add_child(row);app.button(row,"Apply fill",apply_pending);app.button(row,"Cancel",cancel)
	preview_row.hide();refresh()

func refresh() -> void:
	if panel:panel.visible=app.tool.selected==2

func busy() -> bool:return thread!=null and thread.is_started()

func layer_by_id(id: String) -> Dictionary:
	for layer in app.layers:
		if layer.id==id:return layer
	return {}

func valid_context() -> bool:
	return not cancelled and not context.is_empty() and app.recovery_session==context.session and app.recovery_revision==context.revision and app.frame==context.frame and app.layers[app.active_layer].id==context.layer_id and app.layers[app.active_layer].visible and app.mode.selected==0 and app.tool.selected==2 and not app.playing and not app.exporting and not (app.home and app.home.visible) and not app.has_dialog(app)

func start(point: Vector2) -> void:
	if busy():app.message("Preparing the previous fill. Escape cancels it.");return
	cancel();cancelled=false
	var layer: Dictionary=app.layers[app.active_layer];var cel:=Drawing.cel_at(layer,app.frame)
	if not layer.visible or float(layer.get("opacity",1.0))<=0:app.message("Show the active layer and raise its opacity before filling.");return
	if cel.is_empty():
		var count:=0
		for row in app.layers:count+=row.cels.size()
		if count>=32:app.message("Prototype memory limit: 32 full-HD cels.");return
	var target: Image=cel.image if not cel.is_empty() else Drawing.blank(app.video.width,app.video.height)
	var sample: Image=Drawing.composite(app.layers,app.frame,app.video.width,app.video.height) if sample_visible.button_pressed else target
	var color: int=app.color.color.to_rgba32();var paint:=PackedByteArray([(color>>24)&255,(color>>16)&255,(color>>8)&255,color&255])
	context={"session":app.recovery_session,"revision":app.recovery_revision,"frame":app.frame,"layer_id":layer.id,"cel_id":cel.get("id","")}
	thread=Thread.new()
	var error:=thread.start(Fill.calculate.bind(sample.get_data(),target.get_data(),int(app.video.width),int(app.video.height),Vector2i(point.floor()),paint,int(tolerance.value)),Thread.PRIORITY_LOW)
	if error!=OK:thread=null;context={};app.message("Cannot prepare fill; drawing preserved.")
	else:app.message("Preparing fill. You can continue editing; changes cancel this fill.")

func _process(_delta: float) -> void:
	refresh()
	if not context.is_empty() and not valid_context():cancel()
	if not busy() or thread.is_alive():return
	var result: Dictionary=thread.wait_to_finish();thread=null;last_result=result.duplicate();last_result.erase("data")
	if not valid_context():context={};return
	if result.has("error"):app.message(result.error);context={};return
	if result.changed==0:app.message("That region already has this color.");context={};return
	pending=result
	if result.edge or result.region>int(app.video.width*app.video.height/2):
		var candidate: Array=app.layers.duplicate(true);var candidate_layer: Dictionary=candidate[app.active_layer]
		var candidate_cel:=Drawing.cel_at(candidate_layer,app.frame)
		var candidate_image:=Image.create_from_data(app.video.width,app.video.height,false,Image.FORMAT_RGBA8,result.data)
		if candidate_cel.is_empty():Drawing.insert(candidate_layer,app.frame,app.video.duration_frames,candidate_image)
		else:candidate_cel.image=candidate_image
		preview_row.show();app.canvas.fill_preview=ImageTexture.create_from_image(Drawing.composite(candidate,app.frame,app.video.width,app.video.height));app.canvas.queue_redraw()
		app.message("Fill reaches the canvas edge or covers a large region. Review, then Apply fill or Cancel.")
	else:apply_pending()

func apply_pending() -> void:
	if pending.is_empty() or not valid_context():cancel();return
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
	if busy():thread.wait_to_finish();thread=null
