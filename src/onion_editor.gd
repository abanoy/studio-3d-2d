extends Node
const Drawing=preload("res://src/drawing.gd")
const SHADER=preload("res://src/onion.gdshader")
var app
var enabled: CheckButton
var opacity: SpinBox
var views: Array[Node2D]=[]
var tokens: Array=["",""]
var uploads:=0
var selected:={}

static func neighbors(layer: Dictionary,frame: int) -> Dictionary:
	var previous:={};var next:={}
	for cel in layer.cels:
		if cel.start<=frame and frame<cel.start+cel.duration:continue
		if cel.start<=frame and (previous.is_empty() or cel.start>previous.start):previous=cel
		if cel.start>frame and (next.is_empty() or cel.start<next.start):next=cel
	return {"previous":previous,"next":next}

func setup(parent: Control) -> void:
	enabled=CheckButton.new();enabled.text="Onion skin";enabled.tooltip_text="Previous drawing in blue, next drawing in pink. Editing guide only; never appears in movies.";parent.add_child(enabled);parent.move_child(enabled,app.layer_visibility.get_index()+1)
	opacity=app.advanced_spin(parent,"Onion opacity (%)",5,60,25)
	for index in range(2):
		var view:=preload("res://src/canvas_raster.gd").new();view.show_behind_parent=true
		var material:=ShaderMaterial.new();material.shader=SHADER;view.material=material;app.canvas.add_child(view);view.hide();views.append(view)
	enabled.toggled.connect(func(_value):refresh())
	opacity.value_changed.connect(func(_value):refresh())

func _process(_delta: float) -> void:refresh()

func refresh() -> void:
	if not enabled:return
	var visible: bool=enabled.button_pressed and app.mode.selected==0 and not app.playing and not app.exporting and not (app.home and app.home.visible) and not app.layers.is_empty() and app.layers[app.active_layer].visible and float(app.layers[app.active_layer].get("opacity",1.0))>0 and app.canvas.fill_preview==null
	if not visible:
		for view in views:view.hide()
		return
	selected=neighbors(app.layers[app.active_layer],app.frame)
	var rect: Rect2=app.canvas.image_rect()
	for index in range(2):
		var cel: Dictionary=selected.previous if index==0 else selected.next;var view:=views[index]
		if cel.is_empty():view.hide();view.texture=null;tokens[index]="";continue
		var token:=JSON.stringify(Drawing.raster_token(cel))
		if token!=tokens[index]:
			var pixels:=Drawing.read_image(cel)
			if pixels.has("error"):view.hide();view.texture=null;tokens[index]="";app.message(pixels.error);continue
			view.texture=ImageTexture.create_from_image(pixels.image);tokens[index]=token;uploads+=1;view.queue_redraw()
		var tint:=Color("58ccf0" if index==0 else "f080ad");tint.a=opacity.value/100.0*float(app.layers[app.active_layer].get("opacity",1.0));view.material.set_shader_parameter("ghost_color",tint)
		if view.rect!=rect:view.rect=rect;view.queue_redraw()
		view.show()
