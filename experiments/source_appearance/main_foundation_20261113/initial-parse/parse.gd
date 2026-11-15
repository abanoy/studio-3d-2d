extends SceneTree
const Choice=preload("res://src/source_choice_dialog.gd")
const Importer=preload("res://src/source_import.gd")
func _initialize() -> void:
 var choice=Choice.new();choice.free()
 var importer=Importer.new();importer.free()
 print("SOURCE_CHOICE_PARSE OK")
 quit(0)
