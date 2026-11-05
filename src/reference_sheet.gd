extends Node
# A local editor aid, never a document layer, history image or export input.
const Data=preload("res://src/reference_sheet_data.gd")
const MAX_FILE=Data.MAX_FILE
const MAX_PIXELS=Data.MAX_PIXELS
const MAX_SIDE=Data.MAX_SIDE
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
var cache_root:="res://output/reference-sheets"
var cached_source:=""
var display_name:=""
var project_reference: Dictionary={}
var keep: CheckButton
var project_note: Label
var guide_region:=Rect2i()
var guide_scale: SpinBox
var guide_x: SpinBox
var guide_y: SpinBox
var alignment: HBoxContainer

static func header_error(bytes: PackedByteArray) -> String:return Data.header_error(bytes)
static func read_image(path: String) -> Dictionary:return Data.read_image(path)

func setup(parent: Control) -> void:
	launch=app.button(parent,"Reference sheet…",open)
	launch.tooltip_text="View your local PNG character sheet beside Draw, or as a translucent editing guide. Excluded from movies."
	guide=preload("res://src/reference_guide.gd").new();app.canvas.add_child(guide);guide.hide()
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
	viewer=preload("res://src/reference_sheet_view.gd").new();viewer.custom_minimum_size=Vector2(500,290);viewer.size_flags_vertical=Control.SIZE_EXPAND_FILL;viewer.size_flags_horizontal=Control.SIZE_EXPAND_FILL;box.add_child(viewer);viewer.color_picked.connect(pick_color);viewer.tooltip_text="Right-click a visible sheet pixel to choose its brush color, including alpha."
	app.label(box,"Wheel to zoom; drag to pan; right-click a sheet color to paint with it. Reference guides stay out of movies.").autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	var guide_tools:=HBoxContainer.new();box.add_child(guide_tools)
	app.button(guide_tools,"Use viewed region",use_viewed_region).tooltip_text="Fit the visible part of this sheet over Draw without cropping the PNG."
	app.button(guide_tools,"Whole sheet",reset_guide)
	app.button(guide_tools,"Align guide…",func():alignment.visible=not alignment.visible)
	alignment=HBoxContainer.new();box.add_child(alignment);alignment.hide()
	guide_scale=app.spin(alignment,"Guide size (%)",10,800,100)
	guide_x=app.spin(alignment,"X offset (pixels)",-1920,1920,0)
	guide_y=app.spin(alignment,"Y offset (pixels)",-1080,1080,0)
	var controls:=HBoxContainer.new();box.add_child(controls)
	overlay_toggle=CheckButton.new();overlay_toggle.text="Guide over Draw";controls.add_child(overlay_toggle)
	opacity=app.spin(controls,"Guide opacity (%)",0,100,20)
	keep=CheckButton.new();keep.text="Keep PNG in project";box.add_child(keep);keep.toggled.connect(set_kept)
	project_note=app.label(box,"");project_note.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	note=app.label(box,"");note.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
func refresh_note() -> void:
	sync_kept()
	if is_instance_valid(note):note.text="Open a PNG character sheet to begin." if image==null else "%s · %d × %d" % [display_name,image.get_width(),image.get_height()]
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
	var loaded:=Data.read_image(path)
	if loaded.has("error"):feedback(loaded.error);return loaded.error
	var cached:=Data.cache_image(loaded,ProjectSettings.globalize_path(cache_root))
	if cached.has("error"):feedback(cached.error);return cached.error
	var before:=state();var pinned:=not project_reference.is_empty()
	var title:=display_name if path==source and pinned else path.get_file()
	var candidate:={"format":Data.FORMAT,"name":title,"source":cached.source,"sha256":loaded.sha256}
	if pinned:
		var why:=Data.error(candidate)
		if not why.is_empty():feedback(why);return why
	install_picture(loaded.image,path,cached.source,title,loaded.sha256)
	if pinned:project_reference=candidate
	refresh_note();refresh_guide();commit(before);return ""
func feedback(message: String) -> void:
	if is_instance_valid(note):note.text=message
func install_picture(picture: Image,reload_source: String,cached: String,title: String,digest: String) -> void:
	generation+=1;source=reload_source;cached_source=cached;display_name=title;source_hash=digest;image=picture;texture=ImageTexture.create_from_image(image)
	if is_instance_valid(viewer):viewer.set_picture(texture)
	reset_geometry()
