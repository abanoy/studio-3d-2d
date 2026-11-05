extends Node
const Palette=preload("res://src/color_palette.gd")
var app
var panel: VBoxContainer
var grid: GridContainer
var hint: Label
var detail: VBoxContainer
var name_field: LineEdit
var selected:=-1
var snapshot: Array=[]
var buttons: Array=[]
var last_color:=-1

func setup(parent: Control) -> void:
	panel=VBoxContainer.new();parent.add_child(panel);parent.move_child(panel,app.color.get_index()+1)
	hint=app.label(panel,"Project colors")
	grid=GridContainer.new();grid.columns=6;panel.add_child(grid)
	app.button(panel,"Keep this color",add_current).tooltip_text="Save the current brush color in this project. Click a saved swatch to reuse it."
	detail=VBoxContainer.new();panel.add_child(detail);app.advanced(detail)
	app.label(detail,"Selected swatch name")
	name_field=LineEdit.new();name_field.max_length=48;detail.add_child(name_field)
	name_field.text_submitted.connect(func(_text):rename_selected())
	app.button(detail,"Rename swatch",rename_selected)
	app.button(detail,"Replace with current color",replace_selected)
	app.button(detail,"Remove swatch",remove_selected)
	refresh(true)

func _process(_delta: float) -> void:
	refresh()
	var color: int=app.color.color.to_rgba32()
	if color!=last_color:
		last_color=color
		if selected<0 or selected>=app.palette.size() or app.palette[selected].rgba!=app.color.color.to_html():
			selected=-1
			for i in range(app.palette.size()):
				if app.palette[i].rgba==app.color.color.to_html():selected=i;break
		fields()

func refresh(force:=false) -> void:
	detail.visible=app.advanced_mode
	if not force and snapshot==app.palette:return
	snapshot=app.palette.duplicate(true)
	for child in grid.get_children():grid.remove_child(child);child.queue_free()
	buttons.clear()
	for i in range(app.palette.size()):
		var row: Dictionary=app.palette[i];var swatch:=Button.new();swatch.icon=Palette.icon(Color(row.rgba));swatch.toggle_mode=true;swatch.focus_mode=Control.FOCUS_NONE
		swatch.custom_minimum_size=Vector2(32,32);swatch.tooltip_text=row.name+" • #"+row.rgba
		swatch.pressed.connect(select.bind(i));grid.add_child(swatch);buttons.append(swatch)
	hint.text="Project colors" if not app.palette.is_empty() else "Keep colors here for this project."
	selected=mini(selected,app.palette.size()-1);last_color=-1;fields()

func fields() -> void:
	name_field.text=app.palette[selected].name if selected>=0 and selected<app.palette.size() else ""
	name_field.editable=selected>=0
	for child in detail.get_children():
		if child is Button:child.disabled=selected<0
	for i in range(buttons.size()):buttons[i].set_pressed_no_signal(i==selected)

func editable() -> bool:
	return not app.exporting and not app.playing and app.source_import.pid<=0 and not (app.home and app.home.visible) and not (app.physics_editor.recording and app.physics_editor.recording.active)

func select(index: int) -> void:
	if not editable() or index<0 or index>=app.palette.size():return
	app.finish_stroke()
	if app.color_sampler:app.color_sampler.cancel()
	selected=index;app.color.color=Color(app.palette[index].rgba);last_color=app.color.color.to_rgba32();fields()

func commit(next: Array,text: String) -> void:
	if not editable():return
	var error:=Palette.error(next)
	if not error.is_empty():app.message(error);return
	if next==app.palette:return
	app.finish_stroke()
	var before: Array=app.palette.duplicate(true);app.palette=next.duplicate(true)
	var cost:=2*(JSON.stringify(before).to_utf8_buffer().size()+JSON.stringify(next).to_utf8_buffer().size())
	app.push_history({"type":"palette","before":before,"after":app.palette.duplicate(true),"bytes":cost});app.changed();refresh(true);app.message(text)

func add_current() -> void:
	if not editable():return
	var rgba: String=app.color.color.to_html()
	for i in range(app.palette.size()):
		if app.palette[i].rgba==rgba:select(i);app.message("Already kept: "+app.palette[i].name);return
	if app.palette.size()>=Palette.MAX_COLORS:app.message("This project already has32 swatches. Remove one in Advanced to keep another.");return
	var next: Array=app.palette.duplicate(true);next.append({"name":"Color %d"%(next.size()+1),"rgba":rgba})
	commit(next,"Kept this color in the project. Advanced offers swatch names and removal.");select(next.size()-1)

func rename_selected() -> void:
	if not editable() or selected<0 or selected>=app.palette.size():return
	var next: Array=app.palette.duplicate(true);next[selected].name=name_field.text.strip_edges();commit(next,"Renamed the color swatch.")

func replace_selected() -> void:
	if not editable() or selected<0 or selected>=app.palette.size():return
	var next: Array=app.palette.duplicate(true);next[selected].rgba=app.color.color.to_html();commit(next,"Updated the saved color; existing artwork stays unchanged.")

func remove_selected() -> void:
	if not editable() or selected<0 or selected>=app.palette.size():return
	var next: Array=app.palette.duplicate(true);next.remove_at(selected);commit(next,"Removed the swatch. Existing artwork keeps its colors.")
