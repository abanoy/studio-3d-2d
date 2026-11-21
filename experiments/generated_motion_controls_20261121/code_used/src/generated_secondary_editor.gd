extends RefCounted
# One visible choice beside Hair & clothes, using existing world history.
const Motion=preload("res://src/generated_secondary_motion.gd")
var app
var editor
var choice: OptionButton
var shown: Dictionary={}
var popup_context: Dictionary={}
func setup(parent: Node) -> void:
	choice=OptionButton.new();choice.custom_minimum_size.x=145
	choice.add_item("Keep hair shape");choice.add_item("Natural gravity")
	parent.add_child(choice);choice.item_selected.connect(change)
	choice.get_popup().about_to_popup.connect(func():popup_context=context())
func context() -> Dictionary:
	var actor: RefCounted=app.renderer.active_model()
	return {"id":actor.data.id,"sha":actor.data.sha256,"root":actor.root.get_instance_id(),"session":app.recovery_session,"revision":app.recovery_revision} if actor and is_instance_valid(actor.root) and actor.root.is_inside_tree() else {}
func supported(actor: RefCounted) -> bool:
	return actor!=null and is_instance_valid(actor.root) and actor.root.is_inside_tree() and actor.data.get("kind","model")=="model" and not actor.order.is_empty() and actor.root.get_meta("has_secondary_rig",{}).get("source_family","")=="HAS"
func busy() -> bool:
	# Existing world-history restoration clears live owners. Never use that
	# path while any model is simulating or still starting,including siblings.
	return app.exporting or app.playing or app.has_project.pid>0 or app.source_import.pid>0 or app.source_import.bundle_active or app.sequence_editor.installing or app.sequence_editor.preview_busy or editor.recording.active or not editor.simulations.is_empty() or not editor.pending.is_empty() or is_instance_valid(editor.helper_editor.window) or is_instance_valid(app.local_wind_review.window)
func sync() -> void:
	var actor: RefCounted=app.renderer.active_model()
	choice.visible=supported(actor)
	if not choice.visible:return
	shown=context()
	var value: Dictionary=Motion.setting(actor.data)
	choice.select(1 if value.get("mode","")=="natural" else 0)
	choice.disabled=busy()
	var configured: bool=not actor.root.get_meta("has_secondary_rig",{}).get("chains",[]).is_empty()
	choice.tooltip_text="Generated loose parts only. Keep hair shape preserves the setup. Natural gravity relaxes loose hair and hanging lengths while retaining attachment position. Declared humanoid and known body joints keep their setup. Pause live motion and close wind review before changing. Imported physics is unchanged."
	if not configured:choice.tooltip_text+="\nNo loose-part joints are configured yet. Use Set up loose parts first."
	if value.has("error"):choice.tooltip_text+="\n"+str(value.error)
func change(index: int) -> void:
	var expected: Dictionary=popup_context if not popup_context.is_empty() else shown
	popup_context={}
	var actor: RefCounted=app.renderer.active_model()
	if not supported(actor) or expected!=context() or busy() or index not in [0,1]:sync();app.message("Pause live motion and finish the current action,then choose this model's hair setting again.");return
	var configured: bool=not actor.root.get_meta("has_secondary_rig",{}).get("chains",[]).is_empty()
	var before: Dictionary=app.current_world();var after: Dictionary=before.duplicate(true)
	for row in after.objects:
		if row.id!=actor.data.id:continue
		if index==0:row.metadata.erase(Motion.KEY)
		else:row.metadata[Motion.KEY]={"format":Motion.FORMAT,"mode":"natural"}
		break
	if before==after:return
	var error: String=app.restore_world(after)
	if not error.is_empty():sync();app.message(error);return
	app.push_history({"type":"world","before":before,"after":after});app.changed();sync()
	app.message("Keep hair shape selected. Original helper settings are retained." if index==0 else "Natural gravity selected. Turn on Hair & clothes to let hanging lengths settle." if configured else "Natural gravity selected. Set up loose-part joints first, then turn on Hair & clothes.")
