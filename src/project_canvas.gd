extends Node
const Canvas=preload("res://src/canvas_size.gd")
const Owner=preload("res://src/cel_raster_owner.gd")
var app
var choices: OptionButton
var displayed:=""
func setup(parent: Node) -> void:
 app.label(parent,"Native drawing canvas")
 choices=OptionButton.new();parent.add_child(choices)
 for id in Canvas.PROFILES:
  var size: Vector2i=Canvas.PROFILES[id];choices.add_item("%d x %d" % [size.x,size.y]);choices.set_item_metadata(choices.item_count-1,id)
 app.button(parent,"Apply canvas size",func():apply(str(choices.get_item_metadata(choices.selected))))
 var note: Label=app.label(parent,"Choose before drawing or adding sequences. Existing artwork is never resized. Movies default to this native size; Advanced can choose a delivery size.")
 note.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART;note.custom_minimum_size.x=480
 sync()
func sync() -> void:
 if not choices:return
 var value:=Canvas.profile(app.video)
 if value==displayed:return
 displayed=value
 for i in range(choices.item_count):
  if choices.get_item_metadata(i)==value:choices.select(i);return
func contains_pixels(value) -> bool:
 if value is Image or value is Owner:return true
 if value is Dictionary:
  for item in value.values():
   if contains_pixels(item):return true
 elif value is Array:
  for item in value:
   if contains_pixels(item):return true
 return false
func error(include_history:=true) -> String:
 if app.exporting or app.playing or app.drawing or app.navigating or app.pose_editor.dragging or app.physics_editor.recording.active or app.physics_editor.is_running():return "Stop playback and finish the current edit or recording before changing canvas size."
 if app.fill_editor.busy() or not app.drawing_selection_editor.context.is_empty():return "Finish or cancel the drawing operation before changing canvas size."
 if not app.sequence_editor.graph.is_empty():return "Choose canvas size before adding sequences. Start a new project to use another native canvas."
 for layer in app.layers:
  if not layer.cels.is_empty():return "Existing artwork is kept at its native size. Choose canvas size in a new project before drawing."
 if include_history:
  for command in app.history+app.redo_history:
   if command.type=="sequence_graph" or command.type in ["pixels","cels","cel_patch","layers"] and contains_pixels(command):return "Undo history still owns artwork or sequences at this size. Start a new project before choosing another native canvas."
 return ""
func restore(video: Dictionary) -> String:
 var why:=Canvas.error(video)
 if why.is_empty():why=error(false)
 if not why.is_empty():return why
 app.stop();app.video=video.duplicate(true);app.renderer.video_settings=app.video
 app.sync_output_size();sync();app.set_frame(app.frame);app.refresh_scene_name();app.changed()
 return ""
func apply(value: String) -> String:
 if not Canvas.PROFILES.has(value):return "Choose a supported native canvas."
 if value==Canvas.profile(app.video):sync();return ""
 var why:=error()
 if not why.is_empty():app.message(why);return why
 var before: Dictionary=app.video.duplicate(true);var after:=before.duplicate(true);var size: Vector2i=Canvas.PROFILES[value]
 after.width=size.x;after.height=size.y
 why=restore(after)
 if not why.is_empty():app.message(why);return why
 app.push_history({"type":"canvas_size","before":before,"after":after,"bytes":512});app.message("Native canvas: %d x %d. Existing source files remain unchanged." % [size.x,size.y]);return ""
