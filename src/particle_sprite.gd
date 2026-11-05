extends RefCounted
# Experimental canonical sprite evaluator. No autonomous tick or source-family path.
const FORMAT := "studio_sprite_effect_1"
const MAX_PARTICLES := 1024
var root: MultiMeshInstance3D
var data := {}
var evaluation_error := ""
var last_values: Array = []

static func number(value,low: float=-100000.,high: float=100000.) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and value>=low and value<=high

static func vector(value,count: int) -> bool:
	if not value is Array or value.size()!=count:return false
	for component in value:
		if not number(component):return false
	return true

static func validate(value) -> String:
	if not value is Dictionary or value.get("format")!=FORMAT or not value.get("name") is String or not number(value.get("duration"),.01,60) or not number(value.get("max_particles"),1,MAX_PARTICLES) or value.max_particles!=floor(value.max_particles) or not value.get("particles") is Array or value.particles.size()>MAX_PARTICLES:return "Invalid sprite descriptor."
	for row in value.particles:
		if not row is Dictionary or not number(row.get("birth"),0,60) or not number(row.get("lifetime"),.001,60) or not vector(row.get("position"),3) or not vector(row.get("velocity"),3) or not vector(row.get("acceleration"),3) or not number(row.get("radius"),.000001,1000) or not vector(row.get("color"),4) or not number(row.get("rotation")) or not number(row.get("spin")):return "Invalid sprite birth."
		for c in row.color:
			if not number(c,0,1):return "Invalid sprite color."
	for key in ["alpha","radius","color"]:
		if not value.get(key) is Dictionary:return "Missing sprite curve."
	var a: Dictionary=value.alpha
	for key in ["in_start","in_end","out_start","out_end","start_alpha","end_alpha"]:
		if not number(a.get(key),0,1):return "Invalid sprite alpha curve."
	if not(a.in_start<=a.in_end and a.in_end<=a.out_start and a.out_start<=a.out_end):return "Overlapping sprite fades."
	var r: Dictionary=value.radius
	if not number(r.get("start"),0,1) or not number(r.get("end"),0,1) or r.start>r.end or not number(r.get("from"),0,100) or not number(r.get("to"),0,100) or not number(r.get("bias"),.001,.999) or not r.get("ease") is bool:return "Invalid sprite radius curve."
	var c: Dictionary=value.color
	if not c.get("enabled") is bool or not c.get("ease") is bool or not number(c.get("start"),0,1) or not number(c.get("end"),0,1) or c.start>c.end or not vector(c.get("to"),4):return "Invalid sprite color curve."
	for component in c.to:
		if not number(component,0,1):return "Invalid sprite target color."
	for row in value.particles:
		var active:=0
		for peer in value.particles:
			if peer.birth<=row.birth and row.birth<peer.birth+peer.lifetime:active+=1
		if active>value.max_particles:return "Sprite capacity would discard births."
	return ""

static func ramp(t: float,start: float,end: float) -> float:
	return (1. if t>=end else 0.) if start==end else clampf((t-start)/(end-start),0.,1.)

func sample(seconds: float) -> Array:
	if not is_finite(seconds) or seconds<0 or seconds>=float(data.get("duration",0)):return []
	var result:=[]
	for row in data.particles:
		var age: float=seconds-row.birth
		if age<0 or age>=row.lifetime:continue
		var t: float=age/row.lifetime
		var p:=Vector3(row.position[0],row.position[1],row.position[2])+Vector3(row.velocity[0],row.velocity[1],row.velocity[2])*age+Vector3(row.acceleration[0],row.acceleration[1],row.acceleration[2])*.5*age*age
		var alpha: float=row.color[3]*lerpf(data.alpha.start_alpha,1.,ramp(t,data.alpha.in_start,data.alpha.in_end))*lerpf(1.,data.alpha.end_alpha,ramp(t,data.alpha.out_start,data.alpha.out_end))
		var u:=ramp(t,data.radius.start,data.radius.end)
		u=pow(u,log(data.radius.bias)/log(.5))
		if data.radius.ease:u=u*u*(3.-2.*u)
		var radius: float=row.radius*lerpf(data.radius["from"],data.radius.to,u)
		var color:=Color(row.color[0],row.color[1],row.color[2],alpha)
		if data.color.enabled:
			var v:=ramp(t,data.color.start,data.color.end)
			if data.color.ease:v=v*v*(3.-2.*v)
			color.r=lerpf(color.r,data.color.to[0],v);color.g=lerpf(color.g,data.color.to[1],v);color.b=lerpf(color.b,data.color.to[2],v)
		result.append({"position":p,"radius":radius,"color":color,"rotation":row.rotation+row.spin*age})
	return result

func setup(value: Dictionary,texture: Texture2D) -> String:
	var error:=validate(value)
	if not error.is_empty():return error
	if not texture:return "Missing particle texture."
	var candidate:=MultiMeshInstance3D.new()
	var multi:=MultiMesh.new();multi.transform_format=MultiMesh.TRANSFORM_3D;multi.use_colors=true;multi.use_custom_data=true
	var quad:=QuadMesh.new();quad.size=Vector2(2,2)
	var material:=ShaderMaterial.new();material.shader=preload("res://src/particle_sprite.gdshader");material.set_shader_parameter("sprite",texture);quad.material=material
	multi.mesh=quad;multi.instance_count=int(value.max_particles);multi.visible_instance_count=0
	candidate.multimesh=multi;candidate.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	dispose();root=candidate;data=value.duplicate(true)
	return ""

func evaluate(seconds: float) -> Array:
	if not is_finite(seconds):
		evaluation_error="Particle time must be finite."
		return last_values.duplicate(true)
	evaluation_error=""
	var values:=sample(seconds)
	last_values=values.duplicate(true)
	if not is_instance_valid(root):return values
	root.multimesh.visible_instance_count=values.size()
	var bounds:=AABB()
	for i in range(values.size()):
		var row: Dictionary=values[i]
		var extent: Vector3=Vector3.ONE*row.radius*sqrt(2.)
		var particle_bounds:=AABB(row.position-extent,extent*2.)
		bounds=particle_bounds if i==0 else bounds.merge(particle_bounds)
		root.multimesh.set_instance_transform(i,Transform3D(Basis.IDENTITY.scaled(Vector3.ONE*row.radius),row.position))
		root.multimesh.set_instance_color(i,row.color);root.multimesh.set_instance_custom_data(i,Color(row.rotation,0,0,0))
	root.multimesh.custom_aabb=bounds
	return values

func dispose() -> void:
	if is_instance_valid(root):
		if root.get_parent():root.get_parent().remove_child(root)
		root.free()
	root=null;data={};last_values=[];evaluation_error=""
