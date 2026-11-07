extends Node
const Motion=preload("res://src/motion_animation.gd")
const Model=Motion.Body.Model
var app
var button: Button
var window: Window
var enabled: CheckButton
var strength: HSlider
var note: Label
var summary: Label
var before: Dictionary={}
var target: WeakRef
var helpers: Tree
var part_panel: VBoxContainer
var part_choice: OptionButton
var part_override: CheckButton
var part_strength: HSlider
var part_ids: Array=[]
var draft_strengths: Dictionary={}
var draft_helpers: Dictionary={}
var helper_panel: VBoxContainer
var helper_phase: HSlider
var helper_amount: HSlider

func setup(parent: Node) -> void:
	button=app.button(parent,"Motion feeling…",open)
	window=Window.new();window.title="Motion feeling";window.theme=app.theme;app.add_child(window);window.close_requested.connect(func():window.hide())
	var panel:=PanelContainer.new();window.add_child(panel);panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var body:=VBoxContainer.new();panel.add_child(body)
	summary=app.label(body,"Anticipation and settling around your pose keys.\nYour main keys stay exact.");summary.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	enabled=CheckButton.new();enabled.text="Add motion feeling";body.add_child(enabled)
	app.label(body,"Gentle                                      Lively")
	strength=HSlider.new();strength.min_value=0;strength.max_value=1;strength.step=.05;body.add_child(strength)
	part_panel=VBoxContainer.new();body.add_child(part_panel)
	app.label(part_panel,"Adjust one animated part")
	part_choice=OptionButton.new();part_panel.add_child(part_choice);part_choice.item_selected.connect(func(_i):refresh_part())
	part_override=CheckButton.new();part_override.text="Use a separate amount for this part";part_panel.add_child(part_override)
	part_override.toggled.connect(func(on):
		if part_ids.is_empty():return
		if on:draft_strengths[part_ids[part_choice.selected]]=strength.value
		else:draft_strengths.erase(part_ids[part_choice.selected])
		refresh_part())
	part_strength=HSlider.new();part_strength.min_value=0;part_strength.max_value=1;part_strength.step=.05;part_panel.add_child(part_strength)
	part_strength.value_changed.connect(func(value):
		if not part_ids.is_empty() and part_override.button_pressed:draft_strengths[part_ids[part_choice.selected]]=value)
	note=app.label(body,"");note.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	helpers=Tree.new();helpers.columns=3;helpers.column_titles_visible=true;helpers.set_column_title(0,"Part");helpers.set_column_title(1,"Frame");helpers.set_column_title(2,"Generated");helpers.hide_root=true;helpers.custom_minimum_size=Vector2(0,180);helpers.size_flags_vertical=Control.SIZE_EXPAND_FILL;body.add_child(helpers)
	helper_panel=VBoxContainer.new();body.add_child(helper_panel)
	app.label(helper_panel,"Timing within this movement")
	helper_phase=HSlider.new();helper_phase.min_value=.001;helper_phase.max_value=.999;helper_phase.step=.001;helper_panel.add_child(helper_phase)
	app.label(helper_panel,"Amount of generated motion")
	helper_amount=HSlider.new();helper_amount.max_value=1.;helper_amount.step=.01;helper_panel.add_child(helper_amount)
	app.button(helper_panel,"Reset this helper to automatic",reset_helper)
	helpers.item_selected.connect(refresh_helper)
	helper_phase.value_changed.connect(func(_value):stage_helper())
	helper_amount.value_changed.connect(func(_value):stage_helper())
	app.button(body,"Apply",apply);app.button(body,"Cancel",func():window.hide())
	app.renderer.assets_changed.connect(func():window.hide())

func sync() -> void:
	var rig: RefCounted=app.renderer.active_model()
	button.disabled=not rig or app.exporting or app.playing
	button.text="Try motion feeling…" if rig and not app.advanced_mode and not rig.data.has("motion_assist") else "Motion feeling…"

