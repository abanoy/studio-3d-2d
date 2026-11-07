extends Node
const Drawing=preload("res://src/drawing.gd")
# Keep layer dictionaries/Images alive across structural history, as stroke commands
# address those same objects. Only the small order arrays are copied.
var app
var launch: Button
var dialog: AcceptDialog
var listing: ItemList
var name_edit: LineEdit
var up: Button
var down: Button
var remove: Button
var visible_button: Button
var add: Button
var effects: Button
var opacity: SpinBox
var apply_opacity: Button
var session:=""
var refreshing:=false
var observed:=""
var confirmation: ConfirmationDialog
var pending: Dictionary={}

func setup(parent: Control) -> void:
	launch=app.button(parent,"Layers…",open)
	parent.move_child(launch,app.layer_choice.get_index()+1)
	launch.tooltip_text="Add, rename, stack or remove drawing layers. Top layer paints over the others."
	dialog=AcceptDialog.new();dialog.title="Drawing layers";dialog.exclusive=false;dialog.unresizable=false;dialog.get_ok_button().text="Done";app.add_child(dialog)
	var box:=VBoxContainer.new();dialog.add_child(box)
	var hint:=Label.new();hint.text="Top layer covers the layers below it.";box.add_child(hint)
	listing=ItemList.new();listing.custom_minimum_size=Vector2(420,150);box.add_child(listing)
	listing.item_selected.connect(select_row)
	name_edit=LineEdit.new();name_edit.max_length=64;name_edit.placeholder_text="Layer name";box.add_child(name_edit)
	name_edit.text_submitted.connect(func(_text):rename_layer(name_edit.text))
	var row:=HBoxContainer.new();box.add_child(row)
	app.button(row,"Rename",func():rename_layer(name_edit.text))
	visible_button=app.button(row,"Hide",func():set_visible(not app.layers[app.active_layer].visible))
	up=app.button(row,"Move up",func():move_layer(1));down=app.button(row,"Move down",func():move_layer(-1))
	var creation:=HBoxContainer.new();box.add_child(creation)
	add=app.button(creation,"New layer",func():add_layer("Layer"))
	effects=app.button(creation,"New effects",func():add_layer("Effects"))
	remove=app.button(creation,"Remove…",request_remove)
	var fade:=HBoxContainer.new();box.add_child(fade)
	var caption:=Label.new();caption.text="Opacity (%)";fade.add_child(caption)
	opacity=SpinBox.new();opacity.min_value=0;opacity.max_value=100;opacity.step=1;opacity.value=100;opacity.size_flags_horizontal=Control.SIZE_EXPAND_FILL;fade.add_child(opacity)
	apply_opacity=app.button(fade,"Apply opacity",func():set_opacity(opacity.value))
	opacity.get_line_edit().text_submitted.connect(func(_text):opacity.apply();set_opacity(opacity.value))
	confirmation=ConfirmationDialog.new();confirmation.title="Remove drawing layer?";confirmation.get_ok_button().text="Remove layer";app.add_child(confirmation)
	confirmation.confirmed.connect(confirm_remove)
	confirmation.canceled.connect(func():
		confirmation.hide();pending={}
		if session==app.recovery_session and available():dialog.popup_centered())

func available() -> bool:
	return not app.exporting and not app.playing and not app.layers.is_empty()

func prepare() -> bool:
	if not available():return false
	if dialog.visible and session!=app.recovery_session:dialog.hide();return false
	app.finish_stroke()
	if app.fill_editor:app.fill_editor.cancel()
	return true

func open() -> void:
	if not prepare():return
	session=app.recovery_session;refresh();dialog.popup_centered()

func _process(_delta: float) -> void:
	launch.disabled=not available()
	if session!=app.recovery_session:
		dialog.hide();confirmation.hide();pending={}
	elif dialog.visible and signature()!=observed:refresh()

func signature() -> String:
	var rows:=[app.active_layer]
	for layer in app.layers:rows.append([layer.id,layer.name,layer.visible,layer.get("opacity",1.0),layer.cels.size()])
	return JSON.stringify(rows)

func refresh() -> void:
	if not listing or app.layers.is_empty():return
	refreshing=true;listing.clear()
	for i in range(app.layers.size()-1,-1,-1):
		var layer: Dictionary=app.layers[i]
		var amount: float=layer.get("opacity",1.0)
		listing.add_item(("●  " if layer.visible else "○  ")+layer.name+(" ("+String.num(amount*100,2)+"%)" if amount<1 else ""))
		listing.set_item_metadata(listing.item_count-1,i)
		listing.set_item_tooltip(listing.item_count-1,"%s · %d drawings · %s" % [layer.name,layer.cels.size(),"shown" if layer.visible else "hidden"])
	listing.select(app.layers.size()-1-app.active_layer)
	name_edit.text=app.layers[app.active_layer].name
	opacity.set_value_no_signal(float(app.layers[app.active_layer].get("opacity",1.0))*100)
	visible_button.text="Hide" if app.layers[app.active_layer].visible else "Show"
	up.disabled=app.active_layer==app.layers.size()-1;down.disabled=app.active_layer==0
	remove.disabled=app.layers.size()==1;add.disabled=app.layers.size()>=4;effects.disabled=add.disabled
	refreshing=false
	observed=signature()

