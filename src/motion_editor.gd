extends Node
const Motion=preload("res://src/motion_animation.gd")
const Model=Motion.Body.Model
var app
var button: Button
var window: Window
var enabled: CheckButton
var strength: HSlider
var note: Label
var before: Dictionary={}
var target: WeakRef
var helpers: Tree

func setup(parent: Node) -> void:
	button=app.button(parent,"Motion feeling…",open)
	window=Window.new();window.title="Motion feeling";window.theme=app.theme;app.add_child(window);window.close_requested.connect(func():window.hide())
	var panel:=PanelContainer.new();window.add_child(panel);panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var body:=VBoxContainer.new();panel.add_child(body)
	app.label(body,"Anticipation and settling around your pose keys.\nYour main keys stay exact.").autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	enabled=CheckButton.new();enabled.text="Add motion feeling";body.add_child(enabled)
	app.label(body,"Gentle                                      Lively")
	strength=HSlider.new();strength.min_value=0;strength.max_value=1;strength.step=.05;body.add_child(strength)
	note=app.label(body,"");note.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	helpers=Tree.new();helpers.columns=3;helpers.column_titles_visible=true;helpers.set_column_title(0,"Part");helpers.set_column_title(1,"Frame");helpers.set_column_title(2,"Generated");helpers.hide_root=true;helpers.custom_minimum_size=Vector2(0,180);helpers.size_flags_vertical=Control.SIZE_EXPAND_FILL;body.add_child(helpers)
	app.button(body,"Apply",apply);app.button(body,"Cancel",func():window.hide())
	app.renderer.assets_changed.connect(func():window.hide())

func sync() -> void:
	var rig: RefCounted=app.renderer.active_model()
	button.disabled=not rig or app.exporting or app.playing

func open() -> void:
	var rig: RefCounted=app.renderer.active_model()
	if not rig or app.exporting or app.playing:return
	if app.pose_editor.contacts.live_busy():app.message("Turn Physics and Hair & clothes off before changing motion feeling.");return
	app.pose_editor.finish_drag();before=rig.data.duplicate(true);target=weakref(rig.root)
	enabled.set_pressed_no_signal(rig.motion_enabled());strength.set_value_no_signal(float(rig.data.get("motion_assist",{}).get("strength",.65)));note.text="Saved with this model. Undo restores the previous setting."
	helpers.clear();helpers.visible=app.advanced_mode;var parent:=helpers.create_item();var count:=0
	if app.advanced_mode and rig.motion_enabled():
		var plan: RefCounted=rig.motion_plan()
		if plan:
			var records: Dictionary=plan.helper_keys()
			for id in records:
				for helper in records[id]:
					if count>=256:break
					var row:=helpers.create_item(parent);row.set_text(0,"Model" if id=="@root" else str(rig.bones[id].name));row.set_text(1,"%.2f" % float(helper.frame));row.set_text(2,str(helper.kind));row.set_tooltip_text(0,id);count+=1
		if count>=256:note.text+=" First256 generated keys shown."
		else:note.text+=" Generated keys are rebuilt from your main controls."
	window.size=Vector2i(560,470) if app.advanced_mode else Vector2i(430,270);window.popup_centered()

func apply() -> void:
	var rig: RefCounted=app.renderer.active_model()
	if not rig or not target or target.get_ref()!=rig.root or rig.data!=before or app.exporting or app.playing or app.pose_editor.contacts.live_busy():note.text="The scene changed. Close this window and try again.";return
	if not enabled.button_pressed and before.get("format")!=Motion.FORMAT:window.hide();return
	if rig.data.draft_frame==app.frame:
		if rig.sample_body(app.frame,true)!=rig.sample_body(app.frame,false) or rig.sample_authored_transform(app.frame,true)!=rig.sample_authored_transform(app.frame,false):note.text="Record your draft pose before changing motion feeling.";return
	var changed:=Motion.configure(before,enabled.button_pressed,strength.value,int(app.video.duration_frames))
	if changed.has("error"):note.text=changed.error;return
	var error: String=preload("res://src/contact_clipboard.gd").validate_candidate(rig,changed.data,int(app.video.duration_frames))
	if not error.is_empty():note.text=error;return
	var world: Dictionary=app.current_world()
	for i in range(world.objects.size()):
		if world.objects[i].id==rig.data.id:world.objects[i]=changed.data
	if app.pose_editor.contacts.metadata_bytes(world)>1024*1024:note.text="This change exceeds the project metadata limit.";return
	if changed.data==before:window.hide();return
	error=app.pose_editor.restore_state(changed.data)
	if not error.is_empty():note.text=error;return
	window.hide();app.message("Motion feeling saved. Your main pose keys stay editable.")
