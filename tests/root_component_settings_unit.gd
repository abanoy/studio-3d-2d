extends SceneTree
const D=preload("res://src/root_component_document.gd")
const Ranges=preload("res://src/contact_ranges.gd")
const Motion=preload("res://src/motion_animation.gd")
func _initialize() -> void:
	var plans: Array=JSON.parse_string(FileAccess.get_file_as_string(OS.get_cmdline_user_args()[0]));var checks:=0;var failures:=0
	for plan in plans:
		var original:=D.promote(plan,48);var source: Dictionary=original.data;var saved:=source.duplicate(true);var baseline:=D.compile(source,48)
		var released:=Ranges.edit(source,5,10,{},48);checks+=1
		if released.has("error"):failures+=1;print(released);continue
		var compiled:=D.compile(released.data,48);var exact:=true
		for quarter in range(193):exact=exact and D.Adapter.compiled_sample(baseline,float(quarter)/4.)==D.Adapter.compiled_sample(compiled,float(quarter)/4.)
		checks+=1
		if not exact or Ranges.Contact.Contacts.active(source.animation_clips,6).is_empty() or not Ranges.Contact.Contacts.active(released.data.animation_clips,6).is_empty() or Ranges.Contact.Contacts.active(released.data.animation_clips,12).is_empty():failures+=1;print("FAIL contact range root preservation")
		var enabled:=Motion.configure(source,true,.5,48);checks+=1
		if enabled.has("error"):failures+=1;print(enabled);continue
		var disabled:=Motion.configure(enabled.data,false,.5,48);checks+=1
		if disabled.has("error") or enabled.data.format!=D.FORMAT or disabled.data.root_components!=source.root_components or disabled.data.animation_clips!=source.animation_clips or disabled.data.motion_assist.enabled:failures+=1;print("FAIL assistance settings preserve components")
		checks+=1
		if not Motion.configure(source,true,-1.,48).has("error") or source!=saved:failures+=1;print("FAIL invalid assistance refusal")
	print("ROOT_COMPONENT_SETTINGS "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
