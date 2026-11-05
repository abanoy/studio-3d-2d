extends SceneTree
const Document=preload("res://src/root_component_document.gd")
const Model=Document.Model
func _initialize() -> void:
	var plans: Array=JSON.parse_string(FileAccess.get_file_as_string(OS.get_cmdline_user_args()[0]));var failures:=0;var checks:=0
	for plan in plans:
		var original: Dictionary=plan.duplicate(true);var result:=Document.promote(plan,48);checks+=1
		if result.has("error"):failures+=1;print(result);continue
		var restored: Dictionary=JSON.parse_string(JSON.stringify(result.data));checks+=1
		if not Document.validate(restored,48).is_empty() or Document.legacy_view(restored)!=JSON.parse_string(JSON.stringify(Document.Body.promote(plan,48))):failures+=1
		checks+=1
		if not Model.validate(result.data,48).is_empty() or plan!=original:failures+=1
		var wrong:=restored.duplicate(true);wrong.component_base_format="studio_model_999";checks+=1
		if Document.validate(wrong,48).is_empty():failures+=1
		var piece: Dictionary=restored.animation_clips[0];var at:=int(piece.start);var compiled:=Document.compile(restored,48)
		var edited:=Document.put_component(restored,at,"position",[.1,.2,.3],"ease",48);checks+=1
		if edited.has("error"):failures+=1;print(edited);continue
		var changed:=Document.compile(edited.data,48);var exact:=true
		for quarter in range(193):
			var before:=Document.Adapter.compiled_sample(compiled,float(quarter)/4.);var after:=Document.Adapter.compiled_sample(changed,float(quarter)/4.)
			exact=exact and before.rotation_xyzw==after.rotation_xyzw and before.scale==after.scale
		checks+=1
		if not exact or Model.Timeline.vector(Document.Adapter.compiled_sample(changed,at).position).distance_to(Vector3(.1,.2,.3))>0.0000001 or Document.legacy_view(edited.data)!=Document.legacy_view(restored):failures+=1
		wrong=restored.duplicate(true);wrong.root_components["missing-clip"]={};checks+=1
		if Document.validate(wrong,48).is_empty():failures+=1
	print("ROOT_COMPONENT_DOCUMENT "+JSON.stringify({"checks":checks,"failures":failures,"models":plans.size()}));quit(0 if failures==0 else 1)
