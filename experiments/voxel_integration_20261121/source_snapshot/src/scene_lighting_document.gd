extends RefCounted
# Optional, per-sequence project data. Never stored inside imported model data.
const FORMAT:="studio_scene_lighting_1"
const TYPES:=["directional","point","spot"]
const MAX_LIGHTS:=64

static func empty() -> Dictionary:
	return {"format":FORMAT,"lights":[],"ambient_color":[1.,1.,1.],"ambient_energy":0.}

static func document(video: Dictionary) -> Dictionary:
	return video.get("scene_lighting",empty())

static func indirect(data: Dictionary) -> Dictionary:
	return data.get("indirect",{"enabled":false,"energy":1.,"cell_size":.2,"settle_frames":32})

static func voxel(gi: Dictionary) -> Dictionary:
	return gi.get("voxel",{"position":[0,2,0],"size":[10,6,10],"subdiv":0})

static func number(value: Variant,minimum: float,maximum: float) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and value>=minimum and value<=maximum

static func triple(value: Variant,minimum: float,maximum: float) -> bool:
	if not value is Array or value.size()!=3:return false
	for item in value:
		if not number(item,minimum,maximum):return false
	return true

static func error(value: Variant) -> String:
	if not value is Dictionary or value.get("format")!=FORMAT:return "Unsupported scene lighting document."
	if not value.get("lights") is Array or value.lights.size()>MAX_LIGHTS:return "Scene lighting supports up to 64 authored lights."
	if not triple(value.get("ambient_color"),0,1) or not number(value.get("ambient_energy"),0,4):return "Ambient fill needs an RGB color and intensity from 0 to 4."
	if value.has("indirect"):
		var gi=value.indirect
		if not gi is Dictionary or not gi.get("enabled") is bool:return "Invalid indirect-light setting."
		if not number(gi.get("energy"),0,4) or not number(gi.get("cell_size"),.05,4):return "Indirect light needs strength 0–4 and cell size 0.05–4 scene units."
		if not number(gi.get("settle_frames"),8,120) or float(gi.settle_frames)!=floor(float(gi.settle_frames)):return "Indirect settling must be 8–120 whole render frames."
		if not gi.get("method","sdfgi") in ["sdfgi","voxelgi"]:return "Choose SDFGI or bounded-room VoxelGI."
		if gi.has("voxel"):
			var room=gi.voxel
			if not room is Dictionary or not triple(room.get("position"),-1e12,1e12) or not triple(room.get("size"),1,128):return "VoxelGI needs a room center and size from 1 to 128 scene units per axis."
			if not number(room.get("subdiv"),0,1) or float(room.subdiv)!=floor(float(room.subdiv)):return "Room VoxelGI supports 64 or 128 subdivisions."
	if value.has("reflection"):
		var probe=value.reflection
		if not probe is Dictionary or not probe.get("enabled") is bool:return "Invalid room reflection settings."
		if not triple(probe.get("position"),-1e12,1e12) or not triple(probe.get("size"),.1,100000) or not number(probe.get("intensity"),0,4):return "Room reflections need a position, positive room size and strength from 0 to 4."
	var ids:={}
	for row in value.lights:
		if not row is Dictionary:return "Invalid scene light."
		if not row.get("id") is String or row.id.is_empty() or row.id.length()>128 or ids.has(row.id):return "Scene lights need unique IDs."
		ids[row.id]=true
		if not row.get("name") is String or row.name.strip_edges().is_empty() or row.name.length()>120:return "Light names must contain 1 to 120 characters."
		if not row.get("type") in TYPES or not row.get("visible") is bool or not row.get("shadows") is bool:return "Invalid light type, visibility or shadows."
		if not triple(row.get("position"),-1e12,1e12) or not triple(row.get("rotation_degrees"),-36000,36000):return "Light position or direction is outside the supported range."
		if not triple(row.get("color"),0,1) or not number(row.get("energy"),0,64):return "Light color must be RGB; intensity must be 0 to 64."
		if not number(row.get("range"),.01,100000) or not number(row.get("spot_angle"),1,89):return "Light range must be 0.01 to 100000; spot half-angle must be 1 to 89 degrees."
	return ""

static func create(kind: String,center: Vector3,scale: float=2.) -> Dictionary:
	var distance:=clampf(scale,1.,10000.)
	var position:=center+Vector3(distance*.7,distance,distance)
	var direction:=Basis.looking_at(center-position,Vector3.UP).get_euler()
	return {"id":"light_%d_%d"%[Time.get_ticks_usec(),ResourceUID.create_id()],"name":kind.capitalize()+" light","type":kind,"visible":true,"position":[position.x,position.y,position.z],"rotation_degrees":[rad_to_deg(direction.x),rad_to_deg(direction.y),rad_to_deg(direction.z)],"color":[1.,1.,1.],"energy":1.,"range":distance*4.,"spot_angle":40.,"shadows":true}

static func preset(name: String,center: Vector3,scale: float) -> Array:
	if name=="soft_character":
		var main:=create("directional",center,scale);main.name="Soft character key";main.rotation_degrees=[-25.,-25.,0.];main.energy=.85
		var soft:=create("directional",center,scale);soft.name="Soft character fill";soft.rotation_degrees=[-15.,145.,0.];soft.energy=.3;soft.color=[.85,.9,1.];soft.shadows=false
		return [main,soft]
	var key:=create("directional" if name=="daylight" else "spot",center,scale)
	if name=="daylight":
		key.name="Daylight";key.color=[1.,.94,.84];return [key]
	if name=="stage":
		key.name="Stage spotlight";key.spot_angle=25.;key.energy=3.;return [key]
	key.name="Warm key";key.color=[1.,.82,.65];key.energy=2.
	var fill:=create("point",center,scale)
	fill.name="Cool fill";fill.position[0]=center.x-scale;fill.color=[.65,.8,1.];fill.energy=.5;fill.shadows=false
	return [key,fill]