func document() -> Dictionary:return project_reference.duplicate(true)
func state() -> Dictionary:
	var sheet:={}
	if image!=null:sheet={"format":Data.FORMAT,"name":display_name,"source":cached_source,"sha256":source_hash,"reload_source":source}
	return {"document":document(),"sheet":sheet,"guide":is_instance_valid(overlay_toggle) and overlay_toggle.button_pressed,"opacity":opacity.value if is_instance_valid(opacity) else 20.,"region":[guide_region.position.x,guide_region.position.y,guide_region.size.x,guide_region.size.y],"scale":guide_scale.value if is_instance_valid(guide_scale) else 100.,"x":guide_x.value if is_instance_valid(guide_x) else 0.,"y":guide_y.value if is_instance_valid(guide_y) else 0.}
func commit(before: Dictionary) -> void:
	var after:=state()
	if before.document==after.document:return
	app.finish_stroke();app.stop()
	app.push_history({"type":"reference_sheet","before":before,"after":after,"bytes":2*(JSON.stringify(before).to_utf8_buffer().size()+JSON.stringify(after).to_utf8_buffer().size())})
	app.changed()
func set_kept(value: bool) -> void:
	if app.exporting:sync_kept();return
	if value and image==null:sync_kept();feedback("Open a PNG before keeping it in the project.");return
	var before:=state()
	if value:
		var candidate:={"format":Data.FORMAT,"name":display_name,"source":cached_source,"sha256":source_hash}
		var why:=Data.error(candidate)
		if not why.is_empty():sync_kept();feedback(why);return
		if FileAccess.get_sha256(cached_source)!=source_hash:sync_kept();feedback("The reference cache changed. Reload the original PNG before keeping it.");return
		project_reference=candidate
	else:project_reference={}
	sync_kept();commit(before)
func sync_kept() -> void:
	if is_instance_valid(keep):keep.set_pressed_no_signal(not project_reference.is_empty())
	if is_instance_valid(project_note):project_note.text="Included in project. Packed saves embed the PNG; linked saves keep a PNG beside the project." if not project_reference.is_empty() else "Keep the original PNG. Enable Keep PNG in project to save this sheet with the scene."
func prepare_project(value: Dictionary) -> Dictionary:
	if value.is_empty():return {"data":{}}
	var why:=Data.error(value)
	if not why.is_empty():return {"error":why}
	var loaded:=Data.read_image(value.source)
	if loaded.has("error"):return loaded
	if loaded.sha256!=value.sha256:return {"error":"Reference sheet checksum differs."}
	var cached:=Data.cache_image(loaded,ProjectSettings.globalize_path(cache_root))
	if cached.has("error"):return cached
	var data:=value.duplicate(true);data.source=cached.source
	return {"data":data,"loaded":loaded,"reload_source":value.source}
func install_prepared(prepared: Dictionary) -> void:
	if prepared.data.is_empty():
		if not project_reference.is_empty():clear_picture()
		project_reference={};refresh_note();return
	var data: Dictionary=prepared.data
	install_picture(prepared.loaded.image,prepared.reload_source,data.source,data.name,data.sha256);project_reference=data.duplicate(true)
	if is_instance_valid(overlay_toggle):overlay_toggle.set_pressed_no_signal(false)
	refresh_note();refresh_guide()
func restore_state(value: Dictionary) -> String:
	var sheet: Dictionary=value.sheet.duplicate(true);var loaded:={};var reload_source: String=sheet.get("reload_source","");sheet.erase("reload_source")
	if not sheet.is_empty():
		var why:=Data.error(sheet)
		if not why.is_empty():return why
		loaded=Data.read_image(sheet.source)
		if loaded.has("error"):return loaded.error
		if loaded.sha256!=sheet.sha256:return "Reference history source changed. Existing sheet was kept."
	if not value.document.is_empty() and value.document!=sheet:return "Invalid reference history ownership."
	var region:=Rect2i()
	if not sheet.is_empty():
		var raw=value.get("region",[0,0,loaded.image.get_width(),loaded.image.get_height()])
		if not raw is Array or raw.size()!=4:return "Invalid reference guide history."
		for n in raw:
			if not (n is int or n is float) or not is_finite(float(n)) or float(n)!=floor(float(n)) or n<0 or n>Data.MAX_SIDE:return "Invalid reference guide history."
		region=Rect2i(int(raw[0]),int(raw[1]),int(raw[2]),int(raw[3]))
		if not region.has_area() or not Rect2i(Vector2i.ZERO,loaded.image.get_size()).encloses(region):return "Reference guide history exceeds the sheet."
	for spec in [["scale",10,800,100.],["x",-1920,1920,0.],["y",-1080,1080,0.]]:
		var n=value.get(spec[0],spec[3])
		if not (n is int or n is float) or not is_finite(float(n)) or n<spec[1] or n>spec[2]:return "Invalid reference alignment history."

	if sheet.is_empty():clear_picture()
	else:install_picture(loaded.image,reload_source,sheet.source,sheet.name,sheet.sha256)
	project_reference=value.document.duplicate(true)
	if is_instance_valid(overlay_toggle):overlay_toggle.set_pressed_no_signal(value.guide)
	if is_instance_valid(opacity):opacity.set_value_no_signal(value.opacity)
	guide_region=region
	if is_instance_valid(guide_scale):guide_scale.set_value_no_signal(value.get("scale",100.))
	if is_instance_valid(guide_x):guide_x.set_value_no_signal(value.get("x",0.))
	if is_instance_valid(guide_y):guide_y.set_value_no_signal(value.get("y",0.))
	refresh_note();refresh_guide();return ""