func select_row(row: int) -> void:
	if refreshing or not prepare():return
	app.active_layer=int(listing.get_item_metadata(row));app.layer_choice.select(app.active_layer);app.refresh_layer();refresh()

func unique_name(base: String) -> String:
	var candidate:=base;var number:=2
	while has_name(candidate):candidate=base+" "+str(number);number+=1
	return candidate

func has_name(value: String,except_index: int=-1) -> bool:
	for i in range(app.layers.size()):
		if i!=except_index and app.layers[i].name.nocasecmp_to(value)==0:return true
	return false

func properties(layer: Dictionary,after: Dictionary) -> void:
	var before:={"name":layer.name,"visible":layer.visible}
	if layer.has("opacity"):before.opacity=layer.opacity
	after=before.merged(after,true)
	if after.get("opacity",1.0)==1.0:after.erase("opacity")
	if before==after:refresh();return
	layer.name=after.name;layer.visible=after.visible
	if after.has("opacity"):layer.opacity=after.opacity
	else:layer.erase("opacity")
	app.push_history({"type":"layer_properties","layer":layer,"before":before,"after":after,"bytes":0})
	app.refresh_layer_choices();app.changed();refresh()

func set_opacity(percent: float) -> void:
	if not is_finite(percent) or percent<0 or percent>100 or not prepare():return
	properties(app.layers[app.active_layer],{"opacity":percent/100.0})

func rename_layer(value: String) -> void:
	if not prepare():return
	var cleaned:=value.strip_edges()
	if cleaned.is_empty() or cleaned.length()>64:app.message("Use a layer name between 1 and 64 characters.");return
	for ch in cleaned:
		if ch.unicode_at(0)<32 or ch.unicode_at(0)==127:app.message("Layer names must be on one line.");return
	if has_name(cleaned,app.active_layer):app.message("Another layer already has that name.");return
	var layer: Dictionary=app.layers[app.active_layer];properties(layer,{"name":cleaned,"visible":layer.visible})

func set_visible(value: bool) -> void:
	if not prepare():app.refresh_layer();return
	var layer: Dictionary=app.layers[app.active_layer];properties(layer,{"name":layer.name,"visible":value})

func structure(before: Array,selected: String,bytes: int=0) -> void:
	app.push_history({"type":"layers","before":before,"after":app.layers.duplicate(),"before_selected":selected,"after_selected":app.layers[app.active_layer].id,"bytes":bytes})
	app.refresh_layer_choices();app.changed();refresh()

func add_layer(base: String) -> void:
	if not prepare():return
	if app.layers.size()>=4:app.message("This prototype supports four drawing layers.");return
	var before: Array=app.layers.duplicate();var selected: String=app.layers[app.active_layer].id
	var layer:={"id":str(ResourceUID.create_id()),"name":unique_name(base),"visible":true,"cels":[]}
	app.active_layer+=1;app.layers.insert(app.active_layer,layer);structure(before,selected)

func move_layer(direction: int) -> void:
	if not prepare() or direction not in [-1,1]:return
	var target: int=app.active_layer+direction
	if target<0 or target>=app.layers.size():return
	var before: Array=app.layers.duplicate();var layer: Dictionary=app.layers[app.active_layer]
	app.layers.remove_at(app.active_layer);app.layers.insert(target,layer);app.active_layer=target;structure(before,layer.id)

func request_remove() -> void:
	if not prepare() or app.layers.size()<=1:return
	var layer: Dictionary=app.layers[app.active_layer]
	pending={"layer":layer,"session":app.recovery_session,"revision":app.recovery_revision}
	if layer.cels.is_empty():confirm_remove();return
	# A sibling modal avoids nesting another exclusive window under the layer dialog.
	dialog.hide();confirmation.dialog_text="Remove this layer and its %d drawings?\nUndo can restore them." % layer.cels.size();confirmation.popup_centered()

func confirm_remove() -> void:
	confirmation.hide()
	if pending.is_empty():return
	var request:=pending;pending={}
	if request.session!=app.recovery_session or request.revision!=app.recovery_revision or not prepare():return
	var index: int=-1
	for i in range(app.layers.size()):
		if is_same(app.layers[i],request.layer):index=i;break
	if index<0 or app.layers.size()<=1:return
	var before: Array=app.layers.duplicate();var selected: String=app.layers[app.active_layer].id;var bytes:=0
	# Structural history keeps the existing owners, not decoded frame snapshots.
	# Charge their retained payloads; hot/decoded owner bytes remain separately
	# tracked by the document budget even while only Undo retains the layer.
	var retained:={}
	for cel in request.layer.cels:
		var token:=Drawing.raster_token(cel)
		if token.is_empty() or retained.has(token[0]):continue
		retained[token[0]]=true;bytes+=Drawing.raster_bytes(cel)
	app.layers.remove_at(index);app.active_layer=clampi(index,0,app.layers.size()-1);structure(before,selected,bytes)
	if session==app.recovery_session:dialog.popup_centered()
