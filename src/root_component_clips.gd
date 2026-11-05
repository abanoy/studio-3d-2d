extends RefCounted
# Experimental bridge reuses the existing source-time/gap evaluator.
# Component documents are not admitted by the production Model reader yet.
const B=preload("res://src/body_curves.gd")
const Components=preload("res://src/root_component_curves.gd")
const Runtime=preload("res://src/body_curve_runtime.gd")

static func component_view(body: Dictionary,components: Dictionary,field: String) -> Dictionary:
	var view:=body.duplicate(true)
	for piece in view.pieces:
		if not components.has(piece.id):continue
		piece.legacy_channels.erase("@root");piece.removed.erase("@root");piece["rest_keys"]=[]
		var keys: Array=components[piece.id][field]
		if keys.is_empty():piece.controls.erase("@root")
		else:
			piece.controls["@root"]=keys.duplicate(true)
			piece.origin=int(keys[0].frame)
	return view

static func compile(body: Dictionary,components: Dictionary,duration: int) -> Dictionary:
	var error:=B.validate(body,duration)
	if not error.is_empty():return {"error":error}
	var ids: Array=body.pieces.map(func(piece):return piece.id)
	for id in components:
		if not id in ids:return {"error":"Root components refer to a missing clip."}
		error=Components.validate(components[id])
		if not error.is_empty():return {"error":error}
	var result:={"base":body.base_transform.duplicate(true),"tracks":{}}
	for field in Components.FIELDS:
		var view:=component_view(body,components,field)
		error=B.validate(view,duration)
		if not error.is_empty():return {"error":error}
		var runtime:=Runtime.new();runtime.build(view);result.tracks[field]=runtime
	return result

static func compiled_sample(prepared: Dictionary,frame: float) -> Dictionary:
	var result: Dictionary=prepared.base.duplicate(true)
	for field in Components.FIELDS:result[field]=prepared.tracks[field].channel(frame,"@root")[field]
	return result

static func extract(body: Dictionary) -> Dictionary:
	var result:={}
	for piece in body.pieces:
		if B.owns(piece,"@root"):
			result[piece.id]=Components.split(B.points(body,piece,"@root",true))
			var authored: Array=B.points(body,piece,"@root",false).map(func(key):return int(key.frame))
			for field in Components.FIELDS:
				for key in result[piece.id][field]:
					if not int(key.frame) in authored:key["authored"]=false
	return result

static func sample(body: Dictionary,components: Dictionary,frame: float) -> Dictionary:
	var result: Dictionary=body.base_transform.duplicate(true)
	for field in Components.FIELDS:
		var view:=component_view(body,components,field)
		result[field]=B.sample_channel(view,frame,"@root")[field]
	return result