func reload() -> void:
	if source.is_empty():refresh_note();return
	load_sheet(source)
func clear() -> void:
	if app.exporting:return
	var before:=state();clear_picture();project_reference={};refresh_note();commit(before)
func clear_picture() -> void:
	generation+=1;source="";cached_source="";display_name="";source_hash="";image=null;texture=null
	if is_instance_valid(viewer):viewer.set_picture(null)
	if is_instance_valid(overlay_toggle):overlay_toggle.set_pressed_no_signal(false)
	guide.texture=null;guide.region=Rect2i();guide.hide();reset_geometry()

func refresh_guide() -> void:
	if not guide:return
	var visible: bool=texture!=null and is_instance_valid(window) and is_instance_valid(overlay_toggle) and overlay_toggle.button_pressed and app.mode.selected==0 and not app.playing and not app.exporting and not (app.home and app.home.visible)
	if not visible:guide.hide();return
	var canvas_rect: Rect2=app.canvas.image_rect();var region:=guide_region.intersection(Rect2i(Vector2i.ZERO,image.get_size()))
	if not region.has_area():guide.hide();return
	var sheet_size:=Vector2(region.size);var factor:=minf(canvas_rect.size.x/sheet_size.x,canvas_rect.size.y/sheet_size.y)*guide_scale.value/100
	var extent:=sheet_size*factor;var center:=canvas_rect.get_center()+Vector2(guide_x.value/1920,guide_y.value/1080)*canvas_rect.size
	guide.texture=texture;guide.region=region;guide.rect=Rect2(center-extent/2,extent);guide.modulate=Color(1,1,1,opacity.value/100);guide.queue_redraw();guide.show()
func _process(_delta: float) -> void:
	if launch:launch.disabled=app.exporting
	refresh_guide()

func pick_color(point: Vector2i) -> void:
	if image==null or not Rect2i(Vector2i.ZERO,image.get_size()).has_point(point):return
	var selected:=image.get_pixelv(point)
	if selected.a==0:feedback("That sheet pixel is transparent. Choose a visible color.");return
	app.color.color=selected
	feedback("Brush color selected from "+display_name+".")

func reset_geometry() -> void:
	guide_region=Rect2i(Vector2i.ZERO,image.get_size()) if image!=null else Rect2i()
	if is_instance_valid(guide_scale):guide_scale.set_value_no_signal(100)
	if is_instance_valid(guide_x):guide_x.set_value_no_signal(0)
	if is_instance_valid(guide_y):guide_y.set_value_no_signal(0)
func reset_guide() -> void:
	if image==null:feedback("Open a PNG before fitting the guide.");return
	reset_geometry();refresh_guide();feedback("Whole sheet fitted as the Draw guide.")
func use_viewed_region() -> void:
	if image==null or not is_instance_valid(viewer):feedback("Open a PNG before choosing a guide region.");return
	var picture: Rect2=viewer.picture_rect();var visible:=picture.intersection(Rect2(Vector2.ZERO,viewer.size))
	if not visible.has_area() or not picture.has_area():feedback("Bring part of the sheet into view before choosing it as the guide.");return
	var dimensions:=Vector2(image.get_size());var start:=((visible.position-picture.position)/picture.size*dimensions).floor();var end:=((visible.end-picture.position)/picture.size*dimensions).ceil()
	var region:=Rect2i(Vector2i(start),Vector2i(end-start)).intersection(Rect2i(Vector2i.ZERO,image.get_size()))
	if not region.has_area():feedback("Bring part of the sheet into view before choosing it as the guide.");return
	reset_geometry();guide_region=region;overlay_toggle.set_pressed_no_signal(true);refresh_guide();feedback("Visible region fitted as the Draw guide. The original sheet stays intact.")
