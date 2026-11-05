extends RefCounted
# UI metadata only. Imported target IDs, geometry and animation stay intact.
const Labels=preload("res://src/shape_labels.gd")
const FORMAT:="studio_shape_catalog_1"
const AREAS:=["Brows","Eyes","Mouth","Body","Clothing","Hair","Accessories","Other"]
const ALIASES:={
	"まばたき":["Eyes","Blink"],"瞬き":["Eyes","Blink"],"ウィンク":["Eyes","Wink"],
	"あ":["Mouth","Mouth A"],"い":["Mouth","Mouth I"],"う":["Mouth","Mouth U"],"え":["Mouth","Mouth E"],"お":["Mouth","Mouth O"],
	"blink":["Eyes","Blink"],"eyebrows raise":["Brows","Raise brows"],"mouth angry open":["Mouth","Angry open mouth"],
	"tools":["Accessories","Tools"],"wing shrink":["Accessories","Smaller wings"],"wing expand big":["Accessories","Larger wings"],"normal hair":["Hair","Hair shape"]}

static func normalized(value: String) -> String:
	var original:=value.strip_edges();var separated:=""
	# Native Source controls commonly use CamelCase: CloseLidUpL, OpenJaw.
	# Split acronym boundaries too; do not alter the original stored name or ID.
	for i in range(original.length()):
		var character:=original[i]
		if i>0 and character in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
			var previous:=original[i-1]
			var next_lower: bool=i+1<original.length() and original[i+1] in "abcdefghijklmnopqrstuvwxyz"
			if previous in "abcdefghijklmnopqrstuvwxyz" or previous in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" and next_lower:separated+=" "
		separated+=character
	var name:=separated.to_lower().replace("_"," ").replace("-"," ")
	while "  " in name:name=name.replace("  "," ")
	return name

static func estimate(native_name: String) -> Dictionary:
	var name:=normalized(native_name)
	if ALIASES.has(name):return {"area":ALIASES[name][0],"label":ALIASES[name][1],"evidence":"Name estimate", "manual":false}
	var tokens:=name.split(" ",false);var matches:=[]
	if "brow" in name or "眉" in name:matches.append("Brows")
	var clues:={"Eyes":["eye","eyes","eyelid","eyelids","lid","lids","pupil","pupils","blink","wink","squint","sclera","scerla"],"Mouth":["mouth","lip","lips","tongue","teeth","fang","fangs","jaw"],"Body":["body","belly","waist","shoulder","shoulders","arm","arms","leg","legs"],"Clothing":["skirt","dress","coat","clothing","sleeve","sleeves","shirt","pants"],"Hair":["hair","bangs"],"Accessories":["wing","wings","tools","hat","glasses","ribbon"]}
	for area in clues:
		for token in clues[area]:
			if area=="Eyes" and token in ["eye","eyes"] and matches.has("Brows"):continue # "eye brows" is one area, brow + lid/squint is mixed.
			if token in tokens:matches.append(area);break
	var area: String=matches[0] if matches.size()==1 else "Other"
	return {"area":area,"label":Labels.display(native_name,false).strip_edges(),"evidence":"Name estimate" if matches.size()==1 else ("Ambiguous name" if matches.size()>1 else "Unassigned"),"manual":false}

static func index_key(key,limit: int) -> bool:
	return key is String and key.is_valid_int() and str(int(key))==key and int(key)>=0 and int(key)<limit

static func validate(value) -> String:
	if not value is Dictionary or value.get("format")!=FORMAT or not value.get("controls") is Dictionary:return "Unsupported saved control catalogue."
	var count:=0
	for node in value.controls:
		if not index_key(node,100000) or not value.controls[node] is Dictionary:return "Invalid control part identity."
		for target in value.controls[node]:
			count+=1
			if count>256 or not index_key(target,2048):return "Control catalogue exceeds its assignment limit."
			var entry=value.controls[node][target]
			if not entry is Dictionary or not entry.get("native_name") is String or entry.native_name.length()>512 or not entry.get("label") is String or entry.label.length()>80 or not entry.get("area") in AREAS:return "Invalid saved control assignment."
	return ""

static func lookup(data: Dictionary,node: int,target: int,native_name: String) -> Dictionary:
	var guess:=estimate(native_name);var catalog=data.get("metadata",{}).get("shape_catalog",{})
	if catalog is Dictionary and catalog.is_empty():return guess
	var error:=validate(catalog)
	if not error.is_empty():guess["notice"]=error;return guess
	var entry=catalog.controls.get(str(node),{}).get(str(target),{})
	if entry.is_empty():return guess
	if entry.native_name!=native_name:guess["notice"]="Saved choice belongs to a different native control.";return guess
	return {"area":entry.area,"label":entry.label if not entry.label.is_empty() else guess.label,"evidence":"Manual choice","manual":true}

static func assign(data: Dictionary,node: int,target: int,native_name: String,area: String,label: String) -> Dictionary:
	if node<0 or node>=100000 or target<0 or target>=2048 or not area in AREAS or label.length()>80 or native_name.length()>512:return {"error":"Invalid control assignment."}
	var result:=data.duplicate(true);var metadata: Dictionary=result.get("metadata",{}).duplicate(true)
	var catalog=metadata.get("shape_catalog",{"format":FORMAT,"controls":{}})
	var error:=validate(catalog)
	if not error.is_empty():return {"error":error}
	if not catalog.controls.has(str(node)):catalog.controls[str(node)]={}
	catalog.controls[str(node)][str(target)]={"native_name":native_name,"area":area,"label":label.strip_edges()}
	error=validate(catalog)
	if not error.is_empty():return {"error":error}
	metadata["shape_catalog"]=catalog;result["metadata"]=metadata
	return {"data":result}

static func clear(data: Dictionary,node: int,target: int) -> Dictionary:
	var result:=data.duplicate(true);var metadata: Dictionary=result.get("metadata",{}).duplicate(true)
	if not metadata.has("shape_catalog"):return {"data":result}
	var catalog=metadata.shape_catalog;var error:=validate(catalog)
	if not error.is_empty():return {"error":error}
	if catalog.controls.has(str(node)):
		catalog.controls[str(node)].erase(str(target))
		if catalog.controls[str(node)].is_empty():catalog.controls.erase(str(node))
	if catalog.controls.is_empty():metadata.erase("shape_catalog")
	else:metadata.shape_catalog=catalog
	result["metadata"]=metadata;return {"data":result}
