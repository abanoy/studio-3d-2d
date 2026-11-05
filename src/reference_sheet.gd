extends Node
# A local editor aid, never a document layer, history image or export input.
const MAX_FILE=16*1024*1024
const MAX_PIXELS=4*1024*1024
const MAX_SIDE=8192
var app
var launch: Button
var window: Window
var viewer: Control
var note: Label
var overlay_toggle: CheckButton
var opacity: SpinBox
var guide: Node2D
var source:=""
var source_hash:=""
var image: Image
var texture: ImageTexture
var generation:=0

static func big32(bytes: PackedByteArray,offset: int) -> int:
	return int(bytes[offset])*16777216+int(bytes[offset+1])*65536+int(bytes[offset+2])*256+int(bytes[offset+3])
static func header_error(bytes: PackedByteArray) -> String:
	if bytes.size()>MAX_FILE:return "Reference PNG exceeds 16 MiB."
	if bytes.size()<33 or bytes.slice(0,8)!=PackedByteArray([137,80,78,71,13,10,26,10]) or big32(bytes,8)!=13 or bytes.slice(12,16)!=PackedByteArray([73,72,68,82]):return "Choose a readable PNG reference sheet."
	var width:=big32(bytes,16);var height:=big32(bytes,20)
	if width<1 or height<1 or width>MAX_SIDE or height>MAX_SIDE or width*height>MAX_PIXELS:return "Reference sheet supports up to 4 megapixels and 8192 pixels on either side."
	return ""
static func read_image(path: String) -> Dictionary:
	var file:=FileAccess.open(path,FileAccess.READ)
	if not file:return {"error":"Reference PNG is unavailable. The current sheet was kept."}
	if file.get_length()>MAX_FILE:file.close();return {"error":"Reference PNG exceeds 16 MiB. The current sheet was kept."}
	var bytes:=file.get_buffer(MAX_FILE+1);file.close();var why:=header_error(bytes)
	if not why.is_empty():return {"error":why}
	var decoded:=Image.new();var code:=decoded.load_png_from_buffer(bytes)
	if code!=OK:return {"error":"Reference PNG could not be decoded. The current sheet was kept."}
	if decoded.get_width()!=big32(bytes,16) or decoded.get_height()!=big32(bytes,20):return {"error":"Reference dimensions changed. The current sheet was kept."}
	decoded.convert(Image.FORMAT_RGBA8)
	var hash:=HashingContext.new();hash.start(HashingContext.HASH_SHA256);hash.update(bytes)
	return {"image":decoded,"sha256":hash.finish().hex_encode()}

func setup(parent: Control) -> void:
	launch=app.button(parent,"Reference sheet…",open)
	launch.tooltip_text="View your local PNG character sheet beside Draw, or as a translucent editing guide. Excluded from movies."
	guide=preload("res://src/canvas_raster.gd").new();app.canvas.add_child(guide);guide.hide()
func open() -> void:
	if app.exporting:return
	if not is_instance_valid(window):build()
	window.popup_centered(Vector2i(760,650));viewer.set_picture(texture);refresh_note()
func build() -> void:
	generation+=1
	window=Window.new();window.title="Reference sheet";window.theme=app.theme;window.exclusive=false;window.transient=true;window.min_size=Vector2i(540,440);app.add_child(window)
	window.close_requested.connect(func():generation+=1;window.hide())
	window.focus_exited.connect(func():viewer.dragging=false)
	var panel:=PanelContainer.new();panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT);window.add_child(panel)
	var box:=VBoxContainer.new();panel.add_child(box)
	var row:=HBoxContainer.new();box.add_child(row)
	app.button(row,"Open PNG…",choose);app.button(row,"Reload",reload);app.button(row,"Clear",clear)
	app.button(row,"Fit sheet",func():viewer.fit())
	viewer=preload("res://src/reference_sheet_view.gd").new();viewer.custom_minimum_size=Vector2(500,290);viewer.size_flags_vertical=Control.SIZE_EXPAND_FILL;viewer.size_flags_horizontal=Control.SIZE_EXPAND_FILL;box.add_child(viewer)
	app.label(box,"Wheel to zoom; drag to pan. This view and guide never appear in movies.").autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	var controls:=HBoxContainer.new();box.add_child(controls)
	overlay_toggle=CheckButton.new();overlay_toggle.text="Guide over Draw";controls.add_child(overlay_toggle)
	opacity=app.spin(controls,"Guide opacity (%)",0,100,20)
	app.label(box,"Keep the original PNG. Reference sheets reopen separately from saved projects.").autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	note=app.label(box,"");note.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
func refresh_note() -> void:
	if is_instance_valid(note):note.text="Open a PNG character sheet to begin." if image==null else "%s · %d × %d" % [source.get_file(),image.get_width(),image.get_height()]
func choose() -> void:
	if app.exporting:return
	var token:=generation;var dialog:=FileDialog.new();dialog.access=FileDialog.ACCESS_FILESYSTEM;dialog.file_mode=FileDialog.FILE_MODE_OPEN_FILE;dialog.title="Open reference PNG";dialog.filters=PackedStringArray(["*.png ; PNG reference sheet"])
	if not source.is_empty():dialog.current_dir=source.get_base_dir()
	app.add_child(dialog);dialog.canceled.connect(dialog.queue_free)
	dialog.file_selected.connect(func(path):
		dialog.hide();dialog.queue_free()
		if token!=generation or not is_instance_valid(window) or not window.visible or app.exporting:return
		load_sheet(path))
	dialog.popup_centered_ratio(.7)
func load_sheet(path: String) -> String:
	if app.exporting:return "Finish exporting before changing the reference sheet."
	var loaded:=read_image(path)
	if loaded.has("error"):
		if is_instance_valid(note):note.text=loaded.error
		return loaded.error
	generation+=1;source=path;source_hash=loaded.sha256;image=loaded.image;texture=ImageTexture.create_from_image(image)
	if is_instance_valid(viewer):viewer.set_picture(texture)
	refresh_note();refresh_guide();return ""
func reload() -> void:
	if source.is_empty():refresh_note();return
	load_sheet(source)
func clear() -> void:
	generation+=1;source="";source_hash="";image=null;texture=null
	if is_instance_valid(viewer):viewer.set_picture(null)
	if is_instance_valid(overlay_toggle):overlay_toggle.set_pressed_no_signal(false)
	guide.texture=null;guide.hide();refresh_note()
func refresh_guide() -> void:
	if not guide:return
	var visible: bool=texture!=null and is_instance_valid(window) and is_instance_valid(overlay_toggle) and overlay_toggle.button_pressed and app.mode.selected==0 and not app.playing and not app.exporting and not (app.home and app.home.visible)
	if not visible:guide.hide();return
	var canvas_rect: Rect2=app.canvas.image_rect();var sheet_size:=Vector2(texture.get_size());var factor:=minf(canvas_rect.size.x/sheet_size.x,canvas_rect.size.y/sheet_size.y)
	var extent:=sheet_size*factor;guide.texture=texture;guide.rect=Rect2(canvas_rect.get_center()-extent/2,extent);guide.modulate=Color(1,1,1,opacity.value/100);guide.queue_redraw();guide.show()
func _process(_delta: float) -> void:
	if launch:launch.disabled=app.exporting
	refresh_guide()
