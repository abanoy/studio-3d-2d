extends RefCounted
# UI estimates only. Never rewrite skeleton names, binding IDs, poses or native reports.
static var lexicon: Dictionary={}

static func estimate(original: String) -> String:
	if lexicon.is_empty():
		var parsed=JSON.parse_string(FileAccess.get_file_as_string("res://data/bone_names.en.json"))
		if not parsed is Dictionary or not parsed.get("sides") is Dictionary or not parsed.get("parts") is Dictionary:return ""
		lexicon=parsed
	var name:=original.replace("Ｉ","I").replace("Ｋ","K")
	for i in range(10):name=name.replace(String.chr(0xff10+i),str(i))
	var side:=""
	for prefix in lexicon.sides:
		if lexicon.sides[prefix] is String and name.begins_with(prefix):side=lexicon.sides[prefix];name=name.substr(prefix.length());break
	var number:=""
	while not name.is_empty() and name.right(1) in "0123456789":
		number=name.right(1)+number;name=name.left(-1)
	if not lexicon.parts.get(name) is String:return ""
	var part: String=lexicon.parts[name]
	var label:=side+" "+part if not side.is_empty() else part.left(1).to_upper()+part.substr(1)
	return label+(" "+number if not number.is_empty() else "")

static func normalized(original: String) -> String:
	return original.to_lower().replace("_","").replace(".","").replace("-","").replace(" ","")

static func role(data: Dictionary, original: String) -> String:
	var parameters=data.get("metadata",{}).get("native_parameters",{})
	if not parameters is Dictionary or not parameters.get("humanoid") is Dictionary:return ""
	var found:=""
	for key in parameters.humanoid:
		var entry=parameters.humanoid[key]
		if entry is Dictionary and entry.get("node_name","")==original:
			if not found.is_empty():return ""
			found=str(key)
	return found

static func standard(original: String, humanoid_role: String="") -> String:
	# Exact local vocabulary only. Display labels never establish IK bindings.
	if original.begins_with("__HAS_Loose_"):
		var joint:=original.get_slice("_",original.get_slice_count("_")-1)
		if joint.is_valid_int() and int(joint)>=0 and int(joint)<=8:return "Loose joint "+str(int(joint)+1)
	estimate(original) # Load the shared dictionary, including aliases and roles.
	if lexicon.get("roles",{}).has(humanoid_role):return lexicon.roles[humanoid_role]
	var label: String=lexicon.get("aliases",{}).get(normalized(original),"")
	if not label.is_empty():return label
	label=estimate(original)
	for part in lexicon.get("simple_parts",{}):label=label.replace(part,lexicon.simple_parts[part])
	return label if not label.is_empty() else "Other part"

static func display(original: String, advanced:=false, humanoid_role: String="") -> String:
	var label:=standard(original,humanoid_role)
	return label+" · "+original if advanced else label

static func tooltip(original: String, id: String, advanced:=false, humanoid_role: String="") -> String:
	if not advanced:return standard(original,humanoid_role)+"\nSelect to pose. Advanced shows the internal name."
	var english:=estimate(original)
	return ("English estimate: "+english+"\n" if not english.is_empty() else "")+"Original: "+original+"\nBone ID: "+id

static func matches(original: String, query: String, humanoid_role: String="") -> bool:
	return original.to_lower().contains(query.to_lower()) or estimate(original).to_lower().contains(query.to_lower()) or standard(original,humanoid_role).to_lower().contains(query.to_lower())
