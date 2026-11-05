extends RefCounted
# Prepared evaluator combining shared bone curves and independent root curves.
const Document=preload("res://src/root_component_document.gd")
var body: RefCounted
var components: Dictionary={}

func configure(data: Dictionary,duration: int) -> String:
	var prepared:=Document.compile(data,duration)
	if prepared.has("error"):return prepared.error
	var native_body:=Document.Body.compile(Document.legacy_view(data).duplicate(true))
	body=native_body;components=prepared;return ""

func sample(frame: float) -> Dictionary:
	var result: Dictionary=body.sample(frame)
	result.transform=Document.Adapter.compiled_sample(components,frame)
	return result