func open() -> void:
	var rig: RefCounted=app.renderer.active_model()
	if not rig or app.exporting or app.playing:return
	if app.pose_editor.contacts.live_busy():app.message("Turn Physics and Hair & clothes off before changing motion feeling.");return
	app.pose_editor.finish_drag();before=rig.data.duplicate(true);target=weakref(rig.root)
	var first_try: bool=not app.advanced_mode and not before.has("motion_assist")
	summary.text="This switch and amount also control walking. Adjust its steps in Movement path. Per-part controls below change anticipation and settling." if load("res://src/walking_animation.gd").active(before) else "Anticipation and settling around your pose keys.\nYour main keys stay exact."
	enabled.set_pressed_no_signal(first_try or rig.motion_enabled())
	strength.set_value_no_signal(float(rig.data.get("motion_assist",{}).get("strength",.65)))
	note.text="Apply to try this amount between your pose keys. Play the shot to see it, or Undo to return." if first_try else "Saved with this model. Undo restores the previous setting."
	if not app.advanced_mode:
		var keys: Array = rig.authored_keys()
		if keys.is_empty():
			note.text="Record a starting pose, then move the same part on another frame. Motion feeling works between those poses."
		elif keys.size()==1:
			note.text="You have one pose key. Move the same part on another frame to give Motion feeling two poses to work between."
	draft_strengths=before.get("motion_assist",{}).get("part_strengths",{}).duplicate(true)
	draft_helpers=before.get("motion_assist",{}).get("track_helper_edits",{}).duplicate(true)
	helper_panel.hide()
	var part_source: Dictionary=before if Model.is_body(before) else Motion.Body.Model.contact_animation().promote(before,int(app.video.duration_frames))
	part_ids=Motion.parts(part_source) if not part_source.has("error") else [];part_choice.clear()
	for id in draft_strengths:
		if not id in part_ids:part_ids.append(id)
	for id in part_ids:part_choice.add_item("Model movement" if id=="@root" else str(rig.bones[id].name) if rig.bones.has(id) else str(id))
	part_panel.visible=app.advanced_mode;refresh_part()
	helpers.clear();helpers.visible=app.advanced_mode;var parent:=helpers.create_item();var count:=0
	var undisplayed:=draft_helpers.duplicate(true)
	if app.advanced_mode and rig.motion_enabled():
		var plan: RefCounted=rig.motion_plan()
		if plan:
			var records: Dictionary=plan.helper_keys()
			for id in records:
				for helper in records[id]:
					if count>=256:break
					var row:=helpers.create_item(parent);row.set_text(0,"Model" if id=="@root" else str(rig.bones[id].name));row.set_text(1,"%.2f" % float(helper.frame));row.set_text(2,str(helper.kind));row.set_tooltip_text(0,id);count+=1
					row.set_metadata(0,{"part":id,"helper":helper})
					if undisplayed.has(id):undisplayed[id].erase(helper.id)
		if count>=256:note.text+=" First256 generated keys shown."
		else:note.text+=" Generated keys are rebuilt from your main controls."
	if app.advanced_mode:
		for id in undisplayed:
			for address in undisplayed[id]:
				var row:=helpers.create_item(parent)
				row.set_text(0,"Model" if id=="@root" else str(rig.bones[id].name) if rig.bones.has(id) else str(id))
				row.set_text(1,"—")
				row.set_text(2,"Saved adjustment")
				row.set_tooltip_text(2,address)
				row.set_metadata(0,{"part":id,"helper":{"id":address},"saved_only":true})
	window.size=Vector2i(560,600) if app.advanced_mode else Vector2i(430,270);window.popup_centered()

func apply() -> void:
	var rig: RefCounted=app.renderer.active_model()
	if not rig or not target or target.get_ref()!=rig.root or rig.data!=before or app.exporting or app.playing or app.pose_editor.contacts.live_busy():note.text="The scene changed. Close this window and try again.";return
	if not enabled.button_pressed and not before.has("motion_assist"):window.hide();return
	if rig.data.draft_frame==app.frame:
		if rig.sample_body(app.frame,true)!=rig.sample_body(app.frame,false) or rig.sample_authored_transform(app.frame,true)!=rig.sample_authored_transform(app.frame,false):note.text="Record your draft pose before changing motion feeling.";return
	var changed:=Motion.configure(before,enabled.button_pressed,strength.value,int(app.video.duration_frames),draft_strengths,draft_helpers)
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

func refresh_part() -> void:
	var available:=not part_ids.is_empty()
	part_choice.disabled=not available;part_override.disabled=not available
	var separate: bool=available and draft_strengths.has(part_ids[part_choice.selected])
	part_override.set_pressed_no_signal(separate);part_strength.editable=separate
	part_strength.set_value_no_signal(float(draft_strengths[part_ids[part_choice.selected]]) if separate else strength.value)
	part_strength.tooltip_text="0 keeps this part on its authored motion; other parts keep their own amounts."

func refresh_helper() -> void:
	var row:=helpers.get_selected()
	if not row or not app.advanced_mode:
		helper_panel.hide()
		return
	var selection: Dictionary=row.get_metadata(0)
	var helper: Dictionary=selection.helper
	var saved_only: bool=selection.get("saved_only",false)
	helper_phase.editable=not saved_only
	helper_amount.editable=not saved_only
	if saved_only:
		helper_panel.visible=draft_helpers.get(selection.part,{}).has(helper.id)
		if helper_panel.visible:
			var saved: Dictionary=draft_helpers[selection.part][helper.id]
			helper_phase.set_value_no_signal(saved.phase)
			helper_amount.set_value_no_signal(saved.amount)
			note.text="This saved adjustment has no displayed frame. Reset it here, then Apply."
		return
	helper_panel.visible=helper.get("editable",false)
	if not helper_panel.visible:return
	var edit: Dictionary=draft_helpers.get(selection.part,{}).get(helper.id,{})
	helper_phase.set_value_no_signal(edit.get("phase",helper.get("automatic_phase",helper.phase)))
	helper_amount.set_value_no_signal(edit.get("amount",1.))

func stage_helper() -> void:
	var selection: Dictionary=helpers.get_selected().get_metadata(0)
	if not draft_helpers.has(selection.part):draft_helpers[selection.part]={}
	draft_helpers[selection.part][selection.helper.id]={"phase":helper_phase.value,"amount":helper_amount.value}

func reset_helper() -> void:
	var selection: Dictionary=helpers.get_selected().get_metadata(0)
	if draft_helpers.has(selection.part):
		draft_helpers[selection.part].erase(selection.helper.id)
		if draft_helpers[selection.part].is_empty():draft_helpers.erase(selection.part)
	if selection.get("saved_only",false):
		helpers.get_selected().set_text(2,"Reset on Apply")
		note.text="Apply to save this reset, or Cancel to keep the adjustment."
	refresh_helper()
